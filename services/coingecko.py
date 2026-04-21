import httpx
from typing import Dict, Any, List
from services.cache import get_cached, set_cache

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
    Con cache para evitar rate limits (429).
    """

    # 🔑 clave única de cache por combinación de assets
    cache_key = f"prices:{','.join(sorted(symbols))}"

    # 1️⃣ intentar cache
    cached = get_cached(cache_key)
    if cached:
        print("[Cache] Usando precios cacheados")
        return cached

    # 2️⃣ si no hay cache → pegarle a CoinGecko
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

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPStatusError as e:
        # 🔥 manejo específico del 429
        if e.response.status_code == 429:
            print("[CoinGecko] Rate limit alcanzado (429)")

            # fallback: devolver cache viejo si existe
            if cached:
                return cached

            raise Exception("Rate limit de CoinGecko (429)")
        raise

    result = {}
    for coin in data:
        symbol = coin["symbol"].upper()
        result[symbol] = {
            "id": coin["id"],
            "name": coin["name"],
            "price_usd": float(coin["current_price"]),
            "market_cap": float(coin["market_cap"]),
            "volume_24h": float(coin["total_volume"]),
            "change_1h": coin.get("price_change_percentage_1h_in_currency"),
            "change_24h": coin.get("price_change_percentage_24h"),
            "change_7d": coin.get("price_change_percentage_7d_in_currency"),
            "ath": float(coin["ath"]),
            "ath_change_percentage": coin["ath_change_percentage"],
            "high_24h": coin["high_24h"],
            "low_24h": coin["low_24h"],
        }

    # 3️⃣ guardar en cache
    set_cache(cache_key, result, ex=120)

    return result


async def get_ohlc_data(symbol: str, days: int = 14):
    asset_id = ASSET_ID_MAP.get(symbol.upper(), symbol.lower())
    cache_key = f"ohlc:{asset_id}:{days}"

    # 1️⃣ CACHE
    cached = get_cached(cache_key)
    if cached:
        print(f"[Cache] OHLC {symbol}")
        return cached

    url = f"{COINGECKO_BASE}/coins/{asset_id}/ohlc"
    params = {
        "vs_currency": "usd",
        "days": days,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # 2️⃣ GUARDAR CACHE (más largo que prices)
        set_cache(cache_key, data, ex=120)  

        return data

    except httpx.HTTPStatusError as e:
        print(f"[OHLC ERROR] {symbol}: {e}")

        # 3️⃣ FALLBACK → usar cache viejo si existe
        cached = get_cached(cache_key)
        if cached:
            print(f"[Fallback] usando OHLC cacheado {symbol}")
            return cached

        raise e