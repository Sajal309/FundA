"""Script to fetch real data for sector rotation feature."""
import sys
from pathlib import Path
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import database
from app.services import fetch_real_stocks, calculate_real_indicators
from app.services import sector_rotation_etl
from app.utils import logger


def main():
    """Main function to fetch and process real sector rotation data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch real data for sector rotation')
    parser.add_argument('--days', type=int, default=365, help='Number of days of history to fetch')
    parser.add_argument('--sector', type=str, help='Specific sector to fetch (optional)')
    parser.add_argument('--skip-fetch', action='store_true', help='Skip fetching stock data')
    parser.add_argument('--skip-indicators', action='store_true', help='Skip calculating indicators')
    parser.add_argument('--skip-etl', action='store_true', help='Skip running ETL aggregation')
    args = parser.parse_args()
    
    db = database.SessionLocal()
    
    try:
        logger.info("="*80)
        logger.info("FETCHING REAL SECTOR ROTATION DATA")
        logger.info("="*80)
        
        # Step 1: Fetch stock data
        if not args.skip_fetch:
            logger.info("\n1. Fetching real stock data from yfinance...")
            if args.sector:
                count = fetch_real_stocks.fetch_all_sector_stocks(db, args.sector, args.days)
                logger.info(f"✅ Fetched {count} records for {args.sector}")
            else:
                results = fetch_real_stocks.fetch_all_stocks_data(db, args.days)
                total = sum(results.values())
                logger.info(f"✅ Fetched {total} total records across {len(results)} sectors")
                for sector, count in results.items():
                    logger.info(f"   - {sector}: {count} records")
        
        # Step 2: Calculate market caps
        if not args.skip_fetch:
            logger.info("\n2. Calculating market caps...")
            from app.scripts.populate_sector_rotation_data import calculate_stock_market_caps
            count = calculate_stock_market_caps(db)
            logger.info(f"✅ Calculated {count} market cap records")
        
        # Step 3: Calculate technical indicators
        if not args.skip_indicators:
            logger.info("\n3. Calculating technical indicators...")
            count = calculate_real_indicators.calculate_indicators_for_all_stocks(db)
            logger.info(f"✅ Calculated {count} technical indicators")
        
        # Step 4: Calculate rolling statistics
        if not args.skip_indicators:
            logger.info("\n4. Calculating rolling statistics...")
            from app.scripts.populate_sector_rotation_data import calculate_stock_rolling_stats
            count = calculate_stock_rolling_stats(db)
            logger.info(f"✅ Calculated {count} rolling statistics")
        
        # Step 5: Run ETL aggregation
        if not args.skip_etl:
            logger.info("\n5. Running ETL aggregation...")
            # Get latest date with data
            from sqlalchemy import func
            latest_date = db.query(func.max(models.StockTimeSeries.date)).scalar()
            if latest_date:
                count = sector_rotation_etl.run_daily_aggregation(db, latest_date)
                logger.info(f"✅ Created {count} aggregation snapshots for {latest_date}")
            else:
                logger.warning("No stock time series data found. Skipping ETL.")
        
        logger.info("\n" + "="*80)
        logger.info("✅ REAL DATA FETCH COMPLETE!")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    from app.db import models
    main()

