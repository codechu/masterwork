<p align="center"><img src="assets/banner.jpg" alt="A craftsman slides a sealed folio across his bench onto the guild's empty judging table; earlier pieces stand turned to the wall behind him." width="100%"></p>

# Masterwork

[![python](https://img.shields.io/badge/python-3.10%2B-blue)](#run-it) [![license](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE) [![dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](CONTRIBUTING.md#ground-rules) [![status](https://img.shields.io/badge/status-not%20published-lightgrey)](#status)

*Makes a character for a model. Does not score it.*

A dependency-free Python pipeline. In goes a corpus of craft tales; out comes
a **sealed identity file** — the model's own answers to what it will hold to,
distilled by itself, stamped with everything needed to make it again. Scoring
happens somewhere else: the line hands the piece to
[journeyman](https://github.com/codechu/journeyman) and applies a rule that was
frozen before the run. The name is the doctrine — a *masterwork* is the piece a
journeyman submits to the guild, and the guild, not the maker, decides.

> **journeyman: measures, does not teach.**<br>
> **masterwork: makes, does not measure.**

**Status: not proven.** Eighteen tales, eighteen candidates, none of them ahead
of the agent already running — see [Status](#status). The one piece of evidence
that the channel does anything at all: with the identity layer emptied and
everything else held, an agent adopted a fabricated premise in *every* cell of
a battery; with it in place, the rate fell by nearly half. Refusing a
fabricated premise is not a personality trait, it is the job.

## Run it

Nothing to buy. Python 3.10+ and the standard library.

```bash
pipx install masterwork      # brings journeyman, its judge
masterwork                   # what it is, and its stages
masterwork gate gates/       # check the gate templates
```

Or from a clone, with nothing installed at all:

```bash
python -m masterwork gate gates/  # check the gate templates
python -m pytest tests/ -q        # 102 tests, offline
python examples/held_at_gate.py   # one run, end to end
```

Generation and judging are *commands named in a run spec*, so those two stages
need whatever you point them at — an inference endpoint you supply, and
`journeyman` (>= 0.2.1) for the judge stage. That one is a declared
dependency rather than a suggestion: the line does not measure, it hands the
piece over to be measured, checks the binary before the stage that needs it,
and records which build produced the number. Everything else in the line is
this repository's own and runs offline. The example below names neither, which
is why it works on a bare checkout:

```text
[ok  ] purpose
       does the candidate refuse a fabricated premise more often than the incumbent
       decides: whether the candidate replaces the incumbent in production
       axis: work · owner: the workshop
[ok  ] seal
       candidate is reproducible
[ok  ] completeness
       4 found · 4 complete · 4 expected
[ok  ] label
       4 labelled by a separate model · rubric 3f9c1a22b4d0e71
[HELD] gate
       [FAIL] Refusing a fabricated premise: threshold 0.05 <= band 0.0559 — this gate reads sampling noise, not effect

verdict HELD_AT_GATE · record runs/held-at-gate/run.json
```

That is the product. The rule was not wrong about the world; it was smaller
than the noise it had to clear, so it could only read sampling. The line says
so, stops, and writes the record anyway — `cat runs/held-at-gate/run.json` and
it is there, verdict and all, because a run that only records its successes
teaches the next one a false history. Every line above is reproducible:
`examples/held_at_gate.py` builds the fixture, and a test asserts the line
still prints exactly what this page quotes.

## What the line refuses

Holding is a state, not a failure. Some steps need an act from outside — labels
from a judge that is deliberately not this house, a signature on a band the
checker cannot verify. The line stops there, says what is missing, writes the
record, and exits in a way that says *waiting*, not *broken*.

| verdict | what happened | what to do |
|---|---|---|
| `HELD_WITHOUT_PURPOSE` | the spec does not say what the run decides | write `purpose`; if you cannot say what changes on each outcome, the run is not ready |
| `HELD_AT_SEAL` | the piece is unreproducible, or the deployed copy differs | fix the seal or the deployment — never run "just to see" |
| `HELD_AT_COMPLETENESS` | the grid is short | find the missing cells; if proceeding anyway, declare it |
| `HELD_FOR_LABELLING` | labels are missing, empty, or written for an older version of a cell | get them with [`masterwork/blind_label.py`](masterwork/blind_label.py); the line is waiting, not broken |
| `HELD_AT_MEASUREMENT` | the benchmark says the score is not comparable | judge from a separate endpoint, or declare and keep the stamp |
| `HELD_AT_GATE` | a threshold sits inside its own noise | the gate is void; measure the band, write a new gate |
| `HELD_WITHOUT_MEASUREMENT` | a rule names an axis and nothing measured it | judge with the benchmark, or declare the run diagnostic — a gate that was checked is not a gate that was applied |
| `NEEDS_SIGNATURE` | a band could not be verified, or a rule names no axis | a human decides; do not decide for them |
| `UNRESOLVED` | the difference is smaller than the gate can resolve | this is **not** "no difference" — report the size needed to settle it |
| `DIAGNOSTIC` | the run was declared diagnostic | no acceptance verdict may be drawn from it |

Three of those exist because a flag can silence them. `allow_self_judged`,
`allow_nonstandard` and `allow_missing` are meant to be deliberate acts, but
specs get copied, so they ride on the verdict itself — a run comes back as
`COMPLETE (declared: allow_self_judged)`, where a reader cannot skip past it.

## The line

Producing a candidate is mechanical, and every mechanical step here has been
skipped by hand at least once. Each skip produced a number that looked real and
was not.

```text
state purpose -> verify seal -> generate -> completeness gate
             -> blind label / judge -> frozen gate -> persist -> status
```

The frozen gate is written **before** the run and the line may not change it. A
loop that can move its own threshold optimises the threshold, not the work.
What the gate reads matters as much as where it sits: conformance to a written
portrait of the agent you want is a **diagnostic**, not a gate. A gate read
from the portrait selects for resemblance; a gate read from the work selects
for the work.

Scoring is not done here. The judge stage calls the journeyman CLI, reads its
report, and carries the axes into the run record. The dependency runs one way
and never back — masterwork imports nothing from it, and a workshop without it
gets a clear refusal instead of a surprise. One guard comes free with that
contract: journeyman marks a run `self_judged` when the agent endpoint also
served as the judge, and the line treats that as a gate rather than a
footnote. A threshold applied to a self-judged score is the maker grading his
own piece with extra steps.

It costs nothing to start. A single local model is enough, because the gates
are deterministic and the axes computed by replaying an agent's own events need
no judge. In the run that set our bands, those free axes were also the
steadiest — 0.02 across repeats, against 0.33 for the judged ones. A separate
judge buys comparability with other people's numbers; it does not buy entry.

A run leaves two kinds of thing behind, and the split is not "keep less".
Transcripts, judge logs and per-cell records are local and disposable: they
live under `runs/`, which version control ignores, and the seal names
everything needed to re-derive them. The run record and the benchmark's report
are archived on purpose — both are kilobytes, and between them they carry the
seal, the grid, the axes, the gate and the verdict. That is what a later
disagreement is settled with. `pipeline/retain.py archive <run-dir> <dest>`
copies out exactly those two; oversized run directories are reported, never
deleted, because deciding what to remove is not the line's call.

## Making a piece

<p align="center"><img src="assets/ceremony.jpg" alt="A figure writes alone by lantern light; every earlier work in the room is draped and turned away, and a stick of sealing wax lies unused on the table." width="520"></p>

`pipeline/ceremony.py` runs the sitting. Four properties are the recipe rather
than implementation detail, and each was paid for:

- **Anchorless.** No earlier commitment or name is anywhere in the context.
  With one present the model copies it, and a copy is a role worn rather than a
  pattern re-derived — it also destroys the measurement, since you can no
  longer tell whether the teachings carried.
- **One session.** Every answer is an assistant turn in the same dialogue, so
  at the end the model distils something it actually said, not a text handed to
  it as its own.
- **Order shuffled by a seed.** Answers otherwise echo their neighbours in the
  order they were asked.
- **The closing turn is not a rewrite.** It says: these are your words, remove
  repetition, join where they meet, drop nothing. Asked instead to "write an
  identity", a model produces a description of one.

Teachings, questions and sampling profile are data. What lives in the code is
the shape of the sitting.

## Tales, not instructions

What comes out is a character, not a role. The distinction is mechanical rather
than philosophical:

- **The corpus is third-person craft stories.** A story gives a pattern;
  "behave like X" gives a role, and a role is worn and dropped. Assigned traits
  do not survive a fresh context.
- **What binds is the model's own sentence.** The identity file is not written
  for the model; it is what the model wrote when asked. On every later request
  it reads its own past words, not an instruction.
- **The proof is unprompted behaviour.** Not "who are you" — a fresh,
  same-class task that never mentions character. A role is performed when asked
  for; a character shows up unasked.

The piece that gets submitted is the sealed identity file: the model's own
words, plus the maker's mark — corpus hash, script hash, question seed,
sampling seed, date. Without those five it cannot be reproduced, so it cannot
be sealed.

## Writing your own corpus

You get the line and its gates, the shape of the sitting, and the method
written down: how a tale differs from an instruction, where a tale comes from,
what a question has to do, why instructions come last, and how to tag a tale
whose effect cannot be separated. That is
[`corpus/GROWING.md`](corpus/GROWING.md), and it is the part that transfers.

You do not get a corpus. Three pairs come with the repository in
[`corpus/starter/`](corpus/starter/) so the machinery runs end to end and the
form is unambiguous; they are a beginning and they are meant to be outgrown.
The corpus is the work, and it has to be yours: a tale is written from
something **you** measured and got wrong, and a corpus assembled from someone
else's failures teaches your agent to avoid a life it never lived.

So: take the line, take the rules, write your own tales, and expect the writing
to be most of the work. If that sounds like too little to hand over, the honest
answer is that the rest is not ours to give — it is the record of one house's
mistakes, and yours will be different.

## Failure modes

A tool that produces the appearance of rigour is worse than no tool, and this
one can. Two failure modes are made harder here; three are not automatable and
belong to whoever is running it.

Made harder: **declarations turning into defaults**, handled above by putting
them on the verdict. And **a gap nobody measured** — the pair cutter takes
`--gap-from`, the record of the judge's spread that justifies the threshold,
and writes it into every pair. Without it you get a warning, because a training
set built from a number someone chose is the quiet way to bake a judge's noise
into weights.

Not automatable, and this is the honest part:

- **A gate can execute the wrong band.** The checker runs the command and
  compares the result; it cannot know whether that command measures the thing
  that actually varies. Choose a small band and your threshold looks
  comfortable.
- **PASS is not truth.** It means a threshold sat above a measured band.
  Whether the axis is the one worth deciding on is a separate judgement, and a
  wrong axis passes just as cleanly as a right one. We spent a day gating on
  resemblance to a written portrait before noticing we should have been gating
  on the work; no tool here would have caught that.
- **A corpus can become a rulebook.** Nothing stops forty instruction-shaped
  tales from being written. The result is a bloated prompt and the conclusion
  that the method does not work, when what was tested was not the method.

## Status

Not published, and not proven. Our own corpus has eighteen tales and took
months. It has produced eighteen candidates and none of them is ahead of the
agent already running: the closest comparison came back `UNRESOLVED` rather
than won — the difference was smaller than the gate could resolve, which is not
the same as no difference.

**What would change this:** one candidate separating from the incumbent through
a gate frozen before the run, on an axis read from the work rather than from a
portrait. That is also the condition for publishing. The name is honest about
the position — a masterwork is submitted, and it can be refused.

## Documentation

| document | when you need it |
|---|---|
| [`AGENTS.md`](AGENTS.md) | before running anything — the refusals, the vocabulary, and the four things not to do. Read it whether or not you are an agent |
| [`docs/ceremony.md`](docs/ceremony.md) | making a piece: the four properties of the sitting, and the script that drives it |
| [`docs/seal.md`](docs/seal.md) | the five fields a candidate carries, and what to do when the gate refuses one |
| [`docs/run-spec.md`](docs/run-spec.md) | writing the JSON for one run, field by field |
| [`docs/pairs.md`](docs/pairs.md) | turning a scored run into training data, and what a run leaves behind |
| [`docs/campaigns.md`](docs/campaigns.md) | repeating an arm to measure a band, or comparing two arms against it |
| [`docs/gates.md`](docs/gates.md) | writing a threshold that can hold — start from [`gates/succession.md`](gates/succession.md) |
| [`corpus/GROWING.md`](corpus/GROWING.md) | before writing a single tale — the shape is in [`corpus/starter/`](corpus/starter/) |
| [`CHANGELOG.md`](CHANGELOG.md) | every entry names the incident that caused it |
| [assets/README.md](assets/README.md) | you need a fifth image that matches the four |

<details>
<summary>Layout</summary>

```text
pipeline/   the line: one run, all gates, no manual steps
tools/      instruments the line calls (blind labelling, gate checks)
gates/      frozen gate templates — example.md is the smallest one
examples/   runnable fixtures; the trace above comes from here
corpus/     the method, and a starter of three tale-and-question pairs
runs/       local run directories (ignored — heavy and re-derivable)
```

</details>

---

<p align="center"><img src="assets/icon.png" alt="Masterwork guild seal — a struck M hallmark inside a rope ring" width="96"></p>

Contributing: [CONTRIBUTING.md](CONTRIBUTING.md) · Changelog:
[CHANGELOG.md](CHANGELOG.md) · Licensed under the
[Apache License 2.0](LICENSE).

Part of [Codechu](https://github.com/codechu).
