import asyncio
from typing import Dict

from backtesting.real_data_engine import (
    load_historical_prices,
    compute_returns,
    PortfolioSimulator
)

from utils.indicators import calculate_indicators
from agents.opportunity_agent import opportunity_agent
from agents.portfolio_optimizer_agent import portfolio_optimizer_agent


async def run_real_backtest(assets, days=60):

    print("[Backtest] Cargando datos históricos reales...")

    prices = await load_historical_prices(assets, days=days)
    returns = compute_returns(prices)

    simulator = PortfolioSimulator(capital=1000)

    steps = len(list(returns.values())[0])

    for t in range(steps):

        # ─────────────────────────────────────────
        # 1. ESTADO BASE
        # ─────────────────────────────────────────

        state = {
            "assets": assets,
            "budget_ars": simulator.equity[-1],
            "raw_prices": {},
            "raw_news": [],
            "dolar_rates": {},
            "indicators": {},
            "sentiment_scores": {},
            "opportunities": [],
            "report": "",
            "nodo_error": None,
            "warnings": [],
        }

        # ─────────────────────────────────────────
        # 2. PRECIOS (HISTÓRICOS)
        # ─────────────────────────────────────────

        for asset in assets:
            series = prices[asset][:t+2]

            if len(series) < 20:
                continue

            state["raw_prices"][asset] = {
                "price_usd": series[-1],
                "change_24h": returns[asset][t-1] * 100 if t > 0 else 0,
                "change_7d": (
                    (series[-1] - series[-7]) / series[-7] * 100
                    if len(series) > 7 else 0
                ),
            }

        # ─────────────────────────────────────────
        # 3. INDICADORES (SIN API)
        # ─────────────────────────────────────────

        indicators = {}

        for asset in assets:
            series = prices[asset][:t+1]

            if len(series) < 20:
                continue

            # simulamos OHLC desde precios
            ohlc_mock = [
                [i, p, p, p, p]  # timestamp fake, OHLC iguales
                for i, p in enumerate(series)
            ]

            indicators[asset] = calculate_indicators(ohlc_mock)

        state["indicators"] = indicators

        # SIN sentiment en backtest
        state["sentiment_scores"] = {a: 0.0 for a in assets}

        # ─────────────────────────────────────────
        # 4. AGENTES (SIN MARKET GRAPH)
        # ─────────────────────────────────────────

        state = await opportunity_agent(state)
        state = await portfolio_optimizer_agent(state)

        # ─────────────────────────────────────────
        # 5. PESOS DEL PORTFOLIO
        # ─────────────────────────────────────────

        weights: Dict[str, float] = {}

        for o in state.get("opportunities", []):
            w = o.get("optimized_allocation_pct", 0) / 100
            if w > 0:
                weights[o["asset"]] = w

        # ─────────────────────────────────────────
        # 6. RETURNS DEL DÍA
        # ─────────────────────────────────────────

        daily_returns = {
            asset: returns[asset][t]
            for asset in assets
            if t < len(returns[asset])
        }

        # ─────────────────────────────────────────
        # 7. STEP SIMULACIÓN
        # ─────────────────────────────────────────

        if weights:
            simulator.step(weights, daily_returns)

    print("[Backtest] Finalizado")

    return simulator