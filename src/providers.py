"""Data provider for auto_ta — OHLC via yfinance."""
from __future__ import annotations

import logging

import pandas as pd
import yfinance as yf


def get_ohlc(tickers: list[str]) -> dict:
    """Return observed daily OHLC history and the last usable bar date per ticker."""
    if not tickers:
        return {}
    try:
        data = yf.download(
            tickers, period="400d", interval="1d", group_by="ticker",
            auto_adjust=True, threads=True, progress=False,
        )
    except Exception as exc:
        logging.getLogger(__name__).warning("Price download failed (%s)", type(exc).__name__)
        return {}
    if data is None or data.empty:
        return {}
    out: dict[str, dict] = {}
    grouped = isinstance(data.columns, pd.MultiIndex)
    if not grouped and len(tickers) != 1:
        return {}
    for t in tickers:
        try:
            df = (data[t] if grouped else data).dropna(subset=["Close", "High", "Low"]).sort_index()
            if not isinstance(df.index, pd.DatetimeIndex):
                continue
            df = df.loc[df.index.notna() & ~df.index.duplicated(keep="last")]
            df = df.loc[~df[["Close", "High", "Low"]].isin([float("inf"), float("-inf")]).any(axis=1)]
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
                "as_of": df.index[-1].date().isoformat(),
            }
        except Exception:
            continue
    return out
