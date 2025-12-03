"""Analytics and data analysis functions."""
import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.db import crud, models
from app.utils import logger


def calculate_sector_correlations(
    db: Session,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    lookback_days: int = 30
) -> Dict[str, Dict[str, float]]:
    """
    Calculate correlation matrix between sectors based on returns.
    
    Args:
        db: Database session
        from_date: Start date
        to_date: End date
        lookback_days: Number of days to look back
        
    Returns:
        Dictionary mapping sector pairs to correlation coefficients
    """
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=lookback_days)
    
    # Get all sectors
    sector_ids = crud.get_all_sectors(db)
    
    # Get returns for each sector
    sector_returns = {}
    for sector_id in sector_ids:
        timeseries = crud.get_sector_timeseries(
            db, sector_id, from_date=from_date, to_date=to_date, limit=1000
        )
        if len(timeseries) < 10:
            continue
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(timeseries)):
            prev_close = float(timeseries[i].close)
            curr_close = float(timeseries[i-1].close)
            if prev_close > 0:
                daily_return = (curr_close - prev_close) / prev_close
                returns.append(daily_return)
        
        if len(returns) >= 10:
            sector_returns[sector_id] = returns
    
    # Calculate correlation matrix
    correlations = {}
    sector_list = list(sector_returns.keys())
    
    for i, sector1 in enumerate(sector_list):
        for sector2 in sector_list[i+1:]:
            ret1 = sector_returns[sector1]
            ret2 = sector_returns[sector2]
            
            # Align lengths
            min_len = min(len(ret1), len(ret2))
            ret1_aligned = ret1[:min_len]
            ret2_aligned = ret2[:min_len]
            
            if min_len >= 10:
                corr = np.corrcoef(ret1_aligned, ret2_aligned)[0, 1]
                if not np.isnan(corr):
                    correlations[f"{sector1}_{sector2}"] = float(corr)
    
    return correlations


def analyze_sector_trends(
    db: Session,
    sector_id: str,
    lookback_days: int = 30
) -> Dict[str, any]:
    """
    Analyze trends for a sector.
    
    Args:
        db: Database session
        sector_id: Sector identifier
        lookback_days: Number of days to analyze
        
    Returns:
        Dictionary with trend analysis
    """
    to_date = date.today()
    from_date = to_date - timedelta(days=lookback_days)
    
    timeseries = crud.get_sector_timeseries(
        db, sector_id, from_date=from_date, to_date=to_date, limit=1000
    )
    
    if len(timeseries) < 5:
        return {}
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'date': ts.ts.date(),
        'close': float(ts.close),
        'volume': ts.volume
    } for ts in reversed(timeseries)])
    
    # Calculate trends
    df['returns'] = df['close'].pct_change()
    df['volatility'] = df['returns'].rolling(5).std() * np.sqrt(252)  # Annualized
    
    # Trend direction
    recent_returns = df['returns'].tail(5).mean()
    if recent_returns > 0.001:
        trend = "uptrend"
    elif recent_returns < -0.001:
        trend = "downtrend"
    else:
        trend = "sideways"
    
    # Volatility regime
    avg_vol = df['volatility'].mean()
    current_vol = df['volatility'].iloc[-1] if len(df) > 0 else avg_vol
    if current_vol > avg_vol * 1.2:
        vol_regime = "high"
    elif current_vol < avg_vol * 0.8:
        vol_regime = "low"
    else:
        vol_regime = "normal"
    
    return {
        "trend": trend,
        "trend_strength": abs(recent_returns) * 100,
        "volatility_regime": vol_regime,
        "current_volatility": float(current_vol) if not pd.isna(current_vol) else None,
        "avg_volatility": float(avg_vol) if not pd.isna(avg_vol) else None,
        "price_change_pct": float((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100),
    }


def get_sector_comparison(
    db: Session,
    sector_ids: List[str],
    metric: str = "returns"
) -> Dict[str, List[float]]:
    """
    Compare multiple sectors on a metric.
    
    Args:
        db: Database session
        sector_ids: List of sector IDs to compare
        metric: Metric to compare ("returns", "volatility", "sentiment")
        
    Returns:
        Dictionary mapping sector_id to list of metric values
    """
    comparison = {}
    
    for sector_id in sector_ids:
        if metric == "returns":
            features = crud.get_latest_sector_features(db, sector_id)
            if features:
                comparison[sector_id] = [
                    features.ret_1d or 0,
                    features.ret_5d or 0,
                    features.ret_1m or 0,
                ]
        elif metric == "sentiment":
            sentiment = crud.get_sector_sentiment_daily(db, sector_id)
            if sentiment:
                comparison[sector_id] = [
                    sentiment.sentiment_score_1d or 0,
                    sentiment.sentiment_score_7d or 0,
                ]
    
    return comparison


def get_flows_analysis(
    db: Session,
    sector_id: Optional[str] = None,
    lookback_days: int = 30
) -> Dict[str, any]:
    """
    Analyze FII/DII flows for sector(s).
    
    Args:
        db: Database session
        sector_id: Specific sector (None for aggregate)
        lookback_days: Number of days to analyze
        
    Returns:
        Dictionary with flows analysis
    """
    to_date = date.today()
    from_date = to_date - timedelta(days=lookback_days)
    
    if sector_id:
        # Get flows for specific sector
        flows = db.query(models.SectorFlowsDaily).filter(
            models.SectorFlowsDaily.sector_id == sector_id,
            models.SectorFlowsDaily.date >= from_date,
            models.SectorFlowsDaily.date <= to_date
        ).order_by(models.SectorFlowsDaily.date).all()
    else:
        # Aggregate across all sectors
        flows = db.query(models.SectorFlowsDaily).filter(
            models.SectorFlowsDaily.date >= from_date,
            models.SectorFlowsDaily.date <= to_date
        ).order_by(models.SectorFlowsDaily.date).all()
    
    if not flows:
        return {}
    
    # Aggregate flows by date
    flows_by_date = {}
    for flow in flows:
        date_key = flow.date.isoformat()
        if date_key not in flows_by_date:
            flows_by_date[date_key] = {"fii": 0, "dii": 0}
        if flow.fii_net_inr:
            flows_by_date[date_key]["fii"] += flow.fii_net_inr
        if flow.dii_net_inr:
            flows_by_date[date_key]["dii"] += flow.dii_net_inr
    
    # Calculate statistics
    fii_values = [v["fii"] for v in flows_by_date.values()]
    dii_values = [v["dii"] for v in flows_by_date.values()]
    
    return {
        "total_fii_net": sum(fii_values),
        "total_dii_net": sum(dii_values),
        "avg_daily_fii": sum(fii_values) / len(fii_values) if fii_values else 0,
        "avg_daily_dii": sum(dii_values) / len(dii_values) if dii_values else 0,
        "flows_by_date": flows_by_date,
    }


def get_options_analysis(
    db: Session,
    underlying: str,
    lookback_days: int = 30
) -> Dict[str, any]:
    """
    Analyze options data for an underlying.
    
    Args:
        db: Database session
        underlying: Underlying symbol (e.g., 'NIFTY', 'BANKNIFTY')
        lookback_days: Number of days to analyze
        
    Returns:
        Dictionary with options analysis
    """
    to_date = date.today()
    from_date = to_date - timedelta(days=lookback_days)
    
    options = db.query(models.OptionsDaily).filter(
        models.OptionsDaily.underlying == underlying,
        models.OptionsDaily.date >= from_date,
        models.OptionsDaily.date <= to_date
    ).order_by(models.OptionsDaily.date).all()
    
    if not options:
        return {}
    
    # Extract metrics
    pcr_values = [o.pcr_oi for o in options if o.pcr_oi is not None]
    oi_changes = [o.oi_change_1d for o in options if o.oi_change_1d is not None]
    iv_values = [o.iv_index for o in options if o.iv_index is not None]
    
    latest = options[-1] if options else None
    
    return {
        "current_pcr": latest.pcr_oi if latest else None,
        "avg_pcr": sum(pcr_values) / len(pcr_values) if pcr_values else None,
        "current_oi_change": latest.oi_change_1d if latest else None,
        "avg_oi_change": sum(oi_changes) / len(oi_changes) if oi_changes else None,
        "current_iv": latest.iv_index if latest else None,
        "avg_iv": sum(iv_values) / len(iv_values) if iv_values else None,
        "options_by_date": [
            {
                "date": o.date.isoformat(),
                "pcr_oi": o.pcr_oi,
                "oi_change_1d": o.oi_change_1d,
                "iv_index": o.iv_index,
            }
            for o in options
        ],
    }


def get_sentiment_analysis(
    db: Session,
    sector_id: str,
    lookback_days: int = 30
) -> Dict[str, any]:
    """
    Analyze sentiment trends for a sector.
    
    Args:
        db: Database session
        sector_id: Sector identifier
        lookback_days: Number of days to analyze
        
    Returns:
        Dictionary with sentiment analysis
    """
    to_date = date.today()
    from_date = to_date - timedelta(days=lookback_days)
    
    sentiment_records = db.query(models.SectorSentimentDaily).filter(
        models.SectorSentimentDaily.sector_id == sector_id,
        models.SectorSentimentDaily.date >= from_date,
        models.SectorSentimentDaily.date <= to_date
    ).order_by(models.SectorSentimentDaily.date).all()
    
    if not sentiment_records:
        return {}
    
    sentiment_1d = [s.sentiment_score_1d for s in sentiment_records if s.sentiment_score_1d is not None]
    sentiment_7d = [s.sentiment_score_7d for s in sentiment_records if s.sentiment_score_7d is not None]
    
    latest = sentiment_records[-1] if sentiment_records else None
    
    return {
        "current_sentiment_1d": latest.sentiment_score_1d if latest else None,
        "current_sentiment_7d": latest.sentiment_score_7d if latest else None,
        "avg_sentiment_1d": sum(sentiment_1d) / len(sentiment_1d) if sentiment_1d else None,
        "avg_sentiment_7d": sum(sentiment_7d) / len(sentiment_7d) if sentiment_7d else None,
        "sentiment_trend": "improving" if len(sentiment_1d) >= 2 and sentiment_1d[-1] > sentiment_1d[0] else "declining",
        "sentiment_by_date": [
            {
                "date": s.date.isoformat(),
                "sentiment_1d": s.sentiment_score_1d,
                "sentiment_7d": s.sentiment_score_7d,
                "headline_count": s.headline_count,
            }
            for s in sentiment_records
        ],
    }

