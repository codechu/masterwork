"""The completeness gate: a run that lost cells is not a smaller run.

A battery is a grid — cases crossed with seeds. When some of those cells
come back empty, the tempting move is to average whatever arrived. That is
not a smaller sample of the same thing: cells fail for reasons that
correlate with what is being measured, so dropping them quietly moves the
number in a direction nobody chose.

Two failures this gate exists for, both observed:

  * Eight cells vanished from a battery and the loss was noticed only by
    counting by hand, after the verdict had been written.
  * Cells that hit the harness round limit came back with a full transcript
    and no closing text. Read as "empty" they looked like sloppy work; rerun
    with a higher limit, every one of them closed correctly. They were the
    longest, most careful runs in the battery — exactly the ones whose
    removal flatters the score.

So the gate does not drop anything on its own. It reports what is missing
and stops. Proceeding without a full grid requires saying so out loud
(--allow-missing N), and the allowance is echoed into the report so it
survives into the record.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from dataclasses import dataclass


@dataclass
class Cell:
    name: str
    path: str
    steps: int
    closing: int

    def problem(self, min_steps: int, need_closing: bool) -> str | None:
        if self.steps < min_steps:
            return f"transcript too short ({self.steps} < {min_steps})"
        if need_closing and self.closing == 0:
            return "no closing text — the run stopped before answering"
        return None


def read_cell(path: str, transcript_key: str, closing_key: str) -> Cell:
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return Cell(os.path.basename(path), path, 0, 0)
    steps = len(d.get(transcript_key) or [])
    closing = len((d.get(closing_key) or "").strip())
    return Cell(os.path.splitext(os.path.basename(path))[0], path, steps, closing)


def inspect(pattern: str, expected: list[str] | None, min_steps: int,
            need_closing: bool, transcript_key: str, closing_key: str):
    cells = [read_cell(p, transcript_key, closing_key)
             for p in sorted(glob.glob(pattern))]
    by_name = {c.name: c for c in cells}
    broken = [(c, c.problem(min_steps, need_closing)) for c in cells]
    broken = [(c, why) for c, why in broken if why]
    absent = [n for n in (expected or []) if n not in by_name]
    return cells, broken, absent


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="completeness gate for a battery")
    ap.add_argument("pattern", help="glob of per-cell record files")
    ap.add_argument("--expect", help="file listing expected cell names, one per line")
    ap.add_argument("--min-steps", type=int, default=2,
                    help="a transcript shorter than this did not run")
    ap.add_argument("--no-closing-required", action="store_true",
                    help="accept cells with no closing text (say why in the record)")
    ap.add_argument("--allow-missing", type=int, default=0,
                    help="proceed with this many cells short — an explicit, "
                         "recorded choice, never a default")
    ap.add_argument("--transcript-key", default="messages")
    ap.add_argument("--closing-key", default="final_text")
    a = ap.parse_args(argv)

    expected = None
    if a.expect:
        expected = [l.strip() for l in open(a.expect, encoding="utf-8")
                    if l.strip() and not l.startswith("#")]

    cells, broken, absent = inspect(
        a.pattern, expected, a.min_steps, not a.no_closing_required,
        a.transcript_key, a.closing_key)

    good = len(cells) - len(broken)
    want = len(expected) if expected else len(cells)
    print(f"cells found {len(cells)} · complete {good} · expected {want}")
    for c, why in broken:
        print(f"  INCOMPLETE {c.name}: {why}")
    for n in absent:
        print(f"  ABSENT     {n}")

    short = want - good
    if short <= 0:
        print("grid complete")
        return 0
    if short <= a.allow_missing:
        print(f"proceeding {short} cell(s) short — allowed explicitly "
              f"(--allow-missing {a.allow_missing}); record this alongside the result, "
              f"missing cells are not a random sample")
        return 0
    print(f"\nHELD: {short} cell(s) short of the grid. Fix the run, or state the "
          f"allowance with --allow-missing and say why in the record.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
