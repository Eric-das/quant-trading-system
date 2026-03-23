from __future__ import annotations

import pandas as pd


SUSPICIOUS_NVDA_DATES = {"2026-03-18", "2026-03-19"}


def clean_price_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a minimally cleaned price DataFrame for strategy usage.

    Raw database rows are left untouched. The temporary cleanup rule removes
    known-bad NVDA CSV rows for 2026-03-18 and 2026-03-19.
    """
    cleaned = df.copy()

    if "timestamp" in cleaned.columns:
        cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp"], utc=True)

    removal_mask = (
        cleaned["source"].eq("csv")
        & cleaned["symbol"].eq("NVDA")
        & cleaned["timestamp"].dt.strftime("%Y-%m-%d").isin(SUSPICIOUS_NVDA_DATES)
    )

    original_count = len(cleaned)
    cleaned = cleaned.loc[~removal_mask].copy()

    if "close" in cleaned.columns and cleaned["close"].isna().any():
        cleaned["close"] = cleaned["close"].ffill()

    cleaned = cleaned.sort_values("timestamp").reset_index(drop=True)

    removed_count = original_count - len(cleaned)
    print(f"[clean_data] original row count: {original_count}")
    print(f"[clean_data] cleaned row count: {len(cleaned)}")
    print(f"[clean_data] rows removed: {removed_count}")

    return cleaned

