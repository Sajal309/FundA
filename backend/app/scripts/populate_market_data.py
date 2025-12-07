"""Script to populate market sentiment and flows data."""
import sys
from pathlib import Path
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import database
from app.services import compute_market_sentiment, compute_flows_aggregate
from app.utils import logger


def main():
    """Main function to populate market data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate market sentiment and flows data')
    parser.add_argument('--days', type=int, default=30, help='Number of days to populate')
    parser.add_argument('--sentiment-only', action='store_true', help='Only populate sentiment')
    parser.add_argument('--flows-only', action='store_true', help='Only populate flows')
    args = parser.parse_args()
    
    db = database.SessionLocal()
    
    try:
        logger.info("="*80)
        logger.info("POPULATING MARKET DATA")
        logger.info("="*80)
        
        if not args.flows_only:
            logger.info(f"\n1. Populating market sentiment data ({args.days} days)...")
            count = compute_market_sentiment.populate_market_sentiment_history(db, args.days)
            logger.info(f"✅ Populated {count} market sentiment records")
        
        if not args.sentiment_only:
            logger.info(f"\n2. Populating flows data ({args.days} days)...")
            count = compute_flows_aggregate.populate_flows_from_fii_dii(db, args.days)
            logger.info(f"✅ Populated flows for {count} sector-date combinations")
        
        logger.info("\n" + "="*80)
        logger.info("✅ MARKET DATA POPULATION COMPLETE!")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

