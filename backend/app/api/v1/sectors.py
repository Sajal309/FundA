"""Sector-related API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.db import database, crud
from app.db.schemas import SectorSummary, TimeseriesPoint
from app.services import features, forecasts

router = APIRouter()


# Sector name mapping
SECTOR_NAMES = {
    "NIFTY_BANK": "Nifty Bank",
    "NIFTY_IT": "Nifty IT",
    "NIFTY_FMCG": "Nifty FMCG",
    "NIFTY_PHARMA": "Nifty Pharma",
    "NIFTY_AUTO": "Nifty Auto",
    "NIFTY_ENERGY": "Nifty Energy",
    "NIFTY_METAL": "Nifty Metal",
    "NIFTY_REALTY": "Nifty Realty",
    "NIFTY_PSU_BANK": "Nifty PSU Bank",
    "NIFTY_PRIVATE_BANK": "Nifty Private Bank",
}


@router.get("/sectors", response_model=List[SectorSummary])
def get_sectors(db: Session = Depends(database.get_db)):
    """
    Get list of all sectors with current performance metrics.
    """
    sectors = crud.get_all_sectors(db)
    result = []
    
    for sector_id in sectors:
        try:
            # Get latest price
            latest_price = crud.get_latest_sector_price(db, sector_id)
            if not latest_price:
                continue
            
            # Get latest features
            latest_features = crud.get_latest_sector_features(db, sector_id)
            
            # Get sparkline data (last 5 days)
            timeseries = crud.get_sector_timeseries(db, sector_id, limit=5)
            sparkline = [float(ts.close) for ts in reversed(timeseries)]
            
            # Calculate returns
            ret_1m = latest_features.ret_1m if latest_features else 0.0
            ret_1w = latest_features.ret_5d if latest_features else 0.0  # Using 5d as proxy for 1w
            
            result.append(SectorSummary(
                sector_id=sector_id,
                name=SECTOR_NAMES.get(sector_id, sector_id),
                latest_close=float(latest_price.close),
                ret_1m=ret_1m or 0.0,
                ret_1w=ret_1w or 0.0,
                sparkline=sparkline if sparkline else [float(latest_price.close)]
            ))
        except Exception as e:
            continue
    
    return result


@router.get("/sectors/{sector_id}/timeseries", response_model=List[TimeseriesPoint])
def get_sector_timeseries(
    sector_id: str,
    from_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(database.get_db)
):
    """
    Get historical timeseries data for a sector.
    """
    timeseries = crud.get_sector_timeseries(db, sector_id, from_date, to_date)
    
    if not timeseries:
        raise HTTPException(status_code=404, detail=f"No data found for sector {sector_id}")
    
    return [
        TimeseriesPoint(
            date=ts.ts.date(),
            open=float(ts.open),
            high=float(ts.high),
            low=float(ts.low),
            close=float(ts.close),
            volume=ts.volume
        )
        for ts in reversed(timeseries)  # Return chronological order
    ]

