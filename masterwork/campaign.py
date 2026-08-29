"""A campaign: one arm repeated, or two arms compared — and what it costs.

The line runs one arm once. Almost nothing worth deciding is one run of one
arm: a band is the same arm repeated with nothing changed but sampling, and
a gate is two arms compared against that band. Both were being assembled by
hand — a shell loop, then a script to average, then the gate run separately
— and every hand step is a place for the numbers to be joined wrongly.

Money is a first-class stage here rather than a footnote. A campaign
projects its cost before spending anything, using a measured per-repeat cost
where one exists instead of a guess, and it stops when the next repeat would
cross the ceiling. Stopping mid-campaign with a recorded partial result is
recoverable; discovering the ceiling after the fact is not.

The band it computes is the spread of an arm's own repeats. That number then
has to sit *below* the gate's threshold — which the gate checker verifies
independently, since a campaign that measured its own band and then chose a
threshold under it would be marking its own paper.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys

from masterwork import line as line_mod

PUAN_KEYS = ("axes",)


def arm_scores(records: list[dict]) -> dict[str, list[float]]:
    """Per-axis score from each repeat, in order."""
    out: dict[str, list[float]] = {}
    for r in records:
        axes = ((r.get("measurement") or {}).get("axes")) or {}
        for a, v in axes.items():
            if v is None:
                continue
            out.setdefault(a, []).append(float(v))
    return out


def band(scores: dict[str, list[float]]) -> dict[str, float]:
    """Spread of an arm across its own repeats: what moved when nothing did."""
    return {a: round(max(v) - min(v), 4) for a, v in scores.items() if len(v) > 1}


def spent(records: list[dict]) -> float:
    total = 0.0
    for r in records:
        m = (r.get("measurement") or {})
        total += float((m.get("judge_cost") or {}).get("cost") or 0.0)
    return round(total, 6)


def project(per_repeat: float | None, repeats: int) -> tuple[float | None, str]:
    if per_repeat is None:
        return None, ("no measured cost per repeat — the first repeat measures it; "
                      "a projection from a price list is a guess, and published "
                      "prices move without notice")
    return round(per_repeat * repeats, 4), "projected from a measured repeat"


class Campaign:
    def __init__(self, spec: dict, out_dir: str):
        self.spec, self.out_dir = spec, out_dir
        os.makedirs(out_dir, exist_ok=True)
        self.record = {"name": spec.get("name", "campaign"), "arms": {},
                       "purpose": spec.get("purpose"), "budget": spec.get("budget")}

    def _say(self, msg):
        print(msg, flush=True)

    def run_arm(self, arm: str, arm_spec: dict, repeats: int,
                ceiling: float | None) -> tuple[list[dict], str | None]:
        records, per_repeat = [], self.spec.get("budget", {}).get("cost_per_repeat")
        for i in range(repeats):
            done = spent(records)
            if ceiling is not None and per_repeat and done + per_repeat > ceiling:
                return records, (f"stopping before repeat {i+1} of {arm}: "
                                 f"{done:.4f} spent, next repeat ~{per_repeat:.4f}, "
                                 f"ceiling {ceiling:.4f}")
            self._say(f"[{arm}] repeat {i+1}/{repeats}")
            out = os.path.join(self.out_dir, f"{arm}-{i+1}")
            rc = line_mod.Line(dict(arm_spec, name=f"{arm}-{i+1}"), out).run()
            rec = json.load(open(os.path.join(out, "run.json")))
            records.append(rec)
            if rc not in (0,):
                return records, f"{arm} repeat {i+1} ended {rec.get('verdict')}"
            if per_repeat is None:
                per_repeat = spent(records) or None
                if per_repeat:
                    self._say(f"       measured cost per repeat: {per_repeat:.4f}")
        return records, None

    def run(self) -> int:
        s = self.spec
        repeats = int(s.get("repeats", 3))
        ceiling = (s.get("budget") or {}).get("max_usd")
        proj, why = project((s.get("budget") or {}).get("cost_per_repeat"),
                            repeats * len(s["arms"]))
        self._say(f"projection: {proj if proj is not None else '?'} — {why}")
        if proj is not None and ceiling is not None and proj > ceiling:
            self._say(f"HELD: projected {proj} over ceiling {ceiling}. Raise the "
                      f"ceiling deliberately or cut repeats — not both quietly.")
            self.record["verdict"] = "HELD_AT_BUDGET"
            return self.persist()

        for arm, arm_spec in s["arms"].items():
            records, stop = self.run_arm(arm, arm_spec, repeats, ceiling)
            sc = arm_scores(records)
            self.record["arms"][arm] = {
                "repeats_done": len(records), "scores": sc, "band": band(sc),
                "mean": {a: round(statistics.mean(v), 4) for a, v in sc.items()},
                "spent": spent(records), "stopped": stop}
            if stop:
                self._say(f"[{arm}] {stop}")
                self.record["verdict"] = "HELD_AT_BUDGET" if "ceiling" in stop \
                    else "INCOMPLETE"
                return self.persist()

        self.compare()
        self.record["verdict"] = self.record.get("verdict", "COMPLETE")
        return self.persist()

    def compare(self):
        arms = list(self.record["arms"])
        if len(arms) != 2:
            return
        a, b = arms
        A, B = self.record["arms"][a], self.record["arms"][b]
        diff = {}
        for axis in sorted(set(A["mean"]) & set(B["mean"])):
            d = round(B["mean"][axis] - A["mean"][axis], 4)
            widest = max(A["band"].get(axis, 0.0), B["band"].get(axis, 0.0))
            diff[axis] = {"difference": d, "band": widest,
                          "resolvable": abs(d) > widest}
        self.record["comparison"] = {"incumbent": a, "candidate": b, "axes": diff}
        self._say(f"\n{'axis':<24}{'difference':>12}{'band':>8}  resolvable")
        for axis, v in diff.items():
            self._say(f"{axis:<24}{v['difference']:>+12.4f}{v['band']:>8.2f}"
                      f"  {'yes' if v['resolvable'] else 'no'}")

    def persist(self) -> int:
        total = sum(a.get("spent", 0.0) for a in self.record["arms"].values())
        self.record["spent_total"] = round(total, 6)
        p = os.path.join(self.out_dir, "campaign.json")
        json.dump(self.record, open(p, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        self._say(f"\nverdict {self.record['verdict']} · spent {total:.4f} · {p}")
        return 0 if self.record["verdict"] == "COMPLETE" else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="masterwork campaign", description="run a campaign: repeats, band, comparison")
    ap.add_argument("spec")
    ap.add_argument("--out", default="runs")
    a = ap.parse_args(argv)
    if not os.path.exists(a.spec):
        print(f"HELD: no campaign spec at {a.spec} — see docs/campaigns.md")
        return 4
    try:
        spec = json.load(open(a.spec, encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"HELD: {a.spec} is not valid JSON — {e}")
        return 4
    return Campaign(spec, os.path.join(a.out, spec.get("name", "campaign"))).run()


if __name__ == "__main__":
    sys.exit(main())
