#!/usr/bin/env python3
"""Move the version in both places that carry it, together.

The version lives in pyproject.toml and masterwork/__init__.py. A test
checks they agree; nothing was moving them, and next door a release went
out with one bumped and the other behind — the package said one version
while every artefact it produced was stamped with another.

    tools/bump.py 0.0.2        # edit both, then write the changelog entry

It does not tag, commit, or push: the tag is the release signature and
stays a deliberate act. It refuses to run if the two disagree beforehand,
because starting from a drifted state hides which one was wrong.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = {
    "pyproject.toml": (r'(?m)^version = "([^"]+)"', 'version = "{v}"'),
    "masterwork/__init__.py": (r'(?m)^__version__ = "([^"]+)"',
                               '__version__ = "{v}"'),
}


def main(argv):
    if len(argv) != 1:
        sys.exit(__doc__)
    new = argv[0]
    found = {}
    for name, (pattern, _) in FILES.items():
        text = (ROOT / name).read_text()
        m = re.search(pattern, text)
        if not m:
            sys.exit(f"no version found in {name}")
        found[name] = m.group(1)
    if len(set(found.values())) != 1:
        sys.exit("version drift, fix by hand first: "
                 + " ".join(f"{k}={v}" for k, v in found.items()))
    old = next(iter(found.values()))
    for name, (pattern, template) in FILES.items():
        p = ROOT / name
        p.write_text(re.sub(pattern, template.format(v=new), p.read_text()))
    print(f"{old} -> {new} in {len(FILES)} files")
    print("next: write the CHANGELOG entry, run the suite, then tag")


if __name__ == "__main__":
    main(sys.argv[1:])
