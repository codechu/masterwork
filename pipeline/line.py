"""The line: one run, every gate, no step left to memory.

Producing a candidate is mechanical, and each mechanical step here has been
skipped by hand at least once. Every skip produced a number that looked real
and was not: an unverified deployed copy, a grid quietly short of cells, a
threshold inside its own noise, a negative result never written down.

The line runs the stages in order and stops at the first gate that holds:

    seal -> generate -> completeness -> judge -> gate -> persist

Holding is a state, not a failure. Some steps need an act from outside —
labels from a judge that is deliberately not this house, a signature on a
band the checker cannot verify. The line stops there, says exactly what is
missing, writes the record, and exits in a way that says "waiting", not
"broken". Rerun it when the outside act is done and it picks up.

Two rules the line will not bend:

  * It cannot edit its own gate. Thresholds are read, never written. A loop
    permitted to move its threshold optimises the threshold, not the work.
  * It persists on failure too. A line that records only its successes
    teaches the next run a false history — and the most useful results so
    far have been the negative ones.

Workshop-specific work (generation, judging) arrives as commands in the run
spec. The gates are the line's own, so what counts as a complete grid or a
valid threshold does not vary by who is running it.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

from pipeline import cells as cells_gate
from pipeline import gate as gate_check
from pipeline import measure
from pipeline import retain
from pipeline import seal as seal_gate


def _run(command: str, log_path: str | None) -> tuple[int, str]:
    """Run a workshop command unbuffered, streaming to a log the operator can tail."""
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    if log_path:
        with open(log_path, "w") as log:
            rc = subprocess.call(["bash", "-lc", command], stdout=log,
                                 stderr=subprocess.STDOUT, env=env)
        tail = "".join(open(log_path, encoding="utf-8", errors="replace")
                       .readlines()[-15:])
        return rc, tail
    p = subprocess.run(["bash", "-lc", command], capture_output=True, text=True, env=env)
    return p.returncode, (p.stdout + p.stderr)[-2000:]


def _missing_labels(cfg: dict) -> list[str]:
    """Cells whose label file is absent or carries no verdict.

    A label file that exists but says nothing is worse than a missing one:
    it looks answered. Both are reported the same way.
    """
    import glob as _glob
    pattern = cfg.get("expect")
    if not pattern:
        return []
    key = cfg.get("key", "label")
    missing = []
    for cell in sorted(_glob.glob(cfg["cells"])) if cfg.get("cells") else []:
        name = os.path.splitext(os.path.basename(cell))[0]
        path = pattern.replace("{cell}", name)
        if not os.path.exists(path):
            missing.append(f"{name}: no label file ({path})")
            continue
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            missing.append(f"{name}: label file unreadable ({e})")
            continue
        value = d.get(key) if isinstance(d, dict) else None
        if value in (None, "", []):
            missing.append(f"{name}: label file present but empty")
    return missing


class Line:
    def __init__(self, spec: dict, out_dir: str):
        self.spec = spec
        self.out_dir = out_dir
        self.record: dict = {"name": spec.get("name", "unnamed"),
                             "started": time.strftime("%Y-%m-%d %H:%M:%S"),
                             "stages": []}
        os.makedirs(out_dir, exist_ok=True)

    def stage(self, name: str, ok: bool, detail) -> bool:
        self.record["stages"].append({"stage": name, "ok": bool(ok), "detail": detail})
        mark = "ok  " if ok else "HELD"
        print(f"[{mark}] {name}")
        for line in (detail if isinstance(detail, list) else [detail]):
            if line:
                print(f"       {line}")
        return ok

    def persist(self, verdict: str) -> str:
        # Declarations are meant to be deliberate acts, but a spec gets copied
        # and the escape hatch becomes the habit. They ride on the verdict
        # itself, where a reader cannot skip past them.
        declared = [k for k in ("allow_self_judged", "allow_nonstandard")
                    if (self.spec.get("judge", {}).get("journeyman") or {}).get(k)]
        if (self.spec.get("cells") or {}).get("allow_missing"):
            declared.append("allow_missing")
        if declared:
            verdict = f"{verdict} (declared: {', '.join(sorted(declared))})"
        self.record["declared"] = declared
        self.record["verdict"] = verdict
        # Heavy things stay here and are disposable; the record stays light.
        # Reported, never deleted: what to remove is not the line's call.
        self.record["bytes"] = retain.dir_size(self.out_dir)
        for note in retain.check(self.out_dir, self.spec.get("max_run_bytes",
                                                             50_000_000)):
            print(f"[retention] {note}")
        self.record["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
        path = os.path.join(self.out_dir, "run.json")
        json.dump(self.record, open(path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"\nverdict {verdict} · record {path}")
        return path

    # A run that cannot say what it decides is the expensive kind of run: it
    # produces numbers, and what the numbers were for gets decided afterwards,
    # by whoever reads them. The gates below catch instruments; this one
    # catches the operator, which is the failure the instruments cannot see.
    PURPOSE = ("question", "decides", "axis_kind", "owner")

    def run(self) -> int:
        s = self.spec
        purpose = s.get("purpose") or {}
        missing = [k for k in self.PURPOSE if not purpose.get(k)]
        if missing:
            self.stage("purpose", False, [
                f"missing: {', '.join(missing)}",
                "question: what is being asked · decides: what changes on each "
                "outcome · axis_kind: work | diagnostic · owner: whose call the "
                "decision is",
                "a run whose purpose is written after the numbers arrive is a "
                "run whose purpose the numbers chose"])
            self.persist("HELD_WITHOUT_PURPOSE")
            return 4
        if purpose["axis_kind"] not in ("work", "diagnostic"):
            self.stage("purpose", False, [
                f"axis_kind is {purpose['axis_kind']!r}; it must be 'work' or "
                f"'diagnostic'. A diagnostic axis may not carry an acceptance "
                f"verdict — resemblance to a description is not the work."])
            self.persist("HELD_WITHOUT_PURPOSE")
            return 4
        self.record["purpose"] = purpose
        self.stage("purpose", True, [f"{purpose['question']}",
                                     f"decides: {purpose['decides']}",
                                     f"axis: {purpose['axis_kind']} · "
                                     f"owner: {purpose['owner']}"])

        if "seal" in s:
            c = s["seal"]
            profile = (json.load(open(c["profile"], encoding="utf-8"))
                       if c.get("profile") else None)
            problems = seal_gate.verify(c["identity"], profile, c.get("corpus"),
                                        c.get("script"), c.get("deployed"))
            if not self.stage("seal", not problems, problems or "candidate is reproducible"):
                self.persist("HELD_AT_SEAL")
                return 1

        if "generate" in s:
            c = s["generate"]
            log = os.path.join(self.out_dir, "generate.log")
            print(f"       running; follow with: tail -f {log}")
            rc, tail = _run(c["command"], log)
            if not self.stage("generate", rc == 0, tail if rc else f"log {log}"):
                self.persist("FAILED_IN_GENERATION")
                return 1

        if "cells" in s:
            c = s["cells"]
            expected = c.get("expected")
            found, broken, absent = cells_gate.inspect(
                c["pattern"], expected, c.get("min_steps", 2),
                not c.get("closing_optional", False),
                c.get("transcript_key", "messages"),
                c.get("closing_key", "final_text"))
            want = len(expected) if expected else len(found)
            short = want - (len(found) - len(broken))
            allowed = c.get("allow_missing", 0)
            detail = [f"{len(found)} found · {len(found)-len(broken)} complete · {want} expected"]
            detail += [f"INCOMPLETE {x.name}: {why}" for x, why in broken]
            detail += [f"ABSENT {n}" for n in absent]
            if short > 0 and short <= allowed:
                detail.append(f"proceeding {short} short — allowed explicitly; "
                              f"missing cells are not a random sample")
            if not self.stage("completeness", short <= allowed, detail):
                self.persist("HELD_AT_COMPLETENESS")
                return 1

        if "label" in s:
            c = s["label"]
            if c.get("command"):
                log = os.path.join(self.out_dir, "label.log")
                print(f"       running; follow with: tail -f {log}")
                rc, tail = _run(c["command"], log)
                if not self.stage("label", rc == 0, tail if rc else f"log {log}"):
                    self.persist("FAILED_IN_LABELLING")
                    return 1
            missing = _missing_labels(c)
            if missing:
                self.stage("label", False,
                           [f"{len(missing)} cell(s) still unlabelled",
                            "labelling is deliberately outside this house — "
                            "the line waits rather than guessing"]
                           + [f"  {m}" for m in missing[:20]])
                self.persist("HELD_FOR_LABELLING")
                return 3

        if "judge" in s:
            c = s["judge"]
            log = os.path.join(self.out_dir, "judge.log")
            print(f"       running; follow with: tail -f {log}")
            if "journeyman" in c:
                cfg = c["journeyman"]
                rc, summary, tail = measure.run(cfg, log)
                if not self.stage("judge", rc == 0 and summary is not None,
                                  tail if rc or not summary else
                                  [f"report {summary['report']}",
                                   " · ".join(f"{k} {v}" for k, v in summary["axes"].items())]):
                    self.persist("FAILED_IN_JUDGING")
                    return 1
                self.record["measurement"] = summary
                # The benchmark's own warnings are gates here, not footnotes.
                bad = measure.problems(summary, cfg)
                if not self.stage("measurement is comparable", not bad, bad or
                                  "judged by a separate endpoint, standard scenes"):
                    self.persist("HELD_AT_MEASUREMENT")
                    return 1
            else:
                rc, tail = _run(c["command"], log)
                if not self.stage("judge", rc == 0, tail if rc else f"log {log}"):
                    self.persist("FAILED_IN_JUDGING")
                    return 1

        if "gate" in s and purpose["axis_kind"] == "diagnostic":
            self.stage("gate", True, ["skipped: this run was declared "
                                      "diagnostic, so no acceptance verdict "
                                      "is drawn from it"])
            self.persist("DIAGNOSTIC")
            return 0

        if "gate" in s:
            path = s["gate"]["file"]
            measured = (self.record.get("measurement") or {}).get("axes") or {}
            incumbent = s["gate"].get("incumbent_axes")
            text = open(path, encoding="utf-8").read()
            results, detail, verdicts = [], [], []
            for title, body in gate_check.sections(text):
                if not (gate_check.DECIDES.search(body)
                        or gate_check.field(body, "band-command")):
                    continue
                verdict, notes = gate_check.check_section(body)
                results.append(verdict)
                detail.append(f"[{verdict}] {title}: " + "; ".join(n for n in notes if n))
                if verdict in ("PASS", "UNBOUND") and measured:
                    applied, why = gate_check.evaluate_section(body, measured, incumbent)
                    verdicts.append((title, applied))
                    detail.append(f"    -> {applied}: " + "; ".join(why))
            bad = [v for v in results if v == "FAIL"]
            unsure = [v for v in results if v in ("UNVERIFIABLE", "UNBOUND")]
            if not self.stage("gate", not bad, detail):
                self.persist("HELD_AT_GATE")
                return 1
            if unsure:
                self.persist("NEEDS_SIGNATURE")
                return 2
            if verdicts:
                self.record["axis_verdicts"] = [
                    {"gate": t2, "verdict": v} for t2, v in verdicts]
                if any(v == "REJECT" for _t, v in verdicts):
                    self.persist("REJECTED")
                    return 1
                if all(v == "ACCEPT" for _t, v in verdicts):
                    self.persist("ACCEPTED")
                    return 0
                self.persist("UNRESOLVED")
                return 0

        self.persist("COMPLETE")
        return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="run one campaign through the line")
    ap.add_argument("spec", help="run spec (JSON)")
    ap.add_argument("--out", default="runs", help="where the run record is written")
    a = ap.parse_args(argv)
    spec = json.load(open(a.spec, encoding="utf-8"))
    out = os.path.join(a.out, spec.get("name", "run"))
    return Line(spec, out).run()


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.exit(main())
