---
name: Bug report
about: A stage of the line did something it should not have
labels: bug
---

**What happened**
A clear description of the problem, and which stage it happened in
(ceremony, seal, measure, gate, pairs, retain).

**To reproduce**
The exact `masterwork ...` command and the run-spec you used (redact
endpoints and keys; the shape is what matters).

**Attach**
The seal of the candidate and the `report.json` the judge stage read back,
if the failure involves a measurement. A gate refusal usually names itself
in one line — paste that line verbatim rather than a summary of it.

**Environment**
`masterwork --version` · `journeyman --version` · Python version · OS.
