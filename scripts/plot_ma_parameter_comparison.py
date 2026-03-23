from __future__ import annotations

from pathlib import Path
import sys

import matplotlib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


OUTPUT_DIR = PROJECT_ROOT / "output"
COMPARISON_CSV = OUTPUT_DIR / "ma_parameter_comparison.csv"
NET_RETURN_HEATMAP = OUTPUT_DIR / "ma_net_return_heatmap.png"
SHARPE_HEATMAP = OUTPUT_DIR / "ma_sharpe_heatmap.png"
TOP10_SCORE_PLOT = OUTPUT_DIR / "ma_top10_score.png"
TOP10_NET_RETURN_PLOT = OUTPUT_DIR / "ma_top10_net_return.png"


matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt


def _plot_heatmap(df: pd.DataFrame, value_column: str, title: str, output_path: Path) -> None:
    pivot_df = df.pivot(index="short_window", columns="long_window", values=value_column).sort_index().sort_index(axis=1)

    fig, ax = plt.subplots(figsize=(8, 5))
    image = ax.imshow(pivot_df.values, cmap="YlGnBu", aspect="auto")
    ax.set_title(title)
    ax.set_xlabel("Long Window")
    ax.set_ylabel("Short Window")
    ax.set_xticks(range(len(pivot_df.columns)))
    ax.set_xticklabels(pivot_df.columns)
    ax.set_yticks(range(len(pivot_df.index)))
    ax.set_yticklabels(pivot_df.index)

    for row_idx, short_window in enumerate(pivot_df.index):
        for col_idx, long_window in enumerate(pivot_df.columns):
            value = pivot_df.loc[short_window, long_window]
            if pd.notna(value):
                ax.text(col_idx, row_idx, f"{value:.2f}", ha="center", va="center", color="black", fontsize=9)

    fig.colorbar(image, ax=ax, shrink=0.9)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_top_10_bars(
    df: pd.DataFrame,
    value_column: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    top_10 = df.sort_values(by=[value_column, "sharpe_ratio", "net_total_return"], ascending=[False, False, False]).head(10)
    labels = [f"{int(row.short_window)}/{int(row.long_window)}" for row in top_10.itertuples()]

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(labels, top_10[value_column], color="tab:blue")
    ax.set_title(title)
    ax.set_xlabel("Short / Long Window")
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, axis="y", alpha=0.3)

    for bar, value in zip(bars, top_10[value_column]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    comparison_df = pd.read_csv(COMPARISON_CSV)

    _plot_heatmap(
        comparison_df,
        value_column="net_total_return",
        title="MA Net Total Return Heatmap",
        output_path=NET_RETURN_HEATMAP,
    )
    _plot_heatmap(
        comparison_df,
        value_column="sharpe_ratio",
        title="MA Sharpe Ratio Heatmap",
        output_path=SHARPE_HEATMAP,
    )
    _plot_top_10_bars(
        comparison_df,
        value_column="score",
        title="Top 10 MA Parameter Combinations by Score",
        ylabel="Score",
        output_path=TOP10_SCORE_PLOT,
    )
    _plot_top_10_bars(
        comparison_df,
        value_column="net_total_return",
        title="Top 10 MA Parameter Combinations by Net Total Return",
        ylabel="Net Total Return",
        output_path=TOP10_NET_RETURN_PLOT,
    )

    print(f"Saved: {NET_RETURN_HEATMAP}")
    print(f"Saved: {SHARPE_HEATMAP}")
    print(f"Saved: {TOP10_SCORE_PLOT}")
    print(f"Saved: {TOP10_NET_RETURN_PLOT}")


if __name__ == "__main__":
    main()
