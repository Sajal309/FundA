"""Options chain data ingestion service."""
import pandas as pd
import json
import sys
import argparse
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db import crud, schemas, database
from app.utils import logger


def compute_pcr_and_oi_changes(
    db: Session,
    underlying: str,
    target_date: date,
    call_oi: int,
    put_oi: int,
    call_volume: Optional[int] = None,
    put_volume: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compute PCR and OI changes from historical data.
    
    Args:
        db: Database session
        underlying: Option underlying (e.g., 'NIFTY', 'BANKNIFTY')
        target_date: Date for the data
        call_oi: Total call open interest
        put_oi: Total put open interest
        call_volume: Total call volume (optional)
        put_volume: Total put volume (optional)
        
    Returns:
        Dictionary with computed metrics
    """
    from app.db import models
    from sqlalchemy import desc
    
    # Compute PCR
    pcr_oi = None
    if call_oi and put_oi and call_oi > 0:
        pcr_oi = put_oi / call_oi
    
    pcr_volume = None
    if call_volume and put_volume and call_volume > 0:
        pcr_volume = put_volume / call_volume
    
    # Get historical OI for change calculations
    total_oi = (call_oi or 0) + (put_oi or 0)
    
    oi_change_1d = None
    oi_change_3d = None
    
    if total_oi > 0:
        # Get previous day
        prev_date = target_date - timedelta(days=1)
        prev_options = crud.get_options_daily(db, underlying, prev_date)
        
        if prev_options and prev_options.total_call_oi and prev_options.total_put_oi:
            prev_total_oi = prev_options.total_call_oi + prev_options.total_put_oi
            if prev_total_oi > 0:
                oi_change_1d = ((total_oi - prev_total_oi) / prev_total_oi) * 100
        
        # Get 3 days ago
        three_days_ago = target_date - timedelta(days=3)
        prev_options_3d = crud.get_options_daily(db, underlying, three_days_ago)
        
        if prev_options_3d and prev_options_3d.total_call_oi and prev_options_3d.total_put_oi:
            prev_total_oi_3d = prev_options_3d.total_call_oi + prev_options_3d.total_put_oi
            if prev_total_oi_3d > 0:
                oi_change_3d = ((total_oi - prev_total_oi_3d) / prev_total_oi_3d) * 100
    
    return {
        'pcr_oi': pcr_oi,
        'pcr_volume': pcr_volume,
        'oi_change_1d': oi_change_1d,
        'oi_change_3d': oi_change_3d,
    }


def ingest_options_from_csv(file_path: str, db: Session) -> int:
    """
    Ingest options data from CSV file.
    
    Expected CSV format:
    date,underlying,expiry,total_call_oi,total_put_oi,total_call_volume,total_put_volume,iv_index
    
    Args:
        file_path: Path to CSV file
        db: Database session
        
    Returns:
        Number of records ingested
    """
    try:
        df = pd.read_csv(file_path)
        
        # Validate required columns
        required_cols = ['date', 'underlying']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Convert date column
        df['date'] = pd.to_datetime(df['date']).dt.date
        if 'expiry' in df.columns:
            df['expiry'] = pd.to_datetime(df['expiry']).dt.date
        
        count = 0
        for _, row in df.iterrows():
            try:
                # Compute PCR and OI changes
                metrics = compute_pcr_and_oi_changes(
                    db,
                    row['underlying'],
                    row['date'],
                    int(row['total_call_oi']) if pd.notna(row.get('total_call_oi')) else 0,
                    int(row['total_put_oi']) if pd.notna(row.get('total_put_oi')) else 0,
                    int(row['total_call_volume']) if pd.notna(row.get('total_call_volume')) else None,
                    int(row['total_put_volume']) if pd.notna(row.get('total_put_volume')) else None,
                )
                
                options_data = schemas.OptionsDailyCreate(
                    date=row['date'],
                    underlying=str(row['underlying']),
                    expiry=row.get('expiry') if pd.notna(row.get('expiry')) else None,
                    total_call_oi=int(row['total_call_oi']) if pd.notna(row.get('total_call_oi')) else None,
                    total_put_oi=int(row['total_put_oi']) if pd.notna(row.get('total_put_oi')) else None,
                    total_call_volume=int(row['total_call_volume']) if pd.notna(row.get('total_call_volume')) else None,
                    total_put_volume=int(row['total_put_volume']) if pd.notna(row.get('total_put_volume')) else None,
                    iv_index=float(row['iv_index']) if pd.notna(row.get('iv_index')) else None,
                    **metrics
                )
                crud.create_or_update_options_daily(db, options_data)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to ingest options row {row.get('date', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully ingested {count} options records from {file_path}")
        return count
        
    except Exception as e:
        logger.error(f"Error ingesting options from CSV {file_path}: {e}")
        raise


def ingest_options_from_json(file_path: str, db: Session) -> int:
    """
    Ingest options data from JSON file (option chain format).
    
    Expected JSON format:
    {
        "date": "2025-11-28",
        "underlying": "NIFTY",
        "expiry": "2025-11-30",
        "calls": [
            {"strike": 19000, "oi": 1000000, "volume": 50000, "iv": 0.15},
            ...
        ],
        "puts": [
            {"strike": 19000, "oi": 1200000, "volume": 60000, "iv": 0.16},
            ...
        ]
    }
    
    Args:
        file_path: Path to JSON file
        db: Database session
        
    Returns:
        Number of records ingested
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Aggregate option chain data
        date_str = data.get('date')
        if not date_str:
            raise ValueError("Missing 'date' field in JSON")
        
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        underlying = data.get('underlying', 'NIFTY')
        expiry_str = data.get('expiry')
        expiry = datetime.strptime(expiry_str, '%Y-%m-%d').date() if expiry_str else None
        
        calls = data.get('calls', [])
        puts = data.get('puts', [])
        
        total_call_oi = sum(c.get('oi', 0) for c in calls)
        total_put_oi = sum(p.get('oi', 0) for p in puts)
        total_call_volume = sum(c.get('volume', 0) for c in calls)
        total_put_volume = sum(p.get('volume', 0) for p in puts)
        
        # Compute average IV if available
        iv_index = None
        all_ivs = [c.get('iv') for c in calls if c.get('iv')] + [p.get('iv') for p in puts if p.get('iv')]
        if all_ivs:
            iv_index = sum(all_ivs) / len(all_ivs)
        
        # Compute PCR and OI changes
        metrics = compute_pcr_and_oi_changes(
            db,
            underlying,
            target_date,
            total_call_oi,
            total_put_oi,
            total_call_volume if total_call_volume > 0 else None,
            total_put_volume if total_put_volume > 0 else None,
        )
        
        options_data = schemas.OptionsDailyCreate(
            date=target_date,
            underlying=underlying,
            expiry=expiry,
            total_call_oi=total_call_oi if total_call_oi > 0 else None,
            total_put_oi=total_put_oi if total_put_oi > 0 else None,
            total_call_volume=total_call_volume if total_call_volume > 0 else None,
            total_put_volume=total_put_volume if total_put_volume > 0 else None,
            iv_index=iv_index,
            **metrics
        )
        
        crud.create_or_update_options_daily(db, options_data)
        logger.info(f"Successfully ingested options data for {underlying} on {target_date}")
        return 1
        
    except Exception as e:
        logger.error(f"Error ingesting options from JSON {file_path}: {e}")
        raise


def fetch_options_from_kite(underlying: str, target_date: date, api_key: Optional[str] = None) -> dict:
    """
    Fetch option chain from Kite Connect API (placeholder for production).
    
    Args:
        underlying: Underlying symbol (e.g., 'NIFTY', 'BANKNIFTY')
        target_date: Trading date
        api_key: Kite Connect API key
        
    Returns:
        Dictionary with option chain data
    """
    # TODO: Implement Kite Connect API integration
    # from kiteconnect import KiteConnect
    # kite = KiteConnect(api_key=api_key)
    # instruments = kite.instruments("NFO")
    # option_chain = kite.option_chain(underlying)
    logger.warning(f"fetch_options_from_kite not implemented yet for {underlying} on {target_date}")
    return {}


def main():
    """CLI entrypoint for options ingestion."""
    parser = argparse.ArgumentParser(description='Ingest options chain data')
    parser.add_argument('--source', required=True, help='Path to CSV or JSON file')
    parser.add_argument('--format', choices=['csv', 'json'], help='File format (auto-detected from extension if not specified)')
    
    args = parser.parse_args()
    
    db = next(database.get_db())
    
    try:
        file_path = Path(args.source)
        file_format = args.format or file_path.suffix[1:].lower()
        
        if file_format == 'csv' or file_path.suffix.lower() == '.csv':
            count = ingest_options_from_csv(str(file_path), db)
            print(f"Ingested {count} options records")
        elif file_format == 'json' or file_path.suffix.lower() == '.json':
            count = ingest_options_from_json(str(file_path), db)
            print(f"Ingested {count} options records")
        else:
            logger.error(f"Unsupported file format: {file_format}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Options ingestion failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

