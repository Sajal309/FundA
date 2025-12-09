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
    # NOTE: Filters are temporarily disabled to show all stocks in sector
    # In production, you can enable strict filters based on config.filter_query
    # For now, we only filter by sector_id (already done above)
    if False and sector_key == "banks":  # Disabled - show all stocks
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
    elif False and sector_key == "nbfc":
        # For NBFC, if fields are missing, allow the stock through
        # Only filter out if field exists and doesn't meet criteria
        pass  # No strict filters for now - return all stocks in sector
    elif False and sector_key == "insurance":
        query = query.filter(
            models.StockFundamentals.solvency_ratio > 1.8,
            models.StockFundamentals.embedded_value_growth_5y > 10.0,
            models.StockFundamentals.vnb_margin > 15.0,
            models.StockFundamentals.opex_to_sales < 25.0,
            models.StockFundamentals.roe > 12.0,
        )
    elif False and sector_key == "it":
        query = query.filter(
            models.StockFundamentals.ebit_margin > 18.0,
            models.StockFundamentals.profit_growth_5y > 12.0,
            models.StockFundamentals.free_cash_flow > 0,
            models.StockFundamentals.roe > 18.0,
            models.StockFundamentals.roce > 20.0,
            models.StockFundamentals.debt_to_equity < 0.3,
        )
    elif False and sector_key == "software":
        query = query.filter(
            models.StockFundamentals.revenue_growth_5y > 12.0,
            models.StockFundamentals.gross_margin > 50.0,
            models.StockFundamentals.ebitda_margin > 18.0,
            models.StockFundamentals.free_cash_flow > 0,
            models.StockFundamentals.roe > 15.0,
        )
    elif False and sector_key == "fmcg":
        query = query.filter(
            models.StockFundamentals.roe > 20.0,
            models.StockFundamentals.roce > 20.0,
            models.StockFundamentals.operating_margin > 15.0,
            models.StockFundamentals.sales_growth_5y > 8.0,
            models.StockFundamentals.debt_to_equity < 0.3,
        )
    elif False and sector_key == "pharma":
        query = query.filter(
            models.StockFundamentals.roce > 15.0,
            models.StockFundamentals.roe > 15.0,
            models.StockFundamentals.rnd_to_sales > 5.0,
            models.StockFundamentals.sales_growth_5y > 10.0,
            models.StockFundamentals.debt_to_equity < 0.4,
            models.StockFundamentals.export_share > 40.0,
        )
    elif False and sector_key == "hospitals":
        query = query.filter(
            models.StockFundamentals.ebitda_margin > 18.0,
            models.StockFundamentals.bed_occupancy > 55.0,
            models.StockFundamentals.roce > 15.0,
            models.StockFundamentals.sales_growth_5y > 12.0,
            models.StockFundamentals.debt_to_equity < 0.5,
        )
    elif False and sector_key == "diagnostics":
        query = query.filter(
            models.StockFundamentals.roe > 18.0,
            models.StockFundamentals.operating_margin > 20.0,
            models.StockFundamentals.profit_growth_5y > 12.0,
            models.StockFundamentals.debt_to_equity < 0.3,
        )
    elif False and sector_key == "real_estate":
        query = query.filter(
            models.StockFundamentals.debt_to_equity < 1.0,
            models.StockFundamentals.interest_coverage > 3.0,
            models.StockFundamentals.inventory_days < 400,
            models.StockFundamentals.sales_growth_5y > 10.0,
            models.StockFundamentals.roce > 12.0,
        )
    elif False and sector_key == "cement":
        query = query.filter(
            models.StockFundamentals.roce > 15.0,
            models.StockFundamentals.operating_margin > 18.0,
            models.StockFundamentals.debt_to_equity < 0.7,
            models.StockFundamentals.sales_growth_5y > 8.0,
            models.StockFundamentals.profit_growth_5y > 10.0,
        )
    elif False and sector_key == "metals":
        query = query.filter(
            models.StockFundamentals.roce > 18.0,
            models.StockFundamentals.debt_to_equity < 0.8,
            models.StockFundamentals.operating_margin > 15.0,
            models.StockFundamentals.interest_coverage > 3.0,
            models.StockFundamentals.sales_growth_5y > 8.0,
        )
    elif False and sector_key == "capital_goods":
        query = query.filter(
            models.StockFundamentals.order_book_growth_3y > 12.0,
            models.StockFundamentals.roce > 18.0,
            models.StockFundamentals.operating_margin > 12.0,
            models.StockFundamentals.debt_to_equity < 0.5,
            models.StockFundamentals.sales_growth_5y > 10.0,
        )
    elif False and sector_key == "defence":
        query = query.filter(
            models.StockFundamentals.roce > 20.0,
            models.StockFundamentals.operating_margin > 15.0,
            models.StockFundamentals.order_book_visibility_years > 2.0,
            models.StockFundamentals.sales_growth_5y > 12.0,
            models.StockFundamentals.debt_to_equity < 0.4,
        )
    elif False and sector_key == "infrastructure":
        query = query.filter(
            models.StockFundamentals.order_book_to_sales > 2.0,
            models.StockFundamentals.interest_coverage > 2.0,
            models.StockFundamentals.roce > 12.0,
            models.StockFundamentals.debt_to_equity < 1.0,
            models.StockFundamentals.sales_growth_5y > 10.0,
        )
    elif False and sector_key == "telecom":
        query = query.filter(
            models.StockFundamentals.arpu_growth > 5.0,
            models.StockFundamentals.ebitda_margin > 35.0,
            models.StockFundamentals.roce > 12.0,
            models.StockFundamentals.debt_to_equity < 2.0,
        )
    elif False and sector_key == "chemicals":
        query = query.filter(
            models.StockFundamentals.roce > 18.0,
            models.StockFundamentals.operating_margin > 15.0,
            models.StockFundamentals.sales_growth_5y > 12.0,
            models.StockFundamentals.export_share > 30.0,
            models.StockFundamentals.debt_to_equity < 0.5,
        )
    elif False and sector_key == "agrochemicals":
        query = query.filter(
            models.StockFundamentals.roce > 20.0,
            models.StockFundamentals.operating_margin > 18.0,
            models.StockFundamentals.export_share > 40.0,
            models.StockFundamentals.sales_growth_5y > 10.0,
            models.StockFundamentals.debt_to_equity < 0.4,
        )
    elif False and sector_key == "auto_oem":
        query = query.filter(
            models.StockFundamentals.roce > 18.0,
            models.StockFundamentals.operating_margin > 12.0,
            models.StockFundamentals.sales_growth_5y > 10.0,
            models.StockFundamentals.debt_to_equity < 0.5,
        )
    elif False and sector_key == "auto_ancillary":
        query = query.filter(
            models.StockFundamentals.roce > 18.0,
            models.StockFundamentals.operating_margin > 12.0,
            models.StockFundamentals.sales_growth_5y > 10.0,
            models.StockFundamentals.debt_to_equity < 0.5,
        )
    elif False and sector_key == "textiles":
        query = query.filter(
            models.StockFundamentals.roce > 12.0,
            models.StockFundamentals.operating_margin > 10.0,
            models.StockFundamentals.export_share > 30.0,
            models.StockFundamentals.sales_growth_5y > 8.0,
            models.StockFundamentals.debt_to_equity < 0.8,
        )
    elif False and sector_key == "retail":
        query = query.filter(
            models.StockFundamentals.roce > 18.0,
            models.StockFundamentals.operating_margin > 8.0,
            models.StockFundamentals.sales_growth_5y > 15.0,
            models.StockFundamentals.debt_to_equity < 0.5,
        )
    elif False and sector_key == "oil_gas":
        query = query.filter(
            models.StockFundamentals.roce > 15.0,
            models.StockFundamentals.operating_margin > 12.0,
            models.StockFundamentals.interest_coverage > 3.0,
            models.StockFundamentals.debt_to_equity < 0.8,
        )
    elif False and sector_key == "renewables":
        query = query.filter(
            models.StockFundamentals.roce > 10.0,
            models.StockFundamentals.operating_margin > 20.0,
            models.StockFundamentals.debt_to_equity < 2.0,
            models.StockFundamentals.sales_growth_5y > 12.0,
        )
    elif False and sector_key == "logistics":
        query = query.filter(
            models.StockFundamentals.roce > 15.0,
            models.StockFundamentals.operating_margin > 12.0,
            models.StockFundamentals.sales_growth_5y > 10.0,
            models.StockFundamentals.debt_to_equity < 0.7,
        )
    elif False and sector_key == "consumer_durables":
        query = query.filter(
            models.StockFundamentals.roce > 18.0,
            models.StockFundamentals.operating_margin > 12.0,
            models.StockFundamentals.sales_growth_5y > 10.0,
            models.StockFundamentals.debt_to_equity < 0.5,
        )
    elif False and sector_key == "media":
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
    
    # Get latest stock prices for CMP and 52w % calculation
    from datetime import timedelta
    tickers = [stock.ticker for _, stock in results]
    
    # Get latest prices for each ticker
    latest_prices = {}
    for ticker in tickers:
        latest_ts = db.query(models.StockTimeSeries).filter(
            models.StockTimeSeries.ticker == ticker
        ).order_by(desc(models.StockTimeSeries.date)).first()
        
        if latest_ts:
            latest_prices[ticker] = {
                'close': float(latest_ts.close),
                'date': latest_ts.date
            }
    
    # Get 52-week prices (approximately 252 trading days ago)
    year_ago_date = latest_date - timedelta(days=365)
    year_ago_prices = {}
    for ticker in tickers:
        # Get the earliest price in the last year
        year_ago_ts = db.query(models.StockTimeSeries).filter(
            and_(
                models.StockTimeSeries.ticker == ticker,
                models.StockTimeSeries.date >= year_ago_date,
                models.StockTimeSeries.date <= latest_date
            )
        ).order_by(asc(models.StockTimeSeries.date)).first()
        
        if year_ago_ts:
            year_ago_prices[ticker] = float(year_ago_ts.close)
    
    # Format results
    formatted_results = []
    for fund, stock in results:
        row: Dict[str, Any] = {
            "ticker": stock.ticker,
            "name": stock.company_name,
        }
        
        # Add CMP (Current Market Price) from latest StockTimeSeries
        if stock.ticker in latest_prices:
            row["cmp"] = round(latest_prices[stock.ticker]['close'], 2)
        else:
            row["cmp"] = None
        
        # Add 52w % change
        if stock.ticker in latest_prices and stock.ticker in year_ago_prices:
            current_price = latest_prices[stock.ticker]['close']
            year_ago_price = year_ago_prices[stock.ticker]
            if year_ago_price > 0:
                pct_change = ((current_price - year_ago_price) / year_ago_price) * 100
                row["percent_change_52w"] = round(pct_change, 2)
            else:
                row["percent_change_52w"] = None
        else:
            row["percent_change_52w"] = None
        
        # Add all requested columns from config
        for col_config in config.columns:
            field = col_config.field
            db_field = map_field_name(field)
            
            # Skip if already added (cmp, percent_change_52w)
            if field in row:
                continue
            
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
        
        # Add standardized fields that are always included (for Regular Columns view)
        # These fields are always added to the response, even if not in sector-specific config
        
        # Market cap (ensure it's there, convert to crores if needed)
        # Map both marketCap (from config) and market_cap (standardized)
        if "market_cap" not in row:
            # Try to get from marketCap first (from config columns)
            mcap_value = None
            if "marketCap" in row:
                mcap_value = row["marketCap"]
            elif fund.market_cap:
                mcap_value = fund.market_cap
            
            if mcap_value is not None:
                # Convert to float for comparison (handles Decimal, int, float)
                mcap_float = float(mcap_value)
                # Convert to crores if needed (if value > 10M, likely in absolute Rs)
                if mcap_float >= 10000000:  # If > 10M, likely in Rs, convert to Cr
                    row["market_cap"] = round(mcap_float / 10000000, 2)
                else:
                    row["market_cap"] = round(mcap_float, 2)
            else:
                row["market_cap"] = None
        
        # PE ratio
        if "pe" not in row:
            row["pe"] = round(float(fund.pe), 2) if fund.pe else None
        
        # Dividend yield
        if "dividend_yield" not in row:
            row["dividend_yield"] = round(float(fund.dividend_yield), 2) if fund.dividend_yield else None
        
        # Quarterly variations
        if "qtr_profit_var_pct" not in row:
            row["qtr_profit_var_pct"] = round(float(fund.qtr_profit_var_pct), 2) if fund.qtr_profit_var_pct else None
        if "qtr_sales_var_pct" not in row:
            row["qtr_sales_var_pct"] = round(float(fund.qtr_sales_var_pct), 2) if fund.qtr_sales_var_pct else None
        
        # ROCE
        if "roce" not in row:
            row["roce"] = round(float(fund.roce), 2) if fund.roce else None
        
        # Free cash flow (ensure in crores)
        # Map both freeCashFlow (from config) and free_cash_flow (standardized)
        if "freeCashFlow" in row and "free_cash_flow" not in row:
            fcf_value = row["freeCashFlow"]
            if fcf_value and isinstance(fcf_value, (int, float)):
                if fcf_value >= 10000000:  # Convert to crores if needed
                    row["free_cash_flow"] = round(fcf_value / 10000000, 2)
                else:
                    row["free_cash_flow"] = round(fcf_value, 2)
            else:
                row["free_cash_flow"] = None
        elif "free_cash_flow" not in row:
            if fund.free_cash_flow:
                fcf_value = float(fund.free_cash_flow)
                if fcf_value >= 10000000:  # Convert to crores if needed
                    row["free_cash_flow"] = round(fcf_value / 10000000, 2)
                else:
                    row["free_cash_flow"] = round(fcf_value, 2)
            else:
                row["free_cash_flow"] = None
        
        # Debt to equity
        # Map both debtToEquity (from config) and debt_to_equity (standardized)
        if "debtToEquity" in row and "debt_to_equity" not in row:
            row["debt_to_equity"] = row["debtToEquity"]
        elif "debt_to_equity" not in row:
            row["debt_to_equity"] = round(float(fund.debt_to_equity), 2) if fund.debt_to_equity else None
        
        # ROE
        if "roe" not in row:
            row["roe"] = round(float(fund.roe), 2) if fund.roe else None
        
        # ROE 3Y and 5Y
        if "roe_3y" not in row:
            row["roe_3y"] = round(float(fund.roe_3y), 2) if fund.roe_3y else None
        if "roe_5y" not in row:
            row["roe_5y"] = round(float(fund.roe_5y), 2) if fund.roe_5y else None
        
        # Shareholding
        if "pledged_percent" not in row:
            row["pledged_percent"] = round(float(fund.pledged_percent), 2) if fund.pledged_percent else None
        if "promoter_holding" not in row:
            row["promoter_holding"] = round(float(fund.promoter_holding), 2) if fund.promoter_holding else None
        if "public_holding" not in row:
            row["public_holding"] = round(float(fund.public_holding), 2) if fund.public_holding else None
        
        # Market Cap to Sales ratio
        if "mcap_to_sales" not in row:
            if fund.market_cap and fund.sales and float(fund.sales) > 0:
                mcap_value = float(fund.market_cap)
                sales_value = float(fund.sales)
                # Ensure both are in same units (crores)
                if mcap_value >= 10000000:
                    mcap_value = mcap_value / 10000000
                if sales_value >= 10000000:
                    sales_value = sales_value / 10000000
                mcap_to_sales = mcap_value / sales_value
                row["mcap_to_sales"] = round(mcap_to_sales, 2)
            else:
                row["mcap_to_sales"] = None
        
        formatted_results.append(row)
    
    return formatted_results

