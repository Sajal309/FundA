"""Script to help ingest data for all supported market indices.

This script provides utilities to fetch and ingest data for all the comprehensive
market indices defined in the system.

Usage:
    python -m app.scripts.ingest_all_indices --help
    python -m app.scripts.ingest_all_indices --list
    python -m app.scripts.ingest_all_indices --fetch-yfinance --sector NIFTY_50
    python -m app.scripts.ingest_all_indices --fetch-all-yfinance
"""
import argparse
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.database import SessionLocal
from app.api.v1.sectors import SECTOR_NAMES
from app.services.fetch_nse import NSE_INDEX_SYMBOLS
from app.utils import logger


def get_all_supported_indices() -> Dict[str, str]:
    """Get all supported indices with their display names."""
    return SECTOR_NAMES


def list_all_indices():
    """List all supported indices."""
    indices = get_all_supported_indices()
    
    print("\n" + "="*80)
    print("SUPPORTED MARKET INDICES")
    print("="*80)
    
    # Group by category
    broad_market = []
    sectoral = []
    thematic = []
    
    for sector_id, name in indices.items():
        if any(x in sector_id for x in ['50', '100', '200', '500', 'MIDCAP', 'SMALLCAP', 'NEXT']):
            broad_market.append((sector_id, name))
        elif sector_id.startswith('NIFTY_') and sector_id not in [x[0] for x in broad_market]:
            if any(x in sector_id for x in ['GROWTH', 'DIVIDEND', 'QUALITY', 'VOLATILITY', 'ALPHA', 'BETA']):
                thematic.append((sector_id, name))
            else:
                sectoral.append((sector_id, name))
        else:
            sectoral.append((sector_id, name))
    
    print("\n📊 BROAD MARKET INDICES:")
    for sector_id, name in sorted(broad_market):
        nse_symbol = NSE_INDEX_SYMBOLS.get(sector_id, 'N/A')
        print(f"  • {sector_id:30s} → {name:40s} (NSE: {nse_symbol})")
    
    print("\n🏭 SECTORAL INDICES:")
    for sector_id, name in sorted(sectoral):
        nse_symbol = NSE_INDEX_SYMBOLS.get(sector_id, 'N/A')
        print(f"  • {sector_id:30s} → {name:40s} (NSE: {nse_symbol})")
    
    print("\n🎯 THEMATIC INDICES:")
    for sector_id, name in sorted(thematic):
        nse_symbol = NSE_INDEX_SYMBOLS.get(sector_id, 'N/A')
        print(f"  • {sector_id:30s} → {name:40s} (NSE: {nse_symbol})")
    
    print(f"\n{'='*80}")
    print(f"Total: {len(indices)} indices supported")
    print("="*80 + "\n")


def fetch_yfinance_data(sector_id: str, days: int = 365):
    """Fetch data for a sector using yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        logger.error("yfinance not installed. Install with: pip install yfinance")
        return False
    
    nse_symbol = NSE_INDEX_SYMBOLS.get(sector_id)
    if not nse_symbol:
        logger.error(f"No NSE symbol mapping found for {sector_id}")
        return False
    
    # Map NSE indices to yfinance symbols
    # yfinance uses specific formats for NSE indices
    yfinance_symbol_map = {
        'NIFTY 50': '^NSEI',
        'NIFTY BANK': '^NSEBANK',
        'NIFTY IT': '^NSETIT',
        'NIFTY FMCG': '^NSETFMCG',
        'NIFTY PHARMA': '^NSETPHARMA',
        'NIFTY AUTO': '^NSETAUTO',
        'NIFTY ENERGY': '^NSETENERGY',
        'NIFTY METAL': '^NSETMETAL',
        'NIFTY REALTY': '^NSETREALTY',
        'NIFTY PSU BANK': '^NSETPSU',
        'NIFTY PRIVATE BANK': '^NSETPRIVATE',
        'NIFTY NEXT 50': '^NSENEXT50',
        'NIFTY 100': '^NSEI100',
        'NIFTY 200': '^NSEI200',
        'NIFTY 500': '^NSEI500',
        'NIFTY MIDCAP 50': '^NSEMIDCAP50',
        'NIFTY MIDCAP 100': '^NSEMIDCAP100',
        'NIFTY MIDCAP 150': '^NSEMIDCAP150',
        'NIFTY SMALLCAP 50': '^NSESMALLCAP50',
        'NIFTY SMALLCAP 100': '^NSESMALLCAP100',
        'NIFTY SMALLCAP 250': '^NSESMALLCAP250',
    }
    
    # Try mapped symbol first
    yf_symbol = yfinance_symbol_map.get(nse_symbol)
    
    # If not found, try generic format
    if not yf_symbol:
        # For indices not in map, try removing spaces and using ^NSE prefix
        clean_symbol = nse_symbol.replace(' ', '').replace('&', '').replace('-', '')
        if clean_symbol.startswith('NIFTY'):
            # Try ^NSEI format for NIFTY indices
            yf_symbol = f"^NSE{clean_symbol.replace('NIFTY', '')}"
        else:
            yf_symbol = f"^{clean_symbol}"
    
    logger.info(f"Fetching data for {sector_id} using yfinance symbol: {yf_symbol}")
    
    try:
        ticker = yf.Ticker(yf_symbol)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        hist = ticker.history(start=start_date, end=end_date)
        
        if hist.empty:
            logger.warning(f"No data returned for {yf_symbol}")
            return False
        
        logger.info(f"Fetched {len(hist)} records for {sector_id}")
        
        # Save to CSV for ingestion
        output_dir = Path(__file__).parent.parent.parent / "sample_data"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{sector_id.lower()}_timeseries.csv"
        
        # Format for ingestion - check what format ingestion expects
        hist.reset_index(inplace=True)
        hist['sector_id'] = sector_id
        # Convert Date to datetime if needed
        if 'Date' in hist.columns:
            hist['ts'] = pd.to_datetime(hist['Date'])
        else:
            hist['ts'] = hist.index
        hist['date'] = hist['ts'].dt.date  # Add date column for ingestion
        hist['open'] = hist['Open']
        hist['high'] = hist['High']
        hist['low'] = hist['Low']
        hist['close'] = hist['Close']
        hist['volume'] = hist['Volume'].fillna(0).astype(int)
        
        # Output columns - include both ts and date
        output_cols = ['sector_id', 'date', 'ts', 'open', 'high', 'low', 'close', 'volume']
        hist[output_cols].to_csv(output_file, index=False)
        
        logger.info(f"Saved data to {output_file}")
        logger.info(f"To ingest: python -m app.services.ingestion ingest_from_csv {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error fetching data for {sector_id}: {e}")
        return False


def fetch_all_yfinance(days: int = 365):
    """Fetch data for all supported indices."""
    indices = get_all_supported_indices()
    success_count = 0
    failed = []
    
    logger.info(f"Fetching data for {len(indices)} indices...")
    
    for sector_id in indices.keys():
        if fetch_yfinance_data(sector_id, days):
            success_count += 1
        else:
            failed.append(sector_id)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Fetch complete: {success_count}/{len(indices)} successful")
    if failed:
        logger.warning(f"Failed indices: {', '.join(failed)}")
    logger.info(f"{'='*80}\n")
    
    return success_count, failed


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description='Utilities for ingesting data for all supported market indices'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all supported indices'
    )
    parser.add_argument(
        '--fetch-yfinance',
        action='store_true',
        help='Fetch data using yfinance for a specific sector'
    )
    parser.add_argument(
        '--fetch-all-yfinance',
        action='store_true',
        help='Fetch data using yfinance for all sectors'
    )
    parser.add_argument(
        '--sector',
        type=str,
        help='Specific sector ID to fetch (e.g., NIFTY_50)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='Number of days of historical data to fetch (default: 365)'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_all_indices()
    elif args.fetch_yfinance:
        if not args.sector:
            logger.error("--sector required when using --fetch-yfinance")
            sys.exit(1)
        if args.sector not in SECTOR_NAMES:
            logger.error(f"Unknown sector: {args.sector}")
            logger.info("Use --list to see all supported sectors")
            sys.exit(1)
        fetch_yfinance_data(args.sector, args.days)
    elif args.fetch_all_yfinance:
        fetch_all_yfinance(args.days)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

