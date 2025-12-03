"""Analytics API endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
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

