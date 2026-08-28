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
    measure: adoption
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
        "purpose": {"question": "does the line hold where it should",
                    "decides": "whether the stage order is right",
                    "axis_kind": "work", "owner": "house"},
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
            ["purpose", "seal", "generate", "completeness", "judge", "gate"]


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


def test_self_judged_measurement_never_reaches_the_gate():
    """journeyman says 'not comparable'; the line treats that as a gate."""
    import pipeline.line as line_mod
    with tempfile.TemporaryDirectory() as tmp:
        spec = build(tmp)
        report = os.path.join(tmp, "report.json")
        json.dump({"axes": {"grounding": {"score": 1.0, "n": 1}},
                   "self_judged": True}, open(report, "w"))
        spec["judge"] = {"journeyman": {"endpoint": "http://x/v1",
                                        "executable": "true", "report": report,
                                        "skip_preflight": True}}
        line = line_mod.Line(spec, os.path.join(tmp, "out"))
        assert line.run() == 1
        rec = json.load(open(os.path.join(tmp, "out", "run.json")))
        assert rec["verdict"] == "HELD_AT_MEASUREMENT"
        assert not any(s["stage"] == "gate" for s in rec["stages"])


def _labelled_spec(tmp, labels):
    spec = build(tmp)
    cells_dir = os.path.dirname(spec["cells"]["pattern"])
    lab_dir = os.path.join(tmp, "labels")
    os.makedirs(lab_dir, exist_ok=True)
    for name, value in labels.items():
        json.dump({"label": value}, open(os.path.join(lab_dir, name + ".json"), "w"))
    spec["label"] = {"cells": os.path.join(cells_dir, "*.json"),
                     "expect": os.path.join(lab_dir, "{cell}.json")}
    spec["judge"]["command"] = "echo JUDGED > " + os.path.join(tmp, "judged")
    return spec


def test_missing_labels_hold_the_line_before_judging():
    """Labelling is outside this house; waiting beats guessing."""
    import pipeline.line as line_mod
    with tempfile.TemporaryDirectory() as tmp:
        spec = _labelled_spec(tmp, {"c0": "DENIED"})   # c1 unlabelled
        line = line_mod.Line(spec, os.path.join(tmp, "out"))
        assert line.run() == 3
        assert not os.path.exists(os.path.join(tmp, "judged"))
        rec = json.load(open(os.path.join(tmp, "out", "run.json")))
        assert rec["verdict"] == "HELD_FOR_LABELLING"


def test_empty_label_counts_as_missing():
    """A file that exists and says nothing looks answered. It is not."""
    import pipeline.line as line_mod
    with tempfile.TemporaryDirectory() as tmp:
        spec = _labelled_spec(tmp, {"c0": "DENIED", "c1": ""})
        assert line_mod.Line(spec, os.path.join(tmp, "out")).run() == 3


def test_complete_labels_let_the_run_continue():
    import pipeline.line as line_mod
    with tempfile.TemporaryDirectory() as tmp:
        spec = _labelled_spec(tmp, {"c0": "DENIED", "c1": "ADOPTED"})
        assert line_mod.Line(spec, os.path.join(tmp, "out")).run() == 0
        assert os.path.exists(os.path.join(tmp, "judged"))


def test_a_run_without_a_stated_purpose_is_held():
    """The gates catch instruments; this one catches the operator."""
    import pipeline.line as line_mod
    with tempfile.TemporaryDirectory() as tmp:
        spec = build(tmp)
        spec.pop("purpose")
        line = line_mod.Line(spec, os.path.join(tmp, "out"))
        assert line.run() == 4
        assert json.load(open(os.path.join(tmp, "out", "run.json")))["verdict"] \
            == "HELD_WITHOUT_PURPOSE"


def test_a_diagnostic_run_draws_no_verdict():
    """Resemblance to a description is not the work, and may not accept."""
    import pipeline.line as line_mod
    with tempfile.TemporaryDirectory() as tmp:
        spec = build(tmp)
        spec["purpose"] = {"question": "where does it drift", "decides": "nothing",
                           "axis_kind": "diagnostic", "owner": "house"}
        line = line_mod.Line(spec, os.path.join(tmp, "out"))
        assert line.run() == 0
        rec = json.load(open(os.path.join(tmp, "out", "run.json")))
        assert rec["verdict"] == "DIAGNOSTIC"
