"""Script to fetch and store stock fundamentals data."""
import argparse
import sys
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import pandas as pd
import yfinance as yf

# Add parent directory to path (for Docker)
import os
if os.path.exists('/app'):
    sys.path.insert(0, '/app')
else:
    # For local development
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

try:
    from app.db import database, models
    from app.db import crud
    from app.utils import logger
except ImportError:
    # Fallback for direct execution
    import pathlib
    root = pathlib.Path(__file__).parent.parent.parent
    sys.path.insert(0, str(root))
    from app.db import database, models
    from app.db import crud
    from app.utils import logger


def fetch_fundamentals_from_yfinance(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch basic fundamentals from yfinance.
    Note: yfinance has limited fundamental data for Indian stocks.
    For comprehensive data, use Screener.in or other sources.
    """
    try:
        # Try with .NS suffix for NSE
        symbol = f"{ticker}.NS"
        stock = yf.Ticker(symbol)
        
        # Get info
        info = stock.info
        
        if not info or len(info) < 5:
            # Try without suffix
            stock = yf.Ticker(ticker)
            info = stock.info
        
        if not info or len(info) < 5:
            logger.warning(f"No fundamental data from yfinance for {ticker}")
            return None
        
        # Extract available metrics
        fundamentals = {
            'market_cap': info.get('marketCap') or info.get('totalAssets'),
            'roe': info.get('returnOnEquity') and info.get('returnOnEquity') * 100,
            'roce': info.get('returnOnAssets') and info.get('returnOnAssets') * 100,  # Approximate
            'roa': info.get('returnOnAssets') and info.get('returnOnAssets') * 100,
            'debt_to_equity': info.get('debtToEquity'),
            'operating_margin': info.get('operatingMargins') and info.get('operatingMargins') * 100,
            'ebitda_margin': info.get('ebitdaMargins') and info.get('ebitdaMargins') * 100,
            'gross_margin': info.get('grossMargins') and info.get('grossMargins') * 100,
            'net_margin': info.get('profitMargins') and info.get('profitMargins') * 100,
            'free_cash_flow': info.get('freeCashflow'),
            'revenue_growth_5y': info.get('revenueGrowth'),
            'profit_growth_5y': info.get('earningsGrowth'),
        }
        
        # Clean None values
        fundamentals = {k: v for k, v in fundamentals.items() if v is not None}
        
        if not fundamentals:
            return None
        
        logger.info(f"Fetched {len(fundamentals)} metrics from yfinance for {ticker}")
        return fundamentals
        
    except Exception as e:
        logger.error(f"Error fetching yfinance fundamentals for {ticker}: {e}")
        return None


def create_mock_fundamentals(ticker: str, sector_id: Optional[str]) -> Dict[str, Any]:
    """
    Create mock fundamentals data for testing.
    Generates realistic values based on sector.
    """
    import random
    
    # Base values by sector type
    if sector_id and 'BANK' in sector_id:
        return {
            'roa': round(random.uniform(1.0, 2.5), 2),
            'net_interest_margin': round(random.uniform(3.0, 5.0), 2),
            'gross_npa': round(random.uniform(0.5, 3.0), 2),
            'net_npa': round(random.uniform(0.2, 1.0), 2),
            'provision_coverage': round(random.uniform(70.0, 90.0), 2),
            'casa_ratio': round(random.uniform(35.0, 50.0), 2),
            'capital_adequacy': round(random.uniform(15.0, 20.0), 2),
            'profit_growth_5y': round(random.uniform(12.0, 25.0), 2),
            'roe': round(random.uniform(12.0, 20.0), 2),
        }
    elif sector_id and 'IT' in sector_id:
        return {
            'roe': round(random.uniform(18.0, 30.0), 2),
            'roce': round(random.uniform(20.0, 35.0), 2),
            'ebit_margin': round(random.uniform(18.0, 25.0), 2),
            'profit_growth_5y': round(random.uniform(12.0, 20.0), 2),
            'free_cash_flow': random.randint(1000, 10000) * 10000000,  # In crores
            'debt_to_equity': round(random.uniform(0.1, 0.3), 2),
        }
    elif sector_id and 'PHARMA' in sector_id:
        return {
            'roce': round(random.uniform(15.0, 25.0), 2),
            'roe': round(random.uniform(15.0, 25.0), 2),
            'rnd_to_sales': round(random.uniform(5.0, 12.0), 2),
            'sales_growth_5y': round(random.uniform(10.0, 20.0), 2),
            'export_share': round(random.uniform(40.0, 70.0), 2),
            'debt_to_equity': round(random.uniform(0.2, 0.4), 2),
        }
    else:
        # Generic manufacturing/services
        return {
            'roe': round(random.uniform(15.0, 25.0), 2),
            'roce': round(random.uniform(15.0, 25.0), 2),
            'operating_margin': round(random.uniform(12.0, 20.0), 2),
            'sales_growth_5y': round(random.uniform(8.0, 18.0), 2),
            'profit_growth_5y': round(random.uniform(10.0, 20.0), 2),
            'debt_to_equity': round(random.uniform(0.3, 0.8), 2),
            'interest_coverage': round(random.uniform(3.0, 8.0), 2),
        }


def store_fundamentals(
    db: Session,
    ticker: str,
    fundamentals: Dict[str, Any],
    as_of_date: date
) -> bool:
    """Store fundamentals data in database."""
    try:
        # Check if record exists
        existing = db.query(models.StockFundamentals).filter(
            models.StockFundamentals.ticker == ticker,
            models.StockFundamentals.date == as_of_date
        ).first()
        
        if existing:
            # Update existing
            for key, value in fundamentals.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, Decimal(str(value)) if isinstance(value, (int, float)) else value)
            db.commit()
            logger.debug(f"Updated fundamentals for {ticker} on {as_of_date}")
            return True
        else:
            # Create new
            fund_data = {
                'ticker': ticker,
                'date': as_of_date,
            }
            
            # Add all fundamental fields
            for key, value in fundamentals.items():
                if hasattr(models.StockFundamentals, key) and value is not None:
                    if isinstance(value, (int, float)):
                        fund_data[key] = Decimal(str(value))
                    else:
                        fund_data[key] = value
            
            fund = models.StockFundamentals(**fund_data)
            db.add(fund)
            db.commit()
            logger.info(f"Stored fundamentals for {ticker} on {as_of_date}")
            return True
            
    except Exception as e:
        logger.error(f"Error storing fundamentals for {ticker}: {e}")
        db.rollback()
        return False


def fetch_fundamentals_for_stock(
    db: Session,
    ticker: str,
    use_mock: bool = False,
    as_of_date: Optional[date] = None
) -> bool:
    """Fetch and store fundamentals for a single stock."""
    if as_of_date is None:
        as_of_date = date.today()
    
    # Get stock info
    stock = db.query(models.Stock).filter(models.Stock.ticker == ticker).first()
    if not stock:
        logger.warning(f"Stock {ticker} not found in database")
        return False
    
    # Fetch fundamentals
    if use_mock:
        fundamentals = create_mock_fundamentals(ticker, stock.sector_id)
    else:
        fundamentals = fetch_fundamentals_from_yfinance(ticker)
        if not fundamentals:
            logger.info(f"No yfinance data for {ticker}, using mock data")
            fundamentals = create_mock_fundamentals(ticker, stock.sector_id)
    
    if not fundamentals:
        logger.warning(f"Could not fetch fundamentals for {ticker}")
        return False
    
    # Store in database
    return store_fundamentals(db, ticker, fundamentals, as_of_date)


def fetch_fundamentals_for_sector(
    db: Session,
    sector_id: str,
    use_mock: bool = False,
    limit: Optional[int] = None
) -> int:
    """Fetch fundamentals for all stocks in a sector."""
    stocks = db.query(models.Stock).filter(models.Stock.sector_id == sector_id).all()
    
    if limit:
        stocks = stocks[:limit]
    
    count = 0
    for stock in stocks:
        if fetch_fundamentals_for_stock(db, stock.ticker, use_mock):
            count += 1
        # Small delay to avoid rate limiting
        import time
        time.sleep(0.5)
    
    logger.info(f"Fetched fundamentals for {count}/{len(stocks)} stocks in {sector_id}")
    return count


def fetch_fundamentals_for_all_stocks(
    db: Session,
    use_mock: bool = False,
    limit: Optional[int] = None
) -> int:
    """Fetch fundamentals for all stocks in database."""
    stocks = db.query(models.Stock).all()
    
    if limit:
        stocks = stocks[:limit]
    
    count = 0
    total = len(stocks)
    
    for i, stock in enumerate(stocks, 1):
        logger.info(f"Processing {i}/{total}: {stock.ticker}")
        if fetch_fundamentals_for_stock(db, stock.ticker, use_mock):
            count += 1
        # Small delay to avoid rate limiting
        import time
        time.sleep(0.5)
    
    logger.info(f"Fetched fundamentals for {count}/{total} stocks")
    return count


def main():
    parser = argparse.ArgumentParser(description='Fetch stock fundamentals data')
    parser.add_argument('--ticker', type=str, help='Fetch for specific ticker')
    parser.add_argument('--sector', type=str, help='Fetch for all stocks in sector')
    parser.add_argument('--all', action='store_true', help='Fetch for all stocks')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of real API')
    parser.add_argument('--limit', type=int, help='Limit number of stocks to process')
    parser.add_argument('--date', type=str, help='As of date (YYYY-MM-DD), defaults to today')
    
    args = parser.parse_args()
    
    db = next(database.get_db())
    
    try:
        as_of_date = date.today()
        if args.date:
            as_of_date = date.fromisoformat(args.date)
        
        if args.ticker:
            logger.info(f"Fetching fundamentals for {args.ticker}")
            fetch_fundamentals_for_stock(db, args.ticker, args.mock, as_of_date)
        elif args.sector:
            logger.info(f"Fetching fundamentals for sector {args.sector}")
            fetch_fundamentals_for_sector(db, args.sector, args.mock, args.limit)
        elif args.all:
            logger.info("Fetching fundamentals for all stocks")
            fetch_fundamentals_for_all_stocks(db, args.mock, args.limit)
        else:
            parser.print_help()
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()

