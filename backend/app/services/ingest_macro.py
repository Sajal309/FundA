"""Macro economic data ingestion service."""
import pandas as pd
import sys
import argparse
from pathlib import Path
from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.db import crud, schemas, database
from app.utils import logger


def ingest_macro_from_csv(file_path: str, db: Session) -> int:
    """
    Ingest macro data from CSV file.
    
    Expected CSV format:
    date,usd_inr_close,usd_inr_pct_1d,brent_close,brent_pct_7d,gold_close,us_10y_close
    
    Args:
        file_path: Path to CSV file
        db: Database session
        
    Returns:
        Number of records ingested
    """
    try:
        df = pd.read_csv(file_path)
        
        # Validate required columns
        required_cols = ['date']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Convert date column
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        count = 0
        for _, row in df.iterrows():
            try:
                macro_data = schemas.MacroDailyCreate(
                    date=row['date'],
                    usd_inr_close=float(row['usd_inr_close']) if pd.notna(row.get('usd_inr_close')) else None,
                    usd_inr_pct_1d=float(row['usd_inr_pct_1d']) if pd.notna(row.get('usd_inr_pct_1d')) else None,
                    brent_close=float(row['brent_close']) if pd.notna(row.get('brent_close')) else None,
                    brent_pct_7d=float(row['brent_pct_7d']) if pd.notna(row.get('brent_pct_7d')) else None,
                    gold_close=float(row['gold_close']) if pd.notna(row.get('gold_close')) else None,
                    us_10y_close=float(row['us_10y_close']) if pd.notna(row.get('us_10y_close')) else None,
                )
                crud.create_or_update_macro_daily(db, macro_data)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to ingest macro row {row.get('date', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully ingested {count} macro records from {file_path}")
        return count
        
    except Exception as e:
        logger.error(f"Error ingesting macro from CSV {file_path}: {e}")
        raise


def fetch_macro_from_alpha_vantage(symbol: str, api_key: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch macro data from Alpha Vantage API (placeholder for production).
    
    Args:
        symbol: Symbol (e.g., 'USDINR', 'BRENT', 'GOLD')
        api_key: Alpha Vantage API key
        
    Returns:
        DataFrame with macro data
    """
    # TODO: Implement Alpha Vantage API integration
    # from alpha_vantage.foreignexchange import ForeignExchange
    # from alpha_vantage.commodities import Commodities
    logger.warning(f"fetch_macro_from_alpha_vantage not implemented yet for {symbol}")
    return pd.DataFrame()


def fetch_macro_from_yfinance(symbol: str, days: int = 30) -> pd.DataFrame:
    """
    Fetch macro data from yfinance.
    
    Args:
        symbol: Symbol (e.g., 'USDINR=X', 'CL=F' for Brent, 'GC=F' for Gold)
        days: Number of days to fetch
        
    Returns:
        DataFrame with macro data
    """
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=f"{days}d")
        
        if hist.empty:
            logger.warning(f"No data from yfinance for {symbol}")
            return pd.DataFrame()
        
        # Convert to our format
        df = pd.DataFrame({
            'date': [d.date() for d in hist.index],
            'close': hist['Close'].values,
        })
        
        # Calculate pct changes
        df['pct_1d'] = df['close'].pct_change() * 100
        df['pct_7d'] = df['close'].pct_change(periods=7) * 100
        
        logger.info(f"Fetched {len(df)} records from yfinance for {symbol}")
        return df
        
    except ImportError:
        logger.warning("yfinance not installed. Install with: pip install yfinance")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching from yfinance {symbol}: {e}")
        return pd.DataFrame()


def fetch_all_macro_from_yfinance(db: Session, days: int = 30) -> int:
    """
    Fetch all macro indicators from yfinance and store in database.
    
    Args:
        db: Database session
        days: Number of days to fetch
        
    Returns:
        Number of records ingested
    """
    # Symbol mappings
    symbols = {
        'usd_inr': 'INR=X',  # USD/INR
        'brent': 'CL=F',     # Brent Crude
        'gold': 'GC=F',      # Gold futures
        'us_10y': '^TNX',    # US 10Y Treasury yield
    }
    
    total_count = 0
    
    for indicator, symbol in symbols.items():
        try:
            df = fetch_macro_from_yfinance(symbol, days)
            
            if df.empty:
                continue
            
            for _, row in df.iterrows():
                # Get or create macro record for this date
                macro = crud.get_macro_daily(db, row['date'])
                
                if not macro:
                    macro_data = schemas.MacroDailyCreate(
                        date=row['date'],
                        usd_inr_close=float(row['close']) if indicator == 'usd_inr' else None,
                        brent_close=float(row['close']) if indicator == 'brent' else None,
                        gold_close=float(row['close']) if indicator == 'gold' else None,
                        us_10y_close=float(row['close']) if indicator == 'us_10y' else None,
                    )
                    crud.create_or_update_macro_daily(db, macro_data)
                else:
                    # Update existing record
                    if indicator == 'usd_inr':
                        macro.usd_inr_close = float(row['close'])
                        macro.usd_inr_pct_1d = float(row['pct_1d']) if pd.notna(row.get('pct_1d')) else None
                    elif indicator == 'brent':
                        macro.brent_close = float(row['close'])
                        macro.brent_pct_7d = float(row['pct_7d']) if pd.notna(row.get('pct_7d')) else None
                    elif indicator == 'gold':
                        macro.gold_close = float(row['close'])
                    elif indicator == 'us_10y':
                        macro.us_10y_close = float(row['close'])
                    db.commit()
                
                total_count += 1
            
            logger.info(f"Ingested {indicator} data from yfinance")
            
        except Exception as e:
            logger.error(f"Failed to fetch {indicator} from yfinance: {e}")
            continue
    
    # Compute percentage changes
    compute_macro_pct_changes(db)
    
    return total_count


def compute_macro_pct_changes(db: Session, target_date: Optional[date] = None) -> int:
    """
    Compute percentage changes for macro indicators from historical data.
    
    Args:
        db: Database session
        target_date: Date to compute for (defaults to latest)
        
    Returns:
        Number of records updated
    """
    from app.db import models
    from sqlalchemy import desc
    
    if not target_date:
        latest = db.query(models.MacroDaily).order_by(desc(models.MacroDaily.date)).first()
        if not latest:
            return 0
        target_date = latest.date
    
    # Get historical data for calculations
    macro_records = db.query(models.MacroDaily).filter(
        models.MacroDaily.date <= target_date
    ).order_by(desc(models.MacroDaily.date)).limit(10).all()
    
    if len(macro_records) < 2:
        return 0
    
    count = 0
    for record in macro_records:
        updated = False
        
        # Compute USD/INR 1d change
        if record.usd_inr_close and len(macro_records) > 1:
            prev_record = next((r for r in macro_records if r.date < record.date), None)
            if prev_record and prev_record.usd_inr_close:
                pct_1d = ((record.usd_inr_close - prev_record.usd_inr_close) / prev_record.usd_inr_close) * 100
                if record.usd_inr_pct_1d != pct_1d:
                    record.usd_inr_pct_1d = float(pct_1d)
                    updated = True
        
        # Compute Brent 7d change
        if record.brent_close:
            week_ago = next((r for r in macro_records if r.date <= record.date and (record.date - r.date).days >= 7), None)
            if week_ago and week_ago.brent_close:
                pct_7d = ((record.brent_close - week_ago.brent_close) / week_ago.brent_close) * 100
                if record.brent_pct_7d != pct_7d:
                    record.brent_pct_7d = float(pct_7d)
                    updated = True
        
        if updated:
            db.commit()
            count += 1
    
    logger.info(f"Computed macro pct changes for {count} records")
    return count


def main():
    """CLI entrypoint for macro ingestion."""
    parser = argparse.ArgumentParser(description='Ingest macro economic data')
    parser.add_argument('--source', required=True, help='Path to CSV file or source identifier')
    parser.add_argument('--compute-pct', action='store_true', help='Compute percentage changes from historical data')
    
    args = parser.parse_args()
    
    db = next(database.get_db())
    
    try:
        if args.source.endswith('.csv'):
            count = ingest_macro_from_csv(args.source, db)
            print(f"Ingested {count} macro records")
            
            if args.compute_pct:
                pct_count = compute_macro_pct_changes(db)
                print(f"Computed percentage changes for {pct_count} records")
        else:
            logger.error(f"Unsupported source: {args.source}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Macro ingestion failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

