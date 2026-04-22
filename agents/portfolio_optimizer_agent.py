import math
import numpy as np
from typing import Dict, List
from graph.state import MarketState

MAX_WEIGHT = 0.35
MIN_WEIGHT = 0.03
TARGET_VOL = 0.15  # target de volatilidad portfolio (15%)


async def portfolio_optimizer_agent(state: MarketState) -> MarketState:
    print("[PortfolioOptimizer] Quant optimization (risk parity + sharpe)...")

    opportunities = state.get("opportunities", [])
    budget = state.get("budget_usd", 300.0)
    warnings = state.get("warnings", [])

    investable = [
        o for o in opportunities
        if o["signal"] in ("STRONG_BUY", "BUY")
    ]

    if len(investable) < 2:
        warnings.append("Muy pocos activos para optimización real")
        return state

    assets = [o["asset"] for o in investable]

    # ─────────────────────────────────────────────
    # 1. ESTIMAR RETURNS Y VOLATILIDAD
    # ─────────────────────────────────────────────

    returns = []
    volatilities = []

    for o in investable:
        momentum = o["scores"]["momentum"]
        vol_score = o["scores"]["volatility"]

        # expected return proxy
        r = (momentum - 50) / 50  # [-1,1]
        returns.append(r)

        # volatility proxy
        vol = max(0.05, vol_score / 100)
        volatilities.append(vol)

    returns = np.array(returns)
    volatilities = np.array(volatilities)

    # ─────────────────────────────────────────────
    # 2. MATRIZ DE CORRELACIÓN (SIMPLIFICADA)
    # ─────────────────────────────────────────────

    n = len(assets)
    corr_matrix = np.ones((n, n))

    for i in range(n):
        for j in range(n):
            if i == j:
                corr_matrix[i][j] = 1
            else:
                # penalizar assets similares (crypto suelen estar correlacionadas)
                diff = abs(returns[i] - returns[j])
                corr = 0.8 - diff * 0.5
                corr_matrix[i][j] = max(0.3, min(0.9, corr))

    # covarianza
    cov_matrix = np.outer(volatilities, volatilities) * corr_matrix

    # ─────────────────────────────────────────────
    # 3. RISK PARITY (inverso de volatilidad)
    # ─────────────────────────────────────────────

    inv_vol = 1 / volatilities
    rp_weights = inv_vol / np.sum(inv_vol)

    # ─────────────────────────────────────────────
    # 4. SHARPE-LIKE OPTIMIZATION
    # ─────────────────────────────────────────────

    port_return = np.dot(rp_weights, returns)
    port_vol = math.sqrt(np.dot(rp_weights.T, np.dot(cov_matrix, rp_weights)))

    sharpe = port_return / (port_vol + 1e-6)

    # ajuste: más peso a mejores activos
    adjusted = rp_weights * np.maximum(returns, 0.01)

    weights = adjusted / np.sum(adjusted)

    # ─────────────────────────────────────────────
    # 4.5 CONTROL DE RIESGO TOTAL (ACA VA)
    # ─────────────────────────────────────────────

    MAX_PORTFOLIO_RISK = 0.6  # 60% del capital

    total_weight = np.sum(weights)

    if total_weight > MAX_PORTFOLIO_RISK:
       scale = MAX_PORTFOLIO_RISK / total_weight
       weights = weights * scale

    # ─────────────────────────────────────────────
    # 5. VOLATILITY TARGETING
    # ─────────────────────────────────────────────

    port_vol = math.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

    if port_vol > 0:
        scale = TARGET_VOL / port_vol
        weights = weights * scale

        total_weight = np.sum(weights)

    if total_weight > MAX_PORTFOLIO_RISK:
     scale = MAX_PORTFOLIO_RISK / total_weight
     weights = weights * scale

    # ─────────────────────────────────────────────
    # 6. CAPS Y LIMPIEZA
    # ─────────────────────────────────────────────

    final_weights = {}
    excess = 0

    for i, a in enumerate(assets):
        w = weights[i]

        if w > MAX_WEIGHT:
            excess += w - MAX_WEIGHT
            final_weights[a] = MAX_WEIGHT
        else:
            final_weights[a] = w

    # redistribuir exceso
    if excess > 0:
        remaining = {a: w for a, w in final_weights.items() if w < MAX_WEIGHT}
        total_remain = sum(remaining.values())

        if total_remain > 0:
            for a in remaining:
                final_weights[a] += (remaining[a] / total_remain) * excess

    # filtrar mínimos
    final_weights = {
        a: w for a, w in final_weights.items()
        if w >= MIN_WEIGHT
    }

    # normalizar final
    final_weights = final_weights

    # ─────────────────────────────────────────────
    # 7. OUTPUT
    # ─────────────────────────────────────────────

    optimized = []

    for o in opportunities:
        asset = o["asset"]

        if asset in final_weights:
            w = final_weights[asset]
            allocation_pct = round(w * 100, 2)
            amount = round(budget * w, 2)
        else:
            allocation_pct = 0
            amount = 0

        optimized.append({
            **o,
            "optimized_allocation_pct": allocation_pct,
            "optimized_amount_usd": amount,
        })

    print(f"[PortfolioOptimizer] Sharpe approx: {round(sharpe, 3)}")
    print("[PortfolioOptimizer] Optimización completada")

    return {
        **state,
        "opportunities": optimized,
        "warnings": warnings,
    }