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

