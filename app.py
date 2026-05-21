from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import warnings

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

app = FastAPI(
    title="Trading Research API",
    description="Daily trading research API for sector, stock and trade research automation.",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE = {"daily_research": None, "created_at": None}
CACHE_MINUTES = 10

# -----------------------------
# Universe
# -----------------------------

sector_etfs = {
    "SPY": "Genel piyasa referansı",
    "QQQ": "Nasdaq / büyüme referansı",
    "XLK": "Teknoloji",
    "XLF": "Finans",
    "XLE": "Enerji",
    "XLV": "Sağlık",
    "XLY": "Tüketici döngüsel",
    "XLP": "Tüketici savunma",
    "XLI": "Sanayi",
    "XLU": "Kamu hizmetleri",
    "XLB": "Temel materyaller",
    "XLRE": "Gayrimenkul",
    "XLC": "İletişim hizmetleri",
}

sector_stock_universes = {
    "XLU": {
        "NEE": "NextEra Energy", "SO": "Southern Company", "DUK": "Duke Energy",
        "CEG": "Constellation Energy", "SRE": "Sempra", "AEP": "American Electric Power",
        "EXC": "Exelon", "PEG": "Public Service Enterprise Group", "XEL": "Xcel Energy",
        "ED": "Consolidated Edison", "WEC": "WEC Energy", "D": "Dominion Energy",
        "AWK": "American Water Works",
    },
    "XLV": {
        "LLY": "Eli Lilly", "JNJ": "Johnson & Johnson", "UNH": "UnitedHealth",
        "ABBV": "AbbVie", "MRK": "Merck", "TMO": "Thermo Fisher",
        "ABT": "Abbott", "ISRG": "Intuitive Surgical", "AMGN": "Amgen",
        "GILD": "Gilead", "PFE": "Pfizer", "BMY": "Bristol Myers",
    },
    "XLC": {
        "GOOGL": "Alphabet A", "GOOG": "Alphabet C", "META": "Meta Platforms",
        "NFLX": "Netflix", "TMUS": "T-Mobile", "DIS": "Disney",
        "CMCSA": "Comcast", "VZ": "Verizon", "T": "AT&T",
    },
    "XLE": {
        "XOM": "Exxon Mobil", "CVX": "Chevron", "COP": "ConocoPhillips",
        "EOG": "EOG Resources", "SLB": "Schlumberger", "MPC": "Marathon Petroleum",
        "PSX": "Phillips 66", "VLO": "Valero", "OXY": "Occidental Petroleum",
    },
    "XLK": {
        "MSFT": "Microsoft", "AAPL": "Apple", "NVDA": "NVIDIA",
        "AVGO": "Broadcom", "ORCL": "Oracle", "CRM": "Salesforce",
        "AMD": "AMD", "ADBE": "Adobe", "CSCO": "Cisco",
        "ACN": "Accenture", "IBM": "IBM", "QCOM": "Qualcomm",
    },
    "XLF": {
        "JPM": "JPMorgan Chase", "BAC": "Bank of America", "WFC": "Wells Fargo",
        "GS": "Goldman Sachs", "MS": "Morgan Stanley", "AXP": "American Express",
        "C": "Citigroup", "BLK": "BlackRock", "SCHW": "Charles Schwab",
        "PGR": "Progressive", "CB": "Chubb",
    },
    "XLI": {
        "GE": "GE Aerospace", "CAT": "Caterpillar", "RTX": "RTX",
        "HON": "Honeywell", "UNP": "Union Pacific", "UPS": "UPS",
        "BA": "Boeing", "LMT": "Lockheed Martin", "DE": "Deere", "ETN": "Eaton",
    },
    "XLY": {
        "AMZN": "Amazon", "TSLA": "Tesla", "HD": "Home Depot",
        "MCD": "McDonald's", "NKE": "Nike", "SBUX": "Starbucks",
        "LOW": "Lowe's", "BKNG": "Booking", "TJX": "TJX",
    },
    "XLP": {
        "WMT": "Walmart", "COST": "Costco", "PG": "Procter & Gamble",
        "KO": "Coca-Cola", "PEP": "PepsiCo", "PM": "Philip Morris",
        "MO": "Altria", "MDLZ": "Mondelez", "CL": "Colgate-Palmolive",
    },
    "XLB": {
        "LIN": "Linde", "SHW": "Sherwin-Williams", "APD": "Air Products",
        "ECL": "Ecolab", "FCX": "Freeport-McMoRan", "NEM": "Newmont",
        "DOW": "Dow", "DD": "DuPont",
    },
    "XLRE": {
        "PLD": "Prologis", "AMT": "American Tower", "EQIX": "Equinix",
        "WELL": "Welltower", "SPG": "Simon Property", "PSA": "Public Storage",
        "O": "Realty Income", "DLR": "Digital Realty",
    },
}

# -----------------------------
# Helpers
# -----------------------------

def safe_round(value, digits=2):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return round(float(value), digits)


def to_float(value):
    if isinstance(value, pd.Series):
        return float(value.iloc[0])
    if isinstance(value, np.ndarray):
        return float(value.flatten()[0])
    return float(value)


def normalize_df(df):
    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        # yfinance can return MultiIndex even for one ticker.
        df.columns = df.columns.get_level_values(0)

    needed = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        return pd.DataFrame()

    out = df[needed].copy().dropna()
    return out


def get_single_ticker_data(symbol, period="1mo", interval="1d"):
    # Method 1: yf.download
    try:
        df = yf.download(
            tickers=symbol,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        df = normalize_df(df)
        if len(df) >= 2:
            return df
    except Exception:
        pass

    # Method 2: Ticker.history fallback
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=False)
        df = normalize_df(df)
        if len(df) >= 2:
            return df
    except Exception:
        pass

    return pd.DataFrame()


def change_pct_from_df(df):
    latest = df.iloc[-1]
    previous = df.iloc[-2]
    latest_close = to_float(latest["Close"])
    previous_close = to_float(previous["Close"])
    change_pct = ((latest_close - previous_close) / previous_close) * 100
    return {
        "date": str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(df.index[-1]),
        "latest_close": latest_close,
        "previous_close": previous_close,
        "day_high": to_float(latest["High"]),
        "day_low": to_float(latest["Low"]),
        "volume": int(to_float(latest["Volume"])),
        "change_pct": change_pct,
    }


def get_benchmark_data(primary_symbol, fallback_symbols, period="1mo", interval="1d"):
    for ticker in [primary_symbol] + fallback_symbols:
        df = get_single_ticker_data(ticker, period=period, interval=interval)
        if len(df) >= 2:
            info = change_pct_from_df(df)
            info.update({
                "requested_symbol": primary_symbol,
                "used_symbol": ticker,
                "status": "ok",
            })
            return info

    return {
        "requested_symbol": primary_symbol,
        "used_symbol": None,
        "change_pct": None,
        "status": "error",
    }


def relative_status(value, benchmark):
    if benchmark is None:
        return "Referans veri yok"
    if value > benchmark:
        return "Daha güçlü"
    if value < benchmark:
        return "Daha zayıf"
    return "Nötr"


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_atr(df, period=14):
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(period).mean()

# -----------------------------
# Research engine
# -----------------------------

def scan_sectors():
    spy_benchmark = get_benchmark_data("SPY", ["VOO", "IVV", "^GSPC"], period="1mo", interval="1d")
    qqq_benchmark = get_benchmark_data("QQQ", ["QQQM"], period="1mo", interval="1d")

    spy_change = spy_benchmark["change_pct"]
    qqq_change = qqq_benchmark["change_pct"]

    rows = []
    errors = []

    for symbol, sector_name in sector_etfs.items():
        try:
            df = get_single_ticker_data(symbol, period="1mo", interval="1d")
            if len(df) < 2:
                errors.append({"symbol": symbol, "error": "Yeterli veri yok"})
                continue

            info = change_pct_from_df(df)
            row = {
                "symbol": symbol,
                "sector": sector_name,
                "date": info["date"],
                "latest_close": info["latest_close"],
                "previous_close": info["previous_close"],
                "day_high": info["day_high"],
                "day_low": info["day_low"],
                "change_pct": info["change_pct"],
                "volume": info["volume"],
                "vs_spy": relative_status(info["change_pct"], spy_change),
                "vs_qqq": relative_status(info["change_pct"], qqq_change),
            }
            rows.append(row)
        except Exception as e:
            errors.append({"symbol": symbol, "error": str(e)})

    if not rows:
        raise RuntimeError(f"Sektör verisi alınamadı. Hatalar: {errors}")

    sector_scan = sorted(rows, key=lambda x: x["change_pct"], reverse=True)

    sectors_only = [
        r for r in sector_scan
        if r["symbol"] not in ["SPY", "QQQ"] and r["symbol"] in sector_stock_universes
    ]

    if not sectors_only:
        raise RuntimeError("Hisse evreni tanımlı sektör bulunamadı.")

    selected_sector = sectors_only[0]

    return {
        "sector_scan": [
            {
                **r,
                "latest_close": safe_round(r["latest_close"]),
                "previous_close": safe_round(r["previous_close"]),
                "day_high": safe_round(r["day_high"]),
                "day_low": safe_round(r["day_low"]),
                "change_pct": safe_round(r["change_pct"]),
            }
            for r in sector_scan
        ],
        "sector_errors": errors,
        "spy_benchmark": {
            "requested_symbol": "SPY",
            "used_symbol": spy_benchmark["used_symbol"],
            "change_pct": safe_round(spy_change),
            "status": spy_benchmark["status"],
        },
        "qqq_benchmark": {
            "requested_symbol": "QQQ",
            "used_symbol": qqq_benchmark["used_symbol"],
            "change_pct": safe_round(qqq_change),
            "status": qqq_benchmark["status"],
        },
        "selected_sector": {
            "symbol": selected_sector["symbol"],
            "name": selected_sector["sector"],
            "change_pct": safe_round(selected_sector["change_pct"]),
        },
    }


def scan_stocks_for_sector(sector_symbol, spy_change_pct, sector_change_pct):
    universe = sector_stock_universes[sector_symbol]
    rows = []
    errors = []

    for symbol, company_name in universe.items():
        try:
            df = get_single_ticker_data(symbol, period="3mo", interval="1d")
            if len(df) < 50:
                errors.append({"symbol": symbol, "error": "Yeterli veri yok"})
                continue

            close = df["Close"]
            volume = df["Volume"]

            latest_close = to_float(close.iloc[-1])
            previous_close = to_float(close.iloc[-2])
            close_5d_ago = to_float(close.iloc[-6])
            close_20d_ago = to_float(close.iloc[-21])

            change_1d = ((latest_close - previous_close) / previous_close) * 100
            change_5d = ((latest_close - close_5d_ago) / close_5d_ago) * 100
            change_20d = ((latest_close - close_20d_ago) / close_20d_ago) * 100

            sma20 = to_float(close.tail(20).mean())
            sma50 = to_float(close.tail(50).mean())

            latest_volume = to_float(volume.iloc[-1])
            avg_volume_20 = to_float(volume.tail(20).mean())
            relative_volume = latest_volume / avg_volume_20 if avg_volume_20 > 0 else None

            above_sma20 = latest_close > sma20
            above_sma50 = latest_close > sma50

            vs_spy = relative_status(change_1d, spy_change_pct)
            vs_sector = relative_status(change_1d, sector_change_pct)

            score = 0
            if vs_spy == "Daha güçlü":
                score += 20
            if vs_sector == "Daha güçlü":
                score += 20
            if change_5d > 0:
                score += 15
            if change_20d > 0:
                score += 15
            if above_sma20:
                score += 15
            if above_sma50:
                score += 10
            if relative_volume is not None and relative_volume >= 1:
                score += 5

            rows.append({
                "symbol": symbol,
                "name": company_name,
                "date": str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(df.index[-1]),
                "latest_close": latest_close,
                "change_1d_pct": change_1d,
                "change_5d_pct": change_5d,
                "change_20d_pct": change_20d,
                "vs_spy_1d": vs_spy,
                "vs_sector_1d": vs_sector,
                "above_sma20": above_sma20,
                "above_sma50": above_sma50,
                "relative_volume": relative_volume,
                "research_score": score,
            })

        except Exception as e:
            errors.append({"symbol": symbol, "error": str(e)})

    if not rows:
        raise RuntimeError(f"Hisse tarama verisi alınamadı. Hatalar: {errors}")

    stock_scan = sorted(rows, key=lambda x: x["research_score"], reverse=True)

    clean_scan = []
    for r in stock_scan:
        clean_scan.append({
            **r,
            "latest_close": safe_round(r["latest_close"]),
            "change_1d_pct": safe_round(r["change_1d_pct"]),
            "change_5d_pct": safe_round(r["change_5d_pct"]),
            "change_20d_pct": safe_round(r["change_20d_pct"]),
            "above_sma20": bool(r["above_sma20"]),
            "above_sma50": bool(r["above_sma50"]),
            "relative_volume": safe_round(r["relative_volume"]),
            "research_score": int(r["research_score"]),
        })

    return {
        "stock_scan": clean_scan,
        "stock_errors": errors,
        "final_candidate": clean_scan[0],
    }


def prepare_final_candidate(symbol, name):
    df = get_single_ticker_data(symbol, period="1y", interval="1d")
    if len(df) < 50:
        raise RuntimeError(f"{symbol} için yeterli final aday verisi alınamadı.")

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    latest_close = to_float(close.iloc[-1])
    previous_close = to_float(close.iloc[-2])
    day_high = to_float(high.iloc[-1])
    day_low = to_float(low.iloc[-1])

    close_5d_ago = to_float(close.iloc[-6])
    close_20d_ago = to_float(close.iloc[-21])

    ema20 = to_float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = to_float(close.ewm(span=50, adjust=False).mean().iloc[-1])
    ema200 = to_float(close.ewm(span=200, adjust=False).mean().iloc[-1])

    rsi14 = to_float(calculate_rsi(close, 14).iloc[-1])
    atr14 = to_float(calculate_atr(df, 14).iloc[-1])

    latest_volume = to_float(volume.iloc[-1])
    avg_volume_20 = to_float(volume.tail(20).mean())
    relative_volume = latest_volume / avg_volume_20 if avg_volume_20 > 0 else None

    support_10d = to_float(low.tail(10).min())
    support_20d = to_float(low.tail(20).min())
    support_50d = to_float(low.tail(50).min())

    resistance_10d = to_float(high.tail(10).max())
    resistance_20d = to_float(high.tail(20).max())
    resistance_50d = to_float(high.tail(50).max())
    resistance_6m = to_float(high.tail(126).max())
    resistance_1y = to_float(high.max())

    change_1d = ((latest_close - previous_close) / previous_close) * 100
    change_5d = ((latest_close - close_5d_ago) / close_5d_ago) * 100
    change_20d = ((latest_close - close_20d_ago) / close_20d_ago) * 100

    trend_status = [
        "EMA20 üstü" if latest_close > ema20 else "EMA20 altı",
        "EMA50 üstü" if latest_close > ema50 else "EMA50 altı",
        "EMA200 üstü" if latest_close > ema200 else "EMA200 altı",
    ]

    if rsi14 >= 70:
        rsi_comment = "RSI güçlü fakat aşırı ısınma riski var"
    elif rsi14 >= 60:
        rsi_comment = "RSI güçlü momentum bölgesinde"
    elif rsi14 >= 40:
        rsi_comment = "RSI nötr bölgede"
    else:
        rsi_comment = "RSI zayıf momentum bölgesinde"

    if relative_volume is None:
        volume_comment = "Hacim verisi sınırlı"
    elif relative_volume >= 1.2:
        volume_comment = "Hacim ortalamanın belirgin üstünde"
    elif relative_volume >= 1.0:
        volume_comment = "Hacim ortalama civarı / hafif üstü"
    else:
        volume_comment = "Hacim ortalamanın altında, teyit zayıf"

    entry_reference = resistance_20d
    stop_reference = support_10d
    risk_points = entry_reference - stop_reference

    target_candidates = [resistance_50d, resistance_6m, resistance_1y]
    valid_targets = [x for x in target_candidates if x > entry_reference]

    if valid_targets and risk_points > 0:
        target_1 = min(valid_targets)
        reward_points = target_1 - entry_reference
        risk_reward_value = reward_points / risk_points
        target_text = f"{target_1:.2f}"
        reward_text = f"{reward_points:.2f}"
        rr_text = f"{risk_reward_value:.2f}R"
    else:
        reward_points = None
        risk_reward_value = None
        target_text = "Veri eksik: giriş bölgesinin üzerinde 50G / 6A / 1Y direnç bulunamadı"
        reward_text = "Veri eksik"
        rr_text = "Veri eksik"

    if risk_reward_value is None:
        trade_status = "not_suitable_data_missing"
        trade_decision = "Risk/ödül hesaplanamadığı için aktif işlem planı uygun değil."
    elif risk_reward_value < 1:
        trade_status = "invalid_rr_under_1r"
        trade_decision = "Risk/ödül 1R altında; işlem planı geçersiz."
    elif risk_reward_value < 1.5:
        trade_status = "not_suitable_weak_rr"
        trade_decision = "Risk/ödül 1.5R altında; işlem planı zayıf / uygun değil."
    else:
        trade_status = "watchlist_candidate"
        trade_decision = "Risk/ödül izlenebilir; yine de tetikleyici, haber riski ve insan onayı gerekir."

    return {
        "symbol": symbol,
        "name": name,
        "date": str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(df.index[-1]),
        "latest_close": safe_round(latest_close),
        "previous_close": safe_round(previous_close),
        "day_high": safe_round(day_high),
        "day_low": safe_round(day_low),
        "change_1d_pct": safe_round(change_1d),
        "change_5d_pct": safe_round(change_5d),
        "change_20d_pct": safe_round(change_20d),
        "ema20": safe_round(ema20),
        "ema50": safe_round(ema50),
        "ema200": safe_round(ema200),
        "trend_status": " / ".join(trend_status),
        "rsi14": safe_round(rsi14),
        "rsi_comment": rsi_comment,
        "atr14": safe_round(atr14),
        "latest_volume": int(latest_volume),
        "avg_volume_20": int(avg_volume_20),
        "relative_volume": safe_round(relative_volume),
        "volume_comment": volume_comment,
        "support_10d": safe_round(support_10d),
        "support_20d": safe_round(support_20d),
        "support_50d": safe_round(support_50d),
        "resistance_10d": safe_round(resistance_10d),
        "resistance_20d": safe_round(resistance_20d),
        "resistance_50d": safe_round(resistance_50d),
        "resistance_6m": safe_round(resistance_6m),
        "resistance_1y": safe_round(resistance_1y),
        "entry_reference": safe_round(entry_reference),
        "stop_reference": safe_round(stop_reference),
        "target_1_reference": target_text,
        "risk_points": safe_round(risk_points),
        "reward_points": reward_text,
        "risk_reward": rr_text,
        "trade_status": trade_status,
        "trade_decision": trade_decision,
    }


def build_agent_prompt(selected_sector, final_data):
    return f"""
Aşağıdaki otomatik Daily Research Agent v1 çıktısına göre sabit 18 başlıklı TRADING RESEARCH RAPORU oluştur.

Bu çıktı yatırım tavsiyesi değildir.
Canlı emir gönderme.
Kesin al/sat önerisi verme.
Risk/ödül filtresini uygula.
Net trigger, net limit ve net stop emir fiyatı uydurma.
Destek/direnç bölgelerini referans olarak kullan.
Eksik veri varsa 17. Eksik Veri bölümünde listele.

ÖN FİLTRE ÖZETİ

Seçilen sektör: {selected_sector["symbol"]} — {selected_sector["name"]}
Sektör günlük değişim: {selected_sector["change_pct"]}%

Final research adayı: {final_data["symbol"]} — {final_data["name"]}

VERİLER

Sembol: {final_data["symbol"]}
Şirket: {final_data["name"]}
Varlık tipi: ABD hisse senedi
Zaman dilimi: Swing

Güncel fiyat: {final_data["latest_close"]}
Önceki kapanış: {final_data["previous_close"]}
Günün yüksek seviyesi: {final_data["day_high"]}
Günün düşük seviyesi: {final_data["day_low"]}

1G değişim: {final_data["change_1d_pct"]}%
5G değişim: {final_data["change_5d_pct"]}%
20G değişim: {final_data["change_20d_pct"]}%

Trend durumu: {final_data["trend_status"]}
EMA20: {final_data["ema20"]}
EMA50: {final_data["ema50"]}
EMA200: {final_data["ema200"]}

RSI14: {final_data["rsi14"]}
RSI yorumu: {final_data["rsi_comment"]}

ATR14: {final_data["atr14"]}

Son hacim: {final_data["latest_volume"]}
20G ortalama hacim: {final_data["avg_volume_20"]}
Relative volume: {final_data["relative_volume"]}x
Hacim yorumu: {final_data["volume_comment"]}

Destek seviyeleri:
- 10G destek: {final_data["support_10d"]}
- 20G destek: {final_data["support_20d"]}
- 50G destek: {final_data["support_50d"]}

Direnç seviyeleri:
- 10G direnç: {final_data["resistance_10d"]}
- 20G direnç: {final_data["resistance_20d"]}
- 50G direnç: {final_data["resistance_50d"]}
- 6A direnç: {final_data["resistance_6m"]}
- 1Y direnç: {final_data["resistance_1y"]}

Olası teknik senaryo:
- Breakout giriş referans bölgesi: {final_data["entry_reference"]} üzeri kabul / retest
- Stop referans bölgesi: {final_data["stop_reference"]} altı
- Hedef 1 referans bölgesi: {final_data["target_1_reference"]}
- Yaklaşık risk: {final_data["risk_points"]}
- Yaklaşık ödül: {final_data["reward_points"]}
- Yaklaşık risk/ödül: {final_data["risk_reward"]}

Sermaye: 1000$
İşlem başı risk: %10
Kaldıraç / marjin: Yok
Kesirli işlem: Var

Haber / bilanço riski:
Veri eksik. Güncel şirket özel haber ve yaklaşan bilanço tarihi ayrıca kontrol edilmeli.

Kurallar:
- 18 başlıklı formatı bozma.
- Long emir tipi için Buy stop-limit kullan.
- Tetikleyici bölge yaz ama net trigger / net limit / net stop fiyatı uydurma.
- Risk/ödül 1.5R altında ise işlem planı zayıf / uygun değil yaz.
- Risk/ödül hesaplanamıyorsa işlem planı için veri eksik yaz.
- Tetikleyici gerçekleşmeden işlem uygun deme.
- İnsan onayı gerekli.
"""


def run_daily_research():
    sector_result = scan_sectors()
    selected_sector = sector_result["selected_sector"]

    spy_change = sector_result["spy_benchmark"]["change_pct"]
    if spy_change is None:
        spy_change = 0

    stock_result = scan_stocks_for_sector(
        selected_sector["symbol"],
        spy_change,
        selected_sector["change_pct"],
    )

    final_candidate = stock_result["final_candidate"]
    final_data = prepare_final_candidate(final_candidate["symbol"], final_candidate["name"])
    agent_prompt = build_agent_prompt(selected_sector, final_data)

    return {
        "status": "ok",
        "mode": "research_only",
        "live_orders": False,
        "human_approval_required": True,
        "created_at": datetime.utcnow().isoformat(),
        "summary": {
            "selected_sector": selected_sector,
            "final_candidate": {
                "symbol": final_data["symbol"],
                "name": final_data["name"],
            },
            "trade_status": final_data["trade_status"],
            "trade_decision": final_data["trade_decision"],
            "risk_reward": final_data["risk_reward"],
            "target_1": final_data["target_1_reference"],
        },
        "benchmarks": {
            "spy": sector_result["spy_benchmark"],
            "qqq": sector_result["qqq_benchmark"],
        },
        "sector_scan": sector_result["sector_scan"],
        "sector_errors": sector_result["sector_errors"],
        "stock_scan": stock_result["stock_scan"],
        "stock_errors": stock_result["stock_errors"],
        "final_candidate_data": final_data,
        "agent_prompt": agent_prompt,
    }

# -----------------------------
# API endpoints
# -----------------------------

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Trading Research API is running",
        "time": datetime.utcnow().isoformat(),
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "Trading Research API is healthy",
        "time": datetime.utcnow().isoformat(),
    }


@app.get("/yf-test")
def yf_test():
    test_symbols = ["SPY", "VOO", "IVV", "^GSPC", "QQQ", "XLU", "XLV", "D", "XEL"]
    results = []

    for symbol in test_symbols:
        try:
            df = get_single_ticker_data(symbol, period="1mo", interval="1d")
            results.append({
                "symbol": symbol,
                "rows": len(df),
                "columns": list(df.columns) if len(df) > 0 else [],
                "last_date": str(df.index[-1]) if len(df) > 0 else None,
                "status": "ok" if len(df) >= 2 else "not_enough_data",
            })
        except Exception as e:
            results.append({
                "symbol": symbol,
                "status": "error",
                "error": str(e),
            })

    return {
        "status": "ok",
        "message": "yfinance test completed",
        "results": results,
        "time": datetime.utcnow().isoformat(),
    }


@app.get("/daily-research")
def daily_research(refresh: bool = False):
    now = datetime.utcnow()

    if (
        not refresh
        and CACHE["daily_research"] is not None
        and CACHE["created_at"] is not None
        and now - CACHE["created_at"] < timedelta(minutes=CACHE_MINUTES)
    ):
        cached = CACHE["daily_research"]
        cached["cache"] = "hit"
        return cached

    try:
        result = run_daily_research()
        result["cache"] = "miss"
        CACHE["daily_research"] = result
        CACHE["created_at"] = now
        return result

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "mode": "research_only",
            "live_orders": False,
            "human_approval_required": True,
            "time": datetime.utcnow().isoformat(),
        }
