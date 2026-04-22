import numpy as np


class BacktestEngine:
    def __init__(self, initial_capital=1000):
        self.initial_capital = initial_capital
        self.equity = [initial_capital]
        self.returns = []

    def step(self, weights: dict, returns: dict):
        """
        weights: {"BTC": 0.4, "ETH": 0.6}
        returns: {"BTC": 0.01, "ETH": -0.005}
        """

        portfolio_return = 0

        for asset, w in weights.items():
            r = returns.get(asset, 0)
            portfolio_return += w * r

        new_equity = self.equity[-1] * (1 + portfolio_return)

        self.equity.append(new_equity)
        self.returns.append(portfolio_return)

    def get_equity_curve(self):
        return self.equity

    def get_returns(self):
        return self.returns