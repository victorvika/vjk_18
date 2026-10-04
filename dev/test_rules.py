"""
Dev-only: deterministic rule tests for the SmartRiskAPlus model.
Run:  .venv/bin/python test_rules.py
"""

from model import run
from scenarios import PER, build, htf_base, tail, scenario_long

FAILS = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# ============================ A. full long sequence ============================
ls_bar = 27 * PER + PER - 1


def main():
        print("A. full long sequence (with HTF trend)")
o, h, l, c = scenario_long("with")
ev = run(o, h, l, c)
ls_bar = 27 * PER + PER - 1
check("liquidity sweep fires", [(b, d) for b, d in ev["ls"]] == [(ls_bar, 1)], ev["ls"])
check("MSS fires after the sweep", len(ev["mss"]) == 1 and ev["mss"][0][1] == 1, ev["mss"])
check("one IFVG flipped", len(ev["ifvg"]) == 1, ev["ifvg"])
if ev["ifvg"]:
    z = ev["ifvg"][0]
    check("IFVG zone is upright and 50% CE is its midpoint",
          abs(z["zgTop"] - 101.10) < 1e-9 and abs(z["zgBot"] - 100.90) < 1e-9, z)
check("exactly one CE entry", len(ev["entry"]) == 1, ev["entry"])
if ev["entry"]:
    e = ev["entry"][0]
    check("entry is at the 50% CE", abs(e["ce"] - 101.00) < 1e-9, e["ce"])
    check("SL sits below the entry (long)", e["sl"] < e["ce"], (e["sl"], e["ce"]))
    check("TP sits above the entry (long)", e["tp"] > e["ce"], (e["tp"], e["ce"]))
    check("with-trend trade targets 5R", e["rr"] == 5.0 and abs(e["tp"] - (e["ce"] + 5 * e["risk"])) < 1e-6, e)
check("no invalidation / structure failure", not ev["invalid"] and not ev["structfail"])

# ============================ B. sweep closes outside ==========================
print("B. sweep candle closes BEYOND the level -> no LS (it is a break, not a sweep)")
segs = htf_base((100.00, 100.00, 99.90, 99.95))
segs += [("htf", 99.98, 100.05, 99.50, 99.60)]                 # closes below 99.90
segs += [("htf", 99.60, 99.80, 99.40, 99.70)] * 3
segs += tail(40, 99.70)
o, h, l, c = build(segs)
ev = run(o, h, l, c)
check("no liquidity sweep", ev["ls"] == [], ev["ls"])
check("no entry", ev["entry"] == [], ev["entry"])

# ============================ C. follow-up breaks the wick =====================
print("C. follow-up candle breaks the sweep wick and closes out -> sweep invalidated, no re-arm")
segs = htf_base((100.00, 100.00, 99.90, 99.95))
segs += [
    ("htf", 99.98, 100.05, 99.50, 100.02),                     # valid sweep
    ("htf", 100.02, 100.30, 100.00, 100.25),                   # confirming bar 1
    ("htf", 100.25, 100.40, 99.20, 99.80),                     # breaks the wick AND closes below 99.90
    ("htf", 99.80, 100.60, 100.10, 100.50),
]
segs += tail(40, 100.50)
o, h, l, c = build(segs)
ev = run(o, h, l, c)
check("no liquidity sweep", ev["ls"] == [], ev["ls"])
check("no entry", ev["entry"] == [], ev["entry"])

# ============================ D. FVG respected -> no IFVG ======================
print("D. price closes INSIDE the gap (reacts) -> no IFVG, no entry")
segs = htf_base((100.00, 100.00, 99.90, 99.95))
segs += [
    ("htf", 99.98, 100.05, 99.50, 100.02),
    ("htf", 100.02, 100.30, 100.00, 100.25),
    ("htf", 100.25, 100.60, 100.05, 100.50),
]
segs += [("ltf", 100.50, 100.50, 100.50, 100.50)] * 6
segs += [("ltf", 100.50, 101.00, 100.50, 100.50)]
segs += [("ltf", 100.50, 100.50, 100.50, 100.50)] * 5
segs += [("ltf", 100.50, 101.20, 100.45, 101.20)]              # MSS
segs += [("ltf", 101.30, 101.30, 101.10, 101.25)]              # gap top
segs += [("ltf", 101.20, 101.25, 101.05, 101.10)]
segs += [("ltf", 101.00, 100.90, 100.85, 100.95)]              # bearish FVG
segs += [("ltf", 100.95, 101.05, 100.95, 101.00)]              # closes INSIDE the gap
segs += [("ltf", 101.00, 101.10, 100.95, 101.05)]              # still inside
segs += tail(20, 101.05)
o, h, l, c = build(segs)
ev = run(o, h, l, c)
check("no IFVG flip", ev["ifvg"] == [], ev["ifvg"])
check("no entry", ev["entry"] == [], ev["entry"])

# ============================ E. tap before leaving the zone ===================
print("E. CE tapped before price leaves the zone -> no entry, then arming -> entry")
segs = htf_base((100.00, 100.00, 99.90, 99.95))
segs += [
    ("htf", 99.98, 100.05, 99.50, 100.02),
    ("htf", 100.02, 100.30, 100.00, 100.25),
    ("htf", 100.25, 100.60, 100.05, 100.50),
]
segs += [("ltf", 100.50, 100.50, 100.50, 100.50)] * 6
segs += [("ltf", 100.50, 101.00, 100.50, 100.50)]
segs += [("ltf", 100.50, 100.50, 100.50, 100.50)] * 5
segs += [("ltf", 100.50, 101.20, 100.45, 101.20)]              # MSS
segs += [("ltf", 101.30, 101.30, 101.10, 101.25)]
segs += [("ltf", 101.20, 101.25, 101.05, 101.10)]
segs += [("ltf", 101.00, 100.90, 100.85, 100.95)]              # bearish FVG
segs += [("ltf", 100.95, 101.65, 100.85, 101.60)]              # disrespect -> IFVG
segs += [("ltf", 101.60, 101.65, 100.95, 101.10)]              # taps CE while still in the zone
segs += [("ltf", 101.10, 101.80, 101.20, 101.70)]              # leaves the zone -> armed
segs += [("ltf", 101.70, 101.75, 100.95, 101.10)]              # retrace taps CE -> entry
segs += tail(14, 101.10)
o, h, l, c = build(segs)
ev = run(o, h, l, c)
check("exactly one entry", len(ev["entry"]) == 1, [e["bar"] for e in ev["entry"]])
if ev["entry"]:
    check("entry waits for the arming bar", ev["entry"][0]["bar"] == len(c) - 15, ev["entry"][0]["bar"])

# ============================ F. counter-trend targets 3R ======================
print("F. counter-trend long -> 1:3 instead of 1:5")
o, h, l, c = scenario_long("against")
ev = run(o, h, l, c)
check("sweep + MSS + IFVG + entry all fire",
      len(ev["ls"]) == 1 and len(ev["mss"]) == 1 and len(ev["ifvg"]) == 1 and len(ev["entry"]) == 1,
      (len(ev["ls"]), len(ev["mss"]), len(ev["ifvg"]), len(ev["entry"])))
if ev["entry"]:
    e = ev["entry"][0]
    check("counter-trend trade targets 3R", e["rr"] == 3.0 and not e["withTrend"], e)
    check("TP = entry + 3R", abs(e["tp"] - (e["ce"] + 3 * e["risk"])) < 1e-6, e)

# ============================ G. mirrored short sequence =======================
print("G. mirrored short sequence")
segs = [("htf", 100.00, 100.00, 100.00, 100.00)] * 12
segs.append(("htf", 100.00, 100.10, 100.00, 99.95))            # major swing HIGH 100.10
segs += [("htf", 100.00, 100.00, 100.00, 100.00)] * 12
segs += [
    ("htf", 100.02, 100.50, 100.00, 100.00),                   # HTF 25: sweeps 100.10, closes inside
    ("htf", 100.00, 100.00, 99.75, 99.80),                     # HTF 26: reverses down
    ("htf", 99.80, 99.85, 99.60, 99.75),                       # HTF 27: confirms -> LS short
]
segs += [("ltf", 99.75, 99.75, 99.75, 99.75)] * 6
segs += [("ltf", 99.75, 99.75, 99.25, 99.75)]                  # pivot low
segs += [("ltf", 99.75, 99.75, 99.75, 99.75)] * 5
segs += [("ltf", 99.75, 99.75, 99.10, 99.10)]                  # MSS down
segs += [("ltf", 99.05, 98.95, 98.85, 99.00)]                  # gap bottom (h < l[349])
segs += [("ltf", 99.00, 99.10, 98.90, 99.05)]
segs += [("ltf", 99.15, 99.25, 99.05, 99.20)]                  # bullish FVG (low > high[2])
segs += [("ltf", 99.20, 99.30, 98.40, 98.50)]                  # disrespect downwards
segs += [("ltf", 98.50, 98.60, 98.20, 98.30)]                  # leaves zone below
segs += [("ltf", 98.30, 99.10, 98.25, 99.00)]                  # retrace taps CE
segs += tail(14, 99.00)
o, h, l, c = build(segs)
ev = run(o, h, l, c)
check("bearish sweep fires", [(b, d) for b, d in ev["ls"]] == [(ls_bar, -1)], ev["ls"])
check("MSS fires short", len(ev["mss"]) == 1 and ev["mss"][0][1] == -1, ev["mss"])
check("one IFVG flipped", len(ev["ifvg"]) == 1, ev["ifvg"])
check("exactly one short entry", len(ev["entry"]) == 1 and ev["entry"][0]["dir"] == -1,
      [(e["bar"], e["dir"]) for e in ev["entry"]])
if ev["entry"]:
    e = ev["entry"][0]
    check("SL sits above the entry (short)", e["sl"] > e["ce"], (e["sl"], e["ce"]))
    check("TP sits below the entry (short)", e["tp"] < e["ce"], (e["tp"], e["ce"]))
    check("CE is the zone midpoint", abs(e["ce"] - (e["zgTop"] + e["zgBot"]) / 2) < 1e-9, e)

print()
print(f"{'ALL TESTS PASSED' if not FAILS else 'FAILURES: ' + ', '.join(FAILS)}")
raise SystemExit(1 if FAILS else 0)


if __name__ == "__main__":
    raise SystemExit(main())
