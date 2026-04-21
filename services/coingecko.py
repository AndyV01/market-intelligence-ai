import httpx
from typing import Dict, Any, List

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Mapa de símbolo → ID de CoinGecko
ASSET_ID_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "SOL": "solana",
    "BNB": "binancecoin",
    "ADA": "cardano",
    "XRP": "ripple",
    "MATIC": "matic-network",
    "DOT": "polkadot",
    "AVAX": "avalanche-2",
}


async def get_current_prices(symbols: List[str]) -> Dict[str, Any]:
    """
    Retorna precios actuales, variación 24h, volumen y market cap.
    """
    ids = [ASSET_ID_MAP.get(s.upper(), s.lower()) for s in symbols]
    ids_str = ",".join(ids)

    url = f"{COINGECKO_BASE}/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ids_str,
        "order": "market_cap_desc",
        "per_page": 20,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "1h,24h,7d",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    result = {}
    for coin in data:
        symbol = coin["symbol"].upper()
        result[symbol] = {
            "id": coin["id"],
            "name": coin["name"],
            "price_usd": coin["current_price"],
            "market_cap": coin["market_cap"],
            "volume_24h": coin["total_volume"],
            "change_1h": coin.get("price_change_percentage_1h_in_currency"),
            "change_24h": coin.get("price_change_percentage_24h"),
            "change_7d": coin.get("price_change_percentage_7d_in_currency"),
            "ath": coin["ath"],
            "ath_change_percentage": coin["ath_change_percentage"],
            "high_24h": coin["high_24h"],
            "low_24h": coin["low_24h"],
        }

    return result


async def get_ohlc_data(symbol: str, days: int = 14) -> List[List[float]]:
    """
    Retorna datos OHLC para calcular indicadores técnicos.
    [timestamp, open, high, low, close]
    """
    coin_id = ASSET_ID_MAP.get(symbol.upper(), symbol.lower())
    url = f"{COINGECKO_BASE}/coins/{coin_id}/ohlc"
    params = {"vs_currency": "usd", "days": days}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()