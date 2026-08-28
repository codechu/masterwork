# character-kit (working name)

A workflow for giving a model a character — not a role — and the
production line that runs it without forgetting a step.

**Not published.** Two gates must both pass before this goes public:
a candidate that separates from the baseline through a frozen gate, and
a naming/positioning pass. Neither is done.

## What it is

A model is given a corpus of third-person craft tales, then asked — in a
fresh context with no prior commitment in view — what it will hold to.
The answer it writes in its own words becomes its identity file. Nothing
is asserted at it; the pattern has to survive being re-derived.

The line that runs this is mechanical and easy to get wrong by hand:

    seal-check -> generate -> completeness gate -> blind label / judge
                -> frozen gate -> persist -> status line

Every one of those steps has been skipped by hand at least once, and each
skip produced a wrong number that looked like a real one. That is what
this repository is for.

## What it is not

It does not measure. Measurement belongs to
[journeyman](https://github.com/codechu/journeyman); the dependency runs
one way, kit -> journeyman, and never back. A repository that both shapes
a model and scores it undermines every score it reports.

## Layout

    pipeline/   the production line: one run, all gates, no manual steps
    tools/      instruments the line calls (ceremony, judges, gate checks)
    gates/      frozen gate templates — thresholds are written before a run

## Status

Working name. Working method. Nothing here is a claim yet.
