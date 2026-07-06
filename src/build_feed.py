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


def build(cfg: dict) -> dict:
    tickers = list(cfg["tickers"])
    series = get_ohlc(tickers)
    rows = [analyze(t, series[t], cfg) for t in tickers if t in series]

    if not rows:
        status, notes = "unavailable", "no price data"
    elif len(rows) < len(tickers):
        status, notes = "partial", f"{len(tickers) - len(rows)} tickers missing"
    else:
        status, notes = "active", None

    feed = {
        "service": cfg["service"],
        "schema_version": str(cfg["schema_version"]),
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "ttl_hours": cfg["ttl_hours"],
        "data": {
            "as_of": dt.date.today().isoformat(),
            "count": len(rows),
            "tickers": rows,
            "disclaimer": "Technical levels from price data, not signals to buy or sell.",
        },
    }
    if notes:
        feed["notes"] = notes
    return feed


def main() -> None:
    cfg = load_config()
    feed = build(cfg)
    jsonschema.validate(feed, load_schema())
    out = ROOT / "out"
    (out / "history").mkdir(parents=True, exist_ok=True)
    payload = json.dumps(feed, indent=2)
    (out / "auto_ta.json").write_text(payload, encoding="utf-8")
    (out / "history" / f"{feed['data']['as_of']}.json").write_text(payload, encoding="utf-8")
    print(f"[auto_ta] status={feed['status']} tickers={feed['data']['count']}")


if __name__ == "__main__":
    main()
