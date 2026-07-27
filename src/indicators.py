"""
Indicator set for the Momentum Swing Trading Strategy (RSI / EMA44 / EMA200 /
Price Action / Volume), plus the daily-trendline and weekly-bias helpers used
by Pillar 1 (Trend Structure).
"""
import numpy as np
import pandas as pd


def compute_indicators(df):
    """
    EMA44 = momentum level & dynamic support/resistance.
    EMA200 = trend filter.
    """
    df = df.copy()
    df["EMA44"] = df["Close"].ewm(span=44, adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=200, adjust=False, min_periods=100).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI14"] = (100 - (100 / (1 + rs))).fillna(50)

    prev_close = df["Close"].shift(1)
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - prev_close).abs(),
        (df["Low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    df["ATR14"] = tr.rolling(14).mean()

    df["VolAvg20"] = df["Volume"].shift(1).rolling(20).mean()
    df["VolSurge"] = df["Volume"] / df["VolAvg20"]
    return df


def weekly_trend_bias(df):
    """
    Best-effort approximation of the strategy's WEEKLY macro-context step,
    built by resampling the same daily bars (no separate weekly download
    needed). Returns True if weekly closes are in a rising structure (higher
    weekly close than ~10 weeks ago AND price above a 20-week EMA) — used
    only as a bonus confidence tag, never a hard gate (too few weekly bars
    for young listings to trust it as strictly as EMA200/trendline).
    """
    try:
        weekly = df[["Close"]].resample("W-FRI").last().dropna()
        if len(weekly) < 12:
            return None
        wk_ema20 = weekly["Close"].ewm(span=20, adjust=False).mean()
        last_close = weekly["Close"].iloc[-1]
        close_10wk_ago = weekly["Close"].iloc[-11]
        bullish = bool(last_close > close_10wk_ago and last_close > wk_ema20.iloc[-1])
        return bullish
    except Exception:
        return None


def _find_local_minima(series, window=4):
    idxs = []
    vals = series.values
    n = len(vals)
    for i in range(window, n - window):
        segment = vals[i - window:i + window + 1]
        if vals[i] == np.nanmin(segment):
            idxs.append(i)
    return idxs


def detect_ascending_trendline(df, lookback=40, min_points=3):
    """Fits a line through the last `min_points` swing lows and checks price
    is respecting it (Pillar 1's "Daily Trendline")."""
    recent = df.iloc[-lookback:].reset_index(drop=True)
    if len(recent) < 20:
        return {"detected": False}
    minima_idx = _find_local_minima(recent["Low"], window=3)
    if len(minima_idx) < min_points:
        return {"detected": False}
    xs = np.array(minima_idx[-min_points:])
    ys = recent["Low"].iloc[xs].values
    slope, intercept = np.polyfit(xs, ys, 1)
    if slope <= 0:
        return {"detected": False}
    last_idx = len(recent) - 1
    trendline_today = slope * last_idx + intercept
    close, low = recent["Close"].iloc[-1], recent["Low"].iloc[-1]
    if low <= trendline_today * 1.03 and close >= trendline_today * 0.98:
        return {"detected": True, "trendline_value": float(trendline_today)}
    return {"detected": False}
