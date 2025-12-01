#!/usr/bin/env python3
"""
Standalone CLI tool for extracting stock index prices from audio recordings using LLM
100% LLM-powered extraction - No regex fallback
Uses Llama 2 for accurate price extraction
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.models.transcribe import transcribe
from app.models.llm_extract import extract_with_long_prompt


def main():
    parser = argparse.ArgumentParser(
        description="Extract stock index prices from audio recordings using LLM (100% LLM-powered, no regex)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # With prompt file (REQUIRED for LLM extraction)
  python extract_price.py audio.wav --prompt-file prompt.txt
  
  # With prompt text (REQUIRED for LLM extraction)
  python extract_price.py audio.wav --prompt-text "Extract stock prices from the transcript..."
  
  # JSON output
  python extract_price.py audio.wav --prompt-file prompt.txt --json
  
  # Verbose output with timing
  python extract_price.py audio.wav --prompt-file prompt.txt --verbose
  
  # Save to file
  python extract_price.py audio.wav --prompt-file prompt.txt --output result.json
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
        "--prompt-file",
        type=str,
        required=True,
        help="Path to prompt file (REQUIRED - provides extraction instructions to LLM)"
    )
    
    parser.add_argument(
        "--prompt-text",
        type=str,
        help="Alternative: provide prompt text directly instead of --prompt-file"
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
        
        total_start = time.time()
        trans_start = time.time()
        trans_result = transcribe(str(audio_path))
        trans_duration = time.time() - trans_start
        
        if isinstance(trans_result, dict):
            transcript = trans_result['result']
            trans_time = trans_result.get('time', trans_duration)
        else:
            transcript = trans_result
            trans_time = trans_duration
        
        if not transcript:
            print("Error: Failed to transcribe audio", file=sys.stderr)
            sys.exit(1)
        
        # Extract price using LLM (only method available)
        if args.transcript_only:
            total_duration = time.time() - total_start
            result = {
                "transcript": transcript,
                "timing": {
                    "transcription_s": round(trans_time, 3),
                    "total_s": round(total_duration, 3)
                }
            }
        else:
            # 100% LLM-powered extraction (NO REGEX FALLBACK)
            if args.verbose:
                print("Using Llama 2 LLM for extraction (100% LLM-powered)...", file=sys.stderr)
            
            extract_start = time.time()
            llm_result = extract_with_long_prompt(
                transcript,
                prompt_file=args.prompt_file if not args.prompt_text else None,
                prompt_text=args.prompt_text
            )
            extract_duration = time.time() - extract_start
            total_duration = time.time() - total_start
            
            if not llm_result:
                print("Error: LLM extraction failed - no valid JSON returned from LLM", file=sys.stderr)
                print("Ensure your prompt is correct and the LLM can parse the transcript", file=sys.stderr)
                sys.exit(1)
            
            # Build result with new format (matching client requirements)
            result = {
                "full_transcription": llm_result.get('full_transcription', transcript),
                "standardized_quote": llm_result.get('standardized_quote'),
                "index_name": llm_result.get('index_name'),
                "quote_analysis": llm_result.get('quote_analysis', {}),
                "timing": {
                    "transcription_s": round(trans_time, 3),
                    "extraction_s": round(extract_duration, 3),
                    "total_s": round(total_duration, 3)
                },
                "extraction_method": "LLM (Llama 2)",
                "model": "meta-llama/Llama-2-7b-chat-hf"
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
            print(f"\n  Processing completed in {trans_time:.2f}s", file=sys.stderr)
        
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
    print("\n" + "="*60)
    print("STOCK PRICE EXTRACTION RESULTS (100% LLM-POWERED)")
    print("="*60)
    
    index = result.get('index_name')
    quote_analysis = result.get('quote_analysis', {})
    
    if index:
        print(f"\n[INDEX] Index: {index}")
    else:
        print("\n[INDEX] Index: Not extracted")
    
    current_price = quote_analysis.get('current_price')
    if current_price is not None:
        print(f"[PRICE] Price: {current_price}")
    else:
        print("[PRICE] Price: Not mentioned")
    
    change_points = quote_analysis.get('change_points')
    if change_points is not None:
        sign = "+" if change_points >= 0 else ""
        print(f"[CHANGE] Change: {sign}{change_points} pts")
    
    change_percent = quote_analysis.get('change_percent')
    if change_percent is not None:
        sign = "+" if change_percent >= 0 else ""
        print(f"[CHANGE %] Change %: {sign}{change_percent}%")
    
    intraday_high = quote_analysis.get('intraday_high')
    if intraday_high is not None:
        print(f"[HIGH] Intraday High: {intraday_high}")
    
    intraday_low = quote_analysis.get('intraday_low')
    if intraday_low is not None:
        print(f"[LOW] Intraday Low: {intraday_low}")
    
    market_direction = quote_analysis.get('market_direction')
    if market_direction:
        print(f"[DIRECTION] Market Direction: {market_direction.upper()}")
    
    session_context = quote_analysis.get('session_context')
    if session_context:
        print(f"[SESSION] Session: {session_context.upper()}")
    
    if result.get('standardized_quote'):
        print(f"\n[QUOTE] {result['standardized_quote']}")
    
    # Display timing information
    timing = result.get('timing', {})
    if timing:
        print(f"\n[TIMING]")
        if timing.get('transcription_s'):
            print(f"  🎤 Transcription: {timing['transcription_s']:.3f}s")
        if timing.get('extraction_s'):
            print(f"  🤖 Extraction: {timing['extraction_s']:.3f}s")
        if timing.get('total_s'):
            print(f"  ⏱️  Total: {timing['total_s']:.3f}s")
    
    if verbose:
        print(f"\n[TRANSCRIPT]")
        print(f"   {result.get('full_transcription', 'N/A')}")
    
    if result.get('extraction_method'):
        print(f"\n[EXTRACTION METHOD] {result.get('extraction_method', 'LLM')}")
    
    if result.get('model'):
        print(f"[MODEL] {result.get('model', 'meta-llama/Llama-2-7b-chat-hf')}")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

