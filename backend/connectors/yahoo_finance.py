from __future__ import annotations

import asyncio

import redis.asyncio as aioredis
import yfinance as yf

from connectors.base import BaseConnector


class YahooFinanceConnector(BaseConnector):
    source_name = "yahoo_finance"

    async def fetch_ticker(self, ticker: str) -> dict:
        """Fetch ticker info. yfinance is synchronous, so we offload to a thread."""
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: yf.Ticker(ticker).info)
        return info
