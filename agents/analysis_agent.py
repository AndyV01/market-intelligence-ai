import asyncio
import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import MarketState
from services.coingecko import get_ohlc_data
from utils.indicators import calculate_indicators


async def analysis_agent(state: MarketState) -> MarketState:
    """
    Agente 2: Análisis técnico + sentiment del LLM.
    - Calcula RSI, MACD, Bollinger por cada asset
    - Usa Groq (Llama 3) para analizar sentiment de noticias
    """
    print("[AnalysisAgent] Iniciando análisis técnico y sentiment...")

    assets = state.get("assets", [])
    raw_news = state.get("raw_news", [])
    raw_prices = state.get("raw_prices", {})
    warnings = state.get("warnings", [])

    # 1. Indicadores técnicos (paralelo por asset)
    indicators = {}
    ohlc_tasks = {asset: get_ohlc_data(asset, days=14) for asset in assets}

    ohlc_results = await asyncio.gather(*ohlc_tasks.values(), return_exceptions=True)

    for asset, result in zip(ohlc_tasks.keys(), ohlc_results):
        if isinstance(result, Exception):
            warnings.append(f"No se pudo obtener OHLC para {asset}: {str(result)}")
            indicators[asset] = {"error": str(result)}
        else:
            indicators[asset] = calculate_indicators(result)
            print(f"[AnalysisAgent] {asset} - RSI: {indicators[asset].get('rsi', {}).get('value')}")

    # 2. Sentiment via LLM (Groq / Llama 3)
    sentiment_scores = {}
    try:
        sentiment_scores = await _analyze_sentiment_with_llm(assets, raw_news)
    except Exception as e:
        warnings.append(f"Sentiment LLM falló: {str(e)}")
        # Fallback: usar sentiment_hint de los votos de CryptoPanic
        sentiment_scores = _fallback_sentiment(assets, raw_news)

    print(f"[AnalysisAgent] Sentiment scores: {sentiment_scores}")

    return {
        **state,
        "indicators": indicators,
        "sentiment_scores": sentiment_scores,
        "warnings": warnings,
        "nodo_error": None,
    }


async def _analyze_sentiment_with_llm(
    assets: list,
    news: list,
) -> dict:
    """
    Usa Groq (Llama 3) para analizar el sentiment de las noticias
    y devolver un score por asset entre -1 (muy bearish) y 1 (muy bullish).
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY no configurada")

    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        api_key=groq_api_key,
    )

    # Preparar resumen de noticias para el prompt
    news_summary = "\n".join([
        f"- [{', '.join(n.get('currencies', []))}] {n.get('title', '')} ({n.get('sentiment_hint', 'neutral')})"
        for n in news[:10]
    ])

    assets_str = ", ".join(assets)

    system_msg = SystemMessage(content="""Eres un analista de criptomonedas experto en análisis de sentimiento de mercado.
Tu tarea es analizar noticias y devolver ÚNICAMENTE un JSON con scores de sentimiento.
Responde SOLO con el JSON, sin texto adicional, sin markdown, sin backticks.""")

    human_msg = HumanMessage(content=f"""Analiza el sentimiento de estas noticias para los assets: {assets_str}

NOTICIAS RECIENTES:
{news_summary}

Devuelve un JSON con el siguiente formato exacto (score de -1 a 1, donde -1=muy bearish, 0=neutral, 1=muy bullish):
{{
  "BTC": 0.5,
  "ETH": 0.2,
  ...
}}

Solo incluye los assets: {assets_str}
""")

    response = await llm.ainvoke([system_msg, human_msg])
    content = response.content.strip()

    # Limpiar posibles backticks
    content = content.replace("```json", "").replace("```", "").strip()

    import json
    scores = json.loads(content)

    # Validar que los scores estén en rango [-1, 1]
    return {
        asset: max(-1.0, min(1.0, float(scores.get(asset, 0.0))))
        for asset in assets
    }


def _fallback_sentiment(assets: list, news: list) -> dict:
    """Fallback sin LLM: sentiment basado en votos de CryptoPanic"""
    scores = {asset: 0.0 for asset in assets}

    for item in news:
        hint = item.get("sentiment_hint", "neutral")
        currencies = item.get("currencies", [])

        value = 0.3 if hint == "bullish" else (-0.3 if hint == "bearish" else 0.0)

        for currency in currencies:
            if currency in scores:
                scores[currency] = max(-1.0, min(1.0, scores[currency] + value))

    return scores