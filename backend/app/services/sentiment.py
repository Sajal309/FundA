"""Sentiment analysis service for news headlines."""
import re
from typing import Tuple, Optional
from app.utils import logger


# Simple keyword-based sentiment (can be replaced with VADER or transformers)
POSITIVE_KEYWORDS = [
    'surge', 'rally', 'gain', 'rise', 'up', 'growth', 'profit', 'beat', 'strong',
    'positive', 'bullish', 'outperform', 'upgrade', 'buy', 'soar', 'jump',
    'record', 'high', 'breakthrough', 'success', 'win', 'boost', 'momentum'
]

NEGATIVE_KEYWORDS = [
    'fall', 'drop', 'decline', 'down', 'loss', 'miss', 'weak', 'negative',
    'bearish', 'underperform', 'downgrade', 'sell', 'crash', 'plunge',
    'crisis', 'concern', 'risk', 'worry', 'fear', 'uncertainty', 'volatility',
    'recession', 'slowdown', 'pressure', 'struggle', 'challenge'
]


def score_sentiment_simple(text: str) -> Tuple[float, str]:
    """
    Simple keyword-based sentiment scoring.
    
    Args:
        text: Text to analyze (headline or article)
        
    Returns:
        Tuple of (score, label) where score is -1 to +1 and label is 'positive', 'negative', or 'neutral'
    """
    if not text:
        return 0.0, 'neutral'
    
    text_lower = text.lower()
    
    # Count positive and negative keywords
    positive_count = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in text_lower)
    negative_count = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in text_lower)
    
    # Calculate score
    total_keywords = positive_count + negative_count
    if total_keywords == 0:
        return 0.0, 'neutral'
    
    score = (positive_count - negative_count) / max(total_keywords, 1)
    
    # Normalize to -1 to +1 range
    score = max(-1.0, min(1.0, score))
    
    # Determine label
    if score > 0.2:
        label = 'positive'
    elif score < -0.2:
        label = 'negative'
    else:
        label = 'neutral'
    
    return score, label


def score_sentiment_vader(text: str) -> Tuple[float, str]:
    """
    VADER sentiment scoring (requires vaderSentiment package).
    
    Args:
        text: Text to analyze
        
    Returns:
        Tuple of (score, label)
    """
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(text)
        
        # Use compound score (-1 to +1)
        score = scores['compound']
        
        # Determine label
        if score >= 0.05:
            label = 'positive'
        elif score <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'
        
        return score, label
        
    except ImportError:
        logger.warning("vaderSentiment not installed, falling back to simple scoring")
        return score_sentiment_simple(text)


def extract_sector_tags(text: str, sector_keywords: dict) -> list:
    """
    Extract sector tags from text based on keywords.
    
    Args:
        text: Text to analyze
        sector_keywords: Dict mapping sector_id to list of keywords
        
    Returns:
        List of sector IDs that match the text
    """
    text_lower = text.lower()
    matched_sectors = []
    
    for sector_id, keywords in sector_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matched_sectors.append(sector_id)
                break  # Only add each sector once
    
    return matched_sectors


# Sector keyword mapping for news tagging
SECTOR_KEYWORDS = {
    # Broad Market Indices - general market keywords
    'NIFTY_50': ['nifty 50', 'nifty', 'sensex', 'market', 'indian market', 'stock market', 'equity'],
    'NIFTY_NEXT_50': ['nifty next 50', 'next 50', 'midcap', 'mid cap'],
    'NIFTY_100': ['nifty 100', 'largecap', 'large cap', 'blue chip'],
    'NIFTY_200': ['nifty 200', 'largecap', 'midcap'],
    'NIFTY_500': ['nifty 500', 'broad market', 'entire market'],
    'NIFTY_MIDCAP_50': ['midcap 50', 'mid cap 50'],
    'NIFTY_MIDCAP_100': ['midcap 100', 'mid cap 100'],
    'NIFTY_MIDCAP_150': ['midcap 150', 'mid cap 150'],
    'NIFTY_SMALLCAP_50': ['smallcap 50', 'small cap 50'],
    'NIFTY_SMALLCAP_100': ['smallcap 100', 'small cap 100'],
    'NIFTY_SMALLCAP_250': ['smallcap 250', 'small cap 250', 'smallcap', 'small cap'],
    # Sectoral Indices
    'NIFTY_BANK': ['bank', 'banking', 'lender', 'credit', 'loan', 'nbfc', 'hdfc', 'icici', 'sbi', 'axis'],
    'NIFTY_IT': ['it', 'software', 'tech', 'technology', 'infosys', 'tcs', 'wipro', 'hcl'],
    'NIFTY_FMCG': ['fmcg', 'consumer', 'hul', 'nestle', 'britannia', 'tata consumer'],
    'NIFTY_PHARMA': ['pharma', 'pharmaceutical', 'drug', 'medicine', 'sun pharma', 'dr reddy'],
    'NIFTY_AUTO': ['auto', 'automobile', 'car', 'vehicle', 'maruti', 'tata motors', 'mahindra'],
    'NIFTY_ENERGY': ['energy', 'oil', 'gas', 'petrol', 'reliance', 'ongc', 'brent'],
    'NIFTY_METAL': ['metal', 'steel', 'aluminum', 'tata steel', 'jsw', 'hindalco'],
    'NIFTY_REALTY': ['realty', 'real estate', 'property', 'housing', 'dlf', 'godrej properties'],
    'NIFTY_PSU_BANK': ['psu bank', 'public sector bank', 'sbi', 'pnb', 'boi'],
    'NIFTY_PRIVATE_BANK': ['private bank', 'hdfc', 'icici', 'axis', 'kotak'],
    'NIFTY_FIN_SERVICE': ['financial services', 'finance', 'financial', 'banking', 'insurance'],
    'NIFTY_HEALTHCARE': ['healthcare', 'health care', 'hospital', 'medical', 'pharma'],
    'NIFTY_CONSUMER_DURABLES': ['consumer durables', 'durables', 'appliances', 'whirlpool', 'voltas'],
    'NIFTY_INFRA': ['infrastructure', 'infra', 'construction', 'l&t', 'larsen'],
    'NIFTY_OIL_GAS': ['oil', 'gas', 'petroleum', 'ongc', 'oil india', 'gail'],
    'NIFTY_PSE': ['psu', 'public sector', 'government company', 'psu stocks'],
    'NIFTY_SERVICES': ['services', 'service sector'],
    'NIFTY_COMMODITIES': ['commodities', 'commodity', 'agriculture', 'agri'],
    # Thematic Indices
    'NIFTY_GROWTH_SECTORS_15': ['growth', 'growth stocks', 'growth sectors'],
    'NIFTY_DIVIDEND_OPPORTUNITIES_50': ['dividend', 'dividend yield', 'dividend stocks'],
    'NIFTY_QUALITY_30': ['quality', 'quality stocks', 'quality index'],
    'NIFTY_LOW_VOLATILITY_50': ['low volatility', 'low vol', 'stable stocks'],
    'NIFTY_ALPHA_50': ['alpha', 'alpha stocks', 'outperformance'],
    'NIFTY_HIGH_BETA_50': ['high beta', 'volatile', 'volatility'],
}

