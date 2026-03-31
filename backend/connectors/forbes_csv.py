from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

LOCAL_CSV = Path(__file__).parent.parent / "data" / "fortune500.csv"


class ForbesConnector:
    """Reads Fortune 500 CSV. Tries local file first, falls back to remote."""

    source_name = "forbes"
    URL = "https://raw.githubusercontent.com/cmusam/fortune500/master/csv/fortune500-2023.csv"

    async def fetch_all(self) -> list[dict]:
        loop = asyncio.get_event_loop()
        records = await loop.run_in_executor(None, self._read_csv)
        return records

    def _read_csv(self) -> list[dict]:
        # Try local first
        if LOCAL_CSV.exists():
            logger.info("Reading Fortune 500 from local CSV: %s", LOCAL_CSV)
            df = pd.read_csv(LOCAL_CSV)
        else:
            try:
                logger.info("Fetching Fortune 500 from remote: %s", self.URL)
                df = pd.read_csv(self.URL)
            except Exception:
                logger.warning("Forbes CSV not available locally or remotely")
                return []

        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        return df.to_dict(orient="records")
