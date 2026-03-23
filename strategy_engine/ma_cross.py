from __future__ import annotations

import pandas as pd


def generate_signal(
    df: pd.DataFrame,
    short_window: int = 5,
    long_window: int = 20,
) -> pd.DataFrame:
    """
    Compute a simple moving average crossover signal from cleaned price data.
    """
    result = df.copy().sort_values("timestamp").reset_index(drop=True)
    result["ma_short"] = result["close"].rolling(window=short_window, min_periods=short_window).mean()
    result["ma_long"] = result["close"].rolling(window=long_window, min_periods=long_window).mean()
    result["signal"] = -1
    result.loc[result["ma_short"] > result["ma_long"], "signal"] = 1
    return result
