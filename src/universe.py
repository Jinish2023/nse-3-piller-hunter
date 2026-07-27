"""
Stock universe — tries to pull the live NSE 500 list first (free CSV, no
key). Falls back to a hardcoded liquid-stock list if that fetch fails
(NSE's site is flaky for scripted requests without a browser session).
"""
import io
import requests
import pandas as pd

NIFTY500_CSV_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"

FALLBACK_UNIVERSE = [
    "RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","HINDUNILVR","ITC","SBIN",
    "BHARTIARTL","KOTAKBANK","LT","AXISBANK","BAJFINANCE","ASIANPAINT","MARUTI",
    "SUNPHARMA","TITAN","ULTRACEMCO","WIPRO","NESTLEIND","HCLTECH","TATAMOTORS",
    "TATASTEEL","POWERGRID","NTPC","ONGC","M&M","ADANIENT","ADANIPORTS","JSWSTEEL",
    "GRASIM","BAJAJFINSV","INDUSINDBK","TECHM","DRREDDY","CIPLA","DIVISLAB",
    "EICHERMOT","HEROMOTOCO","BAJAJ-AUTO","BRITANNIA","COALINDIA","HINDALCO",
    "SHREECEM","UPL","APOLLOHOSP","BPCL","IOC","GAIL","VEDL","PIDILITIND","DABUR",
    "GODREJCP","MARICO","COLPAL","SIEMENS","ABB","HAVELLS","DLF","GODREJPROP",
    "OBEROIRLTY","PHOENIXLTD","INDIGO","IRCTC","ZOMATO","NYKAA","PAYTM",
    "POLICYBZR","TATAPOWER","TATACONSUM","AMBUJACEM","ACC","RAMCOCEM","JKCEMENT",
    "BANDHANBNK","FEDERALBNK","IDFCFIRSTB","PNB","BANKBARODA","CANBK","AUBANK",
    "CHOLAFIN","MUTHOOTFIN","SBICARD","PFC","RECLTD","IRFC","HUDCO","BEL","HAL",
    "BHEL","SAIL","NMDC","NATIONALUM","JINDALSTEL","APLAPOLLO","TRENT","ABFRL",
    "PAGEIND","RELAXO","BATAINDIA","VBL","UBL","GLENMARK","LUPIN","AUROPHARMA",
    "TORNTPHARM","ALKEM","ZYDUSLIFE","LAURUSLABS","BIOCON","IPCALAB","GRANULES",
    "SUZLON","INOXWIND","KPITTECH","PERSISTENT","COFORGE","LTIM","MPHASIS",
    "TATAELXSI","CYIENT","POLYCAB","KEI","CROMPTON","VOLTAS","WHIRLPOOL","DIXON",
    "AMBER","KAYNES","CGPOWER","SUNDARMFIN","MOTHERSON","BOSCHLTD","EXIDEIND",
    "MRF","APOLLOTYRE","BALKRISIND","ASHOKLEY","ESCORTS","TVSMOTOR","SONACOMS",
    "BHARATFORG","CUMMINSIND","THERMAX","ASTRAL","SUPREMEIND","JUBLFOOD",
    "DEVYANI","RADICO","EMAMILTD","KAJARIACER","DEEPAKNTR","PIIND","SRF",
    "AARTIIND","NAVINFLUOR","TATACHEM","GNFC","COROMANDEL","CHAMBLFERT",
    "MANAPPURAM","LICHSGFIN","CANFINHOME","IEX","MCX","CDSL","BSE","CAMS",
    "ANGELONE","MOTILALOFS","IIFL","JMFINANCIL","LODHA","NAUKRI","INDHOTEL",
    "PVRINOX","CONCOR","GMRINFRA","ADANIENSOL","ADANIGREEN","ADANIPOWER",
    "TORNTPOWER","IGL","MGL","PETRONET","GSPL","OIL","HINDPETRO","IDEA",
    "TATACOMM","LTTS","ZFCVINDIA","TIINDIA","SCHAEFFLER","BALRAMCHIN","EIDPARRY",
]


def fetch_stock_universe():
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(NIFTY500_CSV_URL, headers=headers, timeout=15)
        if resp.status_code == 200 and "Symbol" in resp.text:
            df = pd.read_csv(io.StringIO(resp.text))
            symbols = df["Symbol"].dropna().astype(str).str.strip().tolist()
            if len(symbols) > 100:
                print(f"  Loaded live NIFTY 500 list ({len(symbols)} symbols).")
                return symbols
    except Exception as e:
        print(f"  Live universe fetch failed ({e}), using fallback list.")
    print(f"  Using fallback universe ({len(FALLBACK_UNIVERSE)} symbols).")
    return FALLBACK_UNIVERSE
