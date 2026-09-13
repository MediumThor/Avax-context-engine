from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterator

import httpx

from packages.context_engine.models import Candle


class BinanceVisionClient:
    """Read-only Binance public market-data client using data-api.binance.vision."""

    base_url = "https://data-api.binance.vision"

    def __init__(self, timeout: float = 30.0) -> None:
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout, headers={"User-Agent":"avax-context-engine/0.1"})

    def close(self) -> None:
        self._client.close()

    def fetch_last_price(self, symbol: str) -> float:
        """Last trade price. Display only — not a closed candle and not a forecast input."""
        response = self._client.get("/api/v3/ticker/price", params={"symbol": symbol})
        response.raise_for_status()
        payload = response.json()
        return float(payload["price"])

    def fetch_klines(self, symbol: str, interval: str, start_ms: int, end_ms: int, limit: int = 1000) -> list[Candle]:
        rows: list[Candle] = []
        cursor = int(start_ms)
        while cursor <= end_ms:
            response = self._client.get("/api/v3/klines", params={"symbol":symbol,"interval":interval,"startTime":cursor,"endTime":end_ms,"limit":min(limit,1000)})
            response.raise_for_status()
            payload = response.json()
            if not payload:
                break
            for row in payload:
                open_ms = int(row[0]); close_ms = int(row[6])
                if open_ms > end_ms:
                    break
                rows.append(Candle(symbol=symbol,timeframe=interval,open_time=datetime.fromtimestamp(open_ms/1000,tz=timezone.utc),open=float(row[1]),high=float(row[2]),low=float(row[3]),close=float(row[4]),volume=float(row[5]),is_closed=close_ms <= end_ms))
            next_cursor = int(payload[-1][0]) + 1
            if next_cursor <= cursor:
                raise RuntimeError("Kline pagination did not advance")
            cursor = next_cursor
            if len(payload) < min(limit,1000):
                break
        return rows

    def iter_recent_days(self, symbol: str, interval: str, days: int, end: datetime | None = None) -> Iterator[Candle]:
        if days <= 0:
            raise ValueError("days must be positive")
        end_dt = (end or datetime.now(timezone.utc)).astimezone(timezone.utc)
        start_dt = end_dt.timestamp() - days * 86400
        for candle in self.fetch_klines(symbol, interval, int(start_dt*1000), int(end_dt.timestamp()*1000)):
            if candle.is_closed:
                yield candle
