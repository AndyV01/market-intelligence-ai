import httpx
import os
from typing import List, Dict, Any

CRYPTOPANIC_BASE = "https://cryptopanic.com/api/free/v1"


async def get_crypto_news(symbols: List[str], limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retorna noticias recientes filtradas por currencies.
    Usa el free tier de CryptoPanic (no requiere API key en modo básico).
    Con API key en .env se obtienen más resultados y sentiment.
    """
    api_key = os.getenv("CRYPTOPANIC_API_KEY", "")
    currencies = ",".join(symbols)

    params = {
        "currencies": currencies,
        "kind": "news",
        "filter": "hot",
        "public": "true",
    }

    if api_key:
        params["auth_token"] = api_key

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{CRYPTOPANIC_BASE}/posts/", params=params)
            resp.raise_for_status()
            data = resp.json()

        news = []
        for item in data.get("results", [])[:limit]:
            news.append({
                "title": item.get("title", ""),
                "published_at": item.get("published_at", ""),
                "url": item.get("url", ""),
                "currencies": [c["code"] for c in item.get("currencies", [])],
                "votes": item.get("votes", {}),
                # positive / negative / important del free tier
                "sentiment_hint": _extract_sentiment_hint(item.get("votes", {})),
            })

        return news

    except Exception as e:
        return [{"error": str(e), "title": "No se pudieron obtener noticias", "currencies": symbols}]


def _extract_sentiment_hint(votes: Dict) -> str:
    """
    Infiere sentiment básico de los votos de CryptoPanic.
    """
    positive = votes.get("positive", 0) or 0
    negative = votes.get("negative", 0) or 0

    if positive > negative * 1.5:
        return "bullish"
    elif negative > positive * 1.5:
        return "bearish"
    return "neutral"