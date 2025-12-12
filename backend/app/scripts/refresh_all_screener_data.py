"""Script to refresh all stock screener data from trusted sources.

This script fetches fresh, accurate fundamental data for all stocks
from trusted sources (Screener.in, NSE, yfinance) and updates the database.

Usage:
    docker compose exec backend python -m app.scripts.refresh_all_screener_data
    docker compose exec backend python -m app.scripts.refresh_all_screener_data --sector NIFTY_BANK
    docker compose exec backend python -m app.scripts.refresh_all_screener_data --ticker RELIANCE
"""
import argparse
import sys
from datetime import date
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import database, models
from app.scripts.fetch_stock_fundamentals import fetch_fundamentals_for_stock
from app.utils import logger
from sqlalchemy import func


def refresh_sector_data(db, sector_id: str, limit: int = None):
    """Refresh fundamentals for all stocks in a sector."""
    stocks = db.query(models.Stock).filter(models.Stock.sector_id == sector_id).all()
    
    if limit:
        stocks = stocks[:limit]
    
    # Filter out sector/index names - only process actual stock tickers
    # Sector names typically contain spaces or are all caps like "NIFTY BANK"
    actual_stocks = []
    for stock in stocks:
        # Skip if ticker looks like a sector/index name (contains spaces, or is a known index)
        if ' ' in stock.ticker or stock.ticker.upper() in ['NIFTY BANK', 'NIFTY 50', 'NIFTY IT', 'NIFTY PHARMA']:
            logger.warning(f"Skipping {stock.ticker} - appears to be a sector/index, not a stock")
            continue
        actual_stocks.append(stock)
    
    total = len(actual_stocks)
    success = 0
    failed = 0
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Refreshing data for {sector_id} ({total} stocks)")
    logger.info(f"{'='*80}")
    
    for i, stock in enumerate(actual_stocks, 1):
        logger.info(f"\n[{i}/{total}] Processing {stock.ticker}...")
        
        try:
            if fetch_fundamentals_for_stock(db, stock.ticker):
                success += 1
                logger.info(f"✅ Successfully refreshed {stock.ticker}")
            else:
                failed += 1
                logger.warning(f"❌ Failed to refresh {stock.ticker}")
        except Exception as e:
            failed += 1
            logger.error(f"❌ Error refreshing {stock.ticker}: {e}")
        
        # Rate limiting - be respectful to data sources
        if i < total:
            time.sleep(2)  # 2 second delay between requests
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Summary for {sector_id}:")
    logger.info(f"  ✅ Success: {success}")
    logger.info(f"  ❌ Failed: {failed}")
    logger.info(f"  📊 Total: {total}")
    logger.info(f"{'='*80}")
    
    return success, failed


def refresh_all_data(db, limit: int = None):
    """Refresh fundamentals for all stocks in database."""
    stocks = db.query(models.Stock).all()
    
    if limit:
        stocks = stocks[:limit]
    
    # Filter out sector/index names - only process actual stock tickers
    actual_stocks = []
    known_indices = ['NIFTY BANK', 'NIFTY 50', 'NIFTY IT', 'NIFTY PHARMA', 'NIFTY FMCG', 
                     'NIFTY AUTO', 'NIFTY ENERGY', 'NIFTY METAL', 'NIFTY REALTY']
    for stock in stocks:
        # Skip if ticker looks like a sector/index name
        if ' ' in stock.ticker or stock.ticker.upper() in known_indices:
            continue
        actual_stocks.append(stock)
    
    total = len(actual_stocks)
    success = 0
    failed = 0
    
    logger.info(f"\n{'='*80}")
    logger.info(f"REFRESHING ALL STOCK SCREENER DATA")
    logger.info(f"{'='*80}")
    logger.info(f"Total stocks to process: {total}")
    logger.info(f"Data sources: NSE → yfinance")
    logger.info(f"{'='*80}\n")
    
    for i, stock in enumerate(actual_stocks, 1):
        logger.info(f"\n[{i}/{total}] Processing {stock.ticker} ({stock.sector_id})...")
        
        try:
            if fetch_fundamentals_for_stock(db, stock.ticker):
                success += 1
                logger.info(f"✅ Successfully refreshed {stock.ticker}")
            else:
                failed += 1
                logger.warning(f"❌ Failed to refresh {stock.ticker}")
        except Exception as e:
            failed += 1
            logger.error(f"❌ Error refreshing {stock.ticker}: {e}")
        
        # Rate limiting - be respectful to data sources
        if i < total:
            time.sleep(2)  # 2 second delay between requests
        
        # Progress update every 10 stocks
        if i % 10 == 0:
            logger.info(f"\n📊 Progress: {i}/{total} ({i*100//total}%) | Success: {success} | Failed: {failed}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"FINAL SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"  ✅ Success: {success}")
    logger.info(f"  ❌ Failed: {failed}")
    logger.info(f"  📊 Total: {total}")
    logger.info(f"  📈 Success Rate: {success*100//total if total > 0 else 0}%")
    logger.info(f"{'='*80}")
    
    return success, failed


def verify_data_quality(db, sample_size: int = 10):
    """Verify data quality by checking sample stocks."""
    logger.info(f"\n{'='*80}")
    logger.info(f"VERIFYING DATA QUALITY")
    logger.info(f"{'='*80}")
    
    # Get latest fundamentals date
    latest_date = db.query(func.max(models.StockFundamentals.date)).scalar()
    logger.info(f"Latest fundamentals date: {latest_date}")
    
    # Get sample stocks with fundamentals
    # Fix SQLAlchemy join by explicitly specifying the join condition
    sample_stocks = db.query(models.StockFundamentals).join(
        models.Stock, models.StockFundamentals.ticker == models.Stock.ticker
    ).filter(
        models.StockFundamentals.date == latest_date
    ).limit(sample_size).all()
    
    logger.info(f"\nSample stocks with fundamentals ({len(sample_stocks)}):")
    for fund in sample_stocks:
        stock = db.query(models.Stock).filter(models.Stock.ticker == fund.ticker).first()
        metrics_count = sum([
            1 for attr in ['roe', 'roce', 'pe', 'pb', 'market_cap', 'debt_to_equity',
                          'operating_margin', 'net_margin'] 
            if getattr(fund, attr, None) is not None
        ])
        logger.info(f"  {fund.ticker:10s} - {metrics_count} metrics available")
    
    logger.info(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description='Refresh all stock screener data from trusted sources')
    parser.add_argument('--sector', type=str, help='Refresh for specific sector (e.g., NIFTY_BANK)')
    parser.add_argument('--ticker', type=str, help='Refresh for specific ticker')
    parser.add_argument('--all', action='store_true', help='Refresh for all stocks')
    parser.add_argument('--limit', type=int, help='Limit number of stocks to process')
    parser.add_argument('--verify', action='store_true', help='Verify data quality after refresh')
    
    args = parser.parse_args()
    
    db = database.SessionLocal()
    
    try:
        if args.ticker:
            logger.info(f"Refreshing data for {args.ticker}...")
            if fetch_fundamentals_for_stock(db, args.ticker):
                logger.info(f"✅ Successfully refreshed {args.ticker}")
            else:
                logger.error(f"❌ Failed to refresh {args.ticker}")
        elif args.sector:
            refresh_sector_data(db, args.sector, args.limit)
        elif args.all:
            refresh_all_data(db, args.limit)
        else:
            parser.print_help()
            sys.exit(1)
        
        if args.verify:
            verify_data_quality(db)
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()

