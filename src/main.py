"""
Orchestration: universe -> scan (3-pillar) -> PDF + Excel tracker -> Telegram.
Pure technical scan — no news, no LLM.
"""
import os
from datetime import datetime

from . import config
from .universe import fetch_stock_universe
from .scanner import scan_universe
from .report_pdf import build_pdf
from .report_excel import append_candidates_to_tracker
from .telegram_bot import send_telegram_document


def main():
    now_ist = datetime.now(config.IST)
    run_label = now_ist.strftime("%A, %d %b %Y — %I:%M %p IST")
    print(f"Run: {run_label}")

    print("[1/4] Loading stock universe...")
    universe = fetch_stock_universe()

    print("[2/4] Scanning universe for 3-pillar momentum swing candidates...")
    candidates = scan_universe(universe)

    print("[3/4] Building PDF and updating the Excel tracker...")
    build_pdf(candidates, run_label, config.PDF_OUTPUT_PATH)
    if candidates:
        append_candidates_to_tracker(candidates, run_dt=now_ist)

    print("[4/4] Sending PDF and Excel tracker to Telegram (if configured)...")
    send_telegram_document(
        config.PDF_OUTPUT_PATH,
        f"📊 NSE Momentum Swing Scan — {run_label}\n{len(candidates)} candidates today. Not investment advice.",
    )
    if os.path.exists(config.TRACKER_XLSX_PATH):
        send_telegram_document(
            config.TRACKER_XLSX_PATH,
            f"📈 Master Tracker updated — {run_label}",
        )

    print("Done.")


if __name__ == "__main__":
    main()
