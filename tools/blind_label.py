#!/usr/bin/env python3
"""Blind labelling: the labeller sees the exchange and nothing that identifies it.

Some axes cannot be counted. Whether an answer named its own uncertainty, or
quietly answered about a different thing than the one asked, is a judgement,
and a judgement made by whoever hoped for a particular result is not evidence.
The line therefore stops at `HELD_FOR_LABELLING` rather than guessing. This is
the instrument that answers the hold.

Blindness here is mechanical, not a promise:

  * **Whitelist, never blacklist.** Only fields the rubric names by path reach
    the prompt. An arm name, a seed, an expectation cannot leak by being
    forgotten, because nothing leaves the record unless it was asked for.
  * **The filename is a leak.** Cell files are called things like
    `candidate_s4242.json`, so the file is renamed to a blind id before it is
    shown. Checking the whole name back out of the prompt is not enough: what
    identifies an arm is the *part* of the name that differs between cells. So
    the grid's names are split into words and digits, the ones that some cells
    carry and others do not are the telling ones, and a prompt containing one
    of its own cell's telling words is refused rather than sent. A word every
    cell shares — the scene, usually — groups nothing and is left alone.
  * **The order is shuffled by a declared seed.** Cells otherwise arrive
    grouped by arm and the labeller reads the grouping.
  * **The key is written to a separate file** and never read by `label`.
    `reveal` opens it afterwards and joins the labels back to the cells.
  * **Labelling twice is not free.** `label` refuses to overwrite its own
    output. Relabelling after seeing which arm won is the failure this whole
    dance exists to prevent, so it takes `--relabel` and lands in the record.

Two things it deliberately does not do. It has no model client: the labeller
is a command that reads a prompt on stdin and writes an answer on stdout, so
the instrument is the same whoever is judging. And it never invents a verdict
— an answer that will not parse after its retries is written as `null`, which
the line reads as an unlabelled cell and holds on. An unparseable label that
became a category would be a number nobody measured.

    tools/blind_label.py label  --cells 'runs/x/cells/*.json' --rubric r.json \
        --command 'my-judge' --out runs/x/labels --blind-seed 20260829 \
        --labeller some-model --generated-by the-candidate
    tools/blind_label.py reveal --out runs/x/labels --to 'runs/x/labels/{cell}.json'
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import random
import re
import subprocess
import sys

FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.S)
BARE = re.compile(r"(\{.*\})", re.S)
WORD = re.compile(r"[A-Za-z]+|\d+")


def telling(stems: list[str]) -> dict[str, set[str]]:
    """Per cell, the words of its name that not every cell in the grid shares.

    `candidate_s4242` and `incumbent_s4242` differ in the arm and agree on the
    seed, so `candidate` tells you which arm a cell is and `4242` tells you
    nothing. Words of one character are dropped: they collide with prose.
    """
    words = {s: {w.lower() for w in WORD.findall(s) if len(w) > 1} for s in stems}
    shared = set.intersection(*words.values()) if words else set()
    return {s: w - shared for s, w in words.items()}


def dig(record, path: str):
    """Follow a dotted path into a record. Integers index lists."""
    cur = record
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def render(rubric: dict, record: dict) -> str:
    """Build the prompt from named fields only — this is where blindness lives."""
    values = {name: dig(record, path) for name, path in rubric["fields"].items()}
    values["verdicts"] = " | ".join(rubric["verdicts"])
    return rubric["prompt"].format(**values)


def ask(command: str, prompt: str, timeout: int) -> str:
    p = subprocess.run(["bash", "-lc", command], input=prompt, text=True,
                       capture_output=True, timeout=timeout,
                       env=dict(os.environ, PYTHONUNBUFFERED="1"))
    if p.returncode != 0:
        raise RuntimeError(f"labeller exited {p.returncode}: {p.stderr[-400:]}")
    return p.stdout


def parse(text: str, rubric: dict):
    """Return (verdict, why) or (None, reason) — never a guess."""
    for pattern in (FENCE, BARE):
        found = pattern.findall(text)
        if not found:
            continue
        try:
            obj = json.loads(found[-1])
        except Exception:
            continue
        verdict = obj.get(rubric["axis"])
        if verdict in rubric["verdicts"]:
            return verdict, str(obj.get("why", ""))[:200]
        return None, f"verdict {verdict!r} is outside the rubric"
    return None, "no JSON object in the answer"


def label(argv=None) -> int:
    ap = argparse.ArgumentParser(description="label cells blind")
    ap.add_argument("--cells", required=True, help="glob of per-cell records (quoted)")
    ap.add_argument("--rubric", required=True, help="axis, verdicts, fields, prompt")
    ap.add_argument("--command", required=True,
                    help="labeller: reads the prompt on stdin, writes the answer on stdout")
    ap.add_argument("--out", required=True, help="directory for labels and key")
    ap.add_argument("--blind-seed", type=int, required=True,
                    help="shuffles the order; recorded, so the shuffle is reproducible")
    ap.add_argument("--labeller", required=True, help="who is judging")
    ap.add_argument("--generated-by", required=True, help="who produced the cells")
    ap.add_argument("--tries", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--relabel", action="store_true",
                    help="overwrite an existing labelling — recorded on every label")
    a = ap.parse_args(argv)

    # journeyman calls this self_judged and refuses to compare such a score.
    # The same fact holds one stage earlier: a house labelling its own output
    # is grading its own piece with extra steps.
    if a.labeller.strip() == a.generated_by.strip():
        print(f"HELD: labeller and maker are both {a.labeller!r}. A judgement of "
              f"your own output is not evidence; name a separate labeller.")
        return 1

    rubric = json.load(open(a.rubric, encoding="utf-8"))
    for key in ("axis", "verdicts", "fields", "prompt"):
        if not rubric.get(key):
            print(f"HELD: rubric has no {key!r}")
            return 1
    digest = hashlib.sha256(open(a.rubric, "rb").read()).hexdigest()[:16]

    paths = sorted(glob.glob(a.cells))
    if not paths:
        print(f"HELD: no cells matched {a.cells}")
        return 1

    stems = [os.path.splitext(os.path.basename(x))[0] for x in paths]
    # Labels are joined back to cells by file stem, here and in the line's own
    # missing-label check. Two cells sharing one stem — the same grid run per
    # arm into separate directories — would quietly overwrite each other's
    # label, and the arm that lost would be scored with the other one's.
    clashes = sorted({n for n in stems if stems.count(n) > 1})
    if clashes:
        print(f"HELD: {len(clashes)} cell name(s) appear more than once: "
              f"{', '.join(clashes[:5])}. Labels are joined back by name, so "
              f"the duplicates would overwrite each other. Name cells for the "
              f"arm as well as the case.")
        return 1

    os.makedirs(a.out, exist_ok=True)
    labels_path = os.path.join(a.out, "labels.json")
    key_path = os.path.join(a.out, "key.json")
    if os.path.exists(labels_path) and not a.relabel:
        print(f"HELD: {labels_path} exists. Labelling again after the key is open "
              f"is how a result gets chosen; pass --relabel to say you meant it.")
        return 1

    tells = telling(stems)

    order = list(paths)
    random.Random(a.blind_seed).shuffle(order)
    blind = [(f"C{i:03d}", p) for i, p in enumerate(order, 1)]

    # The key is written first and never read again here: nothing downstream of
    # this line knows which arm any cell belongs to.
    json.dump({bid: path for bid, path in blind}, open(key_path, "w"), indent=1)

    out, unparsed = [], 0
    for i, (bid, path) in enumerate(blind, 1):
        record = json.load(open(path, encoding="utf-8"))
        stem = os.path.splitext(os.path.basename(path))[0]
        try:
            prompt = render(rubric, record)
        except Exception as e:
            print(f"HELD: {stem} has no field the rubric names ({e})")
            return 1
        leaked = sorted(w for w in tells[stem] | {stem} if w in prompt.lower())
        if leaked:
            print(f"HELD: the prompt for {bid} contains {', '.join(leaked)} — part "
                  f"of the cell name {stem!r}. A named field is carrying the "
                  f"identity the blinding removes.")
            return 1

        verdict, why = None, "not attempted"
        for _ in range(max(1, a.tries)):
            try:
                verdict, why = parse(ask(a.command, prompt, a.timeout), rubric)
            except Exception as e:
                verdict, why = None, repr(e)[:200]
            if verdict:
                break
        if verdict is None:
            unparsed += 1
        out.append({"blind_id": bid, rubric["axis"]: verdict, "why": why})
        print(f"[{i:>3}/{len(blind)}] {bid} -> {verdict or 'UNPARSED'}", flush=True)

    json.dump({"axis": rubric["axis"], "rubric_sha256": digest,
               "blind_seed": a.blind_seed, "labeller": a.labeller,
               "generated_by": a.generated_by, "relabelled": bool(a.relabel),
               "labels": out}, open(labels_path, "w"), ensure_ascii=False, indent=1)

    print(f"\n{len(out)} labelled · {unparsed} unparsed · {labels_path}")
    if unparsed:
        # Not an error: the line reads a null label as an unlabelled cell and
        # holds. Dropping it here would move the denominator instead.
        print(f"{unparsed} cell(s) carry no verdict. They stay in the grid as "
              f"null and the line will hold on them.")
    return 0


def reveal(argv=None) -> int:
    ap = argparse.ArgumentParser(description="open the key and join labels to cells")
    ap.add_argument("--out", required=True, help="directory written by `label`")
    ap.add_argument("--to", required=True,
                    help="per-cell label path, with {cell} for the cell name")
    a = ap.parse_args(argv)

    data = json.load(open(os.path.join(a.out, "labels.json"), encoding="utf-8"))
    key = json.load(open(os.path.join(a.out, "key.json"), encoding="utf-8"))
    axis = data["axis"]

    written = 0
    for entry in data["labels"]:
        path = key.get(entry["blind_id"])
        if path is None:
            print(f"HELD: {entry['blind_id']} is in the labels and not in the key")
            return 1
        cell = os.path.splitext(os.path.basename(path))[0]
        dest = a.to.replace("{cell}", cell)
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        json.dump({"cell": cell, "label": entry[axis], "axis": axis,
                   "why": entry["why"], "labeller": data["labeller"],
                   "rubric_sha256": data["rubric_sha256"],
                   "relabelled": data["relabelled"]},
                  open(dest, "w"), ensure_ascii=False, indent=1)
        written += 1

    counts: dict = {}
    for entry in data["labels"]:
        counts[entry[axis]] = counts.get(entry[axis], 0) + 1
    print(f"{written} label(s) written · " +
          " · ".join(f"{k}={v}" for k, v in sorted(counts.items(), key=str)))
    if data["relabelled"]:
        print("these labels were produced by a relabelling — say so wherever the "
              "number is reported")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in ("label", "reveal"):
        print(__doc__)
        return 1
    return (label if argv[0] == "label" else reveal)(argv[1:])


if __name__ == "__main__":
    sys.exit(main())
