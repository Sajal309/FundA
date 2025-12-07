"""Service to fetch real stock data from Kite Connect and yfinance."""
import os
from datetime import date, timedelta
from typing import List, Dict, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from kiteconnect import KiteConnect
import yfinance as yf
import pandas as pd
from app.db import models
from app.utils import logger


# NSE stock symbols mapping - Major stocks by sector
NSE_STOCKS_BY_SECTOR = {
    "NIFTY_BANK": [
        "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK",
        "INDUSINDBK", "FEDERALBNK", "BANDHANBNK", "PNB", "IDFCFIRSTB"
    ],
    "NIFTY_IT": [
        "TCS", "INFY", "WIPRO", "HCLTECH", "TECHM",
        "LTIM", "MPHASIS", "PERSISTENT", "COFORGE", "MINDTREE"
    ],
    "NIFTY_PHARMA": [
        "SUNPHARMA", "DRREDDY", "CIPLA", "LUPIN", "GLENMARK",
        "TORNTPHARM", "DIVISLAB", "AUROPHARMA", "CADILAHC", "ALKEM"
    ],
    "NIFTY_FMCG": [
        "HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR",
        "MARICO", "GODREJCP", "COLPAL", "EMAMILTD", "TATACONSUM"
    ],
    "NIFTY_AUTO": [
        "MARUTI", "M&M", "TATAMOTORS", "BAJAJ-AUTO", "HEROMOTOCO",
        "EICHERMOT", "ASHOKLEY", "TVSMOTOR", "BHARATFORG", "MOTHERSON"
    ],
    "NIFTY_ENERGY": [
        "RELIANCE", "ONGC", "IOC", "BPCL", "HPCL",
        "GAIL", "PETRONET", "MGL", "IGL", "ADANIGREEN"
    ],
    "NIFTY_METAL": [
        "TATASTEEL", "JSWSTEEL", "SAIL", "VEDL", "HINDALCO",
        "JINDALSAW", "NATIONALUM", "HINDZINC", "NMDC", "MOIL"
    ],
    "NIFTY_REALTY": [
        "DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "SOBHA",
        "BRIGADE", "KOLTEPATIL", "MAHLIFE", "PURAVANKARA", "SHOBHA"
    ],
    "NIFTY_50": [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
        "HINDUNILVR", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK"
    ],
}


def get_kite_client() -> Optional[KiteConnect]:
    """Get Kite Connect client if credentials are available."""
    api_key = os.getenv("KITE_API_KEY")
    access_token = os.getenv("KITE_ACCESS_TOKEN")  # Fixed: should be ACCESS_TOKEN not SECRET
    
    if not api_key or not access_token:
        logger.warning("Kite Connect credentials not available")
        return None
    
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        return kite
    except Exception as e:
        logger.error(f"Error initializing Kite Connect: {e}")
        return None


def fetch_stock_data_from_kite(
    ticker: str,
    from_date: date,
    to_date: date,
    kite: Optional[KiteConnect] = None
) -> Optional[pd.DataFrame]:
    """Fetch stock data from Kite Connect."""
    if kite is None:
        kite = get_kite_client()
    
    if kite is None:
        return None
    
    try:
        # Kite uses instrument token, need to get it first
        # For now, we'll use yfinance as fallback
        logger.warning(f"Kite Connect instrument lookup not implemented, using yfinance for {ticker}")
        return None
    except Exception as e:
        logger.error(f"Error fetching from Kite for {ticker}: {e}")
        return None


def fetch_stock_data_from_yfinance(
    ticker: str,
    from_date: date,
    to_date: date,
    days: int = 365
) -> Optional[pd.DataFrame]:
    """Fetch stock data from yfinance."""
    try:
        # yfinance uses .NS suffix for NSE stocks
        symbol = f"{ticker}.NS"
        
        ticker_obj = yf.Ticker(symbol)
        hist = ticker_obj.history(start=from_date, end=to_date)
        
        if hist.empty:
            # Try without .NS suffix
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(start=from_date, end=to_date)
        
        if hist.empty:
            logger.warning(f"No data from yfinance for {ticker}")
            return None
        
        # Convert to our format
        df = pd.DataFrame({
            'date': [d.date() for d in hist.index],
            'open': hist['Open'].values,
            'high': hist['High'].values,
            'low': hist['Low'].values,
            'close': hist['Close'].values,
            'volume': hist['Volume'].fillna(0).astype(int).values,
        })
        
        logger.info(f"Fetched {len(df)} records from yfinance for {ticker}")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching from yfinance for {ticker}: {e}")
        return None


def fetch_and_store_stock_data(
    db: Session,
    ticker: str,
    sector_id: Optional[str] = None,
    days: int = 365
) -> int:
    """Fetch and store stock data in database."""
    # Check if stock exists
    stock = db.query(models.Stock).filter(models.Stock.ticker == ticker).first()
    
    if not stock:
        # Create stock if it doesn't exist
        stock = models.Stock(
            ticker=ticker,
            company_name=ticker.replace("-", " ").title(),
            sector_id=sector_id,
            exchange="NSE",
            shares_outstanding=1000000000  # Default, will be updated if available
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)
    
    # Get date range
    to_date = date.today()
    from_date = to_date - timedelta(days=days)
    
    # Fetch data
    df = fetch_stock_data_from_yfinance(ticker, from_date, to_date, days)
    
    if df is None or df.empty:
        return 0
    
    # Get existing dates
    existing_dates = {
        ts.date for ts in db.query(models.StockTimeSeries.date).filter(
            models.StockTimeSeries.ticker == ticker
        ).all()
    }
    
    count = 0
    for _, row in df.iterrows():
        if row['date'] in existing_dates:
            continue
        
        ts = models.StockTimeSeries(
            ticker=ticker,
            date=row['date'],
            open=Decimal(str(row['open'])),
            high=Decimal(str(row['high'])),
            low=Decimal(str(row['low'])),
            close=Decimal(str(row['close'])),
            volume=int(row['volume']),
            deliverable_volume=int(row['volume'] * 0.5),  # Estimate 50% deliverable
            turnover=Decimal(str(row['close'] * row['volume']))
        )
        db.add(ts)
        count += 1
        
        if count % 100 == 0:
            db.commit()
    
    db.commit()
    logger.info(f"Stored {count} new records for {ticker}")
    return count


def fetch_all_sector_stocks(
    db: Session,
    sector_id: str,
    days: int = 365
) -> int:
    """Fetch data for all stocks in a sector."""
    stocks = NSE_STOCKS_BY_SECTOR.get(sector_id, [])
    
    if not stocks:
        logger.warning(f"No stocks defined for sector {sector_id}")
        return 0
    
    total_count = 0
    for ticker in stocks:
        try:
            count = fetch_and_store_stock_data(db, ticker, sector_id, days)
            total_count += count
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            continue
    
    logger.info(f"Fetched {total_count} total records for sector {sector_id}")
    return total_count


def fetch_all_stocks_data(
    db: Session,
    days: int = 365
) -> Dict[str, int]:
    """Fetch data for all sectors."""
    results = {}
    
    for sector_id in NSE_STOCKS_BY_SECTOR.keys():
        logger.info(f"Fetching data for sector: {sector_id}")
        count = fetch_all_sector_stocks(db, sector_id, days)
        results[sector_id] = count
    
    return results

