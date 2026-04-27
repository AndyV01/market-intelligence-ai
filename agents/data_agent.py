import asyncio
from graph.state import MarketState
from services.coingecko import get_current_prices
from services.cryptopanic import get_crypto_news
from services.dolar import get_dolar_rates
from services.binance import get_ohlc_data, get_spot_prices
from utils.cache import market_data_cache


async def _get_historical_prices(assets: list[str], warnings: list[str]) -> dict[str, list[float]]:
    historical_prices: dict[str, list[float]] = {}

    for asset in assets:
        try:
            cache_key = f"ohlc_close:{asset}:90"
            cached_closes = market_data_cache.get(cache_key)
            if cached_closes is not None:
                historical_prices[asset] = cached_closes
                continue

            ohlc = await get_ohlc_data(asset, interval="1d", limit=90)
            closes = [candle["close"] for candle in ohlc]
            historical_prices[asset] = closes
            market_data_cache.set(cache_key, closes, ttl_seconds=1800)

        except Exception:
            warnings.append(f"OHLC no disponible para {asset}, usando serie vacía")
            historical_prices[asset] = []

    return historical_prices


async def _ensure_prices(raw_prices, assets: list[str], warnings: list[str]):
    if isinstance(raw_prices, Exception):
        warnings.append("CoinGecko no disponible, usando fallback de precios")
        raw_prices = {}

    if raw_prices and len(raw_prices) >= max(1, len(assets) // 2):
        return raw_prices

    fallback_prices = await get_spot_prices(assets)
    if fallback_prices:
        warnings.append("Precios de mercado obtenidos desde Yahoo Finance")
        if raw_prices:
            raw_prices.update({k: v for k, v in fallback_prices.items() if k not in raw_prices})
            return raw_prices
        return fallback_prices

    warnings.append("No se pudieron obtener precios en este ciclo")
    return {}


async def data_agent(state: MarketState) -> MarketState:
    """
    Agente 1: Recolecta datos de mercado en paralelo con cache en backend.
    """
    print("[DataAgent] Iniciando recolección de datos...")
    assets = state.get("assets", ["BTC", "ETH"])
    warnings = state.get("warnings", [])

    assets_key = ",".join(sorted(assets))
    cached_bundle_key = f"data_agent_bundle:{assets_key}"
    cached_bundle = market_data_cache.get(cached_bundle_key)

    if cached_bundle is not None:
        print("[DataAgent] Bundle cache hit")
        return {
            **state,
            **cached_bundle,
            "warnings": warnings,
            "nodo_error": None,
        }

    try:
        prices_task = get_current_prices(assets)
        news_task = get_crypto_news(assets, limit=15)
        dolar_task = get_dolar_rates()

        raw_prices, raw_news, dolar_rates = await asyncio.gather(
            prices_task,
            news_task,
            dolar_task,
            return_exceptions=True,
        )

        raw_prices = await _ensure_prices(raw_prices, assets, warnings)

        if isinstance(raw_news, Exception):
            warnings.append("Error al traer noticias, se continúa sin noticias")
            raw_news = []

        if isinstance(dolar_rates, Exception):
            warnings.append("Error al traer dólar, se continúa sin dólar")
            dolar_rates = {}

        historical_prices = await _get_historical_prices(assets, warnings)

        bundle = {
            "raw_prices": raw_prices,
            "raw_news": raw_news,
            "dolar_rates": dolar_rates,
            "historical_prices": historical_prices,
        }

        market_data_cache.set(cached_bundle_key, bundle, ttl_seconds=300)

        print(f"[DataAgent] Historical loaded: {list(historical_prices.keys())}")

        return {
            **state,
            **bundle,
            "warnings": warnings,
            "nodo_error": None,
        }

    except Exception as e:
        print(f"[DataAgent] Error crítico: {e}")
        return {
            **state,
            "raw_prices": {},
            "raw_news": [],
            "dolar_rates": {},
            "historical_prices": {},
            "warnings": warnings,
            "nodo_error": f"DataAgent falló: {str(e)}",
        }
