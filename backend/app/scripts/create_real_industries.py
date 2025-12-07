"""Script to create real industry classifications and map stocks to them."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.db import database, models
from app.utils import logger


# Real industry classifications based on NSE/BSE industry structure
REAL_INDUSTRIES = [
    # Manufacturing & Materials
    ("ABRASIVES", "Abrasives"),
    ("CEMENT", "Cement"),
    ("CHEMICALS", "Chemicals"),
    ("FERTILIZERS", "Fertilizers"),
    ("GLASS", "Glass & Glass Products"),
    ("PAINTS", "Paints"),
    ("PAPER", "Paper & Paper Products"),
    ("PLASTICS", "Plastics"),
    ("STEEL", "Steel"),
    ("TEXTILES", "Textiles"),
    
    # Engineering & Capital Goods
    ("ENGINEERING", "Engineering"),
    ("INDUSTRIAL_MACHINERY", "Industrial Machinery"),
    ("FASTENERS", "Fasteners"),
    ("RAILWAY_WAGONS", "Railways Wagons"),
    
    # Automobiles & Components
    ("AUTOMOBILES", "Automobiles"),
    ("AUTO_COMPONENTS", "Auto Components"),
    ("TYRES", "Tyres"),
    
    # Consumer Goods
    ("FMCG", "Fast Moving Consumer Goods"),
    ("CONSUMER_DURABLES", "Consumer Durables"),
    ("WATCHES_ACCESSORIES", "Watches & Accessories"),
    ("FOOTWEAR", "Footwear"),
    ("JEWELLERY", "Jewellery"),
    
    # Services
    ("BANKING", "Banking"),
    ("FINANCIAL_SERVICES", "Financial Services"),
    ("INSURANCE", "Insurance"),
    ("DEPOSITORY_SERVICES", "Depository Services"),
    ("IT_SOFTWARE", "IT Software & Services"),
    ("TELECOM", "Telecommunications"),
    ("MEDIA", "Media & Entertainment"),
    ("RETAIL", "Retail"),
    ("HOTELS", "Hotels"),
    ("LOGISTICS", "Logistics & Transportation"),
    
    # Healthcare
    ("PHARMACEUTICALS", "Pharmaceuticals"),
    ("HEALTHCARE", "Healthcare"),
    
    # Energy & Utilities
    ("OIL_GAS", "Oil & Gas"),
    ("POWER", "Power"),
    ("RENEWABLE_ENERGY", "Renewable Energy"),
    
    # Infrastructure & Construction
    ("REALTY", "Real Estate"),
    ("CONSTRUCTION", "Construction"),
    ("INFRASTRUCTURE", "Infrastructure"),
    
    # Metals & Mining
    ("METALS", "Metals & Mining"),
    ("ALUMINIUM", "Aluminium"),
    ("COPPER", "Copper"),
    ("GOLD", "Gold"),
    
    # Others
    ("AGRICULTURE", "Agriculture"),
    ("SHIPPING", "Shipping"),
    ("AVIATION", "Aviation"),
    ("DIVERSIFIED", "Diversified"),
]


# Map stock tickers to industries based on their business
STOCK_TO_INDUSTRY_MAPPING = {
    # Banking
    "HDFCBANK": "BANKING",
    "ICICIBANK": "BANKING",
    "SBIN": "BANKING",
    "KOTAKBANK": "BANKING",
    "AXISBANK": "BANKING",
    "INDUSINDBK": "BANKING",
    "FEDERALBNK": "BANKING",
    "BANDHANBNK": "BANKING",
    "PNB": "BANKING",
    "IDFCFIRSTB": "BANKING",
    
    # IT Software
    "TCS": "IT_SOFTWARE",
    "INFY": "IT_SOFTWARE",
    "WIPRO": "IT_SOFTWARE",
    "HCLTECH": "IT_SOFTWARE",
    "TECHM": "IT_SOFTWARE",
    "LTIM": "IT_SOFTWARE",
    "MPHASIS": "IT_SOFTWARE",
    "PERSISTENT": "IT_SOFTWARE",
    "COFORGE": "IT_SOFTWARE",
    "MINDTREE": "IT_SOFTWARE",
    
    # Pharmaceuticals
    "SUNPHARMA": "PHARMACEUTICALS",
    "DRREDDY": "PHARMACEUTICALS",
    "CIPLA": "PHARMACEUTICALS",
    "LUPIN": "PHARMACEUTICALS",
    "GLENMARK": "PHARMACEUTICALS",
    "TORNTPHARM": "PHARMACEUTICALS",
    "DIVISLAB": "PHARMACEUTICALS",
    "AUROPHARMA": "PHARMACEUTICALS",
    "CADILAHC": "PHARMACEUTICALS",
    "ALKEM": "PHARMACEUTICALS",
    
    # FMCG
    "HINDUNILVR": "FMCG",
    "ITC": "FMCG",
    "NESTLEIND": "FMCG",
    "BRITANNIA": "FMCG",
    "DABUR": "FMCG",
    "MARICO": "FMCG",
    "GODREJCP": "FMCG",
    "COLPAL": "FMCG",
    "EMAMILTD": "FMCG",
    "TATACONSUM": "FMCG",
    
    # Automobiles
    "MARUTI": "AUTOMOBILES",
    "M&M": "AUTOMOBILES",
    "TATAMOTORS": "AUTOMOBILES",
    "BAJAJ-AUTO": "AUTOMOBILES",
    "HEROMOTOCO": "AUTOMOBILES",
    "EICHERMOT": "AUTOMOBILES",
    "ASHOKLEY": "AUTOMOBILES",
    "TVSMOTOR": "AUTOMOBILES",
    "BHARATFORG": "AUTO_COMPONENTS",
    "MOTHERSON": "AUTO_COMPONENTS",
    
    # Energy
    "RELIANCE": "OIL_GAS",
    "ONGC": "OIL_GAS",
    "IOC": "OIL_GAS",
    "BPCL": "OIL_GAS",
    "HPCL": "OIL_GAS",
    "GAIL": "OIL_GAS",
    "PETRONET": "OIL_GAS",
    "MGL": "OIL_GAS",
    "IGL": "OIL_GAS",
    "ADANIGREEN": "RENEWABLE_ENERGY",
    
    # Metals
    "TATASTEEL": "STEEL",
    "JSWSTEEL": "STEEL",
    "SAIL": "STEEL",
    "VEDL": "METALS",
    "HINDALCO": "ALUMINIUM",
    "JINDALSAW": "STEEL",
    "NATIONALUM": "ALUMINIUM",
    "HINDZINC": "METALS",
    "NMDC": "METALS",
    "MOIL": "METALS",
    
    # Realty
    "DLF": "REALTY",
    "GODREJPROP": "REALTY",
    "OBEROIRLTY": "REALTY",
    "PRESTIGE": "REALTY",
    "SOBHA": "REALTY",
    "BRIGADE": "REALTY",
    "KOLTEPATIL": "REALTY",
    "MAHLIFE": "REALTY",
    "PURAVANKARA": "REALTY",
    "SHOBHA": "REALTY",
}


# Map sectors to industries (fallback when stock mapping not available)
SECTOR_TO_INDUSTRY_FALLBACK = {
    "NIFTY_BANK": "BANKING",
    "NIFTY_IT": "IT_SOFTWARE",
    "NIFTY_PHARMA": "PHARMACEUTICALS",
    "NIFTY_FMCG": "FMCG",
    "NIFTY_AUTO": "AUTOMOBILES",
    "NIFTY_ENERGY": "OIL_GAS",
    "NIFTY_METAL": "METALS",
    "NIFTY_REALTY": "REALTY",
    "NIFTY_50": "DIVERSIFIED",
    "NIFTY_PSU_BANK": "BANKING",
    "NIFTY_PRIVATE_BANK": "BANKING",
    "NIFTY_FIN_SERVICE": "FINANCIAL_SERVICES",
    "NIFTY_HEALTHCARE": "HEALTHCARE",
    "NIFTY_CONSUMER_DURABLES": "CONSUMER_DURABLES",
    "NIFTY_INFRA": "INFRASTRUCTURE",
    "NIFTY_OIL_GAS": "OIL_GAS",
}


def create_real_industries(db: Session) -> int:
    """Create real industry classifications."""
    count = 0
    for industry_id, name in REAL_INDUSTRIES:
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


def assign_industries_to_stocks(db: Session) -> int:
    """Assign real industries to stocks based on ticker mapping."""
    updated_count = 0
    
    stocks = db.query(models.Stock).all()
    for stock in stocks:
        # First try ticker-based mapping
        industry_id = STOCK_TO_INDUSTRY_MAPPING.get(stock.ticker)
        
        # If not found, use sector-based fallback
        if not industry_id and stock.sector_id:
            industry_id = SECTOR_TO_INDUSTRY_FALLBACK.get(stock.sector_id)
        
        # If still not found, use DIVERSIFIED
        if not industry_id:
            industry_id = "DIVERSIFIED"
        
        # Update if different
        if stock.industry_id != industry_id:
            stock.industry_id = industry_id
            updated_count += 1
    
    db.commit()
    logger.info(f"Updated industry_id for {updated_count} stocks")
    return updated_count


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create real industries and assign to stocks')
    parser.add_argument('--create-industries', action='store_true', help='Create new industries')
    args = parser.parse_args()
    
    db = database.SessionLocal()
    
    try:
        logger.info("="*80)
        logger.info("CREATING REAL INDUSTRIES AND ASSIGNING TO STOCKS")
        logger.info("="*80)
        
        # Step 1: Create industries
        if args.create_industries:
            logger.info("\n1. Creating real industries...")
            create_real_industries(db)
        else:
            logger.info("\n1. Skipping industry creation (use --create-industries to create new ones)")
        
        # Step 2: Assign industries to stocks
        logger.info("\n2. Assigning industries to stocks...")
        count = assign_industries_to_stocks(db)
        
        # Summary
        total_stocks = db.query(models.Stock).count()
        stocks_with_industry = db.query(models.Stock).filter(
            models.Stock.industry_id.isnot(None)
        ).count()
        
        # Show industry distribution
        from sqlalchemy import func
        industry_dist = db.query(
            models.Stock.industry_id,
            func.count(models.Stock.id).label('count')
        ).filter(
            models.Stock.industry_id.isnot(None)
        ).group_by(models.Stock.industry_id).order_by(func.count(models.Stock.id).desc()).all()
        
        logger.info("\n" + "="*80)
        logger.info(f"✅ SUMMARY:")
        logger.info(f"   Total stocks: {total_stocks}")
        logger.info(f"   Stocks with industry_id: {stocks_with_industry}")
        logger.info(f"   Updated: {count}")
        logger.info(f"\n   Industry distribution:")
        for ind_id, count in industry_dist[:15]:
            ind = db.query(models.Industry).filter(models.Industry.industry_id == ind_id).first()
            name = ind.name if ind else ind_id
            logger.info(f"     {name:30s}: {count:>3d} stocks")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

