# masterwork

A *masterwork* is the piece a journeyman submits to the guild to qualify as
a master. Not "a great work" — the modern reading is a corruption. It is the
piece you make and hand over, and the guild, not the maker, decides.

That is the whole doctrine of this repository, carried in its name.

> **journeyman: measures, does not teach.**
> **masterwork: makes, does not measure.**

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

## Layout

    pipeline/   the line: one run, all gates, no manual steps
    tools/      instruments the line calls (ceremony, judges, gate checks)
    gates/      frozen gate templates

## Status

Not published, and not proven. Publication needs a candidate that separates
from the baseline through a frozen gate. As of today there is none: the best
candidate sits behind the incumbent. The name is honest about that — a
masterwork is submitted, and it can be refused.
