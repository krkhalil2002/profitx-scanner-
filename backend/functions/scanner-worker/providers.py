"""Market data providers. Each returns a normalized dict:
{symbol, open, prev_close, volume, avg_volume, float}

DATA_PROVIDER=mock  -> deterministic fake data (free, no API key; good for dev/demo)
DATA_PROVIDER=fmp   -> Financial Modeling Prep (key read from Secrets Manager)
"""
import json
import os
import random
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen

import boto3


class MockProvider:
    """Same symbol + same day => same numbers, so results are reproducible."""

    def fetch(self, symbol):
        r = random.Random(f"{symbol}-{date.today().isoformat()}")
        prev_close = round(r.uniform(2, 50), 2)
        gap = r.uniform(0, 12)
        return {
            "symbol": symbol,
            "open": round(prev_close * (1 + gap / 100), 2),
            "prev_close": prev_close,
            "volume": r.randint(300_000, 3_000_000),
            "avg_volume": r.randint(200_000, 1_000_000),
            "float": r.randint(5_000_000, 120_000_000),
        }


class FMPProvider:
    # NOTE: verify endpoint paths and field names against the current FMP docs
    # before relying on this. Only this class needs to change if they differ.
    BASE = "https://financialmodelingprep.com/stable"

    def __init__(self, secret_arn):
        self._secret_arn = secret_arn
        self._key = None  # cached across warm invocations

    def _api_key(self):
        if self._key is None:
            sm = boto3.client("secretsmanager")
            self._key = sm.get_secret_value(SecretId=self._secret_arn)["SecretString"].strip()
        return self._key

    def _get(self, path, symbol):
        query = urlencode({"symbol": symbol, "apikey": self._api_key()})
        with urlopen(f"{self.BASE}/{path}?{query}", timeout=8) as resp:
            data = json.loads(resp.read())
        return data[0] if data else {}

    def fetch(self, symbol):
        quote = self._get("quote", symbol)
        shares = self._get("shares-float", symbol)
        return {
            "symbol": symbol,
            "open": quote.get("open"),
            "prev_close": quote.get("previousClose"),
            "volume": quote.get("volume"),
            "avg_volume": quote.get("avgVolume"),
            "float": shares.get("floatShares"),
        }


def get_provider():
    name = os.environ.get("DATA_PROVIDER", "mock")
    if name == "mock":
        return MockProvider()
    if name == "fmp":
        return FMPProvider(os.environ["SECRET_ARN"])
    raise ValueError(f"Unknown DATA_PROVIDER: {name}")
