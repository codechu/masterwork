**What & why**
What this changes and the incident behind it. A guard with no incident
behind it is a guess — the changelog says so on its first page, and an
entry that can only cite a run staged to exercise the tool is the loop
turning around.

**Checklist**
- [ ] `python3 -m pytest tests/ -q` passes
- [ ] no new runtime dependencies (the only one is the benchmark, bounded)
- [ ] anything read from `report.json` is read against the shape the
      benchmark actually writes, and the fixture says where that shape
      lives (`# shape: <file:line>`)
- [ ] no verdict a thing gives itself: self-judged runs stay ungateable
- [ ] CHANGELOG entry naming the incident, not the feature
