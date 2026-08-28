"""Training data. The refusals matter more than the output."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import pairs  # noqa: E402


def cell(cid, scene, seed, verdict, positive="good", invalid=False, judge=None):
    return {"cell_id": cid, "scene": scene, "seed": seed, "invalid": invalid,
            "invalid_reason": "404" if invalid else None,
            "seal": {"judge": judge} if judge else {},
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


def test_self_judged_runs_produce_nothing():
    cells = [cell("a", "s1", 1, "good", judge="SELF"),
             cell("b", "s1", 2, "bad", judge="SELF")]
    got, notes = pairs.build(cells, "grounding", 0.5, False, allow_self_judged=False)
    assert got == [] and any("self-judged" in n for n in notes)


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
