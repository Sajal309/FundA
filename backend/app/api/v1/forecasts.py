"""Forecast-related API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import date
from app.db import database, crud, models
from app.db.schemas import ForecastResponse, ForecastDriver
from app.services import forecasts
from sqlalchemy import desc

router = APIRouter()


@router.get("/sectors/{sector_id}/forecast", response_model=ForecastResponse)
def get_sector_forecast(
    sector_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Get 3-month forecast for a sector.
    """
    # Try to get existing forecast
    forecast = crud.get_latest_sector_forecast(db, sector_id)
    
    # If no forecast exists, generate one
    if not forecast:
        forecast = forecasts.generate_forecast_for_sector(db, sector_id)
    
    if not forecast:
        raise HTTPException(
            status_code=404,
            detail=f"Could not generate forecast for sector {sector_id}"
        )
    
    # Convert top_drivers to ForecastDriver objects
    drivers = []
    if forecast.top_drivers:
        for driver_data in forecast.top_drivers:
            drivers.append(ForecastDriver(
                driver=driver_data.get("driver", ""),
                value=driver_data.get("value"),
                impact=driver_data.get("impact", "neutral")
            ))
    
    return ForecastResponse(
        sector_id=forecast.sector_id,
        date=forecast.date,
        forecast_3m_label=forecast.forecast_3m_label,
        prob_up=forecast.prob_up,
        prob_neutral=forecast.prob_neutral,
        prob_down=forecast.prob_down,
        expected_return_pct=forecast.expected_return_pct,
        top_drivers=drivers,
        quarter_score=forecast.quarter_score,
        drivers=forecast.drivers
    )


@router.get("/flows")
def get_flows(
    date: str = None,  # YYYY-MM-DD format
    db: Session = Depends(database.get_db)
):
    """
    Get FII/DII flow data for all sectors.
    Note: This is a placeholder - actual flow data integration would be needed.
    """
    from app.db.schemas import FlowData
    
    sectors = crud.get_all_sectors(db)
    result = []
    
    for sector_id in sectors:
        features = crud.get_latest_sector_features(db, sector_id)
        if features and features.fii_net_inr is not None:
            result.append(FlowData(
                sector_id=sector_id,
                fii_net_inr=features.fii_net_inr,
                dii_net_inr=None  # TODO: Add DII data
            ))
    
    return result


@router.get("/sectors/quarter-outlook")
def get_quarter_outlook(
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """
    Get Quarter Outlook ranking for all sectors.
    
    Returns sectors sorted by quarter_score (descending).
    """
    from app.api.v1.sectors import SECTOR_NAMES
    
    # Get latest forecasts for all sectors
    sectors = crud.get_all_sectors(db)
    sector_forecasts = []
    
    for sector_id in sectors:
        forecast = crud.get_latest_sector_forecast(db, sector_id)
        if forecast and forecast.quarter_score is not None:
            sector_forecasts.append({
                "sector_id": sector_id,
                "name": SECTOR_NAMES.get(sector_id, sector_id),
                "quarter_score": forecast.quarter_score,
                "forecast_3m_label": forecast.forecast_3m_label,
                "expected_return_pct": forecast.expected_return_pct,
            })
    
    # Sort by quarter_score descending
    sector_forecasts.sort(key=lambda x: x["quarter_score"], reverse=True)
    
    # Get latest date
    latest_date = None
    if sector_forecasts:
        latest_forecast = db.query(models.SectorForecast).order_by(
            desc(models.SectorForecast.date)
        ).first()
        if latest_forecast:
            latest_date = latest_forecast.date
    
    return {
        "as_of": latest_date.isoformat() if latest_date else date.today().isoformat(),
        "sectors": sector_forecasts
    }

