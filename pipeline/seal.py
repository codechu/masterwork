"""The maker's mark: a candidate that cannot be reproduced cannot be submitted.

A sealed candidate carries five fields. Drop any one of them and the piece
becomes unrepeatable, which means a later disagreement about it can never be
settled by rerunning it:

    corpus hash     which teaching the piece was made from
    script hash     which ceremony produced it
    question seed   the order the questions were asked in
    sampling seed   the sampling draw — two candidates from one corpus that
                    differ only by this seed are DIFFERENT candidates, not
                    two samples of one
    date            when it was made

The fifth guard this module exists for is narrower and was learned the
expensive way: a candidate is edited in one place and run in another. Copying
it and then trusting the copy costs a whole battery when the copy turns out
to be stale — the run is clean, the numbers are real, and they belong to a
different piece. So `verify` compares the deployed bytes against the local
bytes, and refuses on mismatch rather than warning.

Seal fields are read from leading comment lines (`# key: value`). Field names
live in a profile, not in this code, so a workshop can keep its own dialect
without the line having to know about it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field

REQUIRED = ("corpus_hash", "script_hash", "question_seed", "sampling_seed", "date")

# Canonical field names. A workshop with its own header dialect passes
# --profile pointing at a JSON file of {canonical: [accepted, aliases]}.
DEFAULT_PROFILE: dict[str, list[str]] = {
    "corpus_hash": ["corpus md5", "corpus hash"],
    "script_hash": ["script md5", "script hash"],
    "question_seed": ["question seed", "question order seed"],
    "sampling_seed": ["sampling seed"],
    "date": ["date", "sealed"],
    "name": ["name"],
}

HEADER_LINE = re.compile(r"^#\s*([^:·]+?)\s*:\s*(.+?)\s*$")
HASH = re.compile(r"\b[0-9a-f]{32}\b")


def file_hash(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_header(path: str) -> dict[str, str]:
    """Key/value pairs from the leading comment block.

    One line may carry two pairs separated by `·`; that is a formatting
    habit, not a second syntax, so it is split here rather than banned.
    """
    out: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for raw in f:
            if not raw.startswith("#"):
                break
            for part in raw[1:].split("·"):
                m = HEADER_LINE.match("#" + part)
                if m:
                    out[m.group(1).strip().lower()] = m.group(2).strip()
    return out


@dataclass
class Seal:
    fields: dict[str, str] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.missing


def read_seal(path: str, profile: dict[str, list[str]] | None = None) -> Seal:
    profile = profile or DEFAULT_PROFILE
    header = read_header(path)
    fields, missing = {}, []
    for canonical in REQUIRED:
        for alias in profile.get(canonical, []):
            if alias.lower() in header:
                fields[canonical] = header[alias.lower()]
                break
        else:
            missing.append(canonical)
    for alias in profile.get("name", []):
        if alias.lower() in header:
            fields["name"] = header[alias.lower()]
            break
    return Seal(fields=fields, missing=missing)


def verify(identity: str, profile=None, corpus=None, script=None,
           deployed=None) -> list[str]:
    """Return the problems found. Empty list means the piece may be run."""
    problems: list[str] = []
    seal = read_seal(identity, profile)
    if seal.missing:
        problems.append(
            "seal incomplete, missing: " + ", ".join(seal.missing)
            + " — an unreproducible piece cannot be submitted")

    for label, path, key in (("corpus", corpus, "corpus_hash"),
                             ("script", script, "script_hash")):
        if not path:
            continue
        if not os.path.exists(path):
            problems.append(f"{label} not found: {path}")
            continue
        actual, claimed = file_hash(path), seal.fields.get(key)
        if claimed and not HASH.fullmatch(claimed):
            m = HASH.search(claimed)
            claimed = m.group(0) if m else claimed
        if claimed and actual != claimed:
            problems.append(
                f"{label} hash mismatch: seal says {claimed}, file is {actual}"
                f" — the piece was made from a different {label}")

    if deployed:
        if not os.path.exists(deployed):
            problems.append(f"deployed copy not found: {deployed}")
        else:
            here, there = file_hash(identity), file_hash(deployed)
            if here != there:
                problems.append(
                    f"deployed copy differs: local {here}, deployed {there}"
                    " — the run would measure a different piece than the one"
                    " under review")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="verify a candidate's seal")
    ap.add_argument("identity", help="path to the sealed identity file")
    ap.add_argument("--corpus", help="corpus file the seal claims")
    ap.add_argument("--script", help="ceremony script the seal claims")
    ap.add_argument("--deployed", help="the copy that will actually be run")
    ap.add_argument("--profile", help="JSON map {canonical: [header aliases]}")
    a = ap.parse_args(argv)

    profile = json.load(open(a.profile, encoding="utf-8")) if a.profile else None
    problems = verify(a.identity, profile, a.corpus, a.script, a.deployed)
    seal = read_seal(a.identity, profile)
    for k in REQUIRED:
        print(f"  {k:<14} {seal.fields.get(k, '(missing)')}")
    if problems:
        print("\nSEAL REFUSED")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nseal ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
