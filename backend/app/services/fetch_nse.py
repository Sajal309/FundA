"""NSE (National Stock Exchange) data fetching service."""
import requests
import pandas as pd
import time
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict
from app.utils import logger


# NSE index symbols mapping - Comprehensive market indices
NSE_INDEX_SYMBOLS = {
    # Broad Market Indices
    'NIFTY_50': 'NIFTY 50',
    'NIFTY_NEXT_50': 'NIFTY NEXT 50',
    'NIFTY_100': 'NIFTY 100',
    'NIFTY_200': 'NIFTY 200',
    'NIFTY_500': 'NIFTY 500',
    'NIFTY_MIDCAP_50': 'NIFTY MIDCAP 50',
    'NIFTY_MIDCAP_100': 'NIFTY MIDCAP 100',
    'NIFTY_MIDCAP_150': 'NIFTY MIDCAP 150',
    'NIFTY_SMALLCAP_50': 'NIFTY SMALLCAP 50',
    'NIFTY_SMALLCAP_100': 'NIFTY SMALLCAP 100',
    'NIFTY_SMALLCAP_250': 'NIFTY SMALLCAP 250',
    # Sectoral Indices
    'NIFTY_BANK': 'NIFTY BANK',
    'NIFTY_IT': 'NIFTY IT',
    'NIFTY_FMCG': 'NIFTY FMCG',
    'NIFTY_PHARMA': 'NIFTY PHARMA',
    'NIFTY_AUTO': 'NIFTY AUTO',
    'NIFTY_ENERGY': 'NIFTY ENERGY',
    'NIFTY_METAL': 'NIFTY METAL',
    'NIFTY_REALTY': 'NIFTY REALTY',
    'NIFTY_PSU_BANK': 'NIFTY PSU BANK',
    'NIFTY_PRIVATE_BANK': 'NIFTY PRIVATE BANK',
    'NIFTY_FIN_SERVICE': 'NIFTY FINANCIAL SERVICES',
    'NIFTY_HEALTHCARE': 'NIFTY HEALTHCARE',
    'NIFTY_CONSUMER_DURABLES': 'NIFTY CONSUMER DURABLES',
    'NIFTY_INFRA': 'NIFTY INFRASTRUCTURE',
    'NIFTY_OIL_GAS': 'NIFTY OIL & GAS',
    'NIFTY_PSE': 'NIFTY PSE',
    'NIFTY_SERVICES': 'NIFTY SERVICES',
    'NIFTY_COMMODITIES': 'NIFTY COMMODITIES',
    # Thematic Indices
    'NIFTY_GROWTH_SECTORS_15': 'NIFTY GROWTH SECTORS 15',
    'NIFTY_DIVIDEND_OPPORTUNITIES_50': 'NIFTY DIVIDEND OPPORTUNITIES 50',
    'NIFTY_QUALITY_30': 'NIFTY QUALITY 30',
    'NIFTY_LOW_VOLATILITY_50': 'NIFTY LOW VOLATILITY 50',
    'NIFTY_ALPHA_50': 'NIFTY ALPHA 50',
    'NIFTY_HIGH_BETA_50': 'NIFTY HIGH BETA 50',
}


def get_nse_session() -> requests.Session:
    """
    Get a requests session with NSE headers and cookies.
    NSE requires visiting the homepage first to get session cookies.
    
    Returns:
        Configured requests session with cookies
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.nseindia.com/',
        'Origin': 'https://www.nseindia.com',
    })
    
    # NSE requires visiting homepage first to get cookies
    try:
        session.get('https://www.nseindia.com/', timeout=10)
        time.sleep(0.5)  # Small delay to avoid rate limiting
    except Exception as e:
        logger.warning(f"Could not initialize NSE session cookies: {e}")
    
    return session


def get_nse_index_code(index_name: str) -> str:
    """
    Convert NSE index name to NSE index code.
    NSE uses specific codes for indices (e.g., 'NIFTY 50' -> 'NIFTY 50' or 'NIFTY50').
    
    Args:
        index_name: Display name of the index (e.g., 'NIFTY BANK')
        
    Returns:
        NSE index code
    """
    # NSE index codes - mapping display names to API codes
    index_code_map = {
        'NIFTY 50': 'NIFTY 50',
        'NIFTY NEXT 50': 'NIFTY NEXT 50',
        'NIFTY 100': 'NIFTY 100',
        'NIFTY 200': 'NIFTY 200',
        'NIFTY 500': 'NIFTY 500',
        'NIFTY MIDCAP 50': 'NIFTY MIDCAP 50',
        'NIFTY MIDCAP 100': 'NIFTY MIDCAP 100',
        'NIFTY MIDCAP 150': 'NIFTY MIDCAP 150',
        'NIFTY SMALLCAP 50': 'NIFTY SMALLCAP 50',
        'NIFTY SMALLCAP 100': 'NIFTY SMALLCAP 100',
        'NIFTY SMALLCAP 250': 'NIFTY SMALLCAP 250',
        'NIFTY BANK': 'NIFTY BANK',
        'NIFTY IT': 'NIFTY IT',
        'NIFTY FMCG': 'NIFTY FMCG',
        'NIFTY PHARMA': 'NIFTY PHARMA',
        'NIFTY AUTO': 'NIFTY AUTO',
        'NIFTY ENERGY': 'NIFTY ENERGY',
        'NIFTY METAL': 'NIFTY METAL',
        'NIFTY REALTY': 'NIFTY REALTY',
        'NIFTY PSU BANK': 'NIFTY PSU BANK',
        'NIFTY PRIVATE BANK': 'NIFTY PRIVATE BANK',
        'NIFTY FINANCIAL SERVICES': 'NIFTY FINANCIAL SERVICES',
        'NIFTY HEALTHCARE': 'NIFTY HEALTHCARE',
        'NIFTY CONSUMER DURABLES': 'NIFTY CONSUMER DURABLES',
        'NIFTY INFRASTRUCTURE': 'NIFTY INFRASTRUCTURE',
        'NIFTY OIL & GAS': 'NIFTY OIL & GAS',
        'NIFTY PSE': 'NIFTY PSE',
        'NIFTY SERVICES': 'NIFTY SERVICES',
        'NIFTY COMMODITIES': 'NIFTY COMMODITIES',
        'NIFTY GROWTH SECTORS 15': 'NIFTY GROWTH SECTORS 15',
        'NIFTY DIVIDEND OPPORTUNITIES 50': 'NIFTY DIVIDEND OPPORTUNITIES 50',
        'NIFTY QUALITY 30': 'NIFTY QUALITY 30',
        'NIFTY LOW VOLATILITY 50': 'NIFTY LOW VOLATILITY 50',
        'NIFTY ALPHA 50': 'NIFTY ALPHA 50',
        'NIFTY HIGH BETA 50': 'NIFTY HIGH BETA 50',
    }
    return index_code_map.get(index_name, index_name)


def fetch_nse_index_history(
    index_name: str,
    from_date: date,
    to_date: date,
    session: Optional[requests.Session] = None
) -> pd.DataFrame:
    """
    Fetch historical index data from NSE using their historical indices API.
    
    NSE API endpoint: /api/historical/indices
    Note: NSE's public API has rate limits. Add delays between requests.
    
    Args:
        index_name: NSE index name (e.g., 'NIFTY BANK')
        from_date: Start date
        to_date: End date
        session: Optional requests session (for rate limiting)
        
    Returns:
        DataFrame with OHLCV data (columns: Date, Open, High, Low, Close, Volume)
    """
    if session is None:
        session = get_nse_session()
    
    index_code = get_nse_index_code(index_name)
    
    # NSE historical indices API endpoint
    base_url = "https://www.nseindia.com/api/historical/indices"
    
    try:
        # NSE API parameters - format may vary by endpoint
        # Try different parameter formats
        params = {
            'index': index_code,
            'from': from_date.strftime('%d-%m-%Y'),
            'to': to_date.strftime('%d-%m-%Y'),
        }
        
        # Alternative: try with different date format
        # Some NSE endpoints use YYYY-MM-DD format
        alt_params = {
            'index': index_code,
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
        }
        
        logger.info(f"Fetching NSE data for {index_name} ({index_code}) from {from_date} to {to_date}")
        
        # NSE uses chart data API for historical data
        # Try chart data endpoint first (more reliable)
        chart_url = "https://www.nseindia.com/api/chart-databyindex"
        chart_params = {
            'index': index_code,
            'indices': 'true',
        }
        
        # Try chart data API first (this is the most reliable endpoint)
        try:
            response = session.get(chart_url, params=chart_params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                # Chart API returns structure with 'grapthData' key
                if 'grapthData' in data:
                    chart_data = data['grapthData']
                    if chart_data and isinstance(chart_data, list) and len(chart_data) > 0:
                        records = []
                        for item in chart_data:
                            try:
                                # Chart data format: [timestamp_ms, close_price]
                                # Timestamp is in milliseconds since epoch
                                if isinstance(item, list) and len(item) >= 2:
                                    timestamp_ms = int(item[0])
                                    close_price = float(item[1])
                                    
                                    # Convert milliseconds to datetime
                                    dt = pd.to_datetime(timestamp_ms, unit='ms')
                                    
                                    # Chart API only provides close prices, use same for OHLC
                                    records.append({
                                        'Date': dt,
                                        'Open': close_price,
                                        'High': close_price,
                                        'Low': close_price,
                                        'Close': close_price,
                                        'Volume': 0,  # Chart API doesn't provide volume
                                    })
                            except Exception as e:
                                logger.debug(f"Error parsing chart data item: {e}, item: {item}")
                                continue
                        
                        if records:
                            df = pd.DataFrame(records)
                            df = df.sort_values('Date')
                            # Filter by date range
                            df = df[(df['Date'] >= pd.Timestamp(from_date)) & (df['Date'] <= pd.Timestamp(to_date))]
                            if len(df) > 0:
                                logger.info(f"✅ Fetched {len(df)} records from NSE chart API for {index_name}")
                                return df
                            else:
                                logger.warning(f"Chart API returned data but none in date range {from_date} to {to_date}")
                else:
                    logger.debug(f"Chart API response missing 'grapthData' key. Keys: {list(data.keys())}")
        except Exception as e:
            logger.debug(f"Chart API failed: {e}")
        
        # Try equity-stockIndices API (returns historical data for constituents, not the index itself)
        # This endpoint may not work for all indexes, but worth trying
        try:
            response = session.get(equity_url, params=equity_params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                # This endpoint returns constituent data, not index history
                # Skip this for now as it doesn't provide index-level historical data
                logger.debug(f"Equity API returned data but it's for constituents, not index history")
        except Exception as e:
            logger.debug(f"Equity API failed: {e}")
        
        # Fallback to historical indices endpoint
        endpoints_to_try = [
            ("https://www.nseindia.com/api/historicalIndices", params),
            ("https://www.nseindia.com/api/historical/indices", params),
            ("https://www.nseindia.com/api/historicalIndices", alt_params),
            ("https://www.nseindia.com/api/historical/indices", alt_params),
        ]
        
        response = None
        for endpoint_url, endpoint_params in endpoints_to_try:
            try:
                response = session.get(endpoint_url, params=endpoint_params, timeout=15)
                if response.status_code == 200:
                    break
                elif response.status_code == 404:
                    continue  # Try next endpoint
                else:
                    logger.debug(f"Endpoint {endpoint_url} returned {response.status_code}")
                    continue
            except Exception as e:
                logger.debug(f"Error trying endpoint {endpoint_url}: {e}")
                continue
        
        if response is None or response.status_code != 200:
            logger.warning(f"NSE API returned status {response.status_code if response else 'None'} for {index_name}")
            return pd.DataFrame()
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse NSE response - structure: {"data": [{"TIMESTAMP": "...", "OPEN": ..., "HIGH": ..., "LOW": ..., "CLOSE": ..., "VOLUME": ...}]}
            if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                records = []
                for record in data['data']:
                    try:
                        # NSE returns dates in various formats, try to parse
                        date_str = record.get('TIMESTAMP', record.get('Date', record.get('date', '')))
                        if isinstance(date_str, str):
                            # Try multiple date formats
                            try:
                                dt = pd.to_datetime(date_str, format='%d-%b-%Y')
                            except:
                                try:
                                    dt = pd.to_datetime(date_str, format='%Y-%m-%d')
                                except:
                                    dt = pd.to_datetime(date_str)
                        else:
                            dt = pd.to_datetime(date_str)
                        
                        records.append({
                            'Date': dt,
                            'Open': float(record.get('OPEN', record.get('Open', record.get('open', 0)))),
                            'High': float(record.get('HIGH', record.get('High', record.get('high', 0)))),
                            'Low': float(record.get('LOW', record.get('Low', record.get('low', 0)))),
                            'Close': float(record.get('CLOSE', record.get('Close', record.get('close', 0)))),
                            'Volume': int(record.get('VOLUME', record.get('Volume', record.get('volume', 0)))),
                        })
                    except Exception as e:
                        logger.debug(f"Error parsing record: {e}")
                        continue
                
                if records:
                    df = pd.DataFrame(records)
                    df = df.sort_values('Date')
                    logger.info(f"✅ Fetched {len(df)} records from NSE for {index_name}")
                    return df
                else:
                    logger.warning(f"No valid records found in NSE response for {index_name}")
                    return pd.DataFrame()
            else:
                logger.warning(f"NSE API returned empty data for {index_name}")
                return pd.DataFrame()
        elif response.status_code == 403:
            logger.warning(f"NSE API returned 403 (Forbidden) for {index_name}. May need to refresh session cookies.")
            # Try to refresh session
            session = get_nse_session()
            time.sleep(1)
            response = session.get(base_url, params=params, timeout=15)
            if response.status_code == 200:
                # Retry parsing
                data = response.json()
                if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                    # Same parsing logic as above
                    records = []
                    for record in data['data']:
                        try:
                            date_str = record.get('TIMESTAMP', record.get('Date', record.get('date', '')))
                            dt = pd.to_datetime(date_str, errors='coerce')
                            records.append({
                                'Date': dt,
                                'Open': float(record.get('OPEN', record.get('Open', record.get('open', 0)))),
                                'High': float(record.get('HIGH', record.get('High', record.get('high', 0)))),
                                'Low': float(record.get('LOW', record.get('Low', record.get('low', 0)))),
                                'Close': float(record.get('CLOSE', record.get('Close', record.get('close', 0)))),
                                'Volume': int(record.get('VOLUME', record.get('Volume', record.get('volume', 0)))),
                            })
                        except:
                            continue
                    if records:
                        df = pd.DataFrame(records)
                        df = df.sort_values('Date')
                        logger.info(f"✅ Fetched {len(df)} records from NSE for {index_name} (after retry)")
                        return df
            return pd.DataFrame()
        else:
            logger.warning(f"NSE API returned status {response.status_code} for {index_name}: {response.text[:200]}")
            return pd.DataFrame()
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching NSE data for {index_name}: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching NSE data for {index_name}: {e}")
        return pd.DataFrame()


def fetch_nse_index_eod(
    index_name: str,
    target_date: Optional[date] = None
) -> Optional[Dict]:
    """
    Fetch end-of-day data for an NSE index.
    
    Args:
        index_name: NSE index name
        target_date: Date to fetch (defaults to latest)
        
    Returns:
        Dictionary with OHLCV data or None
    """
    if target_date is None:
        target_date = date.today()
    
    # Try to fetch from NSE
    df = fetch_nse_index_history(index_name, target_date, target_date)
    
    if df.empty:
        return None
    
    # Return latest row as dict
    if len(df) > 0:
        row = df.iloc[-1]
        return {
            'date': target_date,
            'open': float(row.get('open', 0)),
            'high': float(row.get('high', 0)),
            'low': float(row.get('low', 0)),
            'close': float(row.get('close', 0)),
            'volume': int(row.get('volume', 0)),
        }
    
    return None


def fetch_nse_fii_dii_flows(
    target_date: Optional[date] = None,
    session: Optional[requests.Session] = None
) -> Optional[Dict]:
    """
    Fetch FII/DII flow data from NSE.
    
    NSE provides FII/DII reports at: https://www.nseindia.com/reports/fii-dii
    
    Args:
        target_date: Date to fetch (defaults to latest)
        session: Optional requests session
        
    Returns:
        Dictionary with FII/DII flow data or None
    """
    if session is None:
        session = get_nse_session()
    
    # NSE FII/DII report URL
    url = "https://www.nseindia.com/api/fii-dii"
    
    try:
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Parse NSE response (structure varies)
            logger.info(f"Fetched FII/DII data from NSE")
            return data
        else:
            logger.warning(f"NSE FII/DII API returned status {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching FII/DII data from NSE: {e}")
        return None

