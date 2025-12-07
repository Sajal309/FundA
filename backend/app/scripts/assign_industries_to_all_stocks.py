"""Script to assign industry_id to all stocks based on their sector_id."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.db import database, models
from app.utils import logger
from app.api.v1.sectors import SECTOR_NAMES


def create_comprehensive_industries(db: Session) -> int:
    """Create comprehensive list of industries covering all sectors.
    
    Creates industries that match all sectors (1:1 mapping).
    """
    from app.api.v1.sectors import SECTOR_NAMES
    
    # Create industries from all sectors - each sector becomes its own industry
    industries = []
    for sector_id, sector_name in SECTOR_NAMES.items():
        # Use sector_id as industry_id for 1:1 mapping
        industry_id = sector_id
        industry_name = sector_name
        
        industries.append((industry_id, industry_name))
    
    count = 0
    for industry_id, name in industries:
        existing = db.query(models.Industry).filter(
            models.Industry.industry_id == industry_id
        ).first()
        if not existing:
            industry = models.Industry(
                industry_id=industry_id,
                name=name
            )
            db.add(industry)
            count += 1
    
    db.commit()
    logger.info(f"Created {count} new industries")
    return count


def get_comprehensive_sector_to_industry_mapping() -> dict:
    """Get comprehensive mapping from sectors to industries.
    
    Maps each sector to its own industry (1:1 mapping) so all sectors appear in industry rotation.
    Each sector becomes its own industry - using sector_id as industry_id for direct 1:1 mapping.
    """
    from app.api.v1.sectors import SECTOR_NAMES
    
    # Create 1:1 mapping - each sector becomes its own industry
    # Use sector_id directly as industry_id for clean mapping
    mapping = {}
    
    for sector_id in SECTOR_NAMES.keys():
        # Use sector_id as industry_id for 1:1 mapping
        mapping[sector_id] = sector_id
    
    return mapping


def assign_industries_to_stocks(db: Session) -> int:
    """Assign industry_id to all stocks based on their sector_id."""
    sector_to_industry = get_comprehensive_sector_to_industry_mapping()
    
    # Get all stocks
    stocks = db.query(models.Stock).all()
    
    updated_count = 0
    for stock in stocks:
        if stock.sector_id and stock.sector_id in sector_to_industry:
            industry_id = sector_to_industry[stock.sector_id]
            
            # Only update if industry_id is None or different
            if stock.industry_id != industry_id:
                stock.industry_id = industry_id
                updated_count += 1
    
    db.commit()
    logger.info(f"Updated industry_id for {updated_count} stocks")
    return updated_count


def assign_industries_from_constituents(db: Session) -> int:
    """Assign industries to stocks based on sector constituents if stock doesn't have sector_id."""
    sector_to_industry = get_comprehensive_sector_to_industry_mapping()
    
    # Get all constituents
    constituents = db.query(models.SectorConstituent).all()
    
    updated_count = 0
    for const in constituents:
        if const.sector_id and const.sector_id in sector_to_industry:
            industry_id = sector_to_industry[const.sector_id]
            
            # Find stock by ticker
            stock = db.query(models.Stock).filter(
                models.Stock.ticker == const.ticker
            ).first()
            
            if stock and (stock.industry_id is None or stock.industry_id != industry_id):
                stock.industry_id = industry_id
                if not stock.sector_id:
                    stock.sector_id = const.sector_id
                updated_count += 1
    
    db.commit()
    logger.info(f"Updated {updated_count} stocks from constituents")
    return updated_count


def main():
    """Main function to assign industries to all stocks."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Assign industry_id to all stocks')
    parser.add_argument('--create-industries', action='store_true', help='Create new industries')
    args = parser.parse_args()
    
    db = database.SessionLocal()
    
    try:
        logger.info("="*80)
        logger.info("ASSIGNING INDUSTRIES TO ALL STOCKS")
        logger.info("="*80)
        
        # Step 1: Create comprehensive industries
        if args.create_industries:
            logger.info("\n1. Creating comprehensive industries...")
            create_comprehensive_industries(db)
        else:
            logger.info("\n1. Skipping industry creation (use --create-industries to create new ones)")
        
        # Step 2: Assign industries based on sector_id
        logger.info("\n2. Assigning industries based on sector_id...")
        count1 = assign_industries_to_stocks(db)
        
        # Step 3: Assign industries from constituents
        logger.info("\n3. Assigning industries from sector constituents...")
        count2 = assign_industries_from_constituents(db)
        
        # Summary
        total_stocks = db.query(models.Stock).count()
        stocks_with_industry = db.query(models.Stock).filter(
            models.Stock.industry_id.isnot(None)
        ).count()
        
        logger.info("\n" + "="*80)
        logger.info(f"✅ SUMMARY:")
        logger.info(f"   Total stocks: {total_stocks}")
        logger.info(f"   Stocks with industry_id: {stocks_with_industry}")
        logger.info(f"   Updated from sector_id: {count1}")
        logger.info(f"   Updated from constituents: {count2}")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

