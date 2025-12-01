"""Unit tests for feature computation."""
import pytest
import pandas as pd
from datetime import date
from app.services.features import calculate_rsi, calculate_moving_average, calculate_returns


def test_calculate_returns():
    """Test return calculation."""
    prices = pd.Series([100, 102, 105, 103, 108])
    ret = calculate_returns(prices, 1)
    assert ret is not None
    assert abs(ret - 8.0) < 0.01  # (108/100 - 1) * 100
    
    # Test with insufficient data
    prices_short = pd.Series([100, 102])
    ret_short = calculate_returns(prices_short, 5)
    assert ret_short is None


def test_calculate_moving_average():
    """Test moving average calculation."""
    prices = pd.Series([100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128, 130, 132, 134, 136, 138, 140])
    ma20 = calculate_moving_average(prices, 20)
    assert ma20 is not None
    assert ma20 > 0
    
    # Test with insufficient data
    prices_short = pd.Series([100, 102, 104])
    ma_short = calculate_moving_average(prices_short, 20)
    assert ma_short is None


def test_calculate_rsi():
    """Test RSI calculation."""
    # Create a series with upward trend
    prices = pd.Series([100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128, 130])
    rsi = calculate_rsi(prices, 14)
    assert rsi is not None
    assert 0 <= rsi <= 100
    
    # Test with insufficient data
    prices_short = pd.Series([100, 102, 104])
    rsi_short = calculate_rsi(prices_short, 14)
    assert rsi_short is None

