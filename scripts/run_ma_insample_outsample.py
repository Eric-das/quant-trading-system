from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backtest.ma_backtest import (
    DEFAULT_TRANSACTION_COST_RATE,
    evaluate_strategy,
    extract_trades,
    run_backtest,
)
from services.data_loader import load_price_data
from strategy_engine.ma_cross import generate_signal


OUTPUT_DIR = PROJECT_ROOT / "output"
TRANSACTION_COST_RATE = DEFAULT_TRANSACTION_COST_RATE
SHORT_WINDOWS = (5, 10, 20)
LONG_WINDOWS = (20, 50, 100, 200)
RATING_ORDER = {"EXCELLENT": 3, "GOOD": 2, "OK": 1, "BAD": 0}


def split_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_index = int(len(df) * 0.7)
    insample_df = df.iloc[:split_index].copy().reset_index(drop=True)
    outsample_df = df.iloc[split_index:].copy().reset_index(drop=True)
    return insample_df, outsample_df


def run_parameter_study(df: pd.DataFrame, transaction_cost_rate: float) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []

    for short_window in SHORT_WINDOWS:
        for long_window in LONG_WINDOWS:
            if short_window >= long_window:
                continue

            signal_df = generate_signal(df, short_window=short_window, long_window=long_window)
            backtest_df, metrics = run_backtest(signal_df, transaction_cost_rate=transaction_cost_rate)
            evaluation = evaluate_strategy(metrics, backtest_df)
            rows.append(
                {
                    "short_window": short_window,
                    "long_window": long_window,
                    "gross_total_return": float(evaluation["gross_total_return"]),
                    "net_total_return": float(evaluation["net_total_return"]),
                    "max_drawdown": float(evaluation["max_drawdown"]),
                    "sharpe_ratio": float(evaluation["sharpe_ratio"]),
                    "trade_count": int(float(evaluation["trade_count"])),
                    "win_rate": float(evaluation["win_rate"]),
                    "return_drawdown_ratio": float(evaluation["return_drawdown_ratio"]),
                    "stability": float(evaluation["stability"]),
                    "score": int(float(evaluation["score"])),
                    "rating": str(evaluation["rating"]),
                }
            )

    comparison_df = pd.DataFrame(rows)
    comparison_df["rating_rank"] = comparison_df["rating"].map(RATING_ORDER).fillna(-1)
    comparison_df = comparison_df.sort_values(
        by=["rating_rank", "sharpe_ratio", "net_total_return"],
        ascending=[False, False, False],
    ).drop(columns=["rating_rank"])
    return comparison_df


def format_metrics_block(title: str, metrics: dict[str, float | str]) -> str:
    lines = [
        title,
        "-" * len(title),
        f"Gross total return      : {float(metrics['gross_total_return']):.2%}",
        f"Net total return        : {float(metrics['net_total_return']):.2%}",
        f"Max drawdown            : {float(metrics['max_drawdown']):.2%}",
        f"Sharpe ratio            : {float(metrics['sharpe_ratio']):.4f}",
        f"Trade count             : {int(float(metrics['trade_count']))}",
        f"Win rate                : {float(metrics['win_rate']):.2%}",
        f"Return / drawdown ratio : {float(metrics['return_drawdown_ratio']):.4f}",
        f"Stability               : {float(metrics['stability']):.6f}",
        f"Score                   : {int(float(metrics['score']))}",
        f"Rating                  : {str(metrics['rating'])}",
    ]
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_price_data("NVDA")
    insample_df, outsample_df = split_dataset(df)

    insample_comparison_df = run_parameter_study(
        insample_df,
        transaction_cost_rate=TRANSACTION_COST_RATE,
    )
    insample_csv_path = OUTPUT_DIR / "ma_insample_parameter_comparison.csv"
    insample_comparison_df.to_csv(insample_csv_path, index=False)

    best_row = insample_comparison_df.iloc[0]
    best_short_window = int(best_row["short_window"])
    best_long_window = int(best_row["long_window"])

    outsample_signal_df = generate_signal(
        outsample_df,
        short_window=best_short_window,
        long_window=best_long_window,
    )
    outsample_backtest_df, outsample_metrics = run_backtest(
        outsample_signal_df,
        transaction_cost_rate=TRANSACTION_COST_RATE,
    )
    outsample_evaluation = evaluate_strategy(outsample_metrics, outsample_backtest_df)
    outsample_trades_df = extract_trades(
        outsample_backtest_df,
        transaction_cost_rate=TRANSACTION_COST_RATE,
    )

    outsample_equity_path = OUTPUT_DIR / "ma_best_outsample_equity_curve.csv"
    outsample_trades_path = OUTPUT_DIR / "ma_best_outsample_trades.csv"
    outsample_json_path = OUTPUT_DIR / "ma_best_outsample_result.json"

    outsample_backtest_df.to_csv(outsample_equity_path, index=False)
    outsample_trades_df.to_csv(outsample_trades_path, index=False)
    outsample_payload = {
        "best_insample_parameters": {
            "short_window": best_short_window,
            "long_window": best_long_window,
        },
        "transaction_cost_rate": TRANSACTION_COST_RATE,
        "insample_summary": {
            key: (float(best_row[key]) if key not in {"rating"} else str(best_row[key]))
            for key in [
                "gross_total_return",
                "net_total_return",
                "max_drawdown",
                "sharpe_ratio",
                "trade_count",
                "win_rate",
                "return_drawdown_ratio",
                "stability",
                "score",
                "rating",
            ]
        },
        "outsample_summary": {
            key: (float(outsample_evaluation[key]) if key not in {"rating"} else str(outsample_evaluation[key]))
            for key in [
                "gross_total_return",
                "net_total_return",
                "max_drawdown",
                "sharpe_ratio",
                "trade_count",
                "win_rate",
                "return_drawdown_ratio",
                "stability",
                "score",
                "rating",
            ]
        },
    }
    outsample_json_path.write_text(json.dumps(outsample_payload, indent=2), encoding="utf-8")

    insample_summary = {
        "gross_total_return": float(best_row["gross_total_return"]),
        "net_total_return": float(best_row["net_total_return"]),
        "max_drawdown": float(best_row["max_drawdown"]),
        "sharpe_ratio": float(best_row["sharpe_ratio"]),
        "trade_count": int(best_row["trade_count"]),
        "win_rate": float(best_row["win_rate"]),
        "return_drawdown_ratio": float(best_row["return_drawdown_ratio"]),
        "stability": float(best_row["stability"]),
        "score": int(best_row["score"]),
        "rating": str(best_row["rating"]),
    }

    print()
    print("=" * 72)
    print("MA In-Sample / Out-of-Sample Validation")
    print("=" * 72)
    print(f"Best in-sample parameter pair : short_window={best_short_window}, long_window={best_long_window}")
    print(f"Transaction cost rate        : {TRANSACTION_COST_RATE:.2%} per side")
    print(f"In-sample rows               : {len(insample_df)}")
    print(f"Out-of-sample rows           : {len(outsample_df)}")
    print()
    print(format_metrics_block("In-Sample Metrics", insample_summary))
    print()
    print(format_metrics_block("Out-of-Sample Metrics", outsample_evaluation))
    print("-" * 72)
    print(f"In-sample comparison CSV     : {insample_csv_path}")
    print(f"Out-sample result JSON       : {outsample_json_path}")
    print(f"Out-sample equity CSV        : {outsample_equity_path}")
    print(f"Out-sample trades CSV        : {outsample_trades_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
