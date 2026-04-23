from graph.state import MarketState
from utils.serializer import sanitize


async def asset_allocator_agent(state: MarketState) -> MarketState:
    print("[AssetAllocator] Asignando capital multi-asset...")

    opportunities = state.get("opportunities", [])
    budget = state.get("budget_usd", 300.0)
    warnings = state.get("warnings", [])

    # 🔹 Detectar régimen desde warnings
    regime = "neutral"

    for w in warnings:
        if "risk_off" in w:
            regime = "risk_off"
        elif "risk_on" in w:
            regime = "risk_on"

    # 🔹 Ver si hay crypto buenas
    strong_crypto = [
        o for o in opportunities
        if o["signal"] in ("BUY", "STRONG_BUY") and o["final_score"] >= 65
    ]

    allocation = {}

    # ─────────────────────────────────────────────
    # 🔴 CASO 1: RISK OFF (modo ultra defensivo)
    # ─────────────────────────────────────────────
    if regime == "risk_off":
        allocation = {
            "LECAP": 0.40,     # tasa fija corto plazo
            "CER": 0.30,       # inflación
            "USD": 0.20,       # cobertura dura
            "CRYPTO": 0.10 if strong_crypto else 0.0,
        }

    # 🟡 CASO 2: NEUTRAL
    elif regime == "neutral":
        allocation = {
            "LECAP": 0.30,
            "CER": 0.25,
            "USD": 0.15,
            "CRYPTO": 0.30 if strong_crypto else 0.10,
        }

    # 🟢 CASO 3: RISK ON
    else:
        allocation = {
            "LECAP": 0.10,
            "CER": 0.10,
            "USD": 0.10,
            "CRYPTO": 0.70 if strong_crypto else 0.30,
        }

    # ─────────────────────────────────────────────
    # 🔹 Convertir a montos
    # ─────────────────────────────────────────────

    allocation_usd = {
        k: round(v * budget, 2)
        for k, v in allocation.items()
    }

    print(f"[AssetAllocator] Regime: {regime}")
    print(f"[AssetAllocator] Allocation: {allocation}")

    new_state = {
    **state,
    "macro_allocation": allocation,
    "asset_allocation": allocation,
    "asset_allocation_usd": allocation_usd,
    "nodo_error": None,
    }

    print("DEBUG ASSET ALLOCATOR OUTPUT:", new_state.get("macro_allocation"))

    return sanitize(new_state)