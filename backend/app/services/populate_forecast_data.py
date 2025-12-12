"""Service to populate missing forecast data from real sources."""
from typing import Optional, List
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from decimal import Decimal
from app.db import models, crud
from app.services import ingest_news, fetch_kite_options
from app.utils import logger


def populate_sector_breadth_daily_from_snapshots(
    db: Session,
    target_date: Optional[date] = None
) -> int:
    """
    Populate SectorBreadthDaily from SectorBreadthSnapshot data.
    
    SectorBreadthSnapshot has the breadth data we need, we just need to convert it
    to the SectorBreadthDaily format.
    """
    if target_date is None:
        target_date = date.today()
    
    # Get all sector breadth snapshots for target_date
    snapshots = db.query(models.SectorBreadthSnapshot).filter(
        models.SectorBreadthSnapshot.date == target_date
    ).all()
    
    if not snapshots:
        logger.warning(f"No breadth snapshots found for {target_date}")
        return 0
    
    count = 0
    for snapshot in snapshots:
        # Check if already exists
        existing = db.query(models.SectorBreadthDaily).filter(
            and_(
                models.SectorBreadthDaily.sector_id == snapshot.sector_id,
                models.SectorBreadthDaily.date == target_date
            )
        ).first()
        
        if existing:
            # Update existing
            existing.total_constituents = snapshot.total_stocks
            # Calculate above_50dma from pct_count_above_sma50
            if snapshot.pct_count_above_sma50 is not None:
                existing.above_50dma = int(snapshot.total_stocks * snapshot.pct_count_above_sma50)
            # Calculate above_200dma from pct_count_above_sma100 (closest we have)
            if snapshot.pct_count_above_sma100 is not None:
                existing.above_200dma = int(snapshot.total_stocks * snapshot.pct_count_above_sma100)
            # For 3M highs/lows, we'd need additional data - set to None for now
            existing.making_3m_highs = None
            existing.making_3m_lows = None
            db.commit()
            count += 1
        else:
            # Create new
            above_50dma = int(snapshot.total_stocks * snapshot.pct_count_above_sma50) if snapshot.pct_count_above_sma50 else None
            above_200dma = int(snapshot.total_stocks * snapshot.pct_count_above_sma100) if snapshot.pct_count_above_sma100 else None
            
            breadth_daily = models.SectorBreadthDaily(
                sector_id=snapshot.sector_id,
                date=target_date,
                total_constituents=snapshot.total_stocks,
                above_50dma=above_50dma,
                above_200dma=above_200dma,
                making_3m_highs=None,  # Would need additional calculation
                making_3m_lows=None
            )
            db.add(breadth_daily)
            count += 1
    
    db.commit()
    logger.info(f"Populated {count} SectorBreadthDaily records from snapshots for {target_date}")
    return count


def calculate_sector_valuations_from_stocks(
    db: Session,
    sector_id: str,
    target_date: date
) -> Optional[models.SectorValuationsDaily]:
    """
    Calculate sector P/E ratio from constituent stocks' fundamentals.
    
    Uses market-cap weighted average P/E of stocks in the sector.
    """
    # Get all stocks in sector
    stocks = db.query(models.Stock).filter(
        models.Stock.sector_id == sector_id
    ).all()
    
    if not stocks:
        return None
    
    tickers = [s.ticker for s in stocks]
    
    # Get latest fundamentals for these stocks
    # Get the most recent fundamentals date
    latest_fund_date = db.query(func.max(models.StockFundamentals.date)).filter(
        models.StockFundamentals.ticker.in_(tickers)
    ).scalar()
    
    if not latest_fund_date:
        return None
    
    # Get fundamentals for all stocks on latest date
    fundamentals = db.query(models.StockFundamentals).filter(
        and_(
            models.StockFundamentals.ticker.in_(tickers),
            models.StockFundamentals.date == latest_fund_date,
            models.StockFundamentals.pe.isnot(None),
            models.StockFundamentals.pe > 0
        )
    ).all()
    
    if not fundamentals:
        return None
    
    # Get market caps for weighting
    market_caps = db.query(models.StockMarketCap).filter(
        and_(
            models.StockMarketCap.ticker.in_(tickers),
            models.StockMarketCap.date == target_date
        )
    ).all()
    
    mcap_map = {mc.ticker: float(mc.market_cap) for mc in market_caps}
    
    # Calculate market-cap weighted average P/E
    total_weighted_pe = 0.0
    total_mcap = 0.0
    
    for fund in fundamentals:
        if fund.pe and fund.pe > 0:
            ticker = fund.ticker
            mcap = mcap_map.get(ticker, 0)
            if mcap > 0:
                total_weighted_pe += float(fund.pe) * mcap
                total_mcap += mcap
    
    if total_mcap == 0:
        return None
    
    sector_pe = total_weighted_pe / total_mcap
    
    # Create or update valuation record
    existing = db.query(models.SectorValuationsDaily).filter(
        and_(
            models.SectorValuationsDaily.sector_id == sector_id,
            models.SectorValuationsDaily.date == target_date
        )
    ).first()
    
    if existing:
        existing.pe = Decimal(str(sector_pe))
        db.commit()
        return existing
    else:
        valuation = models.SectorValuationsDaily(
            sector_id=sector_id,
            date=target_date,
            pe=Decimal(str(sector_pe)),
            pb=None,  # Would need book value data
            div_yield=None  # Would need dividend data
        )
        db.add(valuation)
        db.commit()
        return valuation


def populate_sector_valuations_for_all_sectors(
    db: Session,
    target_date: Optional[date] = None
) -> int:
    """Populate valuations for all sectors."""
    if target_date is None:
        target_date = date.today()
    
    # Get all sectors
    sectors = db.query(models.Stock.sector_id).distinct().all()
    sector_ids = [s[0] for s in sectors if s[0]]
    
    count = 0
    for sector_id in sector_ids:
        try:
            valuation = calculate_sector_valuations_from_stocks(db, sector_id, target_date)
            if valuation:
                count += 1
        except Exception as e:
            logger.warning(f"Failed to calculate valuation for {sector_id}: {e}")
            continue
    
    logger.info(f"Populated {count} sector valuations for {target_date}")
    return count


def populate_sector_breadth_for_all_dates(
    db: Session,
    days: int = 30
) -> int:
    """Populate breadth data for recent dates."""
    today = date.today()
    total_count = 0
    
    for i in range(days):
        target_date = today - timedelta(days=i)
        count = populate_sector_breadth_daily_from_snapshots(db, target_date)
        total_count += count
    
    logger.info(f"Populated breadth data for {total_count} sector-date combinations")
    return total_count


def improve_breadth_calculation_from_stocks(
    db: Session,
    sector_id: str,
    target_date: date
) -> Optional[models.SectorBreadthDaily]:
    """
    Calculate breadth metrics directly from stock data if snapshots don't exist.
    Uses stock technical indicators to compute breadth.
    """
    # Get all stocks in sector
    stocks = db.query(models.Stock).filter(
        models.Stock.sector_id == sector_id
    ).all()
    
    if not stocks:
        return None
    
    tickers = [s.ticker for s in stocks]
    
    # Get technical indicators for these stocks on target_date
    indicators = db.query(models.StockTechnicalIndicators).filter(
        and_(
            models.StockTechnicalIndicators.ticker.in_(tickers),
            models.StockTechnicalIndicators.date == target_date
        )
    ).all()
    
    if not indicators:
        return None
    
    # Count stocks above 50DMA
    above_50dma = sum(1 for ind in indicators if ind.sma50 and ind.close and ind.close > ind.sma50)
    above_200dma = sum(1 for ind in indicators if ind.sma100 and ind.close and ind.close > ind.sma100)  # Using SMA100 as proxy
    
    # For 3M highs, we'd need to check if price is at 3M high
    # This is simplified - would need historical price data
    making_3m_highs = None
    making_3m_lows = None
    
    # Create or update breadth daily
    existing = db.query(models.SectorBreadthDaily).filter(
        and_(
            models.SectorBreadthDaily.sector_id == sector_id,
            models.SectorBreadthDaily.date == target_date
        )
    ).first()
    
    if existing:
        existing.total_constituents = len(stocks)
        existing.above_50dma = above_50dma
        existing.above_200dma = above_200dma
        existing.making_3m_highs = making_3m_highs
        existing.making_3m_lows = making_3m_lows
        db.commit()
        return existing
    else:
        breadth = models.SectorBreadthDaily(
            sector_id=sector_id,
            date=target_date,
            total_constituents=len(stocks),
            above_50dma=above_50dma,
            above_200dma=above_200dma,
            making_3m_highs=making_3m_highs,
            making_3m_lows=making_3m_lows
        )
        db.add(breadth)
        db.commit()
        return breadth


def refresh_sector_sentiment_data(
    db: Session,
    target_date: Optional[date] = None,
    days: int = 30
) -> int:
    """
    Refresh sector sentiment data by aggregating from news headlines.
    
    This ensures sentiment data is up-to-date for forecast calculations.
    """
    if target_date is None:
        target_date = date.today()
    
    total_count = 0
    
    # Aggregate sentiment for each date in the range
    for i in range(days):
        current_date = target_date - timedelta(days=i)
        
        # Skip weekends
        if current_date.weekday() >= 5:
            continue
        
        try:
            count = ingest_news.aggregate_sentiment_by_sector(db, current_date)
            total_count += count
        except Exception as e:
            logger.warning(f"Failed to aggregate sentiment for {current_date}: {e}")
            continue
    
    logger.info(f"Refreshed sentiment data for {total_count} sector-date combinations")
    return total_count


def create_earnings_events_from_fundamentals_changes(
    db: Session,
    sector_id: str,
    target_date: date,
    lookback_days: int = 90
) -> int:
    """
    Create earnings events based on fundamentals changes (as a fallback).
    
    When actual earnings data is not available, we can infer earnings revisions
    from changes in stock fundamentals (P/E ratios, profit growth, etc.).
    """
    from_date = target_date - timedelta(days=lookback_days)
    
    # Get all stocks in sector
    stocks = db.query(models.Stock).filter(
        models.Stock.sector_id == sector_id
    ).all()
    
    if not stocks:
        return 0
    
    tickers = [s.ticker for s in stocks]
    
    # Get fundamentals for two time periods
    # Latest fundamentals
    latest_fund_date = db.query(func.max(models.StockFundamentals.date)).filter(
        models.StockFundamentals.ticker.in_(tickers)
    ).scalar()
    
    if not latest_fund_date:
        return 0
    
    # Get fundamentals from lookback period
    old_fund_date = db.query(func.max(models.StockFundamentals.date)).filter(
        and_(
            models.StockFundamentals.ticker.in_(tickers),
            models.StockFundamentals.date >= from_date,
            models.StockFundamentals.date < latest_fund_date
        )
    ).scalar()
    
    if not old_fund_date:
        return 0
    
    # Get latest and old fundamentals
    latest_fundamentals = {
        f.ticker: f for f in db.query(models.StockFundamentals).filter(
            and_(
                models.StockFundamentals.ticker.in_(tickers),
                models.StockFundamentals.date == latest_fund_date
            )
        ).all()
    }
    
    old_fundamentals = {
        f.ticker: f for f in db.query(models.StockFundamentals).filter(
            and_(
                models.StockFundamentals.ticker.in_(tickers),
                models.StockFundamentals.date == old_fund_date
            )
        ).all()
    }
    
    count = 0
    for ticker in tickers:
        latest = latest_fundamentals.get(ticker)
        old = old_fundamentals.get(ticker)
        
        if not latest or not old:
            continue
        
        # Check for significant changes that might indicate earnings revision
        revision_direction = None
        
        # Check profit growth changes
        if latest.profit_growth_5y and old.profit_growth_5y:
            growth_change = float(latest.profit_growth_5y) - float(old.profit_growth_5y)
            if growth_change > 5.0:  # Significant positive change
                revision_direction = 'upgrade'
            elif growth_change < -5.0:  # Significant negative change
                revision_direction = 'downgrade'
        
        # Check P/E ratio changes (inverse relationship)
        if latest.pe and old.pe:
            pe_change_pct = ((float(latest.pe) - float(old.pe)) / float(old.pe)) * 100
            if pe_change_pct < -10:  # P/E decreased significantly (earnings improved)
                if revision_direction != 'downgrade':
                    revision_direction = 'upgrade'
            elif pe_change_pct > 10:  # P/E increased significantly (earnings worsened)
                if revision_direction != 'upgrade':
                    revision_direction = 'downgrade'
        
        # Check quarterly profit variation
        if latest.qtr_profit_var_pct:
            qtr_var = float(latest.qtr_profit_var_pct)
            if qtr_var > 20:  # Strong quarterly growth
                if revision_direction != 'downgrade':
                    revision_direction = 'upgrade'
            elif qtr_var < -20:  # Strong quarterly decline
                if revision_direction != 'upgrade':
                    revision_direction = 'downgrade'
        
        if revision_direction:
            # Check if event already exists
            existing = db.query(models.EarningsEvent).filter(
                and_(
                    models.EarningsEvent.ticker == ticker,
                    models.EarningsEvent.date == latest_fund_date,
                    models.EarningsEvent.revision_direction == revision_direction
                )
            ).first()
            
            if not existing:
                event = models.EarningsEvent(
                    date=latest_fund_date,
                    ticker=ticker,
                    sector_id=sector_id,
                    revision_direction=revision_direction,
                    source='fundamentals_inference',
                    surprise_pct=float(latest.qtr_profit_var_pct) if latest.qtr_profit_var_pct else None
                )
                db.add(event)
                count += 1
    
    db.commit()
    if count > 0:
        logger.info(f"Created {count} earnings events from fundamentals for {sector_id}")
    return count


def populate_earnings_events_for_all_sectors(
    db: Session,
    target_date: Optional[date] = None,
    lookback_days: int = 90
) -> int:
    """Populate earnings events for all sectors using fundamentals fallback."""
    if target_date is None:
        target_date = date.today()
    
    # Get all sectors
    sectors = db.query(models.Stock.sector_id).distinct().all()
    sector_ids = [s[0] for s in sectors if s[0]]
    
    total_count = 0
    for sector_id in sector_ids:
        try:
            count = create_earnings_events_from_fundamentals_changes(
                db, sector_id, target_date, lookback_days
            )
            total_count += count
        except Exception as e:
            logger.warning(f"Failed to create earnings events for {sector_id}: {e}")
            continue
    
    logger.info(f"Created {total_count} total earnings events from fundamentals")
    return total_count


def refresh_options_data(
    db: Session,
    target_date: Optional[date] = None,
    underlyings: Optional[List[str]] = None
) -> int:
    """
    Refresh options data from Kite Connect for forecast calculations.
    
    Args:
        db: Database session
        target_date: Date to fetch for (defaults to today)
        underlyings: List of underlyings to fetch (defaults to ['NIFTY', 'BANKNIFTY'])
        
    Returns:
        Number of underlyings successfully fetched
    """
    if target_date is None:
        target_date = date.today()
    
    if underlyings is None:
        underlyings = ['NIFTY', 'BANKNIFTY']
    
    count = 0
    for underlying in underlyings:
        try:
            success = fetch_kite_options.fetch_and_store_kite_options(
                db, underlying, target_date
            )
            if success:
                count += 1
        except Exception as e:
            logger.warning(f"Failed to fetch options for {underlying}: {e}")
            continue
    
    logger.info(f"Refreshed options data for {count}/{len(underlyings)} underlyings")
    return count

