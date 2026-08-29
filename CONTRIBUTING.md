# Contributing to masterwork

This repository is a line for producing a character for a model and
submitting it to be scored. It is small, standard-library only, and
opinionated about what it refuses to do. Contributions that keep those
refusals intact are the easy ones to accept.

Read [`AGENTS.md`](AGENTS.md) first, whether or not you are an agent. It is
the shortest statement of what the line will not do and why working around a
refusal is the failure the repository exists to prevent.

## Ground rules

- **No dependencies.** `pipeline/` imports the standard library and nothing
  else — no model client, no HTTP, no vendor SDK, no reference to a serving
  stack. Generation, labelling and judging arrive as commands, so a workshop
  swapping its inference stack does not touch a line of this. A gate that
  only fires on one house's plumbing is not a gate, it is a habit.
- **Gates are read, never written.** Nothing that runs may edit a threshold.
  A loop permitted to move its own threshold optimises the threshold.
- **A declaration is a record, not a switch.** `allow_self_judged`,
  `allow_nonstandard`, `allow_missing` exist so a deliberate exception can be
  recorded, and they ride on the verdict where a reader cannot skip past
  them. A change that makes one of them easier to set by default will be
  asked to change.
- **A stopped run beats a moved number.** When something is missing, the line
  says what and waits. Filling a gap with a default, an average over what
  arrived, or a guessed label is the failure mode; every one of them has
  produced a number here that looked real and was not.
- **The dependency on the benchmark runs one way.** masterwork calls the
  [journeyman](https://github.com/codechu/journeyman) CLI and imports nothing
  from it. Scoring belongs there; if an axis needs changing, it changes there.

## Setup

```
git clone https://github.com/codechu/masterwork && cd masterwork
python3 -m pytest tests/ -q
```

No build step and nothing to install to develop. `pytest` is the only
development dependency; the code under test needs nothing.

## Where contributions fit best

**Gates and instruments.** A refusal that a house learned the hard way is the
most valuable thing here, and the bar is that it be mechanical: a rule
somebody has to remember gets read, agreed with and skipped anyway. If you
can state the failure as a condition the line can check, it belongs in
`pipeline/`; if it needs a model to answer, it belongs in `tools/` behind a
command, like `tools/blind_label.py`.

**The method.** [`corpus/GROWING.md`](corpus/GROWING.md) is how a corpus is
grown — what makes a tale differ from an instruction, where a tale comes
from, what a question has to do, why instructions come last, how to tag a
tale whose effect could not be separated. Corrections and additions from
someone who has actually run this are worth more than anything else in the
list.

**Negative results.** A run that held, a gate that turned out to be void, an
axis that measured the wrong thing — these are usable if the reasoning was
frozen before the numbers arrived. Say what you expected, what you measured,
and what the threshold was before you looked. A result whose criterion was
chosen afterwards is not a result.

## What will be refused

- **A corpus.** Three starter pairs ship so the machinery runs end to end and
  the form is unambiguous. They are a beginning and meant to be outgrown. A
  tale is written from something *you* measured and got wrong; a corpus
  assembled from someone else's failures teaches an agent to avoid a life it
  never lived. We will not merge tales, and yours should not be ours.
- **A number without its stamps.** Self-judged, non-standard, or short of a
  full grid — the fact travels with the number.
- **A threshold chosen after the run.** If a frozen rule turns out to be
  wrong, say so in the record and freeze a new one for the next run. Do not
  edit the frozen file.

## Pull requests

One idea per pull request, with the test that would have caught the failure.
Say what you ran and what came back; if it held, say that too. Prose in this
repository states what the code cannot — why a refusal exists — so a change
to behaviour usually means a change to a paragraph as well.

## Status

Not published, and not proven: no candidate has yet separated from the
incumbent through a frozen gate. That is stated here rather than discovered
later. If you are here to use the line rather than improve it, read the
"Using this badly" section of the [README](README.md) first — a tool that
produces the appearance of rigour is worse than no tool, and this one can.
