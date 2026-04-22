import numpy as np
import asyncio
from typing import Dict, List
from services.binance import get_ohlc_data


# ─────────────────────────────────────────────
# 1. PREPARAR DATOS REALES
# ─────────────────────────────────────────────

async def load_historical_prices(assets: List[str], days=90):
    data = {}

    for asset in assets:
        try:
            ohlc = await get_ohlc_data(asset, days=days)

            closes = [candle[4] for candle in ohlc]
            data[asset] = closes
            
            await asyncio.sleep(1)

        except Exception as e:
            print(f"[OHLC ERROR] {asset}: {e}")
            data[asset] = []

    return data


def compute_returns(price_series: Dict[str, List[float]]):
    returns = {}

    for asset, prices in price_series.items():
        asset_returns = []

        for i in range(1, len(prices)):
            r = (prices[i] - prices[i - 1]) / prices[i - 1]
            asset_returns.append(r)

        returns[asset] = asset_returns

    return returns

# ─────────────────────────────────────────────
# 2. SIMULADOR DE PORTFOLIO
# ─────────────────────────────────────────────

class PortfolioSimulator:
    def __init__(self, capital=1000):
        self.capital = capital
        self.equity = [capital]
        self.returns = []

    def step(self, weights: Dict[str, float], returns: Dict[str, float]):
      portfolio_return = 0

      for asset, w in weights.items():
        portfolio_return += w * returns.get(asset, 0)

       # 🧾 COSTO DE TRADING (0.1% por asset)
      fee = 0.001  # 0.1%
      trading_cost = fee * len(weights)

      portfolio_return -= trading_cost

      new_value = self.equity[-1] * (1 + portfolio_return)

      self.equity.append(new_value)
      self.returns.append(portfolio_return)