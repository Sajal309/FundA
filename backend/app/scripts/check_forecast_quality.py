"""Script to check forecast quality and data completeness."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import date
from app.db import database
from app.services import forecast_backtest
from app.utils import logger


def main():
    db = database.SessionLocal()
    try:
        print("📊 Forecast Quality Report")
        print("=" * 60)
        
        # Get quality metrics for all sectors
        print("\n1. Overall Forecast Quality:")
        metrics = forecast_backtest.get_forecast_quality_metrics(db)
        print(f"   Total Forecasts: {metrics['total_forecasts']}")
        print(f"   Avg Quarter Score: {metrics['avg_quarter_score']:.2f}" if metrics['avg_quarter_score'] else "   Avg Quarter Score: N/A")
        print(f"   Avg Confidence: {metrics['avg_confidence']:.1%}" if metrics['avg_confidence'] else "   Avg Confidence: N/A")
        print(f"   Latest Forecast Date: {metrics['latest_forecast_date']}")
        
        # Check data completeness for a sample sector
        print("\n2. Data Completeness (Sample - NIFTY_BANK):")
        from app.db import crud, models
        from sqlalchemy import desc
        
        # Check SectorFeatures first
        features = crud.get_latest_sector_features(db, 'NIFTY_BANK')
        if features:
            print(f"   SectorFeatures (date: {features.date}):")
            print(f"     Breadth: {'✅' if features.breadth_above_50dma is not None else '❌'}")
            print(f"     Valuation: {'✅' if features.valuation_pe_percentile is not None else '❌'}")
            print(f"     Earnings: {'✅' if features.earnings_upgrades_pct_60d is not None else '❌'}")
            print(f"     Sentiment: {'✅' if features.sentiment_score_7d is not None else '❌'}")
            print(f"     Flows: {'✅' if features.fii_net_inr_percentile is not None else '❌'}")
        else:
            print("   ❌ No SectorFeatures found")
        
        # Also check source tables directly
        print(f"\n   Source Tables:")
        breadth = db.query(models.SectorBreadthDaily).filter(
            models.SectorBreadthDaily.sector_id == 'NIFTY_BANK'
        ).order_by(desc(models.SectorBreadthDaily.date)).first()
        print(f"     BreadthDaily: {'✅' if breadth else '❌'}")
        
        valuation = db.query(models.SectorValuationsDaily).filter(
            models.SectorValuationsDaily.sector_id == 'NIFTY_BANK'
        ).order_by(desc(models.SectorValuationsDaily.date)).first()
        print(f"     ValuationsDaily: {'✅' if valuation else '❌'}")
        
        earnings_count = db.query(models.EarningsEvent).filter(
            models.EarningsEvent.sector_id == 'NIFTY_BANK'
        ).count()
        print(f"     EarningsEvents: {'✅' if earnings_count > 0 else '❌'} ({earnings_count} events)")
        
        sentiment = db.query(models.SectorSentimentDaily).filter(
            models.SectorSentimentDaily.sector_id == 'NIFTY_BANK'
        ).order_by(desc(models.SectorSentimentDaily.date)).first()
        print(f"     SentimentDaily: {'✅' if sentiment else '❌'}")
        
        flows = db.query(models.SectorFlowsDaily).filter(
            models.SectorFlowsDaily.sector_id == 'NIFTY_BANK'
        ).order_by(desc(models.SectorFlowsDaily.date)).first()
        print(f"     FlowsDaily: {'✅' if flows else '❌'}")
        
        # Evaluate forecast accuracy (if we have enough historical data)
        print("\n3. Forecast Accuracy (Last 6 months):")
        accuracy = forecast_backtest.evaluate_forecast_accuracy(
            db, from_date=date.today() - timedelta(days=180)
        )
        print(f"   Total Forecasts: {accuracy['total_forecasts']}")
        print(f"   Evaluated: {accuracy['evaluated']}")
        if accuracy['accuracy']:
            print(f"   Accuracy: {accuracy['accuracy']:.1f}%")
            print(f"   Mean Error: {accuracy['mean_error']:.2f}%")
            print(f"   Correct Predictions: {accuracy['correct_predictions']}/{accuracy['evaluated']}")
        else:
            print("   Insufficient data for accuracy evaluation")
        
        print("\n" + "=" * 60)
        print("✅ Quality check complete!")
        
    except Exception as e:
        logger.error(f"Error checking forecast quality: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    from datetime import timedelta
    main()

