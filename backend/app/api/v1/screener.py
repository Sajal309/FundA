"""Stock screener API endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import date
import csv
import io
from app.db import database
from app.config.sector_screeners import SECTOR_SCREENERS
from app.services import sector_screener
from app.utils import logger

router = APIRouter()


@router.get("/sector-screener")
def get_sector_screener(
    sector: str = Query(..., description="Sector key (e.g., 'banks', 'it', 'pharma')"),
    limit: int = Query(100, description="Maximum number of results"),
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """
    Get screened stocks for a given sector.
    
    Returns stocks matching sector-specific criteria, sorted by sector-specific metrics.
    """
    # Validate sector key
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
        } if config.secondary_sort else None
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
