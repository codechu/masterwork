"""The frozen gate: a threshold is only a threshold if it clears the noise.

Before a run decides anything, the decision rule is written down and frozen.
Looking at results afterwards is fine; moving the rule is not. But a frozen
rule is still worthless if the threshold sits inside the arm's own run-to-run
spread — then the gate is not reading the effect, it is reading the sampling.

So a gate section must carry three lines, and this checker enforces all
three by executing the first one:

    band-command: <a command that COMPUTES the spread>
    band-value:   <the spread it produces, with n>
    threshold:    <the decision threshold — must be above the band>

The reason it is three lines rather than a principle: written as a
principle, it gets read, agreed with, and skipped. A skip then costs
nothing and shows up nowhere. With three required lines, skipping means
actively leaving them blank, which is visible.

Two verdicts other than pass, both deliberate:

  * A band-command that merely prints a number already written in its own
    text is not a measurement, it is a quotation. That returns UNVERIFIABLE
    (exit 2) — a human has to sign for it — rather than passing quietly.
  * A section that produces a decision but carries none of the three lines
    fails outright. A section that is deliberately not a gate says so with
    `gate-skip: <reason>`, and the reason is printed, so exemptions cannot
    hide as silence.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import subprocess
import sys

FIELDS = ("band-command", "band-value", "threshold")
# A section that names an axis is applied to the measured report as well as
# checked for validity. Without `measure`, a gate is only a written rule and
# a human still has to bind it to numbers — which is where a verdict quietly
# becomes an opinion.
APPLY = ("measure", "compare")
# Field names are data, like seal headers: a workshop writing its gates in
# another language passes --profile {canonical: [aliases]} rather than
# translating frozen documents, which would edit the record after the fact.
DEFAULT_FIELD_ALIASES: dict[str, list[str]] = {f: [f] for f in FIELDS}
SKIP = re.compile(r"^\s*gate-skip\s*:\s*(.+)$", re.M | re.I)
# A section that decides something: an explicit verdict word or a comparison.
DECIDES = re.compile(r"^.*(?:\b(?:accept|reject|veto|pass|fail)\b\s*:|>=|<=|≥|≤).*$",
                     re.M | re.I)
NUMBER = re.compile(r"-?\d+(?:[.,]\d+)?")
ABOVE = re.compile(r"\babove\b", re.I)
# "above" is a word, and words are dialect like field names. A workshop that
# writes its frozen gates in another language should configure the reader
# rather than translate documents that were frozen before a run.
ABOVE_WORDS = ("above",)


def numbers(text: str) -> list[float]:
    return [float(m.group(0).replace(",", ".")) for m in NUMBER.finditer(text)]


def first_number(text: str):
    n = numbers(text)
    return n[0] if n else None


def field(body: str, name: str, aliases: dict | None = None):
    for alias in (aliases or DEFAULT_FIELD_ALIASES).get(name, [name]):
        m = re.search(rf"^\s*{re.escape(alias)}\s*:\s*(.+)$", body, re.M | re.I)
        if m:
            return m.group(1).strip()
    return None


def sections(text: str):
    for part in re.split(r"^##\s+", text, flags=re.M)[1:]:
        title, _, body = part.partition("\n")
        yield title.strip(), body


def _above(text: str, aliases: dict | None) -> bool:
    words = (aliases or {}).get("above") or ABOVE_WORDS
    return any(re.search(rf"\b{re.escape(w)}\b", text, re.I) for w in words)


def check_section(body: str, timeout: int = 60, aliases: dict | None = None):
    """Return (verdict, notes). verdict: PASS | FAIL | UNVERIFIABLE | SKIP."""
    skip = SKIP.search(body)
    if skip:
        return "SKIP", [f"declared not a gate: {skip.group(1).strip()}"]

    missing = [f for f in FIELDS if field(body, f, aliases) is None]
    if len(missing) == len(FIELDS):
        line = DECIDES.search(body)
        return "FAIL", ["decides something but no band was measured",
                        f"matched decision line: {line.group(0).strip()[:100]!r}"
                        if line else "",
                        "if this is not a gate, add `gate-skip: <reason>`"]
    if missing:
        return "FAIL", [f"missing: {', '.join(missing)} — the gate is void"]

    command = field(body, "band-command", aliases)
    written = first_number(field(body, "band-value", aliases) or "")
    placement = field(body, "threshold", aliases) or ""

    try:
        p = subprocess.run(["bash", "-lc", command], capture_output=True,
                           text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "FAIL", [f"band-command did not finish in {timeout}s"]
    if p.returncode != 0:
        return "FAIL", [f"band-command failed (rc={p.returncode}): "
                        f"{(p.stderr or p.stdout).strip()[:200]}"]

    produced = numbers(p.stdout)
    if not produced or written is None:
        return "UNVERIFIABLE", [f"band is not numeric; output was "
                                f"{p.stdout.strip()[:120]!r} — sign for it by hand"]

    close = [x for x in produced if abs(x - written) <= max(0.02, 0.05 * abs(x))]
    if not close:
        return "FAIL", [f"band-value says {written} but the command produces "
                        f"{produced[:6]} — the band was written from memory"]

    if any(abs(x - written) <= 1e-9 for x in numbers(command)):
        return "UNVERIFIABLE", [f"band-command does not compute {written}, it "
                                f"restates it — a quotation, not a measurement"]

    band = close[0]
    if not _above(placement, aliases):
        return "FAIL", [f"threshold does not claim to be above the band: {placement!r}"]
    threshold = first_number(placement)
    if threshold is None:
        return "UNVERIFIABLE", [f"threshold is not numeric: {placement!r}"]
    if threshold <= band:
        return "FAIL", [f"threshold {threshold} <= band {band:.4f} — this gate "
                        f"reads sampling noise, not effect"]
    sound = (f"band {band:.4f} (computed) · threshold {threshold} "
             f"· margin {threshold - band:+.4f}")
    # Sound rule, nothing to apply it to. Said here, at freeze time, because
    # the alternative is learning it after the run — when a human binds the
    # rule by hand and the verdict quietly becomes an opinion.
    if not field(body, "measure", aliases):
        return "UNBOUND", [sound, "no `measure:` field — this rule can never "
                                  "touch a report; name the axis now, not later"]
    return "PASS", [sound]


def evaluate_section(body: str, measured: dict, incumbent: dict | None = None,
                     aliases: dict | None = None):
    """Apply a checked gate to measured axes. (verdict, notes).

    verdict: ACCEPT | REJECT | UNRESOLVED | NOT_APPLIED

    UNRESOLVED is a real answer and is kept distinct from "no difference".
    A difference smaller than the threshold has not been shown to be absent;
    it has been shown to be unresolvable at this size, and the note says how
    many cells per arm it would take — otherwise the next reader turns a
    silence into a finding.
    """
    axis = field(body, "measure", aliases)
    if not axis:
        return "NOT_APPLIED", ["no `measure:` field — the rule is written but "
                               "never bound to a number"]
    if axis not in measured:
        return "NOT_APPLIED", [f"axis {axis!r} is not in the report "
                               f"(has: {', '.join(sorted(measured)) or 'nothing'})"]

    threshold = first_number(field(body, "threshold", aliases) or "")
    band = first_number(field(body, "band-value", aliases) or "")
    compare = (field(body, "compare", aliases) or "candidate").lower()
    value = measured[axis]

    if "incumbent" in compare:
        if not incumbent or axis not in incumbent:
            return "NOT_APPLIED", [f"comparison needs the incumbent's {axis}, "
                                   f"which was not supplied"]
        difference = value - incumbent[axis]
        shown = (f"{axis}: candidate {value:.4f} − incumbent "
                 f"{incumbent[axis]:.4f} = {difference:+.4f}")
    else:
        difference = value
        shown = f"{axis}: {value:.4f} (absolute)"

    if threshold is None:
        return "NOT_APPLIED", [shown, "threshold is not numeric"]
    if difference >= threshold:
        return "ACCEPT", [shown, f"clears +{threshold}"]
    if difference <= -threshold:
        return "REJECT", [shown, f"falls short by {threshold}"]

    note = [shown, f"inside ±{threshold} — NOT resolvable at this size, "
                   f"which is not the same as no difference"]
    if band and abs(difference) > 0:
        # Band shrinks as 1/sqrt(n); say what size would settle this.
        note.append(f"a difference of {abs(difference):.4f} needs a band below "
                    f"it: roughly {(band / abs(difference)) ** 2:.1f}x the cells "
                    f"used for this band")
    return "UNRESOLVED", note


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="check frozen gate files")
    ap.add_argument("paths", nargs="+", help="gate files, or a directory to walk")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--profile", help="JSON map {canonical field: [aliases]}")
    a = ap.parse_args(argv)

    aliases = dict(DEFAULT_FIELD_ALIASES)
    if a.profile:
        import json as _json
        for k, v in _json.load(open(a.profile, encoding="utf-8")).items():
            aliases[k] = list(v) + aliases.get(k, [])
    files = []
    for p in a.paths:
        files.extend(sorted(glob.glob(os.path.join(p, "**", "*.md"), recursive=True))
                     if os.path.isdir(p) else [p])

    tally: dict[str, int] = {}
    for path in files:
        text = open(path, encoding="utf-8").read()
        printed = False
        for title, body in sections(text):
            if not (DECIDES.search(body) or field(body, "band-command", aliases)):
                continue
            verdict, notes = check_section(body, a.timeout, aliases)
            if not printed:
                print(f"--- {path}")
                printed = True
            print(f"    [{verdict:<12}] {title}")
            for n in notes:
                if n:
                    print(f"        {n}")
            tally[verdict] = tally.get(verdict, 0) + 1

    print("\n" + " · ".join(f"{v} {k}" for k, v in sorted(tally.items())) or "nothing to check")
    if tally.get("FAIL"):
        return 1
    if tally.get("UNVERIFIABLE") or tally.get("UNBOUND"):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
