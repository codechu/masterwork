"""The line: one run, every gate, no step left to memory.

Producing a candidate is mechanical, and each mechanical step here has been
skipped by hand at least once. Every skip produced a number that looked real
and was not: an unverified deployed copy, a grid quietly short of cells, a
threshold inside its own noise, a negative result never written down.

The line runs the stages in order and stops at the first gate that holds:

    seal -> generate -> completeness -> judge -> gate -> persist

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
        self.record["verdict"] = verdict
        self.record["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
        path = os.path.join(self.out_dir, "run.json")
        json.dump(self.record, open(path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"\nverdict {verdict} · record {path}")
        return path

    def run(self) -> int:
        s = self.spec

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

        if "judge" in s:
            log = os.path.join(self.out_dir, "judge.log")
            print(f"       running; follow with: tail -f {log}")
            rc, tail = _run(s["judge"]["command"], log)
            if not self.stage("judge", rc == 0, tail if rc else f"log {log}"):
                self.persist("FAILED_IN_JUDGING")
                return 1

        if "gate" in s:
            path = s["gate"]["file"]
            text = open(path, encoding="utf-8").read()
            results, detail = [], []
            for title, body in gate_check.sections(text):
                if not (gate_check.DECIDES.search(body)
                        or gate_check.field(body, "band-command")):
                    continue
                verdict, notes = gate_check.check_section(body)
                results.append(verdict)
                detail.append(f"[{verdict}] {title}: " + "; ".join(n for n in notes if n))
            bad = [v for v in results if v == "FAIL"]
            unsure = [v for v in results if v == "UNVERIFIABLE"]
            if not self.stage("gate", not bad, detail):
                self.persist("HELD_AT_GATE")
                return 1
            if unsure:
                self.persist("NEEDS_SIGNATURE")
                return 2

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
