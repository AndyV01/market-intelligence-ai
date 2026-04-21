from typing import TypedDict, List, Optional, Dict, Any


class MarketState(TypedDict):
    """
    Estado compartido que fluye entre todos los agentes del grafo.
    """
    # Input
    assets: List[str]                   # ["BTC", "ETH", "USDT"]
    budget_usd: float                   # presupuesto en USD (ej: 300)

    # Data Agent output
    raw_prices: Dict[str, Any]          # precios actuales de cada asset
    raw_news: List[Dict[str, Any]]      # noticias recientes
    dolar_rates: Dict[str, float]       # dólar oficial, MEP, CCL, crypto

    # Analysis Agent output
    indicators: Dict[str, Any]          # RSI, MACD, Bollinger por asset
    sentiment_scores: Dict[str, float]  # score de sentimiento por asset [-1, 1]

    # Opportunity Agent output
    opportunities: List[Dict[str, Any]] # señales detectadas con score

    # Report Agent output
    report: str                         # resumen final legible

    # Control de errores
    nodo_error: Optional[str]
    warnings: List[str]