"""Line tests: the order of the gates, and that a held run still records."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.line import Line  # noqa: E402

SEALED = """# name: Example
# corpus hash: {corpus}
# script hash: 0123456789abcdef0123456789abcdef
# question seed: 0 · sampling seed: 7
# date: 2026-08-28

the piece
"""

# The band command must COMPUTE the value; a command that prints a number it
# already contains is a quotation and the checker calls it UNVERIFIABLE. This
# fixture was written the lazy way first and the checker caught it.
GATE_OK = """# gate
## Axis
    accept: difference >= 0.33
    band-command: python3 -c "import math;print(round(math.sqrt(0.0729), 4))"
    band-value: 0.27
    threshold: 0.33 — above the band
"""

GATE_INSIDE_BAND = GATE_OK.replace("threshold: 0.33 — above the band",
                                   "threshold: 0.10 — above the band")


def build(tmp, gate_text=GATE_OK, closing="done", cells_n=2):
    corpus = os.path.join(tmp, "corpus.md")
    open(corpus, "w").write("tales")
    from pipeline import seal
    identity = os.path.join(tmp, "candidate.txt")
    open(identity, "w").write(SEALED.format(corpus=seal.file_hash(corpus)))
    cells_dir = os.path.join(tmp, "cells")
    os.makedirs(cells_dir, exist_ok=True)
    for i in range(cells_n):
        json.dump({"messages": [{}, {}, {}], "final_text": closing},
                  open(os.path.join(cells_dir, f"c{i}.json"), "w"))
    gate_file = os.path.join(tmp, "gate.md")
    open(gate_file, "w").write(gate_text)
    return {
        "name": "test",
        "seal": {"identity": identity, "corpus": corpus},
        "generate": {"command": "true"},
        "cells": {"pattern": os.path.join(cells_dir, "*.json")},
        "judge": {"command": "true"},
        "gate": {"file": gate_file},
    }


def test_clean_run_completes_and_records():
    with tempfile.TemporaryDirectory() as tmp:
        line = Line(build(tmp), os.path.join(tmp, "out"))
        assert line.run() == 0
        rec = json.load(open(os.path.join(tmp, "out", "run.json")))
        assert rec["verdict"] == "COMPLETE"
        assert [s["stage"] for s in rec["stages"]] == \
            ["seal", "generate", "completeness", "judge", "gate"]


def test_stale_deployed_copy_stops_before_generating():
    """The gate must fire before any GPU time is spent."""
    with tempfile.TemporaryDirectory() as tmp:
        spec = build(tmp)
        stale = os.path.join(tmp, "deployed.txt")
        open(stale, "w").write(open(spec["seal"]["identity"]).read() + "drift")
        spec["seal"]["deployed"] = stale
        spec["generate"]["command"] = "echo SHOULD-NOT-RUN > " + os.path.join(tmp, "ran")
        line = Line(spec, os.path.join(tmp, "out"))
        assert line.run() == 1
        assert not os.path.exists(os.path.join(tmp, "ran"))
        rec = json.load(open(os.path.join(tmp, "out", "run.json")))
        assert rec["verdict"] == "HELD_AT_SEAL"


def test_short_grid_holds_before_judging():
    with tempfile.TemporaryDirectory() as tmp:
        spec = build(tmp, closing="")
        spec["judge"]["command"] = "echo SHOULD-NOT-RUN > " + os.path.join(tmp, "judged")
        line = Line(spec, os.path.join(tmp, "out"))
        assert line.run() == 1
        assert not os.path.exists(os.path.join(tmp, "judged"))
        assert json.load(open(os.path.join(tmp, "out", "run.json")))["verdict"] \
            == "HELD_AT_COMPLETENESS"


def test_threshold_inside_band_holds_and_is_recorded():
    """A negative result is a result: it must reach the record."""
    with tempfile.TemporaryDirectory() as tmp:
        line = Line(build(tmp, GATE_INSIDE_BAND), os.path.join(tmp, "out"))
        assert line.run() == 1
        rec = json.load(open(os.path.join(tmp, "out", "run.json")))
        assert rec["verdict"] == "HELD_AT_GATE"
        assert any("FAIL" in d for d in rec["stages"][-1]["detail"])
