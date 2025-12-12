"""Sector-wise ranking service for stock scoring."""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import numpy as np
from app.db import models
from app.config.ranking_config import get_ranking_config, SectorRankingConfig, MetricWeight
from app.utils import logger


def percentile(values: List[float], p: float) -> float:
    """Calculate percentile of a list of values."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * p
    f = int(k)
    c = k - f
    if f + 1 < len(sorted_vals):
        return sorted_vals[f] * (1 - c) + sorted_vals[f + 1] * c
    return sorted_vals[f]


def winsorize(values: List[float], p1: float = 0.01, p99: float = 0.99) -> List[float]:
    """Winsorize values at p1 and p99 percentiles."""
    if not values:
        return []
    low = percentile(values, p1)
    high = percentile(values, p99)
    return [max(low, min(high, v)) for v in values]


def min_max_normalize(values: List[float]) -> List[float]:
    """Min-max normalize values to [0, 1] range."""
    if not values:
        return []
    min_val = min(values)
    max_val = max(values)
    if min_val == max_val:
        return [0.5] * len(values)  # Neutral value when all same
    return [(v - min_val) / (max_val - min_val) for v in values]


def get_metric_value(row: Dict[str, Any], metric_key: str) -> Optional[float]:
    """Extract metric value from row, handling Decimal conversion."""
    value = row.get(metric_key)
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def compute_sector_ranked_stocks(
    db: Session,
    sector_key: str,
    limit: Optional[int] = None,
    sort_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compute ranked stocks for a sector based on weighted metrics.
    
    Args:
        db: Database session
        sector_key: Sector key (e.g., 'it', 'fmcg')
        limit: Maximum number of stocks to return
        sort_by: Optional field to sort by (defaults to score)
        
    Returns:
        Dictionary with rows, columns, and metadata
    """
    config = get_ranking_config(sector_key)
    
    # Map sector key to sector_id patterns
    sector_id_patterns = {
        "it": ["NIFTY_IT", "IT", "Information Technology"],
        "fmcg": ["NIFTY_FMCG", "FMCG", "Fast Moving Consumer Goods"],
        "pharma": ["NIFTY_PHARMA", "Pharmaceuticals", "Pharma"],
        "cement": ["Cement"],
        "chemicals": ["Chemicals"],
        "auto": ["NIFTY_AUTO", "Automobile", "Auto"],
        "banks": ["NIFTY_BANK", "Banks", "Banking", "NIFTY_PSU_BANK", "NIFTY_PRIVATE_BANK"],
        "nbfc": ["NBFC", "HFC", "Non-Banking Financial Company"],
        "insurance": ["Insurance"],
        "hospitals": ["Hospitals", "Healthcare Services"],
        "diagnostics": ["Diagnostics", "Diagnostic Services"],
        "real_estate": ["NIFTY_REALTY", "Real Estate", "Realty"],
        "metals": ["NIFTY_METAL", "Metals", "Mining"],
        "capital_goods": ["Capital Goods", "Engineering"],
        "defence": ["Defence", "Defense"],
        "infrastructure": ["NIFTY_INFRA", "Infrastructure"],
        "telecom": ["Telecom", "Telecommunications"],
        "agrochemicals": ["Agrochemicals"],
        "renewables": ["Renewable Energy", "Renewables"],
        "logistics": ["Logistics"],
        "consumer_durables": ["NIFTY_CONSUMER_DURABLES", "Consumer Durables"],
        "textiles": ["Textiles"],
        "retail": ["Retail"],
        "oil_gas": ["NIFTY_OIL_GAS", "Oil & Gas", "Oil and Gas"],
        "media": ["NIFTY_MEDIA", "Media", "Entertainment"],
    }
    
    sector_ids = sector_id_patterns.get(sector_key.lower(), [sector_key])
    
    # Get latest date for fundamentals
    latest_date = db.query(func.max(models.StockFundamentals.date)).scalar()
    if not latest_date:
        logger.warning(f"No fundamentals data found")
        return {
            "rows": [],
            "columns": config.columns,
            "meta": {
                "count": 0,
                "computed_at": datetime.utcnow().isoformat()
            }
        }
    
    # Query stocks with latest fundamentals
    query = db.query(
        models.Stock,
        models.StockFundamentals
    ).join(
        models.StockFundamentals,
        and_(
            models.Stock.ticker == models.StockFundamentals.ticker,
            models.StockFundamentals.date == latest_date
        )
    ).filter(
        models.Stock.sector_id.in_(sector_ids)
    )
    
    results = query.all()
    
    if not results:
        logger.warning(f"No stocks found for sector {sector_key}")
        return {
            "rows": [],
            "columns": config.columns,
            "meta": {
                "count": 0,
                "computed_at": datetime.utcnow().isoformat()
            }
        }
    
    # Convert to dictionaries
    rows = []
    for stock, fundamentals in results:
        row = {
            "ticker": stock.ticker,
            "company_name": stock.company_name,
            "sector_id": stock.sector_id,
        }
        
        # Add all fundamental metrics with proper field name mapping
        # Map config field names to database column names
        field_mapping = {
            "opm": "operating_margin",
            "gnpa": "gross_npa",
            "nnpa": "net_npa",
            "casa": "casa_ratio",
        }
        
        # Add all fundamental metrics
        for attr in dir(fundamentals):
            if not attr.startswith('_') and attr not in ['metadata', 'registry']:
                try:
                    value = getattr(fundamentals, attr)
                    if value is not None and isinstance(value, (int, float, Decimal)):
                        # Store with original database column name
                        row[attr] = float(value) if isinstance(value, Decimal) else value
                        # Also add mapped aliases for config compatibility
                        for config_name, db_name in field_mapping.items():
                            if attr == db_name:
                                row[config_name] = float(value) if isinstance(value, Decimal) else value
                except:
                    pass
        
        rows.append(row)
    
    if not rows:
        return {
            "rows": [],
            "columns": config.columns,
            "meta": {
                "count": 0,
                "computed_at": datetime.utcnow().isoformat()
            }
        }
    
    # Collect all metric values for normalization
    all_metrics = set()
    for metric in config.metrics.get("positive", []):
        all_metrics.add(metric.key)
    for metric in config.metrics.get("negative", []):
        all_metrics.add(metric.key)
    
    # Compute normalization for each metric
    metric_normalized: Dict[str, Dict[str, float]] = {}
    
    # Field name mapping for config -> database
    metric_field_mapping = {
        "opm": "operating_margin",
        "gnpa": "gross_npa",
        "nnpa": "net_npa",
        "casa": "casa_ratio",
    }
    
    for metric_key in all_metrics:
        # Map config metric key to database field name
        db_field_name = metric_field_mapping.get(metric_key, metric_key)
        
        # Extract values
        values = []
        value_map = {}  # ticker -> value
        
        for row in rows:
            # Try both the mapped name and original name
            value = get_metric_value(row, db_field_name) or get_metric_value(row, metric_key)
            if value is not None:
                values.append(value)
                value_map[row["ticker"]] = value
        
        if not values:
            # All NULL - use neutral value
            metric_normalized[metric_key] = {
                row["ticker"]: 0.5 for row in rows
            }
            continue
        
        # Calculate median for imputation
        try:
            import numpy as np
            HAS_NUMPY = True
        except ImportError:
            HAS_NUMPY = False
            np = None
        
        if HAS_NUMPY and values:
            median_val = float(np.median(values))
        elif values:
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            if n % 2 == 0:
                median_val = (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2.0
            else:
                median_val = float(sorted_vals[n//2])
        else:
            median_val = 0.0
        
        # Impute missing values with median
        for row in rows:
            if row["ticker"] not in value_map:
                value_map[row["ticker"]] = median_val
                values.append(median_val)
        
        # Winsorize
        winsorized = winsorize(values)
        
        # Normalize
        normalized = min_max_normalize(winsorized)
        
        # Store normalized values by ticker
        metric_normalized[metric_key] = {}
        for i, row in enumerate(rows):
            ticker = row["ticker"]
            if ticker in value_map:
                idx = list(value_map.keys()).index(ticker) if ticker in value_map else i
                if idx < len(normalized):
                    metric_normalized[metric_key][ticker] = normalized[idx]
                else:
                    metric_normalized[metric_key][ticker] = 0.5
            else:
                metric_normalized[metric_key][ticker] = 0.5
    
    # Compute scores
    positive_metrics = config.metrics.get("positive", [])
    negative_metrics = config.metrics.get("negative", [])
    
    # Normalize weights
    pos_weight_sum = sum(m.weight for m in positive_metrics) if positive_metrics else 1.0
    neg_weight_sum = sum(m.weight for m in negative_metrics) if negative_metrics else 1.0
    
    for row in rows:
        ticker = row["ticker"]
        
        # Positive score
        pos_score = 0.0
        for metric in positive_metrics:
            norm_val = metric_normalized.get(metric.key, {}).get(ticker, 0.5)
            weight = metric.weight / pos_weight_sum if pos_weight_sum > 0 else 0
            pos_score += weight * norm_val
        
        # Negative score (inverted)
        neg_score = 0.0
        for metric in negative_metrics:
            norm_val = metric_normalized.get(metric.key, {}).get(ticker, 0.5)
            # For negative metrics, invert: 1 - norm
            inverted_norm = 1.0 - norm_val
            weight = metric.weight / neg_weight_sum if neg_weight_sum > 0 else 0
            neg_score += weight * inverted_norm
        
        # Combined score: pos_score - (neg_score * 0.8) to scale negative effect
        raw_score = pos_score - (neg_score * 0.8)
        
        # Map to 0-100 range
        # raw_score is roughly in [-0.8, 1.0], map to [0, 100]
        score = max(0.0, min(100.0, ((raw_score + 0.8) / 1.8) * 100))
        row["score"] = round(score, 2)
    
    # DEFAULT: Always sort by score (best to worst)
    # Only use sort_by if explicitly provided and different from "score"
    if sort_by and sort_by != "score" and sort_by != "rank":
        # Sort by specified metric, but still include score for reference
        rows.sort(key=lambda r: get_metric_value(r, sort_by) or 0.0, reverse=True)
    else:
        # DEFAULT: Sort by score descending (best to worst)
        rows.sort(key=lambda r: r.get("score", 0.0), reverse=True)
    
    # Add rank
    for i, row in enumerate(rows):
        row["rank"] = i + 1
    
    # Apply limit
    if limit:
        rows = rows[:limit]
    
    return {
        "rows": rows,
        "columns": config.columns,
        "meta": {
            "count": len(rows),
            "computed_at": datetime.utcnow().isoformat()
        }
    }

