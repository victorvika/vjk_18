"""
Dev-only: random-walk statistics for the SmartRiskAPlus model.
Shares the state machine with test_rules.py and preview.py via model.py.

    .venv/bin/python sim_final.py
"""
import numpy as np
import statistics as st

from model import run, DEFAULTS

PER = DEFAULTS["ltf_per_htf"]


def gen(seed, n_htf=4000):
    rng = np.random.default_rng(seed)
    n = n_htf * PER
    step = rng.normal(0.0, 0.0009, n) + 0.00002 * np.sin(np.arange(n) / 900.0)
    c = 100 * np.exp(np.cumsum(step))
    o = np.concatenate([[100.0], c[:-1]])
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.0006, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.0006, n)))
    return o, h, l, c


for seed in (11, 23, 42, 77):
    o, h, l, c = gen(seed)
    ev = run(o, h, l, c)
    n = len(c)
    entries = ev["entry"]
    waits = [e["bar"] - e["zgBar"] for e in entries]
    risks = [e["risk"] / e["ce"] * 100 for e in entries]
    wt = sum(1 for e in entries if e["withTrend"])
    print(f"seed {seed:>3} | {n/(PER*24):5.0f}d | LS {len(ev['ls']):3d} -> MSS {len(ev['mss']):3d} "
          f"-> IFVG {len(ev['ifvg']):3d} -> entries {len(entries):3d} "
          f"(L{sum(1 for e in entries if e['dir']==1)}/S{sum(1 for e in entries if e['dir']==-1)}, "
          f"with-trend {wt}) | structfail {len(ev['structfail']):3d} inval {len(ev['invalid']):3d} "
          f"| one entry/{n/max(len(entries),1):.0f} bars | flip->tap med "
          f"{st.median(waits) if waits else 0:.0f} bars | risk med {st.median(risks) if risks else 0:.2f}%")
