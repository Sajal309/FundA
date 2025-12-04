"""Quarter Outlook feature computation for sectors."""
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from datetime import date, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.db import crud, models
from app.utils import logger


def load_quarter_weights() -> Dict[str, Any]:
    """Load QuarterScore weights from config file."""
    config_path = Path(__file__).parent.parent.parent / "config" / "quarter_weights.yaml"
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}, using defaults")
        return {
            "momentum_1m": 0.10,
            "momentum_3m": 0.15,
            "breadth": 0.20,
            "flows": 0.20,
            "earnings": 0.15,
            "valuation": 0.10,
            "sentiment": 0.05,
            "macro_overlay": 0.05,
        }


def compute_momentum_features(
    db: Session,
    sector_id: str,
    target_date: date,
    nifty_sector_id: str = "NIFTY_50"
) -> Dict[str, Optional[float]]:
    """
    Compute momentum features: ret_3m, ret_6m, relative returns vs Nifty.
    
    Args:
        db: Database session
        sector_id: Sector identifier
        target_date: Target date for computation
        nifty_sector_id: Nifty index sector ID for comparison
        
    Returns:
        Dictionary with momentum features
    """
    # Get sector time series
    sector_ts = crud.get_sector_timeseries(
        db, sector_id, to_date=target_date, limit=200
    )
    
    if not sector_ts or len(sector_ts) < 63:  # Need at least 3 months (63 trading days)
        return {
            "ret_3m": None,
            "ret_6m": None,
            "rel_1m_vs_nifty": None,
            "rel_3m_vs_nifty": None,
        }
    
    # Convert to DataFrame
    sector_df = pd.DataFrame([{
        'date': ts.ts.date(),
        'close': float(ts.close),
    } for ts in reversed(sector_ts)])
    
    sector_df = sector_df.sort_values('date')
    
    # Calculate returns
    ret_3m = None
    ret_6m = None
    
    if len(sector_df) >= 63:
        ret_3m = float((sector_df['close'].iloc[-1] / sector_df['close'].iloc[-63] - 1) * 100)
    if len(sector_df) >= 126:
        ret_6m = float((sector_df['close'].iloc[-1] / sector_df['close'].iloc[-126] - 1) * 100)
    
    # Get Nifty time series for relative returns
    nifty_ts = crud.get_sector_timeseries(
        db, nifty_sector_id, to_date=target_date, limit=200
    )
    
    rel_1m_vs_nifty = None
    rel_3m_vs_nifty = None
    
    if nifty_ts and len(nifty_ts) >= 63:
        nifty_df = pd.DataFrame([{
            'date': ts.ts.date(),
            'close': float(ts.close),
        } for ts in reversed(nifty_ts)])
        nifty_df = nifty_df.sort_values('date')
        
        # 1-month relative return
        if len(sector_df) >= 21 and len(nifty_df) >= 21:
            sector_1m = float((sector_df['close'].iloc[-1] / sector_df['close'].iloc[-21] - 1) * 100)
            nifty_1m = float((nifty_df['close'].iloc[-1] / nifty_df['close'].iloc[-21] - 1) * 100)
            rel_1m_vs_nifty = sector_1m - nifty_1m
        
        # 3-month relative return
        if len(sector_df) >= 63 and len(nifty_df) >= 63:
            sector_3m = float((sector_df['close'].iloc[-1] / sector_df['close'].iloc[-63] - 1) * 100)
            nifty_3m = float((nifty_df['close'].iloc[-1] / nifty_df['close'].iloc[-63] - 1) * 100)
            rel_3m_vs_nifty = sector_3m - nifty_3m
    
    return {
        "ret_3m": ret_3m,
        "ret_6m": ret_6m,
        "rel_1m_vs_nifty": rel_1m_vs_nifty,
        "rel_3m_vs_nifty": rel_3m_vs_nifty,
    }


def compute_breadth_features(
    db: Session,
    sector_id: str,
    target_date: date
) -> Dict[str, Optional[float]]:
    """
    Compute breadth features: % above 50DMA, % making 3M highs.
    
    Args:
        db: Database session
        sector_id: Sector identifier
        target_date: Target date for computation
        
    Returns:
        Dictionary with breadth features
    """
    # Get breadth data if available
    breadth_data = db.query(models.SectorBreadthDaily).filter(
        and_(
            models.SectorBreadthDaily.sector_id == sector_id,
            models.SectorBreadthDaily.date == target_date
        )
    ).first()
    
    if breadth_data and breadth_data.total_constituents and breadth_data.total_constituents > 0:
        breadth_above_50dma = float(breadth_data.above_50dma) / breadth_data.total_constituents
        breadth_3m_highs = float(breadth_data.making_3m_highs) / breadth_data.total_constituents
    else:
        # Fallback: compute from constituents if we have time series data
        constituents = db.query(models.SectorConstituent).filter(
            models.SectorConstituent.sector_id == sector_id
        ).all()
        
        if not constituents:
            return {
                "breadth_above_50dma": None,
                "breadth_3m_highs": None,
            }
        
        # For each constituent, check if we have price data above 50DMA
        # This is simplified - in production, you'd fetch individual stock prices
        # For now, return None if breadth_daily doesn't exist
        breadth_above_50dma = None
        breadth_3m_highs = None
    
    return {
        "breadth_above_50dma": breadth_above_50dma,
        "breadth_3m_highs": breadth_3m_highs,
    }


def compute_flow_features(
    db: Session,
    sector_id: str,
    target_date: date
) -> Dict[str, Optional[float]]:
    """
    Compute flow features: 20-day rolling FII net, percentile vs 1 year.
    
    Args:
        db: Database session
        sector_id: Sector identifier
        target_date: Target date for computation
        
    Returns:
        Dictionary with flow features
    """
    # Get flows for last 20 days
    from_date = target_date - timedelta(days=20)
    flows = db.query(models.SectorFlowsDaily).filter(
        and_(
            models.SectorFlowsDaily.sector_id == sector_id,
            models.SectorFlowsDaily.date >= from_date,
            models.SectorFlowsDaily.date <= target_date
        )
    ).order_by(models.SectorFlowsDaily.date).all()
    
    if not flows:
        return {
            "fii_net_inr_20d": None,
            "fii_net_inr_percentile": None,
        }
    
    # Sum 20-day FII net
    fii_net_20d = sum(float(flow.fii_net_inr or 0) for flow in flows)
    
    # Get 1-year history for percentile calculation
    year_ago = target_date - timedelta(days=365)
    historical_flows = db.query(models.SectorFlowsDaily).filter(
        and_(
            models.SectorFlowsDaily.sector_id == sector_id,
            models.SectorFlowsDaily.date >= year_ago,
            models.SectorFlowsDaily.date <= target_date
        )
    ).all()
    
    fii_net_inr_percentile = None
    if historical_flows:
        # Calculate rolling 20-day sums for percentile
        historical_20d_sums = []
        for i in range(len(historical_flows) - 19):
            window_flows = historical_flows[i:i+20]
            window_sum = sum(float(flow.fii_net_inr or 0) for flow in window_flows)
            historical_20d_sums.append(window_sum)
        
        if historical_20d_sums:
            # Calculate percentile
            fii_net_inr_percentile = float(
                np.sum(np.array(historical_20d_sums) <= fii_net_20d) / len(historical_20d_sums)
            )
    
    return {
        "fii_net_inr_20d": float(fii_net_20d) if fii_net_20d else None,
        "fii_net_inr_percentile": fii_net_inr_percentile,
    }


def compute_valuation_features(
    db: Session,
    sector_id: str,
    target_date: date
) -> Dict[str, Optional[float]]:
    """
    Compute valuation features: P/E, P/E percentile vs 5-year history.
    
    Args:
        db: Database session
        sector_id: Sector identifier
        target_date: Target date for computation
        
    Returns:
        Dictionary with valuation features
    """
    # Get current valuation
    valuation = db.query(models.SectorValuationsDaily).filter(
        and_(
            models.SectorValuationsDaily.sector_id == sector_id,
            models.SectorValuationsDaily.date == target_date
        )
    ).first()
    
    if not valuation or not valuation.pe:
        return {
            "valuation_pe": None,
            "valuation_pe_percentile": None,
        }
    
    valuation_pe = float(valuation.pe)
    
    # Get 5-year history for percentile
    five_years_ago = target_date - timedelta(days=5*365)
    historical_valuations = db.query(models.SectorValuationsDaily).filter(
        and_(
            models.SectorValuationsDaily.sector_id == sector_id,
            models.SectorValuationsDaily.date >= five_years_ago,
            models.SectorValuationsDaily.date <= target_date,
            models.SectorValuationsDaily.pe.isnot(None)
        )
    ).all()
    
    valuation_pe_percentile = None
    if historical_valuations:
        pe_values = [float(v.pe) for v in historical_valuations if v.pe]
        if pe_values:
            valuation_pe_percentile = float(
                np.sum(np.array(pe_values) <= valuation_pe) / len(pe_values)
            )
    
    return {
        "valuation_pe": valuation_pe,
        "valuation_pe_percentile": valuation_pe_percentile,
    }


def compute_earnings_features(
    db: Session,
    sector_id: str,
    target_date: date
) -> Dict[str, Optional[float]]:
    """
    Compute earnings features: % upgrades/downgrades in last 60 days.
    
    Args:
        db: Database session
        sector_id: Sector identifier
        target_date: Target date for computation
        
    Returns:
        Dictionary with earnings features
    """
    # Get earnings events in last 60 days
    from_date = target_date - timedelta(days=60)
    events = db.query(models.EarningsEvent).filter(
        and_(
            models.EarningsEvent.sector_id == sector_id,
            models.EarningsEvent.date >= from_date,
            models.EarningsEvent.date <= target_date,
            models.EarningsEvent.revision_direction.isnot(None)
        )
    ).all()
    
    if not events:
        return {
            "earnings_upgrades_pct_60d": None,
            "earnings_downgrades_pct_60d": None,
        }
    
    # Count upgrades and downgrades
    upgrades = sum(1 for e in events if e.revision_direction == 'upgrade')
    downgrades = sum(1 for e in events if e.revision_direction == 'downgrade')
    total = len(events)
    
    return {
        "earnings_upgrades_pct_60d": float(upgrades / total) if total > 0 else None,
        "earnings_downgrades_pct_60d": float(downgrades / total) if total > 0 else None,
    }


def compute_macro_overlay(
    db: Session,
    sector_id: str,
    target_date: date,
    config: Dict[str, Any]
) -> float:
    """
    Compute macro overlay adjustment based on sector sensitivity.
    
    Args:
        db: Database session
        sector_id: Sector identifier
        target_date: Target date for computation
        config: QuarterScore config with sector sensitivities
        
    Returns:
        Macro overlay score (-0.3 to +0.3 typically)
    """
    # Get latest macro data
    macro = crud.get_macro_daily(db, target_date)
    if not macro:
        return 0.0
    
    # Get sector sensitivity
    sector_sensitivity = config.get('sector_macro_sensitivity', {}).get(
        sector_id,
        config.get('sector_macro_sensitivity', {}).get('default', {})
    )
    
    overlay = 0.0
    
    # USD/INR impact
    if macro.usd_inr_pct_1d and 'usd_inr' in sector_sensitivity:
        # Normalize to -1 to +1 range (assuming typical moves are -2% to +2%)
        usd_move = float(macro.usd_inr_pct_1d) / 2.0
        usd_move = max(-1.0, min(1.0, usd_move))  # Clamp
        overlay += sector_sensitivity['usd_inr'] * usd_move * 0.1
    
    # Crude impact
    if macro.brent_pct_7d and 'crude' in sector_sensitivity:
        # Normalize to -1 to +1 range (assuming typical moves are -10% to +10%)
        crude_move = float(macro.brent_pct_7d) / 10.0
        crude_move = max(-1.0, min(1.0, crude_move))  # Clamp
        overlay += sector_sensitivity['crude'] * crude_move * 0.1
    
    # Rates impact (using US 10Y as proxy)
    if macro.us_10y_close and 'rates' in sector_sensitivity:
        # Get previous value for change
        prev_macro = db.query(models.MacroDaily).filter(
            models.MacroDaily.date < target_date
        ).order_by(models.MacroDaily.date.desc()).first()
        
        if prev_macro and prev_macro.us_10y_close:
            rate_change = float(macro.us_10y_close) - float(prev_macro.us_10y_close)
            # Normalize (assuming typical moves are -0.5% to +0.5%)
            rate_move = rate_change / 0.5
            rate_move = max(-1.0, min(1.0, rate_move))  # Clamp
            overlay += sector_sensitivity['rates'] * rate_move * 0.1
    
    return overlay


def normalize_feature(value: Optional[float], min_val: float, max_val: float) -> float:
    """Normalize a feature value to -1 to +1 range."""
    if value is None:
        return 0.0
    # Clamp to range
    clamped = max(min_val, min(max_val, value))
    # Normalize to -1 to +1
    if max_val == min_val:
        return 0.0
    normalized = 2 * (clamped - min_val) / (max_val - min_val) - 1
    return float(normalized)


def compute_quarter_score(
    db: Session,
    sector_id: str,
    target_date: date,
    features_dict: Optional[Dict[str, Any]] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute QuarterScore and contribution breakdown.
    
    Args:
        db: Database session
        sector_id: Sector identifier
        target_date: Target date for computation
        features_dict: Optional pre-computed features dict
        
    Returns:
        Tuple of (quarter_score, contributions_dict)
    """
    config = load_quarter_weights()
    weights = config
    
    # Compute or use provided features
    if features_dict is None:
        # Compute all features
        momentum = compute_momentum_features(db, sector_id, target_date)
        breadth = compute_breadth_features(db, sector_id, target_date)
        flows = compute_flow_features(db, sector_id, target_date)
        valuation = compute_valuation_features(db, sector_id, target_date)
        earnings = compute_earnings_features(db, sector_id, target_date)
        
        # Get sentiment (from existing features)
        sector_features = crud.get_latest_sector_features(db, sector_id)
        sentiment_score_7d = sector_features.sentiment_score_7d if sector_features else None
    else:
        momentum = features_dict.get('momentum', {})
        breadth = features_dict.get('breadth', {})
        flows = features_dict.get('flows', {})
        valuation = features_dict.get('valuation', {})
        earnings = features_dict.get('earnings', {})
        sentiment_score_7d = features_dict.get('sentiment_score_7d')
    
    # Compute macro overlay
    macro_overlay = compute_macro_overlay(db, sector_id, target_date, config)
    
    # Normalize and score each component
    contributions = {}
    
    # Momentum component (combine 1M and 3M)
    momentum_1m_norm = normalize_feature(momentum.get('rel_1m_vs_nifty'), -10.0, 10.0)
    momentum_3m_norm = normalize_feature(momentum.get('rel_3m_vs_nifty'), -20.0, 20.0)
    momentum_score = (momentum_1m_norm * weights['momentum_1m'] + 
                     momentum_3m_norm * weights['momentum_3m']) / (weights['momentum_1m'] + weights['momentum_3m'])
    contributions['momentum'] = {
        'score': momentum_score,
        'detail': f"1M: {momentum.get('rel_1m_vs_nifty', 0):.2f}%, 3M: {momentum.get('rel_3m_vs_nifty', 0):.2f}% vs Nifty"
    }
    
    # Breadth component
    breadth_norm = normalize_feature(breadth.get('breadth_above_50dma'), 0.0, 1.0)
    breadth_score = breadth_norm
    contributions['breadth'] = {
        'score': breadth_score,
        'detail': f"{breadth.get('breadth_above_50dma', 0)*100:.0f}% stocks above 50DMA"
    }
    
    # Flows component
    flows_norm = normalize_feature(flows.get('fii_net_inr_percentile'), 0.0, 1.0)
    flows_score = flows_norm * 2 - 1  # Convert 0-1 to -1 to +1
    contributions['flows'] = {
        'score': flows_score,
        'detail': f"FII 20d flows at {flows.get('fii_net_inr_percentile', 0)*100:.0f}th percentile"
    }
    
    # Earnings component
    upgrades_pct = earnings.get('earnings_upgrades_pct_60d', 0) or 0
    downgrades_pct = earnings.get('earnings_downgrades_pct_60d', 0) or 0
    earnings_score = normalize_feature(upgrades_pct - downgrades_pct, -1.0, 1.0)
    contributions['earnings'] = {
        'score': earnings_score,
        'detail': f"{upgrades_pct*100:.0f}% upgrades, {downgrades_pct*100:.0f}% downgrades last 60d"
    }
    
    # Valuation component (inverse: lower P/E percentile = better)
    val_percentile = valuation.get('valuation_pe_percentile', 0.5) or 0.5
    valuation_score = 1 - (val_percentile * 2)  # Convert 0-1 to +1 to -1
    contributions['valuation'] = {
        'score': valuation_score,
        'detail': f"P/E at {val_percentile*100:.0f}th percentile (5Y history)"
    }
    
    # Sentiment component
    sentiment_norm = normalize_feature(sentiment_score_7d, 0.0, 100.0) if sentiment_score_7d else 0.0
    sentiment_score = sentiment_norm * 2 - 1  # Convert 0-100 to -1 to +1
    contributions['sentiment'] = {
        'score': sentiment_score,
        'detail': f"News sentiment score: {sentiment_score_7d or 0:.1f}/100"
    }
    
    # Macro overlay
    contributions['macro'] = {
        'score': macro_overlay,
        'detail': f"Macro adjustment: {macro_overlay:+.2f}"
    }
    
    # Compute final QuarterScore
    quarter_score = (
        momentum_score * (weights['momentum_1m'] + weights['momentum_3m']) +
        breadth_score * weights['breadth'] +
        flows_score * weights['flows'] +
        earnings_score * weights['earnings'] +
        valuation_score * weights['valuation'] +
        sentiment_score * weights['sentiment'] +
        macro_overlay * weights['macro_overlay']
    )
    
    return float(quarter_score), contributions

