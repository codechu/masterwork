# Succession gate (template — freeze a copy of this before a run)

A candidate replaces the incumbent only on the work. Fill this in, freeze
it, and do not edit it once the run starts.

Filled in with real numbers so that a copy of it is already a valid gate;
the checker runs the band command, so a template full of placeholders would
be a template that cannot pass its own check.

`measure:` names the axis in the benchmark report and `compare:` says what
the threshold applies to. Without them the rule is valid on paper and can
never touch a number — you find out after the run, when a human binds it by
hand, which is where a verdict turns into an opinion. The checker now says
UNBOUND at freeze time instead.

## Axis: grounding (n = 24 seeds per arm)

    measure: grounding
    compare: candidate - incumbent
    accept: candidate score − incumbent score >= 0.35
    reject: incumbent score − candidate score >= 0.35
    band-command: python3 -c "import math;print(round(1.96*math.sqrt(2*0.25/24),4))"
    band-value: 0.2829
    threshold: 0.35 — above the band by 0.067

The band command above is an analytic ceiling for a score in [0,1] at n
seeds per arm. Prefer a **measured** band where you have one: run the same
arm repeatedly, changing nothing but sampling, and take the spread. Every
measured band so far has come in under the analytic one, and one judge's
measured spread was three times what its designers assumed — the analytic
figure is a stand-in until you have the real one, not a substitute for it.

Between the two thresholds there is no verdict. That range is not "no
difference"; it is "not resolvable at this size", and it is written that
way in the record, along with the number of cells it would take to resolve.

## Diagnostic (not a gate)

    gate-skip: portrait conformance is read for direction, never for a verdict
