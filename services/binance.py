import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

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

ASSET_NAMES = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
    "BNB": "BNB",
    "ADA": "Cardano",
    "XRP": "XRP",
    "MATIC": "Polygon",
    "DOT": "Polkadot",
    "AVAX": "Avalanche",
    "USDT": "Tether",
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

def _pct_change(current: float, base: float | None) -> float:
    if base is None or base == 0:
        return 0.0
    return ((current - base) / base) * 100


def _fetch_spot_prices_sync(assets: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for asset in assets:
        symbol = asset.upper()
        ticker = TICKER_MAP.get(symbol)
        if not ticker:
            continue

        try:
            hist = yf.Ticker(ticker).history(period="10d", interval="1d", auto_adjust=False)
            if hist is None or hist.empty:
                continue

            hist = hist.dropna(subset=["Close"])
            if hist.empty:
                continue

            close_price = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else None
            close_7d = float(hist["Close"].iloc[-8]) if len(hist) >= 8 else None
            high_24h = float(hist["High"].iloc[-1])
            low_24h = float(hist["Low"].iloc[-1])
            volume_24h = float(hist["Volume"].iloc[-1])

            result[symbol] = {
                "id": symbol.lower(),
                "name": ASSET_NAMES.get(symbol, symbol),
                "price_usd": close_price,
                "market_cap": 0.0,
                "volume_24h": volume_24h,
                "change_1h": 0.0,
                "change_24h": _pct_change(close_price, prev_close),
                "change_7d": _pct_change(close_price, close_7d),
                "ath": close_price,
                "ath_change_percentage": 0.0,
                "high_24h": high_24h,
                "low_24h": low_24h,
            }
        except Exception:
            continue

    return result

async def get_ohlc_data(asset: str, interval="1d", limit=100):
    ticker = TICKER_MAP.get(asset.upper())

    if not ticker:
        raise ValueError(f"Asset no soportado en Yahoo Finance: {asset}")

    return await asyncio.to_thread(_fetch_ohlc_sync, ticker, interval, limit)


async def get_spot_prices(assets: list[str]) -> dict[str, Any]:
    return await asyncio.to_thread(_fetch_spot_prices_sync, assets)
