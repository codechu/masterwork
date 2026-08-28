"""Retention: heavy stays local and disposable, light is archived on purpose."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import retain  # noqa: E402


def test_archive_takes_only_the_kilobyte_evidence():
    with tempfile.TemporaryDirectory() as tmp:
        run = os.path.join(tmp, "run-a")
        os.makedirs(run)
        json.dump({"verdict": "COMPLETE"}, open(os.path.join(run, "run.json"), "w"))
        json.dump({"axes": {}}, open(os.path.join(run, "report.json"), "w"))
        open(os.path.join(run, "judge.log"), "w").write("x" * 100000)
        open(os.path.join(run, "transcript.json"), "w").write("y" * 100000)
        dest = os.path.join(tmp, "archive")
        copied = retain.archive(run, dest)
        assert sorted(copied) == ["report.json", "run.json"]
        assert retain.dir_size(dest) < 1000


def test_oversize_is_reported_not_deleted():
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "big.log"), "w").write("x" * 2000)
        problems = retain.check(tmp, 1000)
        assert problems and "over the" in problems[0]
        assert os.path.exists(os.path.join(tmp, "big.log"))


def test_excerpt_quotes_without_carrying():
    assert retain.excerpt("a" * 1000).endswith("…")
    assert len(retain.excerpt("a" * 1000)) == retain.EXCERPT + 1
    assert retain.excerpt("short") == "short"
