"""Derivatives sentiment computation service."""
from typing import Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from app.db import crud, models
from app.utils import logger


def compute_derivatives_sentiment(
    db: Session,
    sector_id: str,
    target_date: date
) -> Dict[str, Any]:
    """
    Compute derivatives sentiment label based on PCR, OI changes, and IV.
    
    Labels:
    - "Bullish": Low PCR (<0.7), increasing OI, low IV
    - "Hedging": Moderate PCR (0.7-1.2), stable OI, moderate IV
    - "Complacent": Low PCR, low IV, decreasing OI
    - "High Fear": High PCR (>1.3), high IV, increasing OI
    
    Args:
        db: Database session
        sector_id: Sector identifier
        target_date: Target date for computation
        
    Returns:
        Dictionary with label, pcr_oi, oi_change_1d, and explanation
    """
    # Map sector to underlying - same mapping as features.py
    sector_to_underlying = {
        # Broad Market - use NIFTY
        'NIFTY_50': 'NIFTY',
        'NIFTY_NEXT_50': 'NIFTY',
        'NIFTY_100': 'NIFTY',
        'NIFTY_200': 'NIFTY',
        'NIFTY_500': 'NIFTY',
        'NIFTY_MIDCAP_50': 'NIFTY',
        'NIFTY_MIDCAP_100': 'NIFTY',
        'NIFTY_MIDCAP_150': 'NIFTY',
        'NIFTY_SMALLCAP_50': 'NIFTY',
        'NIFTY_SMALLCAP_100': 'NIFTY',
        'NIFTY_SMALLCAP_250': 'NIFTY',
        # Banking indices - use BANKNIFTY
        'NIFTY_BANK': 'BANKNIFTY',
        'NIFTY_PSU_BANK': 'BANKNIFTY',
        'NIFTY_PRIVATE_BANK': 'BANKNIFTY',
        'NIFTY_FIN_SERVICE': 'BANKNIFTY',
        # Other sectoral indices - use NIFTY
        'NIFTY_IT': 'NIFTY',
        'NIFTY_FMCG': 'NIFTY',
        'NIFTY_PHARMA': 'NIFTY',
        'NIFTY_AUTO': 'NIFTY',
        'NIFTY_ENERGY': 'NIFTY',
        'NIFTY_METAL': 'NIFTY',
        'NIFTY_REALTY': 'NIFTY',
        'NIFTY_HEALTHCARE': 'NIFTY',
        'NIFTY_CONSUMER_DURABLES': 'NIFTY',
        'NIFTY_INFRA': 'NIFTY',
        'NIFTY_OIL_GAS': 'NIFTY',
        'NIFTY_PSE': 'NIFTY',
        'NIFTY_SERVICES': 'NIFTY',
        'NIFTY_COMMODITIES': 'NIFTY',
        # Thematic indices - use NIFTY
        'NIFTY_GROWTH_SECTORS_15': 'NIFTY',
        'NIFTY_DIVIDEND_OPPORTUNITIES_50': 'NIFTY',
        'NIFTY_QUALITY_30': 'NIFTY',
        'NIFTY_LOW_VOLATILITY_50': 'NIFTY',
        'NIFTY_ALPHA_50': 'NIFTY',
        'NIFTY_HIGH_BETA_50': 'NIFTY',
    }
    underlying = sector_to_underlying.get(sector_id, 'NIFTY')
    
    # Get options data
    options_data = crud.get_options_daily(db, underlying, target_date)
    
    if not options_data:
        return {
            "label": "N/A",
            "pcr_oi": None,
            "oi_change_1d": None,
            "iv_index": None,
            "explanation": "No options data available"
        }
    
    pcr_oi = options_data.pcr_oi
    oi_change_1d = options_data.oi_change_1d
    iv_index = options_data.iv_index
    
    if pcr_oi is None:
        return {
            "label": "N/A",
            "pcr_oi": None,
            "oi_change_1d": oi_change_1d,
            "iv_index": iv_index,
            "explanation": "Incomplete options data"
        }
    
    # Determine sentiment label
    label = "Neutral"
    explanation_parts = []
    
    # PCR-based signals
    if pcr_oi < 0.7:
        explanation_parts.append("Low PCR (bullish)")
        if iv_index and iv_index < 0.15:  # Low IV
            if oi_change_1d and oi_change_1d > 5:
                label = "Bullish"
                explanation_parts.append("increasing OI")
            elif oi_change_1d and oi_change_1d < -5:
                label = "Complacent"
                explanation_parts.append("decreasing OI")
            else:
                label = "Bullish"
        else:
            label = "Bullish"
    elif pcr_oi > 1.3:
        explanation_parts.append("High PCR (bearish)")
        if iv_index and iv_index > 0.25:  # High IV
            if oi_change_1d and oi_change_1d > 5:
                label = "High Fear"
                explanation_parts.append("high IV + increasing OI")
            else:
                label = "Bearish"
        else:
            label = "Bearish"
    else:
        # Moderate PCR (0.7-1.2)
        if iv_index and 0.15 <= iv_index <= 0.25:
            label = "Hedging"
            explanation_parts.append("moderate PCR + moderate IV")
        else:
            label = "Neutral"
            explanation_parts.append("balanced PCR")
    
    # Add OI context
    if oi_change_1d:
        if oi_change_1d > 10:
            explanation_parts.append(f"OI +{oi_change_1d:.1f}%")
        elif oi_change_1d < -10:
            explanation_parts.append(f"OI {oi_change_1d:.1f}%")
    
    # Add IV context
    if iv_index:
        if iv_index > 0.25:
            explanation_parts.append(f"High IV ({iv_index*100:.1f}%)")
        elif iv_index < 0.15:
            explanation_parts.append(f"Low IV ({iv_index*100:.1f}%)")
    
    explanation = ", ".join(explanation_parts) if explanation_parts else "Neutral options positioning"
    
    return {
        "label": label,
        "pcr_oi": float(pcr_oi),
        "oi_change_1d": float(oi_change_1d) if oi_change_1d else None,
        "iv_index": float(iv_index) if iv_index else None,
        "explanation": explanation
    }

