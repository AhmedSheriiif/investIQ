# InvestIQ

An investment portfolio risk-analysis platform: pulls market data for a ticker or portfolio, computes risk metrics and stress-test scenarios, and generates a bilingual (English/Arabic) AI narrative explaining the results — with a Next.js dashboard on top.

## Features

- **Risk metrics** — volatility, drawdown, and related risk measures per ticker or portfolio (`risk_metrics.py`, `portfolio_metrics.py`).
- **Stress testing** — runs portfolios through historical/synthetic stress scenarios (`stress_test.py`).
- **Multi-market support** — handles US tickers and non-US (e.g. Egyptian Exchange, via `.CA`/EGX suffix fallback) with per-market benchmark selection (SPY for US, EGX30 for Egypt).
- **AI narrative generation** — turns the computed metrics into a plain-language risk report, in English or Arabic (`narrative_generator.py`).
- **Auth + persistence** — Supabase-backed auth and saved reports (`supabase_auth.py`, `database.py`, `models.py`).
- **Dashboard** — `investiq-dashboard/`, a Next.js + Recharts frontend for visualizing reports.

## Running it

**Backend:**
```bash
pip install -r requirements.txt
# set up .env — see required vars in data_fetcher.py / supabase_auth.py / narrative_generator.py
uvicorn api:app --reload --port 8000
```
Then visit `http://localhost:8000/docs`, or try:
```
http://localhost:8000/report/AAPL
http://localhost:8000/report/COMI?lang=ar
```

**Dashboard:**
```bash
cd investiq-dashboard
npm install
npm run dev
```

## Tests

```bash
pytest
```

## Stack

Python (FastAPI, pandas, yfinance, SQLAlchemy), Supabase (auth + Postgres), Next.js + Recharts dashboard.

## Status

Portfolio/learning project — not production software; use at your own risk for any real investment decisions.
