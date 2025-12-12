"""Service to fetch sector/index data from NSE."""
from datetime import date, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from decimal import Decimal
from app.db import models
from app.utils import logger


def fetch_sector_index_data_from_nse(sector_id: str, target_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch sector/index data from NSE using nsepython.
    
    Args:
        sector_id: Sector/index ID (e.g., 'NIFTY_50', 'NIFTY_BANK')
        target_date: Date to fetch data for (defaults to latest)
        
    Returns:
        Dictionary with sector data or None if error
    """
    try:
        from app.services import nsepython_service
        
        if not nsepython_service.is_available():
            logger.warning("nsepython not available for sector data")
            return None
        
        # Map sector_id to NSE index name
        sector_name_map = {
            'NIFTY_50': 'NIFTY 50',
            'NIFTY_NEXT_50': 'NIFTY NEXT 50',
            'NIFTY_100': 'NIFTY 100',
            'NIFTY_200': 'NIFTY 200',
            'NIFTY_500': 'NIFTY 500',
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
        }
        
        sector_name = sector_name_map.get(sector_id, sector_id.replace('_', ' '))
        
        # Fetch sector data
        data = nsepython_service.fetch_sector_data(sector_name)
        
        if data and 'data' in data and len(data['data']) > 0:
            # Get the index itself (first entry or aggregate)
            index_data = data['data'][0] if isinstance(data['data'], list) else data
            
            return {
                'sector_id': sector_id,
                'name': sector_name,
                'last_price': float(index_data.get('lastPrice', 0)),
                'change': float(index_data.get('change', 0)),
                'change_pct': float(index_data.get('pChange', 0)),
                'open': float(index_data.get('open', 0)),
                'high': float(index_data.get('dayHigh', 0)),
                'low': float(index_data.get('dayLow', 0)),
                'volume': int(index_data.get('totalTradedVolume', 0)),
                'value': float(index_data.get('totalTradedValue', 0)),
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error fetching sector data from NSE for {sector_id}: {e}")
        return None


def fetch_sector_constituents_from_nse(sector_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch sector/index constituents from NSE.
    
    Args:
        sector_id: Sector/index ID
        
    Returns:
        List of constituent dictionaries or None if error
    """
    try:
        from app.services import nsepython_service
        
        if not nsepython_service.is_available():
            return None
        
        # Map sector_id to NSE index name
        sector_name_map = {
            'NIFTY_50': 'NIFTY 50',
            'NIFTY_BANK': 'NIFTY BANK',
            'NIFTY_IT': 'NIFTY IT',
            # Add more mappings as needed
        }
        
        sector_name = sector_name_map.get(sector_id, sector_id.replace('_', ' '))
        
        # Fetch constituents
        constituents = nsepython_service.fetch_index_constituents(sector_name)
        
        if constituents:
            return [
                {
                    'ticker': c.get('symbol', ''),
                    'name': c.get('identifier', ''),
                    'weight': float(c.get('weight', 0)),
                    'last_price': float(c.get('lastPrice', 0)),
                }
                for c in constituents
                if c.get('symbol')
            ]
        
        return None
        
    except Exception as e:
        logger.error(f"Error fetching constituents from NSE for {sector_id}: {e}")
        return None

