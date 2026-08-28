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
    # normalised: the benchmark appends /v1/chat/completions itself
    assert "--judge" in cmd and "http://y" in cmd


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


def test_endpoint_with_v1_is_normalised():
    """The benchmark appends /v1/chat/completions; a /v1 suffix 404s every
    cell, and a run of 404s completes and reports nothing."""
    assert measure.base_endpoint("http://h:4567/v1") == "http://h:4567"
    assert measure.base_endpoint("http://h:4567/v1/chat/completions") == "http://h:4567"
    assert measure.base_endpoint("http://h:4567/") == "http://h:4567"
    cmd = measure.build_command({"endpoint": "http://h:4567/v1",
                                 "judge_endpoint": "http://j:8000/v1"})
    assert "http://h:4567" in cmd and "http://j:8000" in cmd


def test_nonstandard_needs_a_declaration_too():
    s = {"self_judged": False, "axes": {"a": 1.0}, "nonstandard": "scenes=x",
         "invalid_cells": None}
    assert any("non-standard" in p for p in measure.problems(s, {}))
    assert not measure.problems(s, {"allow_nonstandard": True})


def test_bare_model_run_is_caught():
    """--system-file is optional over there: lose it and you measure the base
    model while the report looks entirely normal."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        piece = os.path.join(tmp, "candidate.txt")
        open(piece, "w").write("the piece")
        s = {"self_judged": False, "axes": {"a": 1.0}, "nonstandard": None,
             "invalid_cells": None, "seal": {"agent_system_md5": None}}
        assert any("bare model" in p for p in measure.problems(s, {"system_file": piece}))


def test_different_piece_is_caught():
    import hashlib
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        piece = os.path.join(tmp, "candidate.txt")
        open(piece, "w").write("the piece")
        s = {"self_judged": False, "axes": {"a": 1.0}, "nonstandard": None,
             "invalid_cells": None, "seal": {"agent_system_md5": "ffffffffffff"}}
        out = measure.problems(s, {"system_file": piece})
        assert any("different piece" in p for p in out)
        good = {**s, "seal": {"agent_system_md5":
                              hashlib.md5(open(piece, "rb").read()).hexdigest()[:12]}}
        assert not measure.problems(good, {"system_file": piece})


def test_unreachable_endpoint_is_reported_before_the_run():
    assert measure.reachable("http://127.0.0.1:1/v1", timeout=1)
