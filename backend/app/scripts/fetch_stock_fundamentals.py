"""Script to fetch and store stock fundamentals data."""
import argparse
import sys
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import pandas as pd
import yfinance as yf

# Add parent directory to path (for Docker)
import os
if os.path.exists('/app'):
    sys.path.insert(0, '/app')
else:
    # For local development
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

try:
    from app.db import database, models
    from app.db import crud
    from app.utils import logger
except ImportError:
    # Fallback for direct execution
    import pathlib
    root = pathlib.Path(__file__).parent.parent.parent
    sys.path.insert(0, str(root))
    from app.db import database, models
    from app.db import crud
    from app.utils import logger


def fetch_fundamentals_from_nse(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch fundamentals from NSE using nsepython.
    NSE provides company information including market cap, P/E, etc.
    """
    try:
        from app.services import nsepython_service
        
        if not nsepython_service.is_available():
            return None
        
        # Fetch stock quote which contains fundamental data
        quote = nsepython_service.fetch_stock_quote(ticker)
        
        if not quote:
            return None
        
        fundamentals = {}
        
        # Extract data from quote structure
        # NSE quote structure may vary, so we check multiple possible locations
        if isinstance(quote, dict):
            # Try metadata for P/E ratios (most reliable)
            metadata = quote.get('metadata', {})
            if metadata:
                # P/E ratio from metadata
                pe = metadata.get('pdSymbolPe')
                if pe and pe > 0:
                    fundamentals['pe'] = float(pe)
                
                # Sector P/E for reference
                sector_pe = metadata.get('pdSectorPe')
                if sector_pe and sector_pe > 0:
                    fundamentals['sector_pe'] = float(sector_pe)
            
            # Try priceInfo for market cap and price data
            price_info = quote.get('priceInfo', {})
            if price_info:
                # Current price (CMP)
                last_price = price_info.get('lastPrice')
                if last_price:
                    fundamentals['current_price'] = float(last_price)
                
                # Previous close
                prev_close = price_info.get('previousClose')
                if prev_close:
                    fundamentals['previous_close'] = float(prev_close)
                
                # VWAP
                vwap = price_info.get('vwap')
                if vwap:
                    fundamentals['vwap'] = float(vwap)
                
                # 52-week high/low
                week_high_low = price_info.get('weekHighLow', {})
                if week_high_low:
                    if week_high_low.get('min'):
                        fundamentals['low_52w'] = float(week_high_low.get('min'))
                    if week_high_low.get('max'):
                        fundamentals['high_52w'] = float(week_high_low.get('max'))
                
                # Calculate market cap if we have price and shares outstanding
                if last_price and 'shares_outstanding' in fundamentals:
                    market_cap_rs = float(last_price) * fundamentals['shares_outstanding']
                    market_cap_cr = market_cap_rs / 10000000  # Convert to crores
                    if 'market_cap' not in fundamentals or fundamentals.get('market_cap') is None:
                        fundamentals['market_cap'] = market_cap_cr
            
            # Try securityInfo for company fundamentals
            security_info = quote.get('securityInfo', {})
            if security_info:
                # Face value
                face_value = security_info.get('faceValue')
                if face_value:
                    fundamentals['face_value'] = float(face_value)
                
                # Issued size (shares outstanding)
                issued_size = security_info.get('issuedSize')
                if issued_size:
                    fundamentals['shares_outstanding'] = float(issued_size)
            
            # Try info section
            info = quote.get('info', {})
            if info:
                # Company name (important for display)
                company_name = info.get('companyName')
                if company_name:
                    fundamentals['company_name'] = company_name
                
                # Industry
                industry = info.get('industry')
                if industry:
                    fundamentals['industry'] = industry
                
                # ISIN
                isin = info.get('isin')
                if isin:
                    fundamentals['isin'] = isin
                
                # Listing date
                listing_date = info.get('listingDate')
                if listing_date:
                    fundamentals['listing_date'] = listing_date
        
        if fundamentals:
            logger.info(f"Fetched {len(fundamentals)} metrics from NSE for {ticker}")
            return fundamentals
        
        return None
        
    except Exception as e:
        logger.error(f"Error fetching NSE fundamentals for {ticker}: {e}")
        return None


def fetch_fundamentals_from_yfinance(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch basic fundamentals from yfinance.
    Note: yfinance has limited fundamental data for Indian stocks.
    For comprehensive data, use Screener.in or other sources.
    """
    try:
        # Try with .NS suffix for NSE
        symbol = f"{ticker}.NS"
        stock = yf.Ticker(symbol)
        
        # Get info
        info = stock.info
        
        if not info or len(info) < 5:
            # Try without suffix
            stock = yf.Ticker(ticker)
            info = stock.info
        
        if not info or len(info) < 5:
            logger.warning(f"No fundamental data from yfinance for {ticker}")
            return None
        
        # Extract ALL available metrics comprehensively
        fundamentals = {}
        
        # Market Cap (convert to crores if needed)
        market_cap = info.get('marketCap') or info.get('totalAssets') or info.get('enterpriseValue')
        if market_cap:
            # Convert to crores (divide by 10,000,000 if in absolute rupees)
            if market_cap > 10000000:
                fundamentals['market_cap'] = market_cap / 10000000
            else:
                fundamentals['market_cap'] = market_cap
        
        # Company Name
        if info.get('longName'):
            fundamentals['company_name'] = info.get('longName')
        elif info.get('shortName'):
            fundamentals['company_name'] = info.get('shortName')
        
        # Price-to-Earnings
        if info.get('trailingPE'):
            fundamentals['pe'] = float(info.get('trailingPE'))
        elif info.get('forwardPE'):
            fundamentals['pe'] = float(info.get('forwardPE'))
        
        # Price-to-Book
        if info.get('priceToBook'):
            fundamentals['pb'] = float(info.get('priceToBook'))
        
        # Dividend Yield
        if info.get('dividendYield'):
            fundamentals['dividend_yield'] = float(info.get('dividendYield')) * 100
        elif info.get('trailingAnnualDividendYield'):
            fundamentals['dividend_yield'] = float(info.get('trailingAnnualDividendYield')) * 100
        
        # Profitability Ratios
        if info.get('returnOnEquity'):
            fundamentals['roe'] = float(info.get('returnOnEquity')) * 100
        if info.get('returnOnAssets'):
            fundamentals['roa'] = float(info.get('returnOnAssets')) * 100
        # ROCE - try multiple sources
        if info.get('returnOnCapitalEmployed'):
            fundamentals['roce'] = float(info.get('returnOnCapitalEmployed')) * 100
        elif info.get('returnOnEquity') and info.get('debtToEquity'):
            # Approximate ROCE: ROE adjusted for leverage
            # ROCE ≈ ROE when debt is low, but we can't calculate exactly without balance sheet
            # For now, use ROE as approximation if ROCE not available
            fundamentals['roce'] = float(info.get('returnOnEquity')) * 100
        elif info.get('returnOnAssets'):
            # Last resort: use ROA (not ideal but better than nothing)
            fundamentals['roce'] = float(info.get('returnOnAssets')) * 100
        
        # Margins
        if info.get('operatingMargins'):
            fundamentals['operating_margin'] = float(info.get('operatingMargins')) * 100
        if info.get('ebitdaMargins'):
            fundamentals['ebitda_margin'] = float(info.get('ebitdaMargins')) * 100
        if info.get('grossMargins'):
            fundamentals['gross_margin'] = float(info.get('grossMargins')) * 100
        if info.get('profitMargins'):
            fundamentals['net_margin'] = float(info.get('profitMargins')) * 100
        
        # Debt Ratios
        if info.get('debtToEquity'):
            fundamentals['debt_to_equity'] = float(info.get('debtToEquity'))
        
        # Cash Flow
        if info.get('freeCashflow'):
            fcf = info.get('freeCashflow')
            # Convert to crores if needed
            if abs(fcf) > 10000000:
                fundamentals['free_cash_flow'] = fcf / 10000000
            else:
                fundamentals['free_cash_flow'] = fcf
        
        # Growth Rates
        if info.get('revenueGrowth'):
            fundamentals['sales_growth_5y'] = float(info.get('revenueGrowth')) * 100
        if info.get('earningsGrowth'):
            fundamentals['profit_growth_5y'] = float(info.get('earningsGrowth')) * 100
        if info.get('earningsQuarterlyGrowth'):
            fundamentals['qtr_profit_var_pct'] = float(info.get('earningsQuarterlyGrowth')) * 100
        
        # Quarterly sales variation (if available)
        if info.get('revenueQuarterlyGrowth'):
            fundamentals['qtr_sales_var_pct'] = float(info.get('revenueQuarterlyGrowth')) * 100
        
        # ROE 3-year and 5-year averages (if available)
        if info.get('returnOnEquity3Year'):
            fundamentals['roe_3y'] = float(info.get('returnOnEquity3Year')) * 100
        if info.get('returnOnEquity5Year'):
            fundamentals['roe_5y'] = float(info.get('returnOnEquity5Year')) * 100
        
        # Interest Coverage (for debt analysis)
        if info.get('interestCoverage'):
            fundamentals['interest_coverage'] = float(info.get('interestCoverage'))
        
        # Sales/Revenue
        if info.get('totalRevenue'):
            revenue = info.get('totalRevenue')
            if revenue > 10000000:
                fundamentals['sales'] = revenue / 10000000
            else:
                fundamentals['sales'] = revenue
        
        # Shares Outstanding
        if info.get('sharesOutstanding'):
            fundamentals['shares_outstanding'] = float(info.get('sharesOutstanding'))
        
        # Current Price
        if info.get('currentPrice'):
            fundamentals['current_price'] = float(info.get('currentPrice'))
        elif info.get('regularMarketPrice'):
            fundamentals['current_price'] = float(info.get('regularMarketPrice'))
        
        # Book Value
        if info.get('bookValue'):
            fundamentals['book_value'] = float(info.get('bookValue'))
        
        # Enterprise Value
        if info.get('enterpriseValue'):
            ev = info.get('enterpriseValue')
            if ev > 10000000:
                fundamentals['enterprise_value'] = ev / 10000000
            else:
                fundamentals['enterprise_value'] = ev
        
        # Additional metrics
        if info.get('52WeekHigh'):
            fundamentals['high_52w'] = float(info.get('52WeekHigh'))
        if info.get('52WeekLow'):
            fundamentals['low_52w'] = float(info.get('52WeekLow'))
        
        # Pledged percentage (if available)
        if info.get('heldPercentInsiders'):
            fundamentals['promoter_holding'] = float(info.get('heldPercentInsiders'))
        
        # Try to extract additional data from financial statements
        try:
            # Get financial statements
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow
            
            # Extract quarterly variations from financials if available
            if financials is not None and not financials.empty:
                # Try to get latest quarter vs previous quarter
                if len(financials.columns) >= 2:
                    latest_col = financials.columns[0]
                    prev_col = financials.columns[1]
                    
                    # Net Income (Profit) variation
                    net_income_rows = financials.index[financials.index.str.contains('Net Income', case=False, na=False)]
                    if len(net_income_rows) > 0:
                        try:
                            latest_ni = financials.loc[net_income_rows[0], latest_col]
                            prev_ni = financials.loc[net_income_rows[0], prev_col]
                            if prev_ni and prev_ni != 0 and latest_ni and not pd.isna(latest_ni) and not pd.isna(prev_ni):
                                qtr_profit_var = ((float(latest_ni) - float(prev_ni)) / abs(float(prev_ni))) * 100
                                if 'qtr_profit_var_pct' not in fundamentals or fundamentals.get('qtr_profit_var_pct') is None:
                                    fundamentals['qtr_profit_var_pct'] = float(qtr_profit_var)
                        except:
                            pass
                    
                    # Revenue (Sales) variation
                    revenue_rows = financials.index[financials.index.str.contains('Revenue', case=False, na=False)]
                    if len(revenue_rows) > 0:
                        try:
                            latest_rev = financials.loc[revenue_rows[0], latest_col]
                            prev_rev = financials.loc[revenue_rows[0], prev_col]
                            if prev_rev and prev_rev != 0 and latest_rev and not pd.isna(latest_rev) and not pd.isna(prev_rev):
                                qtr_sales_var = ((float(latest_rev) - float(prev_rev)) / abs(float(prev_rev))) * 100
                                if 'qtr_sales_var_pct' not in fundamentals or fundamentals.get('qtr_sales_var_pct') is None:
                                    fundamentals['qtr_sales_var_pct'] = float(qtr_sales_var)
                        except:
                            pass
            
            # Extract debt and equity from balance sheet for better debt-to-equity calculation
            if balance_sheet is not None and not balance_sheet.empty:
                if len(balance_sheet.columns) > 0:
                    latest_col = balance_sheet.columns[0]
                    
                    # Total Debt
                    debt_rows = balance_sheet.index[balance_sheet.index.str.contains('Total Debt', case=False, na=False)]
                    if len(debt_rows) > 0:
                        try:
                            total_debt = balance_sheet.loc[debt_rows[0], latest_col]
                            if total_debt and total_debt != 0 and not pd.isna(total_debt):
                                # Total Stockholders Equity
                                equity_rows = balance_sheet.index[balance_sheet.index.str.contains('Stockholders Equity', case=False, na=False)]
                                if len(equity_rows) > 0:
                                    total_equity = balance_sheet.loc[equity_rows[0], latest_col]
                                    if total_equity and total_equity != 0 and not pd.isna(total_equity):
                                        debt_to_equity = float(total_debt) / float(total_equity)
                                        if 'debt_to_equity' not in fundamentals or fundamentals.get('debt_to_equity') is None:
                                            fundamentals['debt_to_equity'] = float(debt_to_equity)
                        except:
                            pass
            
            # Extract free cash flow from cashflow statement
            if cashflow is not None and not cashflow.empty:
                if len(cashflow.columns) > 0:
                    latest_col = cashflow.columns[0]
                    
                    # Free Cash Flow
                    fcf_rows = cashflow.index[cashflow.index.str.contains('Free Cash Flow', case=False, na=False)]
                    if len(fcf_rows) > 0:
                        try:
                            fcf = cashflow.loc[fcf_rows[0], latest_col]
                            if fcf and not pd.isna(fcf):
                                # Convert to crores if needed
                                fcf_float = float(fcf)
                                if abs(fcf_float) > 10000000:
                                    fcf_cr = fcf_float / 10000000
                                else:
                                    fcf_cr = fcf_float
                                if 'free_cash_flow' not in fundamentals or fundamentals.get('free_cash_flow') is None:
                                    fundamentals['free_cash_flow'] = float(fcf_cr)
                        except:
                            pass
        except Exception as e:
            logger.debug(f"Could not extract additional data from financial statements for {ticker}: {e}")
        
        # Clean None values and invalid numbers
        fundamentals = {k: v for k, v in fundamentals.items() if v is not None and not (isinstance(v, float) and (v != v or v == float('inf') or v == float('-inf')))}
        
        if not fundamentals:
            return None
        
        logger.info(f"Fetched {len(fundamentals)} metrics from yfinance for {ticker}")
        return fundamentals
        
    except Exception as e:
        logger.error(f"Error fetching yfinance fundamentals for {ticker}: {e}")
        return None


# Mock data generation removed - only real data sources are used


def store_fundamentals(
    db: Session,
    ticker: str,
    fundamentals: Dict[str, Any],
    as_of_date: date
) -> bool:
    """Store fundamentals data in database and update Stock table if needed."""
    try:
        # First, update Stock table with company name and shares outstanding if available
        stock = db.query(models.Stock).filter(models.Stock.ticker == ticker).first()
        if stock:
            updated_stock = False
            # Update company name if we have a better one
            if 'company_name' in fundamentals and fundamentals['company_name']:
                new_name = fundamentals['company_name']
                if new_name and (not stock.company_name or len(new_name) > len(stock.company_name)):
                    stock.company_name = new_name
                    updated_stock = True
            
            # Update shares outstanding if we have it
            if 'shares_outstanding' in fundamentals and fundamentals['shares_outstanding']:
                shares = fundamentals['shares_outstanding']
                if shares and (not stock.shares_outstanding or shares > stock.shares_outstanding):
                    stock.shares_outstanding = int(shares)
                    updated_stock = True
            
            if updated_stock:
                db.commit()
                logger.debug(f"Updated Stock record for {ticker}")
        
        # Check if fundamentals record exists
        existing = db.query(models.StockFundamentals).filter(
            models.StockFundamentals.ticker == ticker,
            models.StockFundamentals.date == as_of_date
        ).first()
        
        if existing:
            # Update existing
            for key, value in fundamentals.items():
                # Skip non-fundamental fields
                skip_fields = ['company_name', 'industry', 'isin', 'listing_date', 'current_price', 
                              'previous_close', 'vwap', 'high_52w', 'low_52w', 'sector_pe', 'shares_outstanding']
                if key in skip_fields:
                    continue
                
                if hasattr(existing, key) and value is not None:
                    # Check for NaN or infinite values
                    if isinstance(value, (int, float)):
                        if value != value or value == float('inf') or value == float('-inf'):
                            continue
                        setattr(existing, key, Decimal(str(value)))
                    else:
                        setattr(existing, key, value)
            db.commit()
            logger.debug(f"Updated fundamentals for {ticker} on {as_of_date}")
            return True
        else:
            # Create new
            fund_data = {
                'ticker': ticker,
                'date': as_of_date,
            }
            
            # Add all fundamental fields
            for key, value in fundamentals.items():
                # Skip non-fundamental fields
                skip_fields = ['company_name', 'industry', 'isin', 'listing_date', 'current_price', 
                              'previous_close', 'vwap', 'high_52w', 'low_52w', 'sector_pe', 'shares_outstanding']
                if key in skip_fields:
                    continue
                
                if hasattr(models.StockFundamentals, key) and value is not None:
                    # Check for NaN or infinite values
                    if isinstance(value, (int, float)):
                        if value != value or value == float('inf') or value == float('-inf'):
                            continue
                        fund_data[key] = Decimal(str(value))
                    else:
                        fund_data[key] = value
            
            fund = models.StockFundamentals(**fund_data)
            db.add(fund)
            db.commit()
            logger.info(f"Stored fundamentals for {ticker} on {as_of_date}")
            return True
            
    except Exception as e:
        logger.error(f"Error storing fundamentals for {ticker}: {e}")
        db.rollback()
        return False


def fetch_fundamentals_for_stock(
    db: Session,
    ticker: str,
    as_of_date: Optional[date] = None
) -> bool:
    """
    Fetch and store fundamentals for a single stock from trusted sources.
    Priority: NSE (official exchange data) > yfinance (comprehensive fallback)
    """
    if as_of_date is None:
        as_of_date = date.today()
    
    # Get stock info
    stock = db.query(models.Stock).filter(models.Stock.ticker == ticker).first()
    if not stock:
        logger.warning(f"Stock {ticker} not found in database")
        return False
    
    # Fetch fundamentals - Try Screener.in first (most comprehensive), then NSE, then yfinance
    fundamentals = None
    source = None
    
    # Strategy: Always try to merge data from multiple sources for comprehensive fundamentals
    # NSE provides official P/E, market data
    # yfinance provides ROE, ROCE, margins, growth rates
    
    # Step 1: Fetch from NSE (official exchange data - P/E, market data)
    nse_fundamentals = fetch_fundamentals_from_nse(ticker)
    if nse_fundamentals:
        fundamentals = nse_fundamentals
        source = "NSE"
        logger.info(f"✅ Fetched {len(nse_fundamentals)} metrics from NSE for {ticker}")
        import time
        time.sleep(0.5)  # Rate limiting
    
    # Step 2: Always try yfinance to get comprehensive fundamentals (ROE, ROCE, margins, etc.)
    yf_fundamentals = fetch_fundamentals_from_yfinance(ticker)
    if yf_fundamentals:
        if fundamentals:
            # Merge yfinance data (prioritize NSE for P/E, but use yfinance for ratios)
            # Don't overwrite NSE P/E with yfinance if both exist
            for key, value in yf_fundamentals.items():
                if key not in fundamentals or fundamentals.get(key) is None:
                    fundamentals[key] = value
            source = f"{source} + yfinance"
        else:
            fundamentals = yf_fundamentals
            source = "yfinance"
        logger.info(f"✅ Merged {len(yf_fundamentals)} metrics from yfinance for {ticker}")
    
    # If all failed, return False (no mock data)
    if not fundamentals or len(fundamentals) < 2:
        logger.warning(f"❌ Could not fetch sufficient fundamentals for {ticker} from any source")
        return False
    
    logger.info(f"✅ Fetched fundamentals for {ticker} from {source} ({len(fundamentals)} metrics)")
    
    # Store in database
    return store_fundamentals(db, ticker, fundamentals, as_of_date)


def fetch_fundamentals_for_sector(
    db: Session,
    sector_id: str,
    limit: Optional[int] = None
) -> int:
    """Fetch fundamentals for all stocks in a sector. Only uses real data sources."""
    stocks = db.query(models.Stock).filter(models.Stock.sector_id == sector_id).all()
    
    if limit:
        stocks = stocks[:limit]
    
    count = 0
    for stock in stocks:
        if fetch_fundamentals_for_stock(db, stock.ticker):
            count += 1
        # Small delay to avoid rate limiting
        import time
        time.sleep(0.5)
    
    logger.info(f"Fetched fundamentals for {count}/{len(stocks)} stocks in {sector_id}")
    return count


def fetch_fundamentals_for_all_stocks(
    db: Session,
    limit: Optional[int] = None
) -> int:
    """Fetch fundamentals for all stocks in database. Only uses real data sources."""
    stocks = db.query(models.Stock).all()
    
    if limit:
        stocks = stocks[:limit]
    
    count = 0
    total = len(stocks)
    
    for i, stock in enumerate(stocks, 1):
        logger.info(f"Processing {i}/{total}: {stock.ticker}")
        if fetch_fundamentals_for_stock(db, stock.ticker):
            count += 1
        # Small delay to avoid rate limiting
        import time
        time.sleep(0.5)
    
    logger.info(f"Fetched fundamentals for {count}/{total} stocks")
    return count


def main():
    parser = argparse.ArgumentParser(description='Fetch stock fundamentals data')
    parser.add_argument('--ticker', type=str, help='Fetch for specific ticker')
    parser.add_argument('--sector', type=str, help='Fetch for all stocks in sector')
    parser.add_argument('--all', action='store_true', help='Fetch for all stocks')
    parser.add_argument('--limit', type=int, help='Limit number of stocks to process')
    parser.add_argument('--date', type=str, help='As of date (YYYY-MM-DD), defaults to today')
    
    args = parser.parse_args()
    
    db = next(database.get_db())
    
    try:
        as_of_date = date.today()
        if args.date:
            as_of_date = date.fromisoformat(args.date)
        
        if args.ticker:
            logger.info(f"Fetching fundamentals for {args.ticker} (real data only)")
            fetch_fundamentals_for_stock(db, args.ticker, as_of_date)
        elif args.sector:
            logger.info(f"Fetching fundamentals for sector {args.sector} (real data only)")
            fetch_fundamentals_for_sector(db, args.sector, args.limit)
        elif args.all:
            logger.info("Fetching fundamentals for all stocks (real data only)")
            fetch_fundamentals_for_all_stocks(db, args.limit)
        else:
            parser.print_help()
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()

