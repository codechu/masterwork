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
