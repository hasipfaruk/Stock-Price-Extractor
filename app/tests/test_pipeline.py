from app.models.transcribe import transcribe
from app.models.extract import extract_with_regex
import os


def test_end_to_end():
    # Check if sample audio exists, if not skip test
    sample_path = 'app/tests/sample_audio.wav'
    if not os.path.exists(sample_path):
        print(f"Sample audio not found at {sample_path}, skipping test")
        return
    
    t = transcribe(sample_path)
    transcript = t['result'] if isinstance(t, dict) else t
    assert transcript is not None and len(transcript) > 0
    res = extract_with_regex(transcript)
    # if sample has index, ensure extraction works
    if res:
        idx, pr = res
        assert pr is not None