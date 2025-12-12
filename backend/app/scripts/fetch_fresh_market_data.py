"""Script to fetch fresh market sentiment and FII/DII data."""
import sys
from pathlib import Path
from datetime import date, timedelta
import requests
import pandas as pd
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import database, models, crud, schemas
from app.services import compute_market_sentiment
from app.utils import logger


def fetch_fii_dii_from_nse(target_date: date) -> dict:
    """
    Fetch FII/DII data from NSE using nsepython.
    
    NSE provides FII/DII data at: https://www.nseindia.com/reports/fii-dii
    """
    try:
        from app.services import nsepython_service
        
        if not nsepython_service.is_available():
            logger.warning("nsepython not available for FII/DII data")
            return None
        
        # Fetch FII/DII data using nsepython
        data = nsepython_service.fetch_fii_dii_data(target_date)
        
        if data:
            # Parse response structure - NSE returns data in various formats
            if isinstance(data, list) and len(data) > 0:
                latest = data[0]
                return {
                    'fii_buy': int(latest.get('fii_buy_value', latest.get('fiiBuyValue', 0)) or 0),
                    'fii_sell': int(latest.get('fii_sell_value', latest.get('fiiSellValue', 0)) or 0),
                    'dii_buy': int(latest.get('dii_buy_value', latest.get('diiBuyValue', 0)) or 0),
                    'dii_sell': int(latest.get('dii_sell_value', latest.get('diiSellValue', 0)) or 0),
                }
            elif isinstance(data, dict):
                # Try different key formats
                return {
                    'fii_buy': int(data.get('fii_buy_value', data.get('fiiBuyValue', data.get('fii_buy', 0))) or 0),
                    'fii_sell': int(data.get('fii_sell_value', data.get('fiiSellValue', data.get('fii_sell', 0))) or 0),
                    'dii_buy': int(data.get('dii_buy_value', data.get('diiBuyValue', data.get('dii_buy', 0))) or 0),
                    'dii_sell': int(data.get('dii_sell_value', data.get('diiSellValue', data.get('dii_sell', 0))) or 0),
                }
    except Exception as e:
        logger.warning(f"Could not fetch FII/DII from NSE for {target_date}: {e}")
    
    return None


# Mock FII/DII data generation removed - only real data sources are used
# If NSE data is not available, the function will return None


def store_fii_dii_data(db, target_date: date, flow_data: dict) -> bool:
    """Store FII/DII data in database."""
    try:
        # Check if already exists
        existing = db.query(models.FIIDIIDaily).filter(
            models.FIIDIIDaily.date == target_date,
            models.FIIDIIDaily.ticker.is_(None)  # Aggregate data
        ).first()
        
        if existing:
            # Update existing
            existing.fii_buy = flow_data.get('fii_buy')
            existing.fii_sell = flow_data.get('fii_sell')
            existing.dii_buy = flow_data.get('dii_buy')
            existing.dii_sell = flow_data.get('dii_sell')
            existing.source = 'NSE'
            db.commit()
            logger.info(f"Updated FII/DII data for {target_date}")
        else:
            # Create new
            flow_record = models.FIIDIIDaily(
                date=target_date,
                source='NSE',
                ticker=None,  # Aggregate
                fii_buy=flow_data.get('fii_buy'),
                fii_sell=flow_data.get('fii_sell'),
                dii_buy=flow_data.get('dii_buy'),
                dii_sell=flow_data.get('dii_sell'),
            )
            db.add(flow_record)
            db.commit()
            logger.info(f"Created FII/DII data for {target_date}")
        
        return True
    except Exception as e:
        logger.error(f"Error storing FII/DII data for {target_date}: {e}")
        db.rollback()
        return False


def validate_data_accuracy(db, target_date: date) -> dict:
    """Validate the accuracy of fetched data."""
    results = {
        'sentiment': {'valid': False, 'issues': []},
        'fii_dii': {'valid': False, 'issues': []},
    }
    
    # Validate sentiment data
    sentiment = db.query(models.MarketSentimentDaily).filter(
        models.MarketSentimentDaily.date == target_date
    ).first()
    
    if sentiment:
        # Check VIX range (typically 10-30 for India VIX)
        if sentiment.india_vix:
            vix_val = float(sentiment.india_vix)
            if vix_val < 5 or vix_val > 50:
                results['sentiment']['issues'].append(f"VIX value {vix_val} seems out of normal range (5-50)")
            else:
                results['sentiment']['valid'] = True
        
        # Check PCR range (typically 0.5-2.0)
        if sentiment.index_pcr:
            pcr_val = float(sentiment.index_pcr)
            if pcr_val < 0.1 or pcr_val > 5.0:
                results['sentiment']['issues'].append(f"PCR value {pcr_val} seems out of normal range (0.5-2.0)")
        
        # Check breadth range (0-1)
        if sentiment.breadth_nifty500_above_50dma:
            breadth_val = float(sentiment.breadth_nifty500_above_50dma)
            if breadth_val < 0 or breadth_val > 1:
                results['sentiment']['issues'].append(f"Breadth value {breadth_val} should be between 0 and 1")
    
    # Validate FII/DII data
    fii_dii = db.query(models.FIIDIIDaily).filter(
        models.FIIDIIDaily.date == target_date,
        models.FIIDIIDaily.ticker.is_(None)
    ).first()
    
    if fii_dii:
        # Check for reasonable values (in crores)
        if fii_dii.fii_buy and fii_dii.fii_sell:
            fii_net = (fii_dii.fii_buy - fii_dii.fii_sell) / 10000000  # Convert to crores
            if abs(fii_net) > 50000:  # More than 50,000 cr seems unusual
                results['fii_dii']['issues'].append(f"FII net flow {fii_net:.2f} cr seems unusually high")
            else:
                results['fii_dii']['valid'] = True
        
        if fii_dii.dii_buy and fii_dii.dii_sell:
            dii_net = (fii_dii.dii_buy - fii_dii.dii_sell) / 10000000  # Convert to crores
            if abs(dii_net) > 50000:
                results['fii_dii']['issues'].append(f"DII net flow {dii_net:.2f} cr seems unusually high")
    
    return results


def main():
    """Main function to fetch fresh market data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch fresh market sentiment and FII/DII data')
    parser.add_argument('--days', type=int, default=7, help='Number of days to fetch (default: 7)')
    parser.add_argument('--sentiment-only', action='store_true', help='Only fetch sentiment data')
    parser.add_argument('--fii-dii-only', action='store_true', help='Only fetch FII/DII data')
    parser.add_argument('--validate', action='store_true', help='Validate data accuracy after fetching')
    args = parser.parse_args()
    
    db = database.SessionLocal()
    
    try:
        logger.info("="*80)
        logger.info("FETCHING FRESH MARKET DATA")
        logger.info("="*80)
        
        today = date.today()
        sentiment_count = 0
        fii_dii_count = 0
        
        for i in range(args.days):
            target_date = today - timedelta(days=i)
            
            # Skip weekends
            if target_date.weekday() >= 5:
                continue
            
            logger.info(f"\n📅 Processing {target_date}...")
            
            # Fetch market sentiment
            if not args.fii_dii_only:
                try:
                    sentiment = compute_market_sentiment.compute_and_store_market_sentiment(db, target_date)
                    if sentiment:
                        sentiment_count += 1
                        logger.info(f"  ✅ Market sentiment: VIX={sentiment.india_vix}, Regime={sentiment.regime_label}")
                except Exception as e:
                    logger.error(f"  ❌ Error fetching sentiment for {target_date}: {e}")
            
            # Fetch FII/DII data
            if not args.sentiment_only:
                try:
                    # Use NSE (nsepython) as primary source (real data only)
                    flow_data = fetch_fii_dii_from_nse(target_date)
                    
                    # If NSE fails, skip this date (no mock data fallback)
                    if not flow_data:
                        logger.warning(f"❌ NSE FII/DII data not available for {target_date}, skipping (real data only)")
                        continue
                    
                    if flow_data:
                        if store_fii_dii_data(db, target_date, flow_data):
                            fii_dii_count += 1
                            fii_net = (flow_data.get('fii_buy', 0) - flow_data.get('fii_sell', 0)) / 10000000
                            dii_net = (flow_data.get('dii_buy', 0) - flow_data.get('dii_sell', 0)) / 10000000
                            logger.info(f"  ✅ FII/DII: FII net={fii_net:.2f} cr, DII net={dii_net:.2f} cr")
                except Exception as e:
                    logger.error(f"  ❌ Error fetching FII/DII for {target_date}: {e}")
            
            # Validate data if requested
            if args.validate:
                validation = validate_data_accuracy(db, target_date)
                if validation['sentiment']['issues']:
                    logger.warning(f"  ⚠️  Sentiment validation issues: {validation['sentiment']['issues']}")
                if validation['fii_dii']['issues']:
                    logger.warning(f"  ⚠️  FII/DII validation issues: {validation['fii_dii']['issues']}")
        
        logger.info("\n" + "="*80)
        logger.info(f"✅ FETCH COMPLETE!")
        logger.info(f"   Market Sentiment: {sentiment_count} records")
        logger.info(f"   FII/DII Data: {fii_dii_count} records")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

