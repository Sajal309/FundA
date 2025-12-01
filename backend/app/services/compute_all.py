"""Helper script to compute features and forecasts for all sectors."""
import sys
from app.db.database import SessionLocal
from app.services.features import compute_features_for_all_sectors
from app.services.forecasts import generate_forecasts_for_all_sectors
from app.utils import logger


def main():
    """Compute features and forecasts for all sectors."""
    db = SessionLocal()
    try:
        logger.info("Starting feature computation for all sectors...")
        compute_features_for_all_sectors(db)
        
        logger.info("Starting forecast generation for all sectors...")
        generate_forecasts_for_all_sectors(db)
        
        logger.info("Successfully completed feature computation and forecast generation")
    except Exception as e:
        logger.error(f"Error computing features/forecasts: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

