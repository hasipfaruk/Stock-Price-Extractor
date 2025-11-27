#!/usr/bin/env python3
"""
Validation script to test 100% accuracy requirement
Run this to validate extraction accuracy on your sample/validation data
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.tests.test_accuracy import AccuracyTester


def load_test_config(config_file: str) -> dict:
    """Load test configuration from JSON file"""
    config_path = Path(config_file)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_file}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """Run validation tests"""
    
    # Default config location
    config_file = Path(__file__).parent / "validation_config.json"
    
    if not config_file.exists():
        print("="*70)
        print("ACCURACY VALIDATION - SETUP REQUIRED")
        print("="*70)
        print("\nTo validate 100% accuracy, create validation_config.json with:")
        print("""
{
  "prompt_file": "path/to/prompt.txt",
  "test_cases": [
    {
      "name": "Test Case 1",
      "audio": "path/to/audio1.wav",
      "expected": {
        "index_name": "S&P 500",
        "price": "5048.13",
        "change": "-12.45",
        "change_percent": "-0.25",
        "session": "Morning"
      }
    },
    {
      "name": "Test Case 2",
      "audio": "path/to/audio2.wav",
      "expected": {
        "index_name": "NASDAQ",
        "price": "15892.50",
        "change": "+45.20",
        "change_percent": "+0.28",
        "session": "Afternoon"
      }
    }
  ]
}
        """)
        print(f"Then run: python validate.py\n")
        return
    
    print("="*70)
    print("ACCURACY VALIDATION TEST")
    print("="*70 + "\n")
    
    try:
        # Load configuration
        config = load_test_config(str(config_file))
        
        prompt_file = config.get('prompt_file')
        test_cases = config.get('test_cases', [])
        
        if not prompt_file or not test_cases:
            print("Error: Config must have 'prompt_file' and 'test_cases'")
            sys.exit(1)
        
        print(f"Loaded {len(test_cases)} test cases")
        print(f"Using prompt: {prompt_file}\n")
        
        # Run tests
        tester = AccuracyTester(verbose=True)
        summary = tester.test_batch(test_cases, prompt_file)
        
        # Print summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total Tests:      {summary['total_tests']}")
        print(f"Passed:           {summary['passed']}")
        print(f"Failed:           {summary['failed']}")
        print(f"Accuracy Rate:    {summary['accuracy_rate']}")
        print(f"Latency Issues:   {summary['latency_violations']}")
        print("="*70 + "\n")
        
        # Determine overall result
        if summary['accuracy_rate'] == "100.0%":
            print("✅ SUCCESS: 100% accuracy achieved!")
            return 0
        else:
            print(f"⚠️  Accuracy: {summary['accuracy_rate']} (target: 100%)")
            return 1
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
