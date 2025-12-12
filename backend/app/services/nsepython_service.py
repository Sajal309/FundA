"""NSE data fetching service using nsepython library."""
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal
from app.utils import logger

try:
    from nsepythonserver import *
    NSEPYTHON_AVAILABLE = True
except ImportError:
    try:
        from nsepython import *
        NSEPYTHON_AVAILABLE = True
    except ImportError:
        NSEPYTHON_AVAILABLE = False
        logger.warning("nsepython/nsepythonserver not available. Install with: pip install nsepythonserver")


def is_available() -> bool:
    """Check if nsepython is available."""
    return NSEPYTHON_AVAILABLE


def fetch_sector_data(sector_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch sector/index data from NSE.
    
    Args:
        sector_name: Sector/index name (e.g., 'NIFTY 50', 'NIFTY BANK')
        
    Returns:
        Dictionary with sector data or None if error
    """
    if not NSEPYTHON_AVAILABLE:
        logger.error("nsepython not available")
        return None
    
    try:
        # Fetch equity stock indices
        url = f"https://www.nseindia.com/api/equity-stockIndices?index={sector_name.replace(' ', '%20')}"
        data = nsefetch(url)
        
        if data and 'data' in data:
            return data
        return None
    except Exception as e:
        logger.error(f"Error fetching sector data for {sector_name}: {e}")
        return None


def fetch_stock_quote(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch live quote for a stock.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        Dictionary with stock quote data or None if error
    """
    if not NSEPYTHON_AVAILABLE:
        logger.error("nsepython not available")
        return None
    
    try:
        # Use nsefetch to get quote data
        url = f"https://www.nseindia.com/api/quote-equity?symbol={ticker}"
        quote = nsefetch(url)
        return quote
    except Exception as e:
        logger.error(f"Error fetching quote for {ticker}: {e}")
        return None


def fetch_stock_delivery_data(ticker: str, from_date: Optional[date] = None, to_date: Optional[date] = None) -> Optional[pd.DataFrame]:
    """
    Fetch delivery data for a stock.
    
    Args:
        ticker: Stock ticker symbol
        from_date: Start date (optional)
        to_date: End date (optional, defaults to today)
        
    Returns:
        DataFrame with delivery data or None if error
    """
    if not NSEPYTHON_AVAILABLE:
        logger.error("nsepython not available")
        return None
    
    try:
        if to_date is None:
            to_date = date.today()
        if from_date is None:
            from_date = to_date - timedelta(days=30)
        
        # Use equity_history function from nsepython
        # Format: equity_history(symbol, start_date, end_date)
        start_date_str = from_date.strftime('%d-%m-%Y')
        end_date_str = to_date.strftime('%d-%m-%Y')
        
        try:
            data = equity_history(ticker, start_date_str, end_date_str)
        except TypeError as e:
            # If function signature is different, try alternative
            logger.warning(f"equity_history signature issue for {ticker}: {e}")
            # Fallback: use nsefetch for historical data
            url = f"https://www.nseindia.com/api/historical/securityArchives?from={start_date_str}&to={end_date_str}&symbol={ticker}&dataType=priceVolumeDeliverable"
            data = nsefetch(url)
            if data and isinstance(data, dict) and 'data' in data:
                data = data['data']
        
        # Convert to DataFrame
        if isinstance(data, dict) and 'data' in data:
            df = pd.DataFrame(data['data'])
        elif isinstance(data, pd.DataFrame):
            df = data
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            return None
        
        if df.empty:
            return None
        
        # Map NSE column names to standard names
        # Handle priority: use first available column for each target
        column_mapping = {}
        
        # Date columns (priority order)
        for date_col in ['CH_TIMESTAMP', 'TIMESTAMP', 'mTIMESTAMP']:
            if date_col in df.columns and 'date' not in column_mapping.values():
                column_mapping[date_col] = 'date'
                break
        
        # Price columns
        if 'CH_OPENING_PRICE' in df.columns:
            column_mapping['CH_OPENING_PRICE'] = 'open'
        if 'CH_TRADE_HIGH_PRICE' in df.columns:
            column_mapping['CH_TRADE_HIGH_PRICE'] = 'high'
        if 'CH_TRADE_LOW_PRICE' in df.columns:
            column_mapping['CH_TRADE_LOW_PRICE'] = 'low'
        # Close price (priority: CLOSING_PRICE > LAST_TRADED_PRICE)
        if 'CH_CLOSING_PRICE' in df.columns:
            column_mapping['CH_CLOSING_PRICE'] = 'close'
        elif 'CH_LAST_TRADED_PRICE' in df.columns:
            column_mapping['CH_LAST_TRADED_PRICE'] = 'close'
        
        # Volume columns
        if 'CH_TOT_TRADED_QTY' in df.columns:
            column_mapping['CH_TOT_TRADED_QTY'] = 'volume'
        
        # Delivery columns
        if 'COP_DELIV_QTY' in df.columns:
            column_mapping['COP_DELIV_QTY'] = 'deliverable_volume'
        
        # Value columns
        if 'CH_TOT_TRADED_VAL' in df.columns:
            column_mapping['CH_TOT_TRADED_VAL'] = 'turnover'
        
        # Rename columns (no duplicates)
        df = df.rename(columns=column_mapping)
        
        # Ensure date column exists and is parsed
        if 'date' not in df.columns:
            # Try to find any timestamp column
            for col in df.columns:
                if 'TIMESTAMP' in str(col).upper() or 'DATE' in str(col).upper():
                    try:
                        df['date'] = pd.to_datetime(df[col], errors='coerce').dt.date
                        break
                    except:
                        continue
        
        # Convert date to date type if it exists
        if 'date' in df.columns:
            try:
                # If already date type, keep it
                if not pd.api.types.is_datetime64_any_dtype(df['date']):
                    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
                else:
                    df['date'] = df['date'].dt.date
                # Drop rows where date parsing failed
                df = df.dropna(subset=['date'])
            except Exception as e:
                logger.warning(f"Date parsing error: {e}, trying alternative columns")
                # Try alternative timestamp columns
                for alt_col in ['CH_TIMESTAMP', 'TIMESTAMP', 'mTIMESTAMP']:
                    if alt_col in df.columns:
                        try:
                            df['date'] = pd.to_datetime(df[alt_col], errors='coerce').dt.date
                            df = df.dropna(subset=['date'])
                            break
                        except:
                            continue
                if 'date' not in df.columns or df['date'].isna().all():
                    logger.error(f"Could not parse date column")
                    return None
        
        # Convert numeric columns
        for col in ['open', 'high', 'low', 'close', 'volume', 'deliverable_volume', 'turnover']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        logger.error(f"Error fetching delivery data for {ticker}: {e}")
        return None


def fetch_fii_dii_data(target_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch FII/DII trading data from NSE.
    
    Args:
        target_date: Date to fetch data for (defaults to latest)
        
    Returns:
        Dictionary with FII/DII data or None if error
    """
    if not NSEPYTHON_AVAILABLE:
        logger.error("nsepython not available")
        return None
    
    try:
        # FII/DII data endpoint
        if target_date:
            url = f"https://www.nseindia.com/api/fii-dii-trading-data?date={target_date.strftime('%d-%m-%Y')}"
        else:
            url = "https://www.nseindia.com/api/fii-dii-trading-data"
        
        data = nsefetch(url)
        return data
    except Exception as e:
        logger.error(f"Error fetching FII/DII data: {e}")
        return None


def fetch_index_constituents(index_name: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch constituents of an index.
    
    Args:
        index_name: Index name (e.g., 'NIFTY 50', 'NIFTY BANK')
        
    Returns:
        List of dictionaries with constituent data (excluding the index itself) or None if error
    """
    if not NSEPYTHON_AVAILABLE:
        logger.error("nsepython not available")
        return None
    
    try:
        url = f"https://www.nseindia.com/api/equity-stockIndices?index={index_name.replace(' ', '%20')}"
        data = nsefetch(url)
        
        if not data or 'data' not in data:
            return None
        
        # Filter out the index itself (which has symbol matching index_name)
        # and return only individual stock constituents
        constituents = []
        for item in data['data']:
            symbol = item.get('symbol', '')
            identifier = item.get('identifier', '')
            
            # Skip if it's the index itself (not a stock)
            # Index entries typically have symbol matching the index name
            if symbol.upper() == index_name.upper():
                # This is the index itself, skip it
                continue
            
            # Only include items that look like individual stocks
            # Individual stocks typically don't have spaces in their symbol
            if symbol and ' ' not in symbol.strip() and len(symbol.strip()) > 0:
                constituents.append(item)
        
        return constituents if constituents else None
    except Exception as e:
        logger.error(f"Error fetching index constituents for {index_name}: {e}")
        return None


def fetch_option_chain(underlying: str, expiry_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch option chain data.
    
    Args:
        underlying: Underlying symbol (e.g., 'NIFTY', 'BANKNIFTY')
        expiry_date: Expiry date in DD-MMM-YYYY format (optional)
        
    Returns:
        Dictionary with option chain data or None if error
    """
    if not NSEPYTHON_AVAILABLE:
        logger.error("nsepython not available")
        return None
    
    try:
        if expiry_date:
            chain = fnolist(underlying, expiry_date)
        else:
            # Get current expiry
            chain = fnolist(underlying)
        return chain
    except Exception as e:
        logger.error(f"Error fetching option chain for {underlying}: {e}")
        return None


def fetch_bulk_deals(target_date: Optional[date] = None) -> Optional[pd.DataFrame]:
    """
    Fetch bulk deals data.
    
    Args:
        target_date: Date to fetch data for (defaults to latest)
        
    Returns:
        DataFrame with bulk deals data or None if error
    """
    if not NSEPYTHON_AVAILABLE:
        logger.error("nsepython not available")
        return None
    
    try:
        # Use get_bulkdeals function from nsepython
        if target_date:
            data = get_bulkdeals(target_date.strftime('%d-%m-%Y'))
        else:
            data = get_bulkdeals()
        
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict) and 'data' in data:
            return pd.DataFrame(data['data'])
        return None
    except Exception as e:
        logger.error(f"Error fetching bulk deals: {e}")
        return None


def fetch_block_deals(target_date: Optional[date] = None) -> Optional[pd.DataFrame]:
    """
    Fetch block deals data.
    
    Args:
        target_date: Date to fetch data for (defaults to latest)
        
    Returns:
        DataFrame with block deals data or None if error
    """
    if not NSEPYTHON_AVAILABLE:
        logger.error("nsepython not available")
        return None
    
    try:
        # Use get_blockdeals function from nsepython
        if target_date:
            data = get_blockdeals(target_date.strftime('%d-%m-%Y'))
        else:
            data = get_blockdeals()
        
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict) and 'data' in data:
            return pd.DataFrame(data['data'])
        return None
    except Exception as e:
        logger.error(f"Error fetching block deals: {e}")
        return None


def fetch_advance_decline() -> Optional[Dict[str, Any]]:
    """
    Fetch advance/decline data for the market.
    
    Returns:
        Dictionary with advance/decline data or None if error
    """
    if not NSEPYTHON_AVAILABLE:
        logger.error("nsepython not available")
        return None
    
    try:
        url = "https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O"
        data = nsefetch(url)
        return data
    except Exception as e:
        logger.error(f"Error fetching advance/decline data: {e}")
        return None


def fetch_market_status() -> Optional[Dict[str, Any]]:
    """
    Fetch market status (open/closed).
    
    Returns:
        Dictionary with market status or None if error
    """
    if not NSEPYTHON_AVAILABLE:
        logger.error("nsepython not available")
        return None
    
    try:
        # Try to fetch a simple endpoint to check if market is open
        url = "https://www.nseindia.com/api/marketStatus"
        data = nsefetch(url)
        return data
    except Exception as e:
        logger.error(f"Error fetching market status: {e}")
        return None

