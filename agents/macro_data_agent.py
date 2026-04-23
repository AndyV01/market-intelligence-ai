import asyncio
import httpx
from datetime import datetime
from graph.state import MarketState
from utils.serializer import sanitize
import yfinance as yf


RAVA_URL = "https://www.rava.com/perfil"


async def fetch_rava(symbol: str):
    url = f"{RAVA_URL}/{symbol}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        if r.status_code != 200:
            raise Exception(f"Error Rava {symbol}: {r.status_code}")
        return r.text


def extract_price(symbol: str):
    try:
        ticker = yf.Ticker(f"{symbol}.BA")
        data = ticker.history(period="1d")

        if data.empty:
            print("NO DATA:", symbol)
            return None

        price = float(data["Close"].iloc[-1])
        print(f"{symbol} PRICE:", price)

        return price

    except Exception as e:
        print("ERROR:", e)
        return None


def compute_lecap_metrics(price: float, days_to_maturity: int, horizon_days: int = 30):
    if not price or price <= 0:
        return None, None, None

    face_value = 100.0

    total_gain = face_value - price
    tir_anual = (total_gain / price) * (365 / days_to_maturity)

    rendimiento_30d = (tir_anual / 365) * horizon_days

    return tir_anual, rendimiento_30d, horizon_days


async def macro_data_agent(state: MarketState) -> MarketState:
    print("[MacroDataAgent] Fetching Argentina instruments...")

    warnings = state.get("warnings", [])

    try:
        # LECAP
        lecap_symbol = "S30S6"
        lecap_price = extract_price(lecap_symbol)

        lecap_days = 130
        tir_anual, rendimiento_30d, horizon = compute_lecap_metrics(
            lecap_price,
            lecap_days,
            30
        )

        # CER
        cer_symbol = "TX26"
        cer_price = extract_price(cer_symbol)

        cer_tir = 0.08

        # USD
        dolar = state.get("dolar_rates", {})

        if lecap_price is None:
            warnings.append(f"No price for {lecap_symbol}")

        if cer_price is None:
            warnings.append(f"No price for {cer_symbol}")

        argentina_data = {
            "LECAP": [
                {
                    "symbol": lecap_symbol,
                    "price": lecap_price,
                    "tir_anual": tir_anual,
                    "rendimiento_30d": rendimiento_30d,
                    "horizon_days": horizon,
                }
            ],
            "CER": [
                {
                    "symbol": cer_symbol,
                    "price": cer_price,
                    "tir_real": cer_tir,
                }
            ],
            "USD": {
                "mep": dolar.get("mep", {}).get("avg"),
                "ccl": dolar.get("ccl", {}).get("avg"),
                "blue": dolar.get("blue", {}).get("avg"),
            },
        }

        print("[MacroDataAgent] OK:", argentina_data)

        return sanitize({
            **state,
            "argentina_instruments": argentina_data,
            "warnings": warnings,
            "nodo_error": None,
        })

    except Exception as e:
        warnings.append(f"MacroDataAgent error: {str(e)}")

        return sanitize({
            **state,
            "argentina_instruments": {},
            "warnings": warnings,
            "nodo_error": None,
        })