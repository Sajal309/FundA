"""Backtesting service for forecast accuracy validation."""
from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from app.db import models, crud
from app.utils import logger


def calculate_realized_return(
    db: Session,
    sector_id: str,
    forecast_date: date,
    horizon_days: int = 90  # 3 months ≈ 90 trading days
) -> Optional[float]:
    """
    Calculate realized return for a sector after forecast date.
    
    Args:
        db: Database session
        sector_id: Sector identifier
        forecast_date: Date when forecast was made
        horizon_days: Number of trading days to look ahead
        
    Returns:
        Realized return percentage or None if insufficient data
    """
    # Get price on forecast date from time series
    timeseries_on_date = crud.get_sector_timeseries(
        db, sector_id, from_date=forecast_date, to_date=forecast_date, limit=1
    )
    if not timeseries_on_date:
        return None
    
    forecast_price = timeseries_on_date[0].close
    
    # Get price after horizon
    # Approximate: 90 trading days ≈ 4.5 months ≈ 135 calendar days
    target_date = forecast_date + timedelta(days=135)
    
    # Get latest price available up to target_date
    timeseries = crud.get_sector_timeseries(
        db, sector_id, from_date=forecast_date, to_date=target_date, limit=200
    )
    
    if not timeseries or len(timeseries) < 2:
        return None
    
    # Get the last price in the series (closest to target_date)
    final_price = float(timeseries[-1].close)
    initial_price = float(forecast_price)
    
    if initial_price == 0:
        return None
    
    realized_return = ((final_price - initial_price) / initial_price) * 100
    return realized_return


def evaluate_forecast_accuracy(
    db: Session,
    sector_id: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    min_horizon_days: int = 60
) -> Dict[str, any]:
    """
    Evaluate forecast accuracy by comparing forecasts to realized returns.
    
    Args:
        db: Database session
        sector_id: Specific sector (None for all sectors)
        from_date: Start date for evaluation period
        to_date: End date for evaluation period
        min_horizon_days: Minimum days since forecast to evaluate
        
    Returns:
        Dictionary with accuracy metrics
    """
    if to_date is None:
        to_date = date.today()
    
    if from_date is None:
        from_date = to_date - timedelta(days=180)  # 6 months back
    
    # Adjust from_date to ensure we have enough time for horizon
    from_date = from_date - timedelta(days=min_horizon_days)
    
    # Get forecasts in the period
    query = db.query(models.SectorForecast).filter(
        and_(
            models.SectorForecast.date >= from_date,
            models.SectorForecast.date <= to_date
        )
    )
    
    if sector_id:
        query = query.filter(models.SectorForecast.sector_id == sector_id)
    
    forecasts = query.order_by(models.SectorForecast.date).all()
    
    if not forecasts:
        return {
            "total_forecasts": 0,
            "evaluated": 0,
            "accuracy": None,
            "mean_error": None,
            "results": []
        }
    
    results = []
    correct_predictions = 0
    total_evaluated = 0
    errors = []
    
    for forecast in forecasts:
        # Calculate realized return
        realized_return = calculate_realized_return(
            db, forecast.sector_id, forecast.date, horizon_days=90
        )
        
        if realized_return is None:
            continue
        
        total_evaluated += 1
        
        # Determine if forecast was correct
        forecast_label = forecast.forecast_3m_label
        is_correct = False
        
        if forecast_label == "UP" and realized_return > 0:
            is_correct = True
        elif forecast_label == "DOWN" and realized_return < 0:
            is_correct = True
        elif forecast_label == "NEUTRAL" and -2.0 <= realized_return <= 2.0:
            is_correct = True
        
        if is_correct:
            correct_predictions += 1
        
        # Calculate error
        expected_return = forecast.expected_return_pct or 0.0
        error = abs(realized_return - expected_return)
        errors.append(error)
        
        results.append({
            "sector_id": forecast.sector_id,
            "forecast_date": forecast.date.isoformat(),
            "forecast_label": forecast_label,
            "expected_return": expected_return,
            "realized_return": realized_return,
            "error": error,
            "is_correct": is_correct
        })
    
    accuracy = (correct_predictions / total_evaluated * 100) if total_evaluated > 0 else None
    mean_error = sum(errors) / len(errors) if errors else None
    
    return {
        "total_forecasts": len(forecasts),
        "evaluated": total_evaluated,
        "accuracy": accuracy,
        "mean_error": mean_error,
        "correct_predictions": correct_predictions,
        "results": results
    }


def get_forecast_quality_metrics(
    db: Session,
    sector_id: Optional[str] = None
) -> Dict[str, any]:
    """
    Get quality metrics for recent forecasts.
    
    Args:
        db: Database session
        sector_id: Specific sector (None for all sectors)
        
    Returns:
        Dictionary with quality metrics
    """
    # Get latest forecasts
    query = db.query(models.SectorForecast).order_by(desc(models.SectorForecast.date))
    
    if sector_id:
        query = query.filter(models.SectorForecast.sector_id == sector_id)
    
    latest_forecasts = query.limit(50).all()
    
    if not latest_forecasts:
        return {
            "total_forecasts": 0,
            "avg_quarter_score": None,
            "avg_confidence": None,
            "data_completeness": {}
        }
    
    # Calculate average quarter score
    quarter_scores = [f.quarter_score for f in latest_forecasts if f.quarter_score is not None]
    avg_quarter_score = sum(quarter_scores) / len(quarter_scores) if quarter_scores else None
    
    # Calculate average confidence (max probability)
    confidences = []
    for f in latest_forecasts:
        max_prob = max(f.prob_up, f.prob_neutral, f.prob_down)
        confidences.append(max_prob)
    avg_confidence = sum(confidences) / len(confidences) if confidences else None
    
    # Check data completeness
    # Get latest features to check what data is available
    if sector_id:
        latest_features = crud.get_latest_sector_features(db, sector_id)
        if latest_features:
            data_completeness = {
                "breadth": latest_features.breadth_above_50dma is not None,
                "valuation": latest_features.valuation_pe_percentile is not None,
                "earnings": latest_features.earnings_upgrades_pct_60d is not None,
                "sentiment": latest_features.sentiment_score_7d is not None,
                "flows": latest_features.fii_net_inr_percentile is not None,
            }
        else:
            data_completeness = {}
    else:
        data_completeness = {}
    
    return {
        "total_forecasts": len(latest_forecasts),
        "avg_quarter_score": avg_quarter_score,
        "avg_confidence": avg_confidence,
        "data_completeness": data_completeness,
        "latest_forecast_date": latest_forecasts[0].date.isoformat() if latest_forecasts else None
    }

