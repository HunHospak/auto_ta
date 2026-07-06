"""Pure technical-analysis math — no I/O, unit-testable.

Levels only ("here is support / resistance / trend"), never a call ("this will go up").
"""
from __future__ import annotations


def sma(vals: list[float], n: int) -> float | None:
    return round(sum(vals[-n:]) / n, 4) if len(vals) >= n else None


def rsi(closes: list[float], n: int = 14) -> float | None:
    if len(closes) < n + 1:
        return None
    gains = 0.0
    losses = 0.0
    for i in range(len(closes) - n, len(closes)):
        ch = closes[i] - closes[i - 1]
        if ch >= 0:
            gains += ch
        else:
            losses -= ch
    if losses == 0:
        return 100.0
    rs = (gains / n) / (losses / n)
    return round(100.0 - 100.0 / (1.0 + rs), 1)


def trend(last: float, sma20, sma50, sma200) -> str:
    above = sum(1 for m in (sma20, sma50, sma200) if m and last > m)
    have = sum(1 for m in (sma20, sma50, sma200) if m)
    if have == 0:
        return "unknown"
    if above == have:
        return "uptrend"
    if above == 0:
        return "downtrend"
    return "sideways"


def pivots(prev_h: float, prev_l: float, prev_c: float) -> dict:
    p = (prev_h + prev_l + prev_c) / 3.0
    rng = prev_h - prev_l
    return {
        "p": round(p, 2),
        "r1": round(2 * p - prev_l, 2), "s1": round(2 * p - prev_h, 2),
        "r2": round(p + rng, 2), "s2": round(p - rng, 2),
    }


def fib_levels(swing_high: float, swing_low: float) -> dict:
    d = swing_high - swing_low
    return {r: round(swing_high - d * float(r), 2) for r in ("0.236", "0.382", "0.5", "0.618", "0.786")}


def analyze(ticker: str, series: dict, cfg: dict) -> dict:
    closes, highs, lows = series["closes"], series["highs"], series["lows"]
    last = closes[-1]
    smas = {f"sma{n}": sma(closes, n) for n in cfg["sma_windows"]}
    tr = trend(last, smas.get("sma20"), smas.get("sma50"), smas.get("sma200"))
    srw = int(cfg["sr_window"])
    sww = int(cfg["swing_window"])
    support = round(min(lows[-srw:]), 2) if len(lows) >= srw else None
    resistance = round(max(highs[-srw:]), 2) if len(highs) >= srw else None
    swing_high = max(highs[-sww:]) if len(highs) >= sww else max(highs)
    swing_low = min(lows[-sww:]) if len(lows) >= sww else min(lows)

    out = {
        "ticker": ticker,
        "last": round(last, 2),
        "trend": tr,
        "rsi": rsi(closes, int(cfg["rsi_window"])),
        "support": support,
        "resistance": resistance,
        "swing_high": round(swing_high, 2),
        "swing_low": round(swing_low, 2),
        "pivots": pivots(series["prev_h"], series["prev_l"], series["prev_c"]),
        "fib": fib_levels(swing_high, swing_low),
    }
    out.update({k: v for k, v in smas.items()})
    return out
