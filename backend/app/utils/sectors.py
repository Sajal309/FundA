"""Utilities for canonical sector management."""
import yaml
from pathlib import Path
from typing import List, Dict

# Cache for canonical sectors
_canonical_sectors_cache: List[Dict[str, str]] = None


def get_canonical_sectors() -> List[Dict[str, str]]:
    """
    Get the canonical list of sectors from config/sectors.yaml.
    
    Returns:
        List of sector dictionaries with 'id' and 'name' keys
    """
    global _canonical_sectors_cache
    
    if _canonical_sectors_cache is not None:
        return _canonical_sectors_cache
    
    # Load from config file
    config_path = Path(__file__).parent.parent.parent / "config" / "sectors.yaml"
    
    if not config_path.exists():
        # Fallback to default sectors if config doesn't exist
        _canonical_sectors_cache = [
            {"id": "NIFTY_AUTO", "name": "Nifty Auto"},
            {"id": "NIFTY_BANK", "name": "Nifty Bank"},
            {"id": "NIFTY_FMCG", "name": "Nifty FMCG"},
            {"id": "NIFTY_IT", "name": "Nifty IT"},
            {"id": "NIFTY_PHARMA", "name": "Nifty Pharma"},
            {"id": "NIFTY_METAL", "name": "Nifty Metal"},
            {"id": "NIFTY_REALTY", "name": "Nifty Realty"},
            {"id": "NIFTY_ENERGY", "name": "Nifty Energy"},
            {"id": "NIFTY_INFRA", "name": "Nifty Infrastructure"},
        ]
        return _canonical_sectors_cache
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            _canonical_sectors_cache = config.get('sectors', [])
            return _canonical_sectors_cache
    except Exception as e:
        from app.utils import logger
        logger.warning(f"Failed to load sectors config: {e}, using defaults")
        # Return defaults
        _canonical_sectors_cache = [
            {"id": "NIFTY_AUTO", "name": "Nifty Auto"},
            {"id": "NIFTY_BANK", "name": "Nifty Bank"},
            {"id": "NIFTY_FMCG", "name": "Nifty FMCG"},
            {"id": "NIFTY_IT", "name": "Nifty IT"},
            {"id": "NIFTY_PHARMA", "name": "Nifty Pharma"},
            {"id": "NIFTY_METAL", "name": "Nifty Metal"},
            {"id": "NIFTY_REALTY", "name": "Nifty Realty"},
            {"id": "NIFTY_ENERGY", "name": "Nifty Energy"},
            {"id": "NIFTY_INFRA", "name": "Nifty Infrastructure"},
        ]
        return _canonical_sectors_cache


def get_canonical_sector_ids() -> List[str]:
    """Get list of canonical sector IDs only."""
    return [s["id"] for s in get_canonical_sectors()]


def is_canonical_sector(sector_id: str) -> bool:
    """Check if a sector ID is in the canonical list."""
    return sector_id in get_canonical_sector_ids()

