"""
Test harness for validating 100% accuracy requirement
Tests LLM extraction accuracy on validation set
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.models.transcribe import transcribe
from app.models.llm_extract import extract_with_long_prompt
from app.models.normalize import normalize_quote


class AccuracyTester:
    """Test harness for accuracy and performance validation"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.test_results = []
        self.timing_results = []
        self.accuracy_results = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log test message"""
        if self.verbose:
            prefix = f"[{level}]"
            print(f"{prefix} {message}")
    
    def test_extraction(self, 
                       audio_path: str, 
                       prompt_file: str,
                       expected_data: Dict,
                       test_name: str) -> Tuple[bool, Dict]:
        """
        Test single extraction
        
        Args:
            audio_path: Path to audio file
            prompt_file: Path to extraction prompt
            expected_data: Expected extraction results
            test_name: Name of test case
        
        Returns:
            (passed, results) - Whether test passed and result details
        """
        self.log(f"Testing: {test_name}", "TEST")
        
        try:
            # Time transcription
            start_time = time.time()
            trans_result = transcribe(audio_path)
            trans_time = time.time() - start_time
            
            if isinstance(trans_result, dict):
                transcript = trans_result['result']
            else:
                transcript = trans_result
            
            self.log(f"  Transcription: {trans_time:.3f}s", "DEBUG")
            
            # Time LLM extraction
            start_time = time.time()
            extraction = extract_with_long_prompt(
                transcript,
                prompt_file=prompt_file
            )
            extract_time = time.time() - start_time
            
            self.log(f"  Extraction: {extract_time:.3f}s", "DEBUG")
            
            total_time = trans_time + extract_time
            self.log(f"  Total: {total_time:.3f}s", "DEBUG")
            
            # Check if extraction succeeded
            if not extraction:
                self.log(f"   FAILED: Extraction returned None", "ERROR")
                return False, {
                    "test_name": test_name,
                    "status": "FAILED",
                    "reason": "Extraction returned None",
                    "timing": {
                        "transcription_s": trans_time,
                        "extraction_s": extract_time,
                        "total_s": total_time
                    }
                }
            
            # Validate extracted fields
            result = {
                "test_name": test_name,
                "status": "PASSED",
                "extracted": extraction,
                "expected": expected_data,
                "timing": {
                    "transcription_s": trans_time,
                    "extraction_s": extract_time,
                    "total_s": total_time
                },
                "latency_ok": total_time <= 3.0,
                "transcript": transcript
            }
            
            # Compare critical fields
            passed = True
            mismatches = []
            
            for key, expected_value in expected_data.items():
                extracted_value = extraction.get(key)
                
                # Normalize for comparison (case-insensitive, strip whitespace)
                expected_normalized = str(expected_value).lower().strip()
                extracted_normalized = str(extracted_value).lower().strip() if extracted_value else ""
                
                if extracted_normalized != expected_normalized:
                    passed = False
                    mismatches.append({
                        "field": key,
                        "expected": expected_value,
                        "extracted": extracted_value
                    })
                    self.log(f"   Field '{key}': expected '{expected_value}', got '{extracted_value}'", "WARN")
                else:
                    self.log(f"   Field '{key}': {extracted_value}", "DEBUG")
            
            if passed:
                self.log(f"   PASSED: {test_name}", "SUCCESS")
            else:
                self.log(f"    PARTIAL: Some fields mismatched", "WARN")
                result["mismatches"] = mismatches
            
            result["accuracy"] = passed
            return passed, result
            
        except Exception as e:
            self.log(f"   FAILED: {str(e)}", "ERROR")
            return False, {
                "test_name": test_name,
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_batch(self, 
                   test_cases: List[Dict],
                   prompt_file: str) -> Dict:
        """
        Run batch of tests
        
        Args:
            test_cases: List of test case dicts with 'audio', 'expected', 'name'
            prompt_file: Path to extraction prompt
        
        Returns:
            Summary of results
        """
        self.log(f"Running batch of {len(test_cases)} tests", "INFO")
        
        results = []
        passed_count = 0
        latency_violations = 0
        
        for test_case in test_cases:
            audio_path = test_case['audio']
            expected = test_case['expected']
            test_name = test_case.get('name', audio_path)
            
            # Check if audio file exists
            if not Path(audio_path).exists():
                self.log(f"   Audio file not found: {audio_path}", "ERROR")
                results.append({
                    "test_name": test_name,
                    "status": "SKIPPED",
                    "reason": "Audio file not found"
                })
                continue
            
            passed, result = self.test_extraction(
                audio_path,
                prompt_file,
                expected,
                test_name
            )
            
            results.append(result)
            
            if passed:
                passed_count += 1
            
            if not result.get('latency_ok', False):
                latency_violations += 1
                self.log(f"    Latency warning: {result['timing']['total_s']:.3f}s (target: <3s)", "WARN")
        
        summary = {
            "total_tests": len(test_cases),
            "passed": passed_count,
            "failed": len(test_cases) - passed_count,
            "accuracy_rate": f"{(passed_count / len(test_cases) * 100):.1f}%" if test_cases else "N/A",
            "latency_violations": latency_violations,
            "results": results
        }
        
        self.log(f"Batch complete: {passed_count}/{len(test_cases)} passed", "SUMMARY")
        
        return summary
    
    def test_latency(self, 
                    audio_path: str,
                    prompt_file: str,
                    iterations: int = 3) -> Dict:
        """
        Test end-to-end latency
        
        Args:
            audio_path: Path to audio file
            prompt_file: Path to extraction prompt
            iterations: Number of iterations for averaging
        
        Returns:
            Latency statistics
        """
        self.log(f"Testing latency ({iterations} iterations)", "INFO")
        
        timings = []
        
        for i in range(iterations):
            start_time = time.time()
            
            trans_result = transcribe(audio_path)
            if isinstance(trans_result, dict):
                transcript = trans_result['result']
            else:
                transcript = trans_result
            
            extract_with_long_prompt(transcript, prompt_file=prompt_file)
            
            total_time = time.time() - start_time
            timings.append(total_time)
            
            self.log(f"  Iteration {i+1}: {total_time:.3f}s", "DEBUG")
        
        avg_time = sum(timings) / len(timings)
        min_time = min(timings)
        max_time = max(timings)
        
        stats = {
            "iterations": iterations,
            "average_s": avg_time,
            "min_s": min_time,
            "max_s": max_time,
            "target_s": 3.0,
            "meets_target": avg_time <= 3.0,
            "timings": timings
        }
        
        status = "✅ PASS" if stats['meets_target'] else "❌ FAIL"
        self.log(f"Latency: {status} - avg {avg_time:.3f}s (target: <3s)", "SUMMARY")
        
        return stats
    
    def generate_report(self, summary: Dict, output_file: str = None) -> str:
        """
        Generate test report
        
        Args:
            summary: Test summary dict
            output_file: Optional file path to save report
        
        Returns:
            Report as string
        """
        report = f"""
{'='*70}
ACCURACY TEST REPORT
{'='*70}

SUMMARY
-------
Total Tests:           {summary.get('total_tests', 'N/A')}
Passed:                {summary.get('passed', 0)}
Failed:                {summary.get('failed', 0)}
Accuracy Rate:         {summary.get('accuracy_rate', 'N/A')}
Latency Violations:    {summary.get('latency_violations', 0)}

RESULTS DETAIL
--------------
"""
        
        for result in summary.get('results', []):
            status = result.get('status', 'UNKNOWN')
            test_name = result.get('test_name', 'Unknown')
            report += f"\n  {test_name}: {status}"
            
            if 'timing' in result:
                timing = result['timing']
                report += f" ({timing['total_s']:.3f}s total)"
            
            if 'mismatches' in result:
                report += f"\n    Mismatches:"
                for mismatch in result['mismatches']:
                    report += f"\n      - {mismatch['field']}: expected '{mismatch['expected']}', got '{mismatch['extracted']}'"
        
        report += f"\n\n{'='*70}\n"
        
        if output_file:
            Path(output_file).write_text(report)
            print(f"Report saved to: {output_file}")
        
        return report


def demo_test():
    """Demo test with sample data"""
    
    tester = AccuracyTester(verbose=True)
    
    print("\n" + "="*70)
    print("ACCURACY TEST DEMO")
    print("="*70 + "\n")
    
    print("ℹ  This demo shows how to use the test harness for accuracy validation")
    print("ℹ  To run actual tests, provide audio files and expected extraction data\n")
    
    # Example test case structure
    example_test_case = {
        "audio": "sample_audio.wav",
        "name": "Sample Stock Market Recording",
        "expected": {
            "index_name": "S&P 500",
            "price": "5048.13",
            "change": "-12.45",
            "change_percent": "-0.25",
            "session": "Morning"
        }
    }
    
    print("Example test case structure:")
    print(json.dumps(example_test_case, indent=2))
    
    print("\nTo run tests on your data:")
    print("  1. Prepare audio files")
    print("  2. Create test case definitions with expected extraction values")
    print("  3. Call tester.test_batch(test_cases, prompt_file='prompt.txt')")
    print("  4. Review accuracy rate and latency metrics\n")


if __name__ == "__main__":
    demo_test()
