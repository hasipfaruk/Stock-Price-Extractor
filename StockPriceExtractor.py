"""
Stock Index Price Extractor - Python Library
Use this as a library in your own Python projects
Extracts stock index prices from any audio source
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.models.transcribe import transcribe
from app.models.extract import extract_with_regex


class StockPriceExtractor:
    """
    Main class for extracting stock prices from audio recordings
    
    Usage:
        extractor = StockPriceExtractor()
        result = extractor.extract("audio.wav")
        print(result['index'], result['price'])
    """
    
    def __init__(self):
        """Initialize the extractor (models loaded on first use)"""
        pass
    
    def extract(self, audio_path: str, return_transcript: bool = True) -> Dict:
        """
        Extract stock price from audio file
        
        Args:
            audio_path: Path to audio file
            return_transcript: Whether to include transcript in result
            
        Returns:
            Dictionary with keys:
                - index: Stock index name (str or None)
                - price: Price value (str or None)
                - transcript: Transcribed text (str, if return_transcript=True)
                - timing: Processing time info (dict)
        """
        # Transcribe
        trans_result = transcribe(audio_path)
        
        if isinstance(trans_result, dict):
            transcript = trans_result['result']
            trans_time = trans_result.get('time', None)
        else:
            transcript = trans_result
            trans_time = None
        
        if not transcript:
            raise ValueError("Failed to transcribe audio")
        
        # Extract price
        extraction = extract_with_regex(transcript)
        
        if extraction:
            index, price = extraction
        else:
            index, price = None, None
        
        result = {
            'index': index,
            'price': price,
            'timing': {'transcription_s': trans_time} if trans_time else {}
        }
        
        if return_transcript:
            result['transcript'] = transcript
        
        return result
    
    def transcribe_only(self, audio_path: str) -> str:
        """
        Only transcribe audio without extracting price
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text as string
        """
        trans_result = transcribe(audio_path)
        
        if isinstance(trans_result, dict):
            return trans_result['result']
        return trans_result


# Convenience function for quick usage
def extract_price(audio_path: str) -> Dict:
    """
    Quick function to extract stock price from audio
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Dictionary with index, price, transcript, and timing
    """
    extractor = StockPriceExtractor()
    return extractor.extract(audio_path)


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python StockPriceExtractor.py <audio_file>")
        sys.exit(1)
    
    extractor = StockPriceExtractor()
    result = extractor.extract(sys.argv[1])
    
    print("\nResults:")
    print(f"Index: {result.get('index', 'Not found')}")
    print(f"Price: {result.get('price', 'Not found')}")
    print(f"Transcript: {result.get('transcript', 'N/A')[:100]}...")
    if result.get('timing', {}).get('transcription_s'):
        print(f"Time: {result['timing']['transcription_s']:.3f}s")

