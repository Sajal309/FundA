"""Market sentiment and regime computation service."""
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db import models, crud
from app.utils import logger


def compute_market_regime(
    db: Session,
    target_date: Optional[date] = None
) -> str:
    """
    Compute market regime label based on VIX, PCR, breadth, and news sentiment.
    
    Rules:
    - RISK-ON: VIX < 30th percentile, breadth > 60%, news sentiment > 55, PCR in 0.7-1.2
    - RISK-OFF: VIX > 70th percentile, breadth < 40%, news sentiment < 45
    - NEUTRAL: Everything else
    
    Args:
        db: Database session
        target_date: Target date for computation (defaults to latest)
        
    Returns:
        Regime label: 'RISK-ON', 'NEUTRAL', or 'RISK-OFF'
    """
    # Get latest market sentiment data
    if target_date:
        market_sentiment = crud.get_market_sentiment_daily(db, target_date)
    else:
        market_sentiment = db.query(models.MarketSentimentDaily).order_by(
            desc(models.MarketSentimentDaily.date)
        ).first()
    
    if not market_sentiment:
        logger.warning("No market sentiment data available, returning NEUTRAL")
        return "NEUTRAL"
    
    # Extract metrics
    vix_percentile = market_sentiment.india_vix_percentile
    index_pcr = market_sentiment.index_pcr
    breadth = market_sentiment.breadth_nifty500_above_50dma
    news_sentiment = market_sentiment.news_sentiment_score_7d
    
    # Default to None if metrics are missing
    if vix_percentile is None or index_pcr is None or breadth is None or news_sentiment is None:
        logger.warning("Incomplete market sentiment data, returning NEUTRAL")
        return "NEUTRAL"
    
    # RISK-ON conditions
    risk_on_conditions = (
        vix_percentile < 0.30 and  # Low VIX (calm)
        breadth > 0.60 and  # Broad participation
        news_sentiment > 55 and  # Positive news sentiment
        0.7 <= index_pcr <= 1.2  # Balanced PCR
    )
    
    # RISK-OFF conditions
    risk_off_conditions = (
        vix_percentile > 0.70 and  # High VIX (fear)
        breadth < 0.40 and  # Narrow participation
        news_sentiment < 45  # Negative news sentiment
    )
    
    if risk_on_conditions:
        return "RISK-ON"
    elif risk_off_conditions:
        return "RISK-OFF"
    else:
        return "NEUTRAL"


def get_vix_label(vix: Optional[float]) -> str:
    """Get VIX label based on value."""
    if vix is None:
        return "N/A"
    if vix < 15:
        return "Calm"
    if vix < 20:
        return "Normal"
    if vix < 25:
        return "Elevated"
    return "High Fear"


def get_pcr_label(pcr: Optional[float]) -> str:
    """Get PCR label based on value."""
    if pcr is None:
        return "N/A"
    if pcr < 0.7:
        return "Bullish"
    if pcr < 1.0:
        return "Neutral-Bullish"
    if pcr < 1.3:
        return "Neutral-Bearish"
    return "Bearish"


def get_breadth_label(breadth: Optional[float]) -> str:
    """Get breadth label based on percentage."""
    if breadth is None:
        return "N/A"
    if breadth >= 0.7:
        return "Broad"
    if breadth >= 0.5:
        return "Moderate"
    if breadth >= 0.3:
        return "Narrow"
    return "Very Narrow"


def get_sentiment_label(sentiment: Optional[float]) -> str:
    """Get news sentiment label based on score (0-100)."""
    if sentiment is None:
        return "N/A"
    if sentiment >= 65:
        return "Very Positive"
    if sentiment >= 55:
        return "Positive"
    if sentiment >= 45:
        return "Neutral"
    if sentiment >= 35:
        return "Negative"
    return "Very Negative"

