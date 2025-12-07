"""Service to compute and aggregate FII/DII flows."""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from app.db import models
from app.utils import logger


def aggregate_flows_by_date(
    db: Session,
    target_date: date
) -> dict:
    """Aggregate FII/DII flows across all sectors for a date."""
    # Get all sector flows for this date
    sector_flows = db.query(models.SectorFlowsDaily).filter(
        models.SectorFlowsDaily.date == target_date
    ).all()
    
    if sector_flows:
        # Aggregate across sectors
        total_fii = sum(float(flow.fii_net_inr or 0) for flow in sector_flows)
        total_dii = sum(float(flow.dii_net_inr or 0) for flow in sector_flows)
        
        return {
            "fii_net": total_fii,
            "dii_net": total_dii,
        }
    
    # Try to get from FIIDIIDaily table and aggregate
    fii_dii_records = db.query(models.FIIDIIDaily).filter(
        models.FIIDIIDaily.date == target_date
    ).all()
    
    if fii_dii_records:
        # Aggregate buy/sell to get net
        total_fii_buy = sum(float(r.fii_buy or 0) for r in fii_dii_records)
        total_fii_sell = sum(float(r.fii_sell or 0) for r in fii_dii_records)
        total_dii_buy = sum(float(r.dii_buy or 0) for r in fii_dii_records)
        total_dii_sell = sum(float(r.dii_sell or 0) for r in fii_dii_records)
        
        return {
            "fii_net": total_fii_buy - total_fii_sell,
            "dii_net": total_dii_buy - total_dii_sell,
        }
    
    return {"fii_net": 0, "dii_net": 0}


def create_or_update_sector_flows(
    db: Session,
    sector_id: str,
    target_date: date,
    fii_net: Optional[float] = None,
    dii_net: Optional[float] = None
) -> models.SectorFlowsDaily:
    """Create or update sector flows record."""
    existing = db.query(models.SectorFlowsDaily).filter(
        and_(
            models.SectorFlowsDaily.sector_id == sector_id,
            models.SectorFlowsDaily.date == target_date
        )
    ).first()
    
    if existing:
        if fii_net is not None:
            existing.fii_net_inr = Decimal(str(fii_net))
        if dii_net is not None:
            existing.dii_net_inr = Decimal(str(dii_net))
        db.commit()
        return existing
    
    # Create new record
    flow = models.SectorFlowsDaily(
        sector_id=sector_id,
        date=target_date,
        fii_net_inr=Decimal(str(fii_net)) if fii_net is not None else None,
        dii_net_inr=Decimal(str(dii_net)) if dii_net is not None else None,
    )
    
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return flow


def distribute_flows_to_sectors(
    db: Session,
    target_date: date
) -> int:
    """Distribute aggregate FII/DII flows to sectors proportionally."""
    # Get aggregate flows from FIIDIIDaily
    fii_dii_records = db.query(models.FIIDIIDaily).filter(
        models.FIIDIIDaily.date == target_date
    ).all()
    
    if not fii_dii_records:
        return 0
    
    # Aggregate buy/sell to get net
    total_fii_buy = sum(float(r.fii_buy or 0) for r in fii_dii_records)
    total_fii_sell = sum(float(r.fii_sell or 0) for r in fii_dii_records)
    total_dii_buy = sum(float(r.dii_buy or 0) for r in fii_dii_records)
    total_dii_sell = sum(float(r.dii_sell or 0) for r in fii_dii_records)
    
    fii_net = total_fii_buy - total_fii_sell
    dii_net = total_dii_buy - total_dii_sell
    
    if fii_net == 0 and dii_net == 0:
        return 0
    
    # Get all sectors
    sectors = db.query(models.SectorTimeSeries.sector_id).distinct().all()
    sector_ids = [s[0] for s in sectors]
    
    if not sector_ids:
        return 0
    
    # Distribute proportionally (simple equal distribution for now)
    # In production, this would be based on sector market cap weights
    fii_per_sector = fii_net / len(sector_ids) if sector_ids else 0
    dii_per_sector = dii_net / len(sector_ids) if sector_ids else 0
    
    count = 0
    for sector_id in sector_ids:
        try:
            create_or_update_sector_flows(
                db, sector_id, target_date, fii_per_sector, dii_per_sector
            )
            count += 1
        except Exception as e:
            logger.error(f"Error creating flows for {sector_id}: {e}")
            continue
    
    logger.info(f"Distributed flows to {count} sectors for {target_date}")
    return count


def populate_flows_from_fii_dii(
    db: Session,
    days: int = 30
) -> int:
    """Populate sector flows from FIIDIIDaily table."""
    count = 0
    today = date.today()
    
    for i in range(days):
        target_date = today - timedelta(days=i)
        
        # Check if flows already exist
        existing = db.query(models.SectorFlowsDaily).filter(
            models.SectorFlowsDaily.date == target_date
        ).first()
        
        if existing:
            continue
        
        try:
            distributed = distribute_flows_to_sectors(db, target_date)
            count += distributed
        except Exception as e:
            logger.error(f"Error distributing flows for {target_date}: {e}")
            continue
    
    logger.info(f"Populated flows for {count} sector-date combinations")
    return count

