"""Stock screener API endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from sqlalchemy import func
import csv
import io
from app.db import database, models
from app.config.sector_screeners import SECTOR_SCREENERS
from app.config.ranking_config import SECTOR_RANKING_CONFIGS, get_ranking_config
from app.services import sector_screener, ranking_service
from app.utils import logger

router = APIRouter()


@router.get("/sector-screener")
def get_sector_screener(
    sector: str = Query(..., description="Sector key (e.g., 'banks', 'it', 'pharma')"),
    limit: int = Query(100, description="Maximum number of results"),
    sort_by: Optional[str] = Query(None, description="Field to sort by (defaults to score/ranking)"),
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """
    Get screened stocks for a given sector.
    
    Returns stocks sorted by ranking score by default (best to worst).
    If a ranking config exists for the sector, uses weighted scoring.
    Otherwise, falls back to sector-specific sorting.
    """
    sector_lower = sector.lower()
    
    # Check if we have a ranking config for this sector - use ranking service
    if sector_lower in SECTOR_RANKING_CONFIGS:
        try:
            result = ranking_service.compute_sector_ranked_stocks(
                db=db,
                sector_key=sector_lower,
                limit=limit,
                sort_by=sort_by  # Defaults to None, which means sort by score
            )
            
            config = get_ranking_config(sector_lower)
            
            # Get latest data timestamp
            latest_fundamentals = db.query(func.max(models.StockFundamentals.date)).scalar()
            latest_timeseries = db.query(func.max(models.StockTimeSeries.date)).scalar()
            
            last_updated = None
            if latest_fundamentals:
                last_updated = latest_fundamentals.isoformat()
            elif latest_timeseries:
                last_updated = latest_timeseries.isoformat()
            
            # Check if Kite Connect is available
            from app.services import fetch_real_stocks
            kite_available = fetch_real_stocks.get_kite_client() is not None
            
            # Format columns for response
            # Handle both dataclass ColumnConfig objects and dicts
            columns = []
            for col in result["columns"]:
                if hasattr(col, 'field'):
                    # It's a ColumnConfig dataclass
                    columns.append({
                        "field": col.field,
                        "label": col.label,
                        "tooltip": getattr(col, 'tooltip', None)
                    })
                elif isinstance(col, dict):
                    # It's already a dict
                    columns.append(col)
                else:
                    # Fallback: try to access as dict
                    columns.append({
                        "field": col.get("field") if isinstance(col, dict) else getattr(col, "field", ""),
                        "label": col.get("label") if isinstance(col, dict) else getattr(col, "label", ""),
                        "tooltip": col.get("tooltip") if isinstance(col, dict) else getattr(col, "tooltip", None)
                    })
            
            return {
                "sector": sector_lower,
                "label": config.label,
                "columns": columns,
                "rows": result["rows"],
                "count": len(result["rows"]),
                "primarySort": {
                    "field": "score",  # Default to score
                    "direction": "desc"
                },
                "secondarySort": None,
                "metadata": {
                    "last_updated": last_updated,
                    "fetched_at": datetime.utcnow().isoformat(),
                    "is_live": kite_available,
                    "source": "Kite Connect (live)" if kite_available else "yfinance (EOD)",
                    "sorted_by": sort_by or "score",  # Indicate what we sorted by
                }
            }
        except Exception as e:
            logger.error(f"Error computing ranked stocks for {sector}: {e}")
            # Fall through to old screener logic
    
    # Fallback to old screener logic for sectors without ranking config
    if sector not in SECTOR_SCREENERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sector key: {sector}. Valid keys: {', '.join(SECTOR_SCREENERS.keys())}"
        )
    
    config = SECTOR_SCREENERS[sector]
    
    # Screen stocks
    try:
        rows = sector_screener.screen_stocks(db, sector, limit)
    except Exception as e:
        logger.error(f"Error screening stocks for {sector}: {e}")
        raise HTTPException(status_code=500, detail=f"Error screening stocks: {str(e)}")
    
    # Get latest data timestamp
    latest_fundamentals = db.query(func.max(models.StockFundamentals.date)).scalar()
    latest_timeseries = db.query(func.max(models.StockTimeSeries.date)).scalar()
    
    last_updated = None
    if latest_fundamentals:
        last_updated = latest_fundamentals.isoformat()
    elif latest_timeseries:
        last_updated = latest_timeseries.isoformat()
    
    # Check if Kite Connect is available (indicates live data capability)
    from app.services import fetch_real_stocks
    kite_available = fetch_real_stocks.get_kite_client() is not None
    
    # Format columns for response
    columns = [
        {
            "field": col.field,
            "label": col.label,
            "tooltip": col.tooltip
        }
        for col in config.columns
    ]
    
    return {
        "sector": sector,
        "label": config.label,
        "columns": columns,
        "rows": rows,
        "count": len(rows),
        "primarySort": {
            "field": config.primary_sort.field,
            "direction": config.primary_sort.direction
        },
        "secondarySort": {
            "field": config.secondary_sort.field,
            "direction": config.secondary_sort.direction
        } if config.secondary_sort else None,
        "metadata": {
            "last_updated": last_updated,
            "fetched_at": datetime.utcnow().isoformat(),
            "is_live": kite_available,  # True if Kite Connect is configured (live data available)
            "source": "Kite Connect (live)" if kite_available else "yfinance (EOD)",
        }
    }


@router.get("/sector-screener/ranked")
def get_ranked_sector_screener(
    sector: str = Query(..., description="Sector key (e.g., 'it', 'fmcg', 'pharma')"),
    limit: Optional[int] = Query(100, description="Maximum number of stocks to return"),
    sort_by: Optional[str] = Query(None, description="Field to sort by (defaults to score)"),
    db: Session = Depends(database.get_db)
):
    """
    Get ranked stocks for a sector based on weighted metrics.
    
    Returns stocks sorted by computed score (best to worst) with rank included.
    Uses sector-specific weight configurations for scoring.
    """
    # Validate sector key
    sector_lower = sector.lower()
    if sector_lower not in SECTOR_RANKING_CONFIGS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sector key: {sector}. Available sectors: {list(SECTOR_RANKING_CONFIGS.keys())}"
        )
    
    # Get ranked stocks
    try:
        result = ranking_service.compute_sector_ranked_stocks(
            db=db,
            sector_key=sector_lower,
            limit=limit,
            sort_by=sort_by
        )
    except Exception as e:
        logger.error(f"Error computing ranked stocks for {sector}: {e}")
        raise HTTPException(status_code=500, detail=f"Error computing ranked stocks: {str(e)}")
    
    config = get_ranking_config(sector_lower)
    
    return {
        "status": "ok",
        "sector": sector_lower,
        "label": config.label,
        "columns": result["columns"],
        "rows": result["rows"],
        "meta": result["meta"]
    }


@router.get("/sector-screener/export")
def export_sector_screener_csv(
    sector: str = Query(..., description="Sector key"),
    limit: int = Query(100, description="Maximum number of results"),
    db: Session = Depends(database.get_db)
):
    """
    Export screened stocks to CSV.
    """
    # Validate sector key
    if sector not in SECTOR_SCREENERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sector key: {sector}"
        )
    
    config = SECTOR_SCREENERS[sector]
    
    # Screen stocks
    try:
        rows = sector_screener.screen_stocks(db, sector, limit)
    except Exception as e:
        logger.error(f"Error screening stocks for {sector}: {e}")
        raise HTTPException(status_code=500, detail=f"Error screening stocks: {str(e)}")
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    header = ['Rank'] + [col.label for col in config.columns]
    writer.writerow(header)
    
    # Write rows
    for idx, row in enumerate(rows, 1):
        csv_row = [idx] + [row.get(col.field, '') for col in config.columns]
        writer.writerow(csv_row)
    
    # Return CSV response
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={sector}_screener_{date.today().isoformat()}.csv"
        }
    )


@router.get("/sector-screener/compare")
def compare_sector_screeners(
    sectors: str = Query(..., description="Comma-separated sector keys (e.g., 'banks,it,pharma')"),
    limit: int = Query(50, description="Maximum results per sector"),
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """
    Compare multiple sector screeners side by side.
    """
    sector_list = [s.strip() for s in sectors.split(',')]
    
    # Validate sectors
    invalid = [s for s in sector_list if s not in SECTOR_SCREENERS]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sector keys: {', '.join(invalid)}"
        )
    
    if len(sector_list) > 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum 5 sectors can be compared at once"
        )
    
    # Screen each sector
    results = {}
    for sector in sector_list:
        try:
            rows = sector_screener.screen_stocks(db, sector, limit)
            config = SECTOR_SCREENERS[sector]
            results[sector] = {
                "label": config.label,
                "count": len(rows),
                "top_5": rows[:5],  # Top 5 stocks
                "primary_sort_field": config.primary_sort.field,
            }
        except Exception as e:
            logger.error(f"Error screening {sector}: {e}")
            results[sector] = {
                "label": SECTOR_SCREENERS[sector].label,
                "error": str(e)
            }
    
    return {
        "as_of": date.today().isoformat(),
        "sectors": results,
        "count": len(sector_list)
    }


@router.get("/sector-screener/list")
def list_sector_screeners() -> Dict[str, Any]:
    """
    Get list of available sector screeners.
    
    Returns metadata about all available sector screeners.
    """
    screeners = []
    for key, config in SECTOR_SCREENERS.items():
        screeners.append({
            "key": key,
            "label": config.label,
            "filterQuery": config.filter_query,
        })
    
    return {
        "screeners": screeners,
        "count": len(screeners)
    }
