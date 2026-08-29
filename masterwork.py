#!/usr/bin/env python3
"""One door into the line.

Every stage was reachable only as `python3 -m pipeline.<module>`, which
asks a reader to know four module paths that are not discoverable from
each other, and printed the interpreter's own path in its usage line —
a different string on every machine, and not a command anyone would type.

    python3 -m masterwork                 # what this is, and its commands
    python3 -m masterwork gate gates/     # any stage, by name
    python3 -m masterwork --version

Each command is the stage's own parser, unchanged; this only routes to it
and gives it a name a person could have typed.
"""
from __future__ import annotations

import argparse
import importlib
import sys

from pipeline import __version__

NAME = "MASTERWORK"
RIGHT = "character production line"
TAGLINE = "makes the piece; it does not score it"
PAD = 2
GAP = 4  # least space between the name and the words on its right

# command -> (module, one-line help). The help is the stage's own
# description, so the two cannot say different things.
COMMANDS = {
    "line": ("pipeline.line", "run one campaign through the line"),
    "campaign": ("pipeline.campaign", "run a campaign: repeats, band, comparison"),
    "ceremony": ("pipeline.ceremony", "hold a sitting and seal the piece"),
    "gate": ("pipeline.gate", "check frozen gate files"),
    "cells": ("pipeline.cells", "completeness gate for a battery"),
    "seal": ("pipeline.seal", "verify a candidate's seal"),
    "pairs": ("pipeline.pairs", "cut training data from scored runs"),
    "retain": ("pipeline.retain", "run-directory retention"),
    "label": ("tools.blind_label", "blind-label cells for a judged axis"),
}


def banner(version: str) -> str:
    """The four box lines, all of equal display width.

    Built from its content rather than written out, because a hand-drawn
    box drifts and nobody looks at the first thing a user sees.
    """
    left = f"{NAME}  v{version}"
    width = max(len(left) + GAP + len(RIGHT), len(TAGLINE))
    inner = width + 2 * PAD
    space = " " * PAD
    return "\n".join([
        "┌" + "─" * inner + "┐",
        "│" + space + left + " " * (width - len(left) - len(RIGHT))
        + RIGHT + space + "│",
        "│" + space + TAGLINE + " " * (width - len(TAGLINE)) + space + "│",
        "└" + "─" * inner + "┘",
    ])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="masterwork",
        description="the line that makes a character; journeyman scores it")
    ap.add_argument("--version", action="version",
                    version=f"masterwork {__version__}")
    ap.add_argument("-q", "--quiet", action="store_true",
                    help="no banner; results, warnings and errors still print")
    sub = ap.add_subparsers(dest="cmd", required=False)
    for name, (_, blurb) in COMMANDS.items():
        sub.add_parser(name, help=blurb, add_help=False)
    return ap


def main(argv=None) -> int:
    """Route to a stage, or introduce the line when asked for nothing.

    Chrome goes to stderr once a stage is running, so a stage's real output
    can be piped without the mark in it. The bare call is the exception:
    there the mark and the command list *are* the answer, so they go to
    stdout with exit 0.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = build_parser()

    at = next((i for i, a in enumerate(argv) if not a.startswith("-")), None)
    before = argv if at is None else argv[:at]
    quiet = "-q" in before or "--quiet" in before

    if at is None:
        ap.parse_args(argv)          # --version / -h exit here
        if not quiet:
            print(banner(__version__))
        ap.print_help()
        return 0

    cmd = argv[at]
    if cmd not in COMMANDS:
        ap.parse_args(argv)          # argparse names the unknown command, exit 2
        return 2

    if not quiet:
        print(banner(__version__), file=sys.stderr)

    module = importlib.import_module(COMMANDS[cmd][0])
    # The stage's parser takes its name from argv[0]; give it one a person
    # could have typed instead of the interpreter's path.
    sys.argv = [f"masterwork {cmd}"] + argv[at + 1:]
    return module.main() or 0


if __name__ == "__main__":
    sys.exit(main())
