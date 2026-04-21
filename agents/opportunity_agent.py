from graph.state import MarketState
from utils.indicators import score_asset
from typing import List, Dict, Any


# Umbrales configurables
SCORE_STRONG_BUY = 72
SCORE_BUY = 58
SCORE_WAIT = 42
SCORE_SELL = 30


async def opportunity_agent(state: MarketState) -> MarketState:
    """
    Agente 3: Detecta oportunidades combinando indicadores + sentiment.
    Asigna una señal (STRONG_BUY / BUY / WAIT / SELL / AVOID) y
    calcula cuánto invertir si el budget está configurado.
    """
    print("[OpportunityAgent] Evaluando oportunidades...")

    assets = state.get("assets", [])
    indicators = state.get("indicators", {})
    sentiment_scores = state.get("sentiment_scores", {})
    raw_prices = state.get("raw_prices", {})
    dolar_rates = state.get("dolar_rates", {})
    budget_usd = state.get("budget_usd", 300.0)
    warnings = state.get("warnings", [])

    opportunities = []

    for asset in assets:
        asset_indicators = indicators.get(asset, {})
        sentiment = sentiment_scores.get(asset, 0.0)
        price_data = raw_prices.get(asset, {})

        if "error" in asset_indicators or not asset_indicators:
            warnings.append(f"Skipping {asset}: sin indicadores disponibles")
            continue

        # Score técnico (0-100)
        technical_score = score_asset(asset_indicators)

        # Ajuste por sentiment (-10 a +10)
        sentiment_bonus = sentiment * 10

        # Score final
        final_score = round(min(100.0, max(0.0, technical_score + sentiment_bonus)), 1)

        # Señal
        signal = _get_signal(final_score)

        # Porcentaje sugerido del portfolio para este asset
        allocation_pct = _get_allocation(signal, final_score)
        suggested_amount = round(budget_usd * allocation_pct / 100, 2)

        # Precio en ARS (usando dólar crypto)
        price_usd = price_data.get("price_usd", 0)
        crypto_rate = dolar_rates.get("crypto", {}).get("avg")
        price_ars = round(price_usd * crypto_rate, 2) if crypto_rate and price_usd else None

        opportunity = {
            "asset": asset,
            "signal": signal,
            "final_score": final_score,
            "technical_score": round(technical_score, 1),
            "sentiment_score": round(sentiment, 2),
            "price_usd": price_usd,
            "price_ars": price_ars,
            "change_24h": price_data.get("change_24h"),
            "change_7d": price_data.get("change_7d"),
            "suggested_amount_usd": suggested_amount if signal in ("STRONG_BUY", "BUY") else 0,
            "allocation_pct": allocation_pct if signal in ("STRONG_BUY", "BUY") else 0,
            "key_signals": _extract_key_signals(asset_indicators, sentiment),
            "risk_note": _get_risk_note(signal, price_data),
        }

        opportunities.append(opportunity)
        print(f"[OpportunityAgent] {asset}: {signal} (score: {final_score})")

    # Ordenar por score descendente
    opportunities.sort(key=lambda x: x["final_score"], reverse=True)

    # Validar que el total sugerido no supere el budget
    total_suggested = sum(o["suggested_amount_usd"] for o in opportunities)
    if total_suggested > budget_usd:
        # Recalibrar proporcionalmente
        factor = budget_usd / total_suggested
        for o in opportunities:
            o["suggested_amount_usd"] = round(o["suggested_amount_usd"] * factor, 2)

    return {
        **state,
        "opportunities": opportunities,
        "warnings": warnings,
        "nodo_error": None,
    }


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


def _get_allocation(signal: str, score: float) -> float:
    """Porcentaje sugerido del portfolio total"""
    allocations = {
        "STRONG_BUY": 40.0,
        "BUY": 25.0,
        "WAIT": 0.0,
        "SELL": 0.0,
        "AVOID": 0.0,
    }
    return allocations.get(signal, 0.0)


def _extract_key_signals(indicators: Dict, sentiment: float) -> List[str]:
    """Extrae las señales más relevantes en lenguaje natural"""
    signals = []

    rsi = indicators.get("rsi", {})
    macd = indicators.get("macd", {})
    bb = indicators.get("bollinger", {})
    trend = indicators.get("volume_trend", {})

    rsi_signal = rsi.get("signal")
    if rsi_signal == "oversold":
        signals.append("🟢 RSI en sobreventa — posible punto de entrada")
    elif rsi_signal == "overbought":
        signals.append("🔴 RSI en sobrecompra — precaución")
    elif rsi_signal == "approaching_oversold":
        signals.append("🟡 RSI acercándose a sobreventa")

    crossover = macd.get("crossover")
    if crossover == "bullish_crossover":
        signals.append("🟢 MACD: cruce alcista detectado")
    elif crossover == "bearish_crossover":
        signals.append("🔴 MACD: cruce bajista detectado")
    elif macd.get("trend") == "bullish":
        signals.append("🟡 MACD: tendencia alcista")

    bb_pos = bb.get("position")
    if bb_pos == "near_lower_band":
        signals.append("🟢 Precio cerca de la banda inferior de Bollinger — posible rebote")
    elif bb_pos == "near_upper_band":
        signals.append("🔴 Precio cerca de la banda superior — posible corrección")

    if trend.get("trend") == "bullish" and trend.get("strength", 0) > 2:
        signals.append("🟢 Tendencia alcista de medias móviles")
    elif trend.get("trend") == "bearish":
        signals.append("🔴 Tendencia bajista de medias móviles")

    if sentiment > 0.3:
        signals.append(f"🟢 Sentimiento positivo en noticias ({sentiment:+.2f})")
    elif sentiment < -0.3:
        signals.append(f"🔴 Sentimiento negativo en noticias ({sentiment:+.2f})")

    return signals if signals else ["⚪ Sin señales claras en este momento"]


def _get_risk_note(signal: str, price_data: Dict) -> str:
    change_24h = price_data.get("change_24h", 0) or 0
    ath_change = price_data.get("ath_change_percentage", 0) or 0

    notes = []

    if abs(change_24h) > 5:
        direction = "subida" if change_24h > 0 else "caída"
        notes.append(f"Alta volatilidad: {direction} del {abs(change_24h):.1f}% en 24h")

    if ath_change > -10:
        notes.append("Precio cerca de su máximo histórico — mayor riesgo")

    notes.append("⚠️ Esto es análisis informativo, no asesoramiento financiero")

    return " | ".join(notes)