from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from graph.market_graph import market_graph
from utils.serializer import sanitize

router = APIRouter(prefix="/api/v1", tags=["market-intelligence"])

# Estado simple en memoria para jobs asincrónicos
# En producción usar Redis o base de datos
_jobs: dict = {}


# ── Schemas ──────────────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    assets: List[str] = Field(
        default=["BTC", "ETH"],
        description="Lista de símbolos a analizar",
        example=["BTC", "ETH", "SOL"],
    )
    budget_usd: float = Field(
        default=300.0,
        ge=10,
        le=100000,
        description="Presupuesto de inversión en USD",
    )

class AnalysisStatus(BaseModel):
    job_id: str
    status: str         # pending | running | completed | failed
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=AnalysisStatus, summary="Iniciar análisis de mercado")
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Inicia un análisis multi-agente en background.
    Retorna un job_id para consultar el resultado.
    """
    # Normalizar símbolos
    assets = [a.upper().strip() for a in request.assets]
    supported = {"BTC", "ETH", "USDT", "SOL", "BNB", "ADA", "XRP", "MATIC", "DOT", "AVAX"}
    invalid = [a for a in assets if a not in supported]

    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Assets no soportados: {invalid}. Soportados: {list(supported)}"
        )

    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {"status": "pending", "result": None, "error": None}

    background_tasks.add_task(_run_analysis, job_id, assets, request.budget_usd)

    return AnalysisStatus(
        job_id=job_id,
        status="pending",
        message=f"Análisis iniciado para {assets}. Consultá /analyze/{job_id} para el resultado.",
    )


@router.get("/analyze/{job_id}", summary="Consultar resultado de un análisis")
async def get_analysis_result(job_id: str):
    """
    Retorna el estado y resultado de un análisis iniciado previamente.
    """
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    job = _jobs[job_id]

    if job["status"] == "completed":
        return {
            "job_id": job_id,
            "status": "completed",
            "result": job["result"],
        }
    elif job["status"] == "failed":
        return {
            "job_id": job_id,
            "status": "failed",
            "error": job["error"],
        }
    else:
        return {
            "job_id": job_id,
            "status": job["status"],
            "message": "El análisis aún está en progreso...",
        }


@router.post("/analyze/sync", summary="Análisis sincrónico (espera el resultado)")
async def run_analysis_sync(request: AnalysisRequest):
    """
    Corre el análisis completo y espera el resultado (puede tardar 15-30 segundos).
    Ideal para testing o integraciones simples.
    """
    assets = [a.upper().strip() for a in request.assets]
    thread_id = str(uuid.uuid4())

    initial_state = {
        "assets": assets,
        "budget_usd": request.budget_usd,
        "raw_prices": {},
        "raw_news": [],
        "dolar_rates": {},
        "indicators": {},
        "sentiment_scores": {},
        "opportunities": [],
        "report": "",
        "nodo_error": None,
        "warnings": [],
    }

    config = {"configurable": {"thread_id": thread_id}}

    try:
        final_state = await market_graph.ainvoke(initial_state, config=config)
        final_state = sanitize(final_state)
        return sanitize({
            "status": "completed",
            "report": final_state.get("report"),
            "opportunities": final_state.get("opportunities", []),
            "dolar_rates": final_state.get("dolar_rates", {}),
            "warnings": final_state.get("warnings", []),
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el análisis: {str(e)}")


@router.get("/assets/supported", summary="Lista de assets soportados")
async def get_supported_assets():
    return {
        "assets": [
            {"symbol": "BTC", "name": "Bitcoin"},
            {"symbol": "ETH", "name": "Ethereum"},
            {"symbol": "SOL", "name": "Solana"},
            {"symbol": "BNB", "name": "BNB"},
            {"symbol": "ADA", "name": "Cardano"},
            {"symbol": "XRP", "name": "XRP"},
            {"symbol": "MATIC", "name": "Polygon"},
            {"symbol": "DOT", "name": "Polkadot"},
            {"symbol": "AVAX", "name": "Avalanche"},
            {"symbol": "USDT", "name": "Tether"},
        ],
        "available_on_cocos": ["BTC", "ETH", "USDT", "SOL", "BNB", "ADA"],
    }


# ── Background task ───────────────────────────────────────────────────────────

async def _run_analysis(job_id: str, assets: List[str], budget_usd: float):
    _jobs[job_id]["status"] = "running"
    thread_id = str(uuid.uuid4())

    initial_state = {
        "assets": assets,
        "budget_usd": budget_usd,
        "raw_prices": {},
        "raw_news": [],
        "dolar_rates": {},
        "indicators": {},
        "sentiment_scores": {},
        "opportunities": [],
        "report": "",
        "nodo_error": None,
        "warnings": [],
    }

    config = {"configurable": {"thread_id": thread_id}}

    try:
        final_state = await market_graph.ainvoke(initial_state, config=config)
        final_state = sanitize(final_state)
        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["result"] = {
            "report": final_state.get("report"),
            "opportunities": final_state.get("opportunities", []),
            "dolar_rates": final_state.get("dolar_rates", {}),
            "warnings": final_state.get("warnings", []),
        }
    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)