import asyncio
from graph.state import MarketState
from utils.serializer import sanitize
import yfinance as yf

def extract_price(symbol: str):
    try:
        ticker = yf.Ticker(f"{symbol}.BA")
        data = ticker.history(period="1d")

        if data.empty:
            return None

        return float(data["Close"].iloc[-1])
    except:
        return None


def compute_tir(price, face=100, days=90):
    if not price:
        return None
    return ((face - price) / price) * (365 / days)


def compute_gain(capital, rate):
    if not rate:
        return 0
    return capital * (rate / 365 * 30)


async def macro_data_agent(state: MarketState) -> MarketState:
    print("[MacroDataAgent] Argentina PRO...")

    warnings = state.get("warnings", [])
    budget_ars = state.get("budget_ars", 500000)

    #  UNIVERSO REALISTA
    lecaps = ["S30S6", "S31E5", "S30J5"]
    cer_bonds = ["TX26", "TX28"]
    
    argentina_data = {
        "LECAP": [],
        "CER": [],
        "CAUCION": [],
        "USD": state.get("dolar_rates", {})
    }

    # ───────────── LECAPS ─────────────
    for sym in lecaps:
        price = extract_price(sym)
        tir = compute_tir(price, days=120)

        capital = budget_ars * 0.3 / len(lecaps)
        gain = compute_gain(capital, tir)

        argentina_data["LECAP"].append({
            "symbol": sym,
            "price": price,
            "tir": tir,
            "capital": capital,
            "gain_30d": gain,
        })

    # ───────────── CER ─────────────
    for sym in cer_bonds:
        price = extract_price(sym)

        tir_real = 0.08  # luego lo mejorás

        capital = budget_ars * 0.25 / len(cer_bonds)
        gain = compute_gain(capital, tir_real)

        argentina_data["CER"].append({
            "symbol": sym,
            "price": price,
            "tir_real": tir_real,
            "capital": capital,
            "gain_30d": gain,
        })

    # ───────────── CAUCIÓN ─────────────
    caucion_rate = 0.6  # 60% anual aprox

    capital = budget_ars * 0.15
    gain = compute_gain(capital, caucion_rate)

    argentina_data["CAUCION"].append({
        "symbol": "CAUCION",
        "rate": caucion_rate,
        "capital": capital,
        "gain_30d": gain,
    })

    print("[MacroDataAgent] OK:", argentina_data)

    return sanitize({
        **state,
        "argentina_instruments": argentina_data,
        "warnings": warnings,
        "nodo_error": None,
    })