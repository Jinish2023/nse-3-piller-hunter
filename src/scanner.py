"""
Downloads daily OHLCV for the whole universe via yfinance and runs every
symbol through the Three-Pillar screen.
"""
import time
import pandas as pd
import yfinance as yf

from . import config
from .indicators import compute_indicators
from .strategy import score_candidate, compute_trade_levels


def scan_universe(symbols):
    print(f"  Downloading OHLCV for {len(symbols)} symbols via yfinance...")
    tickers = [f"{s}.NS" for s in symbols]
    candidates = []
    batch_size = 60

    for start in range(0, len(tickers), batch_size):
        batch = tickers[start:start + batch_size]
        try:
            data = yf.download(
                tickers=batch, period="15mo", interval="1d",
                group_by="ticker", auto_adjust=True, threads=True, progress=False,
            )
        except Exception as e:
            print(f"    Batch download failed: {e}")
            continue

        for ticker in batch:
            symbol = ticker.replace(".NS", "")
            try:
                if len(batch) == 1:
                    df = data
                else:
                    if ticker not in data.columns.get_level_values(0):
                        continue
                    df = data[ticker]
                df = df.dropna(subset=["Close"])
                # Yahoo sometimes appends a stub row for "today" before the session
                # has actually produced volume (pre-market runs, timezone rollover).
                # Drop any trailing bar with zero/NaN volume so every calculation is
                # anchored to the last fully completed trading day.
                while len(df) and (pd.isna(df["Volume"].iloc[-1]) or df["Volume"].iloc[-1] == 0):
                    df = df.iloc[:-1]
                if len(df) < 60:
                    continue
                df = compute_indicators(df)
                sig = score_candidate(symbol, df)
                if sig:
                    sig["levels"] = compute_trade_levels(sig, df)
                    candidates.append(sig)
            except Exception:
                continue
        time.sleep(1)  # be polite to Yahoo's endpoint between batches

    candidates.sort(key=lambda c: c["score"], reverse=True)
    print(f"  Found {len(candidates)} candidates clearing all 3 pillars + liquidity filters.")
    return candidates[:config.MAX_CANDIDATES_IN_REPORT]
