"""Utility functions for formatting and rounding financial values."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Union, Optional


def round_to_2_decimal(value: Optional[Union[float, Decimal, int]]) -> Optional[float]:
    """
    Round a value to 2 decimal places with proper handling of None.
    
    Args:
        value: Value to round (float, Decimal, int, or None)
        
    Returns:
        Rounded float with 2 decimal places, or None if input is None
    """
    if value is None:
        return None
    
    if isinstance(value, Decimal):
        return float(value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    
    return None


def round_to_int(value: Optional[Union[float, Decimal, int]]) -> Optional[int]:
    """
    Round a value to integer with proper handling of None.
    
    Args:
        value: Value to round
        
    Returns:
        Rounded integer, or None if input is None
    """
    if value is None:
        return None
    
    if isinstance(value, Decimal):
        return int(value.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    
    if isinstance(value, (int, float)):
        return int(round(float(value)))
    
    return None


def safe_divide(numerator: Union[float, Decimal, int], 
                denominator: Union[float, Decimal, int],
                default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if denominator is zero
        
    Returns:
        Division result rounded to 2 decimals, or default
    """
    try:
        num = float(numerator) if numerator is not None else 0.0
        den = float(denominator) if denominator is not None else 0.0
        
        if den == 0:
            return round_to_2_decimal(default) or 0.0
        
        result = num / den
        return round_to_2_decimal(result) or 0.0
    except (TypeError, ValueError):
        return round_to_2_decimal(default) or 0.0

