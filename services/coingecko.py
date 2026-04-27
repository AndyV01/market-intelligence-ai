import asyncio
from typing import Any, Dict, List

import httpx
import yfinance as yf

from utils.cache import market_data_cache

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

YF_TICKER_MAP = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "USDT": "USDT-USD",
    "SOL": "SOL-USD",
    "BNB": "BNB-USD",
    "ADA": "ADA-USD",
    "XRP": "XRP-USD",
    "MATIC": "MATIC-USD",
    "DOT": "DOT-USD",
    "AVAX": "AVAX-USD",
}


def _build_price_payload(symbol: str, price: float) -> Dict[str, Any]:
    return {
        "id": ASSET_ID_MAP.get(symbol, symbol.lower()),
        "name": symbol,
        "price_usd": float(price),
        "market_cap": 0.0,
        "volume_24h": 0.0,
        "change_1h": 0.0,
        "change_24h": 0.0,
        "change_7d": 0.0,
        "ath": float(price),
        "ath_change_percentage": 0.0,
        "high_24h": float(price),
        "low_24h": float(price),
    }


def _fetch_prices_from_yfinance(symbols: List[str]) -> Dict[str, Any]:
    fallback: Dict[str, Any] = {}

    for symbol in symbols:
        ticker = YF_TICKER_MAP.get(symbol.upper())
        if not ticker:
            continue

        try:
            hist = yf.Ticker(ticker).history(period="2d", interval="1d", auto_adjust=False)
            if hist is None or hist.empty:
                continue

            close_price = float(hist["Close"].iloc[-1])
            fallback[symbol.upper()] = _build_price_payload(symbol.upper(), close_price)
        except Exception:
            continue

    return fallback


async def get_current_prices(symbols: List[str]) -> Dict[str, Any]:
    """
    Retorna precios actuales con caché en backend y fallback defensivo.
    """
    normalized = [s.upper() for s in symbols]
    cache_key = f"prices:{','.join(sorted(normalized))}"
    stale_key = f"stale:{cache_key}"

    cached = market_data_cache.get(cache_key)
    if cached:
        print("[Cache] Usando precios cacheados")
        return cached

    ids = [ASSET_ID_MAP.get(s, s.lower()) for s in normalized]
    ids_str = ",".join(ids)

    url = f"{COINGECKO_BASE}/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ids_str,
        "order": "market_cap_desc",
        "per_page": 50,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "1h,24h,7d",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        result: Dict[str, Any] = {}
        for coin in data:
            symbol = coin["symbol"].upper()
            result[symbol] = {
                "id": coin["id"],
                "name": coin["name"],
                "price_usd": float(coin["current_price"]),
                "market_cap": float(coin.get("market_cap") or 0),
                "volume_24h": float(coin.get("total_volume") or 0),
                "change_1h": coin.get("price_change_percentage_1h_in_currency") or 0,
                "change_24h": coin.get("price_change_percentage_24h") or 0,
                "change_7d": coin.get("price_change_percentage_7d_in_currency") or 0,
                "ath": float(coin.get("ath") or coin["current_price"]),
                "ath_change_percentage": coin.get("ath_change_percentage") or 0,
                "high_24h": float(coin.get("high_24h") or coin["current_price"]),
                "low_24h": float(coin.get("low_24h") or coin["current_price"]),
            }

        if result:
            market_data_cache.set(cache_key, result, ttl_seconds=180)
            market_data_cache.set(stale_key, result, ttl_seconds=3600)
            return result

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            print("[CoinGecko] Rate limit alcanzado (429), usando fallback")
        else:
            print(f"[CoinGecko] HTTP error: {e}")
    except Exception as e:
        print(f"[CoinGecko] Error inesperado: {e}")

    stale = market_data_cache.get(stale_key)
    if stale:
        return stale

    fallback = await asyncio.to_thread(_fetch_prices_from_yfinance, normalized)
    if fallback:
        market_data_cache.set(cache_key, fallback, ttl_seconds=90)
        market_data_cache.set(stale_key, fallback, ttl_seconds=1800)
        return fallback

    return {}


async def get_ohlc_data(symbol: str, days: int = 14):
    asset_id = ASSET_ID_MAP.get(symbol.upper(), symbol.lower())
    cache_key = f"ohlc:{asset_id}:{days}"

    cached = market_data_cache.get(cache_key)
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

        market_data_cache.set(cache_key, data, ttl_seconds=600)
        return data

    except Exception as e:
        print(f"[OHLC ERROR] {symbol}: {e}")
        return cached or []
