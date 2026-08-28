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
SKIP = re.compile(r"^\s*gate-skip\s*:\s*(.+)$", re.M | re.I)
# A section that decides something: an explicit verdict word or a comparison.
DECIDES = re.compile(r"^.*(?:\b(?:accept|reject|veto|pass|fail)\b\s*:|>=|<=|≥|≤).*$",
                     re.M | re.I)
NUMBER = re.compile(r"-?\d+(?:[.,]\d+)?")
ABOVE = re.compile(r"\babove\b", re.I)


def numbers(text: str) -> list[float]:
    return [float(m.group(0).replace(",", ".")) for m in NUMBER.finditer(text)]


def first_number(text: str):
    n = numbers(text)
    return n[0] if n else None


def field(body: str, name: str):
    m = re.search(rf"^\s*{re.escape(name)}\s*:\s*(.+)$", body, re.M | re.I)
    return m.group(1).strip() if m else None


def sections(text: str):
    for part in re.split(r"^##\s+", text, flags=re.M)[1:]:
        title, _, body = part.partition("\n")
        yield title.strip(), body


def check_section(body: str, timeout: int = 60):
    """Return (verdict, notes). verdict: PASS | FAIL | UNVERIFIABLE | SKIP."""
    skip = SKIP.search(body)
    if skip:
        return "SKIP", [f"declared not a gate: {skip.group(1).strip()}"]

    missing = [f for f in FIELDS if field(body, f) is None]
    if len(missing) == len(FIELDS):
        line = DECIDES.search(body)
        return "FAIL", ["decides something but no band was measured",
                        f"matched decision line: {line.group(0).strip()[:100]!r}"
                        if line else "",
                        "if this is not a gate, add `gate-skip: <reason>`"]
    if missing:
        return "FAIL", [f"missing: {', '.join(missing)} — the gate is void"]

    command = field(body, "band-command")
    written = first_number(field(body, "band-value") or "")
    placement = field(body, "threshold") or ""

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
    if not ABOVE.search(placement):
        return "FAIL", [f"threshold does not claim to be above the band: {placement!r}"]
    threshold = first_number(placement)
    if threshold is None:
        return "UNVERIFIABLE", [f"threshold is not numeric: {placement!r}"]
    if threshold <= band:
        return "FAIL", [f"threshold {threshold} <= band {band:.4f} — this gate "
                        f"reads sampling noise, not effect"]
    return "PASS", [f"band {band:.4f} (computed) · threshold {threshold} "
                    f"· margin {threshold - band:+.4f}"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="check frozen gate files")
    ap.add_argument("paths", nargs="+", help="gate files, or a directory to walk")
    ap.add_argument("--timeout", type=int, default=60)
    a = ap.parse_args(argv)

    files = []
    for p in a.paths:
        files.extend(sorted(glob.glob(os.path.join(p, "**", "*.md"), recursive=True))
                     if os.path.isdir(p) else [p])

    tally: dict[str, int] = {}
    for path in files:
        text = open(path, encoding="utf-8").read()
        printed = False
        for title, body in sections(text):
            if not (DECIDES.search(body) or field(body, "band-command")):
                continue
            verdict, notes = check_section(body, a.timeout)
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
    if tally.get("UNVERIFIABLE"):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
