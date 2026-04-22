import asyncio
from backtesting.run_real_backtest import run_real_backtest
from backtesting.metrics import evaluate

assets = ["BTC", "ETH", "SOL"]

sim = asyncio.run(run_real_backtest(assets, days=365))
results = evaluate(sim)

print(results)