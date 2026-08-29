# Your first piece

Everything else in `docs/` is reference: it answers a question you already
have. This walks one path from nothing to a sealed candidate, and then says
what the measured half costs. Every command below was run to write this page.

Five minutes for the first three steps. The fourth needs a model endpoint;
the fifth needs a judge.

## 1. Install, and prove it offline

```bash
pipx install masterwork
masterwork
```

The bare command prints the stages. Nothing has been bought and nothing is
running yet.

```bash
git clone https://github.com/codechu/masterwork && cd masterwork
python examples/held_at_gate.py
```

It ends `HELD_AT_GATE` and exits non-zero **on purpose**: it demonstrates a
run the gate refused, because stopping is the thing this line is for. A tool
that only showed you its happy path would be showing you the wrong thing.

## 2. Read the two files you will start from

```bash
cat corpus/starter/tales.md      # three tales
cat corpus/starter/script.json   # three questions, one per tale
```

One question per tale, always. Read
[`corpus/GROWING.md`](../corpus/GROWING.md) before you write a fourth of
either — the invariant is the point, not the count.

## 3. Hold a sitting

You need an OpenAI-compatible endpoint serving whatever model you want the
piece made from.

```bash
masterwork ceremony corpus/starter/tales.md corpus/starter/script.json \
  --endpoint http://your-host:8080 \
  --out candidate.txt --transcript sitting.json \
  --order-seed 777 --sampling-seed 4242
```

```
sitting: 3 questions, order seed 777, sampling seed 4242
  wall (954 chars)
  relief (1410 chars)
  ledger (1966 chars)
  name: Tally
  standing text: 1414 chars
sealed -> candidate.txt
```

`candidate.txt` is a seal header and then the standing text — the model's own
commitments, in its own words. `sitting.json` is the whole conversation,
which is what a disagreement six weeks later is settled with.
See [`ceremony.md`](ceremony.md) for why the sitting has the shape it does.

## 4. Check the seal

```bash
masterwork seal candidate.txt \
  --corpus corpus/starter/tales.md --script corpus/starter/script.json
```

```
  corpus_hash    499914c8110b5446fff7a361d4bb506a
  script_hash    d11c88bf9649c861a374cd77d3f75f16
  question_seed  777
  sampling_seed  4242
  date           2026-08-29

seal ok
```

Both hashes are the files' own, so `md5sum` reproduces them without running
any of this. A candidate that cannot be produced again is an anecdote; see
[`seal.md`](seal.md), including what to do when the gate refuses a piece made
before it existed.

## 5. What the measured half costs

The line does not score. It hands the piece to `journeyman`, which arrived
with the install, and carries the verdict — so scoring needs two things you
supply:

- **an endpoint running the agent under test**, with your candidate as its
  system text;
- **a judge that has passed journeyman's calibration exam.** `journeyman
  qualify` grants or refuses the badge; the registry of who passed and who
  failed ships with it. A run judged by an unqualified judge, or by the agent
  itself, is stamped and cannot reach a threshold here.

Then one JSON file describes the run, field by field in
[`run-spec.md`](run-spec.md):

```bash
masterwork line spec.json --out runs
```

Expect ten to sixty minutes for a standard set, and a judge's API bill in
cents rather than dollars. What you get is `runs/<name>/run.json`: stage by
stage, with the verdict and the measurement, in kilobytes.

## 6. Before you draw a conclusion from it

One run of one arm decides almost nothing. A threshold set below an arm's own
run-to-run spread reads noise and calls it an effect, which is the most
expensive mistake available here.

- [`campaigns.md`](campaigns.md) — repeating an arm to measure its band, then
  comparing two arms against that band.
- [`gates.md`](gates.md) — writing a threshold that can hold, frozen before
  the run rather than chosen after it.
- [`pairs.md`](pairs.md) — turning a scored run into training data, and why
  the minimum gap has no default.

And [`AGENTS.md`](../AGENTS.md), which is the shortest thing here and says
what this tool refuses to do.
