"""Sector Rotation calculation services."""
from typing import List, Dict, Optional, Literal
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from app.db import models
from app.utils import logger


def get_available_dates(db: Session, level: Literal["sector", "industry"] = "sector") -> List[date]:
    """Get list of available dates for sector rotation data."""
    if level == "sector":
        dates = db.query(models.SectorBreadthSnapshot.date).distinct().order_by(desc(models.SectorBreadthSnapshot.date)).all()
    else:
        dates = db.query(models.IndustryBreadthSnapshot.date).distinct().order_by(desc(models.IndustryBreadthSnapshot.date)).all()
    
    return [d[0] for d in dates] if dates else []


def compute_breadth_metrics(
    db: Session,
    level: Literal["sector", "industry"],
    target_date: date,
    metric_type: Literal["mcap", "count"] = "mcap"
) -> List[Dict]:
    """
    Compute breadth metrics for sectors or industries.
    
    Returns list of dicts with:
    - id: sector_id or industry_id
    - name: sector/industry name
    - mcap: total market cap
    - stocks: total stock count
    - metrics: dict with pct_rs55_gt0, pct_rsi_gt50, pct_above_sma20, pct_above_sma50, pct_above_sma100
    """
    if level == "sector":
        snapshots = db.query(models.SectorBreadthSnapshot).filter(
            models.SectorBreadthSnapshot.date == target_date
        ).all()
        
        # Get sector names
        sector_names = {}
        for snapshot in snapshots:
            # Use sector_id as name for now, can be enhanced with a lookup table
            sector_names[snapshot.sector_id] = snapshot.sector_id.replace("NIFTY_", "").replace("_", " ").title()
    else:
        snapshots = db.query(models.IndustryBreadthSnapshot).filter(
            models.IndustryBreadthSnapshot.date == target_date
        ).all()
        
        # Get industry names
        industry_names = {}
        industries = db.query(models.Industry).filter(
            models.Industry.industry_id.in_([s.industry_id for s in snapshots])
        ).all()
        for ind in industries:
            industry_names[ind.industry_id] = ind.name
        
        for snapshot in snapshots:
            if snapshot.industry_id not in industry_names:
                industry_names[snapshot.industry_id] = snapshot.industry_id.replace("_", " ").title()
    
    results = []
    for snapshot in snapshots:
        if level == "sector":
            entity_id = snapshot.sector_id
            name = sector_names.get(entity_id, entity_id.replace("NIFTY_", "").replace("_", " ").title())
        else:
            entity_id = snapshot.industry_id
            name = industry_names.get(entity_id, entity_id.replace("_", " ").title())
        
        if metric_type == "mcap":
            metrics = {
                "pct_rs55_gt0": snapshot.pct_mcap_rs55_gt0 * 100 if snapshot.pct_mcap_rs55_gt0 else 0,
                "pct_rsi_gt50": snapshot.pct_mcap_rsi_gt50 * 100 if snapshot.pct_mcap_rsi_gt50 else 0,
                "pct_above_sma20": snapshot.pct_mcap_above_sma20 * 100 if snapshot.pct_mcap_above_sma20 else 0,
                "pct_above_sma50": snapshot.pct_mcap_above_sma50 * 100 if snapshot.pct_mcap_above_sma50 else 0,
                "pct_above_sma100": snapshot.pct_mcap_above_sma100 * 100 if snapshot.pct_mcap_above_sma100 else 0,
            }
        else:
            metrics = {
                "pct_rs55_gt0": snapshot.pct_count_rs55_gt0 * 100 if snapshot.pct_count_rs55_gt0 else 0,
                "pct_rsi_gt50": snapshot.pct_count_rsi_gt50 * 100 if snapshot.pct_count_rsi_gt50 else 0,
                "pct_above_sma20": snapshot.pct_count_above_sma20 * 100 if snapshot.pct_count_above_sma20 else 0,
                "pct_above_sma50": snapshot.pct_count_above_sma50 * 100 if snapshot.pct_count_above_sma50 else 0,
                "pct_above_sma100": snapshot.pct_count_above_sma100 * 100 if snapshot.pct_count_above_sma100 else 0,
            }
        
        results.append({
            "id": entity_id,
            "name": name,
            "mcap": float(snapshot.total_mcap) / 10000000,  # Convert to crores
            "stocks": snapshot.total_stocks,
            "metrics": metrics
        })
    
    # Sort by mcap descending
    results.sort(key=lambda x: x["mcap"], reverse=True)
    return results


def compute_momentum_scores(
    db: Session,
    level: Literal["sector", "industry"],
    target_date: date
) -> List[Dict]:
    """
    Compute momentum scores for sectors or industries.
    
    Returns list of dicts with:
    - id: sector_id or industry_id
    - name: sector/industry name
    - mcap: total market cap in crores
    - stocks: total stock count
    - score_1m, score_3m, score_6m: momentum scores (0-100)
    """
    if level == "sector":
        scores = db.query(models.SectorMomentumScore).filter(
            models.SectorMomentumScore.date == target_date
        ).all()
        
        sector_names = {}
        for score in scores:
            sector_names[score.sector_id] = score.sector_id.replace("NIFTY_", "").replace("_", " ").title()
    else:
        scores = db.query(models.IndustryMomentumScore).filter(
            models.IndustryMomentumScore.date == target_date
        ).all()
        
        industry_names = {}
        industries = db.query(models.Industry).filter(
            models.Industry.industry_id.in_([s.industry_id for s in scores])
        ).all()
        for ind in industries:
            industry_names[ind.industry_id] = ind.name
        
        for score in scores:
            if score.industry_id not in industry_names:
                industry_names[score.industry_id] = score.industry_id.replace("_", " ").title()
    
    results = []
    for score in scores:
        if level == "sector":
            entity_id = score.sector_id
            name = sector_names.get(entity_id, entity_id.replace("NIFTY_", "").replace("_", " ").title())
        else:
            entity_id = score.industry_id
            name = industry_names.get(entity_id, entity_id.replace("_", " ").title())
        
        results.append({
            "id": entity_id,
            "name": name,
            "mcap": float(score.total_mcap) / 10000000,  # Convert to crores
            "stocks": score.total_stocks,
            "score_1m": score.score_1m if score.score_1m is not None else 0,
            "score_3m": score.score_3m if score.score_3m is not None else 0,
            "score_6m": score.score_6m if score.score_6m is not None else 0,
        })
    
    # Sort by mcap descending
    results.sort(key=lambda x: x["mcap"], reverse=True)
    return results


def compute_delivery_stats(
    db: Session,
    level: Literal["sector", "industry"],
    target_date: date
) -> List[Dict]:
    """
    Compute delivery statistics for sectors or industries.
    
    Returns list of dicts with delivery and volume metrics.
    """
    if level == "sector":
        stats = db.query(models.SectorDeliveryStats).filter(
            models.SectorDeliveryStats.date == target_date
        ).all()
        
        sector_names = {}
        for stat in stats:
            sector_names[stat.sector_id] = stat.sector_id.replace("NIFTY_", "").replace("_", " ").title()
    else:
        stats = db.query(models.IndustryDeliveryStats).filter(
            models.IndustryDeliveryStats.date == target_date
        ).all()
        
        industry_names = {}
        industries = db.query(models.Industry).filter(
            models.Industry.industry_id.in_([s.industry_id for s in stats])
        ).all()
        for ind in industries:
            industry_names[ind.industry_id] = ind.name
        
        for stat in stats:
            if stat.industry_id not in industry_names:
                industry_names[stat.industry_id] = stat.industry_id.replace("_", " ").title()
    
    results = []
    for stat in stats:
        if level == "sector":
            entity_id = stat.sector_id
            name = sector_names.get(entity_id, entity_id.replace("NIFTY_", "").replace("_", " ").title())
        else:
            entity_id = stat.industry_id
            name = industry_names.get(entity_id, entity_id.replace("_", " ").title())
        
        results.append({
            "id": entity_id,
            "name": name,
            "stocks": stat.stocks_count,
            "mcap": float(stat.sector_mcap if level == "sector" else stat.industry_mcap) / 10000000,  # Crores
            "mcap_change_abs": float(stat.sector_mcap_change_abs if level == "sector" else stat.industry_mcap_change_abs) / 10000000 if (stat.sector_mcap_change_abs if level == "sector" else stat.industry_mcap_change_abs) else 0,
            "mcap_change_pct": stat.sector_mcap_change_pct if level == "sector" else stat.industry_mcap_change_pct or 0,
            "traded_value": float(stat.traded_value) / 10000000 if stat.traded_value else 0,  # Crores
            "traded_value_avg": float(stat.traded_value_avg) / 10000000 if stat.traded_value_avg else 0,  # Crores
            "traded_value_multiple": stat.traded_value_multiple if stat.traded_value_multiple else 0,
            "delivery_value": float(stat.delivery_value) / 10000000 if stat.delivery_value else 0,  # Crores
            "delivery_value_avg": float(stat.delivery_value_avg) / 10000000 if stat.delivery_value_avg else 0,  # Crores
            "delivery_value_multiple": stat.delivery_value_multiple if stat.delivery_value_multiple else 0,
        })
    
    # Sort by mcap descending
    results.sort(key=lambda x: x["mcap"], reverse=True)
    return results


def compute_vwap_metrics(
    db: Session,
    level: Literal["sector", "industry"],
    target_date: date
) -> List[Dict]:
    """
    Compute VWAP metrics for sectors or industries.
    
    Returns list of dicts with VWAP-based metrics.
    """
    if level == "sector":
        snapshots = db.query(models.SectorVWAPSnapshot).filter(
            models.SectorVWAPSnapshot.date == target_date
        ).all()
        
        sector_names = {}
        for snapshot in snapshots:
            sector_names[snapshot.sector_id] = snapshot.sector_id.replace("NIFTY_", "").replace("_", " ").title()
    else:
        snapshots = db.query(models.IndustryVWAPSnapshot).filter(
            models.IndustryVWAPSnapshot.date == target_date
        ).all()
        
        industry_names = {}
        industries = db.query(models.Industry).filter(
            models.Industry.industry_id.in_([s.industry_id for s in snapshots])
        ).all()
        for ind in industries:
            industry_names[ind.industry_id] = ind.name
        
        for snapshot in snapshots:
            if snapshot.industry_id not in industry_names:
                industry_names[snapshot.industry_id] = snapshot.industry_id.replace("_", " ").title()
    
    results = []
    for snapshot in snapshots:
        if level == "sector":
            entity_id = snapshot.sector_id
            name = sector_names.get(entity_id, entity_id.replace("NIFTY_", "").replace("_", " ").title())
        else:
            entity_id = snapshot.industry_id
            name = industry_names.get(entity_id, entity_id.replace("_", " ").title())
        
        results.append({
            "id": entity_id,
            "name": name,
            "mcap": float(snapshot.total_mcap) / 10000000,  # Convert to crores
            "pct_mcap_price_above_vwap": snapshot.pct_mcap_price_above_vwap * 100 if snapshot.pct_mcap_price_above_vwap else 0,
        })
    
    # Sort by mcap descending
    results.sort(key=lambda x: x["mcap"], reverse=True)
    return results

