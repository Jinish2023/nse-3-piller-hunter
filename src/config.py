"""
Central configuration — env vars (from GitHub Secrets / .env locally) and
tunable constants. No news/AI keys here: this is a pure technical scanner.
"""
import os
from datetime import timezone, timedelta

# ── Telegram delivery (optional — scanner still runs and produces files
#    locally without these; see README) ──
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# ── Output paths ──
PDF_OUTPUT_PATH = "breakout_scan_report.pdf"
TRACKER_XLSX_PATH = "master_tracker.xlsx"
TRACKER_SHEET_NAME = "Swing Tracker"

# ── Report size ──
MAX_CANDIDATES_IN_REPORT = 18

# ── Liquidity filters (practical, not from the strategy doc, but needed so
#    the scanner doesn't surface illiquid/untradeable names) ──
MIN_AVG_TURNOVER_INR = 2_00_00_000       # ~2 crore/day minimum (value-based)
MIN_AVG_DAILY_VOLUME_SHARES = 500_000    # minimum 20-day avg daily volume (share-count based)

# ── Pillar 3 volume-conviction threshold ──
MIN_RVOL = 1.2  # today's volume must be >= this many times the 20-day average
                # (raise to 1.5 for a stricter, higher-conviction-only scan)

# ── Tracker de-duplication ──
DEDUP_LOOKBACK_DAYS = 5     # only compare against rows logged in the last N days
DEDUP_TOLERANCE_PCT = 0.5   # entry-zone / stop-loss within this % = "same setup"

IST = timezone(timedelta(hours=5, minutes=30))
