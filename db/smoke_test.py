from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from db import check_database_health, recreate_all_tables, session_scope
from db.models import PriceBar, Signal, TradeRecord
from db.repositories import MarketDataRepository, SignalRepository, TradeRecordRepository


def print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def run_db_smoke_test() -> None:
    print_section("Health Check")
    healthy, message = check_database_health()
    print(message)

    if not healthy:
        return

    print_section("Recreate Tables")
    recreate_all_tables()
    print("Project tables were recreated successfully.")

    sample_timestamp = datetime.now(timezone.utc)

    sample_price_bar = PriceBar(
        symbol="AAPL",
        timeframe="1d",
        timestamp=sample_timestamp,
        open=Decimal("210.100000"),
        high=Decimal("212.500000"),
        low=Decimal("209.750000"),
        close=Decimal("211.800000"),
        volume=Decimal("1250000.0000"),
        source="smoke_test",
    )
    sample_signal = Signal(
        symbol="AAPL",
        strategy_name="smoke_test_strategy",
        signal_type="buy",
        signal_strength=Decimal("0.8500"),
        timestamp=sample_timestamp,
        status="new",
        notes="Sample signal inserted by db smoke test.",
    )
    sample_trade_record = TradeRecord(
        symbol="AAPL",
        order_id=f"smoke-test-{int(sample_timestamp.timestamp())}",
        side="buy",
        quantity=Decimal("10.000000"),
        price=Decimal("211.800000"),
        status="filled",
        submitted_at=sample_timestamp,
        executed_at=sample_timestamp,
        broker="local_test",
        notes="Sample trade inserted by db smoke test.",
    )

    print_section("Insert Sample Rows")
    with session_scope() as session:
        market_data_repo = MarketDataRepository(session)
        signal_repo = SignalRepository(session)
        trade_record_repo = TradeRecordRepository(session)

        market_data_repo.save_price_bar(sample_price_bar)
        signal_repo.save_signal(sample_signal)
        trade_record_repo.save_trade_record(sample_trade_record)
        print("Inserted 1 PriceBar, 1 Signal, and 1 TradeRecord.")

    print_section("Query Recent Rows")
    with session_scope() as session:
        market_data_repo = MarketDataRepository(session)
        signal_repo = SignalRepository(session)
        trade_record_repo = TradeRecordRepository(session)

        recent_price_bars = market_data_repo.list_recent_prices(limit=1)
        recent_signals = signal_repo.list_recent_signals(limit=1)
        recent_trade_records = trade_record_repo.list_recent_trades(limit=1)

        print("Recent PriceBar:", recent_price_bars[0] if recent_price_bars else "None")
        print("Recent Signal:", recent_signals[0] if recent_signals else "None")
        print(
            "Recent TradeRecord:",
            recent_trade_records[0] if recent_trade_records else "None",
        )

    print_section("Success")
    print("Database smoke test completed successfully.")


if __name__ == "__main__":
    run_db_smoke_test()
