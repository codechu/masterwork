# Training data, and what is kept

Two stages at the far end of the line: what a scored run can be turned into,
and what is worth keeping afterwards.

## `pairs` — preference data from scored runs

    masterwork pairs RUN_DIR --axis grounding --out pairs.jsonl \
      --min-gap 0.25 --gap-from band.json

On-policy preference pairs, cut from cells the benchmark already scored. The
agent produced both sides; nothing is written for it.

**`--min-gap` is required and has no default.** A pair whose two sides differ
by less than the judge's own spread pairs the *judge's noise* rather than the
agent's behaviour, and training on that teaches the noise. Measure the
spread first — same input, sampling seed varying, n≥3 — and set the gap
above it. `--gap-from` records which measurement justified the number, so a
set can be traced back to it.

**Two refusals, both deliberate:**

- **No pairs from a self-judged run.** The benchmark stamps those, and a
  stamp that travels with the claim is the whole point. `--allow-self-judged`
  exists, is recorded on every pair it produces, and should be rare.
- **No pairs below the gap.** There is no flag for this one.

**`--sft`** cuts winners only, as a supervised set, with `--floor` for the
minimum score to count as a winner.

**`--strip-system`** drops the identity from the prompt. The difference
matters: with the system text in place you teach *behaviour conditional on
that prompt*; without it you teach the behaviour itself. Which one you want
depends on whether the identity will be present at inference.

## `retain` — what a run leaves behind

    masterwork retain check RUN_DIR
    masterwork retain archive RUN_DIR --to archive/

`check` reports the size of a run directory and never deletes anything —
deciding what to remove is not the line's call. `archive` copies out the
kilobyte-sized evidence: the run record and the report, the two files a
disagreement six weeks later is settled with. Everything else under a run is
re-derivable.

A run that grows past `max_run_bytes` (default 50 MB) is **reported** in its
own record, not trimmed. A line that quietly deleted evidence to stay tidy
would be deciding, on its own, which parts of the record stop mattering.
