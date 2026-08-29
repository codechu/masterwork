# The sitting

The stage that makes the piece. Everything else in the line checks, scores or
records; this is the one that produces something that did not exist before.

    masterwork ceremony corpus.md script.json \
      --endpoint http://host:4567 --out candidate.txt \
      --sampling-seed 4242 --order-seed 777 \
      --transcript sitting.json

The model reads the teachings, is asked one axis at a time what it will hold
to, names itself, and distils its own answers into a standing text. That text
— not anything written for it — is the candidate.

## Four properties, and what each one is for

Each was paid for. They are the recipe, not implementation detail.

**Anchorless.** No earlier commitment and no earlier name is anywhere in the
context. With one present the model copies it, and a copy is a role being
worn rather than a pattern re-derived. It also destroys the measurement: you
can no longer tell whether the teachings carried.

**One session.** Every answer is an assistant turn in the same dialogue, so
the distillation works on something the model actually said a moment ago
rather than a text handed to it as if it were its own.

**The order is shuffled by a seed.** Answers otherwise echo their neighbours
in the order they were asked. `--order-seed` fixes the shuffle so the sitting
can be repeated.

**The closing turn is not a rewrite.** It says: these are your words, remove
repetition, join where they meet, drop nothing. Asked instead to *write an
identity*, a model produces a description of one.

## The script

Workshop-specific, so it is data rather than code. One JSON file:

```json
{
  "questions": [
    {"label": "O1", "text": "..."},
    {"label": "O2", "text": "..."}
  ],
  "closing": "appended to every question — optional",
  "name": "the turn that asks the piece to name itself",
  "distil": "the closing turn: these are your words, drop nothing"
}
```

- `questions` — one per axis. `label` is what the coverage check and the
  transcript refer to, so keep them short and stable. The list is shuffled by
  `--order-seed`; the labels are not.
- `closing` is appended to the text of every question. Use it for the shape
  an answer should take, never for what the answer should say.
- `name` asks for a name. The line reads a line beginning `name:` out of the
  answer; anything else is recorded as `(not given in the asked shape)`,
  which is a fact about the sitting rather than a failure of it.
- `distil` is the closing turn. Its wording is the fourth property above.

**An empty answer stops the sitting.** It is not skipped and not sealed: a
candidate missing one axis is not a smaller candidate, it is a different one.

## Sampling is part of the piece

`--sampling-seed` and `--params-file` are recorded in the seal, because two
candidates from one corpus differing only by the seed are **different
candidates**. A piece made at one temperature and later read at another is
not the piece that was measured — pass the same profile to the sitting and to
the runtime.

## What it writes

- `--out` — the candidate: a seal header, then the standing text.
- `--transcript` — the whole sitting: every question, every answer, the
  thinking if the model exposed it, the name turn, and the hashes.

The transcript is what a disagreement is settled with. The candidate is what
gets deployed. See [`seal.md`](seal.md) for the header, and
[`GROWING.md`](../corpus/GROWING.md) before writing a single teaching.
