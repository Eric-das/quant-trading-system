from __future__ import annotations

import math
from pathlib import Path

import matplotlib
import pandas as pd


DEFAULT_TRANSACTION_COST_RATE = 0.001


def run_backtest(
    signal_df: pd.DataFrame,
    transaction_cost_rate: float = DEFAULT_TRANSACTION_COST_RATE,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """
    Run a minimal long-flat backtest from a signal DataFrame.
    """
    result = signal_df.copy().sort_values("timestamp").reset_index(drop=True)
    result["daily_return"] = result["close"].pct_change().fillna(0.0)
    result["position"] = result["signal"].shift(1).fillna(0)
    result["position"] = result["position"].clip(lower=0)
    result["gross_strategy_return"] = result["daily_return"] * result["position"]
    result["position_change"] = result["position"].diff().fillna(result["position"])
    result["transaction_cost"] = result["position_change"].abs() * transaction_cost_rate
    result["net_strategy_return"] = result["gross_strategy_return"] - result["transaction_cost"]

    result["strategy_return"] = result["net_strategy_return"]
    result["cumulative_market_return"] = (1 + result["daily_return"]).cumprod() - 1
    result["gross_cumulative_strategy_return"] = (1 + result["gross_strategy_return"]).cumprod() - 1
    result["cumulative_strategy_return"] = (1 + result["net_strategy_return"]).cumprod() - 1
    result["gross_equity"] = (1 + result["gross_strategy_return"]).cumprod()
    result["net_equity"] = (1 + result["net_strategy_return"]).cumprod()
    result["equity"] = result["net_equity"]

    running_peak = result["net_equity"].cummax()
    drawdown = result["net_equity"] / running_peak - 1

    strategy_std = result["net_strategy_return"].std()
    sharpe_ratio = 0.0
    if strategy_std and not math.isnan(strategy_std):
        sharpe_ratio = (result["net_strategy_return"].mean() / strategy_std) * math.sqrt(252)

    trades_df = extract_trades(result, transaction_cost_rate=transaction_cost_rate)
    trade_count = int(len(trades_df))
    win_rate = 0.0
    average_cost_per_trade = 0.0
    if trade_count:
        win_rate = float((trades_df["net_trade_return"] > 0).mean())
        average_cost_per_trade = float(trades_df["total_trade_cost"].mean())

    gross_total_return = float(result["gross_cumulative_strategy_return"].iloc[-1])
    net_total_return = float(result["cumulative_strategy_return"].iloc[-1])
    total_transaction_cost = float(result["transaction_cost"].sum())
    cost_as_pct_of_gross_return = 0.0
    if gross_total_return != 0:
        cost_as_pct_of_gross_return = float(total_transaction_cost / gross_total_return)

    metrics = {
        "transaction_cost_rate": float(transaction_cost_rate),
        "total_market_return": float(result["cumulative_market_return"].iloc[-1]),
        "gross_total_return": gross_total_return,
        "net_total_return": net_total_return,
        "total_strategy_return": net_total_return,
        "total_transaction_cost": total_transaction_cost,
        "average_cost_per_trade": average_cost_per_trade,
        "cost_as_pct_of_gross_return": cost_as_pct_of_gross_return,
        "max_drawdown": float(drawdown.min()),
        "sharpe_ratio": float(sharpe_ratio),
        "trade_count": float(trade_count),
        "win_rate": float(win_rate),
    }

    return result, metrics


def extract_trades(
    backtest_df: pd.DataFrame,
    transaction_cost_rate: float = DEFAULT_TRANSACTION_COST_RATE,
) -> pd.DataFrame:
    """
    Extract completed long trades from a backtest result DataFrame.
    """
    result = backtest_df.copy().sort_values("timestamp").reset_index(drop=True)
    trades: list[dict[str, object]] = []
    entry_row: pd.Series | None = None

    for _, row in result.iterrows():
        position_change = float(row["position_change"])

        if entry_row is None and position_change > 0:
            entry_row = row
            continue

        if entry_row is not None and position_change < 0:
            exit_row = row
            entry_price = float(entry_row["close"])
            exit_price = float(exit_row["close"])
            gross_trade_return = float((exit_price / entry_price) - 1)
            total_trade_cost = float(transaction_cost_rate * 2)
            trades.append(
                {
                    "entry_timestamp": entry_row["timestamp"],
                    "exit_timestamp": exit_row["timestamp"],
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "gross_trade_return": gross_trade_return,
                    "total_trade_cost": total_trade_cost,
                    "net_trade_return": float(gross_trade_return - total_trade_cost),
                    "holding_days": int(
                        (pd.to_datetime(exit_row["timestamp"]) - pd.to_datetime(entry_row["timestamp"])).days
                    ),
                }
            )
            entry_row = None

    return pd.DataFrame(
        trades,
        columns=[
            "entry_timestamp",
            "exit_timestamp",
            "entry_price",
            "exit_price",
            "gross_trade_return",
            "total_trade_cost",
            "net_trade_return",
            "holding_days",
        ],
    )


def evaluate_strategy(metrics: dict[str, float], result_df: pd.DataFrame) -> dict[str, float | str]:
    """
    Evaluate strategy quality using net performance and a simple scoring model.
    """
    evaluation = dict(metrics)
    max_drawdown = float(evaluation["max_drawdown"])
    net_total_return = float(evaluation["net_total_return"])
    drawdown_abs = abs(max_drawdown)
    return_drawdown_ratio = 0.0
    if drawdown_abs > 0:
        return_drawdown_ratio = net_total_return / drawdown_abs

    stability = float(result_df["net_strategy_return"].std())
    score = 0

    sharpe_ratio = float(evaluation["sharpe_ratio"])
    if sharpe_ratio > 2:
        score += 3
    elif sharpe_ratio > 1:
        score += 2
    elif sharpe_ratio > 0.5:
        score += 1

    if max_drawdown > -0.1:
        score += 2
    elif max_drawdown > -0.2:
        score += 1

    if return_drawdown_ratio > 2:
        score += 2
    elif return_drawdown_ratio > 1:
        score += 1

    trade_count = int(evaluation["trade_count"])
    if trade_count > 20:
        score += 1

    win_rate = float(evaluation["win_rate"])
    if win_rate > 0.6:
        score += 1

    if score >= 7:
        rating = "EXCELLENT"
    elif score >= 5:
        rating = "GOOD"
    elif score >= 3:
        rating = "OK"
    else:
        rating = "BAD"

    evaluation["return_drawdown_ratio"] = float(return_drawdown_ratio)
    evaluation["stability"] = stability
    evaluation["score"] = float(score)
    evaluation["rating"] = rating
    return evaluation


def format_strategy_evaluation_report(evaluation: dict[str, float | str], output_dir: Path) -> str:
    """
    Build a readable terminal/file report for strategy evaluation.
    """
    lines = [
        "=" * 64,
        "Strategy Evaluation Report",
        "=" * 64,
        f"Transaction cost rate    : {float(evaluation['transaction_cost_rate']):.2%} per side",
        f"Total market return      : {float(evaluation['total_market_return']):.2%}",
        f"Gross total return       : {float(evaluation['gross_total_return']):.2%}",
        f"Net total return         : {float(evaluation['net_total_return']):.2%}",
        f"Total transaction cost   : {float(evaluation['total_transaction_cost']):.4f}",
        f"Average cost per trade   : {float(evaluation['average_cost_per_trade']):.4f}",
        f"Max drawdown             : {float(evaluation['max_drawdown']):.2%}",
        f"Sharpe ratio             : {float(evaluation['sharpe_ratio']):.4f}",
        f"Trade count              : {int(float(evaluation['trade_count']))}",
        f"Win rate                 : {float(evaluation['win_rate']):.2%}",
        f"Return / drawdown ratio  : {float(evaluation['return_drawdown_ratio']):.4f}",
        f"Stability                : {float(evaluation['stability']):.6f}",
        "-" * 64,
        f"Score                    : {int(float(evaluation['score']))}",
        f"Rating                   : {str(evaluation['rating'])}",
        "-" * 64,
        f"equity_curve.csv         : {output_dir / 'equity_curve.csv'}",
        f"trades.csv               : {output_dir / 'trades.csv'}",
        f"equity_curve.png         : {output_dir / 'equity_curve.png'}",
        f"price_signals.png        : {output_dir / 'price_signals.png'}",
        f"report.txt               : {output_dir / 'report.txt'}",
        "=" * 64,
    ]
    return "\n".join(lines)


def _save_equity_curve_plot(backtest_df: pd.DataFrame, output_dir: Path) -> Path:
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    plot_path = output_dir / "equity_curve.png"
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(backtest_df["timestamp"], backtest_df["gross_equity"], label="Gross Equity", color="tab:blue")
    ax.plot(backtest_df["timestamp"], backtest_df["net_equity"], label="Net Equity", color="tab:orange")
    ax.set_title("Strategy Equity Curve")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Equity")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return plot_path


def _save_price_signals_plot(backtest_df: pd.DataFrame, output_dir: Path) -> Path:
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    plot_path = output_dir / "price_signals.png"
    buy_points = backtest_df[backtest_df["position_change"] > 0]
    sell_points = backtest_df[backtest_df["position_change"] < 0]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(backtest_df["timestamp"], backtest_df["close"], label="Close Price", color="tab:gray")
    ax.scatter(
        buy_points["timestamp"],
        buy_points["close"],
        label="Buy",
        marker="^",
        color="tab:green",
        s=60,
    )
    ax.scatter(
        sell_points["timestamp"],
        sell_points["close"],
        label="Sell",
        marker="v",
        color="tab:red",
        s=60,
    )
    ax.set_title("Price With Buy/Sell Signals")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Price")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return plot_path


def save_backtest_outputs(
    backtest_df: pd.DataFrame,
    output_dir: str | Path = "output",
    transaction_cost_rate: float = DEFAULT_TRANSACTION_COST_RATE,
) -> tuple[Path, pd.DataFrame]:
    """
    Save CSV and PNG outputs for a completed backtest.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    trades_df = extract_trades(backtest_df, transaction_cost_rate=transaction_cost_rate)
    backtest_df.to_csv(output_path / "equity_curve.csv", index=False)
    trades_df.to_csv(output_path / "trades.csv", index=False)
    _save_equity_curve_plot(backtest_df, output_path)
    _save_price_signals_plot(backtest_df, output_path)

    return output_path, trades_df
