#!/usr/bin/env python3
"""
Reference simulation of Arena_AI_ICT_Sequence_Model.pine.

Pine Script cannot be executed outside TradingView, so this script re-implements
the *model logic* (liquidity map, sweep engine, structure, breaker finder and the
state machine) in Python and drives it with a synthetic textbook setup:

    external SSL  ->  sweep  ->  reclaim  ->  LTF MSS  ->  breaker
                  ->  BUY LIMIT armed  ->  retracement fill  ->  TP

It is a specification test, not a Pine interpreter: it verifies the ORDER of the
sequence and that no signal can appear without the full chain. If you change the
Pine logic, keep this file in sync and re-run it.
"""
import math
import sys

# ---------------------------------------------------------------- state names
(ST_IDLE, ST_EXT_LIQ, ST_HTF_CTX, ST_WAIT_SWEEP, ST_SWEPT, ST_WAIT_MSS,
 ST_MSS, ST_BREAKER, ST_ARMED, ST_WAIT_RET, ST_TRIGGERED, ST_ACTIVE, ST_TP,
 ST_SL, ST_INVALID, ST_EXPIRED) = range(16)

NAMES = {
    ST_IDLE: "IDLE", ST_EXT_LIQ: "EXTERNAL_LIQUIDITY_FOUND",
    ST_HTF_CTX: "HTF_CONTEXT_CONFIRMED", ST_WAIT_SWEEP: "WAITING_FOR_SWEEP",
    ST_SWEPT: "LIQUIDITY_SWEPT", ST_WAIT_MSS: "WAITING_FOR_LTF_MSS",
    ST_MSS: "MSS_CONFIRMED", ST_BREAKER: "BREAKER_CREATED",
    ST_ARMED: "ENTRY_ARMED", ST_WAIT_RET: "WAITING_FOR_RETRACEMENT",
    ST_TRIGGERED: "LIMIT_ENTRY_TRIGGERED", ST_ACTIVE: "TRADE_ACTIVE",
    ST_TP: "TARGET_REACHED", ST_SL: "STOP_HIT",
    ST_INVALID: "SETUP_INVALIDATED", ST_EXPIRED: "SETUP_EXPIRED",
}
FINISHED = {ST_TP, ST_SL, ST_INVALID, ST_EXPIRED}

PARAMS = dict(
    swing=5, ext_swing=20, struct_lookback=200, max_age=600,
    eq_on=True, eq_tol_atr=0.25, eq_min_bars=5, max_levels=12,
    sweep_mode="Wick + close back inside", min_pen_ticks=0.0, strict_atr=0.5,
    reclaim_bars=3, max_sweep_mss=30,
    htf_require=True, htf_dist=4.0,
    mss_close=True, mss_min_atr=0.10,
    disp_on=True, disp_body_ratio=0.50, disp_range_atr=0.80, disp_body_atr=0.30,
    disp_window=5,
    brk_lookback=20, ltf_fvg_on=False,
    entry_mode="50% midpoint", entry_pct=50,
    sl_mode="Sweep extreme", sl_buf_atr=0.25,
    tp_mode="Furthest liquidity", tp_rr_mult=3.0,
    min_rr=2.0, setup_expiry=80, entry_expiry=40, result_keep=10,
    require_ext=True,
)


# ------------------------------------------------------------------- ATR (RMA)
def atr_series(bars, length=14):
    out, prev = [], None
    trs = []
    for i, b in enumerate(bars):
        if i == 0:
            tr = b[1] - b[2]
        else:
            pc = bars[i - 1][3]
            tr = max(b[1] - b[2], abs(b[1] - pc), abs(b[2] - pc))
        trs.append(tr)
        if i < length - 1:
            out.append(None)
            continue
        if prev is None:
            prev = sum(trs[:length]) / length
        else:
            prev = (prev * (length - 1) + tr) / length
        out.append(prev)
    return out


def pivots(bars, strength):
    """Return (high_pivot_at_bar, low_pivot_at_bar) arrays - confirmed at i+strength."""
    n = len(bars)
    ph = [None] * n
    pl = [None] * n
    for i in range(strength, n - strength):
        h, l = bars[i][1], bars[i][2]
        if all(bars[i - k][1] < h for k in range(1, strength + 1)) and \
           all(bars[i + k][1] < h for k in range(1, strength + 1)):
            ph[i] = h
        if all(bars[i - k][2] > l for k in range(1, strength + 1)) and \
           all(bars[i + k][2] > l for k in range(1, strength + 1)):
            pl[i] = l
    return ph, pl


class Liq:
    def __init__(self, price, b_idx, is_bsl, external, strength):
        self.price, self.b_idx, self.is_bsl = price, b_idx, is_bsl
        self.external, self.strength = external, strength
        self.is_eq = self.swept = self.broken = False
        self.brk_bar = None
        self.sw_bar = self.sw_ext = None


STATE_LOG = []
CUR_BAR = 0


class Setup:
    def __init__(self):
        self.reset()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if getattr(self, "_state", None) != value:
            STATE_LOG.append((CUR_BAR, getattr(self, "dir", 0), value, getattr(self, "reason", "")))
        self._state = value

    def reset(self):
        self.dir = 0
        self.state = ST_IDLE
        self.ext_liq = False
        self.ext_liq_p = None
        self.htf_ctx = False
        self.swept = False
        self.sw_level = None
        self.sw_bar = None
        self.sw_ext = None
        self.sw_conf = False
        self.mss = False
        self.mss_level = None
        self.mss_bar = None
        self.brk = False
        self.brk_top = self.brk_bot = self.brk_bar = None
        self.armed = False
        self.arm_bar = None
        self.trig = False
        self.trig_bar = None
        self.entry = self.sl = self.tp1 = self.tp = self.rr = None
        self.tp1_hit = False
        self.reason = ""
        self.end_bar = None
        self.events = {}


def sweep_ok(is_bsl, lvl, o, h, l, c, atr, p):
    pen = (h - lvl) if is_bsl else (lvl - l)
    if pen <= 0 or pen < p["min_pen_ticks"]:
        return False
    back = (c < lvl) if is_bsl else (c > lvl)
    if p["sweep_mode"] == "Wick penetration":
        return True
    if p["sweep_mode"] == "Wick + close back inside":
        return back
    if atr is None:            # na ATR in Pine makes the comparison false
        return False
    rej = (c < o and (h - c) >= p["strict_atr"] * atr) if is_bsl else \
          (c > o and (c - l) >= p["strict_atr"] * atr)
    return back and rej


def simulate(bars, p=PARAMS, htf_zone=None, verbose=True):
    n = len(bars)
    atr = atr_series(bars)
    ph_int, pl_int = pivots(bars, p["swing"])
    ph_ext, pl_ext = pivots(bars, p["ext_swing"])

    liqs = []
    bull, bear = Setup(), Setup()
    setups = {1: bull, -1: bear}
    bull_disp = bear_disp = -10 ** 6
    last_ih = last_ih_bar = last_il = last_il_bar = None
    last_ih_brk = last_il_brk = True
    transitions = []
    last_state = {}

    def eq_tol(price):
        return (atr[i] or 0) * p["eq_tol_atr"]

    def add_level(price, b_idx, is_bsl, external, i):
        tol = eq_tol(price)
        merge_idx = -1
        for k in range(len(liqs) - 1, -1, -1):
            q = liqs[k]
            if merge_idx < 0 and p["eq_on"] and not q.swept and q.is_bsl == is_bsl \
               and q.external == external and abs(q.price - price) <= tol \
               and abs(b_idx - (q.b_idx or b_idx)) >= p["eq_min_bars"]:
                merge_idx = k
        if merge_idx >= 0:
            q = liqs[merge_idx]
            q.price = max(q.price, price) if is_bsl else min(q.price, price)
            q.is_eq = True
            q.b_idx = b_idx
        else:
            liqs.append(Liq(price, b_idx, is_bsl, external, p["ext_swing"] if external else p["swing"]))
        for k in range(len(liqs) - 1, -1, -1):
            if liqs[k].b_idx is not None and i - liqs[k].b_idx > p["max_age"]:
                liqs.pop(k)
        ext = [q for q in liqs if q.external]
        if len(ext) > p["max_levels"]:
            cand = [q for q in ext if not q.swept and not q.broken]
            if cand:
                liqs.remove(min(cand, key=lambda q: q.b_idx))

    def nearest_liq(want_bsl, price, only_ext):
        best = None
        for q in liqs:
            if q.is_bsl != want_bsl or q.swept or q.broken or q.price is None:
                continue
            if only_ext and not q.external:
                continue
            if want_bsl and q.price > price and (best is None or q.price < best):
                best = q.price
            if not want_bsl and q.price < price and (best is None or q.price > best):
                best = q.price
        return best

    def furthest_liq(want_bsl, price, only_ext):
        best = None
        for q in liqs:
            if q.is_bsl != want_bsl or q.swept or q.broken or q.price is None:
                continue
            if only_ext and not q.external:
                continue
            if want_bsl and q.price > price and (best is None or q.price > best):
                best = q.price
            if not want_bsl and q.price < price and (best is None or q.price < best):
                best = q.price
        return best

    def nearest_swing(want_high, price):
        best = None
        for q in liqs:
            if q.is_bsl != want_high or q.swept or q.price is None:
                continue
            if want_high and q.price > price and (best is None or q.price < best):
                best = q.price
            if not want_high and q.price < price and (best is None or q.price > best):
                best = q.price
        return best

    def protected_level(direction, sw_bar):
        lvl, best_idx = None, -1
        for q in liqs:
            if q.is_bsl != (direction == 1) or q.b_idx is None or q.price is None:
                continue
            brk_ok = (not q.broken) or (q.brk_bar is not None and q.brk_bar > sw_bar)
            if not brk_ok:
                continue
            if q.b_idx < sw_bar and q.b_idx >= sw_bar - p["struct_lookback"] and q.b_idx > best_idx:
                best_idx, lvl = q.b_idx, q.price
        return lvl

    def htf_ctx_ok(direction, ref):
        if htf_zone is None or ref is None:
            return False
        top, bot, bullish = htf_zone
        if bullish != (direction == 1):
            return False
        mid = (top + bot) / 2
        return abs(ref - mid) <= p["htf_dist"] * atr[i]

    def find_breaker(is_bull, sw_bar_idx, i):
        max_back = min(p["brk_lookback"], max(1, i - sw_bar_idx))
        leg_start, stop1 = 0, False
        for k in range(1, max_back + 1):
            if stop1:
                break
            o1, c1 = bars[i - k][0], bars[i - k][3]
            if (c1 > o1) == is_bull:
                leg_start = k
            else:
                stop1 = True
        lim = min(leg_start + p["brk_lookback"], i - sw_bar_idx)
        b_off, stop2 = -1, False
        if lim > leg_start:
            for j in range(leg_start + 1, lim + 1):
                if stop2:
                    break
                o2, c2 = bars[i - j][0], bars[i - j][3]
                if (c2 < o2) if is_bull else (c2 > o2):
                    b_off, stop2 = j, True
        if b_off > 0:
            return True, bars[i - b_off][1], bars[i - b_off][2], b_off
        return False, None, None, -1

    def compute_trade(s, is_bull, i):
        zt, zb = s.brk_top, s.brk_bot
        e = (zt + zb) / 2
        if p["entry_mode"] == "Proximal edge":
            e = zt if is_bull else zb
        elif p["entry_mode"] == "Distal edge":
            e = zb if is_bull else zt
        s.entry = e
        buf = p["sl_buf_atr"] * (atr[i] or 0)
        slv = s.sw_ext - buf if is_bull else s.sw_ext + buf
        if p["sl_mode"] == "Breaker distal edge":
            slv = (zb - buf) if is_bull else (zt + buf)
        elif p["sl_mode"] == "LTF swing":
            sw = nearest_swing(False, e) if is_bull else nearest_swing(True, e)
            if sw is not None:
                slv = sw - buf if is_bull else sw + buf
        s.sl = slv
        near, far = nearest_liq(is_bull, e, True), furthest_liq(is_bull, e, True)
        s.tp1 = near
        fin = near if p["tp_mode"] == "Nearest liquidity" else far if p["tp_mode"] == "Furthest liquidity" else None
        if fin is None:
            fin = e + p["tp_rr_mult"] * (e - slv) if is_bull else e - p["tp_rr_mult"] * (slv - e)
        s.tp = fin
        if s.tp1 is None:
            s.tp1 = fin
        risk = abs(e - slv)
        s.rr = (abs(fin - e) / risk) if risk > 0 else None

    STATE_LOG.clear()
    for i in range(n):
        global CUR_BAR
        CUR_BAR = i
        o, h, l, c = bars[i]
        ext_ssl_new = ext_bsl_new = False
        ext_ssl_p = ext_bsl_p = None
        ssl_swept = bsl_swept = False
        ssl_lvl = bsl_lvl = None
        bull_disp_now = bear_disp_now = False

        # ---------------------------------------------------------- liquidity
        if ph_ext[i - p["ext_swing"]] is not None if i >= p["ext_swing"] else False:
            lvl = ph_ext[i - p["ext_swing"]]
            add_level(lvl, i - p["ext_swing"], True, True, i)
            ext_bsl_new, ext_bsl_p = True, lvl
        if pl_ext[i - p["ext_swing"]] is not None if i >= p["ext_swing"] else False:
            lvl = pl_ext[i - p["ext_swing"]]
            add_level(lvl, i - p["ext_swing"], False, True, i)
            ext_ssl_new, ext_ssl_p = True, lvl
        if ph_int[i - p["swing"]] is not None if i >= p["swing"] else False:
            add_level(ph_int[i - p["swing"]], i - p["swing"], True, False, i)
        if pl_int[i - p["swing"]] is not None if i >= p["swing"] else False:
            add_level(pl_int[i - p["swing"]], i - p["swing"], False, False, i)

        # -------------------------------------------------- HH/HL/LH/LL + BOS
        if i >= p["swing"] and ph_int[i - p["swing"]] is not None:
            last_ih, last_ih_bar, last_ih_brk = ph_int[i - p["swing"]], i - p["swing"], False
        if i >= p["swing"] and pl_int[i - p["swing"]] is not None:
            last_il, last_il_bar, last_il_brk = pl_int[i - p["swing"]], i - p["swing"], False
        if last_ih is not None and not last_ih_brk and c > last_ih:
            last_ih_brk = True
            for q in liqs:
                if not q.external and not q.broken and q.b_idx == last_ih_bar:
                    q.broken, q.brk_bar = True, i
        if last_il is not None and not last_il_brk and c < last_il:
            last_il_brk = True
            for q in liqs:
                if not q.external and not q.broken and q.b_idx == last_il_bar:
                    q.broken, q.brk_bar = True, i

        # ---------------------------------------------------------- sweeps
        for q in liqs:
            if q.swept or q.price is None:
                continue
            if not (q.external or not p["require_ext"]):
                continue
            approached = (bars[i - 1][3] < q.price) if q.is_bsl else (bars[i - 1][3] > q.price)
            if approached and sweep_ok(q.is_bsl, q.price, o, h, l, c, atr[i], p):
                q.swept, q.sw_bar, q.sw_ext = True, i, (h if q.is_bsl else l)
                if q.is_bsl and not bsl_swept:
                    bsl_swept, bsl_lvl = True, q.price
                if not q.is_bsl and not ssl_swept:
                    ssl_swept, ssl_lvl = True, q.price

        # ---------------------------------------------------------- displacement
        rng, body = h - l, c - o
        a = atr[i]
        if a is not None and rng > 0:
            if (body / rng) >= p["disp_body_ratio"] and rng >= p["disp_range_atr"] * a \
               and max(body, 0) >= p["disp_body_atr"] * a:
                bull_disp_now = True
            if (-body / rng) >= p["disp_body_ratio"] and rng >= p["disp_range_atr"] * a \
               and max(-body, 0) >= p["disp_body_atr"] * a:
                bear_disp_now = True
        if bull_disp_now:
            bull_disp = i
        if bear_disp_now:
            bear_disp = i

        # ------------------------------------------------------- state machine
        for direction, s in setups.items():
            is_bull = direction == 1
            if s.state in FINISHED:
                if s.end_bar is not None and i - s.end_bar >= p["result_keep"]:
                    s.reset()
                continue

            # PHASE 0
            if s.state < ST_SWEPT:
                new_level = ext_ssl_new if is_bull else ext_bsl_new
                if new_level:
                    if s.state != ST_IDLE:
                        s.reset()
                    s.dir, s.ext_liq = direction, True
                    s.ext_liq_p = ext_ssl_p if is_bull else ext_bsl_p
                    s.state = ST_EXT_LIQ
                    s.events[i] = "setups"
                if s.state == ST_EXT_LIQ:
                    if htf_ctx_ok(direction, s.ext_liq_p):
                        s.htf_ctx, s.state = True, ST_HTF_CTX
                    elif not p["htf_require"]:
                        s.htf_ctx, s.state = False, ST_HTF_CTX
                if s.state == ST_HTF_CTX:
                    s.state = ST_WAIT_SWEEP
                swept_now = ssl_swept if is_bull else bsl_swept
                if swept_now:
                    if s.state == ST_IDLE:
                        s.dir, s.ext_liq = direction, True
                        s.ext_liq_p = ssl_lvl if is_bull else bsl_lvl
                    s.swept = True
                    s.sw_level = ssl_lvl if is_bull else bsl_lvl
                    s.sw_bar, s.sw_ext = i, (l if is_bull else h)
                    s.state = ST_SWEPT
                    if not s.htf_ctx and htf_ctx_ok(direction, s.sw_level):
                        s.htf_ctx = True

            # PHASE 1
            if s.state == ST_SWEPT:
                reclaim = (c > s.sw_level) if is_bull else (c < s.sw_level)
                if reclaim:
                    s.sw_conf, s.state = True, ST_WAIT_MSS
                elif i - s.sw_bar > p["reclaim_bars"]:
                    s.reason, s.end_bar, s.state = "Sweep was not reclaimed in time", i, ST_INVALID
            if s.state == ST_WAIT_MSS:
                s.sw_ext = min(s.sw_ext or l, l) if is_bull else max(s.sw_ext or h, h)
                prot = protected_level(direction, s.sw_bar)
                if prot is not None:
                    beyond = (c > prot) if p["mss_close"] else (h > prot)
                    if not is_bull:
                        beyond = (c < prot) if p["mss_close"] else (l < prot)
                    av = atr[i]
                    min_break = False if av is None else \
                        ((c > prot + p["mss_min_atr"] * av) if is_bull else (c < prot - p["mss_min_atr"] * av))
                    disp_ok = True if not p["disp_on"] else \
                        ((i - bull_disp) <= p["disp_window"] if is_bull else (i - bear_disp) <= p["disp_window"])
                    if beyond and min_break and disp_ok:
                        s.mss, s.mss_level, s.mss_bar = True, prot, i
                        s.state = ST_MSS
                if s.state == ST_WAIT_MSS and i - s.sw_bar > p["max_sweep_mss"]:
                    s.reason, s.end_bar, s.state = "Sweep -> MSS window expired", i, ST_EXPIRED

            # PHASE 2
            if s.state == ST_MSS:
                if p["htf_require"] and not s.htf_ctx:
                    s.reason, s.end_bar, s.state = "HTF context missing at the MSS", i, ST_INVALID
                else:
                    ok, top, bot, off = find_breaker(is_bull, s.sw_bar, i)
                    if ok:
                        s.brk, s.brk_top, s.brk_bot = True, top, bot
                        s.brk_bar = i - off if off > 0 else i
                        s.state = ST_BREAKER
                    else:
                        s.reason, s.end_bar, s.state = "No breaker candle found", i, ST_INVALID

            # PHASE 3
            if s.state == ST_BREAKER:
                compute_trade(s, is_bull, i)
                if None in (s.entry, s.sl, s.tp):
                    s.reason, s.end_bar, s.state = "No valid entry / SL / TP", i, ST_INVALID
                elif (is_bull and s.sl >= s.entry) or (not is_bull and s.sl <= s.entry):
                    s.reason, s.end_bar, s.state = "Stop loss on the wrong side of entry", i, ST_INVALID
                elif s.rr is None or s.rr < p["min_rr"]:
                    s.reason, s.end_bar, s.state = "RR below minimum", i, ST_INVALID
                else:
                    s.armed, s.arm_bar, s.state = True, i, ST_ARMED

            # PHASE 4
            if s.state == ST_ARMED and i > s.arm_bar:
                s.state = ST_WAIT_RET
            if s.state == ST_WAIT_RET:
                touched = (l <= s.entry) if is_bull else (h >= s.entry)
                if touched:
                    s.trig, s.trig_bar, s.state = True, i, ST_TRIGGERED
                elif (is_bull and c < s.brk_bot) or (not is_bull and c > s.brk_top):
                    s.reason, s.end_bar, s.state = "Breaker invalidated before entry", i, ST_INVALID
                elif i - s.sw_bar > p["setup_expiry"]:
                    s.reason, s.end_bar, s.state = "Setup exceeded the maximum number of bars", i, ST_EXPIRED
                elif i - s.arm_bar > p["entry_expiry"]:
                    s.reason, s.end_bar, s.state = "Entry window expired", i, ST_EXPIRED

            # PHASE 5
            if s.state == ST_TRIGGERED and i > s.trig_bar:
                s.state = ST_ACTIVE
            if s.state == ST_ACTIVE and s.trig_bar != i:
                sl_hit = (l <= s.sl) if is_bull else (h >= s.sl)
                tp_hit = (h >= s.tp) if is_bull else (l <= s.tp)
                if sl_hit:
                    s.state, s.end_bar = ST_SL, i
                elif tp_hit:
                    s.state, s.end_bar = ST_TP, i

    transitions = [(b, d, st, r) for (b, d, st, r) in STATE_LOG]
    return transitions, setups


# --------------------------------------------------------------- test scenario
def build_bars():
    """A textbook bullish sequence: external SSL -> sweep -> reclaim ->
    displacement MSS -> breaker -> retracement fill -> run to the target."""
    B = []

    def candle(o, c, up=0.10, dn=0.10):
        hi = round(max(o, c) + up, 2)
        lo = round(min(o, c) - dn, 2)
        B.append((round(o, 2), hi, lo, round(c, 2)))

    # 0..24   decline 100.00 -> 90.70 (all lows stay above 90.00)
    px = 100.0
    for _ in range(25):
        candle(px, px - 0.37)
        px -= 0.37
    # 25      external sell-side liquidity: the low at 90.00
    candle(90.70, 90.75, up=0.05, dn=0.75)
    # 26..44  rise 90.75 -> 94.55  (bar 45 confirms the pivot low at bar 25)
    px = 90.75
    for _ in range(19):
        candle(px, px + 0.20)
        px += 0.20
    # 45..54  continue to 94.90
    for _ in range(10):
        candle(px, px + 0.035)
        px += 0.035
    # 55      swing high 95.00 (confirmed as a pivot 5 bars later, external at 75)
    candle(94.90, 94.85, up=0.15, dn=0.10)
    # 56..63  decline 94.85 -> 92.30
    px = 94.85
    for _ in range(8):
        candle(px, px - 0.32)
        px -= 0.32
    # 64..67  small bounce, bar 67 is the local high at 93.20
    for o, c in ((92.30, 92.50), (92.50, 92.70), (92.70, 92.95), (92.95, 93.05)):
        candle(o, c, up=0.15, dn=0.08)
    # 68..69  decline into the sweep
    candle(93.05, 92.60)
    candle(92.60, 91.00)
    # 70      SWEEP the external 90.00 level, close back above it
    candle(90.90, 90.40, up=0.15, dn=1.40)
    # 71..77  rally (the leg) to 92.85
    px = 90.40
    for _ in range(7):
        candle(px, px + 0.35)
        px += 0.35
    # 78      displacement candle that breaks the protected high 93.20 -> MSS
    candle(92.85, 93.60, up=0.10, dn=0.05)
    # 79..85  retracement back into the breaker (entry is the zone midpoint)
    for o, c, up, dn in ((93.60, 93.10, 0.10, 0.15), (93.10, 92.40, 0.10, 0.15),
                         (92.40, 91.60, 0.10, 0.15), (91.60, 90.90, 0.10, 0.15),
                         (90.90, 90.50, 0.10, 0.20), (90.50, 90.20, 0.10, 0.25),
                         (90.20, 90.60, 0.15, 0.25)):
        candle(o, c, up=up, dn=dn)
    # 86..    run to the target (95.00 external buy-side liquidity)
    px = 90.60
    while px < 95.40:
        candle(px, px + 0.18)
        px += 0.18
    for _ in range(5):
        candle(px, px + 0.25)
        px += 0.25
    return B


def validate(bars):
    bad = []
    for i, (o, h, l, c) in enumerate(bars):
        if h < max(o, c) or l > min(o, c) or h < l:
            bad.append(i)
    return bad


def mirror(bars, level=200.0):
    """Reflect a series around a price level, turning a bull scenario into the
    exact bearish equivalent (buy-side liquidity, sweep above, MSS down)."""
    return [(round(level - o, 2), round(level - l, 2), round(level - h, 2),
             round(level - c, 2)) for (o, h, l, c) in bars]


def check_chain(transitions, direction, setups, problems):
    seen = []
    for idx, d, state, reason in transitions:
        if d != direction:
            continue
        if state == ST_IDLE or (seen and seen[-1] == state):
            continue
        seen.append(state)
    order = [ST_EXT_LIQ, ST_HTF_CTX, ST_WAIT_SWEEP, ST_SWEPT, ST_WAIT_MSS,
             ST_MSS, ST_BREAKER, ST_ARMED, ST_WAIT_RET, ST_TRIGGERED,
             ST_ACTIVE, ST_TP]
    pos = -1
    for st in order:
        if st not in seen:
            problems.append(f"{NAMES[st]} never reached")
            continue
        p = seen.index(st)
        if p < pos:
            problems.append(f"{NAMES[st]} came out of order")
        pos = p
    for st in (ST_INVALID, ST_SL, ST_EXPIRED):
        if st in seen and st != seen[-1]:
            problems.append(f"setup ended in {NAMES[st]} but continued afterwards")
    s = setups[direction]
    if not s.armed or not s.trig:
        problems.append("setup never armed or never triggered")
    if s.rr is None or s.rr < PARAMS["min_rr"]:
        problems.append("RR below the configured minimum")
    return seen


def report(title, transitions, direction, setups):
    print("=" * 74)
    print(title)
    print("=" * 74)
    for idx, d, state, reason in transitions:
        if d != direction or state == ST_IDLE:
            continue
        extra = f"   <- {reason}" if reason else ""
        print(f"  bar {idx:3d}  {NAMES[state]}{extra}")
    s = setups[direction]
    fmt = lambda v: "-" if v is None else f"{v:.2f}"
    print(f"\nfinal plan: entry {fmt(s.entry)} | stop {fmt(s.sl)} | "
          f"tp1 {fmt(s.tp1)} | tp {fmt(s.tp)} | rr {fmt(s.rr)}")
    print()


def main():
    problems = []

    bars = build_bars()
    bad = validate(bars)
    if bad:
        print(f"malformed candles at bars: {bad}")
        return 2

    # ---- 1. bullish chain -------------------------------------------------
    t1, st1 = simulate(bars, PARAMS, htf_zone=(90.6, 89.6, True))
    report("TEST 1 - textbook BULLISH sequence", t1, 1, st1)
    check_chain(t1, 1, st1, problems)

    # ---- 2. bearish mirror ------------------------------------------------
    mbars = mirror(bars)
    t2, st2 = simulate(mbars, PARAMS, htf_zone=(110.4, 109.4, False))
    report("TEST 2 - mirrored BEARISH sequence", t2, -1, st2)
    check_chain(t2, -1, st2, problems)

    # ---- 3. sweep without an MSS -----------------------------------------
    print("=" * 74)
    print("TEST 3 - sweep without an MSS must never produce a signal")
    print("=" * 74)
    chop = build_bars()[:71]
    px = 90.40
    for k in range(40):
        px = 90.40 + (0.05 if k % 2 == 0 else -0.05)
        chop.append((round(px, 2), round(px + 0.15, 2), round(px - 0.15, 2), round(px + 0.02, 2)))
    _, st3 = simulate(chop, PARAMS, htf_zone=(90.6, 89.6, True), verbose=False)
    b3 = st3[1]
    print(f"final state    : {NAMES[b3.state]}")
    print(f"entry armed    : {b3.armed}")
    print(f"signal printed : {b3.trig}")
    if b3.trig or b3.armed:
        problems.append("TEST 3: a signal appeared without a confirmed MSS")
    else:
        print("PASS")
    print()

    # ---- 4. RR below the minimum -----------------------------------------
    print("=" * 74)
    print("TEST 4 - a setup under the minimum RR must be rejected")
    print("=" * 74)
    strict = dict(PARAMS, min_rr=10.0)
    t4, st4 = simulate(bars, strict, htf_zone=(90.6, 89.6, True), verbose=False)
    reasons = [r for _, d, _, r in t4 if d == 1 and r]
    armed = [1 for _, d, st, _ in t4 if d == 1 and st == ST_ARMED]
    print(f"rejections     : {reasons[:3]}")
    print(f"times armed    : {len(armed)}")
    if armed:
        problems.append("TEST 4: a sub-minimum RR setup was armed")
    elif not any("RR" in r for r in reasons):
        problems.append("TEST 4: rejected for the wrong reason")
    else:
        print("PASS")
    print()

    print("=" * 74)
    if problems:
        print("FAILED:")
        for x in problems:
            print("  - " + x)
        return 1
    print("ALL TESTS PASSED")
    print("  * full bull chain in order, ending at the target")
    print("  * full bear chain in order (mirrored)")
    print("  * no signal without an MSS")
    print("  * no signal under the minimum RR")
    return 0


if __name__ == "__main__":
    sys.exit(main())
