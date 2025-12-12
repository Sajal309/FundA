"""Script to recompute SectorFeatures for all sectors to include newly populated data."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import date
from app.db import database
from app.services import features
from app.utils import logger


def main():
    db = database.SessionLocal()
    try:
        logger.info("🔄 Recomputing SectorFeatures for all sectors...")
        
        from app.db import crud
        sectors = crud.get_all_sectors(db)
        
        count = 0
        errors = 0
        
        for sector_id in sectors:
            try:
                features_response = features.compute_features_for_sector(db, sector_id, date.today())
                if features_response:
                    count += 1
                    if count % 5 == 0:
                        logger.info(f"Processed {count} sectors...")
            except Exception as e:
                logger.warning(f"Failed to compute features for {sector_id}: {e}")
                errors += 1
                continue
        
        logger.info(f"✅ Recomputed features for {count} sectors ({errors} errors)")
        
    except Exception as e:
        logger.error(f"Error recomputing features: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

