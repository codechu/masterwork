"""A campaign: repeats, the band they imply, and the ceiling that stops it."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from masterwork import campaign  # noqa: E402


def rec(axes, cost=0.0):
    return {"measurement": {"axes": axes, "judge_cost": {"cost": cost}}}


def test_band_is_the_spread_of_an_arms_own_repeats():
    s = campaign.arm_scores([rec({"a": 0.85}), rec({"a": 0.84}), rec({"a": 0.86})])
    assert campaign.band(s) == {"a": 0.02}


def test_a_single_repeat_has_no_band():
    """One run cannot show what moves when nothing changes."""
    assert campaign.band(campaign.arm_scores([rec({"a": 0.5})])) == {}


def test_projection_refuses_to_guess():
    proj, why = campaign.project(None, 6)
    assert proj is None and "guess" in why
    proj, why = campaign.project(0.15, 6)
    assert proj == 0.9


def test_spend_is_summed_from_what_the_provider_charged():
    assert campaign.spent([rec({"a": 1}, 0.12), rec({"a": 1}, 0.13)]) == 0.25


def test_over_ceiling_holds_before_spending():
    with tempfile.TemporaryDirectory() as tmp:
        spec = {"name": "c", "repeats": 3, "arms": {"a": {}, "b": {}},
                "budget": {"max_usd": 0.5, "cost_per_repeat": 0.2}}
        c = campaign.Campaign(spec, tmp)
        assert c.run() == 1
        d = json.load(open(os.path.join(tmp, "campaign.json")))
        assert d["verdict"] == "HELD_AT_BUDGET"
        assert d["arms"] == {}          # nothing was run


def test_comparison_marks_what_the_band_cannot_resolve():
    with tempfile.TemporaryDirectory() as tmp:
        c = campaign.Campaign({"name": "c", "arms": {}}, tmp)
        c.record["arms"] = {
            "incumbent": {"mean": {"x": 0.40, "y": 0.85}, "band": {"x": 0.02, "y": 0.02},
                          "spent": 0.1},
            "candidate": {"mean": {"x": 0.55, "y": 0.84}, "band": {"x": 0.03, "y": 0.02},
                          "spent": 0.1}}
        c.compare()
        axes = c.record["comparison"]["axes"]
        assert axes["x"]["difference"] == 0.15 and axes["x"]["resolvable"] is True
        assert axes["y"]["difference"] == -0.01 and axes["y"]["resolvable"] is False
