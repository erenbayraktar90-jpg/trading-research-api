# trading-research-api

Günlük sektör → hisse → işlem planı araştırması yapan FastAPI servisi ve canlı terminal paneli.

## Çalıştır

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

- Panel: http://127.0.0.1:8000/dashboard
- JSON: http://127.0.0.1:8000/daily-research
- API docs: http://127.0.0.1:8000/docs

## Ne yapar

1. 13 sektör ETF'sini tarar, SPY/QQQ'ya göre en güçlü sektörü seçer.
2. Seçilen sektörün hisse evrenini momentum, SMA ve hacimle skorlar.
3. En yüksek skorlu hisse için EMA, RSI, ATR, destek/direnç ve risk/ödül planı çıkarır.

Research only. Canlı emir yok, insan onayı gerekir. Yatırım tavsiyesi değildir.
