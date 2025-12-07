"""Backtesting API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import date
from app.db import database
from app.services import backtest

router = APIRouter()


@router.get("/backtest")
def run_backtest_endpoint(
    sector_id: Optional[str] = Query(None, description="Specific sector to backtest"),
    from_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """
    Run backtest on historical forecasts.
    
    Returns:
        Dictionary with backtest results and metrics
    """
    results = backtest.run_backtest(db, sector_id, from_date, to_date)
    
    # Add QuarterScore analysis if available
    if results.get("status") == "success" and results.get("results"):
        quarterscore_analysis = backtest.analyze_quarterscore_performance(results["results"])
        results["quarterscore_analysis"] = quarterscore_analysis
    
    return results

