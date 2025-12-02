"""CLI script to run backtests."""
import sys
import argparse
import json
from datetime import date, datetime
from pathlib import Path
from app.db.database import SessionLocal
from app.services.backtest import run_backtest
from app.utils import logger


def main():
    """CLI entrypoint for backtesting."""
    parser = argparse.ArgumentParser(description='Run backtest on historical forecasts')
    parser.add_argument('--sector', help='Specific sector ID to backtest')
    parser.add_argument('--from-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', help='Output CSV file path')
    parser.add_argument('--json', help='Output JSON file path')
    
    args = parser.parse_args()
    
    db = SessionLocal()
    
    try:
        from_date = datetime.strptime(args.from_date, '%Y-%m-%d').date() if args.from_date else None
        to_date = datetime.strptime(args.to_date, '%Y-%m-%d').date() if args.to_date else None
        
        result = run_backtest(
            db,
            sector_id=args.sector,
            from_date=from_date,
            to_date=to_date,
            output_path=args.output
        )
        
        # Print summary
        metrics = result.get("metrics", {})
        print(f"\n{'='*60}")
        print("BACKTEST RESULTS")
        print(f"{'='*60}")
        print(f"Total Forecasts: {metrics.get('total_forecasts', 0)}")
        print(f"Directional Accuracy: {metrics.get('directional_accuracy', 0)*100:.1f}%")
        print(f"Mean Absolute Error: {metrics.get('mean_absolute_error', 0):.2f}%")
        print(f"\nLabel-Specific Accuracy:")
        print(f"  UP: {metrics.get('up_accuracy', 0)*100:.1f}%")
        print(f"  NEUTRAL: {metrics.get('neutral_accuracy', 0)*100:.1f}%")
        print(f"  DOWN: {metrics.get('down_accuracy', 0)*100:.1f}%")
        print(f"{'='*60}\n")
        
        # Save JSON if requested
        if args.json:
            with open(args.json, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"JSON report saved to {args.json}")
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

