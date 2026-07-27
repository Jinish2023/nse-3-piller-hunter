"""
Optional Telegram delivery. If the bot token / chat id aren't configured,
this just skips quietly — the PDF and Excel tracker are still generated
and left on disk for local use.
"""
import os
import requests

from . import config


def send_telegram_document(file_path, caption):
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print(f"  Telegram skipped for {file_path} — TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not configured.")
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendDocument"
    with open(file_path, "rb") as f:
        resp = requests.post(
            url,
            data={"chat_id": config.TELEGRAM_CHAT_ID, "caption": caption},
            files={"document": (os.path.basename(file_path), f)},
            timeout=60,
        )
    if resp.status_code == 200:
        print(f"  Telegram: sent {file_path}.")
    else:
        print(f"  Telegram send failed for {file_path}: {resp.status_code} — {resp.text[:200]}")
