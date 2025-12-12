"""Breadth-related API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import date
from sqlalchemy import desc
from app.db import database, crud, models
from app.api.v1.sectors import SECTOR_NAMES
from app.utils.sectors import get_canonical_sector_ids
from app.utils import logger

router = APIRouter()


@router.get("/breadth")
def get_breadth_metrics(
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """
    Get breadth metrics for all canonical sectors.
    
    Returns:
        Dictionary with as_of date and list of sectors with breadth metrics
    """
    canonical_sectors = get_canonical_sector_ids()
    sector_breadth = []
    
    for sector_id in canonical_sectors:
        # Get latest breadth data from SectorBreadthDaily
        breadth = db.query(models.SectorBreadthDaily).filter(
            models.SectorBreadthDaily.sector_id == sector_id
        ).order_by(desc(models.SectorBreadthDaily.date)).first()
        
        if breadth:
            # Calculate percentages
            total = breadth.total_constituents
            above_50dma_pct = breadth.above_50dma / total if total > 0 else 0.0
            above_200dma_pct = breadth.above_200dma / total if total > 0 and breadth.above_200dma else None
            highs_3m_pct = breadth.highs_3m / total if total > 0 else 0.0
            lows_3m_pct = breadth.lows_3m / total if total > 0 and breadth.lows_3m else None
            
            sector_breadth.append({
                "sector_id": sector_id,
                "name": SECTOR_NAMES.get(sector_id, sector_id),
                "above_50dma_pct": above_50dma_pct,
                "above_200dma_pct": above_200dma_pct,
                "highs_3m_pct": highs_3m_pct,
                "lows_3m_pct": lows_3m_pct,
            })
        else:
            # Try to get from SectorFeatures as fallback
            features = crud.get_latest_sector_features(db, sector_id)
            if features and features.breadth_above_50dma is not None:
                sector_breadth.append({
                    "sector_id": sector_id,
                    "name": SECTOR_NAMES.get(sector_id, sector_id),
                    "above_50dma_pct": features.breadth_above_50dma,
                    "above_200dma_pct": None,  # Not available in SectorFeatures
                    "highs_3m_pct": features.breadth_3m_highs or 0.0,
                    "lows_3m_pct": None,
                })
    
    # Get latest date
    latest_date = None
    latest_breadth = db.query(models.SectorBreadthDaily).order_by(
        desc(models.SectorBreadthDaily.date)
    ).first()
    if latest_breadth:
        latest_date = latest_breadth.date
    else:
        latest_date = date.today()
    
    return {
        "as_of": latest_date.isoformat() if latest_date else date.today().isoformat(),
        "sectors": sector_breadth
    }

