"""
Post-processing to fix common transcription errors
"""

import re


def fix_transcription_errors(text: str) -> str:
    """
    Fix common transcription errors from STT
    
    Common errors:
    - "SNP" -> "S&P"
    - "Ducks" -> "DAX"
    - "Vicks" -> "VIX"
    - "not stack" -> "NASDAQ"
    - "Tau" -> "Dow" (when followed by "Jones")
    - "up15" -> "up 15"
    - "up50,000,000" -> "up 50" (fix large number errors)
    """
    # Fix S&P errors
    text = re.sub(r'\bSNP\s*500\b', 'S&P 500', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSNP\s*five\s*hundred\b', 'S&P 500', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSNP\b', 'S&P', text, flags=re.IGNORECASE)
    
    # Fix DAX errors
    text = re.sub(r'\bDucks\b', 'DAX', text, flags=re.IGNORECASE)
    text = re.sub(r'\bDucks\s+sharply\b', 'DAX sharply', text, flags=re.IGNORECASE)
    
    # Fix VIX errors
    text = re.sub(r'\bVicks\b', 'VIX', text, flags=re.IGNORECASE)
    
    # Fix NASDAQ errors
    text = re.sub(r'\bnot\s+stack\b', 'NASDAQ', text, flags=re.IGNORECASE)
    
    # Fix "Tau Jones" -> "Dow Jones"
    text = re.sub(r'\bTau\s+Jones\b', 'Dow Jones', text, flags=re.IGNORECASE)
    
    # Fix "up15" -> "up 15" (missing space)
    text = re.sub(r'\bup(\d+)\b', r'up \1', text, flags=re.IGNORECASE)
    text = re.sub(r'\bdown(\d+)\b', r'down \1', text, flags=re.IGNORECASE)
    
    # Fix large number errors like "up50,000,000" -> "up 50"
    # This happens when STT mishears "fifty" as "50,000,000"
    # Pattern: "up" followed by very large number (6+ digits with commas)
    text = re.sub(r'\bup\s+(\d{1,2}),\d{3,}(?:,\d{3})*\b', r'up \1', text, flags=re.IGNORECASE)
    text = re.sub(r'\bdown\s+(\d{1,2}),\d{3,}(?:,\d{3})*\b', r'down \1', text, flags=re.IGNORECASE)
    
    # Fix "app" -> "up" when followed by percentage (e.g., "NASDAQ app 2%")
    text = re.sub(r'\bapp\s+(\d+)\s*%\b', r'up \1%', text, flags=re.IGNORECASE)
    
    # Fix number formatting
    # "34,020" -> keep as is
    # "40 to 5" -> might be "4250" or "425"
    text = re.sub(r'(\d+)\s+to\s+(\d+)', r'\1\2', text)  # "40 to 5" -> "405" (context dependent)
    
    # Fix "Session Law" -> "Session Low"
    text = re.sub(r'Session\s+Law', 'Session Low', text, flags=re.IGNORECASE)
    
    # Fix "Laging" -> "lagging"
    text = re.sub(r'\bLaging\b', 'lagging', text, flags=re.IGNORECASE)
    
    return text

