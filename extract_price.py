#!/usr/bin/env python3
"""
Standalone CLI tool for extracting stock index prices from audio recordings
Can be used directly from command line without running a server
Works with any audio source containing stock market information
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.models.transcribe import transcribe
from app.models.extract import extract_with_regex, extract_detailed
from app.models.llm_extract import extract_with_long_prompt


def main():
    parser = argparse.ArgumentParser(
        description="Extract stock index prices from audio recordings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python extract_price.py audio.wav
  
  # JSON output
  python extract_price.py audio.wav --json
  
  # Verbose output with timing
  python extract_price.py audio.wav --verbose
  
  # Save to file
  python extract_price.py audio.wav --output result.json
  
  # Use LLM extraction with prompt file
  python extract_price.py audio.wav --use-llm --prompt-file prompt.txt
  
  # Use LLM extraction with prompt text
  python extract_price.py audio.wav --use-llm --prompt-text "Extract stock prices..."
        """
    )
    
    parser.add_argument(
        "audio_file",
        type=str,
        help="Path to audio file (WAV, MP3, FLAC, etc.)"
    )
    
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed information including transcript and timing"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Save results to file (JSON format)"
    )
    
    parser.add_argument(
        "--transcript-only",
        action="store_true",
        help="Only show transcript, don't extract price"
    )
    
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use LLM for extraction instead of regex (requires --prompt-file or --prompt-text)"
    )
    
    parser.add_argument(
        "--prompt-file",
        type=str,
        help="Path to prompt file (for LLM extraction)"
    )
    
    parser.add_argument(
        "--prompt-text",
        type=str,
        help="Prompt text directly (for LLM extraction)"
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    audio_path = Path(args.audio_file)
    if not audio_path.exists():
        print(f"Error: Audio file not found: {args.audio_file}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Transcribe audio
        if args.verbose:
            print("Transcribing audio...", file=sys.stderr)
        
        trans_result = transcribe(str(audio_path))
        
        if isinstance(trans_result, dict):
            transcript = trans_result['result']
            trans_time = trans_result.get('time', None)
        else:
            transcript = trans_result
            trans_time = None
        
        if not transcript:
            print("Error: Failed to transcribe audio", file=sys.stderr)
            sys.exit(1)
        
        # Extract price if requested
        if args.transcript_only:
            result = {
                "transcript": transcript,
                "timing": {"transcription_s": trans_time} if trans_time else {}
            }
        else:
            # Use LLM if requested
            if args.use_llm:
                if not args.prompt_file and not args.prompt_text:
                    print("Error: --use-llm requires --prompt-file or --prompt-text", file=sys.stderr)
                    sys.exit(1)
                
                if args.verbose:
                    print("Using LLM for extraction...", file=sys.stderr)
                
                llm_result = extract_with_long_prompt(
                    transcript,
                    prompt_file=args.prompt_file,
                    prompt_text=args.prompt_text
                )
                
                if llm_result:
                    result = {
                        "index_name": llm_result.get('index_name'),
                        "price": llm_result.get('price'),
                        "change": llm_result.get('change'),
                        "change_percent": llm_result.get('change_percent'),
                        "session": llm_result.get('session'),
                        "standardized_quote": llm_result.get('standardized_quote'),
                        "transcript": transcript,
                        "timing": {"transcription_s": trans_time} if trans_time else {},
                        "extraction_method": "LLM"
                    }
                else:
                    print("Warning: LLM extraction failed, falling back to regex", file=sys.stderr)
                    # Fall through to regex extraction
                    extraction = extract_detailed(transcript)
                    if extraction:
                        result = {
                            "index_name": extraction.get('index_name'),
                            "price": extraction.get('price'),
                            "change": extraction.get('change'),
                            "change_percent": extraction.get('change_percent'),
                            "session": extraction.get('session'),
                            "standardized_quote": extraction.get('standardized_quote'),
                            "transcript": transcript,
                            "timing": {"transcription_s": trans_time} if trans_time else {},
                            "extraction_method": "regex"
                        }
                    else:
                        result = {
                            "index": None,
                            "price": None,
                            "transcript": transcript,
                            "timing": {"transcription_s": trans_time} if trans_time else {},
                            "extraction_method": "regex"
                        }
            else:
                # Use regex extraction (default)
                extraction = extract_detailed(transcript)
                if extraction:
                    result = {
                        "index_name": extraction.get('index_name'),
                        "price": extraction.get('price'),
                        "change": extraction.get('change'),
                        "change_percent": extraction.get('change_percent'),
                        "session": extraction.get('session'),
                        "standardized_quote": extraction.get('standardized_quote'),
                        "transcript": transcript,
                        "timing": {"transcription_s": trans_time} if trans_time else {},
                        "extraction_method": "regex"
                    }
                else:
                    # Fallback to simple extraction
                    simple_extraction = extract_with_regex(transcript)
                    if simple_extraction:
                        index, price = simple_extraction
                    else:
                        index, price = None, None
                    
                    result = {
                        "index": index,
                        "price": price,
                        "transcript": transcript,
                        "timing": {"transcription_s": trans_time} if trans_time else {},
                        "extraction_method": "regex"
                    }
        
        # Output results
        if args.output:
            # Save to file
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Results saved to: {args.output}", file=sys.stderr)
            if not args.json:
                print_result(result, args.verbose)
        elif args.json:
            # JSON output to stdout
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # Human-readable output
            print_result(result, args.verbose)
        
        # Check timing requirement
        if trans_time and trans_time > 3.0:
            print(f"\n  Warning: Processing took {trans_time:.2f}s (target: < 3s)", file=sys.stderr)
        elif trans_time:
            print(f"\n Processing completed in {trans_time:.2f}s", file=sys.stderr)
        
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def print_result(result: dict, verbose: bool = False):
    """Print results in human-readable format"""
    print("\n" + "="*50)
    print("STOCK PRICE EXTRACTION RESULTS")
    if result.get('extraction_method'):
        print(f"Method: {result['extraction_method'].upper()}")
    print("="*50)
    
    # Handle both old format (index/price) and new format (index_name/price)
    index = result.get('index_name') or result.get('index')
    price = result.get('price')
    
    if index:
        print(f"\n[INDEX] Index: {index}")
    else:
        print("\n[INDEX] Index: Not found")
    
    if price:
        print(f"[PRICE] Price: {price}")
    else:
        print("[PRICE] Price: Not found")
    
    if result.get('change'):
        print(f"[CHANGE] Change: {result['change']}")
    
    if result.get('change_percent'):
        print(f"[CHANGE %] Change %: {result['change_percent']}")
    
    if result.get('session'):
        print(f"[SESSION] Session: {result['session']}")
    
    if result.get('standardized_quote'):
        print(f"\n[QUOTE] {result['standardized_quote']}")
    
    if verbose:
        print(f"\n[TRANSCRIPT]")
        print(f"   {result.get('transcript', 'N/A')}")
        
        if result.get('timing', {}).get('transcription_s'):
            print(f"\n[TIME] Processing Time: {result['timing']['transcription_s']:.3f}s")
    
    print("="*50 + "\n")


if __name__ == "__main__":
    main()

