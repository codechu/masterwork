"""What survives a run, and what does not.

A line that keeps everything becomes a disk problem, and then a slow one:
every future search walks the transcripts of runs nobody will reopen. A
line that keeps nothing cannot defend a number six weeks later. The split
that works is not "keep less", it is: **heavy artefacts stay local and
disposable, light evidence is archived on purpose.**

Local and disposable — transcripts, judge logs, per-cell records, the
benchmark's run directory. They live under a runs directory that version
control ignores, and they are re-derivable: the seal names the corpus, the
script and both seeds.

Archived on purpose — the run record and the benchmark's report. Both are
kilobytes. Together they carry the seal, the grid, the axes, the gate and
the verdict, which is everything a later disagreement can be settled with.

Excerpts are capped rather than dropped, so a record can quote without
carrying. Three hundred characters is enough to recognise an answer and far
too little to store one.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

EXCERPT = 300
# What is worth copying out of a run directory when the run is over.
ARCHIVE = ("run.json", "report.json")


def excerpt(text: str | None, limit: int = EXCERPT) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[:limit] + "…"


def dir_size(path: str) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def largest(path: str, n: int = 5) -> list[tuple[int, str]]:
    found = []
    for root, _dirs, files in os.walk(path):
        for f in files:
            p = os.path.join(root, f)
            try:
                found.append((os.path.getsize(p), p))
            except OSError:
                pass
    return sorted(found, reverse=True)[:n]


def check(path: str, max_bytes: int) -> list[str]:
    """Report — do not delete. Deciding what to remove is not the line's call."""
    size = dir_size(path)
    if size <= max_bytes:
        return []
    out = [f"run directory is {size/1e6:.1f} MB, over the {max_bytes/1e6:.1f} MB "
           f"mark — this is local and disposable, but say so before it grows a habit"]
    out += [f"  {s/1e6:.1f} MB {p}" for s, p in largest(path)]
    return out


def archive(run_dir: str, dest: str) -> list[str]:
    """Copy only the light, decision-bearing files out of a run directory."""
    os.makedirs(dest, exist_ok=True)
    copied = []
    for root, _dirs, files in os.walk(run_dir):
        for f in files:
            if f in ARCHIVE:
                src = os.path.join(root, f)
                rel = os.path.relpath(src, run_dir).replace(os.sep, "-")
                shutil.copy2(src, os.path.join(dest, rel))
                copied.append(rel)
    return copied


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="masterwork retain", description="run-directory retention")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="report size without deleting anything")
    c.add_argument("run_dir")
    c.add_argument("--max-mb", type=float, default=50.0)
    a2 = sub.add_parser("archive", help="copy out the kilobyte-sized evidence")
    a2.add_argument("run_dir")
    a2.add_argument("dest")
    a = ap.parse_args(argv)

    if a.cmd == "check":
        problems = check(a.run_dir, int(a.max_mb * 1e6))
        print(f"{dir_size(a.run_dir)/1e6:.2f} MB  {a.run_dir}")
        for p in problems:
            print(p)
        return 0
    copied = archive(a.run_dir, a.dest)
    if not copied:
        print(f"nothing to archive: no {' or '.join(ARCHIVE)} under {a.run_dir}")
        return 1
    total = sum(os.path.getsize(os.path.join(a.dest, c)) for c in copied)
    print(f"archived {len(copied)} file(s), {total/1024:.1f} KB -> {a.dest}")
    for c in copied:
        print(f"  {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
