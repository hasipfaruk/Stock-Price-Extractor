"""
Normalization and validation pipeline for extracted financial data
"""

from typing import Any, Optional, Dict


def normalize_numeric(value: Any) -> Optional[str]:
    """Normalize numeric values to string format"""
    if value is None or value == "":
        return None
    
    value_str = str(value).strip()
    if value_str.lower() in ['none', 'null', 'n/a', 'na']:
        return None
    
    return value_str


def normalize_percentage(value: Any) -> Optional[str]:
    """Normalize percentage values"""
    if value is None or value == "":
        return None
    
    value_str = str(value).strip()
    if value_str.lower() in ['none', 'null', 'n/a', 'na']:
        return None
    
    # Ensure it has % if needed
    if '%' not in value_str and value_str and value_str[0] in ['+', '-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
        value_str = value_str + '%'
    
    return value_str


def normalize_index_name(value: Any) -> Optional[str]:
    """Normalize index names"""
    if value is None or value == "":
        return None
    
    value_str = str(value).strip().upper()
    if value_str in ['NONE', 'NULL', 'N/A', 'NA']:
        return None
    
    return value_str


def _is_placeholder_value(value: Any) -> bool:
    """Check if a value is a placeholder that should be rejected"""
    if value is None:
        return False
    
    value_str = str(value).strip().upper()
    
    # List of placeholder patterns to detect
    placeholder_patterns = [
        'ACTUAL_INDEX_FROM_TRANSCRIPT',
        'ACTUAL_PRICE_FROM_TRANSCRIPT',
        'ACTUAL_CHANGE_OR_NULL',
        'ACTUAL_PERCENTAGE_OR_NULL',
        'ACTUAL_SESSION_OR_NULL',
        'EXTRACT THE ACTUAL',
        'EXTRACT FROM TRANSCRIPT',
        'INDEX @ PRICE CHANGE',
    ]
    
    for pattern in placeholder_patterns:
        if pattern in value_str:
            return True
    
    return False


def validate_and_normalize_extraction(extracted: Dict) -> Optional[Dict]:
    """
    Validate and normalize extracted financial data
    Ensures consistent output structure
    
    Args:
        extracted: Dictionary with extracted data
        
    Returns:
        Normalized and validated dictionary
    """
    if not extracted or not isinstance(extracted, dict):
        return None
    
    # Check for placeholder values - reject if found
    for key, value in extracted.items():
        if _is_placeholder_value(value):
            print(f"⚠️ Warning: Detected placeholder value in {key}: {value}")
            print("   This suggests the LLM copied example text instead of extracting real values.")
            # Set to None to force re-extraction or indicate error
            extracted[key] = None
    
    # Normalize all fields
    normalized = {
        'index_name': normalize_index_name(extracted.get('index_name')),
        'price': normalize_numeric(extracted.get('price')),
        'change': normalize_numeric(extracted.get('change')),
        'change_percent': normalize_percentage(extracted.get('change_percent')),
        'session': normalize_index_name(extracted.get('session')),
        'standardized_quote': str(extracted.get('standardized_quote', '')).strip() or None,
    }
    
    # Filter out None values for cleaner output
    return {k: v for k, v in normalized.items() if v is not None}
