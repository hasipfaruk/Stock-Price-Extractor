import re
from typing import Optional, Tuple


# robust regex for common index names
INDEX_PATTERNS = [
r"(?P<index>S&P\s*500|S&P500|S&P)\b",
r"(?P<index>Nasdaq Composite|Nasdaq)\b",
r"(?P<index>Dow Jones|Dow)\b",
r"(?P<index>Russell 2000|Russell)\b",
]


PRICE_PATTERN = r"(?P<price>\d{1,3}(?:[\.,]\d{1,2})?)"


def extract_with_regex(text: str) -> Optional[Tuple[str,str]]:
    # Try to find index + numeric price near it
    for idx_pat in INDEX_PATTERNS:
        combined = idx_pat + r"[\s\S]{0,40}?" + PRICE_PATTERN
        m = re.search(combined, text, re.IGNORECASE)
        if m:
            index_name = m.group('index')
            price_raw = m.group('price').replace(',', '.')
            # normalize
            return index_name, price_raw
    
    # fallback: find first numeric and first capitalized word
    m = re.search(PRICE_PATTERN, text)
    if m:
        price = m.group('price').replace(',', '.')
        # try to get preceding token for index name
        tokens = text.split()
        return "UnknownIndex", price
    return None


# Optional LLM-based extraction entrypoint (for edge cases)
def extract_with_llm(transcript: str, llm_infer_fn) -> Optional[Tuple[str,str]]:
    # llm_infer_fn should accept a prompt and return text
    prompt = (
        "You are given a short transcript from audio. Extract ONLY the main stock index name and its numeric price. "
        "Return in JSON like: {\"index\": \"S&P 500\", \"price\": \"5234.12\"}. If none found, return {\"index\": null, \"price\": null}.\n\nTranscript:\n"+transcript
    )
    resp = llm_infer_fn(prompt)
    # parse simple json or regex
    m_idx = re.search(r'"index"\s*:\s*"([^"]+)"', resp)
    m_price = re.search(r'"price"\s*:\s*"([^"]+)"', resp)
    if m_idx and m_price:
        return m_idx.group(1), m_price.group(1)
    return None