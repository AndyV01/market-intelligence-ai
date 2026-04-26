import asyncio
from datetime import datetime, timedelta, timezone

import yfinance as yf

TICKER_MAP = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
    "BNB": "BNB-USD",
    "ADA": "ADA-USD",
    "XRP": "XRP-USD",
    "MATIC": "MATIC-USD",
    "DOT": "DOT-USD",
    "AVAX": "AVAX-USD",
    "USDT": "USDT-USD",
}

INTERVAL_MAP = {
    "1d": "1d",
    "1h": "1h",
}


def _fetch_ohlc_sync(ticker: str, interval: str, limit: int):
    yf_interval = INTERVAL_MAP.get(interval)
    if yf_interval is None:
        raise ValueError(f"Intervalo no soportado en Yahoo Finance: {interval}")

    end = datetime.now(timezone.utc)
    if interval == "1d":
        start = end - timedelta(days=max(limit + 10, 120))
    else:
        start = end - timedelta(hours=max(limit + 24, 240))

    frame = yf.download(
        tickers=ticker,
        start=start,
        end=end,
        interval=yf_interval,
        progress=False,
        auto_adjust=False,
        threads=False,
    )

    if frame is None or frame.empty:
        return []

    frame = frame.tail(limit)
    ohlc = []
    for ts, row in frame.iterrows():
        ohlc.append(
            {
                "timestamp": int(ts.timestamp() * 1000),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row["Volume"]),
            }
        )

    return ohlc


async def get_ohlc_data(asset: str, interval="1d", limit=100):
    ticker = TICKER_MAP.get(asset.upper())

    if not ticker:
        raise ValueError(f"Asset no soportado en Yahoo Finance: {asset}")

    return await asyncio.to_thread(_fetch_ohlc_sync, ticker, interval, limit)
