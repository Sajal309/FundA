"""Script to run sector rotation ETL aggregation."""
import sys
from datetime import date
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import database
from app.services import sector_rotation_etl
from app.utils import logger


def main():
    """Run daily aggregation for sector rotation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run sector rotation ETL aggregation')
    parser.add_argument(
        '--date',
        type=str,
        help='Target date in YYYY-MM-DD format (default: today)',
        default=None
    )
    args = parser.parse_args()
    
    target_date = None
    if args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)
    
    db = next(database.get_db())
    try:
        count = sector_rotation_etl.run_daily_aggregation(db, target_date)
        logger.info(f"✅ Successfully created {count} aggregation snapshots")
    except Exception as e:
        logger.error(f"❌ Error running aggregation: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

