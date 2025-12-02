"""Script to fetch real data from external APIs."""
import sys
import os
import argparse
from datetime import date, datetime, timedelta
from app.db.database import SessionLocal
from app.services.ingest_macro import fetch_all_macro_from_yfinance
from app.services.ingest_news import ingest_news_from_api
from app.utils import logger


def main():
    """CLI entrypoint for fetching real data."""
    parser = argparse.ArgumentParser(description='Fetch real data from external APIs')
    parser.add_argument('--macro', action='store_true', help='Fetch macro data from yfinance')
    parser.add_argument('--news', action='store_true', help='Fetch news from NewsAPI')
    parser.add_argument('--days', type=int, default=30, help='Number of days to fetch (default: 30)')
    parser.add_argument('--news-api-key', help='NewsAPI key (or set NEWSAPI_KEY env var)')
    
    args = parser.parse_args()
    
    if not args.macro and not args.news:
        parser.print_help()
        sys.exit(1)
    
    db = SessionLocal()
    
    try:
        if args.macro:
            logger.info("Fetching macro data from yfinance...")
            count = fetch_all_macro_from_yfinance(db, days=args.days)
            print(f"✅ Fetched and ingested {count} macro data records")
        
        if args.news:
            from app.config import settings
            api_key = args.news_api_key or os.getenv('NEWSAPI_KEY') or settings.newsapi_key
            if not api_key:
                logger.error("NewsAPI key required. Set NEWSAPI_KEY env var, use --news-api-key, or configure in settings")
                sys.exit(1)
            
            logger.info("Fetching news from NewsAPI...")
            to_date = date.today()
            from_date = to_date - timedelta(days=args.days)
            count = ingest_news_from_api(db, api_key, from_date=from_date, to_date=to_date)
            print(f"✅ Fetched and ingested {count} news articles")
            
            # Aggregate sentiment
            from app.services.ingest_news import aggregate_sentiment_by_sector
            agg_count = aggregate_sentiment_by_sector(db, to_date)
            print(f"✅ Aggregated sentiment for {agg_count} sectors")
        
    except Exception as e:
        logger.error(f"Failed to fetch real data: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

