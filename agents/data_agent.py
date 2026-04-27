import asyncio
from graph.state import MarketState
from services.coingecko import get_current_prices
from services.cryptopanic import get_crypto_news
from services.dolar import get_dolar_rates
from services.binance import get_ohlc_data
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

        except Exception as e:
            warnings.append(f"OHLC error {asset}: {str(e)}")
            historical_prices[asset] = []

    return historical_prices


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

        if isinstance(raw_prices, Exception):
            warnings.append(f"Error fetching prices: {str(raw_prices)}")
            raw_prices = {}

        if isinstance(raw_news, Exception):
            warnings.append(f"Error fetching news: {str(raw_news)}")
            raw_news = []

        if isinstance(dolar_rates, Exception):
            warnings.append(f"Error fetching dolar rates: {str(dolar_rates)}")
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
