"""Script to populate sector rotation data from existing sector data."""
import sys
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from app.db import database, models
from app.utils import logger
import pandas as pd
import numpy as np


def create_sample_industries(db: Session) -> int:
    """Create sample industries."""
    industries = [
        ("BANKING", "Banking"),
        ("IT_SOFTWARE", "IT Software & Services"),
        ("PHARMACEUTICALS", "Pharmaceuticals"),
        ("FMCG", "Fast Moving Consumer Goods"),
        ("AUTOMOBILES", "Automobiles"),
        ("ENERGY", "Energy"),
        ("METALS", "Metals & Mining"),
        ("REALTY", "Real Estate"),
        ("TELECOM", "Telecommunications"),
        ("CEMENT", "Cement"),
    ]
    
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
    logger.info(f"Created {count} industries")
    return count


def create_stocks_from_constituents(db: Session) -> int:
    """Create stock records from sector constituents."""
    # Get all sector constituents
    constituents = db.query(models.SectorConstituent).all()
    
    if not constituents:
        logger.warning("No sector constituents found. Creating sample stocks...")
        return create_sample_stocks(db)
    
    # Map sectors to industries (simple mapping)
    sector_to_industry = {
        "NIFTY_BANK": "BANKING",
        "NIFTY_IT": "IT_SOFTWARE",
        "NIFTY_PHARMA": "PHARMACEUTICALS",
        "NIFTY_FMCG": "FMCG",
        "NIFTY_AUTO": "AUTOMOBILES",
        "NIFTY_ENERGY": "ENERGY",
        "NIFTY_METAL": "METALS",
        "NIFTY_REALTY": "REALTY",
    }
    
    count = 0
    seen_tickers = set()
    
    for const in constituents:
        if const.ticker in seen_tickers:
            continue
        
        existing = db.query(models.Stock).filter(
            models.Stock.ticker == const.ticker
        ).first()
        
        if not existing:
            industry_id = sector_to_industry.get(const.sector_id)
            stock = models.Stock(
                ticker=const.ticker,
                company_name=const.company_name,
                sector_id=const.sector_id,
                industry_id=industry_id,
                exchange="NSE",
                shares_outstanding=1000000000  # Default 1B shares
            )
            db.add(stock)
            count += 1
            seen_tickers.add(const.ticker)
    
    db.commit()
    logger.info(f"Created {count} stocks from constituents")
    return count


def create_sample_stocks(db: Session) -> int:
    """Create sample stocks for sectors that don't have constituents."""
    # Get all sectors
    sectors = db.query(models.SectorTimeSeries.sector_id).distinct().all()
    sector_ids = [s[0] for s in sectors]
    
    sector_to_industry = {
        "NIFTY_BANK": "BANKING",
        "NIFTY_IT": "IT_SOFTWARE",
        "NIFTY_PHARMA": "PHARMACEUTICALS",
        "NIFTY_FMCG": "FMCG",
        "NIFTY_AUTO": "AUTOMOBILES",
        "NIFTY_ENERGY": "ENERGY",
        "NIFTY_METAL": "METALS",
        "NIFTY_REALTY": "REALTY",
    }
    
    # Sample stock names per sector
    sample_stocks = {
        "NIFTY_BANK": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK"],
        "NIFTY_IT": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM"],
        "NIFTY_PHARMA": ["SUNPHARMA", "DRREDDY", "CIPLA", "LUPIN", "GLENMARK"],
        "NIFTY_FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR"],
        "NIFTY_AUTO": ["MARUTI", "M&M", "TATAMOTORS", "BAJAJ-AUTO", "HEROMOTOCO"],
        "NIFTY_ENERGY": ["RELIANCE", "ONGC", "IOC", "BPCL", "HPCL"],
        "NIFTY_METAL": ["TATASTEEL", "JSWSTEEL", "SAIL", "VEDL", "HINDALCO"],
        "NIFTY_REALTY": ["DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "SOBHA"],
    }
    
    count = 0
    for sector_id in sector_ids:
        stocks = sample_stocks.get(sector_id, [])
        industry_id = sector_to_industry.get(sector_id)
        
        for ticker in stocks:
            existing = db.query(models.Stock).filter(
                models.Stock.ticker == ticker
            ).first()
            
            if not existing:
                stock = models.Stock(
                    ticker=ticker,
                    company_name=ticker.replace("-", " ").title(),
                    sector_id=sector_id,
                    industry_id=industry_id,
                    exchange="NSE",
                    shares_outstanding=1000000000
                )
                db.add(stock)
                count += 1
    
    db.commit()
    logger.info(f"Created {count} sample stocks")
    return count


def create_stock_time_series_from_sector(db: Session, days: int = 252) -> int:
    """Create stock time series data derived from sector data."""
    # Get all stocks
    stocks = db.query(models.Stock).all()
    
    if not stocks:
        logger.warning("No stocks found. Create stocks first.")
        return 0
    
    # Get sector time series for reference
    sectors = {}
    for stock in stocks:
        if stock.sector_id and stock.sector_id not in sectors:
            sector_ts = db.query(models.SectorTimeSeries).filter(
                models.SectorTimeSeries.sector_id == stock.sector_id
            ).order_by(desc(models.SectorTimeSeries.ts)).limit(days).all()
            if sector_ts:
                sectors[stock.sector_id] = sector_ts
    
    count = 0
    target_date = date.today()
    
    # Get all existing records to avoid duplicates
    existing_records = db.query(
        models.StockTimeSeries.ticker,
        models.StockTimeSeries.date
    ).all()
    existing_set = {(r.ticker, r.date) for r in existing_records}
    
    for stock in stocks:
        if stock.sector_id not in sectors:
            continue
        
        sector_data = sectors[stock.sector_id]
        if not sector_data:
            continue
        
        # For each sector date, create stock data with some variation
        for sector_ts in reversed(sector_data):  # Start from oldest
            ts_date = sector_ts.ts.date()
            
            # Check if already exists
            if (stock.ticker, ts_date) in existing_set:
                continue
            
            # Create stock data with variation from sector
            # Add random variation: ±5% from sector price
            variation = random.uniform(0.95, 1.05)
            base_price = float(sector_ts.close)
            
            stock_ts = models.StockTimeSeries(
                ticker=stock.ticker,
                date=ts_date,
                open=Decimal(base_price * variation * random.uniform(0.98, 1.02)),
                high=Decimal(base_price * variation * random.uniform(1.00, 1.03)),
                low=Decimal(base_price * variation * random.uniform(0.97, 1.00)),
                close=Decimal(base_price * variation),
                volume=int(sector_ts.volume * random.uniform(0.5, 2.0)),
                deliverable_volume=int(sector_ts.volume * random.uniform(0.3, 0.7)),
                turnover=Decimal(base_price * variation * sector_ts.volume * random.uniform(0.5, 2.0))
            )
            db.add(stock_ts)
            existing_set.add((stock.ticker, ts_date))  # Track in memory
            count += 1
            
            if count % 500 == 0:
                db.commit()
                logger.info(f"Created {count} stock time series records...")
    
    db.commit()
    logger.info(f"Created {count} stock time series records")
    return count


def calculate_stock_market_caps(db: Session) -> int:
    """Calculate and store market caps for stocks."""
    stocks = db.query(models.Stock).all()
    count = 0
    
    # Get existing records
    existing_records = db.query(
        models.StockMarketCap.ticker,
        models.StockMarketCap.date
    ).all()
    existing_set = {(r.ticker, r.date) for r in existing_records}
    
    for stock in stocks:
        if not stock.shares_outstanding:
            continue
        
        # Get all time series for this stock
        timeseries = db.query(models.StockTimeSeries).filter(
            models.StockTimeSeries.ticker == stock.ticker
        ).all()
        
        for ts in timeseries:
            if (stock.ticker, ts.date) in existing_set:
                continue
            
            # Market cap = price * shares outstanding
            market_cap = float(ts.close) * stock.shares_outstanding
            
            mcap = models.StockMarketCap(
                ticker=stock.ticker,
                date=ts.date,
                market_cap=Decimal(market_cap)
            )
            db.add(mcap)
            existing_set.add((stock.ticker, ts.date))
            count += 1
            
            if count % 500 == 0:
                db.commit()
                logger.info(f"Created {count} market cap records...")
    
    db.commit()
    logger.info(f"Created {count} market cap records")
    return count


def calculate_stock_technical_indicators(db: Session) -> int:
    """Calculate technical indicators for stocks."""
    stocks = db.query(models.Stock).all()
    count = 0
    
    # Get benchmark (Nifty 50) returns for RS55 calculation
    benchmark_ts = db.query(models.SectorTimeSeries).filter(
        models.SectorTimeSeries.sector_id == "NIFTY_50"
    ).order_by(models.SectorTimeSeries.ts).all()
    
    benchmark_prices = {ts.ts.date(): float(ts.close) for ts in benchmark_ts}
    
    for stock in stocks:
        # Get time series ordered by date
        timeseries = db.query(models.StockTimeSeries).filter(
            models.StockTimeSeries.ticker == stock.ticker
        ).order_by(models.StockTimeSeries.date).all()
        
        if len(timeseries) < 100:
            continue
        
        prices = [float(ts.close) for ts in timeseries]
        dates = [ts.date for ts in timeseries]
        
        # Convert to pandas for easier calculation
        df = pd.DataFrame({
            'date': dates,
            'close': prices
        })
        
        # Calculate indicators for each date
        for i in range(20, len(timeseries)):  # Start from day 20 (need 20 for SMA20)
            ts_date = dates[i]
            
            existing = db.query(models.StockTechnicalIndicators).filter(
                and_(
                    models.StockTechnicalIndicators.ticker == stock.ticker,
                    models.StockTechnicalIndicators.date == ts_date
                )
            ).first()
            
            if existing:
                continue
            
            # Get price window
            window_20 = prices[max(0, i-19):i+1]
            window_50 = prices[max(0, i-49):i+1]
            window_100 = prices[max(0, i-99):i+1]
            
            # Calculate SMAs
            sma20 = np.mean(window_20) if len(window_20) >= 20 else None
            sma50 = np.mean(window_50) if len(window_50) >= 50 else None
            sma100 = np.mean(window_100) if len(window_100) >= 100 else None
            
            # Calculate RSI (14 period)
            rsi14 = None
            if i >= 14:
                price_changes = [prices[j] - prices[j-1] for j in range(max(1, i-13), i+1)]
                gains = [max(0, ch) for ch in price_changes]
                losses = [max(0, -ch) for ch in price_changes]
                avg_gain = np.mean(gains) if gains else 0
                avg_loss = np.mean(losses) if losses else 0
                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    rsi14 = 100 - (100 / (1 + rs))
            
            # Calculate returns
            return_1m = None
            return_3m = None
            return_6m = None
            if i >= 21:  # 1 month ≈ 21 trading days
                return_1m = ((prices[i] - prices[i-21]) / prices[i-21]) * 100
            if i >= 63:  # 3 months ≈ 63 trading days
                return_3m = ((prices[i] - prices[i-63]) / prices[i-63]) * 100
            if i >= 126:  # 6 months ≈ 126 trading days
                return_6m = ((prices[i] - prices[i-126]) / prices[i-126]) * 100
            
            # Calculate RS55 (55-day relative strength vs benchmark)
            rs55 = None
            if i >= 55 and ts_date in benchmark_prices:
                # Get benchmark price 55 days ago
                benchmark_dates = sorted(benchmark_prices.keys())
                try:
                    idx = benchmark_dates.index(ts_date)
                    if idx >= 55:
                        bench_price_55d_ago = benchmark_prices[benchmark_dates[idx-55]]
                        bench_return_55d = ((benchmark_prices[ts_date] - bench_price_55d_ago) / bench_price_55d_ago) * 100
                        stock_return_55d = ((prices[i] - prices[i-55]) / prices[i-55]) * 100
                        rs55 = stock_return_55d - bench_return_55d
                except (ValueError, IndexError):
                    pass
            
            # Calculate VWAP (simplified - using 20-day average)
            vwap = sma20  # Simplified VWAP
            
            indicator = models.StockTechnicalIndicators(
                ticker=stock.ticker,
                date=ts_date,
                sma20=Decimal(sma20) if sma20 else None,
                sma50=Decimal(sma50) if sma50 else None,
                sma100=Decimal(sma100) if sma100 else None,
                rsi14=Decimal(rsi14) if rsi14 else None,
                rs55=rs55,
                return_1m=return_1m,
                return_3m=return_3m,
                return_6m=return_6m,
                vwap=Decimal(vwap) if vwap else None
            )
            db.add(indicator)
            count += 1
            
            if count % 1000 == 0:
                db.commit()
                logger.info(f"Created {count} technical indicator records...")
    
    db.commit()
    logger.info(f"Created {count} technical indicator records")
    return count


def calculate_stock_rolling_stats(db: Session) -> int:
    """Calculate 20-day rolling statistics for stocks."""
    stocks = db.query(models.Stock).all()
    count = 0
    
    for stock in stocks:
        timeseries = db.query(models.StockTimeSeries).filter(
            models.StockTimeSeries.ticker == stock.ticker
        ).order_by(models.StockTimeSeries.date).all()
        
        if len(timeseries) < 20:
            continue
        
        # Calculate rolling stats for each date (starting from day 20)
        for i in range(19, len(timeseries)):
            ts_date = timeseries[i].date
            
            existing = db.query(models.StockRollingStats).filter(
                and_(
                    models.StockRollingStats.ticker == stock.ticker,
                    models.StockRollingStats.date == ts_date
                )
            ).first()
            
            if existing:
                continue
            
            # Get last 20 days
            window = timeseries[i-19:i+1]
            
            # Calculate averages
            traded_values = [float(ts.close) * float(ts.volume) for ts in window]
            delivery_values = [
                float(ts.close) * float(ts.deliverable_volume or 0) 
                for ts in window if ts.deliverable_volume
            ]
            
            avg_traded_value = Decimal(np.mean(traded_values))
            avg_delivery_value = Decimal(np.mean(delivery_values)) if delivery_values else None
            
            stats = models.StockRollingStats(
                ticker=stock.ticker,
                date=ts_date,
                avg_traded_value_20d=avg_traded_value,
                avg_delivery_value_20d=avg_delivery_value
            )
            db.add(stats)
            count += 1
            
            if count % 1000 == 0:
                db.commit()
                logger.info(f"Created {count} rolling stats records...")
    
    db.commit()
    logger.info(f"Created {count} rolling stats records")
    return count


def main():
    """Main function to populate all sector rotation data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate sector rotation data')
    parser.add_argument('--skip-stocks', action='store_true', help='Skip creating stocks')
    parser.add_argument('--skip-timeseries', action='store_true', help='Skip creating time series')
    parser.add_argument('--skip-indicators', action='store_true', help='Skip calculating indicators')
    parser.add_argument('--skip-etl', action='store_true', help='Skip running ETL aggregation')
    args = parser.parse_args()
    
    db = database.SessionLocal()
    
    try:
        logger.info("="*80)
        logger.info("POPULATING SECTOR ROTATION DATA")
        logger.info("="*80)
        
        # Step 1: Create industries
        logger.info("\n1. Creating industries...")
        create_sample_industries(db)
        
        # Step 2: Create stocks
        if not args.skip_stocks:
            logger.info("\n2. Creating stocks...")
            create_stocks_from_constituents(db)
        
        # Step 3: Create stock time series
        if not args.skip_timeseries:
            logger.info("\n3. Creating stock time series...")
            create_stock_time_series_from_sector(db)
        
        # Step 4: Calculate market caps
        if not args.skip_timeseries:
            logger.info("\n4. Calculating market caps...")
            calculate_stock_market_caps(db)
        
        # Step 5: Calculate technical indicators
        if not args.skip_indicators:
            logger.info("\n5. Calculating technical indicators...")
            calculate_stock_technical_indicators(db)
        
        # Step 6: Calculate rolling stats
        if not args.skip_indicators:
            logger.info("\n6. Calculating rolling statistics...")
            calculate_stock_rolling_stats(db)
        
        # Step 7: Run ETL aggregation
        if not args.skip_etl:
            logger.info("\n7. Running ETL aggregation...")
            from app.services import sector_rotation_etl
            
            # Get latest date with stock data
            latest_date = db.query(func.max(models.StockTimeSeries.date)).scalar()
            if latest_date:
                count = sector_rotation_etl.run_daily_aggregation(db, latest_date)
                logger.info(f"✅ Created {count} aggregation snapshots for {latest_date}")
            else:
                logger.warning("No stock time series data found. Skipping ETL.")
        
        logger.info("\n" + "="*80)
        logger.info("✅ DATA POPULATION COMPLETE!")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ Error populating data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

