import asyncio
import os
import json
from statistics import mean

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from graph.state import MarketState
from services.coingecko import get_ohlc_data
from utils.indicators import calculate_indicators
from utils.serializer import sanitize

# ─────────────────────────────────────────────────────────────
# AGENTE PRINCIPAL
# ─────────────────────────────────────────────────────────────

async def analysis_agent(state: MarketState) -> MarketState:
    print("[AnalysisAgent] Iniciando análisis técnico + sentiment PRO...")

    assets = state.get("assets", [])
    raw_news = state.get("raw_news", [])
    warnings = state.get("warnings", [])

    # ── 1. INDICADORES TÉCNICOS ────────────────────────────────
    indicators = {}
    ohlc_tasks = {asset: get_ohlc_data(asset, days=14) for asset in assets}

    ohlc_results = await asyncio.gather(*ohlc_tasks.values(), return_exceptions=True)

    for asset, result in zip(ohlc_tasks.keys(), ohlc_results):
        if isinstance(result, Exception):
            warnings.append(f"OHLC error {asset}: {str(result)}")
            indicators[asset] = {"error": str(result)}
        else:
            indicators[asset] = sanitize(calculate_indicators(result))

    # ── 2. SENTIMENT (LLM + fallback) ──────────────────────────
    try:
        llm_scores = await _analyze_sentiment_with_llm(assets, raw_news)
    except Exception as e:
        warnings.append(f"LLM sentiment falló: {str(e)}")
        llm_scores = {}

    fallback_scores = _fallback_sentiment(assets, raw_news)

    # ── 3. FUSIÓN INTELIGENTE ──────────────────────────────────
    sentiment_scores = {}

    for asset in assets:
        llm = llm_scores.get(asset)
        fb = fallback_scores.get(asset, 0)

        if llm is not None:
            # peso 70% LLM, 30% fallback
            score = (llm * 0.7) + (fb * 0.3)
        else:
            score = fb

        sentiment_scores[asset] = float(round(max(-1.0, min(1.0, score)), 3))

    print("[AnalysisAgent] Sentiment final:", sentiment_scores)

    return sanitize({
        **state,
        "indicators": indicators,
        "sentiment_scores": sentiment_scores,
        "warnings": warnings,
        "nodo_error": None,
    })


# ─────────────────────────────────────────────────────────────
# LLM SENTIMENT (MEJORADO)
# ─────────────────────────────────────────────────────────────

async def _analyze_sentiment_with_llm(assets: list, news: list) -> dict:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY no configurada")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=groq_api_key,
    )

    # ── prompt más estructurado ───────────────────────────────
    news_summary = "\n".join([
        f"- {n.get('title', '')} | sentiment_hint: {n.get('sentiment_hint', 'neutral')} | coins: {','.join(n.get('currencies', []))}"
        for n in news[:12]
    ])

    assets_str = ", ".join(assets)

    system_msg = SystemMessage(content="""
Eres un analista cuantitativo de criptomonedas.

Tu tarea:
- Analizar noticias
- Evaluar impacto REAL en precio
- Devolver SOLO JSON válido

Reglas:
- Score entre -1 y 1
- -1 = muy bearish
- 0 = neutral
- 1 = muy bullish
- No inventar assets
- No texto extra
""")

    human_msg = HumanMessage(content=f"""
Assets: {assets_str}

Noticias:
{news_summary}

Devuelve JSON EXACTO:

{{
  "BTC": 0.2,
  "ETH": -0.1
}}

Solo esos assets.
""")

    response = await llm.ainvoke([system_msg, human_msg])
    content = response.content.strip()

    # ── limpieza robusta ─────────────────────────────────────
    content = content.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(content)
    except Exception:
        raise ValueError(f"JSON inválido del LLM: {content}")
    # ✅ VALIDACIÓN EXTRA DE JSON
    if not isinstance(parsed, dict):
         raise ValueError(f"LLM no devolvió un JSON válido: {parsed}")
   
    # ── validación fuerte ────────────────────────────────────
    clean = {}
    for asset in assets:
        val = parsed.get(asset, 0)

        try:
            val = float(val)
        except:
            val = 0

        clean[asset] = float(max(-1.0, min(1.0, float(val))))

    return clean


# ─────────────────────────────────────────────────────────────
# FALLBACK (HEURÍSTICO MEJORADO)
# ─────────────────────────────────────────────────────────────

def _fallback_sentiment(assets: list, news: list) -> dict:
    scores = {asset: [] for asset in assets}

    for item in news:
        hint = item.get("sentiment_hint", "neutral")
        currencies = item.get("currencies", [])

        if hint == "bullish":
            value = 0.4
        elif hint == "bearish":
            value = -0.4
        else:
            value = 0.0

        for c in currencies:
            if c in scores:
                scores[c].append(value)

    # promedio por asset
    final = {}
    for asset, vals in scores.items():
        final[asset] = float(round(mean(vals), 3)) if vals else 0.0

    return final