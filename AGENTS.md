# Reading this repository as an agent

You are probably here because someone asked you to run a character
experiment, and you can read the whole codebase faster than a person can
read this file. Read it anyway: what follows is not how the code works — you
can see that — but what it refuses to do, and why working around a refusal
is the failure this repository exists to prevent.

## What this is in one paragraph

A model reads a corpus of craft tales and is asked, one axis at a time, what
it will hold to. Its own answers, distilled by itself into one standing text,
become the identity it reads on every later request. That text is the
*piece*. The line here produces a piece, submits it to a separate benchmark
for scoring, and applies a decision rule that was written before the run.

## The four things you must not do

1. **Do not put a previous commitment, name, or identity into the ceremony
   context.** With one present the model copies it. A copy is a role being
   worn, not a pattern re-derived, and it also destroys the measurement:
   you can no longer tell whether the tales carried.
2. **Do not write or change a threshold after seeing results.** Gates are
   read, never written, by anything that runs. If a rule turns out to be
   wrong, say so in the record and freeze a new one for the next run; do not
   edit the frozen file.
3. **Do not clear a refusal by passing the flag that silences it**, unless
   the person you are working for decided that. `allow_self_judged`,
   `allow_nonstandard`, `allow_missing` exist so a deliberate exception can
   be *recorded*. Setting them to make a run finish converts a stopped run
   into a wrong number.
4. **Do not report a score without its stamps.** A self-judged score is not
   comparable. A run short of cells is not a smaller run. Both facts travel
   with the number, and dropping them is how a hedge becomes a claim.

## What the line will refuse, and what the refusal means

| verdict | what happened | what to do |
|---|---|---|
| `HELD_WITHOUT_PURPOSE` | the spec does not say what the run decides | write `purpose`; if you cannot say what changes on each outcome, the run is not ready |
| `HELD_AT_SEAL` | the piece is unreproducible, or the deployed copy differs | fix the seal or the deployment — never run "just to see" |
| `HELD_AT_COMPLETENESS` | the grid is short | find the missing cells; if proceeding anyway, declare it |
| `HELD_FOR_LABELLING` | labels are missing, empty, or written for an older version of a cell | get them with `tools/blind_label.py`; the line is waiting, not broken |
| `HELD_AT_MEASUREMENT` | the benchmark says the score is not comparable | judge from a separate endpoint, or declare and keep the stamp |
| `HELD_AT_GATE` | a threshold sits inside its own noise | the gate is void; measure the band, write a new gate |
| `NEEDS_SIGNATURE` | a band could not be verified, or a rule names no axis | a human decides; do not decide for them |
| `UNRESOLVED` | the difference is smaller than the gate can resolve | this is **not** "no difference" — report the size needed to settle it |
| `DIAGNOSTIC` | the run was declared diagnostic | no acceptance verdict may be drawn from it |

## One model, no budget, no second party

Nothing here requires a separate judge, an API key, or money. A workshop
with a single local model can run the whole line, and the path is not a
degraded one:

- **Counted axes need no judge at all.** They are computed by replaying the
  agent's own events during the run, before any judging happens. In the
  measurement that established our bands, the counted axes moved 0.02 across
  repeats while the judged axes moved 0.33 — the axes that cost nothing were
  the ones a gate could actually stand on.
- **The deterministic stages are the bulk of the line.** Seal, completeness,
  band, budget, retention and the frozen gate check involve no model.
- **Judged axes still work, self-judged.** They arrive stamped not
  comparable, which is honest rather than fatal: read them as diagnosis, do
  not gate on them, and keep the stamp with any number you quote.

A separate judge buys comparability with other people's runs, and a second
qualified model can be a useful adviser. Neither is a requirement, and a
house improving inside its own loop is a first-class way to use this.

## Vocabulary

- **piece** — the sealed identity file; what the model wrote about itself.
- **seal** — corpus hash, script hash, question seed, sampling seed, date.
  Two candidates from one corpus differing only by sampling seed are
  *different candidates*, not two samples of one.
- **band** — how much a measurement moves when nothing changes but sampling.
  A threshold below its band reads noise.
- **counted vs judged axis** — counted axes are computed from replayed
  events and are stable; judged axes are a model's label and move. Do not
  average them together, and do not gate on a judged axis at small cell
  counts.

## Where to start

```bash
python -m pytest tests/ -q          # 83 tests, no network
python -m pipeline.gate gates/      # check the frozen gate templates
python examples/held_at_gate.py     # one run, end to end, no model needed
```

The commands and the verdict table above also open the [README](README.md); they are here because this file is where an agent lands first.

Then read [`corpus/GROWING.md`](corpus/GROWING.md) before writing a single tale. The corpus is
the work; the code is what stops the work from lying to you.
