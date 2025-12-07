"""ETL service for computing sector rotation aggregations."""
from typing import Optional, List, List as ListType
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from app.db import models
from app.utils import logger


def compute_stock_technical_indicators(
    db: Session,
    ticker: str,
    target_date: date
) -> Optional[models.StockTechnicalIndicators]:
    """
    Compute technical indicators for a stock on a given date.
    
    This is a placeholder - in production, this would:
    1. Fetch stock price history
    2. Calculate SMA20, SMA50, SMA100
    3. Calculate RSI14
    4. Calculate RS55 (relative strength vs benchmark)
    5. Calculate returns (1M, 3M, 6M)
    6. Calculate VWAP
    """
    # TODO: Implement actual calculation logic
    # For now, return None to indicate data not available
    return None


def compute_stock_rolling_stats(
    db: Session,
    ticker: str,
    target_date: date
) -> Optional[models.StockRollingStats]:
    """
    Compute 20-day rolling statistics for a stock.
    
    This calculates:
    - avg_traded_value_20d: 20-day average of close * volume
    - avg_delivery_value_20d: 20-day average of close * deliverable_volume
    """
    # Get last 20 trading days of data
    timeseries = db.query(models.StockTimeSeries).filter(
        and_(
            models.StockTimeSeries.ticker == ticker,
            models.StockTimeSeries.date <= target_date
        )
    ).order_by(desc(models.StockTimeSeries.date)).limit(20).all()
    
    if len(timeseries) < 20:
        return None
    
    # Calculate averages
    total_traded_value = sum(float(ts.close) * float(ts.volume) for ts in timeseries)
    total_delivery_value = sum(
        float(ts.close) * float(ts.deliverable_volume or 0) 
        for ts in timeseries if ts.deliverable_volume
    )
    
    avg_traded_value = Decimal(total_traded_value / 20)
    avg_delivery_value = Decimal(total_delivery_value / 20) if timeseries[0].deliverable_volume else None
    
    stats = models.StockRollingStats(
        ticker=ticker,
        date=target_date,
        avg_traded_value_20d=avg_traded_value,
        avg_delivery_value_20d=avg_delivery_value
    )
    
    return stats


def compute_sector_breadth_snapshot(
    db: Session,
    sector_id: str,
    target_date: date
) -> Optional[models.SectorBreadthSnapshot]:
    """
    Compute breadth snapshot for a sector on a given date.
    
    Aggregates stock-level technical indicators to sector-level percentages.
    """
    # Get all stocks in this sector
    stocks = db.query(models.Stock).filter(
        models.Stock.sector_id == sector_id
    ).all()
    
    if not stocks:
        return None
    
    # Get market caps for these stocks on target_date
    market_caps = db.query(models.StockMarketCap).filter(
        and_(
            models.StockMarketCap.ticker.in_([s.ticker for s in stocks]),
            models.StockMarketCap.date == target_date
        )
    ).all()
    
    # Get technical indicators
    indicators = db.query(models.StockTechnicalIndicators).filter(
        and_(
            models.StockTechnicalIndicators.ticker.in_([s.ticker for s in stocks]),
            models.StockTechnicalIndicators.date == target_date
        )
    ).all()
    
    # Get current prices
    timeseries = db.query(models.StockTimeSeries).filter(
        and_(
            models.StockTimeSeries.ticker.in_([s.ticker for s in stocks]),
            models.StockTimeSeries.date == target_date
        )
    ).all()
    
    # Create lookup maps
    mcap_map = {mc.ticker: float(mc.market_cap) for mc in market_caps}
    indicator_map = {ind.ticker: ind for ind in indicators}
    price_map = {ts.ticker: float(ts.close) for ts in timeseries}
    
    # Calculate totals
    total_mcap = sum(mcap_map.values())
    total_stocks = len(stocks)
    
    if total_mcap == 0:
        return None
    
    # Calculate metrics
    mcap_rs55_gt0 = sum(
        mcap_map.get(ticker, 0) 
        for ticker, ind in indicator_map.items() 
        if ind.rs55 and ind.rs55 > 0
    )
    mcap_rsi_gt50 = sum(
        mcap_map.get(ticker, 0) 
        for ticker, ind in indicator_map.items() 
        if ind.rsi14 and ind.rsi14 > 50
    )
    mcap_above_sma20 = sum(
        mcap_map.get(ticker, 0) 
        for ticker, ind in indicator_map.items() 
        if ind.sma20 and price_map.get(ticker, 0) > float(ind.sma20)
    )
    mcap_above_sma50 = sum(
        mcap_map.get(ticker, 0) 
        for ticker, ind in indicator_map.items() 
        if ind.sma50 and price_map.get(ticker, 0) > float(ind.sma50)
    )
    mcap_above_sma100 = sum(
        mcap_map.get(ticker, 0) 
        for ticker, ind in indicator_map.items() 
        if ind.sma100 and price_map.get(ticker, 0) > float(ind.sma100)
    )
    
    # Count-based metrics
    count_rs55_gt0 = sum(1 for ind in indicator_map.values() if ind.rs55 and ind.rs55 > 0)
    count_rsi_gt50 = sum(1 for ind in indicator_map.values() if ind.rsi14 and ind.rsi14 > 50)
    count_above_sma20 = sum(
        1 for ticker, ind in indicator_map.items() 
        if ind.sma20 and price_map.get(ticker, 0) > float(ind.sma20)
    )
    count_above_sma50 = sum(
        1 for ticker, ind in indicator_map.items() 
        if ind.sma50 and price_map.get(ticker, 0) > float(ind.sma50)
    )
    count_above_sma100 = sum(
        1 for ticker, ind in indicator_map.items() 
        if ind.sma100 and price_map.get(ticker, 0) > float(ind.sma100)
    )
    
    snapshot = models.SectorBreadthSnapshot(
        date=target_date,
        sector_id=sector_id,
        total_mcap=Decimal(total_mcap),
        total_stocks=total_stocks,
        pct_mcap_rs55_gt0=mcap_rs55_gt0 / total_mcap if total_mcap > 0 else 0,
        pct_mcap_rsi_gt50=mcap_rsi_gt50 / total_mcap if total_mcap > 0 else 0,
        pct_mcap_above_sma20=mcap_above_sma20 / total_mcap if total_mcap > 0 else 0,
        pct_mcap_above_sma50=mcap_above_sma50 / total_mcap if total_mcap > 0 else 0,
        pct_mcap_above_sma100=mcap_above_sma100 / total_mcap if total_mcap > 0 else 0,
        pct_count_rs55_gt0=count_rs55_gt0 / total_stocks if total_stocks > 0 else 0,
        pct_count_rsi_gt50=count_rsi_gt50 / total_stocks if total_stocks > 0 else 0,
        pct_count_above_sma20=count_above_sma20 / total_stocks if total_stocks > 0 else 0,
        pct_count_above_sma50=count_above_sma50 / total_stocks if total_stocks > 0 else 0,
        pct_count_above_sma100=count_above_sma100 / total_stocks if total_stocks > 0 else 0,
    )
    
    return snapshot


def compute_sector_momentum_score(
    db: Session,
    sector_id: str,
    target_date: date
) -> Optional[models.SectorMomentumScore]:
    """
    Compute momentum scores for a sector.
    
    Calculates market-cap weighted returns over 1M, 3M, 6M and converts to 0-100 scores.
    """
    # Get all stocks in sector
    stocks = db.query(models.Stock).filter(
        models.Stock.sector_id == sector_id
    ).all()
    
    if not stocks:
        return None
    
    # Get market caps
    market_caps = db.query(models.StockMarketCap).filter(
        and_(
            models.StockMarketCap.ticker.in_([s.ticker for s in stocks]),
            models.StockMarketCap.date == target_date
        )
    ).all()
    
    # Get technical indicators with returns
    indicators = db.query(models.StockTechnicalIndicators).filter(
        and_(
            models.StockTechnicalIndicators.ticker.in_([s.ticker for s in stocks]),
            models.StockTechnicalIndicators.date == target_date
        )
    ).all()
    
    mcap_map = {mc.ticker: float(mc.market_cap) for mc in market_caps}
    indicator_map = {ind.ticker: ind for ind in indicators}
    
    total_mcap = sum(mcap_map.values())
    if total_mcap == 0:
        return None
    
    # Calculate weighted returns
    weighted_return_1m = sum(
        (mcap_map.get(ticker, 0) / total_mcap) * (ind.return_1m or 0)
        for ticker, ind in indicator_map.items()
        if ind.return_1m is not None
    )
    weighted_return_3m = sum(
        (mcap_map.get(ticker, 0) / total_mcap) * (ind.return_3m or 0)
        for ticker, ind in indicator_map.items()
        if ind.return_3m is not None
    )
    weighted_return_6m = sum(
        (mcap_map.get(ticker, 0) / total_mcap) * (ind.return_6m or 0)
        for ticker, ind in indicator_map.items()
        if ind.return_6m is not None
    )
    
    # Get all sectors for normalization (we'll compute scores after all sectors are processed)
    # For now, store raw returns - scores will be computed in a second pass
    score = models.SectorMomentumScore(
        date=target_date,
        sector_id=sector_id,
        total_mcap=Decimal(total_mcap),
        total_stocks=len(stocks),
        return_1m=weighted_return_1m,
        return_3m=weighted_return_3m,
        return_6m=weighted_return_6m,
        score_1m=None,  # Will be computed in normalization pass
        score_3m=None,
        score_6m=None,
    )
    
    return score


def normalize_momentum_scores(
    db: Session,
    target_date: date,
    level: str = "sector"
) -> int:
    """
    Normalize momentum scores to 0-100 scale.
    
    This should be called after all sectors/industries have their raw returns computed.
    """
    if level == "sector":
        scores = db.query(models.SectorMomentumScore).filter(
            models.SectorMomentumScore.date == target_date
        ).all()
    else:
        scores = db.query(models.IndustryMomentumScore).filter(
            models.IndustryMomentumScore.date == target_date
        ).all()
    
    if not scores:
        return 0
    
    # Extract returns for normalization
    returns_1m = [s.return_1m for s in scores if s.return_1m is not None]
    returns_3m = [s.return_3m for s in scores if s.return_3m is not None]
    returns_6m = [s.return_6m for s in scores if s.return_6m is not None]
    
    # Calculate min/max for normalization
    def normalize_value(value: float, values: ListType[float]) -> float:
        if not values or len(values) == 0:
            return 50.0  # Default to neutral
        min_val = min(values)
        max_val = max(values)
        if max_val == min_val:
            return 50.0  # All same value, return neutral
        return 100.0 * (value - min_val) / (max_val - min_val)
    
    # Update scores
    count = 0
    for score in scores:
        if score.return_1m is not None:
            score.score_1m = normalize_value(score.return_1m, returns_1m)
        if score.return_3m is not None:
            score.score_3m = normalize_value(score.return_3m, returns_3m)
        if score.return_6m is not None:
            score.score_6m = normalize_value(score.return_6m, returns_6m)
        count += 1
    
    db.commit()
    return count


def compute_sector_delivery_stats(
    db: Session,
    sector_id: str,
    target_date: date
) -> Optional[models.SectorDeliveryStats]:
    """
    Compute delivery statistics for a sector.
    """
    # Get all stocks in sector
    stocks = db.query(models.Stock).filter(
        models.Stock.sector_id == sector_id
    ).all()
    
    if not stocks:
        return None
    
    tickers = [s.ticker for s in stocks]
    
    # Get today's data
    today_data = db.query(models.StockTimeSeries).filter(
        and_(
            models.StockTimeSeries.ticker.in_(tickers),
            models.StockTimeSeries.date == target_date
        )
    ).all()
    
    # Get previous day for MCap change
    prev_date = target_date - timedelta(days=1)
    prev_mcaps = db.query(models.StockMarketCap).filter(
        and_(
            models.StockMarketCap.ticker.in_(tickers),
            models.StockMarketCap.date == prev_date
        )
    ).all()
    
    today_mcaps = db.query(models.StockMarketCap).filter(
        and_(
            models.StockMarketCap.ticker.in_(tickers),
            models.StockMarketCap.date == target_date
        )
    ).all()
    
    # Get rolling stats
    rolling_stats = db.query(models.StockRollingStats).filter(
        and_(
            models.StockRollingStats.ticker.in_(tickers),
            models.StockRollingStats.date == target_date
        )
    ).all()
    
    # Calculate aggregates
    sector_mcap = sum(float(mc.market_cap) for mc in today_mcaps)
    prev_sector_mcap = sum(float(mc.market_cap) for mc in prev_mcaps)
    mcap_change_abs = sector_mcap - prev_sector_mcap
    mcap_change_pct = (mcap_change_abs / prev_sector_mcap * 100) if prev_sector_mcap > 0 else 0
    
    # Traded and delivery values
    traded_value = sum(float(ts.close) * float(ts.volume) for ts in today_data)
    delivery_value = sum(
        float(ts.close) * float(ts.deliverable_volume or 0) 
        for ts in today_data if ts.deliverable_volume
    )
    
    # Averages from rolling stats
    traded_value_avg = sum(float(rs.avg_traded_value_20d or 0) for rs in rolling_stats)
    delivery_value_avg = sum(float(rs.avg_delivery_value_20d or 0) for rs in rolling_stats)
    
    traded_value_multiple = (traded_value / traded_value_avg) if traded_value_avg > 0 else 0
    delivery_value_multiple = (delivery_value / delivery_value_avg) if delivery_value_avg > 0 else 0
    
    stats = models.SectorDeliveryStats(
        date=target_date,
        sector_id=sector_id,
        stocks_count=len(stocks),
        sector_mcap=Decimal(sector_mcap),
        sector_mcap_change_abs=Decimal(mcap_change_abs),
        sector_mcap_change_pct=mcap_change_pct,
        traded_value=Decimal(traded_value),
        traded_value_avg=Decimal(traded_value_avg),
        traded_value_multiple=traded_value_multiple,
        delivery_value=Decimal(delivery_value) if delivery_value > 0 else None,
        delivery_value_avg=Decimal(delivery_value_avg) if delivery_value_avg > 0 else None,
        delivery_value_multiple=delivery_value_multiple if delivery_value_multiple > 0 else None,
    )
    
    return stats


def compute_sector_vwap_snapshot(
    db: Session,
    sector_id: str,
    target_date: date
) -> Optional[models.SectorVWAPSnapshot]:
    """
    Compute VWAP snapshot for a sector.
    """
    stocks = db.query(models.Stock).filter(
        models.Stock.sector_id == sector_id
    ).all()
    
    if not stocks:
        return None
    
    tickers = [s.ticker for s in stocks]
    
    # Get market caps
    market_caps = db.query(models.StockMarketCap).filter(
        and_(
            models.StockMarketCap.ticker.in_(tickers),
            models.StockMarketCap.date == target_date
        )
    ).all()
    
    # Get price and VWAP data
    timeseries = db.query(models.StockTimeSeries).filter(
        and_(
            models.StockTimeSeries.ticker.in_(tickers),
            models.StockTimeSeries.date == target_date
        )
    ).all()
    
    indicators = db.query(models.StockTechnicalIndicators).filter(
        and_(
            models.StockTechnicalIndicators.ticker.in_(tickers),
            models.StockTechnicalIndicators.date == target_date
        )
    ).all()
    
    mcap_map = {mc.ticker: float(mc.market_cap) for mc in market_caps}
    price_map = {ts.ticker: float(ts.close) for ts in timeseries}
    vwap_map = {ind.ticker: float(ind.vwap) for ind in indicators if ind.vwap}
    
    total_mcap = sum(mcap_map.values())
    if total_mcap == 0:
        return None
    
    # Calculate % of mcap where price > VWAP
    mcap_above_vwap = sum(
        mcap_map.get(ticker, 0)
        for ticker in price_map.keys()
        if ticker in vwap_map and price_map[ticker] > vwap_map[ticker]
    )
    
    pct_mcap_above_vwap = mcap_above_vwap / total_mcap if total_mcap > 0 else 0
    
    snapshot = models.SectorVWAPSnapshot(
        date=target_date,
        sector_id=sector_id,
        total_mcap=Decimal(total_mcap),
        pct_mcap_price_above_vwap=pct_mcap_above_vwap,
    )
    
    return snapshot


def run_daily_aggregation(
    db: Session,
    target_date: Optional[date] = None
) -> int:
    """
    Run daily aggregation for all sectors and industries.
    
    Returns number of snapshots created.
    """
    if target_date is None:
        target_date = date.today()
    
    count = 0
    
    # Get all sectors
    sectors = db.query(models.Stock.sector_id).distinct().all()
    sector_ids = [s[0] for s in sectors if s[0]]
    
    logger.info(f"Computing aggregations for {len(sector_ids)} sectors on {target_date}")
    
    for sector_id in sector_ids:
        try:
            # Breadth
            breadth = compute_sector_breadth_snapshot(db, sector_id, target_date)
            if breadth:
                # Upsert - delete existing first
                existing = db.query(models.SectorBreadthSnapshot).filter(
                    and_(
                        models.SectorBreadthSnapshot.sector_id == sector_id,
                        models.SectorBreadthSnapshot.date == target_date
                    )
                ).first()
                if existing:
                    db.delete(existing)
                    db.flush()  # Ensure delete is committed before insert
                db.add(breadth)
                count += 1
            
            # Momentum
            momentum = compute_sector_momentum_score(db, sector_id, target_date)
            if momentum:
                existing = db.query(models.SectorMomentumScore).filter(
                    and_(
                        models.SectorMomentumScore.sector_id == sector_id,
                        models.SectorMomentumScore.date == target_date
                    )
                ).first()
                if existing:
                    db.delete(existing)
                    db.flush()
                db.add(momentum)
                count += 1
            
            # Deliveries
            deliveries = compute_sector_delivery_stats(db, sector_id, target_date)
            if deliveries:
                existing = db.query(models.SectorDeliveryStats).filter(
                    and_(
                        models.SectorDeliveryStats.sector_id == sector_id,
                        models.SectorDeliveryStats.date == target_date
                    )
                ).first()
                if existing:
                    db.delete(existing)
                    db.flush()
                db.add(deliveries)
                count += 1
            
            # VWAP
            vwap = compute_sector_vwap_snapshot(db, sector_id, target_date)
            if vwap:
                existing = db.query(models.SectorVWAPSnapshot).filter(
                    and_(
                        models.SectorVWAPSnapshot.sector_id == sector_id,
                        models.SectorVWAPSnapshot.date == target_date
                    )
                ).first()
                if existing:
                    db.delete(existing)
                    db.flush()
                db.add(vwap)
                count += 1
                
        except Exception as e:
            logger.error(f"Error computing aggregations for {sector_id}: {e}")
            continue
    
    db.commit()
    
    # Normalize momentum scores after all sectors are processed
    logger.info("Normalizing momentum scores...")
    normalized_count = normalize_momentum_scores(db, target_date, "sector")
    logger.info(f"Normalized {normalized_count} momentum scores")
    
    # TODO: Also compute for industries if needed
    # normalize_momentum_scores(db, target_date, "industry")
    
    logger.info(f"✅ Created {count} aggregation snapshots")
    return count

