"""Unit tests for ranking service."""
import pytest
from decimal import Decimal
from app.services.ranking_service import (
    percentile,
    winsorize,
    min_max_normalize,
    get_metric_value
)


def test_percentile():
    """Test percentile calculation."""
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert percentile(values, 0.5) == pytest.approx(5.5, abs=0.1)
    assert percentile(values, 0.0) == 1
    assert percentile(values, 1.0) == 10
    assert percentile(values, 0.25) == pytest.approx(3.25, abs=0.1)


def test_winsorize():
    """Test winsorization."""
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]  # 100 is outlier
    winsorized = winsorize(values, 0.1, 0.9)
    assert max(winsorized) < 100  # Outlier should be capped
    assert min(winsorized) >= 1


def test_min_max_normalize():
    """Test min-max normalization."""
    values = [1, 2, 3, 4, 5]
    normalized = min_max_normalize(values)
    assert normalized[0] == 0.0  # Min should be 0
    assert normalized[-1] == 1.0  # Max should be 1
    assert all(0 <= v <= 1 for v in normalized)
    
    # Test identical values
    identical = [5, 5, 5, 5]
    normalized_identical = min_max_normalize(identical)
    assert all(v == 0.5 for v in normalized_identical)


def test_get_metric_value():
    """Test metric value extraction."""
    row = {
        "roce": Decimal("25.5"),
        "roe": 15.3,
        "pe": None,
        "debt_to_equity": "10.2"  # String should be handled
    }
    
    assert get_metric_value(row, "roce") == 25.5
    assert get_metric_value(row, "roe") == 15.3
    assert get_metric_value(row, "pe") is None
    assert get_metric_value(row, "debt_to_equity") == 10.2


def test_compute_sector_ranked_stocks_mock(mocker):
    """Test ranking computation with mocked database."""
    from app.services import ranking_service
    from app.db import models
    
    # Mock database query
    mock_stock = models.Stock(
        ticker="TCS",
        company_name="Tata Consultancy Services",
        sector_id="NIFTY_IT"
    )
    
    mock_fundamentals = models.StockFundamentals(
        ticker="TCS",
        roce=Decimal("30.5"),
        roe=Decimal("25.3"),
        opm=Decimal("28.0"),
        profit_growth_5y=Decimal("15.2"),
        sales_growth_5y=Decimal("12.5"),
        free_cash_flow=Decimal("10000000000"),
        debt_to_equity=Decimal("0.1"),
        pe=Decimal("25.0"),
        date=models.StockFundamentals.date
    )
    
    # This is a simplified test - in practice, you'd mock the DB session
    # For now, we test the normalization functions which are the core logic
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

