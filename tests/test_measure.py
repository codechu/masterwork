"""The seam to journeyman: hand the piece over, refuse to grade it here."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import measure  # noqa: E402


def test_command_carries_the_piece_and_a_separate_judge():
    cmd = measure.build_command({
        "endpoint": "http://x/v1", "model": "m", "system_file": "candidate.txt",
        "judge_endpoint": "http://y/v1", "seeds": "1,2"})
    assert cmd[:2] == ["journeyman", "run"]
    assert "--system-file" in cmd and "candidate.txt" in cmd
    assert "--judge" in cmd and "http://y/v1" in cmd


def test_self_judged_report_may_not_be_gated():
    """The maker grading his own piece, with extra steps."""
    summary = {"self_judged": True, "axes": {"grounding": 1.0}, "nonstandard": None,
               "invalid_cells": None}
    assert any("self_judged" in p for p in measure.problems(summary, {}))
    assert not measure.problems(summary, {"allow_self_judged": True})


def test_empty_axes_is_not_a_pass():
    summary = {"self_judged": False, "axes": {}, "nonstandard": None,
               "invalid_cells": None}
    assert any("nothing was measured" in p for p in measure.problems(summary, {}))


def test_reads_the_report_contract():
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "report.json")
        json.dump({"axes": {"grounding": {"score": 1.0, "n": 2},
                            "wall-pricing": {"score": 0.5, "n": 2}},
                   "self_judged": False, "seal": {"bench": "0.1.0"}}, open(p, "w"))
        s = measure.read_report(p)
        assert s["axes"] == {"grounding": 1.0, "wall-pricing": 0.5}
        assert s["n"]["grounding"] == 2 and s["seal"]["bench"] == "0.1.0"


def test_newest_report_is_found_under_a_runs_dir():
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "run-a")
        os.makedirs(d)
        p = os.path.join(d, "report.json")
        json.dump({"axes": {}}, open(p, "w"))
        assert measure.newest_report(tmp) == p
