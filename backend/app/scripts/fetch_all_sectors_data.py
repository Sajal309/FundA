"""Script to fetch and store data for all sectors using yfinance.

This script fetches historical data for all supported sectors and stores it directly
in the database, then computes features and forecasts.

Usage:
    docker compose exec backend python -m app.scripts.fetch_all_sectors_data
    docker compose exec backend python -m app.scripts.fetch_all_sectors_data --days 730
    docker compose exec backend python -m app.scripts.fetch_all_sectors_data --sector NIFTY_50
"""
import argparse
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Optional
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.database import SessionLocal
from app.db import crud, schemas
from app.api.v1.sectors import SECTOR_NAMES
from app.services.fetch_nse import NSE_INDEX_SYMBOLS, fetch_nse_index_history, get_nse_session
from app.services.features import compute_features_for_all_sectors
from app.services.forecasts import generate_forecasts_for_all_sectors
from app.utils import logger


# Comprehensive yfinance symbol mapping for NSE indices
# Note: Many NSE indices are not available in yfinance
# Using verified symbols that work with yfinance
# Trying multiple symbol formats for better coverage
YFINANCE_SYMBOL_MAP = {
    # Broad Market - Verified
    'NIFTY 50': '^NSEI',
    'NIFTY BANK': '^NSEBANK',
    'NIFTY NEXT 50': '^NSENEXT50',  # May not work, try alternatives below
    
    # Sectoral Indices - Using CNX prefix (verified)
    'NIFTY IT': '^CNXIT',
    'NIFTY FMCG': '^CNXFMCG',
    'NIFTY PHARMA': '^CNXPHARMA',
    'NIFTY AUTO': '^CNXAUTO',
    'NIFTY ENERGY': '^CNXENERGY',
    'NIFTY METAL': '^CNXMETAL',
    'NIFTY REALTY': '^CNXREALTY',
    'NIFTY PSU BANK': '^CNXPSU',
    'NIFTY PRIVATE BANK': '^CNXPVT',
    'NIFTY FINANCIAL SERVICES': '^CNXFIN',
    'NIFTY HEALTHCARE': '^CNXHEALTH',
    'NIFTY CONSUMER DURABLES': '^CNXCONSUMER',
    'NIFTY INFRASTRUCTURE': '^CNXINFRA',
    'NIFTY OIL & GAS': '^CNXOILGAS',
    'NIFTY PSE': '^CNXPSE',
    'NIFTY SERVICES': '^CNXSERVICES',
    'NIFTY COMMODITIES': '^CNXCOMMODITIES',
    
    # Broad Market - Alternative symbols to try
    'NIFTY 100': '^CNX100',
    'NIFTY 200': '^CNX200',
    'NIFTY 500': '^CNX500',  # May not work
    
    # Midcap/Smallcap - Alternative symbols
    'NIFTY MIDCAP 50': '^CNXMID',
    'NIFTY MIDCAP 100': '^CNXMID100',
    'NIFTY MIDCAP 150': '^CNXMID150',
    'NIFTY SMALLCAP 50': '^CNXSC',
    'NIFTY SMALLCAP 100': '^CNXSC100',
    'NIFTY SMALLCAP 250': '^CNXSC250',
    
    # Thematic - Alternative symbols
    'NIFTY GROWTH SECTORS 15': '^CNXGROWTH',
    'NIFTY DIVIDEND OPPORTUNITIES 50': '^CNXDIVIDEND',
    'NIFTY QUALITY 30': '^CNXQUALITY',
    'NIFTY LOW VOLATILITY 50': '^CNXLOWVOL',
    'NIFTY ALPHA 50': '^CNXALPHA',
    'NIFTY HIGH BETA 50': '^CNXHIGHBETA',
}

# Alternative symbol mappings for indexes that don't work with primary mapping
YFINANCE_ALTERNATIVE_SYMBOLS = {
    'NIFTY NEXT 50': ['^NSENEXT50', '^NSEJUNIOR', '^CNXNEXT50'],
    'NIFTY 500': ['^CNX500', '^NSE500'],
    'NIFTY MIDCAP 50': ['^CNXMID', '^NSEMIDCAP50', '^CNXMIDCAP50'],
    'NIFTY MIDCAP 100': ['^CNXMID100', '^NSEMIDCAP100'],
    'NIFTY MIDCAP 150': ['^CNXMID150', '^NSEMIDCAP150'],
    'NIFTY SMALLCAP 50': ['^CNXSC', '^NSESMALLCAP50'],
    'NIFTY SMALLCAP 100': ['^CNXSC100', '^NSESMALLCAP100'],
    'NIFTY SMALLCAP 250': ['^CNXSC250', '^NSESMALLCAP250'],
    'NIFTY PSU BANK': ['^CNXPSU', '^NSETPSU'],
    'NIFTY PRIVATE BANK': ['^CNXPVT', '^NSETPRIVATE'],
    'NIFTY HEALTHCARE': ['^CNXHEALTH', '^NSETHEALTH'],
    'NIFTY CONSUMER DURABLES': ['^CNXCONSUMER', '^NSETCONSUMER'],
    'NIFTY OIL & GAS': ['^CNXOILGAS', '^NSETOILGAS'],
    'NIFTY SERVICES': ['^CNXSERVICES', '^NSETSERVICES'],
    'NIFTY COMMODITIES': ['^CNXCOMMODITIES', '^NSETCOMMODITIES'],
}


def get_yfinance_symbol(sector_id: str) -> Optional[str]:
    """Get yfinance symbol for a sector, trying multiple alternatives."""
    nse_symbol = NSE_INDEX_SYMBOLS.get(sector_id)
    if not nse_symbol:
        return None
    
    # Try direct mapping first
    yf_symbol = YFINANCE_SYMBOL_MAP.get(nse_symbol)
    if yf_symbol:
        return yf_symbol
    
    # Try alternative symbols if available
    alternatives = YFINANCE_ALTERNATIVE_SYMBOLS.get(nse_symbol, [])
    if alternatives:
        # Return first alternative (will try others in fetch function if this fails)
        return alternatives[0]
    
    # Try common NSE index formats
    # Many indices use ^CNX prefix instead of ^NSE
    clean_symbol = nse_symbol.replace(' ', '').replace('&', '').replace('-', '').upper()
    
    # Try ^CNX format (common for sectoral indices)
    if clean_symbol.startswith('NIFTY'):
        suffix = clean_symbol.replace('NIFTY', '')
        # Try CNX format
        cnx_symbol = f"^CNX{suffix}"
        # Try NSE format
        nse_symbol = f"^NSE{suffix}"
        # Return CNX first as it's more common
        return cnx_symbol
    
    return None


def fetch_and_store_sector_data_from_nse(
    db,
    sector_id: str,
    days: int = 365
) -> int:
    """Fetch data for a sector using NSE direct API and store in database."""
    nse_symbol = NSE_INDEX_SYMBOLS.get(sector_id)
    if not nse_symbol:
        logger.warning(f"No NSE symbol found for {sector_id}")
        return 0
    
    logger.info(f"Fetching data from NSE for {sector_id} ({nse_symbol})")
    
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Fetch from NSE
        df = fetch_nse_index_history(nse_symbol, start_date, end_date)
        
        if df.empty:
            logger.warning(f"No data returned from NSE for {nse_symbol} ({sector_id})")
            return 0
        
        logger.info(f"Fetched {len(df)} records from NSE for {sector_id}")
        
        # Get existing dates to avoid duplicates
        existing_ts = crud.get_sector_timeseries(db, sector_id, limit=10000)
        existing_dates = {ts.ts.date() for ts in existing_ts}
        
        count = 0
        for _, row in df.iterrows():
            ts_date = row['Date'].date() if hasattr(row['Date'], 'date') else pd.Timestamp(row['Date']).date()
            
            if ts_date in existing_dates:
                continue
            
            try:
                ts_data = schemas.SectorTimeSeriesCreate(
                    sector_id=sector_id,
                    ts=pd.Timestamp(row['Date']),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']) if pd.notna(row['Volume']) else 0
                )
                crud.create_sector_time_series(db, ts_data)
                count += 1
                
                if count % 50 == 0:
                    db.commit()
                    logger.debug(f"  Stored {count} records for {sector_id}...")
            except Exception as e:
                logger.warning(f"Failed to store record for {sector_id} on {ts_date}: {e}")
                continue
        
        db.commit()
        logger.info(f"✅ Stored {count} new records from NSE for {sector_id} (total: {len(df)} records)")
        return count
        
    except Exception as e:
        logger.error(f"Error fetching data from NSE for {sector_id}: {e}")
        return 0


def fetch_and_store_sector_data(
    db,
    sector_id: str,
    days: int = 365
) -> int:
    """Fetch data for a sector using yfinance (with NSE fallback) and store in database."""
    try:
        import yfinance as yf
    except ImportError:
        logger.error("yfinance not installed. Install with: pip install yfinance")
        # Try NSE as fallback
        return fetch_and_store_sector_data_from_nse(db, sector_id, days)
    
    # Get primary symbol and alternatives
    nse_symbol = NSE_INDEX_SYMBOLS.get(sector_id)
    primary_symbol = get_yfinance_symbol(sector_id)
    alternative_symbols = YFINANCE_ALTERNATIVE_SYMBOLS.get(nse_symbol, []) if nse_symbol else []
    
    # Combine all symbols to try
    symbols_to_try = [primary_symbol] if primary_symbol else []
    if alternative_symbols and primary_symbol not in alternative_symbols:
        symbols_to_try.extend(alternative_symbols)
    
    if not symbols_to_try:
        logger.warning(f"No yfinance symbol found for {sector_id}")
        return 0
    
    # Try each symbol until one works
    hist = None
    successful_symbol = None
    for yf_symbol in symbols_to_try:
        if not yf_symbol:
            continue
        logger.info(f"Trying yfinance symbol: {yf_symbol} for {sector_id}")
        try:
            ticker = yf.Ticker(yf_symbol)
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            hist = ticker.history(start=start_date, end=end_date)
            
            if not hist.empty:
                successful_symbol = yf_symbol
                break
        except Exception as e:
            logger.debug(f"Symbol {yf_symbol} failed: {e}")
            continue
    
    if hist is None or hist.empty:
        logger.warning(f"No data returned from yfinance for {sector_id} (tried: {', '.join(symbols_to_try)})")
        # Try NSE as fallback
        logger.info(f"Trying NSE API as fallback for {sector_id}...")
        nse_count = fetch_and_store_sector_data_from_nse(db, sector_id, days)
        if nse_count > 0:
            return nse_count
        return 0
    
    logger.info(f"✅ Successfully fetched data from yfinance for {sector_id} using symbol: {successful_symbol}")
    
    try:
        
        logger.info(f"Fetched {len(hist)} records for {sector_id}")
        
        # Get existing dates to avoid duplicates
        existing_ts = crud.get_sector_timeseries(db, sector_id, limit=10000)
        existing_dates = {ts.ts.date() for ts in existing_ts}
        
        count = 0
        for idx, row in hist.iterrows():
            # yfinance returns index as Timestamp
            ts_date = idx.date() if hasattr(idx, 'date') else pd.Timestamp(idx).date()
            
            if ts_date in existing_dates:
                continue
            
            try:
                ts_data = schemas.SectorTimeSeriesCreate(
                    sector_id=sector_id,
                    ts=pd.Timestamp(idx),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']) if pd.notna(row['Volume']) else 0
                )
                crud.create_sector_time_series(db, ts_data)
                count += 1
                
                if count % 50 == 0:
                    db.commit()
                    logger.debug(f"  Stored {count} records for {sector_id}...")
            except Exception as e:
                logger.warning(f"Failed to store record for {sector_id} on {ts_date}: {e}")
                continue
        
        db.commit()
        logger.info(f"✅ Stored {count} new records for {sector_id} (total: {len(hist)} records)")
        return count
        
    except Exception as e:
        logger.error(f"Error fetching data for {sector_id}: {e}")
        return 0


def fetch_all_sectors_data(
    db,
    days: int = 365,
    sector_id: Optional[str] = None
) -> dict:
    """Fetch data for all sectors or a specific sector."""
    if sector_id:
        if sector_id not in SECTOR_NAMES:
            logger.error(f"Unknown sector: {sector_id}")
            return {"success": 0, "failed": 1, "failed_sectors": [sector_id]}
        
        sectors_to_fetch = [sector_id]
    else:
        sectors_to_fetch = list(SECTOR_NAMES.keys())
    
    logger.info(f"Fetching data for {len(sectors_to_fetch)} sectors...")
    
    success_count = 0
    failed_sectors = []
    total_records = 0
    
    for idx, sector_id in enumerate(sectors_to_fetch, 1):
        logger.info(f"\n[{idx}/{len(sectors_to_fetch)}] Processing {sector_id}...")
        try:
            count = fetch_and_store_sector_data(db, sector_id, days)
            if count > 0:
                success_count += 1
                total_records += count
            else:
                # Check if sector already has data
                existing = crud.get_sector_timeseries(db, sector_id, limit=1)
                if existing:
                    logger.info(f"  ⏭️  {sector_id} already has data, skipping")
                    success_count += 1
                else:
                    # Try NSE as fallback
                    logger.info(f"  🔄 Trying NSE API for {sector_id}...")
                    nse_count = fetch_and_store_sector_data_from_nse(db, sector_id, days)
                    if nse_count > 0:
                        success_count += 1
                        total_records += nse_count
                    else:
                        failed_sectors.append(sector_id)
        except Exception as e:
            logger.error(f"  ❌ Failed to fetch {sector_id}: {e}")
            failed_sectors.append(sector_id)
        
        # Add delay to avoid rate limiting (especially for NSE)
        if idx < len(sectors_to_fetch):
            time.sleep(0.5)  # 500ms delay between requests
    
    result = {
        "success": success_count,
        "failed": len(failed_sectors),
        "total_records": total_records,
        "failed_sectors": failed_sectors
    }
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Fetch Summary:")
    logger.info(f"  ✅ Success: {success_count}/{len(sectors_to_fetch)}")
    logger.info(f"  ❌ Failed: {len(failed_sectors)}")
    logger.info(f"  📊 Total records stored: {total_records}")
    if failed_sectors:
        logger.warning(f"  Failed sectors: {', '.join(failed_sectors)}")
    logger.info(f"{'='*80}\n")
    
    return result


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description='Fetch and store data for all sectors using yfinance'
    )
    parser.add_argument(
        '--sector',
        type=str,
        help='Specific sector ID to fetch (e.g., NIFTY_50). If not provided, fetches all sectors.'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='Number of days of historical data to fetch (default: 365)'
    )
    parser.add_argument(
        '--skip-features',
        action='store_true',
        help='Skip computing features after fetching data'
    )
    parser.add_argument(
        '--skip-forecasts',
        action='store_true',
        help='Skip generating forecasts after fetching data'
    )
    
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        # Fetch data
        result = fetch_all_sectors_data(db, days=args.days, sector_id=args.sector)
        
        if result["success"] == 0:
            logger.error("No data was fetched. Exiting.")
            sys.exit(1)
        
        # Compute features
        if not args.skip_features:
            logger.info("\n" + "="*80)
            logger.info("Computing features for all sectors...")
            logger.info("="*80)
            features_count = compute_features_for_all_sectors(db, date.today())
            logger.info(f"✅ Computed features for {features_count} sectors")
        
        # Generate forecasts
        if not args.skip_forecasts:
            logger.info("\n" + "="*80)
            logger.info("Generating forecasts for all sectors...")
            logger.info("="*80)
            forecasts_count = generate_forecasts_for_all_sectors(db, date.today())
            logger.info(f"✅ Generated forecasts for {forecasts_count} sectors")
        
        logger.info("\n" + "="*80)
        logger.info("✅ DATA FETCHING COMPLETE!")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

