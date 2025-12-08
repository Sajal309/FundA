"""Analytics API endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import date
from app.db import database
from app.services import analytics

router = APIRouter()


@router.get("/analytics/correlations")
def get_sector_correlations(
    from_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    lookback_days: int = Query(30, description="Number of days to look back"),
    db: Session = Depends(database.get_db)
):
    """
    Get correlation matrix between sectors.
    
    Returns correlation coefficients for sector pairs based on returns.
    """
    correlations = analytics.calculate_sector_correlations(
        db, from_date=from_date, to_date=to_date, lookback_days=lookback_days
    )
    return {"correlations": correlations}


@router.get("/sectors/top-correlations")
def get_top_correlations(
    lookback_days: int = Query(30, description="Number of days to look back"),
    top_n: int = Query(5, description="Number of top correlations to return"),
    db: Session = Depends(database.get_db)
):
    """
    Get top positive and negative correlations between canonical sectors.
    
    Returns:
        Dictionary with 'top_positive' and 'top_negative' lists
    """
    from datetime import date
    result = analytics.get_top_correlations(db, lookback_days=lookback_days, top_n=top_n)
    return {
        "as_of": date.today().isoformat(),
        **result
    }


@router.get("/analytics/sectors/{sector_id}/trends")
def get_sector_trends(
    sector_id: str,
    lookback_days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(database.get_db)
):
    """
    Analyze trends for a specific sector.
    
    Returns trend direction, volatility regime, and price changes.
    """
    trends = analytics.analyze_sector_trends(db, sector_id, lookback_days)
    if not trends:
        raise HTTPException(status_code=404, detail=f"No data found for sector {sector_id}")
    return trends


@router.get("/analytics/sectors/compare")
def compare_sectors(
    sector_ids: str = Query(..., description="Comma-separated sector IDs"),
    metric: str = Query("returns", description="Metric to compare: returns, sentiment"),
    db: Session = Depends(database.get_db)
):
    """
    Compare multiple sectors on a metric.
    
    Example: /analytics/sectors/compare?sector_ids=NIFTY_BANK,NIFTY_IT&metric=returns
    """
    sector_list = [s.strip() for s in sector_ids.split(",")]
    comparison = analytics.get_sector_comparison(db, sector_list, metric)
    return {"comparison": comparison}


@router.get("/analytics/flows")
def get_flows_analysis(
    sector_id: Optional[str] = Query(None, description="Specific sector (optional)"),
    lookback_days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(database.get_db)
):
    """
    Analyze FII/DII flows.
    
    Returns aggregate flows, averages, and daily breakdown.
    """
    flows = analytics.get_flows_analysis(db, sector_id, lookback_days)
    return flows


@router.get("/analytics/options/{underlying}")
def get_options_analysis(
    underlying: str,
    lookback_days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(database.get_db)
):
    """
    Analyze options data for an underlying.
    
    Returns PCR, OI changes, IV, and historical data.
    """
    options = analytics.get_options_analysis(db, underlying, lookback_days)
    if not options:
        raise HTTPException(status_code=404, detail=f"No options data found for {underlying}")
    return options


@router.get("/analytics/sectors/{sector_id}/sentiment")
def get_sentiment_analysis(
    sector_id: str,
    lookback_days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(database.get_db)
):
    """
    Analyze sentiment trends for a sector.
    
    Returns sentiment scores, trends, and daily breakdown.
    """
    sentiment = analytics.get_sentiment_analysis(db, sector_id, lookback_days)
    if not sentiment:
        raise HTTPException(status_code=404, detail=f"No sentiment data found for sector {sector_id}")
    return sentiment


@router.get("/analytics/sectors/{sector_id}/performance")
def get_performance_metrics(
    sector_id: str,
    lookback_days: int = Query(252, description="Number of days to analyze (default 252 = 1 year)"),
    db: Session = Depends(database.get_db)
):
    """
    Get performance metrics for a sector (Sharpe ratio, max drawdown, win rate, RSI, etc.).
    """
    metrics = analytics.calculate_performance_metrics(db, sector_id, lookback_days)
    if not metrics:
        raise HTTPException(status_code=404, detail=f"No data found for sector {sector_id}")
    return metrics


@router.get("/analytics/sectors/strength-ranking")
def get_sector_strength_ranking(
    lookback_days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(database.get_db)
):
    """
    Get sectors ranked by relative strength (momentum + returns).
    """
    rankings = analytics.calculate_sector_strength_ranking(db, lookback_days)
    return {"rankings": rankings}


@router.get("/analytics/sectors/{sector_id}/beta")
def get_beta_and_correlation(
    sector_id: str,
    market_sector_id: str = Query("NIFTY_50", description="Market index for comparison"),
    lookback_days: int = Query(252, description="Number of days to analyze"),
    db: Session = Depends(database.get_db)
):
    """
    Calculate beta and correlation to market.
    """
    metrics = analytics.calculate_beta_and_correlation_to_market(
        db, sector_id, market_sector_id, lookback_days
    )
    if not metrics:
        raise HTTPException(status_code=404, detail=f"No data found for sector {sector_id}")
    return metrics


@router.get("/analytics/macro/summary")
def get_macro_summary(
    lookback_days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(database.get_db)
):
    """
    Get summary of macro indicators (USD/INR, Brent, Gold, US 10Y).
    """
    summary = analytics.get_macro_indicators_summary(db, lookback_days)
    return summary


@router.get("/analytics/news/latest")
def get_latest_news(
    sector_id: Optional[str] = Query(None, description="Filter by sector"),
    limit: int = Query(10, description="Number of headlines"),
    db: Session = Depends(database.get_db)
):
    """
    Get latest news headlines.
    """
    headlines = analytics.get_latest_news_headlines(db, sector_id, limit)
    return {"headlines": headlines}

