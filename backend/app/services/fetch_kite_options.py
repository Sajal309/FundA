"""Kite Connect options data fetching service."""
import os
from datetime import date, datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from app.db import crud, schemas, database
from app.config import settings
from app.services.ingest_options import compute_pcr_and_oi_changes
from app.utils import logger


def fetch_and_store_kite_options(
    db: Session,
    underlying: str,
    target_date: Optional[date] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    access_token: Optional[str] = None
) -> bool:
    """
    Fetch options data from Kite and store in database.
    
    Args:
        db: Database session
        underlying: Underlying symbol (e.g., 'NIFTY', 'BANKNIFTY')
        target_date: Date to fetch for
        api_key: Kite API key (uses config if not provided)
        api_secret: Kite API secret (uses config if not provided)
        access_token: Kite access token (required)
        
    Returns:
        True if successful, False otherwise
    """
    from app.services.ingest_options import fetch_options_from_kite
    
    if target_date is None:
        target_date = date.today()
    
    # Get API credentials from config if not provided
    if not api_key:
        api_key = settings.kite_api_key or os.getenv('KITE_API_KEY')
    if not api_secret:
        api_secret = settings.kite_api_secret or os.getenv('KITE_API_SECRET')
    if not access_token:
        access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    if not api_key:
        logger.error("Kite API key required")
        return False
    
    if not access_token:
        logger.warning("Kite access token required. You need to authenticate first.")
        logger.info("To get access token:")
        logger.info("1. Visit: https://kite.trade/connect/login?api_key={}".format(api_key))
        logger.info("2. Login and authorize")
        logger.info("3. Copy the access token from the redirect URL")
        logger.info("4. Set KITE_ACCESS_TOKEN environment variable")
        return False
    
    # Fetch options data
    options_data = fetch_options_from_kite(
        underlying, target_date, api_key, api_secret, access_token
    )
    
    if not options_data or not options_data.get('total_call_oi'):
        logger.warning(f"No options data fetched for {underlying}")
        return False
    
    # Compute PCR and OI changes
    metrics = compute_pcr_and_oi_changes(
        db,
        underlying,
        target_date,
        options_data.get('total_call_oi', 0),
        options_data.get('total_put_oi', 0),
        options_data.get('total_call_volume'),
        options_data.get('total_put_volume'),
    )
    
    # Create options record
    options_record = schemas.OptionsDailyCreate(
        date=target_date,
        underlying=underlying,
        expiry=options_data.get('expiry'),
        total_call_oi=options_data.get('total_call_oi'),
        total_put_oi=options_data.get('total_put_oi'),
        total_call_volume=options_data.get('total_call_volume'),
        total_put_volume=options_data.get('total_put_volume'),
        iv_index=options_data.get('iv_index'),
        **metrics
    )
    
    crud.create_or_update_options_daily(db, options_record)
    logger.info(f"Fetched and stored options data for {underlying} on {target_date}")
    
    return True


def fetch_all_kite_options(
    db: Session,
    target_date: Optional[date] = None,
    underlyings: Optional[List[str]] = None
) -> int:
    """
    Fetch options data for all specified underlyings.
    
    Args:
        db: Database session
        target_date: Date to fetch for
        underlyings: List of underlyings (defaults to NIFTY and BANKNIFTY)
        
    Returns:
        Number of underlyings successfully fetched
    """
    if underlyings is None:
        underlyings = ['NIFTY', 'BANKNIFTY']
    
    if target_date is None:
        target_date = date.today()
    
    count = 0
    for underlying in underlyings:
        try:
            if fetch_and_store_kite_options(db, underlying, target_date):
                count += 1
        except Exception as e:
            logger.error(f"Failed to fetch options for {underlying}: {e}")
            continue
    
    logger.info(f"Fetched options data for {count}/{len(underlyings)} underlyings")
    return count


def main():
    """CLI entrypoint for Kite options fetching."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch options data from Kite Connect')
    parser.add_argument('--underlying', help='Specific underlying (e.g., NIFTY, BANKNIFTY)')
    parser.add_argument('--date', help='Date to fetch (YYYY-MM-DD, defaults to today)')
    parser.add_argument('--access-token', help='Kite access token (or set KITE_ACCESS_TOKEN env var)')
    
    args = parser.parse_args()
    
    db = next(database.get_db())
    
    try:
        target_date = None
        if args.date:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        
        access_token = args.access_token or os.getenv('KITE_ACCESS_TOKEN')
        
        if args.underlying:
            success = fetch_and_store_kite_options(
                db, args.underlying, target_date,
                access_token=access_token
            )
            if success:
                print(f"✅ Fetched options data for {args.underlying}")
            else:
                print(f"❌ Failed to fetch options data for {args.underlying}")
        else:
            count = fetch_all_kite_options(db, target_date)
            print(f"✅ Fetched options data for {count} underlyings")
    except Exception as e:
        logger.error(f"Kite options fetch failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

