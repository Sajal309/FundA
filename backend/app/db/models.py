"""Database models for SectorView."""
from sqlalchemy import Column, String, Date, DateTime, Numeric, Float, BigInteger, Integer, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class SectorTimeSeries(Base):
    """EOD daily time series data for sectors."""
    __tablename__ = "sector_time_series"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sector_id = Column(String, nullable=False, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    open = Column(Numeric(15, 2), nullable=False)
    high = Column(Numeric(15, 2), nullable=False)
    low = Column(Numeric(15, 2), nullable=False)
    close = Column(Numeric(15, 2), nullable=False)
    volume = Column(BigInteger, nullable=False)
    
    __table_args__ = ()


class SectorFeatures(Base):
    """Computed daily features for sectors."""
    __tablename__ = "sector_features"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sector_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    ret_1d = Column(Float, nullable=True)
    ret_5d = Column(Float, nullable=True)
    ret_1m = Column(Float, nullable=True)
    ma20 = Column(Float, nullable=True)
    ma50 = Column(Float, nullable=True)
    rsi = Column(Float, nullable=True)
    fii_net_inr = Column(BigInteger, nullable=True)
    brent_pct_change_7d = Column(Float, nullable=True)
    # Options-based features
    pcr_oi = Column(Float, nullable=True)  # Put-Call Ratio by OI
    oi_change_1d = Column(Float, nullable=True)  # % change in OI vs 1 day ago
    oi_change_3d = Column(Float, nullable=True)  # % change in OI vs 3 days ago
    iv_index = Column(Float, nullable=True)  # Implied volatility index
    # Sentiment features
    sentiment_score_1d = Column(Float, nullable=True)  # 1-day sentiment score
    sentiment_score_7d = Column(Float, nullable=True)  # 7-day rolling sentiment score
    
    __table_args__ = (
        UniqueConstraint("sector_id", "date", name="uq_sector_features"),
    )


class SectorForecast(Base):
    """3-month forecast results for sectors."""
    __tablename__ = "sector_forecasts"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sector_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    forecast_3m_label = Column(String, nullable=False)  # UP/NEUTRAL/DOWN
    prob_up = Column(Float, nullable=False)
    prob_neutral = Column(Float, nullable=False)
    prob_down = Column(Float, nullable=False)
    expected_return_pct = Column(Float, nullable=False)
    top_drivers = Column(JSON, nullable=True)
    
    __table_args__ = (
        UniqueConstraint("sector_id", "date", name="uq_sector_forecasts"),
    )


class SectorConstituent(Base):
    """Static snapshot of sector constituents."""
    __tablename__ = "sector_constituents"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sector_id = Column(String, nullable=False, index=True)
    ticker = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    weight_pct = Column(Float, nullable=False)
    
    __table_args__ = ()


class FIIDIIDaily(Base):
    """Raw FII/DII flow data by ticker."""
    __tablename__ = "fii_dii_daily"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    source = Column(String, nullable=False)  # 'NSE', 'NSDL', etc.
    ticker = Column(String, nullable=True, index=True)  # None for aggregate
    fii_buy = Column(BigInteger, nullable=True)
    fii_sell = Column(BigInteger, nullable=True)
    dii_buy = Column(BigInteger, nullable=True)
    dii_sell = Column(BigInteger, nullable=True)
    
    __table_args__ = ()


class SectorFlowsDaily(Base):
    """Aggregated FII/DII flows by sector."""
    __tablename__ = "sector_flows_daily"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    sector_id = Column(String, nullable=False, index=True)
    fii_net_inr = Column(BigInteger, nullable=True)
    dii_net_inr = Column(BigInteger, nullable=True)
    fii_gross = Column(BigInteger, nullable=True)  # fii_buy + fii_sell
    dii_gross = Column(BigInteger, nullable=True)  # dii_buy + dii_sell
    
    __table_args__ = (
        UniqueConstraint("sector_id", "date", name="uq_sector_flows"),
    )


class MacroDaily(Base):
    """Daily macro economic indicators."""
    __tablename__ = "macro_daily"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    usd_inr_close = Column(Numeric(10, 4), nullable=True)
    usd_inr_pct_1d = Column(Float, nullable=True)
    brent_close = Column(Numeric(10, 2), nullable=True)
    brent_pct_7d = Column(Float, nullable=True)
    gold_close = Column(Numeric(10, 2), nullable=True)  # INR per 10g
    us_10y_close = Column(Numeric(6, 4), nullable=True)  # US 10Y yield %
    
    __table_args__ = ()


class OptionsDaily(Base):
    """Daily options chain data aggregated by underlying."""
    __tablename__ = "options_daily"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    underlying = Column(String, nullable=False, index=True)  # e.g., 'NIFTY', 'BANKNIFTY', 'NIFTY_BANK'
    expiry = Column(Date, nullable=True)  # Nearest expiry date used for aggregation
    total_call_oi = Column(BigInteger, nullable=True)  # Total call open interest
    total_put_oi = Column(BigInteger, nullable=True)  # Total put open interest
    pcr_oi = Column(Float, nullable=True)  # Put-Call Ratio by OI (put_oi / call_oi)
    pcr_volume = Column(Float, nullable=True)  # Put-Call Ratio by volume
    total_call_volume = Column(BigInteger, nullable=True)
    total_put_volume = Column(BigInteger, nullable=True)
    oi_change_1d = Column(Float, nullable=True)  # % change in total OI vs previous day
    oi_change_3d = Column(Float, nullable=True)  # % change in total OI vs 3 days ago
    iv_index = Column(Float, nullable=True)  # Implied volatility index (if available)
    
    __table_args__ = (
        UniqueConstraint("underlying", "date", name="uq_options_daily"),
    )


class NewsHeadline(Base):
    """News headlines with sentiment scores."""
    __tablename__ = "news_headlines"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    headline = Column(String, nullable=False)
    source = Column(String, nullable=False)  # e.g., 'Economic Times', 'Business Standard'
    url = Column(String, nullable=True)
    text = Column(String, nullable=True)  # Full article text if available
    sector_tags = Column(JSON, nullable=True)  # List of sector IDs this news relates to
    sentiment_score = Column(Float, nullable=True)  # -1 (negative) to +1 (positive)
    sentiment_label = Column(String, nullable=True)  # 'positive', 'negative', 'neutral'
    
    __table_args__ = ()


class SectorSentimentDaily(Base):
    """Aggregated daily sentiment by sector."""
    __tablename__ = "sector_sentiment_daily"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    sector_id = Column(String, nullable=False, index=True)
    sentiment_score_1d = Column(Float, nullable=True)  # Average sentiment for the day
    sentiment_score_7d = Column(Float, nullable=True)  # 7-day rolling average
    headline_count = Column(Integer, nullable=True)  # Number of headlines for this sector/date
    
    __table_args__ = (
        UniqueConstraint("sector_id", "date", name="uq_sector_sentiment"),
    )

