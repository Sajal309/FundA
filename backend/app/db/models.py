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
    # Quarter Outlook features
    ret_3m = Column(Float, nullable=True)  # 3-month return
    ret_6m = Column(Float, nullable=True)  # 6-month return
    rel_1m_vs_nifty = Column(Float, nullable=True)  # Sector 1M return - Nifty 1M return
    rel_3m_vs_nifty = Column(Float, nullable=True)  # Sector 3M return - Nifty 3M return
    breadth_above_50dma = Column(Float, nullable=True)  # Proportion of constituents above 50DMA (0-1)
    breadth_3m_highs = Column(Float, nullable=True)  # % making 3-month highs (0-1)
    fii_net_inr_20d = Column(Numeric(15, 2), nullable=True)  # Rolling 20-day FII net into sector
    fii_net_inr_percentile = Column(Float, nullable=True)  # Percentile vs last 1 year (0-1)
    valuation_pe = Column(Float, nullable=True)  # Current sector P/E
    valuation_pe_percentile = Column(Float, nullable=True)  # P/E percentile vs 5-year history (0-1)
    earnings_upgrades_pct_60d = Column(Float, nullable=True)  # % of stocks with EPS upgrades last 60 days (0-1)
    earnings_downgrades_pct_60d = Column(Float, nullable=True)  # % of stocks with EPS downgrades last 60 days (0-1)
    quarter_score = Column(Float, nullable=True)  # Final composite QuarterScore metric
    
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
    quarter_score = Column(Float, nullable=True)  # QuarterScore metric
    drivers = Column(JSON, nullable=True)  # QuarterScore contributions by pillar
    
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


class SectorBreadthDaily(Base):
    """Daily breadth metrics for sectors."""
    __tablename__ = "sector_breadth_daily"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    sector_id = Column(String, nullable=False, index=True)
    total_constituents = Column(Integer, nullable=True)
    above_50dma = Column(Integer, nullable=True)
    above_200dma = Column(Integer, nullable=True)
    making_3m_highs = Column(Integer, nullable=True)
    making_3m_lows = Column(Integer, nullable=True)
    
    __table_args__ = (
        UniqueConstraint("sector_id", "date", name="uq_sector_breadth"),
    )


class EarningsEvent(Base):
    """Earnings events and revisions."""
    __tablename__ = "earnings_events"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)  # Result date
    ticker = Column(String, nullable=False, index=True)
    sector_id = Column(String, nullable=True, index=True)
    eps_actual = Column(Numeric(10, 2), nullable=True)
    eps_estimate = Column(Numeric(10, 2), nullable=True)
    surprise_pct = Column(Float, nullable=True)  # (actual - estimate) / estimate
    revision_direction = Column(String, nullable=True)  # 'upgrade', 'downgrade', 'none'
    source = Column(String, nullable=True)  # Data source
    
    __table_args__ = ()


class SectorValuationsDaily(Base):
    """Daily sector valuation metrics."""
    __tablename__ = "sector_valuations_daily"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    sector_id = Column(String, nullable=False, index=True)
    pe = Column(Numeric(10, 2), nullable=True)  # Price-to-Earnings ratio
    pb = Column(Numeric(10, 2), nullable=True)  # Price-to-Book ratio
    div_yield = Column(Numeric(6, 4), nullable=True)  # Dividend yield %
    
    __table_args__ = (
        UniqueConstraint("sector_id", "date", name="uq_sector_valuations"),
    )


class MarketSentimentDaily(Base):
    """Daily market-wide sentiment indicators."""
    __tablename__ = "market_sentiment_daily"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    india_vix = Column(Numeric(6, 2), nullable=True)  # India VIX level
    india_vix_percentile = Column(Float, nullable=True)  # VIX percentile vs history (0-1)
    index_pcr = Column(Float, nullable=True)  # Index Put-Call Ratio
    breadth_nifty500_above_50dma = Column(Float, nullable=True)  # % of Nifty 500 above 50DMA (0-1)
    news_sentiment_score_7d = Column(Float, nullable=True)  # Overall market news sentiment (0-100)
    regime_label = Column(String, nullable=True)  # 'RISK-ON', 'NEUTRAL', 'RISK-OFF'
    
    __table_args__ = ()


# Sector Rotation Models

class Industry(Base):
    """Industry master data."""
    __tablename__ = "industries"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    industry_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    __table_args__ = ()


class Stock(Base):
    """Stock/Instrument master data."""
    __tablename__ = "stocks"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False, unique=True, index=True)
    company_name = Column(String, nullable=False)
    sector_id = Column(String, nullable=True, index=True)
    industry_id = Column(String, nullable=True, index=True)
    isin = Column(String, nullable=True)
    exchange = Column(String, nullable=True)  # 'NSE', 'BSE'
    shares_outstanding = Column(BigInteger, nullable=True)  # For market cap calculation
    
    __table_args__ = ()


class StockTimeSeries(Base):
    """EOD daily time series data for individual stocks."""
    __tablename__ = "stock_time_series"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Numeric(15, 2), nullable=False)
    high = Column(Numeric(15, 2), nullable=False)
    low = Column(Numeric(15, 2), nullable=False)
    close = Column(Numeric(15, 2), nullable=False)
    volume = Column(BigInteger, nullable=False)
    deliverable_volume = Column(BigInteger, nullable=True)
    turnover = Column(Numeric(20, 2), nullable=True)  # Traded value
    
    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_stock_time_series"),
    )


class StockMarketCap(Base):
    """Daily market cap for stocks."""
    __tablename__ = "stock_market_caps"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    market_cap = Column(Numeric(20, 2), nullable=False)  # In INR
    
    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_stock_market_caps"),
    )


class StockTechnicalIndicators(Base):
    """Technical indicators for individual stocks."""
    __tablename__ = "stock_technical_indicators"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    sma20 = Column(Numeric(15, 2), nullable=True)
    sma50 = Column(Numeric(15, 2), nullable=True)
    sma100 = Column(Numeric(15, 2), nullable=True)
    rsi14 = Column(Numeric(6, 2), nullable=True)
    rs55 = Column(Float, nullable=True)  # 55-day relative strength vs benchmark
    return_1m = Column(Float, nullable=True)  # 1-month return
    return_3m = Column(Float, nullable=True)  # 3-month return
    return_6m = Column(Float, nullable=True)  # 6-month return
    vwap = Column(Numeric(15, 2), nullable=True)  # Volume-weighted average price
    
    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_stock_technical_indicators"),
    )


class StockRollingStats(Base):
    """Rolling statistics for stocks (for delivery calculations)."""
    __tablename__ = "stock_rolling_stats"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    avg_traded_value_20d = Column(Numeric(20, 2), nullable=True)  # 20-day average traded value
    avg_delivery_value_20d = Column(Numeric(20, 2), nullable=True)  # 20-day average delivery value
    
    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_stock_rolling_stats"),
    )


# Sector Rotation Aggregation Tables

class SectorBreadthSnapshot(Base):
    """Precomputed breadth snapshots for sectors."""
    __tablename__ = "sector_breadth_snapshots"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    sector_id = Column(String, nullable=False, index=True)
    total_mcap = Column(Numeric(20, 2), nullable=False)
    total_stocks = Column(Integer, nullable=False)
    # MCap-based percentages (0-1)
    pct_mcap_rs55_gt0 = Column(Float, nullable=True)
    pct_mcap_rsi_gt50 = Column(Float, nullable=True)
    pct_mcap_above_sma20 = Column(Float, nullable=True)
    pct_mcap_above_sma50 = Column(Float, nullable=True)
    pct_mcap_above_sma100 = Column(Float, nullable=True)
    # Count-based percentages (0-1)
    pct_count_rs55_gt0 = Column(Float, nullable=True)
    pct_count_rsi_gt50 = Column(Float, nullable=True)
    pct_count_above_sma20 = Column(Float, nullable=True)
    pct_count_above_sma50 = Column(Float, nullable=True)
    pct_count_above_sma100 = Column(Float, nullable=True)
    
    __table_args__ = (
        UniqueConstraint("sector_id", "date", name="uq_sector_breadth_snapshots"),
    )


class IndustryBreadthSnapshot(Base):
    """Precomputed breadth snapshots for industries."""
    __tablename__ = "industry_breadth_snapshots"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    industry_id = Column(String, nullable=False, index=True)
    total_mcap = Column(Numeric(20, 2), nullable=False)
    total_stocks = Column(Integer, nullable=False)
    # MCap-based percentages (0-1)
    pct_mcap_rs55_gt0 = Column(Float, nullable=True)
    pct_mcap_rsi_gt50 = Column(Float, nullable=True)
    pct_mcap_above_sma20 = Column(Float, nullable=True)
    pct_mcap_above_sma50 = Column(Float, nullable=True)
    pct_mcap_above_sma100 = Column(Float, nullable=True)
    # Count-based percentages (0-1)
    pct_count_rs55_gt0 = Column(Float, nullable=True)
    pct_count_rsi_gt50 = Column(Float, nullable=True)
    pct_count_above_sma20 = Column(Float, nullable=True)
    pct_count_above_sma50 = Column(Float, nullable=True)
    pct_count_above_sma100 = Column(Float, nullable=True)
    
    __table_args__ = (
        UniqueConstraint("industry_id", "date", name="uq_industry_breadth_snapshots"),
    )


class SectorMomentumScore(Base):
    """Precomputed momentum scores for sectors."""
    __tablename__ = "sector_momentum_scores"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    sector_id = Column(String, nullable=False, index=True)
    total_mcap = Column(Numeric(20, 2), nullable=False)
    total_stocks = Column(Integer, nullable=False)
    score_1m = Column(Float, nullable=True)  # 0-100
    score_3m = Column(Float, nullable=True)  # 0-100
    score_6m = Column(Float, nullable=True)  # 0-100
    return_1m = Column(Float, nullable=True)  # Raw return %
    return_3m = Column(Float, nullable=True)  # Raw return %
    return_6m = Column(Float, nullable=True)  # Raw return %
    
    __table_args__ = (
        UniqueConstraint("sector_id", "date", name="uq_sector_momentum_scores"),
    )


class IndustryMomentumScore(Base):
    """Precomputed momentum scores for industries."""
    __tablename__ = "industry_momentum_scores"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    industry_id = Column(String, nullable=False, index=True)
    total_mcap = Column(Numeric(20, 2), nullable=False)
    total_stocks = Column(Integer, nullable=False)
    score_1m = Column(Float, nullable=True)  # 0-100
    score_3m = Column(Float, nullable=True)  # 0-100
    score_6m = Column(Float, nullable=True)  # 0-100
    return_1m = Column(Float, nullable=True)  # Raw return %
    return_3m = Column(Float, nullable=True)  # Raw return %
    return_6m = Column(Float, nullable=True)  # Raw return %
    
    __table_args__ = (
        UniqueConstraint("industry_id", "date", name="uq_industry_momentum_scores"),
    )


class SectorDeliveryStats(Base):
    """Precomputed delivery statistics for sectors."""
    __tablename__ = "sector_delivery_stats"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    sector_id = Column(String, nullable=False, index=True)
    stocks_count = Column(Integer, nullable=False)
    sector_mcap = Column(Numeric(20, 2), nullable=False)  # In crores
    sector_mcap_change_abs = Column(Numeric(20, 2), nullable=True)  # Change from prev day
    sector_mcap_change_pct = Column(Float, nullable=True)  # % change
    traded_value = Column(Numeric(20, 2), nullable=True)  # Total traded value in crores
    traded_value_avg = Column(Numeric(20, 2), nullable=True)  # 20-day average
    traded_value_multiple = Column(Float, nullable=True)  # traded_value / traded_value_avg
    delivery_value = Column(Numeric(20, 2), nullable=True)  # Total delivery value in crores
    delivery_value_avg = Column(Numeric(20, 2), nullable=True)  # 20-day average
    delivery_value_multiple = Column(Float, nullable=True)  # delivery_value / delivery_value_avg
    
    __table_args__ = (
        UniqueConstraint("sector_id", "date", name="uq_sector_delivery_stats"),
    )


class IndustryDeliveryStats(Base):
    """Precomputed delivery statistics for industries."""
    __tablename__ = "industry_delivery_stats"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    industry_id = Column(String, nullable=False, index=True)
    stocks_count = Column(Integer, nullable=False)
    industry_mcap = Column(Numeric(20, 2), nullable=False)  # In crores
    industry_mcap_change_abs = Column(Numeric(20, 2), nullable=True)  # Change from prev day
    industry_mcap_change_pct = Column(Float, nullable=True)  # % change
    traded_value = Column(Numeric(20, 2), nullable=True)  # Total traded value in crores
    traded_value_avg = Column(Numeric(20, 2), nullable=True)  # 20-day average
    traded_value_multiple = Column(Float, nullable=True)  # traded_value / traded_value_avg
    delivery_value = Column(Numeric(20, 2), nullable=True)  # Total delivery value in crores
    delivery_value_avg = Column(Numeric(20, 2), nullable=True)  # 20-day average
    delivery_value_multiple = Column(Float, nullable=True)  # delivery_value / delivery_value_avg
    
    __table_args__ = (
        UniqueConstraint("industry_id", "date", name="uq_industry_delivery_stats"),
    )


class SectorVWAPSnapshot(Base):
    """Precomputed VWAP snapshots for sectors."""
    __tablename__ = "sector_vwap_snapshots"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    sector_id = Column(String, nullable=False, index=True)
    total_mcap = Column(Numeric(20, 2), nullable=False)
    pct_mcap_price_above_vwap = Column(Float, nullable=True)  # 0-1
    
    __table_args__ = (
        UniqueConstraint("sector_id", "date", name="uq_sector_vwap_snapshots"),
    )


class IndustryVWAPSnapshot(Base):
    """Precomputed VWAP snapshots for industries."""
    __tablename__ = "industry_vwap_snapshots"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    industry_id = Column(String, nullable=False, index=True)
    total_mcap = Column(Numeric(20, 2), nullable=False)
    pct_mcap_price_above_vwap = Column(Float, nullable=True)  # 0-1
    
    __table_args__ = (
        UniqueConstraint("industry_id", "date", name="uq_industry_vwap_snapshots"),
    )

