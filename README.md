# auto_ta

Independent ArkenLabs satellite service. Computes **technical levels** from price data for a watchlist:
trend (via 20/50/200 SMAs), support/resistance, classic pivot points, Fibonacci retracement, and RSI.
Publishes one JSON feed the Arken research page consumes.

**Honest scope:** levels and context only — never "buy" / "sell". The old idea of *recognizing a chart
on screen* was dropped: unreliable and unnecessary, since we compute directly from the price series.

## Run locally
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python src/build_feed.py       # writes out/auto_ta.json + history
python scripts/post_text.py    # writes out/post.txt
```

## Configure
`config.yaml`: `tickers` watchlist, `sma_windows`, `sr_window` (support/resistance lookback),
`swing_window` (for Fibonacci), `rsi_window`.

## Deploy
`.github/workflows/publish.yml` runs weekday cron, builds, publishes `out/` to GitHub Pages:
`https://<user>.github.io/auto_ta/auto_ta.json`. No secrets required.

## Independence
Knows nothing about Arken. Arken knows only the feed URL + the shared schema.
