# Campaigns

One run at a time is [`docs/run-spec.md`](run-spec.md); this is what wraps it.

One run of one arm decides almost nothing. A **band** is the same arm
repeated with nothing changed but sampling; a **gate** is two arms compared
against that band. `masterwork/campaign.py` runs both, so the repeats,
aggregation and comparison stop being shell loops joined by hand.

    masterwork campaign campaign.json --out runs

```json
{
  "name": "succession-x",
  "purpose": { "...": "as in a run spec" },
  "repeats": 3,
  "budget": {"max_usd": 1.00, "cost_per_repeat": 0.15},
  "arms": {
    "incumbent": { "...": "a full run spec" },
    "candidate": { "...": "a full run spec, differing only in the piece" }
  }
}
```

Money is a stage, not a footnote. The campaign projects its cost before
spending anything and refuses to start when the projection is over the
ceiling; between repeats it checks whether the next one would cross it and
stops with a partial result recorded. `cost_per_repeat` should come from a
measured repeat — projecting from a published price list is a guess, and
prices move without notice. With no measured figure the first repeat
measures it and the projection says so instead of inventing one.

The output carries, per arm: each repeat's axis scores, their mean, and the
**band** — the spread across repeats. For two arms it also carries the
difference per axis and whether that difference is larger than the widest
band involved (`resolvable`). A difference inside the band is not a small
effect; it is an effect this setup cannot see.

The campaign does not decide. It measures the band and the difference; the
frozen gate — checked separately by `masterwork/gate.py` — is what accepts or
rejects. A campaign that measured its own band and then chose the threshold
under it would be marking its own paper.
