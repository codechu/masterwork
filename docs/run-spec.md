# The run spec

One JSON file describes a run. The line reads it, walks the stages in order,
and stops at the first gate that holds. Every field below is what the code
actually reads — `pipeline/line.py` is the authority; this file explains why
each one is there.

    python -m pipeline.line spec.json --out runs

## purpose — required

The only stage that checks the operator rather than an instrument.

```json
"purpose": {
  "question":  "does candidate X do better work than the incumbent?",
  "decides":   "accept -> X enters the surgery gates; reject -> X closes",
  "axis_kind": "work",
  "owner":     "the person whose call this is"
}
```

`axis_kind` is `work` or `diagnostic`. A **diagnostic** run ends as
`DIAGNOSTIC` and draws no acceptance verdict — resemblance to a written
description of the agent you want is a diagnostic, not the work.

A run whose purpose is written after the numbers arrive is a run whose
purpose the numbers chose.

## seal — verify the piece before spending anything

```json
"seal": {
  "identity": "path/to/candidate.txt",
  "corpus":   "path/to/corpus.md",
  "script":   "path/to/ceremony-script.json",
  "deployed": "path/to/the/copy/that/will/actually/run",
  "profile":  "path/to/header-aliases.json"
}
```

`identity` is the only required key. `corpus` and `script` are hashed and
compared with what the seal claims. `deployed` is compared byte for byte
with `identity`: a candidate edited in one place and run in another gives a
clean battery whose numbers belong to a different piece.

`profile` maps canonical field names onto a workshop's own header dialect,
and an entry may carry a regex for a field the seal never wrote as
`key: value`:

```json
{"corpus_hash": ["korpus md5"],
 "date": {"aliases": ["tarih"], "pattern": "(\\d{4}-\\d{2}-\\d{2})"}}
```

A sealed file is its bytes. Teach the reader the dialect; do not edit the
seal to please the reader.

## generate — produce the cells

```json
"generate": {"command": "python3 my_scene_runner.py --seeds 1,2,3"}
```

Workshop-specific, so it is a command rather than code here. It streams to
`runs/<name>/generate.log`, which you can follow while it runs.

## cells — the completeness gate

```json
"cells": {
  "pattern": "/tmp/run/cells/*.json",
  "expected": ["case_a_1", "case_a_2"],
  "min_steps": 2,
  "closing_optional": false,
  "transcript_key": "messages",
  "closing_key": "final_text",
  "allow_missing": 0
}
```

Nothing is dropped. A short grid stops the run, and `allow_missing` is how a
deliberate exception is recorded — the allowance is echoed into the record,
because cells fail for reasons that correlate with what is being measured.

## label — wait for what comes from outside

```json
"label": {
  "cells":  "/tmp/run/cells/*.json",
  "expect": "/tmp/run/labels/{cell}.json",
  "key":    "label",
  "command": "optional: something that produces the labels"
}
```

`{cell}` is replaced by the cell's file stem. A label file that exists and
carries nothing counts as missing — it is the worse case, because it looks
answered. With labels outstanding the run ends `HELD_FOR_LABELLING`: waiting,
not broken. Rerun when they arrive.

A label is also missing when it was written for a different version of the
cell. Labels carry the hash of the record they judged, so regenerating the
cells and keeping the labels — same names, different transcripts — comes back
here instead of scoring deleted answers.

`command` runs only when something is unlabelled. Rerunning a complete line
does not relabel, which is deliberate: a line that relabelled every time would
walk into the refusal below and teach whoever runs it to keep the override on.

`tools/blind_label.py` answers the hold, and how it does it is the point:
only fields the rubric names reach the labeller, the order is shuffled by a
declared seed, the key mapping cells to blind ids is written aside and opened
afterwards, and an answer that will not parse is written as `null` rather than
guessed — which brings the run straight back to this gate.

```json
"command": "tools/blind_label.py label --cells '/tmp/run/cells/*.json' --rubric r.json --command 'my-judge' --out /tmp/run/blind --key /secure/key.json --blind-seed 20260829 --labeller other-model --generated-by the-candidate --arm-words candidate,incumbent && tools/blind_label.py reveal --out /tmp/run/blind --key /secure/key.json --to '/tmp/run/labels/{cell}.json'"
```

A rubric is `axis`, `verdicts`, `fields` (placeholder to dotted path in the
cell record) and `prompt`. `tools/rubric-example.json` is one, in full.

Three flags are worth knowing rather than copying. `--key` puts the blind-id
map somewhere the labeller cannot read, which matters when the labeller is an
agent with a filesystem. `--arm-words` names the arms: the automatic backstop
against a leak is built from cell filenames, so it has nothing to work with
when cells are named `cell_01`. And `reveal --relabel` is what it takes to
replace labels the line already has — it lands on every label written and the
line puts it on the verdict, next to `allow_self_judged`.

## judge — submit to the benchmark

```json
"judge": {
  "journeyman": {
    "endpoint":       "http://host:4567",
    "model":          "the agent's model id",
    "system_file":    "the piece under test",
    "judge_endpoint": "https://separate-judge/api",
    "judge_model":    "a judge that passed its calibration exam",
    "scenes":         "optional; omitting = the standard set",
    "seeds":          "optional; omitting = the standard seeds",
    "runs_dir":       "where the benchmark writes",
    "allow_self_judged": false,
    "allow_nonstandard": false,
    "skip_preflight":    false
  }
}
```

Endpoints are normalised: the benchmark appends `/v1/chat/completions`
itself, so a URL already ending in `/v1` would 404 every cell — and a run of
404s completes and reports nothing. Before spending a battery, the endpoint
is asked for its model list.

After the run the report's agent-system hash is compared with the piece you
sealed. `--system-file` is optional over there, so a spec that loses the line
measures the bare model while the report looks entirely ordinary.

For a workshop that does not use this benchmark, `"judge": {"command": "..."}`
runs anything and the comparability checks do not apply.

## gate — the frozen rule

```json
"gate": {"file": "gates/succession.md", "incumbent_axes": {"grounding": 0.72}}
```

See [`docs/gates.md`](gates.md). `incumbent_axes` supplies the arm being compared
against, when the rule says `compare: candidate - incumbent`.

## Other keys

- `name` — names the run directory. Default `"run"`.
- `max_run_bytes` — size above which the run directory is reported as
  heavy. Reported, never deleted: deciding what to remove is not the line's
  call. Default 50 MB.

## What the run leaves

`runs/<name>/run.json` — stage by stage, with the verdict, the measurement
summary, any declarations, and the directory's size. Kilobytes. Together
with the benchmark's `report.json` it is what a disagreement six weeks later
is settled with; everything else under `runs/` is re-derivable and can be
deleted.

## Beyond one run

One run of one arm decides almost nothing. Repeating an arm to measure its
band, and comparing two arms against that band, is [`docs/campaigns.md`](campaigns.md).
