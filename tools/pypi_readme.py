#!/usr/bin/env python3
"""Generate README.pypi.md from README.md.

PyPI renders the long description outside the repository, so every
relative link and image in the README would 404 there. This is the same
file with those made absolute — against **the tag being released**, never
against a branch.

The branch part is not a preference. A published description cannot be
edited afterwards, so a branch name inside one is load-bearing forever:
rename the branch and every image on every past release page breaks, and
GitHub does not redirect raw URLs across a rename. The sibling repository
learned that by nearly doing it.

    tools/pypi_readme.py           # rewrite README.pypi.md
    tools/pypi_readme.py --check   # exit 1 if it is out of date

tests/test_readme_pypi.py runs --check.
"""
import pathlib
import re
import sys

REPO = "https://github.com/codechu/masterwork"
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "README.md"
DST = ROOT / "README.pypi.md"


def ref():
    """The tag this version will be released under."""
    version = re.search(r'(?m)^version = "([^"]+)"',
                        (ROOT / "pyproject.toml").read_text()).group(1)
    return "v" + version


def render(text, ref_=None):
    r = ref_ or ref()
    blob = f"{REPO}/blob/{r}/"
    raw = REPO.replace("github.com", "raw.githubusercontent.com") + f"/{r}/"

    def local(t):
        return not t.startswith(("http://", "https://", "mailto:", "#"))

    def link(m):
        return m.group(0) if not local(m.group(1)) else "](" + blob + m.group(1) + ")"

    def attr(m):
        # Images are HTML here, so the markdown rewrite never sees them.
        return (m.group(0) if not local(m.group(2))
                else f'{m.group(1)}="{raw}{m.group(2)}"')

    text = re.sub(r"\]\(([^)]+)\)", link, text)
    return re.sub(r'\b(src|href)="([^"]+)"', attr, text)


def main(argv):
    want = render(SRC.read_text())
    if "--check" in argv:
        have = DST.read_text() if DST.exists() else ""
        if have == want:
            return 0
        print("README.pypi.md is stale — run tools/pypi_readme.py",
              file=sys.stderr)
        return 1
    DST.write_text(want)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
