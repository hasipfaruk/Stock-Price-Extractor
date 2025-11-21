# Using LLM Instead of Regex

You can use LLM (Phi-3) for extraction instead of regex. This is useful when you have a long prompt (500+ lines) with custom extraction rules.

## Method 1: Command Line (CLI)

```bash
# Use LLM with a prompt file
python extract_price.py audio.wav --use-llm --prompt-file prompt.txt

# Use LLM with prompt text directly
python extract_price.py audio.wav --use-llm --prompt-text "Extract stock prices from the transcript. Return JSON with index_name and price."

# With verbose output
python extract_price.py audio.wav --use-llm --prompt-file prompt.txt --verbose
```

## Method 2: API (Python)

```python
import requests

# Upload audio file and use LLM
with open("audio.wav", "rb") as f:
    files = {"file": ("audio.wav", f)}
    data = {
        "use_llm": "true",  # Enable LLM
        "prompt_text": "Your 500-line prompt here..."  # Or use prompt_file
    }
    response = requests.post("http://localhost:8000/extract", files=files, data=data)
    result = response.json()
    print(result)
```

## Method 3: API (with prompt file)

```python
import requests

# Use prompt file
with open("audio.wav", "rb") as f:
    files = {"file": ("audio.wav", f)}
    data = {
        "use_llm": "true",
        "prompt_file": "/path/to/prompt.txt"  # Path to your prompt file
    }
    response = requests.post("http://localhost:8000/extract", files=files, data=data)
    result = response.json()
```

## Important Notes

1. **LLM Model**: Uses `microsoft/Phi-3-mini-128k-instruct` (128k context window)
2. **First Load**: LLM model download is ~2GB and takes time (one-time)
3. **Speed**: LLM is slower than regex (may exceed 3 seconds)
4. **Requirement**: You MUST provide either `--prompt-file` or `--prompt-text`
5. **Default**: If not specified, uses regex (fast, < 3 seconds)

## When to Use LLM

- ✅ You have a long, complex prompt (500+ lines)
- ✅ You need custom extraction rules
- ✅ Regex patterns are not sufficient
- ❌ For speed-critical applications (use regex instead)

## When to Use Regex (Default)

- ✅ Fast processing (< 3 seconds)
- ✅ Standard stock index extraction
- ✅ Production use
- ✅ No custom prompts needed

