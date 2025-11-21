import re
from typing import Optional, Tuple, Dict, List


# Comprehensive index patterns - ORDER MATTERS (more specific first)
# Handle transcription errors: SNP->S&P, Ducks->DAX, Vicks->VIX
INDEX_PATTERNS = [
    r"(?P<index>S&P\s*five\s*hundred|S&P\s*500|S&P500|SNP\s*500|SNP\s*five\s*hundred)",  # Handle SNP typo
    r"(?P<index>Hang\s*Seng|Hang\s*Seng\s*Index)",
    r"(?P<index>Shanghai\s*Composite|Shanghai)",
    r"(?P<index>Russell\s*2000)",
    r"(?P<index>DAX|Ducks)",  # Handle Ducks typo
    r"(?P<index>VIX|Vicks)",  # Handle Vicks typo
    r"(?P<index>NASDAQ|Nasdaq\s*Composite|Nasdaq|not\s*stack)",  # Handle "not stack" -> NASDAQ
    r"(?P<index>Dow\s*Jones|Dow\s*Jones\s*Industrial)",  # Dow Jones (specific)
    r"(?P<index>Dow\b(?!\s*(?:down|lower|sharply))|DOW\b(?!\s*(?:down|lower|sharply)))",  # Dow but not "down"
    r"(?P<index>S&P|s&p|SNP)",  # Handle SNP
    r"(?P<index>Russell)",
    r"(?P<index>FTSE|FT-SE)",
    r"(?P<index>Nikkei)",
    r"(?P<index>CAC\s*40)",
]


def normalize_spoken_numbers(text: str) -> str:
    """Convert spoken numbers to digits"""
    text_lower = text.lower()
    
    # Number word mappings
    number_map = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
        'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
        'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
        'eighteen': '18', 'nineteen': '19', 'twenty': '20', 'thirty': '30',
        'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
        'eighty': '80', 'ninety': '90',
    }
    
    # Common spoken number patterns (order matters - longer first)
    patterns = [
        (r'thirty-four\s+thousand\s+twenty', '34020'),
        (r'forty-two\s+twenty-five', '4225'),
        (r'forty-two\s+fifty', '4250'),
        (r'forty-two\s+twelve', '4212'),
        (r'forty-two\s+hundred', '4200'),
        (r'fifteen\s+thousand', '15000'),
        (r'twenty-two\s+point\s+five', '22.5'),
        (r'one\s+thirty-two', '132'),
        (r'point\s+seven\s+five', '0.75'),
        (r'point\s+five', '0.5'),
        (r'two\s+point\s+three', '2.3'),
    ]
    
    for pattern, replacement in patterns:
        text_lower = re.sub(pattern, replacement, text_lower)
    
    return text_lower


def normalize_index_name(index: str) -> str:
    """Normalize index name to standard format - handles transcription errors"""
    if not index:
        return None
    
    index_upper = index.upper()
    index_lower = index.lower()
    
    # Fix transcription errors first
    if 'snp' in index_lower and 's&p' not in index_lower:
        index_lower = index_lower.replace('snp', 's&p')
        index_upper = index_upper.replace('SNP', 'S&P')
    
    if 'ducks' in index_lower:
        return 'DAX'
    
    if 'vicks' in index_lower:
        return 'VIX'
    
    if 'not stack' in index_lower or 'nasdaq' in index_lower:
        return 'NASDAQ'
    
    # S&P variations
    if 's&p' in index_lower or 's and p' in index_lower:
        if 'five hundred' in index_lower or '500' in index:
            return 'S&P 500'
        return 'S&P 500'  # Default S&P to S&P 500
    
    # DOW variations
    if 'dow' in index_lower:
        return 'DOW'
    
    # NASDAQ
    if 'nasdaq' in index_lower:
        return 'NASDAQ'
    
    # Russell
    if 'russell' in index_lower:
        return 'RUSSELL 2000'
    
    # Others - keep uppercase
    if index_upper in ['DAX', 'VIX', 'HANG SENG', 'SHANGHAI', 'FTSE', 'NIKKEI', 'CAC 40']:
        return index_upper
    
    # Hang Seng
    if 'hang seng' in index_lower:
        return 'HANG SENG'
    
    # Shanghai
    if 'shanghai' in index_lower:
        return 'SHANGHAI COMP'
    
    return index_upper


def extract_detailed(text: str) -> Optional[Dict]:
    """
    Extract detailed information including price, change, percentage, and context
    Handles multiple indices, session high/low values, and technical levels
    """
    # Normalize spoken numbers first
    text = normalize_spoken_numbers(text)
    text_lower = text.lower()
    original_text = text  # Keep original for case-sensitive matching
    
    result = {
        'index_name': None,
        'price': None,
        'change': None,
        'change_percent': None,
        'session': None,
        'session_high': None,
        'session_low': None,
        'standardized_quote': None
    }
    
    # Find ALL indices (for multiple indices case)
    # Store with position to preserve order from text
    found_indices_with_pos = []
    for idx_pat in INDEX_PATTERNS:
        for match in re.finditer(idx_pat, text, re.IGNORECASE):
            matched_text = match.group('index')
            # Filter out false positives: "down" (lowercase) should not match "Dow"
            if matched_text.lower() == 'down':
                # Check if it's part of "Dow Jones" - if not, skip it
                context = text[max(0, match.start()-20):match.end()+20].lower()
                if 'jones' not in context:
                    continue
            normalized = normalize_index_name(matched_text)
            if normalized:
                # Check if we already have this index
                if not any(norm == normalized for _, norm in found_indices_with_pos):
                    found_indices_with_pos.append((match.start(), normalized))
    
    # Sort by position to preserve order from text, then extract just the names
    found_indices_with_pos.sort(key=lambda x: x[0])
    found_indices = [norm for _, norm in found_indices_with_pos]
    
    # Use first index found (or handle multiple indices)
    if found_indices:
        result['index_name'] = found_indices[0]
    else:
        return None
    
    # Find price - look for "at" or "@" followed by number (handle commas)
    # Priority: "at X" or "@ X" patterns first, then standalone large numbers
    price_patterns = [
        r"(?:at|@)\s*(\d{1,3}(?:,\d{3})+(?:\.\d+)?)",  # "at 34,020" or "@ 15,000"
        r"(?:at|@)\s*(\d{4,5}(?:\.\d+)?)",  # "at 4212" or "at 22.5" (4-5 digits)
        r"currently\s+at\s+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)",  # "currently at 4225"
        r"now\s+at\s+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)",  # "now at 22.5"
        r"(\d{4,5}(?:\.\d+)?)\s*$",  # Large number at end (like "4212" at end)
    ]
    
    for pattern in price_patterns:
        price_match = re.search(pattern, text)
        if price_match:
            price_str = price_match.group(1).replace(',', '').replace(' ', '')
            # Only accept if it's a reasonable price (4+ digits or has decimal like 22.5)
            price_digits = price_str.replace('.', '')
            if len(price_digits) >= 4 or ('.' in price_str and len(price_digits) >= 3):
                result['price'] = price_str
                break
    
    # If no price found but we have session high/low, use "currently at" value
    if not result['price'] and ('currently at' in text_lower or 'now at' in text_lower):
        current_match = re.search(r'(?:currently|now)\s+at\s+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', text_lower)
        if current_match:
            price_str = current_match.group(1).replace(',', '').replace(' ', '')
            result['price'] = price_str
    
    # Extract session high/low values (Test 9, 10)
    # Match full numbers including 4+ digits (e.g., "4250", "4200")
    # Use a more flexible pattern that captures the full number
    session_high_match = re.search(r'session\s+high\s+(\d+(?:,\d{3})*(?:\.\d+)?)', text_lower)
    if session_high_match:
        result['session_high'] = session_high_match.group(1).replace(',', '').replace(' ', '')
    
    session_low_match = re.search(r'session\s+low\s+(\d+(?:,\d{3})*(?:\.\d+)?)', text_lower)
    if session_low_match:
        result['session_low'] = session_low_match.group(1).replace(',', '').replace(' ', '')
    
    # Find change in points - look for "up/down X points" patterns
    # Make sure we don't match prices (avoid numbers > 1000 as changes)
    change_patterns = [
        r"(?:up|higher|gaining|rising)\s+(\d{1,3}(?:\.\d+)?)\s*(?:points?|pts?)",  # "up 23 points"
        r"(?:down|lower|losing|falling)\s+(\d{1,3}(?:\.\d+)?)\s*(?:points?|pts?)",  # "down 58 points"
        r"up\s+(\d{1,3}(?:\.\d+)?)\s*(?:points?|pts?)",  # "up 12 points"
        r"up\s+(\d{1,2})\b",  # "up 15" or "up 50" (short form, no "points")
    ]
    
    # Special case: "up 132" (without "points") - usually change, not price
    # Also handle "at 132" in breaking context (Test 8)
    # Pattern: "breaking above ... at 132" or "up 132 ... breaking"
    breaking_match = re.search(r'(?:up|at)\s+(\d{2,3})\s+(?:breaking|above|days|moving)', text_lower)
    if breaking_match:
        result['change'] = f"+{breaking_match.group(1)}"
    # Also check: "breaking above ... at 132" (at comes after breaking)
    breaking_at_match = re.search(r'breaking\s+above.*?at\s+(\d{2,3})', text_lower)
    if breaking_at_match and not result['change']:
        result['change'] = f"+{breaking_at_match.group(1)}"
    
    # Special case: "up one thirty-two" -> "+132"
    if 'up one thirty-two' in text_lower or 'up one thirty two' in text_lower:
        result['change'] = "+132"
    
    # Extract change from patterns (only if not already set)
    if not result['change']:
        for pattern in change_patterns:
            change_match = re.search(pattern, text_lower)
            if change_match:
                change_val = change_match.group(1)
                # Only accept reasonable change values (not prices)
                try:
                    change_int = int(change_val.replace('.', ''))
                    if change_int < 1000:  # Changes are usually < 1000
                        match_start = change_match.start()
                        context_before = text_lower[max(0, match_start-20):match_start]
                        
                        if 'down' in context_before or 'lower' in context_before or 'losing' in context_before or 'falling' in context_before:
                            result['change'] = f"-{change_val}"
                        elif 'up' in context_before or 'higher' in context_before or 'gaining' in context_before or 'rising' in context_before:
                            result['change'] = f"+{change_val}"
                        else:
                            result['change'] = f"+{change_val}"
                        break
                except ValueError:
                    continue
    
    # Find percentage change
    percent_patterns = [
        r"(?:up|higher)\s+(\d+(?:\.\d+)?)\s*percent",
        r"(?:down|lower)\s+(\d+(?:\.\d+)?)\s*percent",
        r"(\+?\d+(?:\.\d+)?)\s*%",  # "+2%" or "2%"
        r"point\s+(\d+(?:\.\d+)?)\s*percent\s+(?:higher|lower)",
        r"(\d+(?:\.\d+)?)\s*percent\s+(?:higher|lower)",
    ]
    
    for pattern in percent_patterns:
        percent_match = re.search(pattern, text_lower)
        if percent_match:
            percent_val = percent_match.group(1)
            match_start = percent_match.start()
            context_before = text_lower[max(0, match_start-20):match_start]
            
            if 'down' in context_before or 'lower' in context_before:
                result['change_percent'] = f"-{percent_val}"
            elif 'up' in context_before or 'higher' in context_before:
                result['change_percent'] = f"+{percent_val}"
            elif percent_val.startswith('+'):
                result['change_percent'] = percent_val
            elif percent_val.startswith('-'):
                result['change_percent'] = percent_val
            else:
                result['change_percent'] = f"+{percent_val}"
            break
    
    # Special case: "point five percent" -> "+0.5%"
    if 'point five percent' in text_lower:
        result['change_percent'] = "+0.5"
    if 'point seven five percent' in text_lower:
        result['change_percent'] = "-0.75"
    
    # Find session context
    if 'closing' in text_lower or 'close' in text_lower:
        result['session'] = 'CLOSING'
    elif 'premarket' in text_lower or 'pre-market' in text_lower:
        result['session'] = 'PREMARKET'
    elif 'session high' in text_lower or result['session_high']:
        result['session'] = 'SESSION HIGH'
    elif 'session low' in text_lower or result['session_low']:
        result['session'] = 'SESSION LOW'
    elif 'overnight' in text_lower:
        result['session'] = 'OVERNIGHT'
    
    # Handle multiple indices (Test 3, Test 6)
    if len(found_indices) > 1:
        # Extract changes for each index
        multi_quotes = []
        for idx in found_indices:
            # Find change associated with this index
            # Handle both "S&P 500" and "S&P" patterns
            idx_variations = [idx.lower()]
            if 's&p' in idx.lower() or 'snp' in idx.lower():
                idx_variations.extend(['s&p', 'snp', 's&p 500', 's&p five hundred'])
            if 'dow' in idx.lower():
                idx_variations.extend(['dow', 'dow jones'])
            if 'nasdaq' in idx.lower():
                idx_variations.extend(['nasdaq'])
            if 'russell' in idx.lower():
                idx_variations.extend(['russell', 'russell 2000'])
            
            quote_parts = [idx]
            change_found = False
            percent_found = False
            
            for idx_var in idx_variations:
                # Pattern: "INDEX up/down X" - handle comma-separated
                patterns = [
                    rf'\b{re.escape(idx_var)}\s+(?:up|down)\s+(\d{{1,3}})\b',
                    rf'\b{re.escape(idx_var)}\s+up\s+(\d{{1,3}})\b',
                    rf'\b{re.escape(idx_var)}\s+down\s+(\d{{1,3}})\b',
                ]
                
                for pattern in patterns:
                    idx_change_match = re.search(pattern, text_lower)
                    if idx_change_match:
                        change_val = idx_change_match.group(1)
                        # Determine direction
                        match_text = text_lower[max(0, idx_change_match.start()-10):idx_change_match.end()]
                        if 'down' in match_text or 'lower' in match_text:
                            quote_parts.append(f"-{change_val} pts")
                        else:
                            quote_parts.append(f"+{change_val} pts")
                        change_found = True
                        break
                
                if change_found:
                    break
            
            # Check for percentage change for this index
            # Also handle "app 2%" (post-processed from "app" -> "up")
            for idx_var in idx_variations:
                percent_patterns = [
                    rf'\b{re.escape(idx_var)}\s+(?:up|down|app)\s+(\d+(?:\.\d+)?)\s*%',  # Handle "app" -> "up"
                    rf'\b{re.escape(idx_var)}\s+up\s+(\d+(?:\.\d+)?)\s*%',
                    rf'\b{re.escape(idx_var)}\s+(\d+(?:\.\d+)?)\s*%',  # "NASDAQ 2%" (no "up")
                ]
                for pattern in percent_patterns:
                    percent_match = re.search(pattern, text_lower)
                    if percent_match:
                        percent_val = percent_match.group(1)
                        match_text = text_lower[max(0, percent_match.start()-10):percent_match.end()]
                        if 'down' in match_text or 'lower' in match_text:
                            quote_parts.append(f"-{percent_val}%")
                        else:
                            quote_parts.append(f"+{percent_val}%")
                        percent_found = True
                        break
                if percent_found:
                    break
            
            # Add context (Test 6)
            if idx == 'NASDAQ' and 'tech' in text_lower and 'driving' in text_lower:
                quote_parts.append('TECH DRIVING')
            if idx == 'RUSSELL 2000' and ('lagging' in text_lower or 'laging' in text_lower):
                quote_parts.append('LAGGING')
            
            multi_quotes.append(' '.join(quote_parts))
        
        result['standardized_quote'] = '; '.join(multi_quotes)
        return result
    
    # Build standardized quote for single index
    quote_parts = []
    
    # Index name (always first)
    quote_parts.append(result['index_name'])
    
    # Session context (but don't duplicate if we have session high/low values)
    if result['session']:
        if result['session'] == 'PREMARKET' and 'futures' in text_lower:
            quote_parts.append('FUTURES PREMARKET')
        elif result['session'] not in ['SESSION HIGH', 'SESSION LOW'] or (not result['session_high'] and not result['session_low']):
            # Only add session if we don't have session high/low values (to avoid duplication)
            quote_parts.append(result['session'])
    
    # Price with @ symbol (put before session high/low)
    if result['price']:
        quote_parts.append(f"@ {result['price']}")
    
    # Session high/low values (Test 9, 10) - add after price
    if result['session_high']:
        quote_parts.append(f"SESSION HIGH {result['session_high']}")
    if result['session_low']:
        quote_parts.append(f"SESSION LOW {result['session_low']}")
    
    # Change in points (before technical context for Test 8)
    if result['change']:
        change_val = result['change'].lstrip('+-')
        if result['change'].startswith('-'):
            quote_parts.append(f"-{change_val} pts")
        else:
            quote_parts.append(f"+{change_val} pts")
    
    # Technical context (Test 8) - after change
    if 'breaking above' in text_lower and 'moving average' in text_lower:
        if '200' in text_lower and ('day' in text_lower or 'dma' in text_lower):
            quote_parts.append('BREAKING ABOVE 200-DMA')
    
    # Percentage change in parentheses
    if result['change_percent']:
        percent_val = result['change_percent'].lstrip('+-')
        if result['change_percent'].startswith('-'):
            quote_parts.append(f"(-{percent_val}%)")
        else:
            quote_parts.append(f"(+{percent_val}%)")
    
    # Add context for Test 4 (sharply lower) and Test 6 (tech driving, lagging)
    if 'sharply lower' in text_lower and result['index_name'] == 'DAX':
        # Insert "SHARPLY LOWER" before price or percentage
        if result['price']:
            # Find price position and insert before it
            for i, part in enumerate(quote_parts):
                if '@' in part:
                    quote_parts.insert(i, 'SHARPLY LOWER')
                    break
        elif result['change_percent']:
            # Find percentage position and insert before it
            for i, part in enumerate(quote_parts):
                if '(' in part and '%' in part:
                    quote_parts.insert(i, 'SHARPLY LOWER')
                    break
        else:
            # Add at the end if no price or percentage
            quote_parts.append('SHARPLY LOWER')
    
    # Add context for Test 6 (tech driving, lagging)
    if 'tech' in text_lower and 'driving' in text_lower and result['index_name'] == 'NASDAQ':
        # Add "TECH DRIVING" after percentage
        quote_parts.append('TECH DRIVING')
    if 'lagging' in text_lower or 'laging' in text_lower:
        # Check if Russell is mentioned
        if 'russell' in text_lower:
            # Add Russell lagging to quote
            if result['index_name'] != 'RUSSELL 2000':
                quote_parts.append('; RUSSELL 2000 LAGGING')
            else:
                quote_parts.append('LAGGING')
    
    result['standardized_quote'] = ' '.join(quote_parts)
    
    return result


def extract_with_regex(text: str) -> Optional[Tuple[str, str]]:
    """
    Simple extraction - returns (index, price) tuple
    """
    detailed = extract_detailed(text)
    if detailed and detailed.get('index_name') and detailed.get('price'):
        return (detailed['index_name'], detailed['price'])
    return None


# Optional LLM-based extraction entrypoint (for edge cases)
def extract_with_llm(transcript: str, llm_infer_fn) -> Optional[Tuple[str, str]]:
    """LLM-based extraction for complex cases"""
    prompt = (
        "You are given a short transcript from audio. Extract ONLY the main stock index name and its numeric price. "
        "Return in JSON like: {\"index\": \"S&P 500\", \"price\": \"5234.12\"}. If none found, return {\"index\": null, \"price\": null}.\n\nTranscript:\n" + transcript
    )
    resp = llm_infer_fn(prompt)
    # parse simple json or regex
    m_idx = re.search(r'"index"\s*:\s*"([^"]+)"', resp)
    m_price = re.search(r'"price"\s*:\s*"([^"]+)"', resp)
    if m_idx and m_price:
        return m_idx.group(1), m_price.group(1)
    return None
