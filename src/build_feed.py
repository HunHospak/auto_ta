"""Orchestration: ingest -> compute -> validate(schema) -> write out/."""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from providers import get_ohlc  # noqa: E402
from compute import analyze  # noqa: E402


def load_config() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def load_schema() -> dict:
    return json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))


def build(cfg: dict, *, generated_at: dt.datetime | None = None) -> dict:
    now = generated_at or dt.datetime.now(dt.timezone.utc)
    tickers = list(cfg["tickers"])
    series = get_ohlc(tickers)
    max_age_days = int(cfg.get("max_observation_age_days", 4))
    fresh = {
        ticker: bars for ticker, bars in series.items()
        if 0 <= (now.date() - dt.date.fromisoformat(bars["as_of"])).days <= max_age_days
    }
    as_of = max((bars["as_of"] for bars in fresh.values()), default=None)
    rows = [
        {**analyze(t, fresh[t], cfg), "as_of": as_of}
        for t in tickers if t in fresh and fresh[t]["as_of"] == as_of
    ]

    notes = []
    if not rows:
        status = "unavailable"
        notes.append(f"No usable OHLC bars within the last {max_age_days} calendar days.")
    else:
        if (now.date() - dt.date.fromisoformat(as_of)).days > 3:
            notes.append(f"Latest usable OHLC bars are from {as_of}.")
        if len(rows) < len(tickers):
            notes.append(f"{len(tickers) - len(rows)} tickers lacked usable OHLC bars for {as_of}.")
        status = "partial" if notes else "active"

    feed = {
        "service": cfg["service"],
        "schema_version": str(cfg["schema_version"]),
        "generated_at": now.replace(microsecond=0).isoformat(),
        "status": status,
        "ttl_hours": cfg["ttl_hours"],
        "data": {
            "as_of": as_of,
            "count": len(rows),
            "tickers": rows,
            "disclaimer": "Technical levels from price data, not signals to buy or sell.",
        },
    }
    if notes:
        feed["notes"] = " ".join(notes)
    return feed


def main() -> None:
    cfg = load_config()
    feed = build(cfg)
    jsonschema.validate(feed, load_schema())
    out = ROOT / "out"
    (out / "history").mkdir(parents=True, exist_ok=True)
    payload = json.dumps(feed, indent=2, allow_nan=False)
    (out / "auto_ta.json").write_text(payload, encoding="utf-8")
    if feed["data"]["as_of"]:
        (out / "history" / f"{feed['data']['as_of']}.json").write_text(payload, encoding="utf-8")
    print(f"[auto_ta] status={feed['status']} tickers={feed['data']['count']}")


if __name__ == "__main__":
    main()
