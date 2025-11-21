# How to Run with LLM

## Step-by-Step Guide

### Step 1: Create a Prompt File (Optional but Recommended)

Create a file called `prompt.txt` with your extraction rules. Example:

```
You are an expert financial data extractor. Extract stock index price information from the given transcript.

Extract the following information:
1. Index name (e.g., S&P 500, NASDAQ, DOW, DAX, VIX)
2. Current price
3. Change in points (if mentioned)
4. Change percentage (if mentioned)
5. Session context (e.g., CLOSING, PREMARKET, SESSION HIGH, SESSION LOW)

Return the result as JSON in this format:
{
  "index_name": "S&P 500",
  "price": "4212",
  "change": "+23",
  "change_percent": "+0.5",
  "session": null,
  "standardized_quote": "S&P 500 @ 4212 +23 pts (+0.5%)"
}
```

Or use the example: `example_prompt.txt`

### Step 2: Run with LLM

#### Method A: Command Line (CLI)

```bash
# Basic usage with prompt file
python extract_price.py audio.wav --use-llm --prompt-file prompt.txt

# With verbose output
python extract_price.py audio.wav --use-llm --prompt-file prompt.txt --verbose

# With prompt text directly (no file needed)
python extract_price.py audio.wav --use-llm --prompt-text "Extract stock prices from transcript. Return JSON."

# Save results to file
python extract_price.py audio.wav --use-llm --prompt-file prompt.txt --output result.json
```

#### Method B: API Server

**1. Start the server:**
```bash
python run_server.py
```

**2. Use Python client:**
```python
import requests

# With prompt file
with open("audio.wav", "rb") as f:
    files = {"file": ("audio.wav", f)}
    data = {
        "use_llm": "true",
        "prompt_file": "prompt.txt"  # Path to your prompt file
    }
    response = requests.post("http://localhost:8000/extract", files=files, data=data)
    result = response.json()
    print(result)

# OR with prompt text directly
with open("audio.wav", "rb") as f:
    files = {"file": ("audio.wav", f)}
    data = {
        "use_llm": "true",
        "prompt_text": "Extract stock prices from transcript. Return JSON with index_name and price."
    }
    response = requests.post("http://localhost:8000/extract", files=files, data=data)
    result = response.json()
    print(result)
```

**3. Use curl:**
```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@audio.wav" \
  -F "use_llm=true" \
  -F "prompt_file=prompt.txt"
```

### Step 3: First Run (Model Download)

**Important:** On first run, the LLM model (~2GB) will be downloaded automatically. This takes time (5-10 minutes depending on internet speed).

You'll see:
```
Downloading model files...
model.safetensors: 100%|████████| 2.3G/2.3G [05:23<00:00, 7.2MB/s]
```

After first download, subsequent runs are faster.

## Example Output

```
==================================================
STOCK PRICE EXTRACTION RESULTS
Method: LLM
==================================================

[INDEX] Index: S&P 500
[PRICE] Price: 4212
[CHANGE] Change: +23
[CHANGE %] Change %: +0.5
[SESSION] Session: None

[QUOTE] S&P 500 @ 4212 +23 pts (+0.5%)

[TRANSCRIPT]
   S&P 500 up 23 points that's 0.5% higher at 4212.

[TIME] Processing Time: 8.234s
==================================================
```

## Important Notes

1. **First Run**: LLM model download takes 5-10 minutes (one-time)
2. **Speed**: LLM is slower than regex (5-15 seconds vs 2-3 seconds)
3. **Requirement**: You MUST provide `--prompt-file` or `--prompt-text`
4. **Model**: Uses `microsoft/Phi-3-mini-128k-instruct` (128k context)
5. **Memory**: LLM requires ~4GB RAM (model is ~2GB)

## Troubleshooting

**Error: "Could not load LLM"**
- Check internet connection (needs to download model)
- Ensure you have enough disk space (~3GB)
- Check if you have enough RAM (~4GB)

**Error: "use_llm requires --prompt-file or --prompt-text"**
- You must provide a prompt file or prompt text
- Create `prompt.txt` or use `--prompt-text "your prompt"`

**Slow Performance:**
- LLM is slower than regex (expected)
- First run is slower (model loading)
- Consider using regex for production if speed is critical

## Quick Test

```bash
# Test with example prompt
python extract_price.py audio.wav --use-llm --prompt-file example_prompt.txt --verbose
```

