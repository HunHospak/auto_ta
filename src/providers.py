"""Data provider for auto_ta — OHLC via yfinance."""
from __future__ import annotations

import yfinance as yf


def get_ohlc(tickers: list[str]) -> dict:
    """Return { ticker: {closes, highs, lows, prev_h, prev_l, prev_c} } (lists of floats)."""
    if not tickers:
        return {}
    data = yf.download(
        tickers, period="400d", interval="1d", group_by="ticker",
        auto_adjust=True, threads=True, progress=False,
    )
    out: dict[str, dict] = {}
    multi = len(tickers) > 1
    for t in tickers:
        try:
            df = (data[t] if multi else data).dropna(subset=["Close", "High", "Low"])
            if len(df) < 30:
                continue
            closes = [float(x) for x in df["Close"].tolist()]
            highs = [float(x) for x in df["High"].tolist()]
            lows = [float(x) for x in df["Low"].tolist()]
            out[t] = {
                "closes": closes,
                "highs": highs,
                "lows": lows,
                "prev_h": highs[-2],
                "prev_l": lows[-2],
                "prev_c": closes[-2],
            }
        except Exception:
            continue
    return out
