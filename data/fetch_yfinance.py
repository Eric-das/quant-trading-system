from __future__ import annotations

import pandas as pd

try:
    import yfinance as yf
except ImportError as exc:  # pragma: no cover - import guard for easier debugging
    raise ImportError(
        "yfinance is required for Yahoo Finance ingestion. "
        "Install dependencies from requirements.txt."
    ) from exc


STANDARD_COLUMNS = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]


def _debug_frame(step: str, symbol: str, period: str, interval: str, frame: pd.DataFrame) -> None:
    """Print a compact view of what Yahoo returned for easier debugging."""
    print(f"[yfinance] step={step}")
    print(f"[yfinance] symbol={symbol} period={period} interval={interval}")
    print(f"[yfinance] shape={frame.shape}")
    print(f"[yfinance] columns={list(frame.columns)}")


def fetch_price_data(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Download OHLCV price data from Yahoo Finance and return a cleaned DataFrame.

    The returned frame uses lowercase standardized column names so the load
    script can map rows into the ORM model with very little ceremony.
    """
    print(f"[yfinance] fetch requested for symbol={symbol} period={period} interval={interval}")

    try:
        frame = yf.download(
            tickers=symbol,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False,
            threads=False,
        )
        _debug_frame("download", symbol, period, interval, frame)
    except Exception as exc:
        print(f"[yfinance] download failed: {exc!r}")
        frame = pd.DataFrame()
        _debug_frame("download_failed", symbol, period, interval, frame)

    # Some environments behave better with the Ticker.history path, so use it
    # as a quiet fallback when download() returns nothing useful.
    if frame.empty:
        print("[yfinance] download returned no rows, trying Ticker.history fallback")
        try:
            frame = yf.Ticker(symbol).history(
                period=period,
                interval=interval,
                auto_adjust=False,
            )
            _debug_frame("history", symbol, period, interval, frame)
        except Exception as exc:
            print(f"[yfinance] history failed: {exc!r}")
            frame = pd.DataFrame()
            _debug_frame("history_failed", symbol, period, interval, frame)

    if frame.empty:
        print(f"[yfinance] no data available for symbol={symbol}")
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    # Recent yfinance versions may return MultiIndex columns even for one ticker.
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)

    frame = frame.reset_index()
    timestamp_column = "Datetime" if "Datetime" in frame.columns else "Date"

    frame = frame.rename(
        columns={
            timestamp_column: "timestamp",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )

    required_columns = {"timestamp", "open", "high", "low", "close", "volume"}
    missing_columns = sorted(required_columns - set(frame.columns))
    if missing_columns:
        print(f"[yfinance] missing expected columns after normalization: {missing_columns}")
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    cleaned = frame[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    cleaned["symbol"] = symbol.upper()
    cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp"], utc=True)
    cleaned["volume"] = cleaned["volume"].fillna(0)

    # Keep only rows with a full OHLC payload to avoid partial inserts.
    cleaned = cleaned.dropna(subset=["timestamp", "open", "high", "low", "close"])
    cleaned = cleaned[STANDARD_COLUMNS].sort_values("timestamp").reset_index(drop=True)
    _debug_frame("cleaned", symbol.upper(), period, interval, cleaned)

    return cleaned
