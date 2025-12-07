"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime


class SectorTimeSeriesBase(BaseModel):
    """Base schema for sector time series."""
    sector_id: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class SectorTimeSeriesCreate(SectorTimeSeriesBase):
    """Schema for creating sector time series."""
    pass


class SectorTimeSeriesResponse(SectorTimeSeriesBase):
    """Schema for sector time series response."""
    id: int
    
    class Config:
        from_attributes = True


class SectorFeaturesBase(BaseModel):
    """Base schema for sector features."""
    sector_id: str
    date: date
    ret_1d: Optional[float] = None
    ret_5d: Optional[float] = None
    ret_1m: Optional[float] = None
    ma20: Optional[float] = None
    ma50: Optional[float] = None
    rsi: Optional[float] = None
    fii_net_inr: Optional[int] = None
    brent_pct_change_7d: Optional[float] = None
    # Options-based features
    pcr_oi: Optional[float] = None  # Put-Call Ratio by OI
    oi_change_1d: Optional[float] = None  # % change in OI vs 1 day ago
    oi_change_3d: Optional[float] = None  # % change in OI vs 3 days ago
    iv_index: Optional[float] = None  # Implied volatility index
    # Sentiment features
    sentiment_score_1d: Optional[float] = None  # 1-day sentiment score
    sentiment_score_7d: Optional[float] = None  # 7-day rolling sentiment score
    # Quarter Outlook features
    ret_3m: Optional[float] = None  # 3-month return
    ret_6m: Optional[float] = None  # 6-month return
    rel_1m_vs_nifty: Optional[float] = None  # Sector 1M return - Nifty 1M return
    rel_3m_vs_nifty: Optional[float] = None  # Sector 3M return - Nifty 3M return
    breadth_above_50dma: Optional[float] = None  # Proportion of constituents above 50DMA (0-1)
    breadth_3m_highs: Optional[float] = None  # % making 3-month highs (0-1)
    fii_net_inr_20d: Optional[float] = None  # Rolling 20-day FII net into sector
    fii_net_inr_percentile: Optional[float] = None  # Percentile vs last 1 year (0-1)
    valuation_pe: Optional[float] = None  # Current sector P/E
    valuation_pe_percentile: Optional[float] = None  # P/E percentile vs 5-year history (0-1)
    earnings_upgrades_pct_60d: Optional[float] = None  # % of stocks with EPS upgrades last 60 days (0-1)
    earnings_downgrades_pct_60d: Optional[float] = None  # % of stocks with EPS downgrades last 60 days (0-1)
    quarter_score: Optional[float] = None  # Final composite QuarterScore metric


class SectorFeaturesCreate(SectorFeaturesBase):
    """Schema for creating sector features."""
    pass


class SectorFeaturesResponse(SectorFeaturesBase):
    """Schema for sector features response."""
    id: int
    
    class Config:
        from_attributes = True


class ForecastDriver(BaseModel):
    """Schema for forecast driver."""
    driver: str
    value: Any
    impact: str  # positive/negative


class SectorForecastBase(BaseModel):
    """Base schema for sector forecast."""
    sector_id: str
    date: date
    forecast_3m_label: str  # UP/NEUTRAL/DOWN
    prob_up: float
    prob_neutral: float
    prob_down: float
    expected_return_pct: float
    top_drivers: Optional[List[Dict[str, Any]]] = None
    quarter_score: Optional[float] = None  # QuarterScore metric
    drivers: Optional[Dict[str, Dict[str, Any]]] = None  # QuarterScore contributions by pillar


class SectorForecastCreate(SectorForecastBase):
    """Schema for creating sector forecast."""
    pass


class SectorForecastResponse(SectorForecastBase):
    """Schema for sector forecast response."""
    id: int
    
    class Config:
        from_attributes = True


class SectorConstituentBase(BaseModel):
    """Base schema for sector constituent."""
    sector_id: str
    ticker: str
    company_name: str
    weight_pct: float


class SectorConstituentCreate(SectorConstituentBase):
    """Schema for creating sector constituent."""
    pass


class SectorConstituentResponse(SectorConstituentBase):
    """Schema for sector constituent response."""
    id: int
    
    class Config:
        from_attributes = True


# API Response schemas
class SectorSummary(BaseModel):
    """Schema for sector summary in /api/v1/sectors endpoint."""
    sector_id: str
    name: str
    latest_close: float
    ret_1m: float
    ret_1w: float
    sparkline: List[float]
    valuation_pe: Optional[float] = None
    valuation_state: Optional[str] = None  # "cheap", "fair", "expensive"
    sentiment_score_7d: Optional[float] = None  # 0-100


class ForecastResponse(BaseModel):
    """Schema for /api/v1/sectors/{sector_id}/forecast endpoint."""
    sector_id: str
    date: date
    forecast_3m_label: str
    prob_up: float
    prob_neutral: float
    prob_down: float
    expected_return_pct: float
    top_drivers: List[ForecastDriver]
    quarter_score: Optional[float] = None
    drivers: Optional[Dict[str, Dict[str, Any]]] = None  # QuarterScore contributions
    derivatives_sentiment: Optional[Dict[str, Any]] = None  # Derivatives sentiment label and metrics


class TimeseriesPoint(BaseModel):
    """Schema for a single timeseries data point."""
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class FlowData(BaseModel):
    """Schema for FII/DII flow data."""
    sector_id: str
    fii_net_inr: Optional[int] = None
    dii_net_inr: Optional[int] = None


# Flows schemas
class FIIDIIDailyBase(BaseModel):
    """Base schema for FII/DII daily flows."""
    date: date
    source: str
    ticker: Optional[str] = None
    fii_buy: Optional[int] = None
    fii_sell: Optional[int] = None
    dii_buy: Optional[int] = None
    dii_sell: Optional[int] = None


class FIIDIIDailyCreate(FIIDIIDailyBase):
    """Schema for creating FII/DII daily flows."""
    pass


class FIIDIIDailyResponse(FIIDIIDailyBase):
    """Schema for FII/DII daily flows response."""
    id: int
    
    class Config:
        from_attributes = True


class SectorFlowsDailyBase(BaseModel):
    """Base schema for sector flows daily."""
    date: date
    sector_id: str
    fii_net_inr: Optional[int] = None
    dii_net_inr: Optional[int] = None
    fii_gross: Optional[int] = None
    dii_gross: Optional[int] = None


class SectorFlowsDailyCreate(SectorFlowsDailyBase):
    """Schema for creating sector flows daily."""
    pass


class SectorFlowsDailyResponse(SectorFlowsDailyBase):
    """Schema for sector flows daily response."""
    id: int
    
    class Config:
        from_attributes = True


# Macro schemas
class MacroDailyBase(BaseModel):
    """Base schema for macro daily data."""
    date: date
    usd_inr_close: Optional[float] = None
    usd_inr_pct_1d: Optional[float] = None
    brent_close: Optional[float] = None
    brent_pct_7d: Optional[float] = None
    gold_close: Optional[float] = None
    us_10y_close: Optional[float] = None


class MacroDailyCreate(MacroDailyBase):
    """Schema for creating macro daily data."""
    pass


class MacroDailyResponse(MacroDailyBase):
    """Schema for macro daily data response."""
    id: int
    
    class Config:
        from_attributes = True


# Options schemas
class OptionsDailyBase(BaseModel):
    """Base schema for options daily data."""
    date: date
    underlying: str  # e.g., 'NIFTY', 'BANKNIFTY', 'NIFTY_BANK'
    expiry: Optional[date] = None
    total_call_oi: Optional[int] = None
    total_put_oi: Optional[int] = None
    pcr_oi: Optional[float] = None  # Put-Call Ratio by OI
    pcr_volume: Optional[float] = None  # Put-Call Ratio by volume
    total_call_volume: Optional[int] = None
    total_put_volume: Optional[int] = None
    oi_change_1d: Optional[float] = None  # % change in total OI
    oi_change_3d: Optional[float] = None
    iv_index: Optional[float] = None  # Implied volatility index


class OptionsDailyCreate(OptionsDailyBase):
    """Schema for creating options daily data."""
    pass


class OptionsDailyResponse(OptionsDailyBase):
    """Schema for options daily data response."""
    id: int
    
    class Config:
        from_attributes = True


# News and sentiment schemas
class NewsHeadlineBase(BaseModel):
    """Base schema for news headline."""
    date: date
    headline: str
    source: str
    url: Optional[str] = None
    text: Optional[str] = None
    sector_tags: Optional[List[str]] = None
    sentiment_score: Optional[float] = None  # -1 to +1
    sentiment_label: Optional[str] = None  # 'positive', 'negative', 'neutral'


class NewsHeadlineCreate(NewsHeadlineBase):
    """Schema for creating news headline."""
    pass


class NewsHeadlineResponse(NewsHeadlineBase):
    """Schema for news headline response."""
    id: int
    
    class Config:
        from_attributes = True


class SectorSentimentDailyBase(BaseModel):
    """Base schema for sector sentiment daily."""
    date: date
    sector_id: str
    sentiment_score_1d: Optional[float] = None
    sentiment_score_7d: Optional[float] = None
    headline_count: Optional[int] = None


class SectorSentimentDailyCreate(SectorSentimentDailyBase):
    """Schema for creating sector sentiment daily."""
    pass


class SectorSentimentDailyResponse(SectorSentimentDailyBase):
    """Schema for sector sentiment daily response."""
    id: int
    
    class Config:
        from_attributes = True


# Quarter Outlook schemas
class SectorBreadthDailyBase(BaseModel):
    """Base schema for sector breadth daily."""
    date: date
    sector_id: str
    total_constituents: Optional[int] = None
    above_50dma: Optional[int] = None
    above_200dma: Optional[int] = None
    making_3m_highs: Optional[int] = None
    making_3m_lows: Optional[int] = None


class SectorBreadthDailyCreate(SectorBreadthDailyBase):
    """Schema for creating sector breadth daily."""
    pass


class SectorBreadthDailyResponse(SectorBreadthDailyBase):
    """Schema for sector breadth daily response."""
    id: int
    
    class Config:
        from_attributes = True


class EarningsEventBase(BaseModel):
    """Base schema for earnings event."""
    date: date
    ticker: str
    sector_id: Optional[str] = None
    eps_actual: Optional[float] = None
    eps_estimate: Optional[float] = None
    surprise_pct: Optional[float] = None
    revision_direction: Optional[str] = None  # 'upgrade', 'downgrade', 'none'
    source: Optional[str] = None


class EarningsEventCreate(EarningsEventBase):
    """Schema for creating earnings event."""
    pass


class EarningsEventResponse(EarningsEventBase):
    """Schema for earnings event response."""
    id: int
    
    class Config:
        from_attributes = True


class SectorValuationsDailyBase(BaseModel):
    """Base schema for sector valuations daily."""
    date: date
    sector_id: str
    pe: Optional[float] = None
    pb: Optional[float] = None
    div_yield: Optional[float] = None


class SectorValuationsDailyCreate(SectorValuationsDailyBase):
    """Schema for creating sector valuations daily."""
    pass


class SectorValuationsDailyResponse(SectorValuationsDailyBase):
    """Schema for sector valuations daily response."""
    id: int
    
    class Config:
        from_attributes = True


class MarketSentimentDailyBase(BaseModel):
    """Base schema for market sentiment daily."""
    date: date
    india_vix: Optional[float] = None
    india_vix_percentile: Optional[float] = None
    index_pcr: Optional[float] = None
    breadth_nifty500_above_50dma: Optional[float] = None
    news_sentiment_score_7d: Optional[float] = None
    regime_label: Optional[str] = None  # 'RISK-ON', 'NEUTRAL', 'RISK-OFF'


class MarketSentimentDailyCreate(MarketSentimentDailyBase):
    """Schema for creating market sentiment daily."""
    pass


class MarketSentimentDailyResponse(MarketSentimentDailyBase):
    """Schema for market sentiment daily response."""
    id: int
    
    class Config:
        from_attributes = True

