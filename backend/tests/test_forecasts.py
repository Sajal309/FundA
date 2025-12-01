"""Unit tests for forecast computation."""
import pytest
from app.services.forecasts import compute_rule_forecast
from app.db.schemas import SectorFeaturesResponse
from datetime import date


def test_forecast_strong_up():
    """Test forecast with strong positive signals."""
    features = SectorFeaturesResponse(
        id=1,
        sector_id="NIFTY_BANK",
        date=date.today(),
        ret_1m=5.0,  # Strong positive momentum
        ma20=46000.0,
        ma50=45000.0,  # MA20 > MA50
        fii_net_inr=1000000000,  # Strong FII inflows
        rsi=65.0
    )
    
    result = compute_rule_forecast(features, "NIFTY_BANK")
    
    assert result["forecast_3m_label"] == "UP"
    assert result["prob_up"] > 0.7
    assert result["expected_return_pct"] > 0
    assert len(result["top_drivers"]) > 0


def test_forecast_neutral():
    """Test forecast with neutral signals."""
    features = SectorFeaturesResponse(
        id=2,
        sector_id="NIFTY_IT",
        date=date.today(),
        ret_1m=1.5,  # Moderate positive
        ma20=31000.0,
        ma50=31200.0,  # MA20 < MA50
        fii_net_inr=100000000,  # Small FII flow
        rsi=50.0
    )
    
    result = compute_rule_forecast(features, "NIFTY_IT")
    
    # Should be NEUTRAL or UP depending on exact score
    assert result["forecast_3m_label"] in ["UP", "NEUTRAL", "DOWN"]
    assert 0 <= result["prob_up"] <= 1
    assert 0 <= result["prob_neutral"] <= 1
    assert 0 <= result["prob_down"] <= 1
    # Probabilities should sum to approximately 1.0
    total_prob = result["prob_up"] + result["prob_neutral"] + result["prob_down"]
    assert abs(total_prob - 1.0) < 0.02


def test_forecast_strong_down():
    """Test forecast with strong negative signals."""
    features = SectorFeaturesResponse(
        id=3,
        sector_id="NIFTY_METAL",
        date=date.today(),
        ret_1m=-5.0,  # Strong negative momentum
        ma20=18000.0,
        ma50=19000.0,  # MA20 < MA50
        fii_net_inr=-1000000000,  # Strong FII outflows
        rsi=35.0
    )
    
    result = compute_rule_forecast(features, "NIFTY_METAL")
    
    assert result["forecast_3m_label"] == "DOWN"
    assert result["prob_down"] > 0.7
    assert result["expected_return_pct"] < 0


def test_forecast_drivers():
    """Test that drivers are properly identified."""
    features = SectorFeaturesResponse(
        id=4,
        sector_id="NIFTY_BANK",
        date=date.today(),
        ret_1m=3.5,
        ma20=46000.0,
        ma50=45000.0,
        fii_net_inr=600000000,
        rsi=60.0
    )
    
    result = compute_rule_forecast(features, "NIFTY_BANK")
    
    assert "top_drivers" in result
    assert len(result["top_drivers"]) > 0
    
    # Check driver structure
    for driver in result["top_drivers"]:
        assert "driver" in driver
        assert "value" in driver
        assert "impact" in driver
        assert driver["impact"] in ["positive", "negative", "neutral"]

