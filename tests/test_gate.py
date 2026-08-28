"""Gate tests. Each is a way a threshold has been wrong in practice."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import gate  # noqa: E402

GOOD = """## K1
    accept: arm difference >= 0.33
    band-command: python3 -c "import math;print(1.96*math.sqrt(0.65*0.35*2/24))"
    band-value: 0.27 (two-proportion difference, n=24 per arm)
    threshold: 0.33 — above the band by 0.06
"""


def check(body):
    return gate.check_section(body)[0]


def test_computed_band_above_threshold_passes():
    assert check(GOOD.split("\n", 1)[1]) == "PASS"


def test_threshold_inside_band_fails():
    """The failure the three-line rule was written for."""
    body = GOOD.split("\n", 1)[1].replace("threshold: 0.33 — above the band by 0.06",
                                          "threshold: 0.20 — above the band")
    assert check(body) == "FAIL"


def test_band_written_from_memory_fails():
    body = GOOD.split("\n", 1)[1].replace("band-value: 0.27", "band-value: 0.05")
    assert check(body) == "FAIL"


def test_restated_band_is_unverifiable_not_pass():
    """A command that prints a number it already contains measured nothing."""
    body = ('    reject: violations >= 4\n'
            '    band-command: python3 -c "print(\'upper bound ~3.4 cells\')"\n'
            '    band-value: 3.4\n'
            '    threshold: 4 — above the band\n')
    assert check(body) == "UNVERIFIABLE"


def test_deciding_section_without_band_fails():
    assert check("    accept: difference >= 0.30\n") == "FAIL"


def test_declared_non_gate_is_skipped_with_its_reason():
    verdict, notes = gate.check_section(
        "    accept: >= 0.3\n    gate-skip: results section, not a pre-registered gate\n")
    assert verdict == "SKIP" and "results section" in notes[0]
