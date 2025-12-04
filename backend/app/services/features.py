"""Feature computation service for sector analysis."""
import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db import crud, schemas, models
from app.utils import logger
from app.services import features_quarter


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        prices: Series of closing prices
        period: RSI period (default 14)
        
    Returns:
        RSI value (0-100)
    """
    if len(prices) < period + 1:
        return None
    
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None


def calculate_moving_average(prices: pd.Series, period: int) -> float:
    """
    Calculate simple moving average.
    
    Args:
        prices: Series of closing prices
        period: MA period
        
    Returns:
        Moving average value
    """
    if len(prices) < period:
        return None
    ma = prices.rolling(window=period).mean()
    return float(ma.iloc[-1]) if not pd.isna(ma.iloc[-1]) else None


def calculate_returns(prices: pd.Series, periods: int) -> float:
    """
    Calculate percentage return over N periods.
    
    Args:
        prices: Series of closing prices
        periods: Number of periods to look back
        
    Returns:
        Percentage return
    """
    if len(prices) < periods + 1:
        return None
    
    return float((prices.iloc[-1] / prices.iloc[-(periods + 1)] - 1) * 100)


def calculate_annualized_volatility(prices: pd.Series, window: int = 20) -> Optional[float]:
    """
    Calculate annualized volatility over a rolling window.

    Uses simple daily returns and scales by sqrt(252).

    Args:
        prices: Series of closing prices
        window: Lookback window in trading days

    Returns:
        Annualized volatility in percent, or None if insufficient data
    """
    if len(prices) < window + 1:
        return None

    returns = prices.pct_change().dropna()
    window_returns = returns.iloc[-window:]
    if window_returns.empty:
        return None

    vol = window_returns.std() * np.sqrt(252) * 100.0
    return float(vol) if not np.isnan(vol) else None


def compute_features_for_sector(
    db: Session,
    sector_id: str,
    target_date: Optional[date] = None
) -> Optional[schemas.SectorFeaturesResponse]:
    """
    Compute features for a sector on a given date.
    
    Args:
        db: Database session
        sector_id: Sector identifier
        target_date: Date to compute features for (defaults to latest available)
        
    Returns:
        SectorFeatures schema object
    """
    # Get time series data
    timeseries = crud.get_sector_timeseries(db, sector_id, limit=100)
    
    if not timeseries:
        logger.warning(f"No time series data found for {sector_id}")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'ts': ts.ts,
        'close': float(ts.close),
        'volume': ts.volume
    } for ts in timeseries])
    
    df = df.sort_values('ts')
    df.set_index('ts', inplace=True)
    
    if target_date:
        # Filter to data up to target_date
        df = df[df.index <= pd.Timestamp(target_date)]
    
    if len(df) < 10:
        logger.warning(f"Insufficient data for {sector_id}: need at least 10 days, got {len(df)}")
        return None
    
    # Calculate features
    closes = df['close']
    
    ret_1d = calculate_returns(closes, 1)
    ret_5d = calculate_returns(closes, 5)
    ret_1m = calculate_returns(closes, 21)  # ~1 month (21 trading days)
    ret_3m = calculate_returns(closes, 63) if len(closes) >= 63 else None  # ~3 months
    ret_6m = calculate_returns(closes, 126) if len(closes) >= 126 else None  # ~6 months
    
    ma20 = calculate_moving_average(closes, 20) if len(closes) >= 20 else None
    ma50 = calculate_moving_average(closes, 50) if len(closes) >= 50 else None
    rsi = calculate_rsi(closes, 14)
    
    # Get the date for this feature set
    feature_date = target_date if target_date else df.index[-1].date()
    
    # Get flows data for this sector and date
    sector_flows = crud.get_sector_flows_daily(db, sector_id, feature_date)
    fii_net_inr = sector_flows.fii_net_inr if sector_flows else None
    
    # Get macro data for this date
    macro_data = crud.get_macro_daily(db, feature_date)
    brent_pct_change_7d = None
    if macro_data:
        # Access attribute safely - it might not exist if migration didn't run or data is old
        brent_pct_change_7d = getattr(macro_data, 'brent_pct_change_7d', None)
    
    # Get options data for this sector/date
    # Map sector_id to option underlying (e.g., NIFTY_BANK -> BANKNIFTY, NIFTY_IT -> NIFTY)
    sector_to_underlying = {
        'NIFTY_BANK': 'BANKNIFTY',
        'NIFTY_IT': 'NIFTY',
        'NIFTY_FMCG': 'NIFTY',
        'NIFTY_PHARMA': 'NIFTY',
        'NIFTY_AUTO': 'NIFTY',
        'NIFTY_ENERGY': 'NIFTY',
        'NIFTY_METAL': 'NIFTY',
        'NIFTY_REALTY': 'NIFTY',
        'NIFTY_PSU_BANK': 'BANKNIFTY',
        'NIFTY_PRIVATE_BANK': 'BANKNIFTY',
    }
    underlying = sector_to_underlying.get(sector_id, 'NIFTY')
    options_data = crud.get_options_daily(db, underlying, feature_date)
    
    pcr_oi = options_data.pcr_oi if options_data else None
    oi_change_1d = options_data.oi_change_1d if options_data else None
    oi_change_3d = options_data.oi_change_3d if options_data else None
    iv_index = options_data.iv_index if options_data else None
    
    # Get sentiment data for this sector and date
    sector_sentiment = crud.get_sector_sentiment_daily(db, sector_id, feature_date)
    sentiment_score_1d = sector_sentiment.sentiment_score_1d if sector_sentiment else None
    sentiment_score_7d = sector_sentiment.sentiment_score_7d if sector_sentiment else None
    
    # Compute Quarter Outlook features
    momentum_features = features_quarter.compute_momentum_features(db, sector_id, feature_date)
    breadth_features = features_quarter.compute_breadth_features(db, sector_id, feature_date)
    flow_features = features_quarter.compute_flow_features(db, sector_id, feature_date)
    valuation_features = features_quarter.compute_valuation_features(db, sector_id, feature_date)
    earnings_features = features_quarter.compute_earnings_features(db, sector_id, feature_date)
    
    # Compute QuarterScore
    quarter_score, contributions = features_quarter.compute_quarter_score(
        db, sector_id, feature_date,
        features_dict={
            'momentum': momentum_features,
            'breadth': breadth_features,
            'flows': flow_features,
            'valuation': valuation_features,
            'earnings': earnings_features,
            'sentiment_score_7d': sentiment_score_7d,
        }
    )
    
    # Create features object
    features = schemas.SectorFeaturesCreate(
        sector_id=sector_id,
        date=feature_date,
        ret_1d=ret_1d,
        ret_5d=ret_5d,
        ret_1m=ret_1m,
        ret_3m=ret_3m,
        ret_6m=ret_6m,
        ma20=ma20,
        ma50=ma50,
        rsi=rsi,
        fii_net_inr=fii_net_inr,
        brent_pct_change_7d=brent_pct_change_7d,
        pcr_oi=pcr_oi,
        oi_change_1d=oi_change_1d,
        oi_change_3d=oi_change_3d,
        iv_index=iv_index,
        sentiment_score_1d=sentiment_score_1d,
        sentiment_score_7d=sentiment_score_7d,
        # Quarter Outlook features
        rel_1m_vs_nifty=momentum_features.get('rel_1m_vs_nifty'),
        rel_3m_vs_nifty=momentum_features.get('rel_3m_vs_nifty'),
        breadth_above_50dma=breadth_features.get('breadth_above_50dma'),
        breadth_3m_highs=breadth_features.get('breadth_3m_highs'),
        fii_net_inr_20d=flow_features.get('fii_net_inr_20d'),
        fii_net_inr_percentile=flow_features.get('fii_net_inr_percentile'),
        valuation_pe=valuation_features.get('valuation_pe'),
        valuation_pe_percentile=valuation_features.get('valuation_pe_percentile'),
        earnings_upgrades_pct_60d=earnings_features.get('earnings_upgrades_pct_60d'),
        earnings_downgrades_pct_60d=earnings_features.get('earnings_downgrades_pct_60d'),
        quarter_score=quarter_score,
    )
    
    # Save to database
    db_features = crud.create_or_update_sector_features(db, features)
    logger.info(f"Computed features for {sector_id} on {feature_date}")
    
    return schemas.SectorFeaturesResponse.model_validate(db_features)


def build_feature_vector(
    db: Session,
    sector_id: str,
    target_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Build a composite, model-ready feature vector for a sector on a given date.

    This is a convenience wrapper that:
    - Pulls the latest stored SectorFeatures row
    - Computes additional derived features (e.g., 20d volatility)
    - Adds placeholders for flows, options, macro, and sentiment features
      so the interface is stable as more data sources are wired in.
    """
    # Latest stored feature row (already includes basic technicals)
    base_features = crud.get_latest_sector_features(db, sector_id)
    if not base_features:
        logger.warning(f"No stored features found for {sector_id} when building feature vector")
        return {}

    # Time-series-derived features (e.g., volatility)
    ts = crud.get_sector_timeseries(db, sector_id, limit=100)
    closes = pd.Series([float(row.close) for row in ts]) if ts else pd.Series(dtype=float)
    vol_20d = calculate_annualized_volatility(closes, window=20) if not closes.empty else None

    # Flow-based features (placeholders until flows ETL is wired)
    fii_net = getattr(base_features, "fii_net_inr", None)
    dii_net = None  # will come from sector_flows_daily in later milestones
    denom = (abs(fii_net or 0) + abs(dii_net or 0) + 1)
    flow_ratio = float((fii_net or 0) / denom)

    # Macro / sentiment placeholders (to be populated when ETL is implemented)
    brent_pct_7d = getattr(base_features, "brent_pct_change_7d", None)
    sentiment_score_1d = None
    sentiment_score_7d = None

    feature_vector: Dict[str, Any] = {
        "sector_id": sector_id,
        "date": base_features.date,
        # existing technicals
        "ret_1d": base_features.ret_1d,
        "ret_5d": base_features.ret_5d,
        "ret_1m": base_features.ret_1m,
        "ma20": base_features.ma20,
        "ma50": base_features.ma50,
        "rsi": base_features.rsi,
        # new technicals
        "volatility_20d": vol_20d,
        # flows
        "fii_net_inr": fii_net,
        "dii_net_inr": dii_net,
        "flow_ratio": flow_ratio,
        # macro
        "brent_pct_change_7d": brent_pct_7d,
        # sentiment
        "sentiment_score_1d": sentiment_score_1d,
        "sentiment_score_7d": sentiment_score_7d,
    }

    return feature_vector


def compute_features_for_all_sectors(
    db: Session,
    target_date: Optional[date] = None
) -> int:
    """
    Compute features for all sectors.
    
    Args:
        db: Database session
        target_date: Date to compute features for
        
    Returns:
        Number of sectors processed
    """
    sectors = crud.get_all_sectors(db)
    count = 0
    
    for sector_id in sectors:
        try:
            compute_features_for_sector(db, sector_id, target_date)
            count += 1
        except Exception as e:
            logger.error(f"Failed to compute features for {sector_id}: {e}")
            continue
    
    logger.info(f"Computed features for {count} sectors")
    return count

