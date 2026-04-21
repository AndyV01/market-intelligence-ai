import math
from typing import Dict, List
from graph.state import MarketState


MAX_SINGLE_POSITION = 0.4   # 40% máximo por asset
MIN_POSITION = 0.05         # mínimo para incluir


async def portfolio_optimizer_agent(state: MarketState) -> MarketState:
    print("[PortfolioOptimizer] Optimizando portfolio...")

    opportunities = state.get("opportunities", [])
    budget = state.get("budget_usd", 300.0)
    warnings = state.get("warnings", [])

    # ── 1. Filtrar assets invertibles ─────────────────────
    investable = [
        o for o in opportunities
        if o["signal"] in ("STRONG_BUY", "BUY")
    ]

    if not investable:
        warnings.append("No hay activos aptos para inversión")
        return state

    # ── 2. Score → peso base ──────────────────────────────
    weights = {}

    for o in investable:
        score = o["final_score"]

        # exponencial → prioriza high conviction
        weights[o["asset"]] = math.exp(score / 20)

    # ── 3. Ajuste por volatilidad ─────────────────────────
    for o in investable:
        asset = o["asset"]
        vol_score = o["scores"]["volatility"]  # 0–100

        # mayor volatilidad → menor peso
        vol_penalty = (100 - vol_score) / 100

        weights[asset] *= vol_penalty

    # ── 4. Normalizar pesos ───────────────────────────────
    total_weight = sum(weights.values())

    normalized = {
        asset: w / total_weight
        for asset, w in weights.items()
    }

    # ── 5. Cap por asset (riesgo) ─────────────────────────
    capped = {}
    overflow = 0

    for asset, w in normalized.items():
        if w > MAX_SINGLE_POSITION:
            overflow += w - MAX_SINGLE_POSITION
            capped[asset] = MAX_SINGLE_POSITION
        else:
            capped[asset] = w

    # Redistribuir exceso
    if overflow > 0:
        remaining_assets = [
            a for a in capped if capped[a] < MAX_SINGLE_POSITION
        ]
        if remaining_assets:
            extra = overflow / len(remaining_assets)
            for a in remaining_assets:
                capped[a] += extra

    # ── 6. Limpiar posiciones muy chicas ──────────────────
    final_weights = {
        a: w for a, w in capped.items()
        if w >= MIN_POSITION
    }

    # Re-normalizar
    total = sum(final_weights.values())
    final_weights = {
        a: w / total for a, w in final_weights.items()
    }

    # ── 7. Aplicar al portfolio ───────────────────────────
    optimized = []

    for o in opportunities:
        asset = o["asset"]

        if asset in final_weights:
            allocation_pct = round(final_weights[asset] * 100, 2)
            amount = round(budget * final_weights[asset], 2)
        else:
            allocation_pct = 0
            amount = 0

        optimized.append({
            **o,
            "optimized_allocation_pct": allocation_pct,
            "optimized_amount_usd": amount,
        })

    print("[PortfolioOptimizer] Portfolio optimizado listo")

    return {
        **state,
        "opportunities": optimized,
        "warnings": warnings,
    }