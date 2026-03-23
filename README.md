# 📈 Quant Trading System

A systematic trading framework built with Python.

---

## 🚀 Features

- Data pipeline (yfinance → PostgreSQL)
- Strategy engine (MA crossover)
- Backtesting system
- Performance analysis

---

## 📊 Strategy

Moving Average Crossover

- Buy when short MA > long MA
- Sell when short MA < long MA

---

## 🔧 How to Run

```bash
python scripts/run_ma_backtest.py