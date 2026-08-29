"""Seal tests. Each one names the mistake it exists to stop."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import seal  # noqa: E402

COMPLETE = """# masterwork seal
# name: Example
# corpus hash: {corpus}
# script hash: 0123456789abcdef0123456789abcdef
# question seed: 0 · sampling seed: 2718
# date: 2026-08-28

the piece itself
"""


def write(tmp, text, name="candidate.txt"):
    p = os.path.join(tmp, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


def test_reads_two_pairs_from_one_line():
    """`a: 1 · b: 2` is a formatting habit, not a second syntax."""
    with tempfile.TemporaryDirectory() as tmp:
        p = write(tmp, COMPLETE.format(corpus="0" * 32))
        s = seal.read_seal(p)
        assert s.complete, s.missing
        assert s.fields["question_seed"] == "0"
        assert s.fields["sampling_seed"] == "2718"


def test_missing_field_refuses():
    """Four of five fields still leaves the piece unreproducible."""
    with tempfile.TemporaryDirectory() as tmp:
        text = COMPLETE.format(corpus="0" * 32).replace("# date: 2026-08-28\n", "")
        p = write(tmp, text)
        problems = seal.verify(p)
        assert any("missing" in x for x in problems)


def test_corpus_mismatch_is_named():
    """A piece made from another corpus is another piece."""
    with tempfile.TemporaryDirectory() as tmp:
        corpus = write(tmp, "tales", "corpus.md")
        p = write(tmp, COMPLETE.format(corpus="f" * 32))
        problems = seal.verify(p, corpus=corpus)
        assert any("corpus hash mismatch" in x for x in problems)


def test_deployed_copy_must_match():
    """The expensive one: edited here, run there, numbers belong elsewhere."""
    with tempfile.TemporaryDirectory() as tmp:
        corpus = write(tmp, "tales", "corpus.md")
        p = write(tmp, COMPLETE.format(corpus=seal.file_hash(corpus)))
        deployed = write(tmp, open(p).read() + "drift", "deployed.txt")
        assert not seal.verify(p, corpus=corpus)
        problems = seal.verify(p, corpus=corpus, deployed=deployed)
        assert any("deployed copy differs" in x for x in problems)


def test_profile_lets_a_workshop_keep_its_dialect():
    """Header names are data, not code; the line stays language-neutral."""
    with tempfile.TemporaryDirectory() as tmp:
        p = write(tmp, "# korpus md5: %s\n# script md5: %s\n"
                       "# soru-sirasi seed: 0 · ornekleme seed: 7\n# tarih: 2026-08-28\n"
                       % ("0" * 32, "1" * 32))
        profile = {"corpus_hash": ["korpus md5"], "script_hash": ["script md5"],
                   "question_seed": ["soru-sirasi seed"],
                   "sampling_seed": ["ornekleme seed"], "date": ["tarih"]}
        assert seal.read_seal(p, profile).complete


def test_pattern_recovers_a_field_that_is_not_key_value():
    """An older seal carries its date in the title line. The file is its bytes:
    editing it to add a field would change the piece. Teach the reader."""
    with tempfile.TemporaryDirectory() as tmp:
        p = write(tmp, "# SEAL — candidate, 2026-08-26\n# corpus md5: %s\n"
                       "# script md5: %s\n# question seed: 0 · sampling seed: 7\n"
                       % ("0" * 32, "1" * 32))
        profile = {"corpus_hash": ["corpus md5"], "script_hash": ["script md5"],
                   "question_seed": ["question seed"],
                   "sampling_seed": ["sampling seed"],
                   "date": {"aliases": ["date"], "pattern": r"(\d{4}-\d{2}-\d{2})"}}
        s = seal.read_seal(p, profile)
        assert s.complete, s.missing
        assert s.fields["date"] == "2026-08-26"


def test_a_seed_written_as_the_word_None_is_missing_not_present():
    """The ceremony formats its header with f-strings; an unset sampling seed
    used to arrive as the four-character string "None" and count as supplied —
    a candidate whose sampling was never pinned clearing the one gate that
    exists to say it cannot be made again."""
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "candidate.txt")
        open(p, "w").write(
            "# corpus hash: " + "a" * 32 + "\n# script hash: " + "b" * 32 +
            "\n# question seed: 1 · sampling seed: None\n# date: 2026-08-29\n\nwords\n")
        s = seal.read_seal(p)
        assert "sampling_seed" in s.missing and not s.complete


def test_a_candidate_that_is_not_there_is_a_problem_not_a_traceback():
    """The line calls verify() directly, so the check belongs here."""
    assert seal.verify("/nowhere/candidate.txt") == [
        "no candidate at /nowhere/candidate.txt — nothing to verify"]
