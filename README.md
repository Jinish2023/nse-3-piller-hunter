# NSE Momentum Swing Scanner — 3-Pillar Daily Screen

A pure **technical** scanner for NSE stocks, built around the Momentum Swing
Trading Strategy (RSI / EMA44 / EMA200 / Price Action / Volume). No news
feeds, no LLM, no AI narrative — every number comes from real daily OHLCV
data pulled from Yahoo Finance.

## What it does

1. Loads the NIFTY 500 list (falls back to a hardcoded liquid-stock list).
2. Downloads ~15 months of daily OHLCV per stock via `yfinance`.
3. Runs every stock through the **Three-Pillar Framework**, evaluated on the
   daily chart:
   - **Pillar 1 (Trend):** price above EMA200 AND above a rising daily trendline
   - **Pillar 2 (Momentum):** RSI 40–70 & rising, EMA44 sloping up, price above
     EMA44, volume above its 20-day average
   - **Pillar 3 (Volume, partial):** an up day with volume ≥ 1.2x the 20-day
     average
   All three must pass — two out of three is not enough (matches the strategy).
4. Computes entry / stop-loss / target levels from real price structure
   (recent breakout high, recent pullback low, ATR-scaled buffers).
5. Builds a PDF report and appends every candidate to a persistent Excel
   tracker (`master_tracker.xlsx`), with de-duplication so the same live
   setup doesn't create a new row every day.
6. Optionally sends both files to a Telegram chat.

**What's intentionally NOT included:** the 2–3-red-candle / 1st-green-candle
price-action trigger, true 4H momentum monitoring, and 1H precision entry —
these genuinely need intraday bars, which aren't reliably available for free
NSE data. See the code comments in `src/strategy.py` for exactly where each
piece of the strategy maps (or doesn't) onto daily bars.

## Project structure

```
nse-momentum-scanner/
├── .github/workflows/scan.yml   # scheduled GitHub Actions run
├── src/
│   ├── config.py                # env vars + tunable constants
│   ├── universe.py               # stock list (NIFTY 500 + fallback)
│   ├── indicators.py             # EMA44/EMA200/RSI/ATR + trendline detector
│   ├── strategy.py               # the 3-pillar gate + entry/stop/target math
│   ├── scanner.py                # yfinance download loop
│   ├── report_pdf.py             # PDF report builder
│   ├── report_excel.py           # Excel tracker (append + de-dup)
│   ├── telegram_bot.py           # optional Telegram delivery
│   └── main.py                   # orchestration
├── run.py                        # entry point: python run.py
├── requirements.txt
├── .env.example
└── master_tracker.xlsx           # created on first run, committed by CI
```

## Run it locally

```bash
git clone <your-repo-url>
cd nse-momentum-scanner
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

This produces `breakout_scan_report.pdf` and `master_tracker.xlsx` in the
repo root. Telegram delivery is skipped automatically if you haven't set
`TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` (see `.env.example` — for local
runs, just `export` them or use a tool like `python-dotenv`).

## Step-by-step: setting this up on GitHub with a scheduled run

1. **Create the repo**
   - On GitHub, click **New repository** → name it (e.g. `nse-momentum-scanner`)
     → keep it **Private** if you don't want your setup public → **Create repository**.

2. **Push this code**
   ```bash
   cd nse-momentum-scanner
   git init
   git add .
   git commit -m "Initial commit: 3-pillar momentum swing scanner"
   git branch -M main
   git remote add origin https://github.com/<your-username>/nse-momentum-scanner.git
   git push -u origin main
   ```

3. **(Optional) Set up Telegram delivery**
   - Message **@BotFather** on Telegram → `/newbot` → follow the prompts →
     copy the **bot token** it gives you.
   - Message your new bot once (anything), then visit
     `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser and
     find `"chat":{"id": ...}` — that number is your **chat ID**.
   - Skip this step entirely if you just want the PDF/Excel as workflow
     artifacts / committed files — the scanner runs fine without Telegram.

4. **Add the secrets to GitHub**
   - In your repo: **Settings → Secrets and variables → Actions → New
     repository secret**.
   - Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (only if you did step 3).

5. **Enable the scheduled workflow**
   - The workflow file is already at `.github/workflows/scan.yml` — GitHub
     picks it up automatically once it's on the `main` branch.
   - It's scheduled for **15:45 IST, Monday–Friday** (after NSE market
     close). Edit the `cron:` line in that file if you want a different time
     — cron times are in UTC.
   - GitHub Actions schedules can lag by a few minutes at busy times; that's
     normal.

6. **Test it manually before waiting for the schedule**
   - Go to your repo's **Actions** tab → select **NSE Momentum Swing Scan**
     → click **Run workflow** → **Run workflow** (this uses the
     `workflow_dispatch` trigger already included).
   - Watch the run log. On success, `master_tracker.xlsx` will be committed
     back to the repo automatically, and (if configured) both files will
     land in your Telegram chat.

7. **Ongoing use**
   - Every scheduled run appends new candidates to `master_tracker.xlsx` and
     pushes the update back to your repo — so your trade journal builds up
     automatically over time, viewable directly on GitHub or by pulling the
     repo locally.

## Disclaimer

Educational / research tool only. Not investment advice. Verify
independently and consult a SEBI-registered advisor before trading.
