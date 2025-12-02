"""News headline ingestion service with sentiment scoring."""
import os
import pandas as pd
import json
import sys
import argparse
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db import crud, schemas, database
from app.services.sentiment import score_sentiment_simple, extract_sector_tags, SECTOR_KEYWORDS
from app.utils import logger


def ingest_news_from_csv(file_path: str, db: Session) -> int:
    """
    Ingest news headlines from CSV file.
    
    Expected CSV format:
    date,headline,source,url,text
    
    Args:
        file_path: Path to CSV file
        db: Database session
        
    Returns:
        Number of records ingested
    """
    try:
        df = pd.read_csv(file_path)
        
        # Validate required columns
        required_cols = ['date', 'headline', 'source']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Convert date column
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Fill optional columns
        for col in ['url', 'text']:
            if col not in df.columns:
                df[col] = None
        
        count = 0
        for _, row in df.iterrows():
            try:
                # Score sentiment
                text_to_score = row.get('text') or row['headline']
                sentiment_score, sentiment_label = score_sentiment_simple(str(text_to_score))
                
                # Extract sector tags
                sector_tags = extract_sector_tags(str(text_to_score), SECTOR_KEYWORDS)
                
                headline_data = schemas.NewsHeadlineCreate(
                    date=row['date'],
                    headline=str(row['headline']),
                    source=str(row['source']),
                    url=row.get('url') if pd.notna(row.get('url')) else None,
                    text=row.get('text') if pd.notna(row.get('text')) else None,
                    sector_tags=sector_tags if sector_tags else None,
                    sentiment_score=sentiment_score,
                    sentiment_label=sentiment_label
                )
                crud.create_news_headline(db, headline_data)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to ingest news row {row.get('date', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully ingested {count} news records from {file_path}")
        return count
        
    except Exception as e:
        logger.error(f"Error ingesting news from CSV {file_path}: {e}")
        raise


def ingest_news_from_json(file_path: str, db: Session) -> int:
    """
    Ingest news headlines from JSON file.
    
    Expected JSON format:
    [
        {
            "date": "2025-11-28",
            "headline": "NIFTY Bank surges on strong earnings",
            "source": "Economic Times",
            "url": "https://...",
            "text": "Full article text..."
        },
        ...
    ]
    
    Args:
        file_path: Path to JSON file
        db: Database session
        
    Returns:
        Number of records ingested
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            data = [data]
        
        count = 0
        for item in data:
            try:
                target_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
                
                # Score sentiment
                text_to_score = item.get('text') or item['headline']
                sentiment_score, sentiment_label = score_sentiment_simple(str(text_to_score))
                
                # Extract sector tags
                sector_tags = extract_sector_tags(str(text_to_score), SECTOR_KEYWORDS)
                
                headline_data = schemas.NewsHeadlineCreate(
                    date=target_date,
                    headline=item['headline'],
                    source=item.get('source', 'Unknown'),
                    url=item.get('url'),
                    text=item.get('text'),
                    sector_tags=sector_tags if sector_tags else None,
                    sentiment_score=sentiment_score,
                    sentiment_label=sentiment_label
                )
                crud.create_news_headline(db, headline_data)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to ingest news item: {e}")
                continue
        
        logger.info(f"Successfully ingested {count} news records from {file_path}")
        return count
        
    except Exception as e:
        logger.error(f"Error ingesting news from JSON {file_path}: {e}")
        raise


def aggregate_sentiment_by_sector(db: Session, target_date: Optional[date] = None) -> int:
    """
    Aggregate sentiment scores by sector.
    
    Args:
        db: Database session
        target_date: Date to aggregate for (defaults to latest)
        
    Returns:
        Number of sector sentiment records created/updated
    """
    from app.db import models
    from sqlalchemy import func
    
    # Get all sectors
    sectors = crud.get_all_sectors(db)
    
    # Get headlines for the target date
    if target_date:
        headlines = crud.get_news_headlines(db, from_date=target_date, to_date=target_date, limit=10000)
    else:
        # Get latest date with headlines
        latest_headline = db.query(models.NewsHeadline).order_by(
            models.NewsHeadline.date.desc()
        ).first()
        if not latest_headline:
            logger.warning("No news headlines found to aggregate")
            return 0
        target_date = latest_headline.date
        headlines = crud.get_news_headlines(db, from_date=target_date, to_date=target_date, limit=10000)
    
    if not headlines:
        logger.warning(f"No headlines found for date {target_date}")
        return 0
    
    count = 0
    for sector_id in sectors:
        try:
            # Filter headlines for this sector
            sector_headlines = [
                h for h in headlines
                if h.sector_tags and sector_id in h.sector_tags
            ]
            
            if not sector_headlines:
                continue
            
            # Calculate 1-day sentiment
            sentiment_scores = [h.sentiment_score for h in sector_headlines if h.sentiment_score is not None]
            sentiment_score_1d = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else None
            
            # Calculate 7-day rolling sentiment
            week_start = target_date - timedelta(days=7)
            week_headlines = crud.get_news_headlines(
                db,
                sector_id=sector_id,
                from_date=week_start,
                to_date=target_date,
                limit=10000
            )
            week_scores = [h.sentiment_score for h in week_headlines if h.sentiment_score is not None]
            sentiment_score_7d = sum(week_scores) / len(week_scores) if week_scores else None
            
            # Create or update sector sentiment
            sector_sentiment = schemas.SectorSentimentDailyCreate(
                date=target_date,
                sector_id=sector_id,
                sentiment_score_1d=sentiment_score_1d,
                sentiment_score_7d=sentiment_score_7d,
                headline_count=len(sector_headlines)
            )
            crud.create_or_update_sector_sentiment_daily(db, sector_sentiment)
            count += 1
            
        except Exception as e:
            logger.error(f"Failed to aggregate sentiment for {sector_id}: {e}")
            continue
    
    logger.info(f"Aggregated sentiment for {count} sectors on {target_date}")
    return count


def fetch_news_from_api(
    api_key: Optional[str] = None,
    keywords: List[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> List[dict]:
    """
    Fetch news from NewsAPI.
    
    Args:
        api_key: NewsAPI API key (get from https://newsapi.org/)
        keywords: List of keywords to search for
        from_date: Start date for news
        to_date: End date for news
        
    Returns:
        List of news articles
    """
    if not api_key:
        logger.warning("NewsAPI key not provided. Set NEWSAPI_KEY environment variable.")
        return []
    
    try:
        import requests
        
        # NewsAPI endpoint
        url = "https://newsapi.org/v2/everything"
        
        # Build query
        query = " OR ".join(keywords) if keywords else "India stock market"
        
        params = {
            'q': query,
            'apiKey': api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 100,
        }
        
        if from_date:
            params['from'] = from_date.isoformat()
        if to_date:
            params['to'] = to_date.isoformat()
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            logger.info(f"Fetched {len(articles)} articles from NewsAPI")
            return articles
        elif response.status_code == 401:
            logger.error("NewsAPI authentication failed. Check your API key.")
            return []
        else:
            logger.warning(f"NewsAPI returned status {response.status_code}")
            return []
            
    except ImportError:
        logger.warning("requests library not installed")
        return []
    except Exception as e:
        logger.error(f"Error fetching news from NewsAPI: {e}")
        return []


def ingest_news_from_api(
    db: Session,
    api_key: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> int:
    """
    Fetch news from NewsAPI and ingest into database.
    
    Args:
        db: Database session
        api_key: NewsAPI API key
        keywords: Keywords to search (defaults to Indian market keywords)
        from_date: Start date
        to_date: End date
        
    Returns:
        Number of records ingested
    """
    if keywords is None:
        keywords = [
            'NIFTY', 'BSE', 'Sensex', 'Indian stock market',
            'Indian banks', 'Indian IT', 'Indian pharma'
        ]
    
    articles = fetch_news_from_api(api_key, keywords, from_date, to_date)
    
    count = 0
    for article in articles:
        try:
            # Parse published date
            published_str = article.get('publishedAt', '')
            if published_str:
                published_date = datetime.fromisoformat(published_str.replace('Z', '+00:00')).date()
            else:
                published_date = date.today()
            
            # Score sentiment
            text_to_score = article.get('content') or article.get('title', '')
            sentiment_score, sentiment_label = score_sentiment_simple(str(text_to_score))
            
            # Extract sector tags
            sector_tags = extract_sector_tags(str(text_to_score), SECTOR_KEYWORDS)
            
            headline_data = schemas.NewsHeadlineCreate(
                date=published_date,
                headline=article.get('title', ''),
                source=article.get('source', {}).get('name', 'NewsAPI'),
                url=article.get('url'),
                text=article.get('content'),
                sector_tags=sector_tags if sector_tags else None,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label
            )
            crud.create_news_headline(db, headline_data)
            count += 1
            
        except Exception as e:
            logger.warning(f"Failed to ingest news article: {e}")
            continue
    
    logger.info(f"Ingested {count} news articles from NewsAPI")
    return count


def main():
    """CLI entrypoint for news ingestion."""
    parser = argparse.ArgumentParser(description='Ingest news headlines with sentiment scoring')
    parser.add_argument('--source', help='Path to CSV or JSON file')
    parser.add_argument('--api', action='store_true', help='Fetch from NewsAPI instead of file')
    parser.add_argument('--aggregate', action='store_true', help='Aggregate sentiment by sector after ingestion')
    parser.add_argument('--date', help='Specific date to aggregate for (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=7, help='Days to fetch from API (default: 7)')
    
    args = parser.parse_args()
    
    if not args.source and not args.api:
        parser.error("Either --source or --api must be provided")
    
    db = next(database.get_db())
    
    try:
        if args.api:
            # Fetch from NewsAPI
            from app.config import settings
            api_key = os.getenv('NEWSAPI_KEY') or settings.newsapi_key
            if not api_key:
                logger.error("NewsAPI key required. Set NEWSAPI_KEY env var or in config")
                sys.exit(1)
            
            from datetime import timedelta
            to_date = date.today()
            from_date = to_date - timedelta(days=args.days)
            count = ingest_news_from_api(db, api_key, from_date=from_date, to_date=to_date)
            print(f"Ingested {count} news records from NewsAPI")
        else:
            # Ingest from file
            file_path = Path(args.source)
            file_format = args.format if hasattr(args, 'format') else file_path.suffix[1:].lower()
            
            if file_format == 'csv' or file_path.suffix.lower() == '.csv':
                count = ingest_news_from_csv(str(file_path), db)
                print(f"Ingested {count} news records")
            elif file_format == 'json' or file_path.suffix.lower() == '.json':
                count = ingest_news_from_json(str(file_path), db)
                print(f"Ingested {count} news records")
            else:
                logger.error(f"Unsupported file format: {file_format}")
                sys.exit(1)
        
        if args.aggregate:
            target_date = None
            if args.date:
                target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
            agg_count = aggregate_sentiment_by_sector(db, target_date)
            print(f"Aggregated sentiment for {agg_count} sectors")
    except Exception as e:
        logger.error(f"News ingestion failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

