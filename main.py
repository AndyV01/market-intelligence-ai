from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
 
load_dotenv()
 
app = FastAPI(
    title="Market Intelligence AI",
    description="Sistema multi-agente de análisis de criptomonedas con LangGraph",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
 
# CORS — ajustar origins en producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# Importar routes después de configurar CORS
from api.routes import router
app.include_router(router)
 
 
@app.get("/", tags=["health"])
async def root():
    return {
        "service": "Market Intelligence AI",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }
 
 
@app.get("/health", tags=["health"])
async def health_check():
    groq_configured = bool(os.getenv("GROQ_API_KEY"))
    return {
        "status": "healthy",
        "groq_configured": groq_configured,
        "environment": os.getenv("ENVIRONMENT", "development"),
    }