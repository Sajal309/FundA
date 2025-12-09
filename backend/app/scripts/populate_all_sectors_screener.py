"""Script to populate stocks and fundamentals for all screener sectors.

This script creates sample stocks and fundamentals data for all sectors
that are configured in the screener but don't have data yet.

Usage:
    docker compose exec backend python -m app.scripts.populate_all_sectors_screener
    docker compose exec backend python -m app.scripts.populate_all_sectors_screener --stocks-only
    docker compose exec backend python -m app.scripts.populate_all_sectors_screener --fundamentals-only
"""
import argparse
import sys
from datetime import date
from pathlib import Path
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import database, models
from app.config.sector_screeners import SECTOR_SCREENERS, SECTOR_NAME_MAP
from app.scripts.fetch_stock_fundamentals import create_mock_fundamentals, store_fundamentals
from app.utils import logger


# Sample stock tickers per sector (realistic Indian stock tickers)
SAMPLE_STOCKS = {
    "banks": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "INDUSINDBK", "FEDERALBNK", "BANDHANBNK"],
    "nbfc": ["BAJFINANCE", "MUTHOOTFIN", "MANAPPURAM", "LICHSGFIN", "MFSL", "HDFCAMC", "IIFL", "CHOLAFIN"],
    "insurance": ["LICI", "HDFCLIFE", "ICICIPRULI", "SBILIFE", "MAXHEALTH", "STARHEALTH", "ICICIGI", "NEWINDIA"],
    "it": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM", "PERSISTENT", "MPHASIS"],
    "software": ["ZENSAR", "SONATA", "INTELLECT", "NEWGEN", "QUICKHEAL", "CYIENT", "MINDTREE", "LTI"],
    "fmcg": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR", "MARICO", "GODREJCP", "COLPAL"],
    "pharma": ["SUNPHARMA", "DRREDDY", "CIPLA", "LUPIN", "GLENMARK", "TORNTPHARM", "CADILAHC", "AUROPHARMA"],
    "hospitals": ["APOLLOHOSP", "FORTIS", "MAXHEALTH", "NH", "RAINBOW", "KIMS", "NARAYANA", "GLOBALHOSP"],
    "diagnostics": ["METROPOLIS", "THYROCARE", "LALPATHLAB", "DRLALPATH", "SRL", "VIVANTA", "SUPERDIAG", "AGILENT"],
    "real_estate": ["DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "SOBHA", "BRIGADE", "KOLTEPATIL", "MAHLIFE"],
    "cement": ["ULTRACEMCO", "SHREECEM", "ACC", "AMBUJACEM", "DALMIABHA", "RAMCOCEM", "JKLAKSHMI", "ORIENTCEM"],
    "metals": ["TATASTEEL", "JSWSTEEL", "SAIL", "VEDL", "HINDALCO", "NALCO", "JINDALSAW", "RATNAMANI"],
    "capital_goods": ["LT", "SIEMENS", "ABB", "BHEL", "THERMAX", "CROMPTON", "VOLTAS", "BLUESTAR"],
    "defence": ["HAL", "BEL", "MIDHANI", "BEML", "GARDENREACH", "COCHINSHIP", "MAZAGON", "BHARATFORG"],
    "infrastructure": ["LARSEN", "ADANIPORTS", "IRCTC", "RVNL", "IRCON", "RITES", "NBCC", "NCC"],
    "telecom": ["BHARTIARTL", "RELIANCE", "VODAFONE", "IDEA", "TATACOMM", "MTNL", "BSNL", "TECHM"],
    "chemicals": ["UPL", "SRF", "ALKEM", "PIIND", "GHCL", "TATACHEM", "RALLIS", "DEEPAKNTR"],
    "agrochemicals": ["UPL", "RALLIS", "DEEPAKNTR", "BAYERCROP", "SYNGENTA", "ADAMA", "FMC", "NUTRICHEM"],
    "auto_oem": ["MARUTI", "M&M", "TATAMOTORS", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT", "ASHOKLEY", "TVSMOTOR"],
    "auto_ancillary": ["BOSCHLTD", "MOTHERSON", "MINDACORP", "SAMKRG", "MUNJALSHOW", "EXIDEIND", "AMARAJABAT", "SUNDARAM"],
    "textiles": ["ARVIND", "WELSPUN", "TRIDENT", "RAYMOND", "KPRMILL", "VARDHMAN", "GRASIM", "BIRLACORPN"],
    "retail": ["RELIANCE", "DMART", "SHOPPERSSTOP", "TITAN", "TATACONSUM", "V-MART", "SPENCERS", "FUTURE"],
    "oil_gas": ["RELIANCE", "ONGC", "IOC", "BPCL", "HPCL", "GAIL", "PETRONET", "IGL"],
    "renewables": ["ADANIGREEN", "TATAPOWER", "NTPC", "SJVN", "NHPC", "POWERGRID", "TORNTPOWER", "JSWENERGY"],
    "logistics": ["DELHIVERY", "GATI", "TCI", "CONCOR", "CONTAINER", "ALLCARGO", "MAHINDRA", "MAHINDRALOG"],
    "consumer_durables": ["WHIRLPOOL", "VOLTAS", "BLUESTAR", "CROMPTON", "ORIENTELEC", "HAVELLS", "VGUARD", "BAJAJELEC"],
    "media": ["ZEE", "SUNTV", "NETWORK18", "TVTODAY", "HTMEDIA", "JAGRAN", "DBCORP", "ENIL"],
}


def create_stocks_for_sector(db, sector_key: str, sector_names: list, num_stocks: int = 10):
    """Create sample stocks for a sector."""
    config = SECTOR_SCREENERS.get(sector_key)
    if not config:
        return 0
    
    # Get sample tickers for this sector
    sample_tickers = SAMPLE_STOCKS.get(sector_key, [])
    if not sample_tickers:
        # Generate generic tickers if no samples
        sample_tickers = [f"{sector_key.upper()}{i:02d}" for i in range(1, num_stocks + 1)]
    
    # Use first sector name as sector_id
    sector_id = sector_names[0] if sector_names else sector_key.upper()
    
    count = 0
    seen_tickers = set()
    for ticker in sample_tickers[:num_stocks]:
        # Skip duplicates in the same batch
        if ticker in seen_tickers:
            continue
        seen_tickers.add(ticker)
        
        # Check if stock already exists
        existing = db.query(models.Stock).filter(models.Stock.ticker == ticker).first()
        if existing:
            # Update sector_id if needed
            if existing.sector_id not in sector_names:
                existing.sector_id = sector_id
                db.commit()
            continue
        
        # Create new stock
        stock = models.Stock(
            ticker=ticker,
            company_name=ticker.replace("-", " ").replace("_", " ").title(),
            sector_id=sector_id,
            exchange="NSE",
            shares_outstanding=random.randint(500000000, 5000000000)  # 50Cr to 500Cr shares
        )
        db.add(stock)
        count += 1
        
        # Commit in batches to avoid long transactions
        if count % 5 == 0:
            db.commit()
    
    db.commit()
    logger.info(f"Created {count} stocks for {config.label} ({sector_key})")
    return count


def create_fundamentals_for_sector(db, sector_key: str, sector_names: list, as_of_date: date):
    """Create fundamentals data for all stocks in a sector."""
    config = SECTOR_SCREENERS.get(sector_key)
    if not config:
        return 0
    
    # Get all stocks for this sector
    stocks = db.query(models.Stock).filter(
        models.Stock.sector_id.in_(sector_names)
    ).all()
    
    if not stocks:
        logger.warning(f"No stocks found for {config.label} ({sector_key})")
        return 0
    
    count = 0
    for stock in stocks:
        # Check if fundamentals already exist
        existing = db.query(models.StockFundamentals).filter(
            models.StockFundamentals.ticker == stock.ticker,
            models.StockFundamentals.date == as_of_date
        ).first()
        
        if existing:
            continue
        
        # Generate mock fundamentals
        fundamentals = create_mock_fundamentals(stock.ticker, stock.sector_id)
        
        # Store fundamentals
        if store_fundamentals(db, stock.ticker, fundamentals, as_of_date):
            count += 1
    
    logger.info(f"Created {count} fundamentals for {config.label} ({sector_key})")
    return count


def main():
    parser = argparse.ArgumentParser(description='Populate stocks and fundamentals for all screener sectors')
    parser.add_argument('--stocks-only', action='store_true', help='Only create stocks, skip fundamentals')
    parser.add_argument('--fundamentals-only', action='store_true', help='Only create fundamentals, skip stocks')
    parser.add_argument('--sector', type=str, help='Process only specific sector key')
    parser.add_argument('--date', type=str, help='As of date (YYYY-MM-DD), defaults to today')
    parser.add_argument('--num-stocks', type=int, default=10, help='Number of stocks per sector (default: 10)')
    
    args = parser.parse_args()
    
    db = database.SessionLocal()
    as_of_date = date.today()
    if args.date:
        as_of_date = date.fromisoformat(args.date)
    
    try:
        logger.info("="*80)
        logger.info("POPULATING ALL SECTORS FOR STOCK SCREENER")
        logger.info("="*80)
        
        # Get sectors to process
        sectors_to_process = [args.sector] if args.sector else list(SECTOR_SCREENERS.keys())
        
        total_stocks = 0
        total_fundamentals = 0
        
        for sector_key in sectors_to_process:
            config = SECTOR_SCREENERS.get(sector_key)
            if not config:
                continue
            
            sector_names = SECTOR_NAME_MAP.get(sector_key, [])
            if not sector_names:
                sector_names = [sector_key.upper()]
            
            logger.info(f"\n{'='*80}")
            logger.info(f"Processing: {config.label} ({sector_key})")
            logger.info(f"{'='*80}")
            
            # Create stocks
            if not args.fundamentals_only:
                stocks_count = create_stocks_for_sector(db, sector_key, sector_names, args.num_stocks)
                total_stocks += stocks_count
            
            # Create fundamentals
            if not args.stocks_only:
                fundamentals_count = create_fundamentals_for_sector(db, sector_key, sector_names, as_of_date)
                total_fundamentals += fundamentals_count
        
        logger.info(f"\n{'='*80}")
        logger.info("SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Total stocks created: {total_stocks}")
        logger.info(f"Total fundamentals created: {total_fundamentals}")
        logger.info(f"✅ Done!")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()

