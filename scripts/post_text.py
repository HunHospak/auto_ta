"""Generate a ready-to-post social snippet from the latest feed."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARROW = {"uptrend": "▲", "downtrend": "▼", "sideways": "•", "unknown": "?"}


def main() -> None:
    feed = json.loads((ROOT / "out" / "auto_ta.json").read_text(encoding="utf-8"))
    d = feed["data"]
    lines = [f"Technical levels — {d['as_of']}"]
    for r in d["tickers"][:6]:
        lines.append(
            f"{ARROW.get(r['trend'], '')} ${r['ticker']} {r['last']}  "
            f"S {r.get('support')} / R {r.get('resistance')}  RSI {r.get('rsi')}"
        )
    lines.append("Levels, not signals · not investment advice · arkenlabs.eu")
    text = "\n".join(lines)
    (ROOT / "out" / "post.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
