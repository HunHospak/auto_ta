import datetime as dt
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import build_feed
import providers


class PriceProviderTests(unittest.TestCase):
    @staticmethod
    def bars(end):
        return pd.DataFrame(
            {"Close": [100.0] * 40, "High": [101.0] * 40, "Low": [99.0] * 40},
            index=pd.bdate_range(end=end, periods=40),
        )

    def test_one_ticker_supports_flat_and_grouped_bars(self):
        bars = self.bars("2026-11-20").iloc[::-1]
        grouped = pd.concat({"SPY": bars}, axis=1)
        for sample in (bars, grouped):
            with self.subTest(columns=sample.columns), patch.object(providers.yf, "download", return_value=sample):
                result = providers.get_ohlc(["SPY"])
                self.assertEqual(result["SPY"]["prev_c"], 100.0)
                self.assertEqual(result["SPY"]["as_of"], "2026-11-20")

    def test_provider_exception_yields_unavailable_feed(self):
        config = {"tickers": ["SPY"], "service": "auto_ta", "schema_version": "1.0", "ttl_hours": 30}
        with patch.object(providers.yf, "download", side_effect=OSError("upstream unavailable")):
            feed = build_feed.build(config)
        self.assertEqual(feed["status"], "unavailable")
        self.assertEqual(feed["data"]["count"], 0)
        self.assertTrue(feed["notes"])

    def test_flat_batch_is_not_attributed_to_multiple_tickers(self):
        bars = self.bars("2026-11-20")
        with patch.object(providers.yf, "download", return_value=bars):
            self.assertEqual(providers.get_ohlc(["SPY", "QQQ"]), {})

    def test_feed_keeps_the_actual_market_date_and_flags_mixed_snapshot(self):
        cfg = {**build_feed.load_config(), "tickers": ["SPY", "QQQ", "IWM"]}
        bars = pd.concat({
            "SPY": self.bars("2026-11-20"), "QQQ": self.bars("2026-11-19"), "IWM": self.bars("2026-11-24"),
        }, axis=1)
        with patch.object(providers.yf, "download", return_value=bars):
            feed = build_feed.build(cfg, generated_at=dt.datetime(2026, 11, 23, tzinfo=dt.timezone.utc))
        self.assertEqual(feed["status"], "partial")
        self.assertEqual(feed["data"]["as_of"], "2026-11-20")
        self.assertEqual([(row["ticker"], row["as_of"]) for row in feed["data"]["tickers"]], [("SPY", "2026-11-20")])

    def test_stale_ohlc_cannot_publish_fresh_technical_levels(self):
        cfg = {**build_feed.load_config(), "tickers": ["SPY"]}
        with patch.object(providers.yf, "download", return_value=self.bars("2026-11-17")):
            feed = build_feed.build(cfg, generated_at=dt.datetime(2026, 11, 23, tzinfo=dt.timezone.utc))
        self.assertEqual(feed["status"], "unavailable")
        self.assertIsNone(feed["data"]["as_of"])
