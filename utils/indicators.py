import pandas as pd
import numpy as np
from typing import List, Dict, Any


def calculate_indicators(ohlc_data: List[List[float]]) -> Dict[str, Any]:
    """
    Calcula RSI, MACD y Bollinger Bands desde datos OHLC.
    ohlc_data: [[timestamp, open, high, low, close], ...]
    """
    if not ohlc_data or len(ohlc_data) < 14:
        return {"error": "Datos insuficientes para calcular indicadores"}

    df = pd.DataFrame(ohlc_data, columns=["timestamp", "open", "high", "low", "close"])
    df["close"] = df["close"].astype(float)
    df = df.sort_values("timestamp").reset_index(drop=True)

    return {
        "rsi": _calculate_rsi(df["close"]),
        "macd": _calculate_macd(df["close"]),
        "bollinger": _calculate_bollinger(df["close"]),
        "volume_trend": _assess_price_trend(df["close"]),
        "current_price": float(df["close"].iloc[-1]),
        "data_points": len(df),
    }


def _calculate_rsi(prices: pd.Series, period: int = 14) -> Dict[str, Any]:
    """RSI: 0-30 oversold (compra), 70-100 overbought (venta)"""
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = -delta.clip(upper=0).rolling(window=period).mean()

    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    current_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None

    signal = "neutral"
    if current_rsi is not None:
        if current_rsi < 30:
            signal = "oversold"       # posible oportunidad de compra
        elif current_rsi < 45:
            signal = "approaching_oversold"
        elif current_rsi > 70:
            signal = "overbought"     # posible oportunidad de venta
        elif current_rsi > 55:
            signal = "approaching_overbought"

    return {
        "value": round(current_rsi, 2) if current_rsi else None,
        "signal": signal,
        "interpretation": _rsi_interpretation(current_rsi),
    }


def _calculate_macd(prices: pd.Series) -> Dict[str, Any]:
    """MACD: cruce de medias exponenciales"""
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line

    current_macd = float(macd_line.iloc[-1])
    current_signal = float(signal_line.iloc[-1])
    current_hist = float(histogram.iloc[-1])
    prev_hist = float(histogram.iloc[-2]) if len(histogram) > 1 else 0

    # Detectar cruce
    crossover = None
    if prev_hist < 0 and current_hist > 0:
        crossover = "bullish_crossover"   # señal de compra
    elif prev_hist > 0 and current_hist < 0:
        crossover = "bearish_crossover"   # señal de venta

    trend = "bullish" if current_macd > current_signal else "bearish"

    return {
        "macd": round(current_macd, 4),
        "signal": round(current_signal, 4),
        "histogram": round(current_hist, 4),
        "trend": trend,
        "crossover": crossover,
    }


def _calculate_bollinger(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, Any]:
    """Bollinger Bands: detecta volatilidad y niveles de soporte/resistencia"""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()

    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)

    current_price = float(prices.iloc[-1])
    current_upper = float(upper.iloc[-1]) if not pd.isna(upper.iloc[-1]) else None
    current_lower = float(lower.iloc[-1]) if not pd.isna(lower.iloc[-1]) else None
    current_sma = float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else None

    position = "middle"
    if current_lower and current_upper:
        band_range = current_upper - current_lower
        if band_range > 0:
            pct_b = (current_price - current_lower) / band_range
            if pct_b < 0.2:
                position = "near_lower_band"   # posible rebote hacia arriba
            elif pct_b > 0.8:
                position = "near_upper_band"   # posible corrección

    return {
        "upper": round(current_upper, 4) if current_upper else None,
        "middle": round(current_sma, 4) if current_sma else None,
        "lower": round(current_lower, 4) if current_lower else None,
        "position": position,
        "bandwidth": round((current_upper - current_lower) / current_sma * 100, 2)
                     if current_upper and current_lower and current_sma else None,
    }


def _assess_price_trend(prices: pd.Series, short: int = 7, long: int = 21) -> Dict[str, Any]:
    """Tendencia simple con medias móviles"""
    if len(prices) < long:
        return {"trend": "unknown", "strength": 0}

    sma_short = prices.rolling(window=short).mean().iloc[-1]
    sma_long = prices.rolling(window=long).mean().iloc[-1]
    current = prices.iloc[-1]

    trend = "bullish" if sma_short > sma_long else "bearish"
    strength = abs(sma_short - sma_long) / sma_long * 100

    return {
        "trend": trend,
        "strength": round(strength, 2),
        "above_short_ma": current > sma_short,
        "above_long_ma": current > sma_long,
    }


def _rsi_interpretation(rsi: float) -> str:
    if rsi is None:
        return "Sin datos suficientes"
    if rsi < 30:
        return f"RSI {rsi:.0f}: Zona de sobreventa — posible oportunidad de entrada"
    if rsi < 45:
        return f"RSI {rsi:.0f}: Acercándose a zona de sobreventa"
    if rsi > 70:
        return f"RSI {rsi:.0f}: Zona de sobrecompra — precaución, posible corrección"
    if rsi > 55:
        return f"RSI {rsi:.0f}: Acercándose a zona de sobrecompra"
    return f"RSI {rsi:.0f}: Zona neutral"


def score_asset(indicators: Dict[str, Any]) -> float:
    """
    Calcula un score de oportunidad de 0 a 100.
    Mayor score = mayor señal de entrada.
    """
    score = 50.0  # base neutral

    rsi = indicators.get("rsi", {})
    macd = indicators.get("macd", {})
    bollinger = indicators.get("bollinger", {})
    trend = indicators.get("volume_trend", {})

    # RSI: sobreventa suma puntos, sobrecompra resta
    rsi_val = rsi.get("value")
    if rsi_val is not None:
        if rsi_val < 30:
            score += 25
        elif rsi_val < 45:
            score += 10
        elif rsi_val > 70:
            score -= 20
        elif rsi_val > 60:
            score -= 8

    # MACD: cruce alcista suma, bajista resta
    crossover = macd.get("crossover")
    if crossover == "bullish_crossover":
        score += 20
    elif crossover == "bearish_crossover":
        score -= 15

    macd_trend = macd.get("trend")
    if macd_trend == "bullish":
        score += 5
    else:
        score -= 5

    # Bollinger: cerca del lower band suma
    bb_position = bollinger.get("position")
    if bb_position == "near_lower_band":
        score += 15
    elif bb_position == "near_upper_band":
        score -= 10

    # Tendencia de precio
    if trend.get("trend") == "bullish":
        score += 10
    else:
        score -= 5

    return max(0.0, min(100.0, score))