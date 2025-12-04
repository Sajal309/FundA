"""CRUD operations for database models."""
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import date, datetime
from app.db import models, schemas


def create_sector_time_series(db: Session, time_series: schemas.SectorTimeSeriesCreate) -> models.SectorTimeSeries:
    """Create a new sector time series record."""
    db_ts = models.SectorTimeSeries(**time_series.dict())
    db.add(db_ts)
    db.commit()
    db.refresh(db_ts)
    return db_ts


def get_sector_timeseries(
    db: Session,
    sector_id: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 1000
) -> List[models.SectorTimeSeries]:
    """Get time series data for a sector."""
    query = db.query(models.SectorTimeSeries).filter(
        models.SectorTimeSeries.sector_id == sector_id
    )
    
    if from_date:
        query = query.filter(models.SectorTimeSeries.ts >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        query = query.filter(models.SectorTimeSeries.ts <= datetime.combine(to_date, datetime.max.time()))
    
    return query.order_by(desc(models.SectorTimeSeries.ts)).limit(limit).all()


def get_latest_sector_price(db: Session, sector_id: str) -> Optional[models.SectorTimeSeries]:
    """Get the latest price data for a sector."""
    return db.query(models.SectorTimeSeries).filter(
        models.SectorTimeSeries.sector_id == sector_id
    ).order_by(desc(models.SectorTimeSeries.ts)).first()


def create_or_update_sector_features(
    db: Session,
    features: schemas.SectorFeaturesCreate
) -> models.SectorFeatures:
    """Create or update sector features."""
    existing = db.query(models.SectorFeatures).filter(
        models.SectorFeatures.sector_id == features.sector_id,
        models.SectorFeatures.date == features.date
    ).first()
    
    if existing:
        for key, value in features.dict(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_features = models.SectorFeatures(**features.dict())
        db.add(db_features)
        db.commit()
        db.refresh(db_features)
        return db_features


def get_latest_sector_features(
    db: Session,
    sector_id: str
) -> Optional[models.SectorFeatures]:
    """Get the latest features for a sector."""
    return db.query(models.SectorFeatures).filter(
        models.SectorFeatures.sector_id == sector_id
    ).order_by(desc(models.SectorFeatures.date)).first()


def create_or_update_sector_forecast(
    db: Session,
    forecast: schemas.SectorForecastCreate
) -> models.SectorForecast:
    """Create or update sector forecast."""
    existing = db.query(models.SectorForecast).filter(
        models.SectorForecast.sector_id == forecast.sector_id,
        models.SectorForecast.date == forecast.date
    ).first()
    
    if existing:
        for key, value in forecast.dict(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_forecast = models.SectorForecast(**forecast.dict())
        db.add(db_forecast)
        db.commit()
        db.refresh(db_forecast)
        return db_forecast


def get_latest_sector_forecast(
    db: Session,
    sector_id: str
) -> Optional[models.SectorForecast]:
    """Get the latest forecast for a sector."""
    return db.query(models.SectorForecast).filter(
        models.SectorForecast.sector_id == sector_id
    ).order_by(desc(models.SectorForecast.date)).first()


def get_all_sectors(db: Session) -> List[str]:
    """Get list of all unique sector IDs."""
    return [row[0] for row in db.query(models.SectorTimeSeries.sector_id).distinct().all()]


def get_sector_constituents(
    db: Session,
    sector_id: str,
    limit: int = 5
) -> List[models.SectorConstituent]:
    """Get top constituents for a sector."""
    return db.query(models.SectorConstituent).filter(
        models.SectorConstituent.sector_id == sector_id
    ).order_by(desc(models.SectorConstituent.weight_pct)).limit(limit).all()


def create_sector_constituent(
    db: Session,
    constituent: schemas.SectorConstituentCreate
) -> models.SectorConstituent:
    """Create a sector constituent record."""
    db_const = models.SectorConstituent(**constituent.dict())
    db.add(db_const)
    db.commit()
    db.refresh(db_const)
    return db_const


# FII/DII flows CRUD
def create_fii_dii_daily(
    db: Session,
    flow: schemas.FIIDIIDailyCreate
) -> models.FIIDIIDaily:
    """Create a FII/DII daily flow record."""
    db_flow = models.FIIDIIDaily(**flow.dict())
    db.add(db_flow)
    db.commit()
    db.refresh(db_flow)
    return db_flow


def get_fii_dii_daily(
    db: Session,
    date: Optional[date] = None,
    ticker: Optional[str] = None
) -> List[models.FIIDIIDaily]:
    """Get FII/DII daily flows."""
    query = db.query(models.FIIDIIDaily)
    if date:
        query = query.filter(models.FIIDIIDaily.date == date)
    if ticker:
        query = query.filter(models.FIIDIIDaily.ticker == ticker)
    return query.order_by(desc(models.FIIDIIDaily.date)).all()


def create_or_update_sector_flows_daily(
    db: Session,
    flow: schemas.SectorFlowsDailyCreate
) -> models.SectorFlowsDaily:
    """Create or update sector flows daily."""
    existing = db.query(models.SectorFlowsDaily).filter(
        models.SectorFlowsDaily.sector_id == flow.sector_id,
        models.SectorFlowsDaily.date == flow.date
    ).first()
    
    if existing:
        for key, value in flow.dict(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_flow = models.SectorFlowsDaily(**flow.dict())
        db.add(db_flow)
        db.commit()
        db.refresh(db_flow)
        return db_flow


def get_sector_flows_daily(
    db: Session,
    sector_id: str,
    target_date: Optional[date] = None
) -> Optional[models.SectorFlowsDaily]:
    """Get sector flows for a specific date (or latest)."""
    query = db.query(models.SectorFlowsDaily).filter(
        models.SectorFlowsDaily.sector_id == sector_id
    )
    if target_date:
        query = query.filter(models.SectorFlowsDaily.date == target_date)
    return query.order_by(desc(models.SectorFlowsDaily.date)).first()


# Macro CRUD
def create_or_update_macro_daily(
    db: Session,
    macro: schemas.MacroDailyCreate
) -> models.MacroDaily:
    """Create or update macro daily data."""
    existing = db.query(models.MacroDaily).filter(
        models.MacroDaily.date == macro.date
    ).first()
    
    if existing:
        for key, value in macro.dict(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_macro = models.MacroDaily(**macro.dict())
        db.add(db_macro)
        db.commit()
        db.refresh(db_macro)
        return db_macro


def get_macro_daily(
    db: Session,
    target_date: Optional[date] = None
) -> Optional[models.MacroDaily]:
    """Get macro data for a specific date (or latest)."""
    query = db.query(models.MacroDaily)
    if target_date:
        query = query.filter(models.MacroDaily.date == target_date)
    return query.order_by(desc(models.MacroDaily.date)).first()


# Options CRUD
def create_or_update_options_daily(
    db: Session,
    options: schemas.OptionsDailyCreate
) -> models.OptionsDaily:
    """Create or update options daily data."""
    existing = db.query(models.OptionsDaily).filter(
        models.OptionsDaily.underlying == options.underlying,
        models.OptionsDaily.date == options.date
    ).first()
    
    if existing:
        for key, value in options.dict(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_options = models.OptionsDaily(**options.dict())
        db.add(db_options)
        db.commit()
        db.refresh(db_options)
        return db_options


def get_options_daily(
    db: Session,
    underlying: str,
    target_date: Optional[date] = None
) -> Optional[models.OptionsDaily]:
    """Get options data for a specific underlying and date (or latest)."""
    query = db.query(models.OptionsDaily).filter(
        models.OptionsDaily.underlying == underlying
    )
    if target_date:
        query = query.filter(models.OptionsDaily.date == target_date)
    return query.order_by(desc(models.OptionsDaily.date)).first()


def get_all_option_underlyings(db: Session) -> List[str]:
    """Get list of all unique option underlyings."""
    return [row[0] for row in db.query(models.OptionsDaily.underlying).distinct().all()]


# News and sentiment CRUD
def create_news_headline(
    db: Session,
    headline: schemas.NewsHeadlineCreate
) -> models.NewsHeadline:
    """Create a news headline record."""
    db_headline = models.NewsHeadline(**headline.dict())
    db.add(db_headline)
    db.commit()
    db.refresh(db_headline)
    return db_headline


def get_news_headlines(
    db: Session,
    sector_id: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 100
) -> List[models.NewsHeadline]:
    """Get news headlines, optionally filtered by sector and date range."""
    query = db.query(models.NewsHeadline)
    
    if from_date:
        query = query.filter(models.NewsHeadline.date >= from_date)
    if to_date:
        query = query.filter(models.NewsHeadline.date <= to_date)
    
    # Get all results first, then filter by sector in Python
    # (PostgreSQL JSON filtering can be complex, this is simpler)
    results = query.order_by(desc(models.NewsHeadline.date)).limit(limit * 10 if sector_id else limit).all()
    
    if sector_id:
        # Filter by sector_tags containing the sector_id
        filtered = [
            h for h in results
            if h.sector_tags and sector_id in h.sector_tags
        ]
        return filtered[:limit]
    
    return results[:limit]


def create_or_update_sector_sentiment_daily(
    db: Session,
    sentiment: schemas.SectorSentimentDailyCreate
) -> models.SectorSentimentDaily:
    """Create or update sector sentiment daily."""
    existing = db.query(models.SectorSentimentDaily).filter(
        models.SectorSentimentDaily.sector_id == sentiment.sector_id,
        models.SectorSentimentDaily.date == sentiment.date
    ).first()
    
    if existing:
        for key, value in sentiment.dict(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_sentiment = models.SectorSentimentDaily(**sentiment.dict())
        db.add(db_sentiment)
        db.commit()
        db.refresh(db_sentiment)
        return db_sentiment


def get_sector_sentiment_daily(
    db: Session,
    sector_id: str,
    target_date: Optional[date] = None
) -> Optional[models.SectorSentimentDaily]:
    """Get sector sentiment for a specific date (or latest)."""
    query = db.query(models.SectorSentimentDaily).filter(
        models.SectorSentimentDaily.sector_id == sector_id
    )
    if target_date:
        query = query.filter(models.SectorSentimentDaily.date == target_date)
    return query.order_by(desc(models.SectorSentimentDaily.date)).first()


# Quarter Outlook CRUD functions
def create_or_update_sector_breadth_daily(
    db: Session,
    breadth: schemas.SectorBreadthDailyCreate
) -> models.SectorBreadthDaily:
    """Create or update sector breadth daily."""
    existing = db.query(models.SectorBreadthDaily).filter(
        models.SectorBreadthDaily.sector_id == breadth.sector_id,
        models.SectorBreadthDaily.date == breadth.date
    ).first()
    
    if existing:
        for key, value in breadth.dict(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_breadth = models.SectorBreadthDaily(**breadth.dict())
        db.add(db_breadth)
        db.commit()
        db.refresh(db_breadth)
        return db_breadth


def create_earnings_event(
    db: Session,
    event: schemas.EarningsEventCreate
) -> models.EarningsEvent:
    """Create a new earnings event."""
    db_event = models.EarningsEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def create_or_update_sector_valuations_daily(
    db: Session,
    valuation: schemas.SectorValuationsDailyCreate
) -> models.SectorValuationsDaily:
    """Create or update sector valuations daily."""
    existing = db.query(models.SectorValuationsDaily).filter(
        models.SectorValuationsDaily.sector_id == valuation.sector_id,
        models.SectorValuationsDaily.date == valuation.date
    ).first()
    
    if existing:
        for key, value in valuation.dict(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_valuation = models.SectorValuationsDaily(**valuation.dict())
        db.add(db_valuation)
        db.commit()
        db.refresh(db_valuation)
        return db_valuation


def create_or_update_market_sentiment_daily(
    db: Session,
    sentiment: schemas.MarketSentimentDailyCreate
) -> models.MarketSentimentDaily:
    """Create or update market sentiment daily."""
    existing = db.query(models.MarketSentimentDaily).filter(
        models.MarketSentimentDaily.date == sentiment.date
    ).first()
    
    if existing:
        for key, value in sentiment.dict(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_sentiment = models.MarketSentimentDaily(**sentiment.dict())
        db.add(db_sentiment)
        db.commit()
        db.refresh(db_sentiment)
        return db_sentiment


def get_market_sentiment_daily(
    db: Session,
    target_date: Optional[date] = None
) -> Optional[models.MarketSentimentDaily]:
    """Get market sentiment daily for a specific date (or latest)."""
    query = db.query(models.MarketSentimentDaily)
    if target_date:
        query = query.filter(models.MarketSentimentDaily.date == target_date)
    return query.order_by(desc(models.MarketSentimentDaily.date)).first()

