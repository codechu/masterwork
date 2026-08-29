# The seal

A candidate that cannot be produced again is not a candidate, it is an
anecdote. The seal is the header the sitting writes above the standing text,
and the gate that refuses anything without it.

    masterwork seal candidate.txt
    masterwork seal candidate.txt --corpus corpus.md --script script.json
    masterwork seal candidate.txt --profile our-dialect.json

## The five fields

| field | why it is there |
|---|---|
| `corpus_hash` | which teachings the piece was made from |
| `script_hash` | which questions were asked, in which wording |
| `question_seed` | the shuffle — the order answers were given in |
| `sampling_seed` | two candidates differing only in this are different candidates |
| `date` | when the sitting happened, machine-readable |

`name` is read when present and is not required.

The sitting writes them itself:

```
# name: Truehand
# corpus hash: 9f2c…
# script hash: 4ab1…
# question seed: 777 · sampling seed: 4242
# date: 2026-08-29T16:13:04
```

## What the gate does

- **Missing fields → refused.** The message names them. An incomplete seal is
  not a warning: the piece cannot be submitted.
- **`--corpus` / `--script` given → hashed and compared** with what the seal
  claims. A seal that says one corpus while the file is another is worse than
  no seal, because it looks answered.
- **`--deployed` given → compared byte for byte** with the candidate. A piece
  edited in one place and run in another gives a clean battery whose numbers
  belong to a different piece. This is the failure the flag exists for.

## When the header is in another dialect

A workshop that writes its own headers should not edit them to please the
reader. Teach the reader the dialect instead.

**Most of it is just names.** The defaults already accept `corpus md5` /
`corpus hash`, `script md5` / `script hash`, `question seed` /
`question order seed`, `sampling seed`, and `date` / `sealed`; a header in
another language needs nothing but its own words:

```json
{"corpus_hash": ["korpus md5"], "date": ["tarih"]}
```

**When the value carries more than the value**, give its shape — in the
notation you would use to describe a date, not as a regular expression:

```json
{"date": {"aliases": ["sealed"], "format": "yyyy-MM-dd"}}
```

That reads `sealed on 2026-08-29 by the workshop` as `2026-08-29`.

| token | reads |
|---|---|
| `yyyy` `yy` | a four- or two-digit year |
| `MM` `dd` | a two-digit month or day |
| `MMM` `MMMM` | a written month — **a word, in any language**: `Aug`, `August`, `Ağustos`, `août` |
| `HH` `mm` `ss` | two-digit hour, minute, second |

Everything else is literal, so `dd MMMM yyyy`, `MM-dd-yyyy` and
`yyyy-MM-ddTHH:mm:ss` all say what they look like. A written month is not
matched against a list of month names: the dialect mechanism exists so a
workshop can keep its own headers, and half the point of that is that they
are not in English.

A shape applies whether or not an alias matched — a header that has the key
and wraps the value in prose is the common case, not the rare one. A shape
this cannot read is **refused** rather than compiled: `YYYY-MM-DD` would
otherwise look for the literal text `YYYY`, find nothing, and report the
field as missing with nothing to say about why.

**`pattern` remains** for a shape `format` cannot express, and takes a
regular expression. It is the exception; if you find yourself reaching for
it often, the shape notation is missing something and that is worth
saying.

**A shape locates a value; it does not rewrite one.** `dd/MM/yyyy` reads
`29/08/2026` as `29/08/2026`, not as `2026-08-29`. Nothing here parses a
date, compares two, or sorts by one — the field's job is that the sitting
recorded when it happened and did not leave it blank. Because `format`
says which part is the year, normalising becomes possible the day two
workshops' seals need comparing; a regular expression could never have
told us that much, which is the difference between the two notations.

**A sealed file is its bytes.** Changing them to satisfy the gate is the one
repair that is never correct.

## A piece made before the gate existed

It will be refused, and that refusal is information rather than an obstacle
to route around: it says the provenance was never recorded. *Incident: the
piece in this house's own production could not pass — its header carried
none of the five, and the transcript beside it was from an older ceremony
that recorded no corpus hash and no sampling seed. What was known about its
making came from a sentence inside the identity itself, which is prose, not a
record.* Such a piece can still be measured; it cannot be reproduced, and a
run that measures it should say so rather than seal it retroactively.
