"""Rule-based forecasting service for sectors."""
from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session
from app.db import crud, schemas
from app.utils import logger


def compute_rule_forecast(features: schemas.SectorFeaturesResponse, sector_id: str) -> Dict[str, Any]:
    """
    Compute rule-based 3-month forecast for a sector.
    
    Args:
        features: SectorFeaturesResponse object with computed features
        sector_id: Sector identifier (for sector-specific rules)
        
    Returns:
        Dictionary with forecast label, probabilities, expected return, and drivers
    """
    score = 0
    drivers = []
    
    # Momentum rules
    if features.ret_1m is not None:
        if features.ret_1m >= 3.0:
            score += 2
            drivers.append({
                "driver": "Strong 1-month momentum",
                "value": f"{features.ret_1m:.2f}%",
                "impact": "positive"
            })
        elif features.ret_1m >= 1.0:
            score += 1
            drivers.append({
                "driver": "Positive 1-month momentum",
                "value": f"{features.ret_1m:.2f}%",
                "impact": "positive"
            })
        elif features.ret_1m <= -3.0:
            score -= 2
            drivers.append({
                "driver": "Strong negative 1-month momentum",
                "value": f"{features.ret_1m:.2f}%",
                "impact": "negative"
            })
        elif features.ret_1m <= -1.0:
            score -= 1
            drivers.append({
                "driver": "Negative 1-month momentum",
                "value": f"{features.ret_1m:.2f}%",
                "impact": "negative"
            })
    
    # Moving average rules
    if features.ma20 is not None and features.ma50 is not None:
        if features.ma20 > features.ma50:
            score += 1
            drivers.append({
                "driver": "MA20 > MA50",
                "value": True,
                "impact": "positive"
            })
        else:
            score -= 1
            drivers.append({
                "driver": "MA20 <= MA50",
                "value": False,
                "impact": "negative"
            })
    
    # FII flows
    if features.fii_net_inr is not None:
        if features.fii_net_inr >= 500_000_000:
            score += 2
            drivers.append({
                "driver": "FII inflows",
                "value": features.fii_net_inr,
                "impact": "positive"
            })
        elif features.fii_net_inr <= -500_000_000:
            score -= 2
            drivers.append({
                "driver": "FII outflows",
                "value": features.fii_net_inr,
                "impact": "negative"
            })
    
    # Options-based rules
    if features.pcr_oi is not None:
        # High PCR (>1.5) suggests bearish sentiment, low PCR (<0.7) suggests bullish
        if features.pcr_oi >= 1.5:
            score -= 1
            drivers.append({
                "driver": "High Put-Call Ratio (bearish)",
                "value": f"{features.pcr_oi:.2f}",
                "impact": "negative"
            })
        elif features.pcr_oi <= 0.7:
            score += 1
            drivers.append({
                "driver": "Low Put-Call Ratio (bullish)",
                "value": f"{features.pcr_oi:.2f}",
                "impact": "positive"
            })
    
    if features.oi_change_1d is not None:
        # Large OI increases suggest strong directional moves
        if features.oi_change_1d >= 10.0:
            score += 1
            drivers.append({
                "driver": "Strong OI buildup",
                "value": f"{features.oi_change_1d:.2f}%",
                "impact": "positive"
            })
        elif features.oi_change_1d <= -10.0:
            score -= 1
            drivers.append({
                "driver": "OI unwinding",
                "value": f"{features.oi_change_1d:.2f}%",
                "impact": "negative"
            })
    
    if features.iv_index is not None:
        # High IV suggests uncertainty/volatility ahead
        if features.iv_index >= 0.25:  # 25% IV
            score -= 1
            drivers.append({
                "driver": "High implied volatility",
                "value": f"{features.iv_index:.2%}",
                "impact": "negative"
            })
        elif features.iv_index <= 0.10:  # 10% IV
            score += 0.5
            drivers.append({
                "driver": "Low implied volatility",
                "value": f"{features.iv_index:.2%}",
                "impact": "positive"
            })
    
    # Macro flags (sector-specific)
    export_sensitive_sectors = ["NIFTY_IT", "NIFTY_PHARMA"]
    if sector_id in export_sensitive_sectors:
        # Placeholder: would need USD/INR data
        # if usd_inr_pct_change <= -2:
        #     score -= 2
        pass
    
    if sector_id == "NIFTY_ENERGY" or "OIL" in sector_id.upper():
        if features.brent_pct_change_7d is not None and features.brent_pct_change_7d >= 5.0:
            score += 2
            drivers.append({
                "driver": "Brent crude surge",
                "value": f"{features.brent_pct_change_7d:.2f}%",
                "impact": "positive"
            })
    
    # Sentiment-based rules
    if features.sentiment_score_1d is not None:
        if features.sentiment_score_1d >= 0.5:
            score += 1.5
            drivers.append({
                "driver": "Strong positive sentiment",
                "value": f"{features.sentiment_score_1d:.2f}",
                "impact": "positive"
            })
        elif features.sentiment_score_1d >= 0.2:
            score += 0.5
            drivers.append({
                "driver": "Positive sentiment",
                "value": f"{features.sentiment_score_1d:.2f}",
                "impact": "positive"
            })
        elif features.sentiment_score_1d <= -0.5:
            score -= 1.5
            drivers.append({
                "driver": "Strong negative sentiment",
                "value": f"{features.sentiment_score_1d:.2f}",
                "impact": "negative"
            })
        elif features.sentiment_score_1d <= -0.2:
            score -= 0.5
            drivers.append({
                "driver": "Negative sentiment",
                "value": f"{features.sentiment_score_1d:.2f}",
                "impact": "negative"
            })
    
    if features.sentiment_score_7d is not None:
        # 7-day sentiment provides trend confirmation
        if features.sentiment_score_7d >= 0.3 and features.sentiment_score_1d is not None and features.sentiment_score_1d > 0:
            score += 0.5
            drivers.append({
                "driver": "Sustained positive sentiment trend",
                "value": f"{features.sentiment_score_7d:.2f} (7d avg)",
                "impact": "positive"
            })
        elif features.sentiment_score_7d <= -0.3 and features.sentiment_score_1d is not None and features.sentiment_score_1d < 0:
            score -= 0.5
            drivers.append({
                "driver": "Sustained negative sentiment trend",
                "value": f"{features.sentiment_score_7d:.2f} (7d avg)",
                "impact": "negative"
            })
    
    # Map score to forecast label and probabilities
    if score >= 3:
        label = "UP"
        prob_up = min(0.95, 0.7 + 0.05 * (score - 3))
        prob_neutral = (1 - prob_up) * 0.6
        prob_down = 1 - prob_up - prob_neutral
        expected_return = min(8.0, 3.0 + 0.5 * (score - 3))
    elif score >= 1:
        label = "NEUTRAL"
        prob_neutral = 0.6
        prob_up = (1 - prob_neutral) * 0.5
        prob_down = 1 - prob_neutral - prob_up
        expected_return = 0.0  # ±2% range, use 0 as midpoint
    else:
        label = "DOWN"
        prob_down = min(0.95, 0.7 + 0.05 * (-score))
        prob_neutral = (1 - prob_down) * 0.6
        prob_up = 1 - prob_down - prob_neutral
        expected_return = max(-8.0, -3.0 - 0.5 * (-score))
    
    # Ensure probabilities sum to 1.0
    total_prob = prob_up + prob_neutral + prob_down
    if abs(total_prob - 1.0) > 0.01:
        prob_up = prob_up / total_prob
        prob_neutral = prob_neutral / total_prob
        prob_down = prob_down / total_prob
    
    return {
        "forecast_3m_label": label,
        "prob_up": round(prob_up, 2),
        "prob_neutral": round(prob_neutral, 2),
        "prob_down": round(prob_down, 2),
        "expected_return_pct": round(expected_return, 2),
        "top_drivers": drivers[:5]  # Top 5 drivers
    }


def generate_forecast_for_sector(
    db: Session,
    sector_id: str,
    target_date: Optional[date] = None
) -> Optional[schemas.SectorForecastResponse]:
    """
    Generate forecast for a sector.
    
    Args:
        db: Database session
        sector_id: Sector identifier
        target_date: Date to generate forecast for
        
    Returns:
        SectorForecast object
    """
    # Get latest features
    features = crud.get_latest_sector_features(db, sector_id)
    
    if not features:
        logger.warning(f"No features found for {sector_id}, computing now...")
        from app.services.features import compute_features_for_sector
        features_response = compute_features_for_sector(db, sector_id, target_date)
        if not features_response:
            logger.error(f"Could not compute features for {sector_id}")
            return None
        features = crud.get_latest_sector_features(db, sector_id)
    
    # Compute forecast
    forecast_data = compute_rule_forecast(schemas.SectorFeaturesResponse.model_validate(features), sector_id)
    
    forecast_date = target_date if target_date else features.date
    
    # Create forecast object
    forecast = schemas.SectorForecastCreate(
        sector_id=sector_id,
        date=forecast_date,
        forecast_3m_label=forecast_data["forecast_3m_label"],
        prob_up=forecast_data["prob_up"],
        prob_neutral=forecast_data["prob_neutral"],
        prob_down=forecast_data["prob_down"],
        expected_return_pct=forecast_data["expected_return_pct"],
        top_drivers=forecast_data["top_drivers"]
    )
    
    # Save to database
    db_forecast = crud.create_or_update_sector_forecast(db, forecast)
    logger.info(f"Generated forecast for {sector_id}: {forecast_data['forecast_3m_label']}")
    
    return schemas.SectorForecastResponse.model_validate(db_forecast)


def generate_forecasts_for_all_sectors(
    db: Session,
    target_date: Optional[date] = None
) -> int:
    """
    Generate forecasts for all sectors.
    
    Args:
        db: Database session
        target_date: Date to generate forecasts for
        
    Returns:
        Number of sectors processed
    """
    sectors = crud.get_all_sectors(db)
    count = 0
    
    for sector_id in sectors:
        try:
            generate_forecast_for_sector(db, sector_id, target_date)
            count += 1
        except Exception as e:
            logger.error(f"Failed to generate forecast for {sector_id}: {e}")
            continue
    
    logger.info(f"Generated forecasts for {count} sectors")
    return count

