"""Completeness tests. The gate must never drop a cell on its own."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import cells  # noqa: E402


def make(tmp, name, steps=4, closing="done"):
    p = os.path.join(tmp, name + ".json")
    json.dump({"messages": [{"role": "user"}] * steps, "final_text": closing},
              open(p, "w"))
    return p


def test_full_grid_passes():
    with tempfile.TemporaryDirectory() as tmp:
        for n in ("a_1", "a_2"):
            make(tmp, n)
        assert cells.main([os.path.join(tmp, "*.json")]) == 0


def test_missing_closing_is_held_not_dropped():
    """The round-limit case: full transcript, no answer. Held, not averaged."""
    with tempfile.TemporaryDirectory() as tmp:
        make(tmp, "a_1")
        make(tmp, "a_2", closing="")
        assert cells.main([os.path.join(tmp, "*.json")]) == 1


def test_allowance_must_be_explicit():
    with tempfile.TemporaryDirectory() as tmp:
        make(tmp, "a_1")
        make(tmp, "a_2", closing="")
        assert cells.main([os.path.join(tmp, "*.json"), "--allow-missing", "1"]) == 0


def test_absent_cell_is_named():
    """A cell that never produced a file is invisible to a glob — name it."""
    with tempfile.TemporaryDirectory() as tmp:
        make(tmp, "a_1")
        expect = os.path.join(tmp, "expect.txt")
        open(expect, "w").write("a_1\na_2\n")
        assert cells.main([os.path.join(tmp, "*.json"), "--expect", expect]) == 1


def test_a_pattern_that_matches_nothing_is_not_a_complete_grid():
    """A mistyped cells pattern used to pass as a finished run."""
    with tempfile.TemporaryDirectory() as tmp:
        assert cells.main([os.path.join(tmp, "nothing-here", "*.json")]) == 1


def test_a_corrupt_cell_is_broken_whatever_the_thresholds():
    """With min-steps 0 and closing optional, garbage used to count as a cell."""
    with tempfile.TemporaryDirectory() as tmp:
        make(tmp, "a_1")
        open(os.path.join(tmp, "a_2.json"), "w").write("{ truncated")
        found, broken, absent = cells.inspect(
            os.path.join(tmp, "*.json"), None, 0, False, "messages", "final_text")
        assert [c.name for c, _ in broken] == ["a_2"]
        assert "could not be read" in broken[0][1]


def test_a_corrupt_cell_is_not_reported_as_absent_as_well():
    """It was named with its extension on one path and without on the other,
    so one file told the operator two different stories about itself."""
    with tempfile.TemporaryDirectory() as tmp:
        make(tmp, "a_1")
        open(os.path.join(tmp, "a_2.json"), "w").write("{ truncated")
        _found, broken, absent = cells.inspect(
            os.path.join(tmp, "*.json"), ["a_1", "a_2"], 2, True,
            "messages", "final_text")
        assert absent == [] and [c.name for c, _ in broken] == ["a_2"]
