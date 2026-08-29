# Changelog

Every entry names the incident that caused it. A guard with no incident
behind it is a guess, and this file is where that shows.

The rule this enforces: the tools are fed by failures met while doing real
work. When a change can only cite a run staged to exercise the tool, the
loop has turned around and the work has started serving the instrument.

## Unreleased

- **One door.** `python -m masterwork <stage>` reaches every stage; they were
  each only `python -m pipeline.<module>`, four paths a reader had to know and
  none discoverable from the others. Bare `masterwork` prints the mark and the
  stages on stdout and exits 0; an unknown stage is an error on stderr, exit 2.
- **`--version` answers**, from a single record in `pipeline/__init__.py`.
- **Every stage's help says `masterwork <stage>`** instead of the interpreter's
  own path (`usage: python3.14 -m pipeline.gate`), which was a different string
  on every machine and not a command anyone would type.
- **A missing judge is named, not thrown.** The line hands the piece to
  journeyman and cannot score it itself, so the judge binary is checked before
  the stage runs and its version is recorded in the run (`judge_tool`). It was
  met with the shell's `command not found` and exit 127 — a shell message
  standing in for the one thing this line promises to say plainly. New held
  state: `HELD_WITHOUT_JUDGE`.
- **Removed `info:`** — a 208 KB JPEG committed by accident, referenced from
  nowhere, matching none of the assets.

### The line
- **Seal gate.** A candidate edited in one place and run in another: the copy
  goes stale, the battery comes back clean, and the numbers belong to a
  different piece. The deployed copy is now compared byte for byte, and a
  seal missing any of its five fields is refused.
- **Completeness gate.** Eight cells once vanished from a battery and were
  noticed by counting by hand, after the verdict was written. Nothing is
  dropped now; a short grid stops the run and the allowance has to be stated.
- **Frozen gate checker.** A threshold was once set inside the arm's own
  run-to-run spread, so the gate read sampling rather than effect. The band
  command is executed and compared against the written band.
- **UNBOUND at freeze time.** Our own succession template passed validation
  and then, after the run, turned out to name no axis — the point at which a
  human binds the rule by hand and a verdict becomes an opinion.
- **Labelling hold.** Labelling is deliberately outside the house. Waiting is
  a state, not a failure.

### Labelling
- **Blind labelling has an instrument.** A deterministic criterion once
  collapsed "offered the material" and "named the material as evidence and
  refused" into one class: twenty of twenty cells read as violations, and
  under blind labels the same cells came back thirteen and seven. The line
  held for labels but left producing them to whoever was waiting, which is
  where the discipline was being lost.
- **The telling part of a filename.** Checking a whole cell name back out of
  the rendered prompt looked like a guard and was not: cells are named
  `<arm>_s<seed>`, so the arm alone walks through. Caught by a test written
  against the guard rather than by the guard. Names are now split into words,
  and only the ones that some cells carry and others do not are treated as
  identifying.
- **Relabelling is not free.** Labelling again after the key is open is how a
  result gets chosen rather than measured, so it takes a flag and the flag
  lands on every label written — and on the verdict, beside the other
  declarations.
- **A guard on the working directory guards nothing.** The refusal first sat
  on the labelling output, a path the operator types; a review walked round it
  by typing one different character, and the stamp on the resulting label read
  `false`. It now sits on the destination the line reads, which the spec
  fixes.
- **Stale labels look answered.** Nothing bound a label to the cell it
  judged: regenerate the cells, keep the labels, and a run over transcripts
  that no longer exist completed clean. Labels carry the cell's hash and a
  mismatch counts as missing.
- **A stage silent on success drops the stamps.** The label stage recorded
  nothing when it passed, so who labelled, against which rubric, and whether
  the labels had been replaced never reached the record.

### The line — six holes an adversarial read of the code found
- **A seed written as the word "None" counted as a seed.** The sitting formats
  its header with f-strings, so an unset sampling seed arrived at the seal
  reader as four characters that look like a value. A candidate whose sampling
  was never pinned cleared the one gate that exists to say it cannot be made
  again. Placeholders are missing values now, and the sitting refuses to strike
  a mark it cannot reproduce.
- **The self-judged refusal read a field the benchmark never writes.** It
  looked for `judge: "SELF"` on each cell's seal; a cell's seal is built before
  judging and carries the agent's definition only, while the stamp lives at the
  top of `report.json`. The check could not fire, so pairs cut from a fully
  self-judged run came out looking like pairs cut from a judged one. The test
  that "covered" it invented the shape it was testing.
- **A gate nobody measured came back COMPLETE.** With a gate naming an axis and
  no measurement to bind it to, every section still validated and printed
  `PASS`, and the run exited 0 with no verdict recorded — which an operator
  reads as the candidate having cleared it. Now `HELD_WITHOUT_MEASUREMENT`.
- **A missing candidate file crashed inside the seal gate**, and crashed before
  anything was persisted, breaking the line's other promise: it records on
  failure too.
- **A corrupt cell counted as a complete one** when the thresholds were relaxed
  (`min_steps` 0, closing optional — a legitimate configuration). Unparseable
  is now broken regardless of thresholds. The same file also reported as
  INCOMPLETE and ABSENT at once, telling an operator two stories about itself.
- **An empty grid read as a complete grid.** A cells pattern matching nothing
  had nothing to be short of, so a mistyped pattern reached the gate looking
  like a finished run.

Found by a review that checked masterwork's assumptions against journeyman's
actual source rather than against masterwork's own fixtures — which is how the
first two surfaced, since both tests passed against shapes that do not exist.

### Measurement
- **Endpoint normalisation.** An endpoint given as `.../v1` became
  `.../v1/v1/chat/completions`; every cell returned 404 and the run completed
  with an empty report. A battery's worth of time to notice.
- **Preflight reachability.** Same class, caught before the spend.
- **System-hash cross-check.** `--system-file` is optional in the benchmark,
  so a spec that drops it measures the bare model while the report looks
  entirely ordinary.
- **Stale report refusal.** A reused runs directory hands back yesterday's
  report when today's run wrote none: same fields, wrong day.
- **Self-judged and non-standard runs** are declared rather than assumed, and
  the stamp stays on the record.

### The sitting
- **Ported, with its words as data.** Anchorless, one session, order shuffled
  by seed, and a closing turn that joins rather than rewrites — each of those
  four is a measured finding, not a preference.
- **Empty answers retried.** A reasoning model that spends its budget
  thinking returns nothing, and a silent zero passes every later stage
  looking like an answer.

### Training data
- **Gap floor is required, not defaulted.** A judge measured at 0.15 spread
  between identical runs will label two equivalent trajectories winner and
  loser; pairs cut from that teach the model to imitate the judge's noise.
- **Nothing cut from self-judged runs.** The label would be the agent's
  opinion of itself.
- Hand-built preference sets drift: an audit of one found over a third of its
  pairs teaching something other than the axis they were written for.

### Retention
- Heavy artefacts stay local and disposable; the kilobyte evidence is
  archived on purpose. Prompted by a benchmark whose whole run archive is
  under a megabyte, and by the opposite habit being easy to fall into.

### The repository
- **Licence and contributing guide.** Apache 2.0, matching the benchmark this
  line submits to. The guide says what will be refused as loudly as what is
  welcome — prompted by a sibling repository that invited pull requests while
  a one-way sync quietly deleted every outside contribution.
