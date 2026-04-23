# 🧠 Market Intelligence AI

Sistema **multi-agente de análisis financiero** enfocado en el mercado argentino.

Combina:
- 📊 Criptomonedas (análisis técnico + sentiment)
- 🇦🇷 Instrumentos locales (LECAP, CER, cauciones)
- 💰 Asignación inteligente de portfolio
- 🖥️ UI estilo terminal financiero (tipo Bloomberg)

---

## 🏗️ Arquitectura

```
DataAgent
   ↓
AnalysisAgent (TA + Sentiment)
   ↓
OpportunityAgent (scoring + señales)
   ↓
AssetAllocator (macro allocation ARS)
   ↓
PortfolioOptimizer (risk parity + sharpe)
   ↓
MacroDataAgent (LECAP / CER / USD)
   ↓
ReportAgent (LLM + fallback)
```

---

## 🚀 Qué hace el sistema

### 📊 Crypto
- RSI, MACD, Bollinger Bands  
- Sentiment con LLM (Groq)  
- Score cuantitativo (0–100)  
- Señales: BUY / SELL / WAIT  

---

### 🇦🇷 Portfolio Argentina

Con presupuesto configurable (default: **$500.000 ARS**):

- 🧾 LECAP (tasa fija)  
- 📈 Bonos CER (inflación)  
- 💵 USD (MEP / CCL / Blue)  
- 🏦 Cauciones (money market)  

Todo proyectado a **30 días**

Ejemplo:

```
Capital: $90.000
TIR anual: 85%
Ganancia estimada (30d): $6.300
Valor final: $96.300
```

---

### 🧠 Asset Allocation

El sistema detecta el régimen de mercado:

- 🟢 risk_on → más crypto  
- 🔴 risk_off → más tasa / CER / USD  
- 🟡 neutral → balanceado  

---

### ⚙️ Portfolio Optimization

- Risk parity  
- Sharpe-like optimization  
- Volatility targeting  
- Control de riesgo total  

---

## 🖥️ Frontend

- ✨ Glassmorphism cards  
- 📈 Animaciones tipo mercado  
- 🔢 Números dinámicos  
- 🏆 Ranking automático  
- 🎨 UI estilo Wall Street  

---

## 🚀 Setup local

### Backend

```bash
git clone https://github.com/AndyV01/market-intelligence-ai
cd market-intelligence-ai

python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -r requirements.txt

cp .env.example .env
# agregar GROQ_API_KEY

uvicorn main:app --reload --port 8000
```

---

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🔑 APIs utilizadas

| API | Key | Uso |
|-----|----|-----|
| CoinGecko | ❌ | precios crypto |
| Binance | ❌ | OHLC histórico |
| dolarapi | ❌ | dólar ARS |
| Groq | ✅ | LLM |
| CryptoPanic | opcional | noticias |

---

## 📡 Endpoints

### POST `/api/v1/analyze/sync`

```json
{
  "assets": ["BTC", "ETH", "SOL"],
  "budget_ars": 500000
}
```

---

### POST `/api/v1/analyze`

Análisis asincrónico (devuelve `job_id`)

---

### GET `/api/v1/analyze/{job_id}`

Consulta estado del análisis

---

### GET `/api/v1/assets/supported`

Lista de assets disponibles

---

## 📦 Output

El sistema devuelve:

- report  
- opportunities  
- macro_allocation  
- argentina_instruments  
- dolar_rates  
- warnings  

---

## 🧠 Ejemplo de salida

```
📊 RESUMEN DEL MERCADO:
Momentum positivo en BTC, debilidad en ETH.

🎯 OPORTUNIDADES:
- BTC → BUY (score 78)

⚠️ EVITAR:
- ETH → WAIT

💰 ASIGNACIÓN:
Crypto: 30%
LECAP: 30%
CER: 25%
USD: 15%
```

---

## 🚢 Deploy (Render)

Build:
```bash
pip install -r requirements.txt
```

Start:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Env:
```
GROQ_API_KEY=xxxx
```

---

## ⚠️ Disclaimer

Este sistema es informativo.  
No constituye asesoramiento financiero.  
Invertir implica riesgo de pérdida de capital.

---

## 🛠️ Tech Stack

### Backend
- FastAPI  
- LangGraph  
- LangChain + Groq  
- numpy / pandas  

### Frontend
- React + Vite  
- UI custom (glass + trading style)  

---

## 🧪 Roadmap

- 📊 Mini charts por instrumento  
- 📡 Datos en tiempo real  
- 🧠 Modelos predictivos  
- 📉 Backtesting  
- 🔔 Alertas inteligentes  