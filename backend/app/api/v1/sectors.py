"""Sector-related API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from sqlalchemy import desc
import pandas as pd
import numpy as np
from app.db import database, crud, models
from app.db.schemas import SectorSummary, TimeseriesPoint
from app.services import features, forecasts

router = APIRouter()


# Sector name mapping - Comprehensive market indices
SECTOR_NAMES = {
    # Broad Market Indices
    "NIFTY_50": "Nifty 50",
    "NIFTY_NEXT_50": "Nifty Next 50",
    "NIFTY_100": "Nifty 100",
    "NIFTY_200": "Nifty 200",
    "NIFTY_500": "Nifty 500",
    "NIFTY_MIDCAP_50": "Nifty Midcap 50",
    "NIFTY_MIDCAP_100": "Nifty Midcap 100",
    "NIFTY_MIDCAP_150": "Nifty Midcap 150",
    "NIFTY_SMALLCAP_50": "Nifty Smallcap 50",
    "NIFTY_SMALLCAP_100": "Nifty Smallcap 100",
    "NIFTY_SMALLCAP_250": "Nifty Smallcap 250",
    # Sectoral Indices
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
    "NIFTY_FIN_SERVICE": "Nifty Financial Services",
    "NIFTY_HEALTHCARE": "Nifty Healthcare",
    "NIFTY_CONSUMER_DURABLES": "Nifty Consumer Durables",
    "NIFTY_INFRA": "Nifty Infrastructure",
    "NIFTY_OIL_GAS": "Nifty Oil & Gas",
    "NIFTY_PSE": "Nifty PSE",
    "NIFTY_SERVICES": "Nifty Services",
    "NIFTY_COMMODITIES": "Nifty Commodities",
    # Thematic Indices
    "NIFTY_GROWTH_SECTORS_15": "Nifty Growth Sectors 15",
    "NIFTY_DIVIDEND_OPPORTUNITIES_50": "Nifty Dividend Opportunities 50",
    "NIFTY_QUALITY_30": "Nifty Quality 30",
    "NIFTY_LOW_VOLATILITY_50": "Nifty Low Volatility 50",
    "NIFTY_ALPHA_50": "Nifty Alpha 50",
    "NIFTY_HIGH_BETA_50": "Nifty High Beta 50",
}


@router.get("/sectors", response_model=List[SectorSummary])
def get_sectors(db: Session = Depends(database.get_db)):
    """
    Get list of all sectors with current performance metrics.
    Returns all sectors defined in SECTOR_NAMES, even if they don't have data yet.
    """
    # Get all sectors from database
    sectors_with_data = crud.get_all_sectors(db)
    
    # Get all defined sectors from SECTOR_NAMES
    all_sector_ids = set(SECTOR_NAMES.keys())
    all_sector_ids.update(sectors_with_data)  # Include any additional sectors from DB
    
    result = []
    
    for sector_id in sorted(all_sector_ids):
        try:
            # Get latest price
            latest_price = crud.get_latest_sector_price(db, sector_id)
            
            # Get latest features
            latest_features = crud.get_latest_sector_features(db, sector_id)
            
            # Get sparkline data (last 5 days)
            timeseries = crud.get_sector_timeseries(db, sector_id, limit=5)
            sparkline = [float(ts.close) for ts in reversed(timeseries)] if timeseries else []
            
            # Use default values if no data
            if not latest_price:
                # Create a placeholder entry with default values
                result.append(SectorSummary(
                    sector_id=sector_id,
                    name=SECTOR_NAMES.get(sector_id, sector_id),
                    latest_close=0.0,
                    ret_1m=0.0,
                    ret_1w=0.0,
                    sparkline=[0.0],
                    valuation_pe=None,
                    valuation_state=None,
                    sentiment_score_7d=None,
                ))
                continue
            
            # Calculate returns
            ret_1m = latest_features.ret_1m if latest_features else 0.0
            ret_1w = latest_features.ret_5d if latest_features else 0.0  # Using 5d as proxy for 1w
            
            # Get valuation and sentiment
            valuation_pe = latest_features.valuation_pe if latest_features else None
            valuation_pe_percentile = latest_features.valuation_pe_percentile if latest_features else None
            sentiment_score_7d = latest_features.sentiment_score_7d if latest_features else None
            
            # Determine valuation state
            valuation_state = None
            if valuation_pe_percentile is not None:
                if valuation_pe_percentile < 0.4:
                    valuation_state = "cheap"
                elif valuation_pe_percentile < 0.6:
                    valuation_state = "fair"
                else:
                    valuation_state = "expensive"
            
            from app.utils.formatting import round_to_2_decimal
            
            result.append(SectorSummary(
                sector_id=sector_id,
                name=SECTOR_NAMES.get(sector_id, sector_id),
                latest_close=round_to_2_decimal(latest_price.close) or 0.0,
                ret_1m=round_to_2_decimal(ret_1m) or 0.0,
                ret_1w=round_to_2_decimal(ret_1w) or 0.0,
                sparkline=[round_to_2_decimal(v) or 0.0 for v in sparkline] if sparkline else [round_to_2_decimal(latest_price.close) or 0.0],
                valuation_pe=round_to_2_decimal(valuation_pe) if valuation_pe else None,
                valuation_state=valuation_state,
                sentiment_score_7d=round_to_2_decimal(sentiment_score_7d) if sentiment_score_7d else None,
            ))
        except Exception as e:
            # Even if there's an error, include the sector with default values
            from app.utils.formatting import round_to_2_decimal
            
            result.append(SectorSummary(
                sector_id=sector_id,
                name=SECTOR_NAMES.get(sector_id, sector_id),
                latest_close=0.0,
                ret_1m=0.0,
                ret_1w=0.0,
                sparkline=[0.0],
                valuation_pe=None,
                valuation_state=None,
                sentiment_score_7d=None,
            ))
            continue
    
    # Sort by name for better UX
    result.sort(key=lambda x: x.name)
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


@router.get("/breadth")
def get_breadth(
    db: Session = Depends(database.get_db)
):
    """
    Get breadth metrics for canonical sectors only.
    
    Returns:
        Dictionary with sectors and their breadth metrics (above 50DMA, 200DMA, 3M highs/lows)
        Only includes canonical Nifty sector indices.
    """
    from datetime import date, timedelta
    from sqlalchemy import desc
    import pandas as pd
    import numpy as np
    from app.utils.sectors import get_canonical_sector_ids
    
    # Only use canonical sectors
    sectors = get_canonical_sector_ids()
    result = []
    
    # Get latest date from breadth data or use today
    latest_breadth = db.query(models.SectorBreadthDaily).order_by(
        desc(models.SectorBreadthDaily.date)
    ).first()
    
    target_date = latest_breadth.date if latest_breadth else date.today()
    
    for sector_id in sectors:
        breadth_data = db.query(models.SectorBreadthDaily).filter(
            models.SectorBreadthDaily.sector_id == sector_id,
            models.SectorBreadthDaily.date == target_date
        ).first()
        
        if breadth_data and breadth_data.total_constituents and breadth_data.total_constituents > 0:
            # Use stored breadth data
            result.append({
                "sector_id": sector_id,
                "name": SECTOR_NAMES.get(sector_id, sector_id),
                "above_50dma_pct": float(breadth_data.above_50dma) / breadth_data.total_constituents,
                "above_200dma_pct": float(breadth_data.above_200dma) / breadth_data.total_constituents if breadth_data.above_200dma else None,
                "highs_3m_pct": float(breadth_data.making_3m_highs) / breadth_data.total_constituents,
                "lows_3m_pct": float(breadth_data.making_3m_lows) / breadth_data.total_constituents if breadth_data.making_3m_lows else None,
            })
        else:
            # Compute approximate breadth from sector index itself
            timeseries = crud.get_sector_timeseries(db, sector_id, limit=200)
            if timeseries and len(timeseries) >= 50:
                # Convert to DataFrame
                df = pd.DataFrame([{
                    'ts': ts.ts,
                    'close': float(ts.close),
                } for ts in timeseries])
                df = df.sort_values('ts')
                df.set_index('ts', inplace=True)
                
                # Filter to target_date
                df = df[df.index <= pd.Timestamp(target_date)]
                
                if len(df) >= 50:
                    closes = df['close']
                    current_price = closes.iloc[-1]
                    
                    # Calculate moving averages
                    ma50 = closes.rolling(50).mean().iloc[-1] if len(closes) >= 50 else None
                    ma200 = closes.rolling(200).mean().iloc[-1] if len(closes) >= 200 else None
                    
                    # Check if above 50DMA/200DMA
                    above_50dma = 1.0 if (ma50 and current_price > ma50) else 0.0
                    above_200dma = 1.0 if (ma200 and current_price > ma200) else 0.0
                    
                    # Check for 3M highs/lows (approximate: check if current price is near 3M high/low)
                    if len(closes) >= 63:  # ~3 months
                        high_3m = closes.rolling(63).max().iloc[-1]
                        low_3m = closes.rolling(63).min().iloc[-1]
                        price_range = high_3m - low_3m
                        
                        if price_range > 0:
                            # If within 5% of high, consider it a high
                            highs_3m = 1.0 if (current_price >= high_3m * 0.95) else 0.0
                            # If within 5% of low, consider it a low
                            lows_3m = 1.0 if (current_price <= low_3m * 1.05) else 0.0
                        else:
                            highs_3m = 0.0
                            lows_3m = 0.0
                    else:
                        highs_3m = None
                        lows_3m = None
                    
                    result.append({
                        "sector_id": sector_id,
                        "name": SECTOR_NAMES.get(sector_id, sector_id),
                        "above_50dma_pct": above_50dma,
                        "above_200dma_pct": above_200dma if ma200 else None,
                        "highs_3m_pct": highs_3m,
                        "lows_3m_pct": lows_3m,
                    })
    
    return {
        "as_of": target_date.isoformat(),
        "sectors": result
    }

