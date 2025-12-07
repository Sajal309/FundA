"""Backtesting module for evaluating forecast accuracy."""
import pandas as pd
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from app.db import crud, models
from app.utils import logger


def calculate_realized_return(
    db: Session,
    sector_id: str,
    forecast_date: date,
    horizon_days: int = 90  # 3 months ≈ 90 trading days
) -> Optional[float]:
    """
    Calculate realized return from forecast date to horizon.
    
    Args:
        db: Database session
        sector_id: Sector identifier
        forecast_date: Date when forecast was made
        horizon_days: Number of trading days to look forward
        
    Returns:
        Realized return percentage, or None if insufficient data
    """
    # Get price at forecast date
    forecast_price = crud.get_latest_sector_price(db, sector_id)
    if not forecast_price or forecast_price.ts.date() != forecast_date:
        # Try to get price on or before forecast date
        timeseries = crud.get_sector_timeseries(
            db, sector_id, to_date=forecast_date, limit=1
        )
        if not timeseries:
            return None
        forecast_price = timeseries[0]
    
    # Get price at horizon (approximately 90 trading days later)
    # Trading days ≈ calendar days * 5/7, so 90 trading days ≈ 126 calendar days
    horizon_date = forecast_date + timedelta(days=int(horizon_days * 1.4))
    horizon_timeseries = crud.get_sector_timeseries(
        db, sector_id, to_date=horizon_date, limit=100
    )
    
    if not horizon_timeseries:
        return None
    
    # Find closest price to horizon
    horizon_price = None
    for ts in horizon_timeseries:
        if ts.ts.date() >= forecast_date + timedelta(days=horizon_days * 0.8):
            horizon_price = ts
            break
    
    if not horizon_price:
        # Use latest available price
        horizon_price = horizon_timeseries[0]
    
    # Calculate return
    if forecast_price.close and horizon_price.close:
        return float((horizon_price.close - forecast_price.close) / forecast_price.close * 100)
    
    return None


def evaluate_forecast_accuracy(
    db: Session,
    sector_id: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> List[Dict]:
    """
    Evaluate forecast accuracy for historical forecasts.
    
    Args:
        db: Database session
        sector_id: Specific sector to evaluate (None for all)
        from_date: Start date for evaluation
        to_date: End date for evaluation
        
    Returns:
        List of evaluation results
    """
    # Get forecasts to evaluate
    query = db.query(models.SectorForecast)
    
    if sector_id:
        query = query.filter(models.SectorForecast.sector_id == sector_id)
    if from_date:
        query = query.filter(models.SectorForecast.date >= from_date)
    if to_date:
        query = query.filter(models.SectorForecast.date <= to_date)
    
    forecasts = query.order_by(models.SectorForecast.date).all()
    
    results = []
    for forecast in forecasts:
        # Calculate realized return
        realized_return = calculate_realized_return(
            db, forecast.sector_id, forecast.date, horizon_days=90
        )
        
        if realized_return is None:
            continue
        
        # Determine actual label
        if realized_return >= 2.0:
            actual_label = "UP"
        elif realized_return <= -2.0:
            actual_label = "DOWN"
        else:
            actual_label = "NEUTRAL"
        
        # Check if forecast was correct
        is_correct = (forecast.forecast_3m_label == actual_label)
        
        # Calculate error metrics
        forecast_error = abs(realized_return - forecast.expected_return_pct)
        
        results.append({
            "sector_id": forecast.sector_id,
            "forecast_date": forecast.date.isoformat(),
            "forecast_label": forecast.forecast_3m_label,
            "actual_label": actual_label,
            "forecast_return": forecast.expected_return_pct,
            "realized_return": realized_return,
            "is_correct": is_correct,
            "forecast_error": forecast_error,
            "prob_up": forecast.prob_up,
            "prob_neutral": forecast.prob_neutral,
            "prob_down": forecast.prob_down,
            "quarter_score": float(forecast.quarter_score) if forecast.quarter_score else None,
        })
    
    return results


def compute_backtest_metrics(results: List[Dict]) -> Dict:
    """
    Compute aggregate metrics from backtest results.
    
    Args:
        results: List of evaluation results
        
    Returns:
        Dictionary with aggregate metrics
    """
    if not results:
        return {
            "total_forecasts": 0,
            "directional_accuracy": 0.0,
            "mean_absolute_error": 0.0,
            "up_accuracy": 0.0,
            "down_accuracy": 0.0,
            "neutral_accuracy": 0.0,
        }
    
    total = len(results)
    correct = sum(1 for r in results if r["is_correct"])
    directional_accuracy = correct / total if total > 0 else 0.0
    
    # Mean absolute error
    mae = sum(r["forecast_error"] for r in results) / total if total > 0 else 0.0
    
    # Label-specific accuracy
    up_forecasts = [r for r in results if r["forecast_label"] == "UP"]
    down_forecasts = [r for r in results if r["forecast_label"] == "DOWN"]
    neutral_forecasts = [r for r in results if r["forecast_label"] == "NEUTRAL"]
    
    up_correct = sum(1 for r in up_forecasts if r["actual_label"] == "UP")
    down_correct = sum(1 for r in down_forecasts if r["actual_label"] == "DOWN")
    neutral_correct = sum(1 for r in neutral_forecasts if r["actual_label"] == "NEUTRAL")
    
    up_accuracy = up_correct / len(up_forecasts) if up_forecasts else 0.0
    down_accuracy = down_correct / len(down_forecasts) if down_forecasts else 0.0
    neutral_accuracy = neutral_correct / len(neutral_forecasts) if neutral_forecasts else 0.0
    
    # Confusion matrix
    confusion_matrix = {
        "up_predicted_up": sum(1 for r in results if r["forecast_label"] == "UP" and r["actual_label"] == "UP"),
        "up_predicted_down": sum(1 for r in results if r["forecast_label"] == "UP" and r["actual_label"] == "DOWN"),
        "up_predicted_neutral": sum(1 for r in results if r["forecast_label"] == "UP" and r["actual_label"] == "NEUTRAL"),
        "down_predicted_up": sum(1 for r in results if r["forecast_label"] == "DOWN" and r["actual_label"] == "UP"),
        "down_predicted_down": sum(1 for r in results if r["forecast_label"] == "DOWN" and r["actual_label"] == "DOWN"),
        "down_predicted_neutral": sum(1 for r in results if r["forecast_label"] == "DOWN" and r["actual_label"] == "NEUTRAL"),
        "neutral_predicted_up": sum(1 for r in results if r["forecast_label"] == "NEUTRAL" and r["actual_label"] == "UP"),
        "neutral_predicted_down": sum(1 for r in results if r["forecast_label"] == "NEUTRAL" and r["actual_label"] == "DOWN"),
        "neutral_predicted_neutral": sum(1 for r in results if r["forecast_label"] == "NEUTRAL" and r["actual_label"] == "NEUTRAL"),
    }
    
    return {
        "total_forecasts": total,
        "directional_accuracy": round(directional_accuracy, 3),
        "mean_absolute_error": round(mae, 2),
        "up_accuracy": round(up_accuracy, 3),
        "down_accuracy": round(down_accuracy, 3),
        "neutral_accuracy": round(neutral_accuracy, 3),
        "confusion_matrix": confusion_matrix,
    }


def run_backtest(
    db: Session,
    sector_id: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    output_path: Optional[str] = None
) -> Dict:
    """
    Run full backtest and generate report.
    
    Args:
        db: Database session
        sector_id: Specific sector to backtest
        from_date: Start date
        to_date: End date
        output_path: Path to save CSV report (optional)
        
    Returns:
        Dictionary with backtest results and metrics
    """
    logger.info(f"Starting backtest for sector={sector_id}, from={from_date}, to={to_date}")
    
    # Evaluate forecasts
    results = evaluate_forecast_accuracy(db, sector_id, from_date, to_date)
    
    if not results:
        logger.warning("No forecast results to evaluate")
        return {
            "status": "no_data",
            "results": [],
            "metrics": compute_backtest_metrics([])
        }
    
    # Compute metrics
    metrics = compute_backtest_metrics(results)
    
    # Save to CSV if path provided
    if output_path:
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False)
        logger.info(f"Backtest report saved to {output_path}")
    
    logger.info(f"Backtest complete: {metrics['directional_accuracy']*100:.1f}% accuracy on {metrics['total_forecasts']} forecasts")
    
    return {
        "status": "success",
        "results": results,
        "metrics": metrics
    }


def analyze_quarterscore_performance(
    results: List[Dict]
) -> Dict[str, Any]:
    """
    Analyze QuarterScore performance by score buckets.
    
    Args:
        results: List of evaluation results with quarter_score
        
    Returns:
        Dictionary with performance by QuarterScore buckets
    """
    # Filter results with QuarterScore
    scored_results = [r for r in results if r.get("quarter_score") is not None]
    
    if not scored_results:
        return {
            "total_scored": 0,
            "buckets": []
        }
    
    # Define buckets
    buckets = [
        {"name": "Strong Positive", "min": 1.5, "max": float('inf')},
        {"name": "Moderate Positive", "min": 0.5, "max": 1.5},
        {"name": "Neutral", "min": -0.5, "max": 0.5},
        {"name": "Moderate Negative", "min": -1.5, "max": -0.5},
        {"name": "Strong Negative", "min": float('-inf'), "max": -1.5},
    ]
    
    bucket_analysis = []
    for bucket in buckets:
        bucket_results = [
            r for r in scored_results
            if bucket["min"] <= r["quarter_score"] < bucket["max"]
        ]
        
        if bucket_results:
            avg_return = sum(r["realized_return"] for r in bucket_results) / len(bucket_results)
            accuracy = sum(1 for r in bucket_results if r["is_correct"]) / len(bucket_results)
            bucket_analysis.append({
                "bucket": bucket["name"],
                "count": len(bucket_results),
                "avg_realized_return": round(avg_return, 2),
                "accuracy": round(accuracy, 3),
                "avg_quarterscore": round(sum(r["quarter_score"] for r in bucket_results) / len(bucket_results), 2),
            })
    
    return {
        "total_scored": len(scored_results),
        "buckets": bucket_analysis
    }

