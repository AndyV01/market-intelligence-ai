def evaluate(simulator):
    import numpy as np

    equity = simulator.equity
    returns = simulator.returns

    def sharpe():
        if np.std(returns) == 0:
            return 0
        return np.sqrt(252) * np.mean(returns) / np.std(returns)

    def drawdown():
        peak = equity[0]
        max_dd = 0

        for v in equity:
            if v > peak:
                peak = v
            dd = (peak - v) / peak
            max_dd = max(max_dd, dd)

        return max_dd

    return {
        "final_capital": round(equity[-1], 2),
        "total_return": round((equity[-1] / equity[0] - 1), 3),
        "sharpe": round(sharpe(), 3),
        "max_drawdown": round(drawdown(), 3),
        "trades": len(returns),
    }