import httpx

BASE_URL = "https://api.binance.com/api/v3/klines"

SYMBOL_MAP = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "SOL": "SOLUSDT",
}

async def get_ohlc_data(asset: str, interval="1d", limit=100):
    symbol = SYMBOL_MAP.get(asset)

    if not symbol:
        raise ValueError(f"Asset no soportado en Binance: {asset}")

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.get(BASE_URL, params=params)
        res.raise_for_status()
        data = res.json()

    # formato limpio
    ohlc = []
    for candle in data:
        ohlc.append({
            "timestamp": candle[0],
            "open": float(candle[1]),
            "high": float(candle[2]),
            "low": float(candle[3]),
            "close": float(candle[4]),
            "volume": float(candle[5]),
        })

    return ohlc