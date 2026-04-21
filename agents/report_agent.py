import os
import json
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import MarketState


async def report_agent(state: MarketState) -> MarketState:
    """
    Agente 4: Genera un reporte final en lenguaje natural.
    Usa Groq (Llama 3) para redactar el resumen ejecutivo.
    Fallback: reporte estructurado sin LLM.
    """
    print("[ReportAgent] Generando reporte final...")

    opportunities = state.get("opportunities", [])
    dolar_rates = state.get("dolar_rates", {})
    budget_usd = state.get("budget_usd", 300.0)
    warnings = state.get("warnings", [])
    assets = state.get("assets", [])

    try:
        report = await _generate_llm_report(opportunities, dolar_rates, budget_usd, assets)
    except Exception as e:
        warnings.append(f"LLM report falló, usando fallback: {str(e)}")
        report = _generate_fallback_report(opportunities, dolar_rates, budget_usd)

    print("[ReportAgent] Reporte generado.")

    return {
        **state,
        "report": report,
        "warnings": warnings,
        "nodo_error": None,
    }


async def _generate_llm_report(
    opportunities: list,
    dolar_rates: dict,
    budget_usd: float,
    assets: list,
) -> str:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY no configurada")

    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.3,
        api_key=groq_api_key,
    )

    # Serializar datos relevantes para el prompt
    opps_summary = json.dumps(
        [{
            "asset": o["asset"],
            "signal": o["signal"],
            "score": o["final_score"],
            "price_usd": o["price_usd"],
            "change_24h": o["change_24h"],
            "suggested_usd": o["suggested_amount_usd"],
            "key_signals": o["key_signals"],
        } for o in opportunities],
        ensure_ascii=False,
        indent=2,
    )

    crypto_rate = dolar_rates.get("crypto", {}).get("avg", "N/D")
    blue_rate = dolar_rates.get("blue", {}).get("avg", "N/D")
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

    system_msg = SystemMessage(content="""Eres un analista financiero especializado en criptomonedas para el mercado argentino.
Redactas reportes claros, directos y útiles en español rioplatense.
Siempre incluyes la advertencia de que el análisis es informativo y no es asesoramiento financiero.""")

    human_msg = HumanMessage(content=f"""Genera un reporte de mercado conciso para un inversor argentino con ${budget_usd} USD disponibles.

FECHA Y HORA: {timestamp}
DÓLAR CRYPTO: ${crypto_rate} ARS
DÓLAR BLUE: ${blue_rate} ARS

ANÁLISIS DE ASSETS:
{opps_summary}

El reporte debe tener:
1. 📊 RESUMEN DEL MERCADO (2-3 líneas del contexto general)
2. 🎯 OPORTUNIDADES DETECTADAS (listado de señales BUY/STRONG_BUY con justificación breve)
3. ⚠️ ASSETS A EVITAR O ESPERAR (señales WAIT/SELL/AVOID con razón)
4. 💰 ASIGNACIÓN SUGERIDA (cómo distribuir los ${budget_usd} USD)
5. 📌 NOTA DE RIESGO (siempre al final)

Sé directo y concreto. Máximo 400 palabras.""")

    response = await llm.ainvoke([system_msg, human_msg])
    return response.content


def _generate_fallback_report(
    opportunities: list,
    dolar_rates: dict,
    budget_usd: float,
) -> str:
    """Reporte estructurado sin LLM como fallback."""
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    crypto_rate = dolar_rates.get("crypto", {}).get("avg", "N/D")
    blue_rate = dolar_rates.get("blue", {}).get("avg", "N/D")

    lines = [
        f"📊 MARKET INTELLIGENCE REPORT — {timestamp}",
        f"💵 Dólar Crypto: ${crypto_rate} ARS | Dólar Blue: ${blue_rate} ARS",
        f"💰 Presupuesto: ${budget_usd} USD",
        "",
        "=" * 50,
        "🎯 SEÑALES DETECTADAS",
        "=" * 50,
    ]

    buy_signals = [o for o in opportunities if o["signal"] in ("STRONG_BUY", "BUY")]
    wait_signals = [o for o in opportunities if o["signal"] in ("WAIT", "SELL", "AVOID")]

    if buy_signals:
        for o in buy_signals:
            lines.append(f"\n✅ {o['asset']} — {o['signal']} (Score: {o['final_score']}/100)")
            lines.append(f"   Precio: ${o['price_usd']:,.2f} USD | Cambio 24h: {o.get('change_24h', 0):.1f}%")
            lines.append(f"   Inversión sugerida: ${o['suggested_amount_usd']} USD")
            for sig in o.get("key_signals", []):
                lines.append(f"   {sig}")
    else:
        lines.append("\nNo se detectaron oportunidades de compra claras en este momento.")

    if wait_signals:
        lines.append("\n⏳ ESPERAR O EVITAR:")
        for o in wait_signals:
            lines.append(f"  • {o['asset']} — {o['signal']} (Score: {o['final_score']}/100)")

    lines.extend([
        "",
        "=" * 50,
        "⚠️ AVISO: Este análisis es únicamente informativo.",
        "No constituye asesoramiento financiero.",
        "Invertir en criptomonedas implica riesgo de pérdida total del capital.",
        "=" * 50,
    ])

    return "\n".join(lines)