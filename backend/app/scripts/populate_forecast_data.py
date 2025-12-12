"""Script to populate missing forecast data for better accuracy."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import date, timedelta
from app.db import database
from app.services import populate_forecast_data, sector_rotation_etl
from app.utils import logger
import argparse


def main():
    parser = argparse.ArgumentParser(description="Populate forecast data")
    parser.add_argument("--days", type=int, default=30, help="Number of days to populate")
    parser.add_argument("--breadth-only", action="store_true", help="Only populate breadth data")
    parser.add_argument("--valuations-only", action="store_true", help="Only populate valuations")
    parser.add_argument("--sentiment-only", action="store_true", help="Only refresh sentiment data")
    parser.add_argument("--earnings-only", action="store_true", help="Only populate earnings events")
    parser.add_argument("--options-only", action="store_true", help="Only refresh options data")
    parser.add_argument("--date", type=str, help="Specific date to populate (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    db = database.SessionLocal()
    try:
        if args.date:
            target_date = date.fromisoformat(args.date)
        else:
            target_date = date.today()
        
        if args.breadth_only:
            logger.info(f"Populating breadth data for last {args.days} days...")
            count = populate_forecast_data.populate_sector_breadth_for_all_dates(db, args.days)
            logger.info(f"✅ Populated {count} breadth records")
        elif args.valuations_only:
            logger.info(f"Populating valuations for {target_date}...")
            count = populate_forecast_data.populate_sector_valuations_for_all_sectors(db, target_date)
            logger.info(f"✅ Populated {count} valuation records")
        elif args.sentiment_only:
            logger.info(f"Refreshing sentiment data for last {args.days} days...")
            count = populate_forecast_data.refresh_sector_sentiment_data(db, target_date, args.days)
            logger.info(f"✅ Refreshed {count} sentiment records")
        elif args.earnings_only:
            logger.info(f"Populating earnings events from fundamentals...")
            count = populate_forecast_data.populate_earnings_events_for_all_sectors(db, target_date)
            logger.info(f"✅ Created {count} earnings events")
        elif args.options_only:
            logger.info(f"Refreshing options data for {target_date}...")
            count = populate_forecast_data.refresh_options_data(db, target_date)
            logger.info(f"✅ Refreshed {count} options records")
        else:
            # Populate all missing data
            logger.info("Populating all forecast data...")
            
            # 1. Populate breadth from snapshots
            logger.info("1. Populating breadth data...")
            breadth_count = populate_forecast_data.populate_sector_breadth_for_all_dates(db, args.days)
            logger.info(f"   ✅ Populated {breadth_count} breadth records")
            
            # 2. Populate valuations
            logger.info("2. Populating valuations...")
            val_count = populate_forecast_data.populate_sector_valuations_for_all_sectors(db, target_date)
            logger.info(f"   ✅ Populated {val_count} valuation records")
            
            # 3. Refresh sentiment data
            logger.info("3. Refreshing sentiment data...")
            sentiment_count = populate_forecast_data.refresh_sector_sentiment_data(db, target_date, args.days)
            logger.info(f"   ✅ Refreshed {sentiment_count} sentiment records")
            
            # 4. Populate earnings events (fallback from fundamentals)
            logger.info("4. Populating earnings events from fundamentals...")
            earnings_count = populate_forecast_data.populate_earnings_events_for_all_sectors(db, target_date)
            logger.info(f"   ✅ Created {earnings_count} earnings events")
            
            # 5. Refresh options data
            logger.info("5. Refreshing options data...")
            options_count = populate_forecast_data.refresh_options_data(db, target_date)
            logger.info(f"   ✅ Refreshed {options_count} options records")
            
            # 6. Ensure sector rotation ETL has run (for breadth snapshots)
            logger.info("6. Ensuring sector rotation data is up to date...")
            snapshot_count = sector_rotation_etl.run_daily_aggregation(db, target_date)
            logger.info(f"   ✅ Created {snapshot_count} snapshots")
            
            # 7. Recompute SectorFeatures to include all new data
            logger.info("7. Recomputing SectorFeatures to aggregate new data...")
            from app.services import features
            from app.db import crud
            sectors = crud.get_all_sectors(db)
            features_count = 0
            for sector_id in sectors:
                try:
                    features_response = features.compute_features_for_sector(db, sector_id, target_date)
                    if features_response:
                        features_count += 1
                except Exception as e:
                    logger.debug(f"Failed to recompute features for {sector_id}: {e}")
                    continue
            logger.info(f"   ✅ Recomputed {features_count} SectorFeatures records")
            
            logger.info(f"\n✅ Forecast data population complete!")
            logger.info(f"   - Breadth: {breadth_count} records")
            logger.info(f"   - Valuations: {val_count} records")
            logger.info(f"   - Sentiment: {sentiment_count} records")
            logger.info(f"   - Earnings Events: {earnings_count} records")
            logger.info(f"   - Options: {options_count} records")
            logger.info(f"   - Snapshots: {snapshot_count} records")
            logger.info(f"   - Features Recomputed: {features_count} records")
    
    except Exception as e:
        logger.error(f"Error populating forecast data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

