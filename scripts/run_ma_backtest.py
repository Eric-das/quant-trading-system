from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backtest.ma_backtest import (
    DEFAULT_TRANSACTION_COST_RATE,
    evaluate_strategy,
    format_strategy_evaluation_report,
    run_backtest,
    save_backtest_outputs,
)
from services.data_loader import load_price_data
from strategy_engine.ma_cross import generate_signal


OUTPUT_DIR = PROJECT_ROOT / "output"
TRANSACTION_COST_RATE = DEFAULT_TRANSACTION_COST_RATE
SHORT_WINDOWS = (5, 10, 20)
LONG_WINDOWS = (20, 50, 100, 200)
RATING_ORDER = {"EXCELLENT": 3, "GOOD": 2, "OK": 1, "BAD": 0}


def run_parameter_comparison(
    df: pd.DataFrame,
    output_dir: Path,
    transaction_cost_rate: float,
) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []

    for short_window in SHORT_WINDOWS:
        for long_window in LONG_WINDOWS:
            if short_window >= long_window:
                continue

            signal_df = generate_signal(
                df,
                short_window=short_window,
                long_window=long_window,
            )
            backtest_df, metrics = run_backtest(
                signal_df,
                transaction_cost_rate=transaction_cost_rate,
            )
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
    comparison_df.to_csv(output_dir / "ma_parameter_comparison.csv", index=False)
    return comparison_df


def _format_top_10_table(comparison_df: pd.DataFrame) -> str:
    top_10 = comparison_df.head(10).copy()
    display_df = top_10.assign(
        gross_total_return=top_10["gross_total_return"].map(lambda value: f"{value:.2%}"),
        net_total_return=top_10["net_total_return"].map(lambda value: f"{value:.2%}"),
        max_drawdown=top_10["max_drawdown"].map(lambda value: f"{value:.2%}"),
        sharpe_ratio=top_10["sharpe_ratio"].map(lambda value: f"{value:.4f}"),
        win_rate=top_10["win_rate"].map(lambda value: f"{value:.2%}"),
        return_drawdown_ratio=top_10["return_drawdown_ratio"].map(lambda value: f"{value:.4f}"),
        stability=top_10["stability"].map(lambda value: f"{value:.6f}"),
    )
    columns = [
        "short_window",
        "long_window",
        "rating",
        "score",
        "sharpe_ratio",
        "net_total_return",
        "gross_total_return",
        "max_drawdown",
        "trade_count",
        "win_rate",
        "return_drawdown_ratio",
        "stability",
    ]
    return display_df.loc[:, columns].to_string(index=False)


def main() -> None:
    df = load_price_data("NVDA")

    signal_df = generate_signal(df)
    backtest_df, metrics = run_backtest(
        signal_df,
        transaction_cost_rate=TRANSACTION_COST_RATE,
    )
    output_dir, _ = save_backtest_outputs(
        backtest_df,
        OUTPUT_DIR,
        transaction_cost_rate=TRANSACTION_COST_RATE,
    )
    evaluation = evaluate_strategy(metrics, backtest_df)
    report_text = format_strategy_evaluation_report(evaluation, output_dir)
    (output_dir / "report.txt").write_text(report_text + "\n", encoding="utf-8")

    comparison_df = run_parameter_comparison(
        df,
        output_dir,
        transaction_cost_rate=TRANSACTION_COST_RATE,
    )

    print()
    print(report_text)
    print()
    print("Top 10 MA Parameter Combinations")
    print("=" * 120)
    print(_format_top_10_table(comparison_df))
    print("=" * 120)
    print(f"Comparison CSV           : {output_dir / 'ma_parameter_comparison.csv'}")


if __name__ == "__main__":
    main()
