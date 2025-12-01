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
        'PRICE INFORMATION FROM TRANSCRIPTS',
        'INFORMATION FROM TRANSCRIPTS',
        'THE STOCK INDEX NAME MENTIONED',
        'THE CHANGE IN POINTS MENTIONED',
        'THE PERCENTAGE CHANGE MENTIONED',
        'THE TRADING SESSION CONTEXT MENTIONED',
        'MENTIONED IN THE TRANSCRIPT',
        'FROM THE TRANSCRIPT',
        'IN THE TRANSCRIPT',
        'THE TRANSCRIPT',
    ]
    
    # Check for instruction-like text (contains multiple instruction keywords)
    instruction_keywords = ['MENTIONED', 'TRANSCRIPT', 'EXTRACT', 'INFORMATION', 'CONTEXT']
    keyword_count = sum(1 for keyword in instruction_keywords if keyword in value_str)
    
    # If value contains 2+ instruction keywords, it's likely instruction text
    if keyword_count >= 2:
        return True
    
    # Check for specific placeholder patterns
    for pattern in placeholder_patterns:
        if pattern in value_str:
            return True
    
    # Check if value looks like a sentence/instruction rather than data
    if len(value_str) > 30 and any(word in value_str for word in ['THE', 'FROM', 'IN', 'MENTIONED', 'EXTRACT']):
        # Likely instruction text if it's long and contains instruction words
        return True
    
    return False


def _normalize_number(value: Any) -> Optional[float]:
    """Convert value to number (float) or return None"""
    if value is None or value == "":
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    value_str = str(value).strip()
    if value_str.lower() in ['none', 'null', 'n/a', 'na', '']:
        return None
    
    # Remove +, -, %, and other non-numeric characters except decimal point
    cleaned = value_str.replace('+', '').replace('-', '').replace('%', '').replace(',', '').strip()
    
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _normalize_market_direction(value: Any) -> Optional[str]:
    """Normalize market direction to 'up', 'down', or 'flat'"""
    if value is None:
        return None
    
    value_str = str(value).strip().lower()
    
    if any(word in value_str for word in ['up', 'higher', 'gaining', 'advancing', 'rallying', 'positive']):
        return 'up'
    elif any(word in value_str for word in ['down', 'lower', 'falling', 'declining', 'negative']):
        return 'down'
    elif any(word in value_str for word in ['flat', 'unchanged', 'little changed', 'barely']):
        return 'flat'
    
    return None


def _normalize_session_context(value: Any) -> Optional[str]:
    """Normalize session context to lowercase standard format"""
    if value is None:
        return None
    
    value_str = str(value).strip().lower()
    
    # Map to standard session names
    session_map = {
        'opening': 'opening',
        'open': 'opening',
        'midday': 'midday',
        'noon': 'midday',
        'closing': 'closing',
        'close': 'closing',
        'premarket': 'premarket',
        'pre-market': 'premarket',
        'afterhours': 'afterhours',
        'after hours': 'afterhours',
        'overnight': 'overnight',
    }
    
    for key, normalized in session_map.items():
        if key in value_str:
            return normalized
    
    return value_str if value_str else None


def validate_and_normalize_extraction(extracted: Dict, transcript: str = None) -> Optional[Dict]:
    """
    Validate and normalize extracted financial data
    Ensures consistent output structure matching client requirements
    
    Args:
        extracted: Dictionary with extracted data
        transcript: Original transcript text (optional, for full_transcription field)
        
    Returns:
        Normalized and validated dictionary with client-required format
    """
    if not extracted or not isinstance(extracted, dict):
        return None
    
    # Check for placeholder values - reject if found
    placeholder_fields = []
    for key, value in extracted.items():
        if key == 'quote_analysis' and isinstance(value, dict):
            # Check nested quote_analysis fields
            for sub_key, sub_value in value.items():
                if _is_placeholder_value(sub_value):
                    print(f"⚠️ Warning: Detected placeholder value in {key}.{sub_key}: {sub_value}")
                    placeholder_fields.append(f"{key}.{sub_key}")
        elif _is_placeholder_value(value):
            print(f"⚠️ Warning: Detected placeholder value in {key}: {value}")
            print("   This suggests the LLM copied instruction text instead of extracting real values.")
            placeholder_fields.append(key)
    
    # If too many placeholder values detected, reject the entire extraction
    if len(placeholder_fields) >= 3:
        print(f"❌ Error: Too many placeholder values detected in fields: {placeholder_fields}")
        print("   The LLM copied instruction text instead of extracting from transcript.")
        return None
    
    # Build normalized output matching working code format
    # Always use the provided transcript (most accurate)
    normalized = {
        'full_transcription': transcript or extracted.get('full_transcription') or '',
        'standardized_quote': extracted.get('standardized_quote'),  # Can be None
        'index_name': normalize_index_name(extracted.get('index_name')),  # Can be None
    }
    
    # Handle quote_analysis object - preserve structure from extraction
    quote_analysis = extracted.get('quote_analysis', {})
    if not isinstance(quote_analysis, dict):
        quote_analysis = {}
    
    # Ensure all required fields exist (matching working code)
    normalized['quote_analysis'] = {
        'current_price': _normalize_number(quote_analysis.get('current_price')),
        'change_points': _normalize_number(quote_analysis.get('change_points')),
        'change_percent': _normalize_number(quote_analysis.get('change_percent')),
        'intraday_high': _normalize_number(quote_analysis.get('intraday_high')),
        'intraday_low': _normalize_number(quote_analysis.get('intraday_low')),
        'market_direction': _normalize_market_direction(quote_analysis.get('market_direction')),
        'session_context': _normalize_session_context(quote_analysis.get('session_context')),
    }
    
    # Ensure full_transcription is set (matching working code)
    if not normalized['full_transcription'] and transcript:
        normalized['full_transcription'] = transcript
    
    return normalized
