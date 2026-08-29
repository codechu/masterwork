"""The package installs as one name, and the description carries no branch.

Two failures this holds shut, both learned next door rather than here:

  * the stages used to live in top-level `pipeline/` and `tools/` —
    `pipeline` is taken on PyPI and both are names any environment might
    already have, so installing this would have collided with whatever
    was there;
  * a published description cannot be edited, so a branch named in one is
    load-bearing forever: rename it and every image on every past release
    page breaks, and GitHub does not redirect raw URLs across a rename.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def test_only_one_top_level_package_is_installed():
    packages = re.search(r"(?ms)^packages = \[(.*?)\]",
                         read("pyproject.toml")).group(1)
    names = re.findall(r'"([^"]+)"', packages)
    assert names == ["masterwork"], f"would install {names} into site-packages"


def test_the_judge_is_a_declared_dependency():
    deps = re.search(r"(?ms)^dependencies = \[(.*?)\]",
                     read("pyproject.toml")).group(1)
    assert "journeyman-bench" in deps, (
        "the line cannot finish without journeyman; whoever installs "
        "masterwork must get it")


def test_versions_agree():
    packaged = re.search(r'(?m)^version = "([^"]+)"',
                         read("pyproject.toml")).group(1)
    in_code = re.search(r'(?m)^__version__ = "([^"]+)"',
                        read("masterwork/__init__.py")).group(1)
    assert packaged == in_code, f"pyproject {packaged} vs code {in_code}"


def test_pypi_readme_is_current():
    tool = os.path.join(ROOT, "tools", "pypi_readme.py")
    p = subprocess.run([sys.executable, tool, "--check"],
                       capture_output=True, text=True)
    assert p.returncode == 0, "README.pypi.md is stale — run tools/pypi_readme.py"


def test_the_description_names_no_branch():
    text = read("README.pypi.md")
    for ref in ("/master/", "/main/", "/HEAD/"):
        assert ref not in text, f"{ref} is a branch; use the tag"


def test_nothing_relative_survives_in_the_description():
    text = read("README.pypi.md")
    leftovers = [t for t in re.findall(r"\]\(([^)]+)\)", text)
                 if not t.startswith(("http://", "https://", "mailto:", "#"))]
    leftovers += [t for t in re.findall(r'src="([^"]+)"', text)
                  if not t.startswith(("http://", "https://"))]
    assert leftovers == [], f"these would 404 on PyPI: {leftovers}"
