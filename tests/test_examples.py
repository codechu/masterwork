"""The README's trace is quoted from this example. A test keeps them honest.

Prose drifts from code silently; a trace pasted into a README is prose. If the
line's wording or verdict changes, this fails and the README gets updated in
the same commit rather than six months later.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_the_readme_trace_still_comes_out_of_the_line():
    p = subprocess.run([sys.executable, "examples/held_at_gate.py"],
                       cwd=ROOT, capture_output=True, text=True)
    assert p.returncode == 1, p.stdout + p.stderr
    for quoted in ("[ok  ] purpose",
                   "[ok  ] seal",
                   "4 found · 4 complete · 4 expected",
                   "4 labelled by a separate model",
                   "[HELD] gate",
                   "threshold 0.05 <= band 0.0559",
                   "verdict HELD_AT_GATE"):
        assert quoted in p.stdout, f"README quotes {quoted!r}; the line no longer prints it"


def test_the_example_needs_no_model_and_no_network():
    """It names no generate or judge command, which is why a bare checkout runs it."""
    src = open(os.path.join(ROOT, "examples", "held_at_gate.py"), encoding="utf-8").read()
    assert '"generate"' not in src and '"judge"' not in src
