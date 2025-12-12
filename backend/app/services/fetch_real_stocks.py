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


# Cache for instrument tokens to avoid repeated API calls
_instrument_cache: Dict[str, Dict] = {}
_instruments_loaded = False


def get_kite_client() -> Optional[KiteConnect]:
    """Get Kite Connect client if credentials are available."""
    api_key = os.getenv("KITE_API_KEY")
    access_token = os.getenv("KITE_ACCESS_TOKEN")
    
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


def get_instrument_token(
    kite: KiteConnect,
    ticker: str,
    exchange: str = "NSE"
) -> Optional[int]:
    """
    Get instrument token for a stock ticker from Kite Connect.
    
    Args:
        kite: KiteConnect client instance
        ticker: Stock ticker symbol (e.g., 'RELIANCE', 'TCS')
        exchange: Exchange code (default: 'NSE')
        
    Returns:
        Instrument token if found, None otherwise
    """
    global _instrument_cache, _instruments_loaded
    
    # Check cache first
    cache_key = f"{exchange}:{ticker}"
    if cache_key in _instrument_cache:
        return _instrument_cache[cache_key].get('instrument_token')
    
    try:
        # Load instruments if not already loaded
        if not _instruments_loaded:
            logger.info("Loading NSE instruments from Kite Connect...")
            instruments = kite.instruments(exchange)
            for inst in instruments:
                key = f"{inst['exchange']}:{inst['tradingsymbol']}"
                _instrument_cache[key] = inst
            _instruments_loaded = True
            logger.info(f"Loaded {len(_instrument_cache)} instruments into cache")
        
        # Try exact match first
        if cache_key in _instrument_cache:
            return _instrument_cache[cache_key].get('instrument_token')
        
        # Try case-insensitive match
        for key, inst in _instrument_cache.items():
            if key.upper() == cache_key.upper():
                return inst.get('instrument_token')
        
        logger.warning(f"Instrument token not found for {ticker} on {exchange}")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching instrument token for {ticker}: {e}")
        return None


def fetch_stock_data_from_kite(
    ticker: str,
    from_date: date,
    to_date: date,
    kite: Optional[KiteConnect] = None,
    interval: str = "day"
) -> Optional[pd.DataFrame]:
    """
    Fetch stock data from Kite Connect (live/intraday or historical).
    
    Args:
        ticker: Stock ticker symbol (e.g., 'RELIANCE', 'TCS')
        from_date: Start date
        to_date: End date
        kite: KiteConnect client (optional, will create if not provided)
        interval: Data interval - 'minute', '3minute', '5minute', '15minute', '30minute', '60minute', 'day'
        
    Returns:
        DataFrame with OHLCV data or None if error
    """
    if kite is None:
        kite = get_kite_client()
    
    if kite is None:
        return None
    
    try:
        # Get instrument token
        instrument_token = get_instrument_token(kite, ticker, "NSE")
        if instrument_token is None:
            logger.warning(f"Could not find instrument token for {ticker}, falling back to yfinance")
            return None
        
        # Fetch historical data from Kite
        # Kite expects dates in format: "YYYY-MM-DD"
        from_date_str = from_date.isoformat()
        to_date_str = to_date.isoformat()
        
        logger.info(f"Fetching {interval} data from Kite for {ticker} (token: {instrument_token}) from {from_date_str} to {to_date_str}")
        
        # Fetch historical data
        hist_data = kite.historical_data(
            instrument_token=instrument_token,
            from_date=from_date_str,
            to_date=to_date_str,
            interval=interval,
            continuous=False,
            oi=False
        )
        
        if not hist_data:
            logger.warning(f"No historical data returned from Kite for {ticker}")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(hist_data)
        
        if df.empty:
            return None
        
        # Convert timestamp to date
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Select and rename columns
        result_df = pd.DataFrame({
            'date': df['date'],
            'open': df['open'],
            'high': df['high'],
            'low': df['low'],
            'close': df['close'],
            'volume': df['volume'].fillna(0).astype(int),
        })
        
        logger.info(f"Fetched {len(result_df)} records from Kite for {ticker}")
        return result_df
        
    except Exception as e:
        logger.error(f"Error fetching from Kite for {ticker}: {e}")
        return None


def fetch_live_quote_from_kite(
    ticker: str,
    kite: Optional[KiteConnect] = None
) -> Optional[Dict]:
    """
    Fetch live quote for a stock from Kite Connect.
    
    Args:
        ticker: Stock ticker symbol
        kite: KiteConnect client (optional)
        
    Returns:
        Dictionary with live quote data or None
    """
    if kite is None:
        kite = get_kite_client()
    
    if kite is None:
        return None
    
    try:
        instrument_token = get_instrument_token(kite, ticker, "NSE")
        if instrument_token is None:
            return None
        
        # Get live quote using instrument token
        # Kite quote API accepts both "EXCHANGE:SYMBOL" format and instrument tokens
        quote = kite.quote([instrument_token])
        
        if not quote or str(instrument_token) not in quote:
            # Try with exchange:symbol format as fallback
            quote = kite.quote([f"NSE:{ticker}"])
            if not quote or f"NSE:{ticker}" not in quote:
                return None
            data = quote[f"NSE:{ticker}"]
        else:
            data = quote[str(instrument_token)]
        
        return {
            'ticker': ticker,
            'instrument_token': instrument_token,
            'last_price': data.get('last_price', 0),
            'open': data.get('ohlc', {}).get('open', 0),
            'high': data.get('ohlc', {}).get('high', 0),
            'low': data.get('ohlc', {}).get('low', 0),
            'close': data.get('ohlc', {}).get('close', 0),
            'volume': data.get('volume', 0),
            'timestamp': data.get('timestamp', None),
            'net_change': data.get('net_change', 0),
            'net_change_pct': data.get('net_change', 0) / data.get('ohlc', {}).get('close', 1) * 100 if data.get('ohlc', {}).get('close', 0) > 0 else 0,
        }
        
    except Exception as e:
        logger.error(f"Error fetching live quote for {ticker}: {e}")
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


def fetch_stock_data_from_nse(
    ticker: str,
    from_date: date,
    to_date: date
) -> Optional[pd.DataFrame]:
    """
    Fetch stock data with delivery from NSE using nsepython.
    
    Args:
        ticker: Stock ticker symbol
        from_date: Start date
        to_date: End date
        
    Returns:
        DataFrame with OHLCV and delivery data or None if error
    """
    try:
        from app.services import nsepython_service
        
        if not nsepython_service.is_available():
            return None
        
        # Fetch delivery data from NSE (includes OHLCV + delivery)
        df = nsepython_service.fetch_stock_delivery_data(ticker, from_date, to_date)
        
        if df is not None and not df.empty:
            # nsepython_service already handles column mapping, so we just need to verify columns
            # Ensure date column is date type
            # nsepython_service already returns dates as date objects, so just verify
            if 'date' in df.columns:
                try:
                    # Check if first value is already a date object
                    if len(df) > 0 and isinstance(df['date'].iloc[0], date):
                        # Already date type, nothing to do
                        pass
                    else:
                        # Try to parse as datetime then convert to date
                        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
                        df = df.dropna(subset=['date'])
                except Exception as e:
                    # If date parsing fails, try to extract from timestamp columns
                    logger.warning(f"Date parsing issue for {ticker}: {e}, attempting alternative")
                    if 'TIMESTAMP' in df.columns:
                        df['date'] = pd.to_datetime(df['TIMESTAMP'], errors='coerce').dt.date
                        df = df.dropna(subset=['date'])
                    elif 'CH_TIMESTAMP' in df.columns:
                        df['date'] = pd.to_datetime(df['CH_TIMESTAMP'], errors='coerce').dt.date
                        df = df.dropna(subset=['date'])
                    else:
                        logger.error(f"Could not parse date column for {ticker}")
                        return None
                
                # Remove duplicate dates (keep first occurrence)
                if len(df) > 0 and df['date'].duplicated().any():
                    logger.warning(f"Found duplicate dates for {ticker}, removing duplicates")
                    df = df.drop_duplicates(subset=['date'], keep='first')
            
            # Ensure required columns exist
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.warning(f"Missing columns in NSE data for {ticker}: {missing_cols}")
                logger.warning(f"Available columns: {list(df.columns)}")
                return None
            
            # Convert numeric columns
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Handle deliverable_volume
            if 'deliverable_volume' in df.columns:
                df['deliverable_volume'] = pd.to_numeric(df['deliverable_volume'], errors='coerce')
            else:
                df['deliverable_volume'] = None
            
            # Handle turnover
            if 'turnover' in df.columns:
                df['turnover'] = pd.to_numeric(df['turnover'], errors='coerce')
            else:
                df['turnover'] = df['close'] * df['volume']
            
            # Add deliverable_volume if missing (set to None)
            if 'deliverable_volume' not in df.columns:
                df['deliverable_volume'] = None
            
            # Calculate turnover if missing
            if 'turnover' not in df.columns:
                df['turnover'] = df['close'] * df['volume']
            
            logger.info(f"✅ Fetched {len(df)} records with delivery data from NSE for {ticker}")
            return df[['date', 'open', 'high', 'low', 'close', 'volume', 'deliverable_volume', 'turnover']]
        
        return None
    except Exception as e:
        logger.error(f"Error fetching from NSE for {ticker}: {e}")
        return None


def fetch_and_store_stock_data(
    db: Session,
    ticker: str,
    sector_id: Optional[str] = None,
    days: int = 365,
    prefer_kite: bool = True,
    prefer_nse: bool = True  # NEW: Prefer NSE for delivery data
) -> int:
    """
    Fetch and store stock data in database.
    Tries Kite Connect first if available, falls back to yfinance.
    
    Args:
        db: Database session
        ticker: Stock ticker symbol
        sector_id: Sector ID (optional)
        days: Number of days of history to fetch
        prefer_kite: If True, prefer Kite Connect over yfinance
    """
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
    
    # Try NSE first if preferred (for delivery data accuracy)
    df = None
    data_source = "unknown"
    has_delivery_data = False
    
    if prefer_nse:
        df = fetch_stock_data_from_nse(ticker, from_date, to_date)
        if df is not None and not df.empty:
            data_source = "NSE (nsepython)"
            # Check if we have delivery data
            if 'deliverable_volume' in df.columns:
                has_delivery_data = df['deliverable_volume'].notna().any()
            logger.info(f"✅ Using NSE for {ticker} (delivery data: {'Yes' if has_delivery_data else 'No'})")
    
    # Try Kite Connect for real-time data (if NSE failed or for live quotes)
    if (df is None or df.empty) and prefer_kite:
        df = fetch_stock_data_from_kite(ticker, from_date, to_date)
        if df is not None and not df.empty:
            data_source = "Kite Connect (live)"
            logger.info(f"✅ Using Kite Connect for {ticker}")
    
    # Fallback to yfinance if both NSE and Kite failed
    if df is None or df.empty:
        df = fetch_stock_data_from_yfinance(ticker, from_date, to_date, days)
        if df is not None and not df.empty:
            data_source = "yfinance (EOD)"
            logger.info(f"✅ Using yfinance for {ticker}")
    
    if df is None or df.empty:
        logger.warning(f"❌ No data available for {ticker} from any source")
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
        
        # Use actual delivery volume if available, otherwise estimate
        deliverable_vol = None
        if 'deliverable_volume' in row and pd.notna(row['deliverable_volume']):
            deliverable_vol = int(row['deliverable_volume'])
        elif not has_delivery_data:
            # Only estimate if we don't have real delivery data
            deliverable_vol = int(row['volume'] * 0.5)  # Estimate 50% deliverable
        
        # Calculate turnover
        turnover_val = row.get('turnover')
        if turnover_val is None or pd.isna(turnover_val):
            turnover_val = float(row['close']) * float(row['volume'])
        
        ts = models.StockTimeSeries(
            ticker=ticker,
            date=row['date'],
            open=Decimal(str(row['open'])),
            high=Decimal(str(row['high'])),
            low=Decimal(str(row['low'])),
            close=Decimal(str(row['close'])),
            volume=int(row['volume']),
            deliverable_volume=deliverable_vol,
            turnover=Decimal(str(turnover_val))
        )
        db.add(ts)
        count += 1
        
        if count % 100 == 0:
            db.commit()
    
    db.commit()
    logger.info(f"Stored {count} new records for {ticker} from {data_source}")
    return count


def fetch_all_sector_stocks(
    db: Session,
    sector_id: str,
    days: int = 365,
    prefer_nse: bool = True
) -> int:
    """Fetch data for all stocks in a sector."""
    stocks = NSE_STOCKS_BY_SECTOR.get(sector_id, [])
    
    if not stocks:
        logger.warning(f"No stocks defined for sector {sector_id}")
        return 0
    
    total_count = 0
    for ticker in stocks:
        try:
            count = fetch_and_store_stock_data(db, ticker, sector_id, days, prefer_kite=True, prefer_nse=prefer_nse)
            total_count += count
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            continue
    
    logger.info(f"Fetched {total_count} total records for sector {sector_id}")
    return total_count


def fetch_all_stocks_data(
    db: Session,
    days: int = 365,
    prefer_nse: bool = True
) -> Dict[str, int]:
    """Fetch data for all sectors."""
    results = {}
    
    for sector_id in NSE_STOCKS_BY_SECTOR.keys():
        logger.info(f"Fetching data for sector: {sector_id}")
        count = fetch_all_sector_stocks(db, sector_id, days, prefer_nse=prefer_nse)
        results[sector_id] = count
    
    return results

