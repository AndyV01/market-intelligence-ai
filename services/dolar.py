import httpx
from typing import Dict, Any

DOLAR_API_BASE = "https://dolarapi.com/v1"


async def get_dolar_rates() -> Dict[str, float]:
    """
    Retorna los principales tipos de cambio del mercado argentino.
    """
    endpoints = {
        "oficial": "/dolares/oficial",
        "blue": "/dolares/blue",
        "mep": "/dolares/bolsa",
        "ccl": "/dolares/contadoconliqui",
        "crypto": "/dolares/cripto",
        "mayorista": "/dolares/mayorista",
    }

    rates = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, path in endpoints.items():
            try:
                resp = await client.get(f"{DOLAR_API_BASE}{path}")
                resp.raise_for_status()
                data = resp.json()
                rates[name] = {
                    "buy": data.get("compra"),
                    "sell": data.get("venta"),
                    "avg": round((data.get("compra", 0) + data.get("venta", 0)) / 2, 2),
                }
            except Exception:
                rates[name] = {"buy": None, "sell": None, "avg": None}

    return rates