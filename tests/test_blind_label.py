"""Blind labelling tests. What the labeller must not be able to see."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import blind_label  # noqa: E402

RUBRIC = {
    "axis": "existence",
    "verdicts": ["DENIED", "ADOPTED"],
    "fields": {"question": "cases.0.prompt", "answer": "cases.0.answer"},
    "prompt": "Q: {question}\nA: {answer}\nOne of: {verdicts}",
}


def workshop(tmp, answer='{"existence": "DENIED", "why": "said not there"}',
             rubric=None):
    """A cell grid, a rubric, and a labeller command that echoes a fixed answer."""
    cells = os.path.join(tmp, "cells")
    os.makedirs(cells)
    for name, arm in (("candidate_s4242", "candidate"), ("incumbent_s4242", "incumbent")):
        json.dump({"arm": arm, "seed": 4242,
                   "cases": [{"prompt": "is the tale there?", "answer": "no"}]},
                  open(os.path.join(cells, name + ".json"), "w"))
    rpath = os.path.join(tmp, "rubric.json")
    json.dump(rubric or RUBRIC, open(rpath, "w"))
    cmd = os.path.join(tmp, "labeller.py")
    open(cmd, "w").write(
        "import sys\n"
        "p = sys.stdin.read()\n"
        f"open({os.path.join(tmp, 'seen.txt')!r}, 'a').write(p + '\\n----\\n')\n"
        f"print('```json\\n' + {answer!r} + '\\n```')\n")
    return (os.path.join(cells, "*.json"), rpath,
            f"{sys.executable} {cmd}", os.path.join(tmp, "labels"))


def run(cells, rubric, cmd, out, *extra):
    return blind_label.main(["label", "--cells", cells, "--rubric", rubric,
                             "--command", cmd, "--out", out,
                             "--blind-seed", "1", "--labeller", "judge",
                             "--generated-by", "candidate", *extra])


def test_labelling_your_own_output_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        cells, rubric, cmd, out = workshop(tmp)
        assert blind_label.main(
            ["label", "--cells", cells, "--rubric", rubric, "--command", cmd,
             "--out", out, "--blind-seed", "1", "--labeller", "same",
             "--generated-by", "same"]) == 1


def test_the_labeller_never_sees_arm_seed_or_filename():
    with tempfile.TemporaryDirectory() as tmp:
        cells, rubric, cmd, out = workshop(tmp)
        assert run(cells, rubric, cmd, out) == 0
        seen = open(os.path.join(tmp, "seen.txt")).read()
        assert "is the tale there?" in seen
        for leak in ("candidate", "incumbent", "4242"):
            assert leak not in seen


def test_a_field_carrying_the_cell_name_is_refused():
    """Blinding that a named field walks straight through is not blinding."""
    with tempfile.TemporaryDirectory() as tmp:
        leaky = dict(RUBRIC, fields=dict(RUBRIC["fields"], question="arm"))
        cells, rubric, cmd, out = workshop(tmp, rubric=leaky)
        assert run(cells, rubric, cmd, out) == 1


def test_key_is_written_but_not_in_the_labels():
    with tempfile.TemporaryDirectory() as tmp:
        cells, rubric, cmd, out = workshop(tmp)
        assert run(cells, rubric, cmd, out) == 0
        labels = json.load(open(os.path.join(out, "labels.json")))
        assert json.load(open(os.path.join(out, "key.json")))
        assert "candidate" not in json.dumps(labels["labels"])


def test_unparseable_answer_becomes_null_not_a_category():
    with tempfile.TemporaryDirectory() as tmp:
        cells, rubric, cmd, out = workshop(tmp, answer='{"existence": "MAYBE"}')
        assert run(cells, rubric, cmd, out, "--tries", "1") == 0
        labels = json.load(open(os.path.join(out, "labels.json")))["labels"]
        assert [e["existence"] for e in labels] == [None, None]


def test_null_label_reaches_the_cell_so_the_line_holds():
    with tempfile.TemporaryDirectory() as tmp:
        cells, rubric, cmd, out = workshop(tmp, answer='{"existence": "MAYBE"}')
        run(cells, rubric, cmd, out, "--tries", "1")
        dest = os.path.join(tmp, "per-cell", "{cell}.json")
        assert blind_label.main(["reveal", "--out", out, "--to", dest]) == 0
        got = json.load(open(dest.replace("{cell}", "candidate_s4242")))
        assert got["label"] is None


def test_relabelling_takes_saying_so():
    with tempfile.TemporaryDirectory() as tmp:
        cells, rubric, cmd, out = workshop(tmp)
        assert run(cells, rubric, cmd, out) == 0
        assert run(cells, rubric, cmd, out) == 1
        assert run(cells, rubric, cmd, out, "--relabel") == 0
        assert json.load(open(os.path.join(out, "labels.json")))["relabelled"]


def test_reveal_joins_labels_back_to_their_cells():
    with tempfile.TemporaryDirectory() as tmp:
        cells, rubric, cmd, out = workshop(tmp)
        run(cells, rubric, cmd, out)
        dest = os.path.join(tmp, "per-cell", "{cell}.json")
        assert blind_label.main(["reveal", "--out", out, "--to", dest]) == 0
        for name in ("candidate_s4242", "incumbent_s4242"):
            got = json.load(open(dest.replace("{cell}", name)))
            assert got["label"] == "DENIED" and got["cell"] == name


def test_empty_grid_is_held_not_reported_as_nothing_to_do():
    with tempfile.TemporaryDirectory() as tmp:
        _cells, rubric, cmd, out = workshop(tmp)
        assert run(os.path.join(tmp, "nowhere", "*.json"), rubric, cmd, out) == 1


def test_two_cells_with_one_name_are_held():
    """Same grid per arm in separate directories: labels would overwrite."""
    with tempfile.TemporaryDirectory() as tmp:
        cells, rubric, cmd, out = workshop(tmp)
        other = os.path.join(tmp, "arm-b")
        os.makedirs(other)
        json.dump({"arm": "b", "seed": 4242,
                   "cases": [{"prompt": "is the tale there?", "answer": "no"}]},
                  open(os.path.join(other, "candidate_s4242.json"), "w"))
        both = os.path.join(tmp, "*", "candidate_s4242.json")
        assert run(both, rubric, cmd, out) == 1
