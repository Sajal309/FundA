"""Analytics and data analysis functions."""
import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db import crud, models
from app.utils import logger
from app.utils.formatting import round_to_2_decimal, round_to_int, safe_divide


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
        "trend_strength": round_to_2_decimal(abs(recent_returns) * 100) or 0.0,
        "volatility_regime": vol_regime,
        "current_volatility": round_to_2_decimal(current_vol) if not pd.isna(current_vol) else None,
        "avg_volatility": round_to_2_decimal(avg_vol) if not pd.isna(avg_vol) else None,
        "price_change_pct": round_to_2_decimal((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100) or 0.0,
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
    
    # If no sector flows, try to get from FIIDIIDaily
    if not flows:
        from sqlalchemy import and_
        fii_dii_records = db.query(models.FIIDIIDaily).filter(
            and_(
                models.FIIDIIDaily.date >= from_date,
                models.FIIDIIDaily.date <= to_date
            )
        ).order_by(models.FIIDIIDaily.date).all()
        
        if fii_dii_records:
            # Aggregate by date
            flows_by_date = {}
            for record in fii_dii_records:
                date_key = record.date.isoformat()
                if date_key not in flows_by_date:
                    flows_by_date[date_key] = {"fii": 0, "dii": 0}
                
                # Compute net from buy/sell
                fii_net = float(record.fii_buy or 0) - float(record.fii_sell or 0)
                dii_net = float(record.dii_buy or 0) - float(record.dii_sell or 0)
                
                flows_by_date[date_key]["fii"] += fii_net
                flows_by_date[date_key]["dii"] += dii_net
            
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
        
        # Return empty structure with zeros
        return {
            "total_fii_net": 0,
            "total_dii_net": 0,
            "avg_daily_fii": 0,
            "avg_daily_dii": 0,
            "flows_by_date": {},
        }
    
    # Aggregate flows by date
    flows_by_date = {}
    for flow in flows:
        date_key = flow.date.isoformat()
        if date_key not in flows_by_date:
            flows_by_date[date_key] = {"fii": 0, "dii": 0}
        if flow.fii_net_inr:
            flows_by_date[date_key]["fii"] += float(flow.fii_net_inr)
        if flow.dii_net_inr:
            flows_by_date[date_key]["dii"] += float(flow.dii_net_inr)
    
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


def calculate_performance_metrics(
    db: Session,
    sector_id: str,
    lookback_days: int = 252
) -> Dict[str, any]:
    """
    Calculate performance metrics for a sector (Sharpe ratio, max drawdown, win rate, etc.).
    
    Args:
        db: Database session
        sector_id: Sector identifier
        lookback_days: Number of days to analyze (default 252 = 1 year)
        
    Returns:
        Dictionary with performance metrics
    """
    to_date = date.today()
    from_date = to_date - timedelta(days=lookback_days)
    
    timeseries = crud.get_sector_timeseries(
        db, sector_id, from_date=from_date, to_date=to_date, limit=1000
    )
    
    if len(timeseries) < 20:
        return {}
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'date': ts.ts.date(),
        'close': float(ts.close),
    } for ts in reversed(timeseries)])
    
    df['returns'] = df['close'].pct_change()
    df = df.dropna()
    
    if len(df) < 10:
        return {}
    
    returns_series = df['returns']
    
    # Annualized return (improved precision)
    total_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1)
    trading_days = len(df)
    annualized_return = (1 + total_return) ** (252.0 / trading_days) - 1 if trading_days > 0 else 0.0
    
    # Volatility (annualized) - use sample standard deviation for better accuracy
    volatility = returns_series.std(ddof=1) * np.sqrt(252.0) if len(returns_series) > 1 else 0.0
    
    # Sharpe ratio (assuming risk-free rate = 0.05 = 5%)
    risk_free_rate = 0.05
    sharpe_ratio = safe_divide(annualized_return - risk_free_rate, volatility, default=0.0)
    
    # Max drawdown (improved calculation)
    cumulative = (1 + returns_series).cumprod()
    running_max = cumulative.expanding().max()
    # Calculate drawdown as a Series
    drawdown_series = (cumulative - running_max) / running_max
    max_drawdown = round_to_2_decimal(drawdown_series.min()) or 0.0 if len(drawdown_series) > 0 else 0.0
    
    # Win rate
    positive_days = (returns_series > 0).sum()
    win_rate = safe_divide(positive_days, len(returns_series), default=0.0)
    
    # Average win vs average loss
    wins = returns_series[returns_series > 0]
    losses = returns_series[returns_series < 0]
    avg_win = wins.mean() if len(wins) > 0 else 0.0
    avg_loss = losses.mean() if len(losses) > 0 else 0.0
    profit_factor = abs(safe_divide(avg_win, avg_loss, default=0.0))
    
    # RSI calculation (improved precision)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    # Avoid division by zero - replace zeros in loss with NaN, then fill
    rs = gain / loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None
    
    return {
        "annualized_return": round_to_2_decimal(annualized_return) or 0.0,
        "volatility": round_to_2_decimal(volatility) or 0.0,
        "sharpe_ratio": round_to_2_decimal(sharpe_ratio) or 0.0,
        "max_drawdown": round_to_2_decimal(max_drawdown) or 0.0,
        "win_rate": round_to_2_decimal(win_rate) or 0.0,
        "profit_factor": round_to_2_decimal(profit_factor) or 0.0,
        "current_rsi": round_to_2_decimal(current_rsi),
        "total_return": round_to_2_decimal(total_return) or 0.0,
        "avg_daily_return": round_to_2_decimal(returns_series.mean()) or 0.0,
    }


def calculate_sector_strength_ranking(
    db: Session,
    lookback_days: int = 30
) -> List[Dict[str, any]]:
    """
    Rank sectors by relative strength (momentum + returns).
    
    Args:
        db: Database session
        lookback_days: Number of days to analyze
        
    Returns:
        List of sectors ranked by strength
    """
    to_date = date.today()
    from_date = to_date - timedelta(days=lookback_days)
    
    sector_ids = crud.get_all_sectors(db)
    rankings = []
    
    for sector_id in sector_ids:
        timeseries = crud.get_sector_timeseries(
            db, sector_id, from_date=from_date, to_date=to_date, limit=1000
        )
        
        if len(timeseries) < 5:
            continue
        
        df = pd.DataFrame([{
            'close': float(ts.close),
        } for ts in reversed(timeseries)])
        
        # Calculate metrics
        total_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) * 100
        
        # Momentum score (recent performance)
        recent_returns = returns.tail(5).mean() * 100 if len(returns) >= 5 else 0
        
        # Strength score (combination of return and momentum, penalize volatility)
        strength_score = total_return * 0.6 + recent_returns * 0.4 - volatility * 0.1
        
        rankings.append({
            "sector_id": sector_id,
            "total_return": float(total_return),
            "momentum": float(recent_returns),
            "volatility": float(volatility),
            "strength_score": float(strength_score),
        })
    
    # Sort by strength score
    rankings.sort(key=lambda x: x["strength_score"], reverse=True)
    
    return rankings


def calculate_beta_and_correlation_to_market(
    db: Session,
    sector_id: str,
    market_sector_id: str = "NIFTY_50",
    lookback_days: int = 252
) -> Dict[str, any]:
    """
    Calculate beta and correlation to market (NIFTY 50).
    
    Args:
        db: Database session
        sector_id: Sector identifier
        market_sector_id: Market index (default NIFTY_50)
        lookback_days: Number of days to analyze
        
    Returns:
        Dictionary with beta and correlation metrics
    """
    to_date = date.today()
    from_date = to_date - timedelta(days=lookback_days)
    
    # Get sector returns
    sector_ts = crud.get_sector_timeseries(
        db, sector_id, from_date=from_date, to_date=to_date, limit=1000
    )
    market_ts = crud.get_sector_timeseries(
        db, market_sector_id, from_date=from_date, to_date=to_date, limit=1000
    )
    
    if len(sector_ts) < 20 or len(market_ts) < 20:
        return {}
    
    # Convert to DataFrames
    sector_df = pd.DataFrame([{
        'date': ts.ts.date(),
        'close': float(ts.close),
    } for ts in reversed(sector_ts)])
    
    market_df = pd.DataFrame([{
        'date': ts.ts.date(),
        'close': float(ts.close),
    } for ts in reversed(market_ts)])
    
    # Calculate returns
    sector_df['returns'] = sector_df['close'].pct_change()
    market_df['returns'] = market_df['close'].pct_change()
    
    # Merge on date
    merged = pd.merge(sector_df[['date', 'returns']], market_df[['date', 'returns']], 
                     on='date', suffixes=('_sector', '_market'))
    merged = merged.dropna()
    
    if len(merged) < 20:
        return {}
    
    sector_returns = merged['returns_sector'].values
    market_returns = merged['returns_market'].values
    
    # Calculate correlation
    correlation = np.corrcoef(sector_returns, market_returns)[0, 1]
    
    # Calculate beta (covariance / market variance)
    covariance = np.cov(sector_returns, market_returns)[0, 1]
    market_variance = np.var(market_returns)
    beta = covariance / market_variance if market_variance > 0 else 0
    
    # Alpha (excess return adjusted for beta)
    sector_mean = sector_returns.mean() * 252  # Annualized
    market_mean = market_returns.mean() * 252
    alpha = sector_mean - (beta * market_mean)
    
    return {
        "beta": round_to_2_decimal(beta) or 0.0,
        "correlation_to_market": round_to_2_decimal(correlation) or 0.0,
        "alpha": round_to_2_decimal(alpha) or 0.0,
        "market_return": round_to_2_decimal(market_mean) or 0.0,
        "sector_return": round_to_2_decimal(sector_mean) or 0.0,
    }


def get_macro_indicators_summary(
    db: Session,
    lookback_days: int = 30
) -> Dict[str, any]:
    """
    Get summary of macro indicators.
    
    Args:
        db: Database session
        lookback_days: Number of days to analyze
        
    Returns:
        Dictionary with macro indicators summary
    """
    to_date = date.today()
    from_date = to_date - timedelta(days=lookback_days)
    
    macro_data = db.query(models.MacroDaily).filter(
        models.MacroDaily.date >= from_date,
        models.MacroDaily.date <= to_date
    ).order_by(models.MacroDaily.date.desc()).limit(lookback_days).all()
    
    if not macro_data:
        return {}
    
    # Get latest values
    latest = macro_data[0] if macro_data else None
    
    # Calculate changes
    usdinr_change = None
    brent_change = None
    gold_change = None
    us10y_change = None
    
    if len(macro_data) >= 2:
        prev = macro_data[-1]
        if latest.usd_inr_close and prev.usd_inr_close:
            usdinr_change = ((float(latest.usd_inr_close) - float(prev.usd_inr_close)) / float(prev.usd_inr_close)) * 100
        if latest.brent_close and prev.brent_close:
            brent_change = ((float(latest.brent_close) - float(prev.brent_close)) / float(prev.brent_close)) * 100
        if latest.gold_close and prev.gold_close:
            gold_change = ((float(latest.gold_close) - float(prev.gold_close)) / float(prev.gold_close)) * 100
        if latest.us_10y_close and prev.us_10y_close:
            us10y_change = float(latest.us_10y_close) - float(prev.us_10y_close)
    
    return {
        "usd_inr": round_to_2_decimal(latest.usd_inr_close) if latest and latest.usd_inr_close else None,
        "usd_inr_change_pct": round_to_2_decimal(usdinr_change) if usdinr_change is not None else None,
        "brent_crude": round_to_2_decimal(latest.brent_close) if latest and latest.brent_close else None,
        "brent_change_pct": round_to_2_decimal(brent_change) if brent_change is not None else None,
        "gold_price": round_to_2_decimal(latest.gold_close) if latest and latest.gold_close else None,
        "gold_change_pct": round_to_2_decimal(gold_change) if gold_change is not None else None,
        "us_10y_yield": round_to_2_decimal(latest.us_10y_close) if latest and latest.us_10y_close else None,
        "us_10y_change": round_to_2_decimal(us10y_change) if us10y_change is not None else None,
        "date": latest.date.isoformat() if latest else None,
    }


def get_latest_news_headlines(
    db: Session,
    sector_id: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, any]]:
    """
    Get latest news headlines.
    
    Args:
        db: Database session
        sector_id: Optional sector filter
        limit: Number of headlines to return
        
    Returns:
        List of news headlines
    """
    query = db.query(models.NewsHeadline).order_by(models.NewsHeadline.date.desc())
    
    if sector_id:
        # Filter by sector tags (JSONB contains)
        # Use Python-side filtering since JSONB LIKE doesn't work well
        all_headlines = query.limit(limit * 3).all()  # Get more to filter
        headlines = [
            h for h in all_headlines
            if h.sector_tags and sector_id in h.sector_tags
        ][:limit]
    else:
        headlines = query.limit(limit).all()
    
    return [
        {
            "headline": h.headline,
            "source": h.source,
            "published_at": h.date.isoformat() if h.date else None,
            "sentiment_score": float(h.sentiment_score) if h.sentiment_score is not None else None,
            "sector_tags": h.sector_tags if h.sector_tags else [],
            "url": h.url,
        }
        for h in headlines
    ]

