"""
The Three-Pillar Momentum Swing screen and trade-level math. Pure technicals
only — no news, no LLM, nothing but real OHLCV data and arithmetic.
"""
import numpy as np
import pandas as pd

from . import config
from .indicators import detect_ascending_trendline, weekly_trend_bias


def score_candidate(symbol, df):
    """
    Gate every candidate through the strategy's Three-Pillar Framework,
    evaluated on the DAILY chart (Weekly/4H/1H aren't reliably available for
    free NSE data):

      PILLAR 1 — Trend Structure   : Price > EMA200, price above a rising daily trendline
      PILLAR 2 — Momentum          : RSI 40-70 & rising, EMA44 sloping up, price > EMA44,
                                      volume participation above the 20-day average
      PILLAR 3 — Volume (only)     : today is an up day AND RVOL >= MIN_RVOL (1.2x) —
                                      the candle-counting (2-3 red + 1st green) part of
                                      Pillar 3 needs intraday bars and is intentionally
                                      NOT attempted here.

    ALL THREE must pass — per the strategy doc, two out of three is not enough.
    """
    if len(df) < 60:
        return None
    latest = df.iloc[-1]
    if pd.isna(latest.get("EMA44")) or pd.isna(latest.get("RSI14")) or pd.isna(latest.get("VolAvg20")):
        return None

    close = latest["Close"]
    ema44, ema200 = latest["EMA44"], latest.get("EMA200", np.nan)
    rsi, atr = latest["RSI14"], latest["ATR14"]
    vol_surge = latest["VolSurge"] if not pd.isna(latest["VolSurge"]) else 1.0
    prev = df.iloc[-2]

    # ---- practical liquidity filters ----
    avg_turnover = latest["VolAvg20"] * close if not pd.isna(latest["VolAvg20"]) else 0
    if avg_turnover < config.MIN_AVG_TURNOVER_INR:
        return None
    if pd.isna(latest["VolAvg20"]) or latest["VolAvg20"] < config.MIN_AVG_DAILY_VOLUME_SHARES:
        return None

    # ---- PILLAR 1: Trend Structure ----
    tl = detect_ascending_trendline(df)
    p1_above_ema200 = bool(not pd.isna(ema200) and close > ema200)
    p1_above_trendline = bool(tl["detected"])
    if not (p1_above_ema200 and p1_above_trendline):
        return None

    # ---- PILLAR 2: Momentum Confirmation ----
    rsi_lookback = df["RSI14"].iloc[-4] if len(df) >= 4 else rsi
    ema44_lookback = df["EMA44"].iloc[-6] if len(df) >= 6 else ema44
    p2_rsi_range = bool(40 <= rsi <= 70)
    p2_rsi_rising = bool(rsi > rsi_lookback)
    p2_ema44_slope_up = bool(not pd.isna(ema44_lookback) and ema44 > ema44_lookback)
    p2_price_above_ema44 = bool(not pd.isna(ema44) and close > ema44)
    p2_volume_participation = bool(vol_surge >= 1.0)
    if not (p2_rsi_range and p2_rsi_rising and p2_ema44_slope_up
            and p2_price_above_ema44 and p2_volume_participation):
        return None

    # ---- PILLAR 3 (volume only, per strategy's Volume Analysis table:
    #      "Price up + Volume surge = strong buying conviction, CONFIRM entry") ----
    p3_green_day = bool(close > prev["Close"])
    p3_rvol_conviction = bool(vol_surge >= config.MIN_RVOL)
    if not (p3_green_day and p3_rvol_conviction):
        return None

    weekly_bias = weekly_trend_bias(df)

    tags = [
        f"PILLAR 1 (Trend): Price Rs.{close:.1f} above EMA200 Rs.{ema200:.1f}, and above a rising daily trendline",
        f"PILLAR 2 (Momentum): RSI {rsi:.0f} (40-70 range, rising), EMA44 sloping up, price above EMA44, volume {vol_surge:.1f}x 20d avg",
        f"PILLAR 3 (Volume confirmation): Up day + volume {vol_surge:.1f}x avg (>= {config.MIN_RVOL}x conviction threshold)",
    ]
    if weekly_bias is True:
        tags.append("Weekly bias: bullish (bonus context, not a hard gate)")
    elif weekly_bias is False:
        tags.append("Weekly bias: not yet confirmed bullish (daily setup still valid, extra caution advised)")

    # Ranking score for ordering the report — NOT a pass/fail gate (all 3 pillars already are).
    rsi_sweetness = 1.0 - abs(rsi - 55) / 30.0  # closer to 55 (doc's HOLD zone) ranks higher
    score = (
        max(rsi_sweetness, 0) * 1.5
        + min(vol_surge, 3.0) * 1.0
        + 1.0  # trendline confirmed (always true to reach here)
        + (0.5 if weekly_bias else 0)
    )

    return {
        "symbol": symbol,
        "close": float(close),
        "prev_close": float(prev["Close"]),
        "ema44": float(ema44),
        "ema200": float(ema200) if not pd.isna(ema200) else None,
        "rsi": float(rsi),
        "atr": float(atr) if not pd.isna(atr) else None,
        "vol_surge": float(vol_surge),
        "volume_today": float(latest["Volume"]),
        "volume_avg20": float(latest["VolAvg20"]),
        "score": float(score),
        "tags": tags,
        "trendline": tl,
        "weekly_bias": weekly_bias,
    }


def _select_entry_pivot(df, pullback_days=5, breakout_days=3):
    """
    Approximates the strategy's Precision Entry rule ("Buy at the high of the
    first green candle, or a break above it; Stop = low of the 2-3 red candle
    pullback minus 0.5% buffer") using DAILY bars in place of the 1H chart:

      - pivot        = highest daily High in the last `breakout_days` sessions
      - pullback_low = lowest daily Low in the last `pullback_days` sessions

    Returns (pivot_price, pullback_low, source_label).
    """
    recent_entry = df.iloc[-breakout_days:]
    recent_pullback = df.iloc[-pullback_days:]
    pivot = float(recent_entry["High"].max())
    pullback_low = float(recent_pullback["Low"].min())
    source = f"{breakout_days}-day high (daily proxy for 1H entry-candle high)"
    return pivot, pullback_low, source


def compute_trade_levels(signal, df):
    close, atr = signal["close"], (signal["atr"] or signal["close"] * 0.02)

    pivot, pullback_low, pivot_source = _select_entry_pivot(df)

    raw_buffer = 0.3 * atr
    min_buffer = 0.0015 * pivot
    max_buffer = 0.01 * pivot
    buffer = min(max(raw_buffer, min_buffer), max_buffer)
    entry_price = round(pivot + buffer, 1)
    pivot_rounded = round(pivot, 1)

    extended = close > pivot * 1.05
    entry_confirmed = bool(not extended and close >= pivot)

    signal.setdefault("tags", []).append(
        f"Entry pivot: {pivot_source} @ Rs. {pivot_rounded}" + (" (extended — chase risk, per strategy pitfalls)" if extended else "")
    )

    structural_sl = pullback_low * 0.995
    atr_sl = entry_price - 2 * atr
    stop_loss = max(structural_sl, atr_sl) if structural_sl < entry_price else atr_sl
    stop_loss = min(max(stop_loss, entry_price * 0.92), entry_price * 0.985)

    risk = entry_price - stop_loss
    stop_loss_val = round(stop_loss, 1)
    target1_val = round(entry_price + 2 * risk, 1)   # 1:2 R:R (Phase 1 partial exit)
    target2_val = round(entry_price + 3 * risk, 1)   # 1:3 R:R (Phase 2/3 trail)
    return {
        "pivot": pivot_rounded,
        "pivot_source": pivot_source,
        "pullback_low": round(pullback_low, 1),
        "entry_low": pivot_rounded,
        "entry_high": entry_price,
        "entry_price": entry_price,
        "entry_confirmed": entry_confirmed,
        "extended": extended,
        "stop_loss": stop_loss_val,
        "target1": target1_val,
        "target2": target2_val,
        "stop_loss_pct": round((stop_loss_val - entry_price) / entry_price * 100, 1),
        "target1_pct": round((target1_val - entry_price) / entry_price * 100, 1),
        "target2_pct": round((target2_val - entry_price) / entry_price * 100, 1),
    }
