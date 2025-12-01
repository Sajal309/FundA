## Data Sources for SectorView (MVP)

This project is designed to work with **authoritative** data providers for Indian markets.
For the local/demo environment, we primarily use **sample CSVs** and stubbed connectors; you can later
swap in real API keys and production feeds.

### 1. NSE / Nifty Indices (sector EOD)

- **Intended source**: NiftyIndices / NSE sector index pages (live and historical EOD).
- **Demo implementation**: `sample_data/sector_time_series.csv` ingested via
  `backend/app/services/ingestion.py::ingest_from_csv`.
- **Notes**:
  - Production use should rely on official downloads / vendor feeds, not ad‑hoc scraping.
  - Respect NSE terms of use and rate limits.

### 2. Broker APIs (live/intraday, option chains)

- **Intended sources**: Zerodha Kite Connect, Dhan, etc.
- **Current status**: Only **stubs** are planned; no live calls are made in this repo.
- **Secrets**:
  - API keys must be provided via environment variables (see `.env.example` / `secrets.example`).
  - Never commit real keys to git.

### 3. FII/DII Flows

- **Intended sources**: NSE FII/DII reports, NSDL/CDSL FPI reports.
- **Current status**: Not yet wired; future ETL steps will populate `fii_dii_daily` and `sector_flows_daily`.

### 4. Macro & Commodities

- **Intended sources**: Alpha Vantage (FX/commodities), RBI open data, Investing.com (for prototyping).
- **Current status**: Not yet wired; `macro_daily` is a planned table for later milestones.

### 5. Fundamentals & News / Sentiment

- **Intended sources**: Exchange filings, Moneycontrol/Screener (fundamentals), NewsAPI / business news sites (news).
- **Current status**: Not yet wired; `earnings_events`, `fundamentals`, `news_headlines` and sentiment aggregates
  will be added in follow‑up milestones.

### Licensing & TOS

- Always review and comply with the terms of service of NSE, brokers, and news providers.
- For production deployments you should use **licensed feeds** where required.
- This repository is intended as an MVP / educational template and ships only with locally stored sample data.


