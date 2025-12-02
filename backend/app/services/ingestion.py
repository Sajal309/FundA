"""Data ingestion service for EOD sector data."""
import pandas as pd
import sys
import argparse
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from app.db import crud, schemas, database
from app.utils import logger


def ingest_from_csv(file_path: str, db: Session) -> int:
    """
    Ingest sector time series data from CSV file.
    
    Args:
        file_path: Path to CSV file with columns: sector_id, date, open, high, low, close, volume
        db: Database session
        
    Returns:
        Number of records ingested
    """
    try:
        df = pd.read_csv(file_path)
        
        # Validate required columns
        required_cols = ['sector_id', 'date', 'open', 'high', 'low', 'close', 'volume']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        df['ts'] = df['date']
        
        count = 0
        for _, row in df.iterrows():
            try:
                ts_data = schemas.SectorTimeSeriesCreate(
                    sector_id=row['sector_id'],
                    ts=row['ts'],
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume'])
                )
                crud.create_sector_time_series(db, ts_data)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to ingest row {row.get('sector_id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully ingested {count} records from {file_path}")
        return count
        
    except Exception as e:
        logger.error(f"Error ingesting from CSV {file_path}: {e}")
        raise


def fetch_eod_from_nse(sector_id: str, date: datetime) -> dict:
    """
    Fetch EOD data from NSE (placeholder for production implementation).
    
    Args:
        sector_id: Sector identifier (e.g., NIFTY_BANK)
        date: Trading date
        
    Returns:
        Dictionary with open, high, low, close, volume
    """
    # TODO: Implement actual NSE API integration using nsepython or Kite Connect
    # This is a placeholder that would need to be implemented with proper API credentials
    logger.warning(f"fetch_eod_from_nse not implemented yet for {sector_id} on {date}")
    return {}

def ingest_fii_dii_flows(file_path: str, db: Session) -> int:
    """Ingest FII/DII daily flow data from CSV."""
    try:
        df = pd.read_csv(file_path)
        required_cols = ['date', 'source', 'ticker', 'fii_buy', 'fii_sell', 'dii_buy', 'dii_sell']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        df['date'] = pd.to_datetime(df['date']).dt.date
        count = 0
        for _, row in df.iterrows():
            try:
                flow = schemas.FIIDIIDailyCreate(
                    date=row['date'],
                    source=row['source'],
                    ticker=row.get('ticker'),
                    fii_buy=row.get('fii_buy'),
                    fii_sell=row.get('fii_sell'),
                    dii_buy=row.get('dii_buy'),
                    dii_sell=row.get('dii_sell')
                )
                crud.create_fii_dii_daily(db, flow)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to ingest FII/DII row {row}: {e}")
                continue
        logger.info(f"Successfully ingested {count} FII/DII records from {file_path}")
        return count
    except Exception as e:
        logger.error(f"Error ingesting FII/DII CSV {file_path}: {e}")
        raise

def ingest_macro_daily(file_path: str, db: Session) -> int:
    """Ingest macro daily indicators from CSV."""
    try:
        df = pd.read_csv(file_path)
        required_cols = ['date', 'usd_inr_close', 'usd_inr_pct_1d', 'brent_close', 'brent_pct_7d', 'gold_close', 'us_10y_close']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        df['date'] = pd.to_datetime(df['date']).dt.date
        count = 0
        for _, row in df.iterrows():
            try:
                macro = schemas.MacroDailyCreate(
                    date=row['date'],
                    usd_inr_close=row.get('usd_inr_close'),
                    usd_inr_pct_1d=row.get('usd_inr_pct_1d'),
                    brent_close=row.get('brent_close'),
                    brent_pct_7d=row.get('brent_pct_7d'),
                    gold_close=row.get('gold_close'),
                    us_10y_close=row.get('us_10y_close')
                )
                crud.create_or_update_macro_daily(db, macro)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to ingest macro row {row}: {e}")
                continue
        logger.info(f"Successfully ingested {count} macro records from {file_path}")
        return count
    except Exception as e:
        logger.error(f"Error ingesting macro CSV {file_path}: {e}")
        raise

def ingest_news_headlines(file_path: str, db: Session) -> int:
    """Ingest news headlines from CSV."""
    try:
        df = pd.read_csv(file_path)
        required_cols = ['date', 'headline', 'source', 'url', 'sector_tags', 'sentiment_score', 'sentiment_label']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        df['date'] = pd.to_datetime(df['date']).dt.date
        count = 0
        for _, row in df.iterrows():
            try:
                news = schemas.NewsHeadlineCreate(
                    date=row['date'],
                    headline=row['headline'],
                    source=row['source'],
                    url=row.get('url'),
                    sector_tags=row.get('sector_tags'),
                    sentiment_score=row.get('sentiment_score'),
                    sentiment_label=row.get('sentiment_label')
                )
                crud.create_news_headline(db, news)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to ingest news row {row}: {e}")
                continue
        logger.info(f"Successfully ingested {count} news records from {file_path}")
        return count
    except Exception as e:
        logger.error(f"Error ingesting news CSV {file_path}: {e}")
        raise

def ingest_options_daily(file_path: str, db: Session) -> int:
    """Ingest options daily data from CSV."""
    try:
        df = pd.read_csv(file_path)
        required_cols = ['date', 'underlying', 'expiry', 'total_call_oi', 'total_put_oi', 'pcr_oi', 'pcr_volume', 'total_call_volume', 'total_put_volume', 'oi_change_1d', 'oi_change_3d', 'iv_index']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        df['date'] = pd.to_datetime(df['date']).dt.date
        count = 0
        for _, row in df.iterrows():
            try:
                opt = schemas.OptionsDailyCreate(
                    date=row['date'],
                    underlying=row['underlying'],
                    expiry=row.get('expiry'),
                    total_call_oi=row.get('total_call_oi'),
                    total_put_oi=row.get('total_put_oi'),
                    pcr_oi=row.get('pcr_oi'),
                    pcr_volume=row.get('pcr_volume'),
                    total_call_volume=row.get('total_call_volume'),
                    total_put_volume=row.get('total_put_volume'),
                    oi_change_1d=row.get('oi_change_1d'),
                    oi_change_3d=row.get('oi_change_3d'),
                    iv_index=row.get('iv_index')
                )
                crud.create_or_update_options_daily(db, opt)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to ingest options row {row}: {e}")
                continue
        logger.info(f"Successfully ingested {count} options records from {file_path}")
        return count
    except Exception as e:
        logger.error(f"Error ingesting options CSV {file_path}: {e}")
        raise
def main():
    """CLI entrypoint for ingestion."""
    parser = argparse.ArgumentParser(description='Ingest sector EOD data')
    parser.add_argument('--source', required=True, help='Path to CSV file or source identifier')
    parser.add_argument('--sector', help='Specific sector ID to ingest')
    parser.add_argument('--date', help='Specific date to ingest (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    db = next(database.get_db())
    
    try:
        if args.source.endswith('.csv'):
            count = ingest_from_csv(args.source, db)
            print(f"Ingested {count} records")
        else:
            logger.error(f"Unsupported source: {args.source}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

