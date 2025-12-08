"""Earnings-related API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import date, timedelta
from sqlalchemy import func, desc
from app.db import database, crud, models

router = APIRouter()


@router.get("/earnings-watch")
def get_earnings_watch(
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """
    Get earnings watch data: upcoming results and revision heatmap.
    
    Returns:
        Dictionary with next_30d earnings count and revision_heatmap
    """
    from app.api.v1.sectors import SECTOR_NAMES
    from app.utils.sectors import get_canonical_sector_ids
    
    today = date.today()
    next_30d = today + timedelta(days=30)
    
    # Only use canonical sectors
    sectors = get_canonical_sector_ids()
    
    # Get upcoming earnings (next 30 days)
    upcoming_earnings = db.query(models.EarningsEvent).filter(
        models.EarningsEvent.date >= today,
        models.EarningsEvent.date <= next_30d
    ).all()
    
    # Aggregate by sector
    next_30d_by_sector: Dict[str, Dict[str, Any]] = {}
    for event in upcoming_earnings:
        if not event.sector_id:
            continue
        
        if event.sector_id not in next_30d_by_sector:
            next_30d_by_sector[event.sector_id] = {
                "sector_id": event.sector_id,
                "name": SECTOR_NAMES.get(event.sector_id, event.sector_id),
                "results_count": 0,
                "weight_in_sector": 0.0,  # Would need constituent weights to compute properly
            }
        
        next_30d_by_sector[event.sector_id]["results_count"] += 1
    
    # Get revision heatmap (last 60 days)
    from_date = today - timedelta(days=60)
    recent_earnings = db.query(models.EarningsEvent).filter(
        models.EarningsEvent.date >= from_date,
        models.EarningsEvent.date <= today,
        models.EarningsEvent.revision_direction.isnot(None)
    ).all()
    
    # Aggregate revisions by sector
    revision_by_sector: Dict[str, Dict[str, int]] = {}
    for event in recent_earnings:
        if not event.sector_id:
            continue
        
        if event.sector_id not in revision_by_sector:
            revision_by_sector[event.sector_id] = {
                "upgrades": 0,
                "downgrades": 0,
                "total": 0,
            }
        
        revision_by_sector[event.sector_id]["total"] += 1
        if event.revision_direction == 'upgrade':
            revision_by_sector[event.sector_id]["upgrades"] += 1
        elif event.revision_direction == 'downgrade':
            revision_by_sector[event.sector_id]["downgrades"] += 1
    
    # Build revision heatmap
    revision_heatmap = []
    for sector_id in sectors:
        if sector_id in revision_by_sector:
            rev_data = revision_by_sector[sector_id]
            total = rev_data["total"]
            if total > 0:
                revision_heatmap.append({
                    "sector_id": sector_id,
                    "name": SECTOR_NAMES.get(sector_id, sector_id),
                    "upgrades_pct_60d": float(rev_data["upgrades"]) / total,
                    "downgrades_pct_60d": float(rev_data["downgrades"]) / total,
                    "total_revisions": total,
                })
        else:
            # Include sectors with no revisions
            revision_heatmap.append({
                "sector_id": sector_id,
                "name": SECTOR_NAMES.get(sector_id, sector_id),
                "upgrades_pct_60d": 0.0,
                "downgrades_pct_60d": 0.0,
                "total_revisions": 0,
            })
    
    return {
        "as_of": today.isoformat(),
        "next_30d": list(next_30d_by_sector.values()),
        "revision_heatmap": revision_heatmap,
    }

