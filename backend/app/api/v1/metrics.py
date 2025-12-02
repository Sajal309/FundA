"""Metrics and monitoring endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, date
from typing import Dict, Any
from app.db import database, models

router = APIRouter()


@router.get("/metrics")
def get_metrics(db: Session = Depends(database.get_db)) -> Dict[str, Any]:
    """
    Get system metrics for monitoring.
    
    Returns:
        Dictionary with various system metrics
    """
    metrics = {}
    
    # Data freshness
    latest_ts = db.query(func.max(models.SectorTimeSeries.ts)).scalar()
    latest_forecast = db.query(func.max(models.SectorForecast.date)).scalar()
    latest_features = db.query(func.max(models.SectorFeatures.date)).scalar()
    
    metrics["data_freshness"] = {
        "latest_timeseries": latest_ts.isoformat() if latest_ts else None,
        "latest_forecast": latest_forecast.isoformat() if latest_forecast else None,
        "latest_features": latest_features.isoformat() if latest_features else None,
    }
    
    # Record counts
    metrics["record_counts"] = {
        "sector_time_series": db.query(func.count(models.SectorTimeSeries.id)).scalar(),
        "sector_features": db.query(func.count(models.SectorFeatures.id)).scalar(),
        "sector_forecasts": db.query(func.count(models.SectorForecast.id)).scalar(),
        "fii_dii_daily": db.query(func.count(models.FIIDIIDaily.id)).scalar(),
        "sector_flows_daily": db.query(func.count(models.SectorFlowsDaily.id)).scalar(),
        "macro_daily": db.query(func.count(models.MacroDaily.id)).scalar(),
        "options_daily": db.query(func.count(models.OptionsDaily.id)).scalar(),
        "news_headlines": db.query(func.count(models.NewsHeadline.id)).scalar(),
        "sector_sentiment_daily": db.query(func.count(models.SectorSentimentDaily.id)).scalar(),
    }
    
    # Forecast distribution
    forecast_dist = db.query(
        models.SectorForecast.forecast_3m_label,
        func.count(models.SectorForecast.id)
    ).group_by(models.SectorForecast.forecast_3m_label).all()
    
    metrics["forecast_distribution"] = {
        label: count for label, count in forecast_dist
    }
    
    # Latest forecast summary
    latest_forecasts = db.query(models.SectorForecast).filter(
        models.SectorForecast.date == latest_forecast
    ).all() if latest_forecast else []
    
    metrics["latest_forecast_summary"] = {
        "date": latest_forecast.isoformat() if latest_forecast else None,
        "total_sectors": len(latest_forecasts),
        "up_count": sum(1 for f in latest_forecasts if f.forecast_3m_label == "UP"),
        "neutral_count": sum(1 for f in latest_forecasts if f.forecast_3m_label == "NEUTRAL"),
        "down_count": sum(1 for f in latest_forecasts if f.forecast_3m_label == "DOWN"),
    }
    
    return metrics


@router.get("/health")
def health_check(db: Session = Depends(database.get_db)) -> Dict[str, Any]:
    """
    Enhanced health check endpoint.
    
    Returns:
        Health status with database connectivity check
    """
    try:
        # Test database connection
        db.execute(func.text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

