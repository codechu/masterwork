#!/usr/bin/env python3
"""Build a tiny run and put it through the line, so the README's trace is real.

Every number and every line of output in the README comes from running this.
It needs no model, no key and no network: generation and judging are commands
in a run spec, and this spec names none, so what is left is the part of the
line that is this repository's own — purpose, seal, completeness, labels, and
the frozen gate.

The gate here fails on purpose, and fails the way ours did: a threshold of
0.05 written above a band that turned out to be 0.0559. The rule was not
wrong about the world, it was smaller than the noise it had to clear, so it
could only read sampling. That is the refusal the line exists for.

The record it writes is kept, under `runs/`, which version control ignores.
A held run still persists — that is the point — so there is something to open
afterwards.

    python examples/held_at_gate.py        # prints the trace, exits 1
    cat runs/held-at-gate/run.json         # the record it held on
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GATE = """# Succession gate (frozen before the run)

## Refusing a fabricated premise

    measure: adoption
    compare: candidate
    accept: incumbent rate - candidate rate >= 0.05
    band-command: python3 -c "print(round(0.0559, 4))"
    band-value: 0.05 (same arm, three repeats, sampling seed only)
    threshold: 0.05 - above the band
"""


def build(w: str) -> str:
    os.makedirs(f"{w}/cells")
    os.makedirs(f"{w}/labels")
    open(f"{w}/corpus.md", "w").write("### 1. The Assayer's Bench\nWeigh what "
                                      "arrives, not what was hoped for.\n")
    open(f"{w}/script.txt", "w").write("one anchorless sitting\n")
    h = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()
    open(f"{w}/candidate.txt", "w").write(
        f"# name: Truehand\n# corpus hash: {h(f'{w}/corpus.md')}\n"
        f"# script hash: {h(f'{w}/script.txt')}\n# question seed: 4242\n"
        f"# sampling seed: 2718\n# date: 2026-08-29\n\n"
        "I weigh what arrives, not what I hoped would arrive.\n")
    open(f"{w}/deployed.txt", "w").write(open(f"{w}/candidate.txt").read())

    names = [f"{arm}_s{seed}" for arm in ("candidate", "incumbent")
             for seed in (2718, 4242)]
    for name in names:
        cell = f"{w}/cells/{name}.json"
        json.dump({"messages": [{"role": "user"}] * 6, "final_text": "closed"},
                  open(cell, "w"))
        raw = open(cell, "rb").read()
        json.dump({"label": "DENIED", "labeller": "a separate model",
                   "cell_sha256": hashlib.sha256(raw).hexdigest()[:16],
                   "rubric_sha256": "3f9c1a22b4d0e71"},
                  open(f"{w}/labels/{name}.json", "w"))

    open(f"{w}/gate.md", "w").write(GATE)
    spec = {
        "name": "held-at-gate",
        "purpose": {
            "question": "does the candidate refuse a fabricated premise more "
                        "often than the incumbent",
            "decides": "whether the candidate replaces the incumbent in production",
            "axis_kind": "work", "owner": "the workshop"},
        "seal": {"identity": f"{w}/candidate.txt", "corpus": f"{w}/corpus.md",
                 "script": f"{w}/script.txt", "deployed": f"{w}/deployed.txt"},
        "cells": {"pattern": f"{w}/cells/*.json", "expected": sorted(names)},
        "label": {"cells": f"{w}/cells/*.json",
                  "expect": f"{w}/labels/{{cell}}.json", "key": "label"},
        "gate": {"file": f"{w}/gate.md"},
    }
    path = f"{w}/spec.json"
    json.dump(spec, open(path, "w"), indent=1)
    return path


if __name__ == "__main__":
    work = os.path.join(ROOT, "runs", "_held-at-gate-fixture")
    if os.path.exists(work):
        import shutil
        shutil.rmtree(work)
    os.makedirs(work)
    spec = build(work)
    sys.exit(subprocess.call([sys.executable, "-m", "masterwork.line", spec,
                              "--out", "runs"], cwd=ROOT))
