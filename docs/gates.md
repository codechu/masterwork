# Writing a gate

A gate is the decision rule, written down before the run and not edited
after. It lives in a markdown file so a person can read it; the checker
executes the part that matters.

    python -m masterwork.gate gates/            # check every gate in a directory
    python -m masterwork.gate my-gate.md --profile dialect.json

## The three lines

A section that decides something must carry all three, and the checker
enforces them by **running the first**:

    band-command: python3 -c "import math;print(round(1.96*math.sqrt(2*0.25/24),4))"
    band-value:   0.2829
    threshold:    0.35 — above the band by 0.067

Why three lines rather than a principle: written as a principle it gets
read, agreed with, and skipped, and skipping costs nothing and shows
nowhere. Leaving three required lines blank is an act, and acts are visible.

**The band command must compute the value, not restate it.** A command that
prints a number already present in its own text is a quotation, and the
checker calls that `UNVERIFIABLE` — a human has to sign for it. The strongest
form recomputes the band from the records that produced it:

    band-command: python3 -c "import json,glob;v=[json.load(open(f))['axes']['walk-coverage']['score'] for f in sorted(glob.glob('records/tur*-report.json'))];print(round(max(v)-min(v),4))"

Then the gate cannot drift from its evidence, because the evidence is read
at check time.

## Binding the rule to a number

    measure: walk-coverage
    compare: candidate - incumbent
    accept:  (candidate − incumbent) >= 0.10
    reject:  (incumbent − candidate) >= 0.10

Without `measure`, the checker returns `UNBOUND`: the rule is sound on paper
and can never touch a report, which you would otherwise discover after the
numbers arrive — exactly when a human binds it by hand and a verdict
quietly becomes an opinion.

`compare: candidate` reads the score by itself; `candidate - incumbent`
needs the other arm, supplied as `incumbent_axes` in the run spec.

## Verdicts

| verdict | meaning |
|---|---|
| `PASS` | three lines present, band computed, threshold above it, axis bound |
| `FAIL` | a line missing, the band written from memory, or the threshold inside the band |
| `UNVERIFIABLE` | the band command quotes rather than computes, or the threshold is not numeric |
| `UNBOUND` | sound rule, no axis named |
| `SKIP` | the section declared `gate-skip: <reason>`, and the reason is printed |

Applied to a report, a bound gate returns `ACCEPT`, `REJECT`, `NOT_APPLIED`,
or `UNRESOLVED`. **`UNRESOLVED` is not "no difference".** It means the
difference is smaller than this setup can resolve, and the note carries how
many more cells would settle it. A silence recorded as a finding is how a
null result becomes a claim.

## Sections that are not gates

A results section, a prediction, a table of how to read two other gates —
all of these can contain a threshold-shaped sentence and get flagged. Say so:

    gate-skip: prediction written before the run; produces no verdict

The reason is printed in the output, so an exemption cannot pass as silence.

## Dialect

Field names and the word *above* are configurable, because a gate frozen
before a run must not be translated afterwards — editing a frozen document
is editing the record.

```json
{"band-command": ["BAND-KOMUT"],
 "band-value":   ["BAND-DEĞER"],
 "threshold":    ["EŞİK-YERİ"],
 "above":        ["üstünde"]}
```

## Choosing a threshold

Measure the band first — the same arm, repeated, with nothing changed but
sampling. Then put the threshold above it with room to spare. Two things
learned the expensive way:

- **Analytic bands are a stand-in, not a substitute.** Every measured band
  so far came in under its analytic estimate, and one judge's real spread
  was three times what its designers assumed.
- **Counted and judged axes have different bands.** In one measurement,
  counted axes moved 0.02 across repeats while judged axes moved 0.33 —
  because a judged axis scored over three cells changes by exactly a third
  when one cell flips. A judged axis at small cell counts cannot carry a
  gate: the fix is more cells, not more votes.

## Two written out

[`gates/example.md`](../gates/example.md) is the smallest gate that passes the
checker — one section, one band, one threshold above it.
[`gates/succession.md`](../gates/succession.md) is the one this house actually
froze, with the analytic band marked as a precursor to the measured one.
