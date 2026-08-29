"""Seal tests. Each one names the mistake it exists to stop."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from masterwork import seal  # noqa: E402

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


def test_a_shape_is_written_the_way_a_person_writes_dates(tmp_path):
    """`yyyy-MM-dd`, not a doubly-escaped regex in a JSON file.

    A seal profile is written by whoever keeps a workshop's seals. Asking
    for `(\\d{4}-\\d{2}-\\d{2})` there asks them to know our dialect and
    JSON's escaping at once, to say a thing they can already say.
    """
    from masterwork.seal import format_to_regex, read_seal
    assert format_to_regex("yyyy-MM-dd") == r"(\d{4}\-\d{2}\-\d{2})"

    piece = tmp_path / "candidate.txt"
    piece.write_text(
        "# corpus hash: a\n# script hash: b\n# question seed: 1\n"
        "# sampling seed: 2\n# sealed on 2026-08-29 by the workshop\n\ntext\n")
    profile = {"corpus_hash": ["corpus hash"], "script_hash": ["script hash"],
               "question_seed": ["question seed"], "sampling_seed": ["sampling seed"],
               "date": {"aliases": [], "format": "yyyy-MM-dd"}}
    assert read_seal(str(piece), profile).fields["date"] == "2026-08-29"


def test_a_shape_also_cleans_a_value_an_alias_found(tmp_path):
    """It used to run only when no alias matched.

    A header with the key but a value wrapped in prose could not be
    cleaned: the alias matched, returned the whole string, and the shape
    never ran. That is the common case, not the rare one.
    """
    from masterwork.seal import read_seal
    piece = tmp_path / "candidate.txt"
    piece.write_text(
        "# corpus hash: a\n# script hash: b\n# question seed: 1\n"
        "# sampling seed: 2\n# date: sealed on 2026-08-29, unpriced\n\ntext\n")
    profile = {"corpus_hash": ["corpus hash"], "script_hash": ["script hash"],
               "question_seed": ["question seed"], "sampling_seed": ["sampling seed"],
               "date": {"aliases": ["date"], "format": "yyyy-MM-dd"}}
    assert read_seal(str(piece), profile).fields["date"] == "2026-08-29"


def test_a_shape_it_cannot_read_is_refused_rather_than_compiled(tmp_path):
    """`MMM dd, yyyy` consumes `MM` and leaves a literal `M`.

    That compiles to a pattern matching nothing, so the field comes back
    missing and the writer is told only that — with no way to see that
    their shape was the problem. Same for `YYYY-MM-DD`, which is a common
    way to write it and would look for the literal text "YYYY".
    """
    import pytest
    from masterwork.seal import format_to_regex
    for good in ("yyyy-MM-dd", "MM-dd-yyyy", "dd.MM.yyyy",
                 "yyyy-MM-ddTHH:mm:ss"):
        assert format_to_regex(good).startswith("(")
    for bad in ("YYYY-MM-DD", "yyyy-M-d", "DD.MM.YYYY"):
        with pytest.raises(ValueError) as e:
            format_to_regex(bad)
        assert "Supported" in str(e.value)


def test_a_written_month_is_a_word_not_an_english_month_list(tmp_path):
    """`dd MMMM yyyy` must read 29 Ağustos 2026 as readily as 29 August 2026.

    The dialect mechanism exists so a workshop can keep its own headers,
    and half the point of that is that they are not in English. A list of
    month names would have read one and refused the other. A shape locates
    a value; it does not validate one.
    """
    from masterwork.seal import read_seal
    base = ("# corpus hash: a\n# script hash: b\n# question seed: 1\n"
            "# sampling seed: 2\n# date: {}\n\ntext\n")
    prof = {"corpus_hash": ["corpus hash"], "script_hash": ["script hash"],
            "question_seed": ["question seed"], "sampling_seed": ["sampling seed"]}
    for fmt, written, want in (
            ("dd MMM yyyy", "sealed 29 Aug 2026", "29 Aug 2026"),
            ("dd MMMM yyyy", "29 August 2026", "29 August 2026"),
            ("dd MMMM yyyy", "muhurlendi 29 Ağustos 2026", "29 Ağustos 2026"),
            ("dd MMM yyyy", "29 août 2026", "29 août 2026")):
        piece = tmp_path / f"c-{abs(hash((fmt, written)))}.txt"
        piece.write_text(base.format(written), encoding="utf-8")
        pr = dict(prof, date={"aliases": ["date"], "format": fmt})
        assert read_seal(str(piece), pr).fields["date"] == want
