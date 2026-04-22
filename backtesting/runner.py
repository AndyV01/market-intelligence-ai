import random
from backtesting.engine import BacktestEngine
from backtesting.metrics import sharpe_ratio, max_drawdown, win_rate, total_return


def simulate_market(assets, days=60):
    """
    Simula retornos diarios (placeholder).
    Luego lo podés reemplazar por datos reales.
    """
    data = []

    for _ in range(days):
        daily = {}
        for a in assets:
            daily[a] = random.uniform(-0.03, 0.03)  # ±3%
        data.append(daily)

    return data


def run_backtest(opportunity_snapshots):
    """
    opportunity_snapshots:
    lista de estados del opportunity_agent en el tiempo
    """

    engine = BacktestEngine(initial_capital=1000)

    assets = list(opportunity_snapshots[0].keys())
    market_data = simulate_market(assets, days=len(opportunity_snapshots))

    for t, snapshot in enumerate(opportunity_snapshots):
        # pesos desde tu optimizer
        weights = {
            a: snapshot[a]["weight"]
            for a in snapshot
        }

        returns = market_data[t]

        engine.step(weights, returns)

    equity = engine.get_equity_curve()
    returns = engine.get_returns()

    return {
        "sharpe": round(sharpe_ratio(returns), 3),
        "max_drawdown": round(max_drawdown(equity), 3),
        "win_rate": round(win_rate(returns), 3),
        "total_return": round(total_return(equity), 3),
        "equity_curve": equity,
    }