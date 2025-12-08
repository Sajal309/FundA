"""Sector screener service - applies filters and sorting for stock screening."""
from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from app.db import models
from app.config.sector_screeners import SECTOR_SCREENERS, SECTOR_NAME_MAP, FIELD_MAP
from app.utils import logger


def get_sector_names_for_key(sector_key: str) -> List[str]:
    """Get list of sector names/IDs that match a screener key."""
    return SECTOR_NAME_MAP.get(sector_key, [])


def map_field_name(field: str) -> str:
    """Map frontend field name to database column name."""
    return FIELD_MAP.get(field, field)


def apply_sector_filters(
    db: Session,
    query,
    sector_key: str,
    latest_date: Optional[date] = None
) -> Any:
    """
    Apply sector-specific filters to a query.
    
    Args:
        db: Database session
        query: SQLAlchemy query object
        sector_key: Sector screener key (e.g., "banks", "it")
        latest_date: Latest date for fundamentals (defaults to most recent)
        
    Returns:
        Modified query with filters applied
    """
    config = SECTOR_SCREENERS.get(sector_key)
    if not config:
        return query
    
    # Get sector names to filter by
    sector_names = get_sector_names_for_key(sector_key)
    
    # Filter by sector_id matching any of the sector names
    # Note: Stock is already joined in the main query, so we just filter
    if sector_names:
        query = query.filter(models.Stock.sector_id.in_(sector_names))
    
    # Apply sector-specific filters based on config
    if sector_key == "banks":
        query = query.filter(
            models.StockFundamentals.roa > 1.0,
            models.StockFundamentals.net_interest_margin > 3.0,
            models.StockFundamentals.gross_npa < 3.0,
            models.StockFundamentals.net_npa < 1.0,
            models.StockFundamentals.provision_coverage > 70.0,
            models.StockFundamentals.casa_ratio > 35.0,
            models.StockFundamentals.capital_adequacy > 15.0,
            models.StockFundamentals.profit_growth_5y > 12.0,
        )
    elif sector_key == "nbfc":
        query = query.filter(
            models.StockFundamentals.roa > 1.5,
            models.StockFundamentals.roe > 12.0,
            models.StockFundamentals.gross_npa < 3.0,
            models.StockFundamentals.net_npa < 1.0,
            models.StockFundamentals.capital_adequacy > 18.0,
            models.StockFundamentals.aum_growth_5y > 12.0,
            models.StockFundamentals.debt_to_equity < 4.0,
        )
    elif sector_key == "insurance":
        query = query.filter(
            models.StockFundamentals.solvency_ratio > 1.8,
            models.StockFundamentals.embedded_value_growth_5y > 10.0,
            models.StockFundamentals.vnb_margin > 15.0,
            models.StockFundamentals.opex_to_sales < 25.0,
            models.StockFundamentals.roe > 12.0,
        )
    elif sector_key == "it":
        query = query.filter(
            models.StockFundamentals.ebit_margin > 18.0,
            models.StockFundamentals.profit_growth_5y > 12.0,
            models.StockFundamentals.free_cash_flow > 0,
            models.StockFundamentals.roe > 18.0,
            models.StockFundamentals.roce > 20.0,
            models.StockFundamentals.debt_to_equity < 0.3,
        )
    elif sector_key == "software":
        query = query.filter(
            models.StockFundamentals.revenue_growth_5y > 12.0,
            models.StockFundamentals.gross_margin > 50.0,
            models.StockFundamentals.ebitda_margin > 18.0,
            models.StockFundamentals.free_cash_flow > 0,
            models.StockFundamentals.roe > 15.0,
        )
    elif sector_key == "fmcg":
        query = query.filter(
            models.StockFundamentals.roe > 20.0,
            models.StockFundamentals.roce > 20.0,
            models.StockFundamentals.operating_margin > 15.0,
            models.StockFundamentals.sales_growth_5y > 8.0,
            models.StockFundamentals.debt_to_equity < 0.3,
        )
    elif sector_key == "pharma":
        query = query.filter(
            models.StockFundamentals.roce > 15.0,
            models.StockFundamentals.roe > 15.0,
            models.StockFundamentals.rnd_to_sales > 5.0,
            models.StockFundamentals.sales_growth_5y > 10.0,
            models.StockFundamentals.debt_to_equity < 0.4,
            models.StockFundamentals.export_share > 40.0,
        )
    elif sector_key == "hospitals":
        query = query.filter(
            models.StockFundamentals.ebitda_margin > 18.0,
            models.StockFundamentals.bed_occupancy > 55.0,
            models.StockFundamentals.roce > 15.0,
            models.StockFundamentals.sales_growth_5y > 12.0,
            models.StockFundamentals.debt_to_equity < 0.5,
        )
    elif sector_key == "diagnostics":
        query = query.filter(
            models.StockFundamentals.roe > 18.0,
            models.StockFundamentals.operating_margin > 20.0,
            models.StockFundamentals.profit_growth_5y > 12.0,
            models.StockFundamentals.debt_to_equity < 0.3,
        )
    elif sector_key == "real_estate":
        query = query.filter(
            models.StockFundamentals.debt_to_equity < 1.0,
            models.StockFundamentals.interest_coverage > 3.0,
            models.StockFundamentals.inventory_days < 400,
            models.StockFundamentals.sales_growth_5y > 10.0,
            models.StockFundamentals.roce > 12.0,
        )
    elif sector_key == "cement":
        query = query.filter(
            models.StockFundamentals.roce > 15.0,
            models.StockFundamentals.operating_margin > 18.0,
            models.StockFundamentals.debt_to_equity < 0.7,
            models.StockFundamentals.sales_growth_5y > 8.0,
            models.StockFundamentals.profit_growth_5y > 10.0,
        )
    elif sector_key == "metals":
        query = query.filter(
            models.StockFundamentals.roce > 18.0,
            models.StockFundamentals.debt_to_equity < 0.8,
            models.StockFundamentals.operating_margin > 15.0,
            models.StockFundamentals.interest_coverage > 3.0,
            models.StockFundamentals.sales_growth_5y > 8.0,
        )
    elif sector_key == "capital_goods":
        query = query.filter(
            models.StockFundamentals.order_book_growth_3y > 12.0,
            models.StockFundamentals.roce > 18.0,
            models.StockFundamentals.operating_margin > 12.0,
            models.StockFundamentals.debt_to_equity < 0.5,
            models.StockFundamentals.sales_growth_5y > 10.0,
        )
    elif sector_key == "defence":
        query = query.filter(
            models.StockFundamentals.roce > 20.0,
            models.StockFundamentals.operating_margin > 15.0,
            models.StockFundamentals.order_book_visibility_years > 2.0,
            models.StockFundamentals.sales_growth_5y > 12.0,
            models.StockFundamentals.debt_to_equity < 0.4,
        )
    elif sector_key == "infrastructure":
        query = query.filter(
            models.StockFundamentals.order_book_to_sales > 2.0,
            models.StockFundamentals.interest_coverage > 2.0,
            models.StockFundamentals.roce > 12.0,
            models.StockFundamentals.debt_to_equity < 1.0,
            models.StockFundamentals.sales_growth_5y > 10.0,
        )
    elif sector_key == "telecom":
        query = query.filter(
            models.StockFundamentals.arpu_growth > 5.0,
            models.StockFundamentals.ebitda_margin > 35.0,
            models.StockFundamentals.roce > 12.0,
            models.StockFundamentals.debt_to_equity < 2.0,
        )
    elif sector_key == "chemicals":
        query = query.filter(
            models.StockFundamentals.roce > 18.0,
            models.StockFundamentals.operating_margin > 15.0,
            models.StockFundamentals.sales_growth_5y > 12.0,
            models.StockFundamentals.export_share > 30.0,
            models.StockFundamentals.debt_to_equity < 0.5,
        )
    elif sector_key == "agrochemicals":
        query = query.filter(
            models.StockFundamentals.roce > 20.0,
            models.StockFundamentals.operating_margin > 18.0,
            models.StockFundamentals.export_share > 40.0,
            models.StockFundamentals.sales_growth_5y > 10.0,
            models.StockFundamentals.debt_to_equity < 0.4,
        )
    elif sector_key == "auto_oem":
        query = query.filter(
            models.StockFundamentals.roce > 18.0,
            models.StockFundamentals.operating_margin > 12.0,
            models.StockFundamentals.sales_growth_5y > 10.0,
            models.StockFundamentals.debt_to_equity < 0.5,
        )
    elif sector_key == "auto_ancillary":
        query = query.filter(
            models.StockFundamentals.roce > 18.0,
            models.StockFundamentals.operating_margin > 12.0,
            models.StockFundamentals.sales_growth_5y > 10.0,
            models.StockFundamentals.debt_to_equity < 0.5,
        )
    elif sector_key == "textiles":
        query = query.filter(
            models.StockFundamentals.roce > 12.0,
            models.StockFundamentals.operating_margin > 10.0,
            models.StockFundamentals.export_share > 30.0,
            models.StockFundamentals.sales_growth_5y > 8.0,
            models.StockFundamentals.debt_to_equity < 0.8,
        )
    elif sector_key == "retail":
        query = query.filter(
            models.StockFundamentals.roce > 18.0,
            models.StockFundamentals.operating_margin > 8.0,
            models.StockFundamentals.sales_growth_5y > 15.0,
            models.StockFundamentals.debt_to_equity < 0.5,
        )
    elif sector_key == "oil_gas":
        query = query.filter(
            models.StockFundamentals.roce > 15.0,
            models.StockFundamentals.operating_margin > 12.0,
            models.StockFundamentals.interest_coverage > 3.0,
            models.StockFundamentals.debt_to_equity < 0.8,
        )
    elif sector_key == "renewables":
        query = query.filter(
            models.StockFundamentals.roce > 10.0,
            models.StockFundamentals.operating_margin > 20.0,
            models.StockFundamentals.debt_to_equity < 2.0,
            models.StockFundamentals.sales_growth_5y > 12.0,
        )
    elif sector_key == "logistics":
        query = query.filter(
            models.StockFundamentals.roce > 15.0,
            models.StockFundamentals.operating_margin > 12.0,
            models.StockFundamentals.sales_growth_5y > 10.0,
            models.StockFundamentals.debt_to_equity < 0.7,
        )
    elif sector_key == "consumer_durables":
        query = query.filter(
            models.StockFundamentals.roce > 18.0,
            models.StockFundamentals.operating_margin > 12.0,
            models.StockFundamentals.sales_growth_5y > 10.0,
            models.StockFundamentals.debt_to_equity < 0.5,
        )
    elif sector_key == "media":
        query = query.filter(
            models.StockFundamentals.roce > 12.0,
            models.StockFundamentals.operating_margin > 10.0,
            models.StockFundamentals.sales_growth_5y > 8.0,
            models.StockFundamentals.debt_to_equity < 0.5,
        )
    
    return query


def get_latest_fundamentals_date(db: Session) -> Optional[date]:
    """Get the latest date for which we have fundamentals data."""
    latest = db.query(func.max(models.StockFundamentals.date)).scalar()
    # latest is already a date object, not a datetime
    return latest if latest else None


def screen_stocks(
    db: Session,
    sector_key: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Screen stocks for a given sector using the sector-specific filters and sorting.
    
    Args:
        db: Database session
        sector_key: Sector screener key (e.g., "banks", "it")
        limit: Maximum number of results to return
        
    Returns:
        List of stock dictionaries with fundamental data
    """
    config = SECTOR_SCREENERS.get(sector_key)
    if not config:
        logger.warning(f"Unknown sector key: {sector_key}")
        return []
    
    # Get latest fundamentals date
    latest_date = get_latest_fundamentals_date(db)
    if not latest_date:
        logger.warning("No fundamentals data available")
        return []
    
    # Start with fundamentals query
    query = db.query(
        models.StockFundamentals,
        models.Stock
    ).join(
        models.Stock, models.StockFundamentals.ticker == models.Stock.ticker
    ).filter(
        models.StockFundamentals.date == latest_date
    )
    
    # Apply sector-specific filters
    query = apply_sector_filters(db, query, sector_key, latest_date)
    
    # Apply sorting
    primary_field = map_field_name(config.primary_sort.field)
    primary_col = getattr(models.StockFundamentals, primary_field, None)
    if primary_col is None:
        # Try Stock table
        primary_col = getattr(models.Stock, primary_field, None)
    
    if primary_col:
        if config.primary_sort.direction == "desc":
            query = query.order_by(desc(primary_col))
        else:
            query = query.order_by(asc(primary_col))
        
        # Secondary sort
        if config.secondary_sort:
            secondary_field = map_field_name(config.secondary_sort.field)
            secondary_col = getattr(models.StockFundamentals, secondary_field, None)
            if secondary_col:
                if config.secondary_sort.direction == "desc":
                    query = query.order_by(desc(secondary_col))
                else:
                    query = query.order_by(asc(secondary_col))
    
    # Limit results
    results = query.limit(limit).all()
    
    # Format results
    formatted_results = []
    for fund, stock in results:
        row: Dict[str, Any] = {
            "ticker": stock.ticker,
            "name": stock.company_name,
        }
        
        # Add all requested columns
        for col_config in config.columns:
            field = col_config.field
            db_field = map_field_name(field)
            
            # Try to get value from fundamentals or stock
            value = None
            if hasattr(fund, db_field):
                value = getattr(fund, db_field)
            elif hasattr(stock, db_field):
                value = getattr(stock, db_field)
            
            # Format value
            if value is not None:
                if isinstance(value, (int, float)):
                    # Round to 2 decimal places
                    row[field] = round(float(value), 2)
                else:
                    row[field] = value
            else:
                row[field] = None
        
        formatted_results.append(row)
    
    return formatted_results

