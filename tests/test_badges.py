"""The badges that state a fact are checked against the fact.

Three of them assert rather than report: the Python floor, the dependency
count, and the licence. Nothing read them, and two went stale the day the
package shipped — the status badge still said "not published" after it was
on PyPI, and the dependency badge said zero while `journeyman-bench` was a
declared requirement.

The repository already holds that a badge pointing nowhere is decoration
wearing the costume of a signal. A badge asserting an unchecked fact is the
same costume, and it is worse, because a stale number reads as a measurement.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def project():
    text = read("pyproject.toml")

    def field(name):
        m = re.search(rf'(?m)^{name} = "([^"]+)"', text)
        return m.group(1) if m else None

    m = re.search(r"(?ms)^dependencies = \[(.*?)\]", text)
    deps = re.findall(r'"([^"]+)"', m.group(1)) if m else []
    return {"requires-python": field("requires-python"),
            "license": field("license"), "dependencies": deps}


def test_python_floor_matches_requires_python():
    m = re.search(r"badge/python-([\d.]+)%2B-", read("README.md"))
    assert m, "the Python badge changed shape; update this test"
    assert project()["requires-python"] == ">=" + m.group(1)


def test_dependency_count_matches():
    m = re.search(r"badge/dependencies-(\d+)-", read("README.md"))
    assert m, "the dependency badge changed shape"
    declared = project()["dependencies"]
    assert int(m.group(1)) == len(declared), (
        f"badge says {m.group(1)}, pyproject declares {declared}")


def test_licence_matches():
    # shields escapes a literal "-" as "--" and the last segment is the
    # colour. Two ways to get this wrong, both met: a non-greedy match
    # reads "Apache" out of "Apache--2.0", and a greedy `.+` swallows the
    # rest of the row when every badge sits on one line, as they do here.
    m = re.search(r"badge/license-([^()]+)-[a-z]+\)", read("README.md"))
    assert m, "the licence badge changed shape"
    assert m.group(1).replace("--", "-") == project()["license"]


def test_no_badge_claims_it_is_unpublished():
    """It is on PyPI. A badge saying otherwise is a stale claim, not modesty."""
    row = read("README.md")
    assert "not%20published" not in row, (
        "the package is published; say unproven if that is what is meant")


def test_every_badge_is_a_link():
    row = [l for l in read("README.md").splitlines() if l.startswith("[![")]
    assert row, "no badge row found"
    for line in row:
        for badge in re.findall(r"\[!\[[^\]]*\]\([^)]*\)\]\(([^)]*)\)", line):
            assert badge, f"badge with an empty target: {line}"
        assert re.fullmatch(r"(\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)\s*)+", line), (
            f"a badge in this row is not a link: {line}")


def test_pypi_badge_names_the_package_that_is_published():
    """The PyPI badge reads its number live, so it cannot go stale — but it
    can point at the wrong package and still render a plausible version.
    It is the project name that has to be checked, not the number."""
    text = read("README.md")
    m = re.search(r"img\.shields\.io/pypi/v/([\w.-]+)", text)
    assert m, "the PyPI badge changed shape; update this test"
    name = re.search(r'(?m)^name = "([^"]+)"', read("pyproject.toml")).group(1)
    assert m.group(1) == name


def test_ci_badge_points_at_a_workflow_that_exists():
    """A badge pointing nowhere is decoration wearing the costume of a
    signal: GitHub renders an unknown workflow as a grey 'no status'."""
    m = re.search(r"actions/workflows/([\w.-]+)/badge\.svg", read("README.md"))
    assert m, "the CI badge changed shape; update this test"
    assert os.path.exists(os.path.join(ROOT, ".github", "workflows", m.group(1)))
