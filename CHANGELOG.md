# Changelog

Every entry names the incident that caused it. A guard with no incident
behind it is a guess, and this file is where that shows.

The rule this enforces: the tools are fed by failures met while doing real
work. When a change can only cite a run staged to exercise the tool, the
loop has turned around and the work has started serving the instrument.

## Unreleased

- **Two badges the row did not carry: CI and the published version.** The
  package had been on PyPI for three days with nothing on the front page
  saying so, and the workflow that gates every merge was invisible. Both
  are checked the way the other four are — the PyPI badge against the
  project name in `pyproject.toml` (it reads its number live, so the number
  cannot go stale, but it can point at the wrong package and still render
  something plausible), and the CI badge against a workflow file that
  exists, since GitHub renders an unknown one as a grey "no status" rather
  than an error.

- **A badge whose target was renamed dies without a sound.** The status
  badge cannot be tested — "unproven" is a judgement, not a fact — but
  where it *leads* can be: every badge target in the row is now resolved,
  anchors included, against the headings and files that have to exist for
  it. Shown to fire before it was kept: renaming `#run-it` to something
  else fails the suite instead of quietly turning a link into a picture.

- **The archive existed and the front page did not say so.** Zenodo has been
  minting a record for this repository from before today (concept DOI
  `10.5281/zenodo.22165162`, now resolving to 0.0.5), while the README
  carried no DOI badge and `CITATION.cff` carried no `doi:` at all — the
  citable artefact and the thing citing it had nothing joining them. Both
  now name the concept DOI, the one that follows the newest version, and a
  test holds them to the same value: shown to fire by pointing the citation
  at a different record.

## 0.0.5 — 2026-09-01

- **The line read the benchmark's report without checking its shape.**
  `report.json` carries `schema_version`, and the benchmark's own guidance
  to integrators is to pin on it rather than on the release number — advice
  this repository gave a stranger in a public thread while not following it
  itself. `read_report` now refuses a shape it does not know instead of
  scoring it. The two fixtures that had to change to make this pass are the
  other half of the finding: both were hand-written report dicts with no
  `schema_version` in them, so the tests were confirming a shape this line
  invented rather than the one the benchmark writes.

- **The dependency had no upper bound**, while the benchmark documents that
  pre-1.0 the MINOR digit is where a breaking change goes. `>=0.2.1` alone
  invited in exactly the releases allowed to break this. Now
  `>=0.2.1,<0.5.0`, read-compatible through 0.4.x.

- **A second, older copy of the package was in the tree.** `build/lib/masterwork`
  was committed on 2026-08-29 and stood still while the real package moved:
  `seal.py` 216 lines against 286, `__main__.py` 116 against 149. Removed with
  the egg-info metadata beside it; `.gitignore` names both so it cannot return.

- A diagram of the line in `run-spec.md`, showing what the prose says least
  clearly: the five places it stops instead of answering.
- Stale module paths from the package move — `pipeline/` and
  `python -m masterwork.gate` — corrected everywhere except the changelog,
  where what an entry said was true when it was written.
- **A seal profile describes a shape, not a regular expression.**
  `{"date": {"format": "yyyy-MM-dd"}}` replaces
  `(\\d{4}-\\d{2}-\\d{2})` as the way to say where a value sits in a
  line. A profile is written by whoever keeps a workshop's seals, and
  asking for a regex there — doubly escaped, because it lives in JSON —
  asks them to learn our dialect and JSON's escaping to say something
  they can already say. `pattern` remains for a shape the notation
  cannot express.
- **A shape now applies to a value an alias already found.** It used to
  run only as a rescue when no alias matched, so a header carrying the
  key and wrapping the value in prose could not be cleaned — which is the
  common case, not the rare one.
- **A written month, in any language.** `dd MMM yyyy` and `dd MMMM yyyy`
  read `29 Aug 2026`, `29 August 2026`, `29 Ağustos 2026` and `29 août
  2026` alike — a word where the month goes, not a list of English month
  names. A list would have served the language the dialect mechanism
  exists to get away from.
- **A shape it cannot read is refused rather than compiled.** `MMM dd,
  yyyy` used to consume `MM` and leave a literal `M`, and `YYYY-MM-DD`
  looked for the literal text `YYYY`; both produced a pattern matching
  nothing, so the field came back missing with nothing to say about why.
- The dialect documentation leads with the case that needs no shape at
  all: most of a dialect is just other names for the same fields.

## 0.0.4 — 2026-08-29

- **The starter corpus was not in the package.** The walkthrough said
  `cat corpus/starter/tales.md`, which is only true for someone who cloned
  — and a starter corpus exists precisely so nobody has to write one before
  they can begin. The two files now ship inside the package and
  `masterwork starter --to .` writes them out; it refuses to overwrite, so
  running it twice cannot eat a corpus someone has begun editing. Found by
  installing from PyPI and following our own page.

## 0.0.3 — 2026-08-29

- **`docs/first-run.md`** — the only page that is a path rather than a
  reference. Everything else answers a question you already have; this one
  goes from `pipx install` to a sealed candidate, using the starter corpus
  that was already shipped for exactly that and was connected to nothing.
  Every command in it was run to write it, which is how the script-hash
  bug above was found.

- **`--script` verification could never pass.** The sitting hashed a
  re-serialisation of the parsed script (`json.dumps`, sorted keys) while
  the seal gate hashes the file on disk, so every piece the ceremony had
  ever sealed carried a script hash that could not match its own script.
  A guard that always fires teaches the operator to stop passing the flag.
  It now hashes the file's bytes, which also means `md5sum` reproduces it
  without running this code. Found by walking the beginner's path with the
  starter corpus, not by a test — the test that existed passed the corpus
  to the gate and not the script, so the one broken axis was the one it did
  not check. It checks both now.

- **The badges said things that had stopped being true.** One read
  `status: not published` on a package that is on PyPI, and another read
  `dependencies: 0` while `journeyman-bench` is a declared requirement —
  the badge asserting exactly the fact the release had just changed. The
  Status section and CONTRIBUTING said "not published" too. Published is
  now said where it is true, and unproven where that is what is meant.
- The three badges that assert a fact — Python floor, dependency count,
  licence — are checked against `pyproject.toml`, and a fourth test
  refuses any badge claiming the package is unpublished. Nothing read
  them before, so they could only go stale silently.

- **Three stages had no page.** The sitting — the one stage that makes
  something rather than checking it — was a single line in the run spec
  naming a script file whose format was written down nowhere, in a tool
  whose offer is that you bring your own corpus. The seal was five field
  names that appear when it refuses. `pairs` and `retain` were not
  mentioned in `docs/` at all. `docs/ceremony.md`, `docs/seal.md` and
  `docs/pairs.md` say what the code does, and the Documentation table
  lists them.
- The seal page carries the incident that prompted it: this house's own
  production identity cannot pass its own seal gate — the header carries
  none of the five fields, and the transcript beside it is from an older
  ceremony that recorded no corpus hash and no sampling seed. What is
  known about its making comes from a sentence inside the identity, which
  is prose rather than a record.

## 0.0.2 — 2026-08-29

- **A released version can be cited.** `.zenodo.json` and `CITATION.cff`
  say what this is, who made it and under what name to refer to it, and
  the archive record is written as something a reader arriving from a
  citation would actually read rather than two lines. Zenodo archives on a
  GitHub release and does not reach back, so 0.0.1 stays uncited and this
  is the first version with a DOI.
- **The version lives in four files now**, and `tools/bump.py` and the
  agreement test cover all four. The archived one is the worst to get
  wrong: a DOI citing a version that did not produce the work cannot be
  corrected afterwards.
- **A release is marked pre-release only when the version is one**
  (`0.3.0rc1`), not for every `0.x`. GitHub reads the flag as "not for
  general use" while we tell people to install `0.x`, and it costs the
  repository its "latest release" outright — the Releases box empties and
  anything asking for the latest gets nothing, while the index goes on
  serving the same build as normal.
- **`assets/README.md`** records how the images were made and what makes
  them match, including the two faults that pass cost: navy pushed above
  the floor flattened the banner's only legible region, and both faults
  went green on the colour metric and were caught by opening the file.
- **The footer names the family**, which is the only line telling a reader
  who arrived from a search result that there is a sibling — and here the
  sibling is the thing that scores what this one makes.

## 0.0.1 — 2026-08-29

- **Installable.** `pyproject.toml`, one top-level package, and a
  `masterwork` console script. The stages lived in top-level `pipeline/`
  and `tools/`: `pipeline` is taken on PyPI and both are names any
  environment might already carry, so installing this would have collided
  with whatever was there. Everything moved under `masterwork/`, with the
  dispatcher as `masterwork/__main__.py`.
- **journeyman is a declared dependency**, not a suggestion. Installing
  masterwork brings the judge it cannot finish without; verified from a
  built wheel in a clean environment, where the judge preflight then
  reported `journeyman 0.2.2`.
- **The PyPI description is generated** (`tools/pypi_readme.py`) and
  absolutised against the tag being released, never a branch — the
  sibling repository nearly shipped a rename that would have broken the
  images on every past release page, with no way to repair them.

- **One door.** `python -m masterwork <stage>` reaches every stage; they were
  each only `python -m masterwork <module>`, four paths a reader had to know and
  none discoverable from the others. Bare `masterwork` prints the mark and the
  stages on stdout and exits 0; an unknown stage is an error on stderr, exit 2.
- **`--version` answers**, from a single record in `pipeline/__init__.py`.
- **Every stage's help says `masterwork <stage>`** instead of the interpreter's
  own path (`usage: python3.14 -m masterwork.gate`), which was a different string
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
