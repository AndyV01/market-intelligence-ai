# 🧠 Market Intelligence AI

Sistema multi‑agente para análisis de cripto y construcción de portafolio en ARS.

### Demo online

- Demo pública: **https://market-intelligence-ai-three.vercel.app/**
- Frontend desplegado en **Vercel**.
- Backend desplegado en **Render**.
- Estado actual: **completamente funcional**.

---

<img width="1918" height="869" alt="Captura de pantalla 2026-04-27 110906" src="https://github.com/user-attachments/assets/b9743fb8-4482-4074-9f27-0a9f1c1ad9a0" />


## 🎯 Qué resuelve

Este proyecto combina en un único flujo:

- Recolección de precios crypto, noticias y dólar argentino.
- Cálculo de indicadores técnicos por activo.
- Scoring cuantitativo + sentimiento (LLM con fallback heurístico).
- Detección de oportunidades (BUY / STRONG_BUY / WAIT / SELL / AVOID).
- Asignación macro por régimen de mercado (risk_on / neutral / risk_off).
- Optimización de la porción crypto (risk parity + sharpe-like + control de riesgo).
- Cálculo de instrumentos argentinos (LECAP, CER, caución, USD).
- Generación de reporte final (LLM + fallback).

---

## 🏗️ Arquitectura (LangGraph)

```text
DataAgent
  └─ obtiene precios, noticias, dólar y OHLC histórico
      ↓
MacroDataAgent
  └─ construye universo ARS (LECAP, CER, caución, USD)
      ↓
AnalysisAgent
  └─ indicadores técnicos + sentiment (LLM/fallback)
      ↓
OpportunityAgent
  └─ scoring cuantitativo + señales + régimen de mercado
      ↓
AssetAllocatorAgent
  └─ asignación macro (LECAP/CER/USD/CRYPTO)
      ↓
PortfolioOptimizerAgent
  └─ optimiza pesos crypto y montos sugeridos
      ↓
ReportAgent
  └─ reporte ejecutivo en español
```

El grafo incluye nodo de error para fallos críticos y propagación de `warnings` en todo el pipeline.

---

## 🔍 Funcionalidades del sistema (detalle)

### 1) Data ingestion

- **Precios spot crypto** por símbolo soportado.
- **Noticias crypto** para análisis de sentimiento.
- **Dólar ARS** (crypto/blue y otras cotizaciones provistas por API).
- **Histórico OHLC (90 velas por activo)** para detección de tendencia/volatilidad de régimen.

### 2) Análisis técnico + sentimiento

- Indicadores:
  - RSI
  - MACD (incluye detección de crossover)
  - Bollinger Bands (incluye ancho de banda)
- Sentimiento:
  - Primario: LLM (Groq, `llama-3.3-70b-versatile`) con salida JSON validada.
  - Secundario: fallback heurístico por `sentiment_hint` de noticias.
  - Fusión final: **70% LLM + 30% fallback**.

### 3) Motor de oportunidades

- Scoring por activo (0–100) con pesos:
  - Technical: 40%
  - Momentum: 25%
  - Volatility: 15%
  - Sentiment: 20%
- Señales:
  - `STRONG_BUY`, `BUY`, `WAIT`, `SELL`, `AVOID`
- Filtros adicionales de entrada:
  - score mínimo,
  - momentum mínimo,
  - umbrales más estrictos en `risk_off`.
- Salida por activo:
  - score total y parciales,
  - precio USD y referencia ARS,
  - señal,
  - asignación sugerida,
  - key signals interpretables.

### 4) Detección de régimen

Se infiere con BTC histórico:

- Tendencia (MA20 vs MA50 + precio actual).
- Volatilidad rolling reciente.

Resultado:

- `risk_on`
- `neutral`
- `risk_off`

En `risk_off`, el sistema aplica reglas más defensivas.

### 5) Asignación macro (Argentina + crypto)

Distribuye presupuesto en:

- **LECAP**
- **CER**
- **USD**
- **CRYPTO**

La distribución cambia según régimen y calidad de oportunidades detectadas.

### 6) Optimización de portafolio crypto

Sobre oportunidades invertibles (`BUY`/`STRONG_BUY`):

- Risk parity (inverso de volatilidad)
- Ajuste sharpe-like
- Matriz de correlación simplificada
- Caps por activo y mínimo por posición
- Volatility targeting
- Límite de riesgo total del bloque crypto

Salida:

- `optimized_allocation_pct`
- `optimized_amount_ars`

### 7) Instrumentos argentinos (bloque macro)

Incluye estimaciones para:

- **LECAP** (TIR estimada desde precio)
- **Bonos CER** (tir real placeholder configurable)
- **Caución bursátil** (tasa anual aproximada)
- **USD** (cotizaciones recolectadas)

Con proyección de ganancia a 30 días para el presupuesto asignado.

### 8) Reporte automático

- Si hay `GROQ_API_KEY`: reporte narrativo con formato ejecutivo.
- Si falla/no hay LLM: fallback determinístico estructurado.
- Siempre incluye advertencia de riesgo.

---

## 🧪 Backtesting

El repositorio incluye dos caminos:

1. **Simulación placeholder** (`backtesting/runner.py`) con retornos aleatorios.
2. **Backtest con datos reales** (`backtesting/run_real_backtest.py`) que:
   - carga históricos,
   - reconstruye estado por paso temporal,
   - ejecuta `opportunity_agent` + `portfolio_optimizer_agent`,
   - simula equity curve.

Script rápido:

```bash
python run_backtest.py
```

---

## 🌐 API (FastAPI)

Base: `http://localhost:8000/api/v1`

### `POST /analyze/sync`
Ejecuta el pipeline completo y devuelve resultado final.

Payload ejemplo:

```json
{
  "assets": ["BTC", "ETH", "SOL"],
  "budget_ars": 500000
}
```

### `POST /analyze`
Inicia análisis async y devuelve `job_id`.

### `GET /analyze/{job_id}`
Consulta estado/resultados del job async.

### `GET /assets/supported`
Lista símbolos soportados.

### `GET /health`
Healthcheck del servicio + estado de configuración Groq.

### `GET /`
Metadata del servicio.

---

## 📦 Estructura de respuesta principal

`/analyze/sync` devuelve (entre otros):

- `status`
- `report`
- `opportunities`
- `dolar_rates`
- `macro_allocation`
- `argentina_instruments`
- `warnings`

---

## 🖥️ Frontend

Aplicación React + Vite que:

- Consume `/analyze/sync`.
- Refresca análisis automáticamente cada 5 minutos.
- Muestra:
  - reporte,
  - oportunidades,
  - cards de instrumentos ARS,
  - números animados.

## 🚀 Setup local

### Backend

```bash
git clone https://github.com/AndyV01/market-intelligence-ai
cd market-intelligence-ai

python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -r requirements.txt

# opcional pero recomendado para reporte/sentiment con LLM
export GROQ_API_KEY="tu_api_key"

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🔁 CI/CD (GitHub Actions)

El repositorio incluye dos workflows automáticos en `.github/workflows`:

### CI (`ci.yml`)

Se ejecuta en cada `pull_request` y en cada `push` a cualquier rama.

- **Backend (Python 3.11)**
  - Instala dependencias desde `requirements.txt`.
  - Ejecuta chequeo de sintaxis con `python -m compileall .`.
  - Corre smoke tests de API (`/health` y `/api/v1/assets/supported`) usando `FastAPI TestClient`.
- **Frontend (Node 20)**
  - Instala dependencias con `npm ci`.
  - Compila el proyecto con `npm run build`.

Además, usa `concurrency` para cancelar ejecuciones previas del mismo branch y evitar pipelines duplicados.

### CD (`cd.yml`)

Se ejecuta cuando hay `push` a `main` o manualmente desde `workflow_dispatch`.

- Construye y empaqueta backend como `dist/backend.tar.gz`.
- Compila frontend en `frontend/dist`.
- Publica ambos artefactos con `actions/upload-artifact`:
  - `frontend-dist`
  - `backend-source`
- Define retención de artefactos por **14 días**.

Este CD actualmente está orientado a **entrega de artefactos** (no despliega a infraestructura productiva).

---

## 🔌 Integraciones/servicios usados

- CoinGecko
- Binance
- CryptoPanic (opcional)
- Dolar API
- Groq (LLM)
- yfinance (instrumentos locales)

---

## ⚠️ Limitaciones actuales

- El store de jobs async está en memoria (no persistente).
- Parte del módulo ARS usa supuestos fijos (ej.: tir real CER/caución).
- El modelo de optimización usa proxies (no covarianza histórica completa).
- Backtesting real no modela costos/slippage/comisiones.

---

## 🛠️ Stack

### Backend

- FastAPI
- LangGraph
- LangChain + Groq
- NumPy / Pandas
- yfinance

### Frontend

- React
- Vite

---

## ✅ Roadmap sugerido

- Persistencia de jobs (Redis/Postgres).
- Costos de ejecución y slippage en backtest.
- Dataset macro ARS más robusto y dinámico.
- Métricas adicionales (Sortino, Calmar, beta).
- Alertas y scheduler para ejecución periódica.

---

## Disclaimer

Este sistema es informativo/educativo.
No constituye asesoramiento financiero.
Invertir implica riesgo de pérdida de capital.
