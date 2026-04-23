from typing import TypedDict, List, Dict, Any, Optional


class MarketState(TypedDict, total=False):
    """
    Estado compartido que fluye entre todos los agentes del grafo.
    """

    # Input
    assets: List[str]
    budget_usd: float

    # Data Agent output
    raw_prices: Dict[str, Any]
    raw_news: List[Dict[str, Any]]
    dolar_rates: Dict[str, float]
    historical_prices: Dict[str, List[float]]  # ← ya lo estás usando

    # Analysis Agent output
    indicators: Dict[str, Any]
    sentiment_scores: Dict[str, float]

    # Opportunity Agent output
    opportunities: List[Dict[str, Any]]

    # 🔴 NUEVO — CRÍTICO
    macro_allocation: Optional[Dict[str, float]]
    asset_allocation: Optional[Dict[str, float]]
    asset_allocation_usd: Optional[Dict[str, float]]
    argentina_instruments: Optional[Dict[str, Any]]

    # Report
    report: str

    # Control
    nodo_error: Optional[str]
    warnings: List[str]