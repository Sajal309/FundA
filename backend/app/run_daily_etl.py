"""Daily ETL orchestrator for SectorView MVP.

This script is intended to be run inside the backend container, e.g.:

    docker compose exec backend python -m app.run_daily_etl

For the current MVP it:
1. Ingests EOD sector time-series from the sample CSV
2. Computes features for all sectors
3. Generates rule-based forecasts for all sectors
4. Writes a JSON summary report to logs/daily_run_YYYYMMDD.json

Later milestones can extend this to include flows, macro, options, and news.
"""
from __future__ import annotations

import os
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any

from app.db.database import SessionLocal
from app.services import ingestion
from app.services import ingest_flows, ingest_macro, ingest_options, ingest_news
from app.services.features import compute_features_for_all_sectors
from app.services.forecasts import generate_forecasts_for_all_sectors
from app.utils import logger


def _ensure_logs_dir() -> Path:
    root = Path(__file__).resolve().parents[2]
    logs_dir = root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def run_daily_etl(run_date: date | None = None) -> Dict[str, Any]:
    """Run the minimal daily ETL pipeline using local/sample data."""
    run_date = run_date or date.today()
    started_at = datetime.utcnow()

    db = SessionLocal()
    summary: Dict[str, Any] = {
        "run_date": run_date.isoformat(),
        "started_at": started_at.isoformat() + "Z",
        "steps": {},
    }

    try:
        # 1) Ingest EOD sector time-series from sample CSV
        # Try both paths: relative to project root and absolute /app/sample_data
        sample_csv = Path(__file__).resolve().parents[2] / "sample_data" / "sector_time_series.csv"
        if not sample_csv.exists():
            sample_csv = Path("/app/sample_data/sector_time_series.csv")
        if not sample_csv.exists():
            logger.error(f"Sample CSV not found at {sample_csv}")
            summary["steps"]["ingest_eod"] = {
                "status": "failed",
                "records": 0,
                "error": f"missing sample csv: {sample_csv}",
            }
        else:
            logger.info(f"Starting EOD ingestion from {sample_csv}")
            count_eod = ingestion.ingest_from_csv(str(sample_csv), db)
            summary["steps"]["ingest_eod"] = {
                "status": "ok",
                "records": count_eod,
            }

        # 2) Ingest FII/DII flows from sample CSV
        flows_csv = Path(__file__).resolve().parents[2] / "sample_data" / "fii_dii_flows.csv"
        if not flows_csv.exists():
            flows_csv = Path("/app/sample_data/fii_dii_flows.csv")
        if flows_csv.exists():
            logger.info(f"Starting flows ingestion from {flows_csv}")
            count_flows = ingest_flows.ingest_flows_from_csv(str(flows_csv), db)
            summary["steps"]["ingest_flows"] = {
                "status": "ok",
                "records": count_flows,
            }
            # Aggregate flows by sector
            agg_count = ingest_flows.aggregate_flows_by_sector(db, run_date)
            summary["steps"]["aggregate_flows"] = {
                "status": "ok",
                "sectors_processed": agg_count,
            }
        else:
            logger.warning(f"Flows CSV not found at {flows_csv}, skipping")
            summary["steps"]["ingest_flows"] = {
                "status": "skipped",
                "records": 0,
            }

        # 3) Ingest macro data from sample CSV
        macro_csv = Path(__file__).resolve().parents[2] / "sample_data" / "macro_daily.csv"
        if not macro_csv.exists():
            macro_csv = Path("/app/sample_data/macro_daily.csv")
        if macro_csv.exists():
            logger.info(f"Starting macro ingestion from {macro_csv}")
            count_macro = ingest_macro.ingest_macro_from_csv(str(macro_csv), db)
            summary["steps"]["ingest_macro"] = {
                "status": "ok",
                "records": count_macro,
            }
            # Compute percentage changes
            pct_count = ingest_macro.compute_macro_pct_changes(db, run_date)
            summary["steps"]["compute_macro_pct"] = {
                "status": "ok",
                "records_updated": pct_count,
            }
        else:
            logger.warning(f"Macro CSV not found at {macro_csv}, skipping")
            summary["steps"]["ingest_macro"] = {
                "status": "skipped",
                "records": 0,
            }

        # 4) Ingest options data (try Kite first, fallback to CSV)
        kite_access_token = os.getenv('KITE_ACCESS_TOKEN')
        
        if kite_access_token:
            try:
                from app.services.fetch_kite_options import fetch_all_kite_options
                logger.info("Fetching options data from Kite Connect...")
                count_options = fetch_all_kite_options(db, run_date)
                summary["steps"]["ingest_options"] = {
                    "status": "ok",
                    "source": "Kite Connect",
                    "underlyings_processed": count_options,
                }
            except Exception as e:
                logger.warning(f"Kite options fetch failed: {e}, falling back to CSV")
                kite_access_token = None  # Fall through to CSV
        
        if not kite_access_token:
            # Fallback to CSV
            options_csv = Path(__file__).resolve().parents[2] / "sample_data" / "options_daily.csv"
            if not options_csv.exists():
                options_csv = Path("/app/sample_data/options_daily.csv")
            if options_csv.exists():
                logger.info(f"Starting options ingestion from {options_csv}")
                count_options = ingest_options.ingest_options_from_csv(str(options_csv), db)
                summary["steps"]["ingest_options"] = {
                    "status": "ok",
                    "source": "CSV",
                    "records": count_options,
                }
            else:
                logger.warning(f"Options CSV not found at {options_csv}, skipping")
                summary["steps"]["ingest_options"] = {
                    "status": "skipped",
                    "records": 0,
                }

        # 5) Ingest news headlines with sentiment scoring
        # Try NewsAPI first if key is available, otherwise use sample CSV
        from app.config import settings
        news_api_key = settings.newsapi_key or os.getenv('NEWSAPI_KEY')
        
        if news_api_key:
            try:
                logger.info("Fetching news from NewsAPI...")
                from datetime import timedelta
                from_date = run_date - timedelta(days=7)
                count_news = ingest_news.ingest_news_from_api(
                    db, news_api_key, from_date=from_date, to_date=run_date
                )
                summary["steps"]["ingest_news"] = {
                    "status": "ok",
                    "source": "NewsAPI",
                    "records": count_news,
                }
                # Aggregate sentiment by sector
                agg_sentiment_count = ingest_news.aggregate_sentiment_by_sector(db, run_date)
                summary["steps"]["aggregate_sentiment"] = {
                    "status": "ok",
                    "sectors_processed": agg_sentiment_count,
                }
            except Exception as e:
                logger.warning(f"NewsAPI fetch failed: {e}, falling back to CSV")
                news_api_key = None  # Fall through to CSV
        
        if not news_api_key:
            # Fallback to CSV
            news_csv = Path(__file__).resolve().parents[2] / "sample_data" / "news_headlines.csv"
            if not news_csv.exists():
                news_csv = Path("/app/sample_data/news_headlines.csv")
            if news_csv.exists():
                logger.info(f"Starting news ingestion from {news_csv}")
                count_news = ingest_news.ingest_news_from_csv(str(news_csv), db)
                summary["steps"]["ingest_news"] = {
                    "status": "ok",
                    "source": "CSV",
                    "records": count_news,
                }
                # Aggregate sentiment by sector
                agg_sentiment_count = ingest_news.aggregate_sentiment_by_sector(db, run_date)
                summary["steps"]["aggregate_sentiment"] = {
                    "status": "ok",
                    "sectors_processed": agg_sentiment_count,
                }
            else:
                logger.warning(f"News CSV not found at {news_csv}, skipping")
                summary["steps"]["ingest_news"] = {
                    "status": "skipped",
                    "records": 0,
                }

        # 6) Compute features (now includes flows, macro, options, and sentiment)
        logger.info("Starting feature computation for all sectors (daily ETL)...")
        features_count = compute_features_for_all_sectors(db, run_date)
        summary["steps"]["compute_features"] = {
            "status": "ok",
            "sectors_processed": features_count,
        }

        # 7) Generate forecasts (now includes options and sentiment-based drivers)
        logger.info("Starting forecast generation for all sectors (daily ETL)...")
        forecasts_count = generate_forecasts_for_all_sectors(db, run_date)
        summary["steps"]["compute_forecasts"] = {
            "status": "ok",
            "sectors_processed": forecasts_count,
        }

        summary["status"] = "ok"
    except Exception as exc:  # pragma: no cover - safety net
        logger.error(f"Daily ETL run failed: {exc}")
        summary["status"] = "failed"
        summary["error"] = str(exc)
    finally:
        finished_at = datetime.utcnow()
        summary["finished_at"] = finished_at.isoformat() + "Z"
        summary["duration_seconds"] = (finished_at - started_at).total_seconds()
        db.close()

        # Write JSON report
        logs_dir = _ensure_logs_dir()
        out_path = logs_dir / f"daily_run_{run_date.strftime('%Y%m%d')}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, sort_keys=True, default=str)

        logger.info(f"Daily ETL summary written to {out_path}")

    return summary


def main() -> None:
    """CLI entrypoint used when running as a module."""
    run_daily_etl()


if __name__ == "__main__":
    main()


