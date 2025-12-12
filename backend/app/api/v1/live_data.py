"""Live data API endpoints using Kite Connect."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.db import database
from app.services import fetch_real_stocks
from app.utils import logger

router = APIRouter()


@router.get("/live-quote/{ticker}")
def get_live_quote(
    ticker: str,
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """
    Get live quote for a stock from Kite Connect.
    
    Returns:
        Live quote data with price, volume, timestamp, etc.
    """
    kite = fetch_real_stocks.get_kite_client()
    if not kite:
        raise HTTPException(
            status_code=503,
            detail="Kite Connect not configured. Set KITE_API_KEY and KITE_ACCESS_TOKEN environment variables."
        )
    
    quote = fetch_real_stocks.fetch_live_quote_from_kite(ticker, kite)
    
    if not quote:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch live quote for {ticker}. Make sure the ticker is valid and Kite Connect is properly configured."
        )
    
    return {
        **quote,
        "fetched_at": datetime.utcnow().isoformat(),
        "is_live": True,
        "source": "Kite Connect"
    }


@router.get("/live-quotes")
def get_live_quotes(
    tickers: str = Query(..., description="Comma-separated list of tickers"),
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """
    Get live quotes for multiple stocks.
    
    Args:
        tickers: Comma-separated list of ticker symbols (e.g., "RELIANCE,TCS,HDFCBANK")
    """
    kite = fetch_real_stocks.get_kite_client()
    if not kite:
        raise HTTPException(
            status_code=503,
            detail="Kite Connect not configured"
        )
    
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    quotes = {}
    errors = []
    
    for ticker in ticker_list:
        try:
            quote = fetch_real_stocks.fetch_live_quote_from_kite(ticker, kite)
            if quote:
                quotes[ticker] = quote
            else:
                errors.append(f"{ticker}: Not found")
        except Exception as e:
            errors.append(f"{ticker}: {str(e)}")
    
    return {
        "quotes": quotes,
        "errors": errors,
        "fetched_at": datetime.utcnow().isoformat(),
        "is_live": True,
        "source": "Kite Connect"
    }


@router.get("/intraday/{ticker}")
def get_intraday_data(
    ticker: str,
    interval: str = Query("5minute", description="Interval: minute, 3minute, 5minute, 15minute, 30minute, 60minute"),
    days: int = Query(1, description="Number of days of intraday data"),
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """
    Get intraday data for a stock from Kite Connect.
    
    Args:
        ticker: Stock ticker symbol
        interval: Data interval
        days: Number of days of data (max 60 days for intraday)
    """
    kite = fetch_real_stocks.get_kite_client()
    if not kite:
        raise HTTPException(
            status_code=503,
            detail="Kite Connect not configured"
        )
    
    from datetime import date, timedelta
    
    to_date = date.today()
    from_date = to_date - timedelta(days=min(days, 60))  # Kite limits intraday to 60 days
    
    df = fetch_real_stocks.fetch_stock_data_from_kite(
        ticker=ticker,
        from_date=from_date,
        to_date=to_date,
        kite=kite,
        interval=interval
    )
    
    if df is None or df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch intraday data for {ticker}"
        )
    
    # Convert to list of records
    records = df.to_dict('records')
    
    return {
        "ticker": ticker,
        "interval": interval,
        "data": records,
        "count": len(records),
        "fetched_at": datetime.utcnow().isoformat(),
        "is_live": True,
        "source": "Kite Connect"
    }

