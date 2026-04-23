import os
import json
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import MarketState


async def report_agent(state: MarketState) -> MarketState:
    """
    Agente 4: Genera un reporte final en lenguaje natural.
    Usa Groq (Llama 3.3 70B) para redactar el resumen ejecutivo.
    Fallback: reporte estructurado sin LLM.
    """
    print("[ReportAgent] Generando reporte final...")

    opportunities = state.get("opportunities", [])
    dolar_rates = state.get("dolar_rates", {})
    budget_usd = state.get("budget_usd", 300.0)
    warnings = state.get("warnings", [])
    assets = state.get("assets", [])
    macro = state.get("macro_allocation") or {}
    # 🔥 Ordenar por score
    opportunities = sorted(
        opportunities,
        key=lambda x: x.get("final_score", 0),
        reverse=True
    )

    try:
        report = await _generate_llm_report(
            opportunities,
            dolar_rates,
            budget_usd,
            assets
        )
    except Exception as e:
        warnings.append(f"LLM report falló, usando fallback: {str(e)}")
        report = _generate_fallback_report(
            opportunities,
            dolar_rates,
            budget_usd
        )

    print("[ReportAgent] Reporte generado.")
    print("DEBUG REPORT MACRO IN:", macro)

    return {
        **state,
        "macro_allocation": macro,
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

    # Caso sin data o sin oportunidades
    if not opportunities:
        crypto_rate = dolar_rates.get("crypto", {}).get("avg", "N/D")
        blue_rate = dolar_rates.get("blue", {}).get("avg", "N/D")
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

        return (
          f"📊 MARKET STATUS — {timestamp}\n\n"
          f"💵 Dólar Crypto: ${crypto_rate} ARS | Blue: ${blue_rate} ARS\n\n"
          "🧠 CONDICIÓN DEL MERCADO:\n"
          "No hay activos que cumplan criterios de entrada (score + momentum).\n"
          "El sistema se mantiene en modo defensivo.\n\n"
          "📌 ACCIÓN:\n"
          "Esperar confirmaciones. No abrir posiciones.\n\n"
          "⚠️ RIESGO:\n"
          "Operar en estas condiciones aumenta probabilidad de pérdidas."
        )

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY no configurada")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        api_key=groq_api_key,
    )

    # 🔥 limitar ruido (top 5)
    opportunities = opportunities[:5]

    # 🔥 separar BUY vs AVOID
    buy = [o for o in opportunities if o["signal"] in ("BUY", "STRONG_BUY")]
    avoid = [o for o in opportunities if o["signal"] in ("WAIT", "SELL", "AVOID")]

    def enrich(o):
        return {
            "asset": o["asset"],
            "signal": o["signal"],
            "score": o["final_score"],
            "price_usd": o["price_usd"],
            "change_24h": o.get("change_24h", 0),
            "suggested_usd": o["suggested_amount_usd"],
            "confidence": (
                "high" if o["final_score"] > 80
                else "medium" if o["final_score"] > 60
                else "low"
            ),
            "key_signals": o.get("key_signals", []),
        }

    buy_json = json.dumps([enrich(o) for o in buy], ensure_ascii=False, indent=2)
    avoid_json = json.dumps([enrich(o) for o in avoid], ensure_ascii=False, indent=2)

    crypto_rate = dolar_rates.get("crypto", {}).get("avg", "N/D")
    blue_rate = dolar_rates.get("blue", {}).get("avg", "N/D")
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

    system_msg = SystemMessage(content="""
Eres un analista financiero especializado en criptomonedas para el mercado argentino.

Redactas reportes claros, directos y útiles en español rioplatense.

Reglas estrictas:
- No inventes datos que no estén en el input
- Si falta información, indícalo
- Prioriza decisiones accionables sobre descripción
- Sé concreto, sin relleno
- Siempre incluye advertencia de riesgo
""")

    human_msg = HumanMessage(content=f"""
Genera un reporte de mercado conciso para un inversor argentino con ${budget_usd} USD disponibles.

FECHA Y HORA: {timestamp}
DÓLAR CRYPTO: ${crypto_rate} ARS
DÓLAR BLUE: ${blue_rate} ARS

OPORTUNIDADES DE COMPRA:
{buy_json}

ASSETS A EVITAR:
{avoid_json}

Responde usando EXACTAMENTE este formato:

📊 RESUMEN DEL MERCADO:
...

🎯 OPORTUNIDADES DETECTADAS:
- ...

⚠️ ASSETS A EVITAR O ESPERAR:
- ...

💰 ASIGNACIÓN SUGERIDA:
...

📌 NOTA DE RIESGO:
...

No agregues secciones adicionales.
Máximo 400 palabras.
""")

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