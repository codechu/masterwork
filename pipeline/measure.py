"""Measurement is journeyman's job; this is the seam that hands the piece over.

The maker does not grade his own piece. That is the whole reason this
repository and the benchmark are separate, and it only means something if
the line actually submits the work rather than scoring it here.

So the judge stage shells out to the `journeyman` CLI and reads its
report.json back. Shelling out, not importing: the dependency stays one
way and optional, the line keeps its standard-library-only footprint, and a
workshop that has not installed the benchmark gets a clear refusal instead
of an import error at a random moment.

One guard comes free with the contract. journeyman marks a run
`self_judged` when the agent endpoint also served as the judge — its own
way of saying the score is not comparable. A gate applied to such a score
would be the maker grading himself with extra steps, so the line refuses it
unless the spec says out loud that this run is a dev run.

What the line will not do is require anyone to buy a judge. No provider is
named anywhere in this repository, and a separate judge can be a second
local model swapped in after the agent phase — time rather than money. The
requirement is not a separate endpoint; it is that the comparability stamp
travels with the claim and cannot be removed by whoever quotes the number.
"""
from __future__ import annotations

import json
import os
import subprocess


def build_command(cfg: dict) -> list[str]:
    """Translate a run spec's journeyman block into a CLI invocation."""
    cmd = [cfg.get("executable", "journeyman"), "run",
           "--endpoint", cfg["endpoint"]]
    optional = {
        "model": "--model", "api_key": "--api-key",
        "judge_endpoint": "--judge", "judge_model": "--judge-model",
        "judge_api_key": "--judge-api-key",
        "judge_params_file": "--judge-params-file",
        "scenes": "--scenes", "system_file": "--system-file",
        "params_file": "--params-file", "seeds": "--seeds",
        "runs_dir": "--runs-dir",
    }
    for key, flag in optional.items():
        if cfg.get(key) is not None:
            cmd += [flag, str(cfg[key])]
    return cmd


def newest_report(runs_dir: str) -> str | None:
    found = []
    for root, _dirs, files in os.walk(runs_dir):
        if "report.json" in files:
            p = os.path.join(root, "report.json")
            found.append((os.path.getmtime(p), p))
    return max(found)[1] if found else None


def read_report(path: str) -> dict:
    d = json.load(open(path, encoding="utf-8"))
    axes = d.get("axes") or {}
    return {
        "report": path,
        "axes": {k: v.get("score") for k, v in axes.items()} if isinstance(axes, dict) else {},
        "n": {k: v.get("n") for k, v in axes.items()} if isinstance(axes, dict) else {},
        "self_judged": bool(d.get("self_judged")),
        "nonstandard": d.get("nonstandard"),
        "invalid_cells": d.get("invalid_cells"),
        "seal": d.get("seal"),
    }


def problems(summary: dict, cfg: dict) -> list[str]:
    out = []
    if summary["self_judged"] and not cfg.get("allow_self_judged"):
        out.append("journeyman marked this run self_judged — the agent endpoint "
                   "also served as judge, so the score is not comparable and no "
                   "gate may be applied to it. Either judge from a separate "
                   "endpoint — a second local model swapped in after the agent "
                   "phase counts, no purchase needed — or declare "
                   "allow_self_judged, which keeps the not-comparable stamp on "
                   "the record.")
    if summary["nonstandard"]:
        out.append(f"non-standard scene set ({summary['nonstandard']}) — scores "
                   f"are not comparable with standard runs; say so in the record")
    invalid = summary.get("invalid_cells")
    if invalid:
        out.append(f"journeyman reported invalid cells: {invalid}")
    if not summary["axes"]:
        out.append("report carries no axes — nothing was measured")
    return out


def run(cfg: dict, log_path: str | None = None) -> tuple[int, dict | None, str]:
    """Run the benchmark and read its report. Returns (rc, summary, tail)."""
    cmd = build_command(cfg)
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    if log_path:
        with open(log_path, "w") as log:
            rc = subprocess.call(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)
        tail = "".join(open(log_path, encoding="utf-8", errors="replace")
                       .readlines()[-15:])
    else:
        p = subprocess.run(cmd, capture_output=True, text=True, env=env)
        rc, tail = p.returncode, (p.stdout + p.stderr)[-2000:]
    if rc != 0:
        return rc, None, tail
    report = cfg.get("report") or newest_report(cfg.get("runs_dir", "runs"))
    if not report or not os.path.exists(report):
        return 1, None, "benchmark finished but no report.json was found"
    return 0, read_report(report), tail
