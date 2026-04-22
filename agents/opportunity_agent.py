from graph.state import MarketState
from typing import List, Dict, Any
from utils.serializer import sanitize
import numpy as np

# ── Pesos tipo hedge fund ─────────────────────────────
WEIGHTS = {
    "technical": 0.4,
    "momentum": 0.25,
    "volatility": 0.15,
    "sentiment": 0.2,
}

# Umbrales
SCORE_STRONG_BUY = 70
SCORE_BUY = 55
SCORE_WAIT = 40
SCORE_SELL = 30


async def opportunity_agent(state: MarketState) -> MarketState:
    print("[OpportunityAgent] Evaluando oportunidades...")

    assets = state.get("assets", [])
    indicators = state.get("indicators", {})
    sentiment_scores = state.get("sentiment_scores", {})
    raw_prices = state.get("raw_prices", {})
    dolar_rates = state.get("dolar_rates", {})
    historical_prices = state.get("historical_prices", {})
    budget_usd = state.get("budget_usd", 300.0)
    warnings = state.get("warnings", [])

    # ─────────────────────────────────────────
    # ✅ REGIME DETECTION PRO (ACA VA)
    # ─────────────────────────────────────────

    btc_prices = historical_prices.get("BTC", [])

    btc_trend = _get_trend(btc_prices)
    btc_vol = _get_volatility(btc_prices)

    if btc_trend == "bear":
        regime = "risk_off"
    elif btc_vol > 0.04:
        regime = "risk_off"
    elif btc_trend == "neutral":
        regime = "neutral"
    else:
        regime = "risk_on"

    print(f"[Regime PRO] BTC trend: {btc_trend} | vol: {round(btc_vol,4)} → {regime}")

    # 🔴 CORTE TOTAL
    is_risk_off = regime == "risk_off"
    if is_risk_off:
        warnings.append("Market regime: risk_off")

    # ─────────────────────────────────────────
    # OPORTUNIDADES
    # ─────────────────────────────────────────

    opportunities = []

    for asset in assets:
        ind = indicators.get(asset, {})
        sentiment = sentiment_scores.get(asset, 0.0)
        price_data = raw_prices.get(asset, {})

        if not ind or "error" in ind:
            warnings.append(f"Skipping {asset}: sin indicadores")
            continue

        # SCORING
        tech = _score_technical(ind)
        momentum = _score_momentum(price_data)
        volatility = _score_volatility(ind)
        sentiment_score = (sentiment + 1) * 50

        final_score = float(round(
            tech * WEIGHTS["technical"]
            + momentum * WEIGHTS["momentum"]
            + volatility * WEIGHTS["volatility"]
            + sentiment_score * WEIGHTS["sentiment"],
            1,
        ))

        print(f"[OpportunityAgent] {asset}: {_get_signal(final_score)} ({final_score})")

        # FILTROS 
        if final_score < 62:
            continue

        if momentum < 55:
            continue

        if is_risk_off and final_score < 65:
            continue

        signal = _get_signal(final_score)

        allocation_pct = _dynamic_allocation(signal, final_score)
        suggested_amount = round(budget_usd * allocation_pct / 100, 2)

        price_usd = price_data.get("price_usd", 0)
        crypto_rate = dolar_rates.get("crypto", {}).get("avg")

        price_ars = (
            float(round(price_usd * crypto_rate, 2))
            if crypto_rate and price_usd else None
        )

        opportunities.append({
            "asset": asset,
            "signal": signal,
            "final_score": final_score,
            "scores": {
                "technical": round(tech, 1),
                "momentum": round(momentum, 1),
                "volatility": round(volatility, 1),
                "sentiment": round(sentiment_score, 1),
            },
            "price_usd": price_usd,
            "price_ars": price_ars,
            "change_24h": price_data.get("change_24h"),
            "suggested_amount_usd": suggested_amount,
            "allocation_pct": allocation_pct,
            "key_signals": _extract_key_signals(ind, sentiment),
        })

    opportunities.sort(key=lambda x: x["final_score"], reverse=True)

    return sanitize({
        **state,
        "opportunities": opportunities,
        "warnings": warnings,
        "nodo_error": None,
    })


# ─────────────────────────────────────────
# ✅ REGIME HELPERS 
# ─────────────────────────────────────────

def _get_trend(price_series: list):
    if len(price_series) < 50:
        return "neutral"

    ma20 = sum(price_series[-20:]) / 20
    ma50 = sum(price_series[-50:]) / 50
    price = price_series[-1]

    if price > ma20 and ma20 > ma50:
        return "bull"
    elif price < ma20 and ma20 < ma50:
        return "bear"
    return "neutral"


def _get_volatility(price_series: list):
    if len(price_series) < 20:
        return 0

    returns = []
    for i in range(1, len(price_series)):
        r = (price_series[i] - price_series[i-1]) / price_series[i-1]
        returns.append(r)

    return np.std(returns[-20:])


# ── SCORING ─────────────────────────────

def _score_technical(indicators: Dict) -> float:
    score = 50

    rsi = indicators.get("rsi", {}).get("value", 50)
    if rsi < 30:
        score += 20
    elif rsi > 70:
        score -= 20

    macd = indicators.get("macd", {})
    if macd.get("crossover") == "bullish_crossover":
        score += 15
    elif macd.get("crossover") == "bearish_crossover":
        score -= 15

    return max(0, min(100, score))


def _score_momentum(price_data: Dict) -> float:
    change_24h = price_data.get("change_24h", 0) or 0
    change_7d = price_data.get("change_7d", 0) or 0
    score = 50 + (change_24h * 1.5) + (change_7d * 0.5)
    return max(0, min(100, score))


def _score_volatility(indicators: Dict) -> float:
    bb = indicators.get("bollinger", {})
    width = bb.get("width", 0)

    if width > 0.2:
        return 40
    elif width < 0.05:
        return 60

    return 50


def _get_signal(score: float) -> str:
    if score >= SCORE_STRONG_BUY:
        return "STRONG_BUY"
    elif score >= SCORE_BUY:
        return "BUY"
    elif score >= SCORE_WAIT:
        return "WAIT"
    elif score >= SCORE_SELL:
        return "SELL"
    return "AVOID"


def _dynamic_allocation(signal: str, score: float) -> float:
    if signal == "STRONG_BUY":
        return min(50, score * 0.5)
    if signal == "BUY":
        return min(30, score * 0.3)
    return 0


def _extract_key_signals(indicators: Dict, sentiment: float) -> List[str]:
    signals = []

    if sentiment > 0.4:
        signals.append("🟢 Sentimiento positivo fuerte")
    elif sentiment < -0.4:
        signals.append("🔴 Sentimiento negativo fuerte")

    rsi = indicators.get("rsi", {}).get("value")
    if rsi and rsi < 30:
        signals.append("🟢 RSI sobreventa")

    return signals or ["⚪ Sin señales claras"]