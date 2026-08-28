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

import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.request


def base_endpoint(url: str) -> str:
    """The benchmark appends /v1/chat/completions itself.

    Handing it a URL that already ends in /v1 yields /v1/v1/... and every cell
    comes back 404 — invalid, not wrong, so the run completes and reports
    nothing. Costs a full battery to notice, so it is normalised here.
    """
    url = url.rstrip("/")
    for tail in ("/v1/chat/completions", "/chat/completions", "/v1"):
        if url.endswith(tail):
            return url[: -len(tail)]
    return url


def build_command(cfg: dict) -> list[str]:
    """Translate a run spec's journeyman block into a CLI invocation."""
    cmd = [cfg.get("executable", "journeyman"), "run",
           "--endpoint", base_endpoint(cfg["endpoint"])]
    optional = {
        "model": "--model", "api_key": "--api-key",
        "judge_model": "--judge-model",
        "judge_api_key": "--judge-api-key",
        "judge_params_file": "--judge-params-file",
        "scenes": "--scenes", "system_file": "--system-file",
        "params_file": "--params-file", "seeds": "--seeds",
        "runs_dir": "--runs-dir",
    }
    for key, flag in optional.items():
        if cfg.get(key) is not None:
            cmd += [flag, str(cfg[key])]
    if cfg.get("judge_endpoint"):
        cmd += ["--judge", base_endpoint(cfg["judge_endpoint"])]
    return cmd


def reachable(endpoint: str, timeout: float = 8.0) -> str | None:
    """Ask the endpoint for its models before spending a battery on it.

    A wrong host or port does not crash the benchmark: every cell comes back
    invalid and the run completes with an empty report. Ten seconds here
    saves the hour it takes to notice that.
    """
    url = base_endpoint(endpoint) + "/v1/models"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            if r.status >= 400:
                return f"endpoint answered {r.status} at {url}"
        return None
    except urllib.error.HTTPError as e:
        return f"endpoint answered {e.code} at {url}"
    except Exception as e:
        return f"endpoint unreachable at {url}: {e}"


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
    # Did the benchmark actually wear the piece? --system-file is optional
    # over there, so a spec that loses the line measures the bare model and
    # the report looks entirely normal. The benchmark stamps the system text
    # it used; compare it with what we sealed.
    want = cfg.get("system_file")
    if want and os.path.exists(want):
        seen = ((summary.get("seal") or {}).get("agent_system_md5") or "")
        ours = hashlib.md5(open(want, "rb").read()).hexdigest()
        if not seen:
            out.append("the report carries no agent system hash — the benchmark "
                       "ran the bare model, not the candidate")
        elif not (ours.startswith(seen) or seen.startswith(ours)):
            out.append(f"the benchmark measured a different piece: report says "
                       f"{seen}, the sealed candidate is {ours[:len(seen) or 12]}")
    if summary["self_judged"] and not cfg.get("allow_self_judged"):
        out.append("journeyman marked this run self_judged — the agent endpoint "
                   "also served as judge, so the score is not comparable and no "
                   "gate may be applied to it. Either judge from a separate "
                   "endpoint — a second local model swapped in after the agent "
                   "phase counts, no purchase needed — or declare "
                   "allow_self_judged, which keeps the not-comparable stamp on "
                   "the record.")
    if summary["nonstandard"] and not cfg.get("allow_nonstandard"):
        out.append(f"non-standard scene set ({summary['nonstandard']}) — not "
                   f"comparable with standard runs. Declare allow_nonstandard for "
                   f"a development pass; the stamp stays on the record either way.")
    invalid = summary.get("invalid_cells")
    if invalid:
        out.append(f"journeyman reported invalid cells: {invalid}")
    if not summary["axes"]:
        out.append("report carries no axes — nothing was measured")
    return out


def run(cfg: dict, log_path: str | None = None) -> tuple[int, dict | None, str]:
    """Run the benchmark and read its report. Returns (rc, summary, tail)."""
    if not cfg.get("skip_preflight"):
        unreachable = reachable(cfg["endpoint"])
        if unreachable:
            return 1, None, unreachable
    started = time.time()
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
    # A reused runs directory hands back yesterday's numbers when today's run
    # produced nothing. Same shape, same fields, wrong day.
    if not cfg.get("report") and os.path.getmtime(report) < started - 1:
        return 1, None, (f"the newest report under {cfg.get('runs_dir')} predates "
                         f"this run ({report}) — this run wrote none, and reading "
                         f"the old one would report a different day's numbers")
    return 0, read_report(report), tail
