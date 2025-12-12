"""Script to fetch all NSE stocks and populate the database."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import date
from app.db import database, models
from app.utils import logger
from app.services import nsepython_service


def fetch_all_nse_stocks(db):
    """
    Fetch all NSE stocks and add them to the database.
    
    Strategy:
    1. Fetch all major index constituents (NIFTY 50, 100, 200, 500, etc.)
    2. Fetch sectoral index constituents
    3. Combine and deduplicate
    4. Store in database with sector mapping
    """
    all_stocks = {}
    
    # Major indices to fetch
    major_indices = [
        'NIFTY 50',
        'NIFTY NEXT 50',
        'NIFTY 100',
        'NIFTY 200',
        'NIFTY 500',
        'NIFTY MIDCAP 50',
        'NIFTY MIDCAP 100',
        'NIFTY MIDCAP 150',
        'NIFTY SMALLCAP 50',
        'NIFTY SMALLCAP 100',
        'NIFTY SMALLCAP 250',
    ]
    
    # Sectoral indices
    sectoral_indices = [
        'NIFTY AUTO',
        'NIFTY BANK',
        'NIFTY FINANCIAL SERVICES',
        'NIFTY FMCG',
        'NIFTY IT',
        'NIFTY MEDIA',
        'NIFTY METAL',
        'NIFTY PHARMA',
        'NIFTY PRIVATE BANK',
        'NIFTY PSU BANK',
        'NIFTY REALTY',
        'NIFTY ENERGY',
        'NIFTY INFRASTRUCTURE',
        'NIFTY HEALTHCARE',
        'NIFTY CONSUMER DURABLES',
        'NIFTY OIL & GAS',
        'NIFTY PSE',
        'NIFTY SERVICES',
        'NIFTY COMMODITIES',
    ]
    
    all_indices = major_indices + sectoral_indices
    
    logger.info(f"Fetching stocks from {len(all_indices)} indices...")
    
    # Map index names to sector_ids
    index_to_sector = {
        'NIFTY 50': 'NIFTY_50',
        'NIFTY NEXT 50': 'NIFTY_NEXT_50',
        'NIFTY 100': 'NIFTY_100',
        'NIFTY 200': 'NIFTY_200',
        'NIFTY 500': 'NIFTY_500',
        'NIFTY MIDCAP 50': 'NIFTY_MIDCAP_50',
        'NIFTY MIDCAP 100': 'NIFTY_MIDCAP_100',
        'NIFTY MIDCAP 150': 'NIFTY_MIDCAP_150',
        'NIFTY SMALLCAP 50': 'NIFTY_SMALLCAP_50',
        'NIFTY SMALLCAP 100': 'NIFTY_SMALLCAP_100',
        'NIFTY SMALLCAP 250': 'NIFTY_SMALLCAP_250',
        'NIFTY AUTO': 'NIFTY_AUTO',
        'NIFTY BANK': 'NIFTY_BANK',
        'NIFTY FINANCIAL SERVICES': 'NIFTY_FIN_SERVICE',
        'NIFTY FMCG': 'NIFTY_FMCG',
        'NIFTY IT': 'NIFTY_IT',
        'NIFTY MEDIA': 'NIFTY_MEDIA',
        'NIFTY METAL': 'NIFTY_METAL',
        'NIFTY PHARMA': 'NIFTY_PHARMA',
        'NIFTY PRIVATE BANK': 'NIFTY_PRIVATE_BANK',
        'NIFTY PSU BANK': 'NIFTY_PSU_BANK',
        'NIFTY REALTY': 'NIFTY_REALTY',
        'NIFTY ENERGY': 'NIFTY_ENERGY',
        'NIFTY INFRASTRUCTURE': 'NIFTY_INFRA',
        'NIFTY HEALTHCARE': 'NIFTY_HEALTHCARE',
        'NIFTY CONSUMER DURABLES': 'NIFTY_CONSUMER_DURABLES',
        'NIFTY OIL & GAS': 'NIFTY_OIL_GAS',
        'NIFTY PSE': 'NIFTY_PSE',
        'NIFTY SERVICES': 'NIFTY_SERVICES',
        'NIFTY COMMODITIES': 'NIFTY_COMMODITIES',
    }
    
    for index_name in all_indices:
        try:
            logger.info(f"Fetching {index_name}...")
            constituents = nsepython_service.fetch_index_constituents(index_name)
            
            if not constituents:
                logger.warning(f"No constituents found for {index_name}")
                continue
            
            sector_id = index_to_sector.get(index_name)
            
            for stock_data in constituents:
                ticker = stock_data.get('symbol') or stock_data.get('ticker') or stock_data.get('identifier')
                if not ticker:
                    continue
                
                # Normalize ticker (remove .NS suffix if present, remove spaces)
                ticker = ticker.replace('.NS', '').replace('.NSE', '').strip()
                
                # Skip if ticker contains spaces (likely an index, not a stock)
                if ' ' in ticker:
                    continue
                
                # Get company name from various possible fields
                company_name = (
                    stock_data.get('companyName') or 
                    stock_data.get('name') or 
                    stock_data.get('meta', {}).get('companyName') or
                    ticker.replace('-', ' ').title()
                )
                
                # If stock already exists, add this sector to its sectors list
                if ticker in all_stocks:
                    existing = all_stocks[ticker]
                    if sector_id and sector_id not in existing.get('sectors', []):
                        existing['sectors'].append(sector_id)
                else:
                    all_stocks[ticker] = {
                        'ticker': ticker,
                        'company_name': company_name,
                        'sectors': [sector_id] if sector_id else [],
                        'exchange': 'NSE',
                    }
            
            logger.info(f"  ✅ Added {len(constituents)} stocks from {index_name}")
            
        except Exception as e:
            logger.error(f"Error fetching {index_name}: {e}")
            continue
    
    logger.info(f"\nTotal unique stocks found: {len(all_stocks)}")
    
    # Store in database
    added_count = 0
    updated_count = 0
    
    for ticker, stock_info in all_stocks.items():
        # Use primary sector (first one) or None
        primary_sector = stock_info['sectors'][0] if stock_info['sectors'] else None
        
        existing = db.query(models.Stock).filter(models.Stock.ticker == ticker).first()
        
        if existing:
            # Update existing stock
            if primary_sector and not existing.sector_id:
                existing.sector_id = primary_sector
            updated_count += 1
        else:
            # Create new stock
            stock = models.Stock(
                ticker=ticker,
                company_name=stock_info['company_name'],
                sector_id=primary_sector,
                exchange=stock_info['exchange'],
                shares_outstanding=1000000000  # Default, will be updated from fundamentals
            )
            db.add(stock)
            added_count += 1
        
        if (added_count + updated_count) % 100 == 0:
            db.commit()
            logger.info(f"Processed {added_count + updated_count} stocks...")
    
    db.commit()
    
    logger.info(f"\n✅ Stock fetch complete!")
    logger.info(f"   Added: {added_count} new stocks")
    logger.info(f"   Updated: {updated_count} existing stocks")
    logger.info(f"   Total unique stocks: {len(all_stocks)}")
    
    return len(all_stocks)


def main():
    db = database.SessionLocal()
    try:
        logger.info("🚀 Starting NSE stock fetch...")
        count = fetch_all_nse_stocks(db)
        logger.info(f"✅ Successfully fetched {count} stocks from NSE")
    except Exception as e:
        logger.error(f"Error fetching NSE stocks: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

