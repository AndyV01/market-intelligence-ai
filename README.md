# 🧠 Market Intelligence AI

Sistema multi-agente de análisis de criptomonedas construido con **LangGraph + FastAPI**.
Pensado para el mercado argentino (Cocos Crypto / dólar MEP / CCL).

## 🏗️ Arquitectura

```
DataAgent → AnalysisAgent → OpportunityAgent → ReportAgent
   │               │                │                │
CoinGecko      RSI/MACD/BB      Score 0-100     Groq LLM
CryptoPanic    Groq LLM         Señal BUY/SELL   Reporte ES
DolarAPI       Sentiment
```

## 🚀 Setup local

```bash
# 1. Clonar y entrar al proyecto
git clone https://github.com/AndyV01/market-intelligence-ai
cd market-intelligence-ai

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editá .env y agregá tu GROQ_API_KEY

# 5. Levantar el servidor
uvicorn main:app --reload --port 8000
```

Documentación interactiva: http://localhost:8000/docs

## 🔑 APIs necesarias

| API | Requiere key | Cómo obtenerla |
|-----|-------------|----------------|
| CoinGecko | ❌ No | Free tier sin registro |
| dolarapi.com | ❌ No | Free, sin registro |
| Groq (Llama 3) | ✅ Sí | [console.groq.com](https://console.groq.com) — gratis |
| CryptoPanic | Opcional | [cryptopanic.com](https://cryptopanic.com/developers/api/) — free tier |

## 📡 Endpoints principales

### `POST /api/v1/analyze/sync`
Análisis completo sincrónico (espera el resultado).

```json
{
  "assets": ["BTC", "ETH", "SOL"],
  "budget_usd": 300
}
```

### `POST /api/v1/analyze`
Análisis asincrónico (retorna job_id).

### `GET /api/v1/analyze/{job_id}`
Consulta el resultado de un análisis iniciado.

### `GET /api/v1/assets/supported`
Lista de assets disponibles.

## 🎯 Assets soportados
BTC, ETH, SOL, BNB, ADA, XRP, MATIC, DOT, AVAX, USDT

## 🚢 Deploy en Render (free tier)

1. Crear nuevo Web Service en render.com
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Agregar env vars: `GROQ_API_KEY`

## ⚠️ Disclaimer
Este sistema es **informativo**. No constituye asesoramiento financiero.
Invertir en criptomonedas implica riesgo de pérdida total del capital.

## 🛠️ Tech stack
- **FastAPI** — backend REST
- **LangGraph** — orquestación multi-agente (StateGraph + MemorySaver)
- **LangChain + Groq** — LLM (Llama 3.1 8B Instant)
- **pandas / numpy** — indicadores técnicos (RSI, MACD, Bollinger)
- **httpx** — llamadas async a APIs externas