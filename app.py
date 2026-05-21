from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore")

app = FastAPI(
    title="Trading Research API",
    description="Daily trading research API for sector, stock and trade research automation.",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE = {
    "daily_research": None,
    "created_at": None
}

CACHE_MINUTES = 10


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
        "NEE": "NextEra Energy",
        "SO": "Southern Company",
        "DUK": "Duke Energy",
        "CEG": "Constellation Energy",
        "SRE": "Sempra",
        "AEP": "American Electric Power",
        "EXC": "Exelon",
        "PEG": "Public Service Enterprise Group",
        "XEL": "Xcel Energy",
        "ED": "Consolidated Edison",
        "WEC": "WEC Energy",
        "D": "Dominion Energy",
        "AWK": "American Water Works",
    },
    "XLV": {
        "LLY": "Eli Lilly",
        "JNJ": "Johnson & Johnson",
        "UNH": "UnitedHealth",
        "ABBV": "AbbVie",
        "MRK": "Merck",
        "TMO": "Thermo Fisher",
        "ABT": "Abbott",
        "ISRG": "Intuitive Surgical",
        "AMGN": "Amgen",
        "GILD": "Gilead",
        "PFE": "Pfizer",
        "BMY": "Bristol Myers",
    },
    "XLC": {
        "GOOGL": "Alphabet A",
        "GOOG": "Alphabet C",
        "META": "Meta Platforms",
        "NFLX": "Netflix",
        "TMUS": "T-Mobile",
        "DIS": "Disney",
        "CMCSA": "Comcast",
        "VZ": "Verizon",
        "T": "AT&T",
    },
    "XLE": {
        "XOM": "Exxon Mobil",
        "CVX": "Chevron",
        "COP": "ConocoPhillips",
        "EOG": "EOG Resources",
        "SLB": "Schlumberger",
        "MPC": "Marathon Petroleum",
        "PSX": "Phillips 66",
        "VLO": "Valero",
        "OXY": "Occidental Petroleum",
    },
    "XLK": {
        "MSFT": "Microsoft",
        "AAPL": "Apple",
        "NVDA": "NVIDIA",
        "AVGO": "Broadcom",
        "ORCL": "Oracle",
        "CRM": "Salesforce",
        "AMD": "AMD",
        "ADBE": "Adobe",
        "CSCO": "Cisco",
        "ACN": "Accenture",
        "IBM": "IBM",
        "QCOM": "Qualcomm",
    },
    "XLF": {
        "JPM": "JPMorgan Chase",
        "BAC": "Bank of America",
        "WFC": "Wells Fargo",
        "GS": "Goldman Sachs",
        "MS": "Morgan Stanley",
        "AXP": "American Express",
        "C": "Citigroup",
        "BLK": "BlackRock",
        "SCHW": "Charles Schwab",
        "PGR": "Progressive",
        "CB": "Chubb",
    },
    "XLI": {
        "GE": "GE Aerospace",
        "CAT": "Caterpillar",
        "RTX": "RTX",
        "HON": "Honeywell",
        "UNP": "Union Pacific",
        "UPS": "UPS",
        "BA": "Boeing",
        "LMT": "Lockheed Martin",
        "DE": "Deere",
        "ETN": "Eaton",
    },
    "XLY": {
        "AMZN": "Amazon",
        "TSLA": "Tesla",
        "HD": "Home Depot",
        "MCD": "McDonald's",
        "NKE": "Nike",
        "SBUX": "Starbucks",
        "LOW": "Lowe's",
        "BKNG": "Booking",
        "TJX": "TJX",
    },
    "XLP": {
        "WMT": "Walmart",
        "COST": "Costco",
        "PG": "Procter & Gamble",
        "KO": "Coca-Cola",
        "PEP": "PepsiCo",
        "PM": "Philip Morris",
        "MO": "Altria",
        "MDLZ": "Mondelez",
        "CL": "Colgate-Palmolive",
    },
    "XLB": {
        "LIN": "Linde",
        "SHW": "Sherwin-Williams",
        "APD": "Air Products",
        "ECL": "Ecolab",
        "FCX": "Freeport-McMoRan",
        "NEM": "Newmont",
        "DOW": "Dow",
        "DD": "DuPont",
    },
    "XLRE": {
        "PLD": "Prologis",
        "AMT": "American Tower",
        "EQIX": "Equinix",
        "WELL": "Welltower",
        "SPG": "Simon Property",
        "PSA": "Public Storage",
        "O": "Realty Income",
        "DLR": "Digital Realty",
    },
}


def to_float(value):
    if isinstance(value, pd.Series):
        return float(value.iloc[0])
    if isinstance(value, np.ndarray):
        return float(value.flatten()[0])
    return float(value)


def get_single_ticker_data(symbol, period="6mo", interval="1d"):
    df = yf.download(
        tickers=symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False
    ).dropna()

    if isinstance(df.columns, pd.MultiIndex):
        if symbol in df.columns.get_level_values(-1):
            df = df.xs(symbol, axis=1, level=-1)
        else:
            df.columns = df.columns.get_level_values(0)

    return df.dropna()


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


def relative_status(value, benchmark):
    if value > benchmark:
        return "Daha güçlü"
    if value < benchmark:
        return "Daha zayıf"
    return "Nötr"


def safe_round(value, digits=2):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if pd.isna(value):
        return None
    return round(float(value), digits)


def scan_sectors():
    rows = []

    for symbol, sector_name in sector_etfs.items():
        try:
            df = get_single_ticker_data(symbol, period="7d", interval="1d")

            if len(df) < 2:
                rows.append({"symbol": symbol, "sector": sector_name, "error": "Yeterli veri yok"})
                continue

            latest = df.iloc[-1]
            previous = df.iloc[-2]

            latest_close = to_float(latest["Close"])
            previous_close = to_float(previous["Close"])
            day_high = to_float(latest["High"])
            day_low = to_float(latest["Low"])
            volume = int(to_float(latest["Volume"]))

            change = latest_close - previous_close
            change_pct = (change / previous_close) * 100

            rows.append({
                "symbol": symbol,
                "sector": sector_name,
                "date": df.index[-1].strftime("%Y-%m-%d"),
                "latest_close": latest_close,
                "previous_close": previous_close,
                "day_high": day_high,
                "day_low": day_low,
                "change": change,
                "change_pct": change_pct,
                "volume": volume,
                "error": None
            })

        except Exception as e:
            rows.append({"symbol": symbol, "sector": sector_name, "error": str(e)})

    df = pd.DataFrame(rows)
    clean = df[df["error"].isna()].copy()

    if clean.empty:
        raise RuntimeError("Sektör verisi alınamadı.")

    spy_change = clean.loc[clean["symbol"] == "SPY", "change_pct"].iloc[0]
    qqq_change = clean.loc[clean["symbol"] == "QQQ", "change_pct"].iloc[0]

    clean["vs_spy"] = clean["change_pct"].apply(lambda x: relative_status(x, spy_change))
    clean["vs_qqq"] = clean["change_pct"].apply(lambda x: relative_status(x, qqq_change))

    clean = clean.sort_values("change_pct", ascending=False)

    sector_scan = []
    for _, row in clean.iterrows():
        sector_scan.append({
            "symbol": row["symbol"],
            "sector": row["sector"],
            "date": row["date"],
            "latest_close": safe_round(row["latest_close"]),
            "previous_close": safe_round(row["previous_close"]),
            "day_high": safe_round(row["day_high"]),
            "day_low": safe_round(row["day_low"]),
            "change_pct": safe_round(row["change_pct"]),
            "volume": int(row["volume"]),
            "vs_spy": row["vs_spy"],
            "vs_qqq": row["vs_qqq"]
        })

    sectors_only = clean[
        (~clean["symbol"].isin(["SPY", "QQQ"])) &
        (clean["symbol"].isin(sector_stock_universes.keys()))
    ].copy()

    top_sector = sectors_only.sort_values("change_pct", ascending=False).iloc[0]

    return {
        "sector_scan": sector_scan,
        "spy_change_pct": safe_round(spy_change),
        "qqq_change_pct": safe_round(qqq_change),
        "selected_sector": {
            "symbol": top_sector["symbol"],
            "name": top_sector["sector"],
            "change_pct": safe_round(top_sector["change_pct"])
        }
    }


def scan_stocks_for_sector(sector_symbol, spy_change_pct, sector_change_pct):
    universe = sector_stock_universes[sector_symbol]
    rows = []

    for symbol, company_name in universe.items():
        try:
            df = get_single_ticker_data(symbol, period="3mo", interval="1d")

            if len(df) < 50:
                rows.append({"symbol": symbol, "name": company_name, "error": "Yeterli veri yok"})
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
            relative_volume = latest_volume / avg_volume_20 if avg_volume_20 > 0 else np.nan

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
            if relative_volume >= 1:
                score += 5

            rows.append({
                "symbol": symbol,
                "name": company_name,
                "date": df.index[-1].strftime("%Y-%m-%d"),
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
                "error": None
            })

        except Exception as e:
            rows.append({"symbol": symbol, "name": company_name, "error": str(e)})

    df = pd.DataFrame(rows)
    clean = df[df["error"].isna()].copy()

    if clean.empty:
        raise RuntimeError("Hisse tarama verisi alınamadı.")

    clean = clean.sort_values("research_score", ascending=False)

    stock_scan = []
    for _, row in clean.iterrows():
        stock_scan.append({
            "symbol": row["symbol"],
            "name": row["name"],
            "date": row["date"],
            "latest_close": safe_round(row["latest_close"]),
            "change_1d_pct": safe_round(row["change_1d_pct"]),
            "change_5d_pct": safe_round(row["change_5d_pct"]),
            "change_20d_pct": safe_round(row["change_20d_pct"]),
            "vs_spy_1d": row["vs_spy_1d"],
            "vs_sector_1d": row["vs_sector_1d"],
            "above_sma20": bool(row["above_sma20"]),
            "above_sma50": bool(row["above_sma50"]),
            "relative_volume": safe_round(row["relative_volume"]),
            "research_score": int(row["research_score"])
        })

    final = stock_scan[0]

    return {
        "stock_scan": stock_scan,
        "final_candidate": final
    }


def prepare_final_candidate(symbol, name):
    df = get_single_ticker_data(symbol, period="1y", interval="1d")

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
    relative_volume = latest_volume / avg_volume_20 if avg_volume_20 > 0 else np.nan

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

    if relative_volume >= 1.2:
        volume_comment = "Hacim ortalamanın belirgin üstünde"
    elif relative_volume >= 1.0:
        volume_comment = "Hacim ortalama civarı / hafif üstü"
    else:
        volume_comment = "Hacim ortalamanın altında, teyit zayıf"

    entry_reference = resistance_20d
    stop_reference = support_10d

    target_candidates = [resistance_50d, resistance_6m, resistance_1y]
    valid_targets = [x for x in target_candidates if x > entry_reference]

    risk_points = entry_reference - stop_reference

    if valid_targets:
        target_1_reference = min(valid_targets)
        reward_points = target_1_reference - entry_reference
        risk_reward = reward_points / risk_points if risk_points > 0 else None
        target_text = f"{target_1_reference:.2f}"
        reward_text = f"{reward_points:.2f}"
        rr_text = f"{risk_reward:.2f}R"
    else:
        target_1_reference = None
        reward_points = None
        risk_reward = None
        target_text = "Veri eksik: giriş bölgesinin üzerinde 50G / 6A / 1Y direnç bulunamadı"
        reward_text = "Veri eksik"
        rr_text = "Veri eksik"

    if risk_reward is None:
        trade_status = "not_suitable_data_missing"
        trade_decision = "Risk/ödül hesaplanamadığı için aktif işlem planı uygun değil."
    elif risk_reward < 1.5:
        trade_status = "not_suitable_weak_rr"
        trade_decision = "Risk/ödül 1.5R altında; işlem planı zayıf / uygun değil."
    else:
        trade_status = "watchlist_candidate"
        trade_decision = "Risk/ödül izlenebilir; yine de tetikleyici, haber riski ve insan onayı gerekir."

    return {
        "symbol": symbol,
        "name": name,
        "date": df.index[-1].strftime("%Y-%m-%d"),
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
        "trade_decision": trade_decision
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

Price action notu:
Bu hisse, otomatik sektör → hisse ön filtresi sonrası final research adayı olarak seçildi. Fiyat direnç bölgesine yakınsa doğrudan işlem planı değil, breakout / kabul / retest senaryosu izlenmeli. Hacim teyidi zayıfsa bunu risk olarak belirt.

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

    stock_result = scan_stocks_for_sector(
        selected_sector["symbol"],
        sector_result["spy_change_pct"],
        selected_sector["change_pct"]
    )

    final_candidate = stock_result["final_candidate"]

    final_data = prepare_final_candidate(
        final_candidate["symbol"],
        final_candidate["name"]
    )

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
                "name": final_data["name"]
            },
            "trade_status": final_data["trade_status"],
            "trade_decision": final_data["trade_decision"],
            "risk_reward": final_data["risk_reward"],
            "target_1": final_data["target_1_reference"]
        },
        "sector_scan": sector_result["sector_scan"],
        "stock_scan": stock_result["stock_scan"],
        "final_candidate_data": final_data,
        "agent_prompt": agent_prompt
    }


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Trading Research API is running",
        "time": datetime.utcnow().isoformat()
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "Trading Research API is healthy",
        "time": datetime.utcnow().isoformat()
    }


@app.get("/daily-research")
def daily_research(refresh: bool = False):
    now = datetime.utcnow()

    if (
        not refresh and
        CACHE["daily_research"] is not None and
        CACHE["created_at"] is not None and
        now - CACHE["created_at"] < timedelta(minutes=CACHE_MINUTES)
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
            "time": datetime.utcnow().isoformat()
        }
