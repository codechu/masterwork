# masterwork

A *masterwork* is the piece a journeyman submits to the guild to qualify as
a master. Not "a great work" — the modern reading is a corruption. It is the
piece you make and hand over, and the guild, not the maker, decides.

That is the whole doctrine of this repository, carried in its name.

> **journeyman: measures, does not teach.**
> **masterwork: makes, does not measure.**

## What counts as better

Usefulness is the acceptance criterion, and it is not scored here — see
below. Conformance to a written portrait of the agent we want is a
**diagnostic**, not a gate: it tells you where a candidate drifts, and a
candidate can match the portrait closely while doing worse work. A gate
read from the portrait selects for resemblance; a gate read from the work
selects for the work.

The one piece of evidence that the channel does anything at all points the
same way: with the identity layer emptied and everything else held, an
agent adopted a fabricated premise in every cell of a battery; with it in
place, the rate fell by nearly half. Refusing a fabricated premise is not a
personality trait, it is the job.

## What it makes

A character for a model — not a role. The distinction is the point, and it
is mechanical rather than philosophical:

- **Tales, not instructions.** The corpus is third-person craft stories. A
  story gives a pattern; "behave like X" gives a role, and a role is worn
  and dropped. Assigned traits do not survive a fresh context.
- **The ceremony is anchorless.** No prior commitment, no prior name is in
  view when the model is asked what it will hold to. If the old answer is
  in the context, the model copies it — and a copy is a role again. The
  commitment has to be re-derived from the tales, every time.
- **What binds is the model's own sentence.** The identity file is not
  written for the model; it is what the model wrote when asked. On every
  later request it reads its own past words, not an instruction.
- **The proof is unprompted behaviour.** Not "who are you" — a fresh,
  same-class task that never mentions character. A role is performed when
  asked for; a character shows up unasked.

The piece that gets submitted is the sealed identity file: the model's own
words, plus the maker's mark — corpus hash, script hash, question seed,
sampling seed, date. Without those five it cannot be reproduced, so it
cannot be sealed.

## The sitting

`pipeline/ceremony.py` runs it. Four properties are the recipe rather than
implementation detail, and each was paid for:

- **Anchorless.** No earlier commitment or name is anywhere in the context.
  With one present the model copies it, and a copy is a role worn rather
  than a pattern re-derived — it also destroys the measurement, since you
  can no longer tell whether the teachings carried.
- **One session.** Every answer is an assistant turn in the same dialogue,
  so at the end the model distils something it actually said, not a text
  handed to it as its own.
- **Order shuffled by a seed.** Answers otherwise echo their neighbours in
  the order they were asked.
- **The closing turn is not a rewrite.** It says: these are your words,
  remove repetition, join where they meet, drop nothing. Asked instead to
  "write an identity", a model produces a description of one.

Teachings, questions and sampling profile are data. What lives in the code
is the shape of the sitting.

## The line

Producing a candidate is mechanical, and every mechanical step here has
been skipped by hand at least once. Each skip produced a number that looked
real and was not.

    verify seal -> generate -> completeness gate -> blind label / judge
                -> frozen gate -> persist -> status

The frozen gate is written **before** the run and the line may not change
it. A loop that can move its own threshold optimises the threshold, not the
work.

## What it does not do

It does not measure. Scoring belongs to
[journeyman](https://github.com/codechu/journeyman), and the line submits to
it rather than working around it: the judge stage calls the benchmark, reads
its report, and carries the axes into the run record. The dependency runs one
way and never back — masterwork calls the CLI, imports nothing from it, and a
workshop without it gets a clear refusal instead of a surprise.

One guard comes free with that contract. journeyman marks a run
`self_judged` when the agent endpoint also served as the judge — its own way
of saying the score is not comparable. The line treats that as a gate, not a
footnote: a threshold applied to a self-judged score is the maker grading his
own piece with extra steps. Non-standard scene sets and invalid cells are
surfaced the same way.

## Dependencies

The pipeline imports the standard library and nothing else. There is no
model client in here, no HTTP, no vendor SDK, and no reference to any
particular serving stack.

That is not an accident of youth. Generation and judging are commands in
the run spec, so whatever produces a candidate — a local server, a hosted
API, a script someone wrote this morning — is wiring, and the gates apply
the same way regardless. A workshop swapping its inference stack should not
have to touch a line of this.

The rule survives the next step too. The ceremony that actually makes a
candidate still lives outside this repository; when it moves in, it reaches
a model through one narrow seam — a command, or an endpoint named in
config — never through a particular workshop's infrastructure. A gate that
only fires on one house's plumbing is not a gate, it is a habit.

## What a run leaves behind

A line that keeps everything becomes a disk problem and then a slow one:
every later search walks transcripts nobody will reopen. A line that keeps
nothing cannot defend a number six weeks on. The split is not "keep less":

- **Local and disposable** — transcripts, judge logs, per-cell records, the
  benchmark's run directory. They live under `runs/`, which version control
  ignores, and they are re-derivable: the seal names the corpus, the script
  and both seeds.
- **Archived on purpose** — the run record and the benchmark's report. Both
  are kilobytes, and between them they carry the seal, the grid, the axes,
  the gate and the verdict. That is what a later disagreement is settled
  with.

`pipeline/retain.py archive <run-dir> <dest>` copies out exactly those two.
Quotes inside a record are capped at 300 characters — enough to recognise
an answer, far too little to store one. Oversized run directories are
reported, never deleted: deciding what to remove is not the line's call.

## Layout

    pipeline/   the line: one run, all gates, no manual steps
    tools/      instruments the line calls (ceremony, judges, gate checks)
    gates/      frozen gate templates
    runs/       local run directories (ignored — heavy and re-derivable)

## What you get, and what you have to make

You get the line and its gates, the shape of the sitting, and the method
written down: how a tale differs from an instruction, where a tale comes
from, what a question has to do, why instructions come last, and how to
tag a tale whose effect cannot be separated. That is `corpus/GROWING.md`,
and it is the part that transfers.

You do not get a corpus. Three pairs come with the repository so the
machinery runs end to end and the form is unambiguous; they are a beginning
and they are meant to be outgrown. The corpus is the work, and it has to be
yours: a tale is written from something **you** measured and got wrong, and
a corpus assembled from someone else's failures teaches your agent to avoid
a life it never lived.

We are still at it ourselves. Our own corpus has eighteen tales, took
months, and has not yet produced a successor that beats the agent already
running — eighteen candidates, none of them ahead of the incumbent, and the
closest comparison came back unresolved rather than won. That is stated
here rather than discovered later, because a method described by its
successes only is a method you cannot use.

So: take the line, take the rules, write your own tales, and expect the
writing to be most of the work. If that sounds like too little to hand over,
the honest answer is that the rest is not ours to give — it is the record of
one house's mistakes, and yours will be different.

## Using this badly

A tool that produces the appearance of rigour is worse than no tool, and
this one can. The failure modes are known; two are made harder here, and
three are not automatable and belong to whoever is running it.

Made harder:

- **Declarations turning into defaults.** `allow_self_judged`,
  `allow_nonstandard` and `allow_missing` are meant to be deliberate acts,
  but specs get copied. They now ride on the verdict itself — a run comes
  back as `COMPLETE (declared: allow_self_judged)`, where a reader cannot
  skip past it.
- **A gap nobody measured.** The pair cutter takes `--gap-from`, the record
  of the judge's spread that justifies the threshold, and writes it into
  every pair. Without it you get a warning, because a training set built
  from a number someone chose is the quiet way to bake a judge's noise into
  weights.

Not automatable, and this is the honest part:

- **A gate can execute the wrong band.** The checker runs the command and
  compares the result; it cannot know whether that command measures the
  thing that actually varies. Choose a small band and your threshold looks
  comfortable.
- **PASS is not truth.** It means a threshold sat above a measured band.
  Whether the axis is the one worth deciding on is a separate judgement, and
  a wrong axis passes just as cleanly as a right one. We spent a day gating
  on resemblance to a written portrait before noticing we should have been
  gating on the work; no tool here would have caught that.
- **A corpus can become a rulebook.** Nothing stops forty instruction-shaped
  tales from being written. The result is a bloated prompt and the
  conclusion that the method does not work, when what was tested was not the
  method.

## Status

Not published, and not proven. Publication needs a candidate that separates
from the baseline through a frozen gate. As of today there is none: the best
candidate sits behind the incumbent. The name is honest about that — a
masterwork is submitted, and it can be refused.
