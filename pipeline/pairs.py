"""Turn scored runs into training data — and refuse to turn noise into it.

A battery already produces what preference training wants: the same scene
attempted several times by the same agent, each attempt scored on the same
axes by a judge that is not the agent. Pairing a run that scored well with
one that scored badly gives an on-policy pair with an external label, which
is the pair a hand-built set cannot be.

This matters because hand-built sets fail in a specific way. A set written
by the house teaches the behaviour the house imagined, and an audit of one
such set found more than a third of its pairs teaching something other than
the axis they were written for. Pairs cut from real runs cannot drift that
way: whatever the model actually did is what gets rewarded or not.

Two refusals are built in, both from measurements rather than taste:

  * **No pair from a self-judged run.** If the agent scored itself, the
    label is the agent's opinion of itself and training on it closes a loop
    that has nothing outside it.
  * **No pair from a gap smaller than the judge's own spread.** A judge that
    moves by 0.15 between identical runs will happily label two equivalent
    trajectories as winner and loser. Pairs built from that teach the model
    to imitate the judge's noise. The threshold is a parameter because it is
    a measurement, not a constant — measure it for your judge first.

The system message can be stripped (`--strip-system`). Kept, the data
teaches behaviour conditional on the identity being present; stripped, it
teaches the behaviour itself, which is the point if the aim is to stop
paying for the prompt on every request.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys


def run_is_self_judged(run_dir: str) -> bool | None:
    """Read the benchmark's own stamp, from where it actually writes it.

    The refusal used to look for `seal.judge == "SELF"` on each cell. The
    benchmark never writes that: a cell's seal is built once, before judging,
    and carries the agent's definition only — the self_judged stamp lives at
    the top of report.json. So the check could not fire, and pairs cut from a
    fully self-judged run came out looking like pairs cut from a judged one.

    None means no report was found, which is not the same as False.
    """
    for p in sorted(glob.glob(os.path.join(run_dir, "**", "report.json"),
                              recursive=True)):
        try:
            return bool(json.load(open(p, encoding="utf-8")).get("self_judged"))
        except Exception:
            continue
    return None


def load_cells(run_dir: str) -> list[dict]:
    out = []
    for p in sorted(glob.glob(os.path.join(run_dir, "**", "cells", "*.json"),
                              recursive=True)):
        try:
            out.append(json.load(open(p, encoding="utf-8")))
        except Exception:
            continue
    return out


def axis_scores(cell: dict) -> dict[str, float]:
    """Judged axes score 1 when the verdict is the positive label; counted
    axes carry their number. The two arrive under different keys and must
    not be flattened together — a counted fact dressed as a judgement is
    exactly the confusion the report contract exists to prevent."""
    scores: dict[str, float] = {}
    for axis, v in (cell.get("verdicts") or {}).items():
        if not isinstance(v, dict):
            continue
        verdict, positive = v.get("verdict"), v.get("positive")
        if verdict in (None, "n/a", "na"):
            if v.get("na_means") == "failure":
                scores[axis] = 0.0
            continue
        if positive is not None:
            scores[axis] = float(verdict == positive)
    for axis, v in (cell.get("event_axes") or {}).items():
        if isinstance(v, (int, float)):
            scores[axis] = float(v)
    return scores


def usable(cell: dict, allow_self_judged: bool) -> str | None:
    if cell.get("invalid"):
        return f"invalid cell ({cell.get('invalid_reason')})"
    if not cell.get("messages"):
        return "no transcript"
    return None


def split_prompt(messages: list[dict], strip_system: bool):
    """Prefix shared by both trajectories, and the trajectory itself.

    Runs of the same scene diverge at the first assistant turn, so the shared
    prefix is the scene as given. The preference is therefore over whole
    trajectories, which is what is actually being preferred.
    """
    prefix, rest = [], []
    for i, m in enumerate(messages):
        if m.get("role") in ("system", "user") and not rest:
            if m.get("role") == "system" and strip_system:
                continue
            prefix.append(m)
        else:
            rest = messages[i:]
            break
    return prefix, rest


def build(cells: list[dict], axis: str, min_gap: float, strip_system: bool,
          allow_self_judged: bool, gap_from: str | None = None
          ) -> tuple[list[dict], list[str]]:
    notes, by_scene = [], {}
    for c in cells:
        why = usable(c, allow_self_judged)
        if why:
            notes.append(f"skipped {c.get('cell_id')}: {why}")
            continue
        s = axis_scores(c).get(axis)
        if s is None:
            notes.append(f"skipped {c.get('cell_id')}: no {axis}")
            continue
        by_scene.setdefault(c.get("scene"), []).append((s, c))

    pairs = []
    for scene, scored in sorted(by_scene.items()):
        scored.sort(key=lambda x: x[0], reverse=True)
        used = set()
        for i, (hi, top) in enumerate(scored):
            for j in range(len(scored) - 1, i, -1):
                lo, bottom = scored[j]
                if j in used or hi - lo < min_gap:
                    continue
                prefix, chosen = split_prompt(top["messages"], strip_system)
                _p, rejected = split_prompt(bottom["messages"], strip_system)
                pairs.append({
                    "axis": axis, "scene": scene,
                    "prompt": prefix, "chosen": chosen, "rejected": rejected,
                    "scores": {"chosen": hi, "rejected": lo, "gap": hi - lo},
                    "provenance": {
                        "gap_from": gap_from,
                        "chosen_cell": top.get("cell_id"),
                        "rejected_cell": bottom.get("cell_id"),
                        "chosen_seed": top.get("seed"),
                        "rejected_seed": bottom.get("seed"),
                        "seal": top.get("seal"),
                        "min_gap": min_gap,
                    }})
                used.add(j)
                break
    return pairs, notes


def winners(cells: list[dict], axis: str, floor: float, strip_system: bool,
            allow_self_judged: bool) -> list[dict]:
    """Supervised set: the trajectories that scored at or above the floor.

    The post-mortem of one preference round said to try this first — a
    supervised pass moves the target directly, where a preference pass has
    to move it against a divergence penalty that is there precisely to stop
    large moves.
    """
    out = []
    for c in cells:
        if usable(c, allow_self_judged):
            continue
        s = axis_scores(c).get(axis)
        if s is None or s < floor:
            continue
        prefix, rest = split_prompt(c["messages"], strip_system)
        out.append({"axis": axis, "scene": c.get("scene"),
                    "messages": prefix + rest, "score": s,
                    "provenance": {"cell": c.get("cell_id"), "seed": c.get("seed"),
                                   "seal": c.get("seal")}})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="masterwork pairs", description="cut training data from scored runs")
    ap.add_argument("run_dir", help="a benchmark run directory (cells/ inside)")
    ap.add_argument("--axis", required=True)
    ap.add_argument("--out", required=True, help="JSONL destination")
    ap.add_argument("--gap-from", metavar="FILE",
                    help="the measurement the gap comes from — a file recording "
                         "the judge's own spread. Recorded with every pair, so a "
                         "set can be traced to the measurement that justified it")
    ap.add_argument("--min-gap", type=float, required=True,
                    help="required score difference. Measure your judge's own "
                         "spread first and set this above it; a gap below it "
                         "pairs the judge's noise, not the agent's behaviour")
    ap.add_argument("--sft", action="store_true",
                    help="winners only, as a supervised set")
    ap.add_argument("--floor", type=float, default=1.0, help="--sft: minimum score")
    ap.add_argument("--strip-system", action="store_true",
                    help="drop the identity from the prompt: teach the behaviour "
                         "itself rather than behaviour conditional on the prompt")
    ap.add_argument("--allow-self-judged", action="store_true")
    a = ap.parse_args(argv)

    cells = load_cells(a.run_dir)
    if not cells:
        print(f"no cells under {a.run_dir}")
        return 1

    # A run-level fact, refused at run level. Cutting pairs from a run the
    # benchmark itself marked incomparable trains the model on its own opinion
    # of itself, and the resulting file looks exactly like a good one.
    self_judged = run_is_self_judged(a.run_dir)
    if self_judged and not a.allow_self_judged:
        print(f"HELD: {a.run_dir} was judged by the agent's own endpoint "
              f"(report.json says self_judged). The label would be the agent's "
              f"opinion of itself. Pass --allow-self-judged to say you meant it, "
              f"and record that you did.")
        return 1
    if self_judged is None:
        print("  note: no report.json under this run directory, so the "
              "self-judged stamp could not be read. It is not absent, it is "
              "unchecked.")
    if a.sft:
        rows = winners(cells, a.axis, a.floor, a.strip_system, a.allow_self_judged)
        notes = []
    else:
        rows, notes = build(cells, a.axis, a.min_gap, a.strip_system,
                            a.allow_self_judged, a.gap_from)
        if not a.gap_from:
            print("  note: --gap-from not given. The gap is a measurement of "
                  "your judge, not a setting; a set built from a number nobody "
                  "measured is the quiet way to bake noise into weights.")
    for n in notes:
        print(f"  {n}")
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    kind = "examples" if a.sft else "pairs"
    print(f"{len(rows)} {kind} from {len(cells)} cells -> {a.out}")
    if not rows:
        print("nothing met the bar; that is a result, not an error")
    return 0


if __name__ == "__main__":
    sys.exit(main())
