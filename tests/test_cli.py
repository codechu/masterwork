"""The one door: the mark, the flags, and the judge it cannot work without.

Every check here is for something the line did not do when it was only a
set of module paths: it had no name to type, no version to answer with,
no way to be asked what it is, and it met a missing journeyman with a
shell's "command not found" rather than with a sentence.
"""
import contextlib
import io
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import masterwork as mw  # noqa: E402
from pipeline import measure  # noqa: E402


def test_box_is_square_at_any_version():
    for v in ("0.0.0", "0.10.12", "1.0.0-rc1", "12.34.56"):
        widths = {len(l) for l in mw.banner(v).split("\n")}
        assert len(widths) == 1, f"ragged box at v{v}: {sorted(widths)}"


def test_bare_call_introduces_the_line_on_stdout():
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = mw.main([])
    assert code == 0
    assert "MASTERWORK" in out.getvalue()
    assert "ceremony" in out.getvalue()
    assert err.getvalue() == ""


def test_unknown_command_is_an_error():
    with contextlib.redirect_stderr(io.StringIO()):
        with pytest.raises(SystemExit) as e:
            mw.main(["nosuchstage"])
    assert e.value.code == 2


def test_every_stage_is_reachable_by_name():
    import importlib
    for name, (module, blurb) in mw.COMMANDS.items():
        m = importlib.import_module(module)
        assert hasattr(m, "main"), f"{name} -> {module} has no main()"
        assert blurb, f"{name} has no help"


def test_a_missing_judge_is_named_not_thrown():
    version, why = measure.tool({"executable": "nosuch-journeyman-binary"})
    assert version is None
    assert "not on PATH" in why
    assert "journeyman" in why
    # the stop has to say what to do, not only what is wrong
    assert "install" in why.lower()
