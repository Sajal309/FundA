"""Service to calculate real technical indicators from stock data."""
import pandas as pd
import numpy as np
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import models
from app.utils import logger


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return prices.rolling(window=period, min_periods=period).mean()


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_returns(prices: pd.Series, periods: int) -> float:
    """Calculate return over specified periods."""
    if len(prices) < periods + 1:
        return None
    return ((prices.iloc[-1] - prices.iloc[-periods-1]) / prices.iloc[-periods-1]) * 100


def calculate_rs55(stock_prices: pd.Series, benchmark_prices: pd.Series) -> Optional[float]:
    """Calculate 55-day Relative Strength vs benchmark."""
    if len(stock_prices) < 56 or len(benchmark_prices) < 56:
        return None
    
    # Get last 55 days
    stock_55d = stock_prices.iloc[-56:]
    bench_55d = benchmark_prices.iloc[-56:]
    
    # Calculate returns
    stock_return = ((stock_55d.iloc[-1] - stock_55d.iloc[0]) / stock_55d.iloc[0]) * 100
    bench_return = ((bench_55d.iloc[-1] - bench_55d.iloc[0]) / bench_55d.iloc[0]) * 100
    
    # RS55 = Stock return - Benchmark return
    return stock_return - bench_return


def calculate_vwap(prices: pd.Series, volumes: pd.Series, period: int = 20) -> float:
    """Calculate Volume Weighted Average Price."""
    if len(prices) < period:
        return None
    
    recent_prices = prices.iloc[-period:]
    recent_volumes = volumes.iloc[-period:]
    
    vwap = (recent_prices * recent_volumes).sum() / recent_volumes.sum()
    return float(vwap)


def calculate_technical_indicators_for_stock(
    db: Session,
    ticker: str,
    target_date: Optional[date] = None
) -> int:
    """Calculate and store technical indicators for a stock."""
    if target_date is None:
        target_date = date.today()
    
    # Get stock time series
    timeseries = db.query(models.StockTimeSeries).filter(
        models.StockTimeSeries.ticker == ticker,
        models.StockTimeSeries.date <= target_date
    ).order_by(models.StockTimeSeries.date).all()
    
    if len(timeseries) < 100:
        logger.warning(f"Insufficient data for {ticker} (need at least 100 days)")
        return 0
    
    # Convert to DataFrame
    df = pd.DataFrame({
        'date': [ts.date for ts in timeseries],
        'close': [float(ts.close) for ts in timeseries],
        'volume': [float(ts.volume) for ts in timeseries],
    })
    df.set_index('date', inplace=True)
    
    # Get benchmark (Nifty 50) for RS55
    benchmark_ts = db.query(models.SectorTimeSeries).filter(
        models.SectorTimeSeries.sector_id == "NIFTY_50",
        models.SectorTimeSeries.ts <= pd.Timestamp(target_date)
    ).order_by(models.SectorTimeSeries.ts).all()
    
    benchmark_prices = None
    if benchmark_ts:
        bench_df = pd.DataFrame({
            'date': [ts.ts.date() for ts in benchmark_ts],
            'close': [float(ts.close) for ts in benchmark_ts],
        })
        bench_df.set_index('date', inplace=True)
        benchmark_prices = bench_df['close']
    
    # Calculate indicators for each date (starting from day 100)
    count = 0
    for i in range(99, len(timeseries)):
        ts_date = timeseries[i].date
        
        # Check if already calculated
        existing = db.query(models.StockTechnicalIndicators).filter(
            models.StockTechnicalIndicators.ticker == ticker,
            models.StockTechnicalIndicators.date == ts_date
        ).first()
        
        if existing:
            continue
        
        # Get price window up to this date
        price_window = df['close'].iloc[:i+1]
        volume_window = df['volume'].iloc[:i+1]
        
        # Calculate SMAs
        sma20 = calculate_sma(price_window, 20).iloc[-1] if len(price_window) >= 20 else None
        sma50 = calculate_sma(price_window, 50).iloc[-1] if len(price_window) >= 50 else None
        sma100 = calculate_sma(price_window, 100).iloc[-1] if len(price_window) >= 100 else None
        
        # Calculate RSI
        rsi14 = calculate_rsi(price_window, 14).iloc[-1] if len(price_window) >= 14 else None
        
        # Calculate returns
        return_1m = calculate_returns(price_window, 21) if len(price_window) >= 22 else None
        return_3m = calculate_returns(price_window, 63) if len(price_window) >= 64 else None
        return_6m = calculate_returns(price_window, 126) if len(price_window) >= 127 else None
        
        # Calculate RS55
        rs55 = None
        if benchmark_prices is not None and len(price_window) >= 56:
            # Align dates
            common_dates = price_window.index.intersection(benchmark_prices.index)
            if len(common_dates) >= 56:
                aligned_stock = price_window.loc[common_dates]
                aligned_bench = benchmark_prices.loc[common_dates]
                rs55 = calculate_rs55(aligned_stock, aligned_bench)
        
        # Calculate VWAP
        vwap = calculate_vwap(price_window, volume_window, 20)
        
        # Store indicator
        indicator = models.StockTechnicalIndicators(
            ticker=ticker,
            date=ts_date,
            sma20=Decimal(str(sma20)) if sma20 and not np.isnan(sma20) else None,
            sma50=Decimal(str(sma50)) if sma50 and not np.isnan(sma50) else None,
            sma100=Decimal(str(sma100)) if sma100 and not np.isnan(sma100) else None,
            rsi14=Decimal(str(rsi14)) if rsi14 and not np.isnan(rsi14) else None,
            rs55=rs55 if rs55 and not np.isnan(rs55) else None,
            return_1m=return_1m if return_1m and not np.isnan(return_1m) else None,
            return_3m=return_3m if return_3m and not np.isnan(return_3m) else None,
            return_6m=return_6m if return_6m and not np.isnan(return_6m) else None,
            vwap=Decimal(str(vwap)) if vwap and not np.isnan(vwap) else None,
        )
        db.add(indicator)
        count += 1
        
        if count % 100 == 0:
            db.commit()
            logger.info(f"Calculated {count} indicators for {ticker}...")
    
    db.commit()
    logger.info(f"Calculated {count} technical indicators for {ticker}")
    return count


def calculate_indicators_for_all_stocks(
    db: Session,
    target_date: Optional[date] = None
) -> int:
    """Calculate indicators for all stocks."""
    stocks = db.query(models.Stock).all()
    
    total_count = 0
    for stock in stocks:
        try:
            count = calculate_technical_indicators_for_stock(db, stock.ticker, target_date)
            total_count += count
        except Exception as e:
            logger.error(f"Error calculating indicators for {stock.ticker}: {e}")
            continue
    
    logger.info(f"Calculated {total_count} total technical indicators")
    return total_count

