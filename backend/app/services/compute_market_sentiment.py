"""Service to compute and populate market sentiment data."""
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from app.db import models, crud
from app.utils import logger


def fetch_india_vix(target_date: Optional[date] = None) -> Optional[float]:
    """Fetch India VIX from yfinance."""
    try:
        ticker = yf.Ticker("^INDIAVIX")
        if target_date:
            end_date = target_date + timedelta(days=1)
            start_date = target_date - timedelta(days=5)
            hist = ticker.history(start=start_date, end=end_date)
        else:
            hist = ticker.history(period="5d")
        
        if hist.empty:
            return None
        
        # Get latest close
        latest_vix = float(hist['Close'].iloc[-1])
        logger.info(f"Fetched India VIX: {latest_vix}")
        return latest_vix
    except Exception as e:
        logger.error(f"Error fetching India VIX: {e}")
        return None


def compute_vix_percentile(db: Session, vix_value: float, target_date: date) -> Optional[float]:
    """Compute VIX percentile vs historical data."""
    # Get historical VIX data (last 1 year)
    year_ago = target_date - timedelta(days=365)
    
    historical = db.query(models.MarketSentimentDaily.india_vix).filter(
        and_(
            models.MarketSentimentDaily.date >= year_ago,
            models.MarketSentimentDaily.date < target_date,
            models.MarketSentimentDaily.india_vix.isnot(None)
        )
    ).all()
    
    if not historical:
        # If no historical data, use a default percentile based on typical VIX range (10-30)
        if vix_value < 15:
            return 0.25  # Low
        elif vix_value < 20:
            return 0.50  # Medium
        elif vix_value < 25:
            return 0.75  # High
        else:
            return 0.90  # Very High
    
    vix_values = [float(h[0]) for h in historical]
    vix_values.append(vix_value)
    vix_values.sort()
    
    # Calculate percentile
    percentile = vix_values.index(vix_value) / len(vix_values)
    return percentile


def get_index_pcr(db: Session, target_date: date) -> Optional[float]:
    """Get index Put-Call Ratio from options data."""
    # Get latest options data for NIFTY
    options = db.query(models.OptionsDaily).filter(
        and_(
            models.OptionsDaily.underlying == "NIFTY",
            models.OptionsDaily.date <= target_date
        )
    ).order_by(desc(models.OptionsDaily.date)).first()
    
    if options and options.pcr_oi:
        return float(options.pcr_oi)
    
    return None


def compute_breadth_nifty500(db: Session, target_date: date) -> Optional[float]:
    """Compute breadth: % of Nifty 500 stocks above 50DMA."""
    # Get Nifty 500 time series
    nifty500_ts = db.query(models.SectorTimeSeries).filter(
        and_(
            models.SectorTimeSeries.sector_id == "NIFTY_500",
            models.SectorTimeSeries.ts <= pd.Timestamp(target_date)
        )
    ).order_by(desc(models.SectorTimeSeries.ts)).limit(50).all()
    
    if len(nifty500_ts) < 50:
        return None
    
    # Calculate 50-day moving average
    closes = [float(ts.close) for ts in nifty500_ts]
    ma50 = sum(closes) / len(closes)
    current_price = closes[0]
    
    # For now, use a simplified approach: if current price > MA50, breadth is positive
    # In production, this would aggregate across all Nifty 500 stocks
    if current_price > ma50:
        # Estimate breadth based on price position vs MA50
        breadth = min(0.95, 0.5 + (current_price - ma50) / ma50 * 2)
    else:
        breadth = max(0.05, 0.5 - (ma50 - current_price) / ma50 * 2)
    
    return breadth


def compute_news_sentiment_7d(db: Session, target_date: date) -> Optional[float]:
    """Compute 7-day average news sentiment score."""
    week_ago = target_date - timedelta(days=7)
    
    news = db.query(models.NewsHeadline).filter(
        and_(
            models.NewsHeadline.date >= week_ago,
            models.NewsHeadline.date <= target_date,
            models.NewsHeadline.sentiment_score.isnot(None)
        )
    ).all()
    
    if not news:
        return None
    
    # Average sentiment score (convert from -1 to +1 scale to 0-100 scale)
    sentiment_scores = []
    for headline in news:
        if headline.sentiment_score is not None:
            # Convert from -1 to +1 scale to 0-100 scale
            score_0_100 = (headline.sentiment_score + 1) * 50
            sentiment_scores.append(score_0_100)
    
    if not sentiment_scores:
        return None
    
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
    return avg_sentiment


def compute_and_store_market_sentiment(
    db: Session,
    target_date: Optional[date] = None
) -> Optional[models.MarketSentimentDaily]:
    """Compute and store market sentiment data for a date."""
    if target_date is None:
        target_date = date.today()
    
    # Check if already exists
    existing = db.query(models.MarketSentimentDaily).filter(
        models.MarketSentimentDaily.date == target_date
    ).first()
    
    if existing:
        logger.info(f"Market sentiment already exists for {target_date}")
        return existing
    
    # Fetch VIX
    india_vix = fetch_india_vix(target_date)
    if india_vix is None:
        logger.warning(f"Could not fetch India VIX for {target_date}")
        # Use a default value for now
        india_vix = 18.0
    
    # Compute VIX percentile
    vix_percentile = compute_vix_percentile(db, india_vix, target_date)
    
    # Get PCR
    index_pcr = get_index_pcr(db, target_date)
    if index_pcr is None:
        # Default PCR
        index_pcr = 1.0
    
    # Compute breadth
    breadth = compute_breadth_nifty500(db, target_date)
    if breadth is None:
        # Default breadth
        breadth = 0.5
    
    # Compute news sentiment
    news_sentiment = compute_news_sentiment_7d(db, target_date)
    if news_sentiment is None:
        # Default sentiment
        news_sentiment = 50.0
    
    # Compute regime
    from app.services import sentiment_market
    regime_label = sentiment_market.compute_market_regime(
        db, target_date
    )
    # But we need to compute it manually since we don't have the record yet
    if vix_percentile and breadth and news_sentiment and index_pcr:
        if (vix_percentile < 0.30 and breadth > 0.60 and news_sentiment > 55 and 0.7 <= index_pcr <= 1.2):
            regime_label = "RISK-ON"
        elif (vix_percentile > 0.70 and breadth < 0.40 and news_sentiment < 45):
            regime_label = "RISK-OFF"
        else:
            regime_label = "NEUTRAL"
    else:
        regime_label = "NEUTRAL"
    
    # Create record
    market_sentiment = models.MarketSentimentDaily(
        date=target_date,
        india_vix=Decimal(str(india_vix)),
        india_vix_percentile=vix_percentile,
        index_pcr=index_pcr,
        breadth_nifty500_above_50dma=breadth,
        news_sentiment_score_7d=news_sentiment,
        regime_label=regime_label
    )
    
    db.add(market_sentiment)
    db.commit()
    db.refresh(market_sentiment)
    
    logger.info(f"Created market sentiment record for {target_date}: VIX={india_vix}, Regime={regime_label}")
    return market_sentiment


def populate_market_sentiment_history(
    db: Session,
    days: int = 30
) -> int:
    """Populate market sentiment data for the last N days."""
    count = 0
    today = date.today()
    
    for i in range(days):
        target_date = today - timedelta(days=i)
        
        # Skip weekends (Saturday=5, Sunday=6)
        if target_date.weekday() >= 5:
            continue
        
        try:
            result = compute_and_store_market_sentiment(db, target_date)
            if result:
                count += 1
        except Exception as e:
            logger.error(f"Error computing market sentiment for {target_date}: {e}")
            continue
    
    logger.info(f"Populated {count} market sentiment records")
    return count

