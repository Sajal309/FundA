"""Sector Rotation API endpoints."""
from typing import List, Literal, Optional
from datetime import date as date_type
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import sector_rotation

router = APIRouter(prefix="/sector-rotation", tags=["sector-rotation"])


@router.get("/available-dates")
def get_available_dates(
    level: Literal["sector", "industry"] = Query("sector", description="Aggregation level"),
    db: Session = Depends(get_db)
) -> List[str]:
    """Get list of available dates for sector rotation data."""
    dates = sector_rotation.get_available_dates(db, level)
    return [d.isoformat() for d in dates]


@router.get("/breadth")
def get_breadth_metrics(
    level: Literal["sector", "industry"] = Query("sector", description="Aggregation level"),
    date: str = Query(..., description="Date in YYYY-MM-DD format", alias="date"),
    metric_type: Literal["mcap", "count"] = Query("mcap", description="Metric type: mcap or count"),
    db: Session = Depends(get_db)
):
    """Get breadth metrics for sectors or industries."""
    try:
        target_date = date_type.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    results = sector_rotation.compute_breadth_metrics(db, level, target_date, metric_type)
    return {
        "date": date,
        "level": level,
        "metric_type": metric_type,
        "data": results
    }


@router.get("/scores")
def get_momentum_scores(
    level: Literal["sector", "industry"] = Query("sector", description="Aggregation level"),
    date: str = Query(..., description="Date in YYYY-MM-DD format", alias="date"),
    db: Session = Depends(get_db)
):
    """Get momentum scores for sectors or industries."""
    try:
        target_date = date_type.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    results = sector_rotation.compute_momentum_scores(db, level, target_date)
    return {
        "date": date,
        "level": level,
        "data": results
    }


@router.get("/deliveries")
def get_delivery_stats(
    level: Literal["sector", "industry"] = Query("sector", description="Aggregation level"),
    date: str = Query(..., description="Date in YYYY-MM-DD format", alias="date"),
    db: Session = Depends(get_db)
):
    """Get delivery statistics for sectors or industries."""
    try:
        target_date = date_type.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    results = sector_rotation.compute_delivery_stats(db, level, target_date)
    return {
        "date": date,
        "level": level,
        "data": results
    }


@router.get("/vwap")
def get_vwap_metrics(
    level: Literal["sector", "industry"] = Query("sector", description="Aggregation level"),
    date: str = Query(..., description="Date in YYYY-MM-DD format", alias="date"),
    db: Session = Depends(get_db)
):
    """Get VWAP metrics for sectors or industries."""
    try:
        target_date = date_type.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    results = sector_rotation.compute_vwap_metrics(db, level, target_date)
    return {
        "date": date,
        "level": level,
        "data": results
    }
