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
