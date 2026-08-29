"""Training data. The refusals matter more than the output."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import pairs  # noqa: E402


def cell(cid, scene, seed, verdict, positive="good", invalid=False):
    # The seal here mirrors what the benchmark actually writes per cell: the
    # agent's definition, fixed before judging. It carries no judge field —
    # the earlier fixture invented one, and the refusal that read it could
    # therefore never fire against a real run.
    return {"cell_id": cid, "scene": scene, "seed": seed, "invalid": invalid,
            "invalid_reason": "404" if invalid else None,
            "seal": {"agent_system_md5": "0" * 32, "bench": "0.1.0"},
            "verdicts": {"grounding": {"verdict": verdict, "positive": positive,
                                       "na_means": "failure"}},
            "messages": [{"role": "system", "content": "IDENTITY"},
                         {"role": "user", "content": f"scene {scene}"},
                         {"role": "assistant", "content": f"work {cid}"}]}


def test_a_winner_and_a_loser_become_a_pair():
    got, _ = pairs.build([cell("a", "s1", 1, "good"), cell("b", "s1", 2, "bad")],
                         "grounding", min_gap=0.5, strip_system=False,
                         allow_self_judged=True)
    assert len(got) == 1
    p = got[0]
    assert p["provenance"]["chosen_cell"] == "a"
    assert p["provenance"]["rejected_cell"] == "b"
    assert p["chosen"][0]["content"] == "work a"
    assert p["prompt"][0]["role"] == "system"


def test_gap_below_the_judges_spread_is_refused():
    """A judge that moves on identical runs will label equivalents winner and
    loser; pairing those teaches the model to imitate the noise."""
    got, _ = pairs.build([cell("a", "s1", 1, "good"), cell("b", "s1", 2, "bad")],
                         "grounding", min_gap=1.5, strip_system=False,
                         allow_self_judged=True)
    assert got == []


def _run_dir(tmp, self_judged):
    """A run directory shaped like the benchmark's: cells/, and a report on top."""
    import json as _json
    os.makedirs(os.path.join(tmp, "cells"), exist_ok=True)
    for c in (cell("a", "s1", 1, "good"), cell("b", "s1", 2, "bad")):
        _json.dump(c, open(os.path.join(tmp, "cells", c["cell_id"] + ".json"), "w"))
    _json.dump({"self_judged": self_judged, "axes": {}},
               open(os.path.join(tmp, "report.json"), "w"))
    return tmp


def test_self_judged_is_read_from_the_report_not_the_cell_seal():
    """The stamp lives at the top of report.json; cells never carry it."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        assert pairs.run_is_self_judged(_run_dir(tmp, True)) is True
    with tempfile.TemporaryDirectory() as tmp:
        assert pairs.run_is_self_judged(_run_dir(tmp, False)) is False
    with tempfile.TemporaryDirectory() as tmp:
        assert pairs.run_is_self_judged(tmp) is None    # unchecked, not absent


def test_a_self_judged_run_cuts_no_pairs():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        run = _run_dir(os.path.join(tmp, "run"), True)
        out = os.path.join(tmp, "pairs.jsonl")
        rc = pairs.main([run, "--axis", "grounding", "--out", out,
                         "--min-gap", "0.5"])
        assert rc == 1 and not os.path.exists(out)
        assert pairs.main([run, "--axis", "grounding", "--out", out,
                           "--min-gap", "0.5", "--allow-self-judged"]) == 0


def test_invalid_cells_are_named_and_dropped():
    cells = [cell("a", "s1", 1, "good"), cell("b", "s1", 2, "bad", invalid=True)]
    got, notes = pairs.build(cells, "grounding", 0.5, False, True)
    assert got == [] and any("invalid cell" in n for n in notes)


def test_pairs_never_cross_scenes():
    cells = [cell("a", "s1", 1, "good"), cell("b", "s2", 2, "bad")]
    got, _ = pairs.build(cells, "grounding", 0.5, False, True)
    assert got == []


def test_stripping_the_identity_leaves_the_behaviour():
    got, _ = pairs.build([cell("a", "s1", 1, "good"), cell("b", "s1", 2, "bad")],
                         "grounding", 0.5, strip_system=True, allow_self_judged=True)
    assert all(m["role"] != "system" for m in got[0]["prompt"])
    assert got[0]["prompt"][0]["content"] == "scene s1"


def test_supervised_set_takes_winners_only():
    cells = [cell("a", "s1", 1, "good"), cell("b", "s1", 2, "bad")]
    rows = pairs.winners(cells, "grounding", floor=1.0, strip_system=False,
                         allow_self_judged=True)
    assert len(rows) == 1 and rows[0]["provenance"]["cell"] == "a"


def test_na_counts_as_failure_when_the_scene_says_so():
    c = cell("a", "s1", 1, "n/a")
    assert pairs.axis_scores(c)["grounding"] == 0.0
