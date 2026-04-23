import asyncio
from graph.state import MarketState
from services.coingecko import get_current_prices
from services.cryptopanic import get_crypto_news
from services.dolar import get_dolar_rates
from services.binance import get_ohlc_data


async def data_agent(state: MarketState) -> MarketState:
    """
    Agente 1: Recolecta datos de mercado en paralelo.
    
    """
    print("[DataAgent] Iniciando recolección de datos...")
    assets = state.get("assets", ["BTC", "ETH"])
    warnings = state.get("warnings", [])

    # Ejecutar las 3 fuentes en paralelo
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

        # Manejo de errores parciales
        if isinstance(raw_prices, Exception):
            warnings.append(f"Error fetching prices: {str(raw_prices)}")
            raw_prices = {}

        if isinstance(raw_news, Exception):
            warnings.append(f"Error fetching news: {str(raw_news)}")
            raw_news = []

        if isinstance(dolar_rates, Exception):
            warnings.append(f"Error fetching dolar rates: {str(dolar_rates)}")
            dolar_rates = {}

        historical_prices = {}

        for asset in assets:
            try:
                ohlc = await get_ohlc_data(asset, interval="1d", limit=90)
                closes = [candle["close"] for candle in ohlc]
                historical_prices[asset] = closes
                await asyncio.sleep(0.2)    

            except Exception as e:
                  warnings.append(f"OHLC error {asset}: {str(e)}")
                  historical_prices[asset] = []  

        print(f"[DataAgent] Historical loaded: {list(historical_prices.keys())}")
        

        return {
            **state,
            "raw_prices": raw_prices,
            "raw_news": raw_news,
            "dolar_rates": dolar_rates,
            "historical_prices": historical_prices,
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