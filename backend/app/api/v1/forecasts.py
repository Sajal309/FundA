"""Forecast-related API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from app.db import database, crud, models
from app.db.schemas import ForecastResponse, ForecastDriver
from app.services import forecasts, sentiment_market
from app.utils import logger
from sqlalchemy import desc

router = APIRouter()


@router.get("/sectors/{sector_id}/forecast")
def get_sector_forecast(
    sector_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Get 3-month forecast for a sector.
    Returns forecast data with metadata about freshness.
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
    
    forecast_response = ForecastResponse(
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
    
    # Return with metadata for backward compatibility
    # Frontend can access forecast directly or use metadata
    return {
        "forecast": forecast_response.dict(),
        "metadata": {
            "last_updated": forecast.date.isoformat(),
            "fetched_at": datetime.utcnow().isoformat(),
            "is_live": False,  # Forecasts are computed, not live
        }
    }


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


def get_quarter_score_label(score: float) -> str:
    """Map QuarterScore to label based on thresholds."""
    if score >= 1.5:
        return "Strong"
    elif score >= -0.5:
        return "Neutral"
    else:
        return "Weak"


@router.get("/sectors/quarter-outlook")
def get_quarter_outlook(
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """
    Get Quarter Outlook ranking for all sectors.
    
    Returns sectors sorted by quarter_score (descending).
    Only includes canonical sectors.
    """
    from app.api.v1.sectors import SECTOR_NAMES
    from app.utils.sectors import get_canonical_sector_ids
    
    # Only use canonical sectors
    canonical_sectors = get_canonical_sector_ids()
    sector_forecasts = []
    
    for sector_id in canonical_sectors:
        forecast = crud.get_latest_sector_forecast(db, sector_id)
        
        # If no forecast or forecast doesn't have quarter_score, generate one
        if not forecast or forecast.quarter_score is None:
            try:
                forecast = forecasts.generate_forecast_for_sector(db, sector_id)
            except Exception as e:
                logger.warning(f"Failed to generate forecast for {sector_id}: {e}")
                continue
        
        if forecast and forecast.quarter_score is not None:
            quarter_score = float(forecast.quarter_score)
            sector_forecasts.append({
                "sector_id": sector_id,
                "name": SECTOR_NAMES.get(sector_id, sector_id),
                "quarter_score": quarter_score,
                "label": get_quarter_score_label(quarter_score),
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


@router.get("/market-sentiment")
def get_market_sentiment(
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """
    Get market sentiment indicators and regime.
    
    Returns:
        Dictionary with VIX, PCR, breadth, news sentiment, and regime label
    """
    # Get latest market sentiment data
    market_sentiment = crud.get_market_sentiment_daily(db)
    
    if not market_sentiment:
        # Return default structure if no data
        return {
            "date": date.today().isoformat(),
            "india_vix": None,
            "india_vix_percentile": None,
            "index_pcr": None,
            "breadth_nifty500_above_50dma": None,
            "news_sentiment_score_7d": None,
            "regime_label": "NEUTRAL",
            "vix_label": "N/A",
            "pcr_label": "N/A",
            "breadth_label": "N/A",
            "sentiment_label": "N/A",
        }
    
    # Compute regime if not already set
    regime_label = market_sentiment.regime_label
    if not regime_label:
        regime_label = sentiment_market.compute_market_regime(db, market_sentiment.date)
        # Update the record
        market_sentiment.regime_label = regime_label
        db.commit()
    
    return {
        "date": market_sentiment.date.isoformat(),
        "india_vix": float(market_sentiment.india_vix) if market_sentiment.india_vix else None,
        "india_vix_percentile": float(market_sentiment.india_vix_percentile) if market_sentiment.india_vix_percentile else None,
        "index_pcr": float(market_sentiment.index_pcr) if market_sentiment.index_pcr else None,
        "breadth_nifty500_above_50dma": float(market_sentiment.breadth_nifty500_above_50dma) if market_sentiment.breadth_nifty500_above_50dma else None,
        "news_sentiment_score_7d": float(market_sentiment.news_sentiment_score_7d) if market_sentiment.news_sentiment_score_7d else None,
        "regime_label": regime_label,
        "vix_label": sentiment_market.get_vix_label(market_sentiment.india_vix),
        "pcr_label": sentiment_market.get_pcr_label(market_sentiment.index_pcr),
        "breadth_label": sentiment_market.get_breadth_label(market_sentiment.breadth_nifty500_above_50dma),
        "sentiment_label": sentiment_market.get_sentiment_label(market_sentiment.news_sentiment_score_7d),
    }

