# Stock Index Price Extractor

A powerful, **100% open-source** solution for extracting stock index price information from audio recordings using **Llama 2** LLM and **Whisper** ASR. Optimized for speed and accuracy with proper JSON output format.

## 📋 Recent Updates

✅ **Optimized Output Format** - Client-required JSON structure with `quote_analysis` object  
✅ **Speed Optimizations** - Faster processing with optimized prompts and parameters  
✅ **Unique Extraction** - Each transcript extracts unique values (no copying)  
✅ **Proper Data Types** - Numbers as numbers, not strings  
✅ **100% LLM-Only** - No regex fallbacks, purely LLM-based extraction  

## 🔒 Client Requirements Compliance

✅ **Open-Source Only** - Llama 2 instruction-tuned models (NO OpenAI/Gemini/proprietary models)  
✅ **GPU Optimized** - vLLM with FP16, optimized for fast processing  
✅ **High-Quality ASR** - Whisper Small/Medium for accurate transcription  
✅ **100% LLM Extraction** - NO regex fallbacks, purely LLM-based natural language understanding  
✅ **Standardized Output** - Client-required JSON format with all fields  

⚠️ **IMPORTANT: PROMPT REQUIRED** - This solution uses **100% LLM-only** extraction (Llama 2). A custom extraction prompt file (`example_prompt.txt`) is **REQUIRED** for all extraction operations.

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Usage Options

#### 1. **Streamlit Web App** - Recommended (Easiest to Use) ⭐

```bash
# Install streamlit (if not already installed)
pip install streamlit

# Run the app
streamlit run streamlit_app.py
```

**Features:**
- Simple drag-and-drop interface
- Upload audio + prompt file (required)
- Automatic LLM extraction (Llama 2)
- View results instantly
- Download results as JSON
- Batch processing support

**Note**: Prompt file (`example_prompt.txt`) is **REQUIRED** for LLM extraction.

#### 2. **Command Line (CLI)** - For single files

```bash
# Basic usage (prompt file required)
python extract_price.py audio.wav --prompt-file example_prompt.txt

# JSON output
python extract_price.py audio.wav --prompt-file example_prompt.txt --json

# Verbose with timing
python extract_price.py audio.wav --prompt-file example_prompt.txt --verbose

# Save to file
python extract_price.py audio.wav --prompt-file example_prompt.txt --output result.json
```

#### 3. **Python Library** - Use in your own code

```python
from app.models.transcribe import transcribe
from app.models.llm_extract import extract_with_long_prompt

# Transcribe audio
result = transcribe("audio.wav")
transcript = result['result'] if isinstance(result, dict) else result

# Extract using LLM (prompt file required)
extraction = extract_with_long_prompt(
    transcript, 
    prompt_file="example_prompt.txt"
)

# Access results
print(extraction['index_name'])
print(extraction['quote_analysis']['current_price'])
print(extraction['quote_analysis']['change_points'])
```

## 📋 Features

- ✅ **100% Open-Source**: Llama 2 + Whisper (NO proprietary models)
- ✅ **GPU-Optimized**: vLLM with FP16, optimized for speed
- ✅ **LLM Extraction**: Full natural language understanding of price expressions
- ✅ **Robust Validation**: Data normalization with strict output structure
- ✅ **Fast Processing**: Optimized prompts and parameters for speed
- ✅ **Cross-Platform**: Works on Windows, Linux, and macOS
- ✅ **CPU/GPU Support**: Auto-detects and optimizes for your hardware
- ✅ **Local Models**: All models stored in project directory
- ✅ **Batch Processing**: Process multiple files at once

## 📁 Project Structure

```
bloomberg-audio-price-extractor/
├── extract_price.py          # CLI tool
├── streamlit_app.py          # Web interface
├── example_prompt.txt        # Extraction prompt (REQUIRED)
├── app/
│   ├── config.py             # Configuration
│   ├── __init__.py
│   └── models/
│       ├── transcribe.py     # Whisper transcription
│       ├── llm_extract.py    # LLM extraction
│       ├── normalize.py      # Data normalization
│       ├── post_process.py   # Post-processing
│       ├── utils.py          # Utility functions
│       └── __init__.py
├── models/                   # Downloaded models stored here
├── audios/                   # Audio files directory
├── requirements.txt
└── README.md
```

## 📊 Output Format

The system returns JSON in the following format:

```json
{
  "full_transcription": "S&P futures up 12 points in pre-market trading.",
  "standardized_quote": "S&P 500 FUTURES +12 pts PREMARKET",
  "index_name": "S&P 500",
  "quote_analysis": {
    "current_price": null,
    "change_points": 12,
    "change_percent": null,
    "intraday_high": null,
    "intraday_low": null,
    "market_direction": "up",
    "session_context": "premarket"
  }
}
```

### Output Fields

- **`full_transcription`**: Complete transcribed text from audio
- **`standardized_quote`**: Formatted quote string following client rules
- **`index_name`**: Primary index name (e.g., "S&P 500", "DOW", "NASDAQ")
- **`quote_analysis`**: Object containing:
  - **`current_price`**: Current index level/price (number or null)
  - **`change_points`**: Change in points (number, positive or negative, or null)
  - **`change_percent`**: Change in percentage (number, positive or negative, or null)
  - **`intraday_high`**: Intraday high if mentioned (number or null)
  - **`intraday_low`**: Intraday low if mentioned (number or null)
  - **`market_direction`**: "up", "down", or "flat" (or null)
  - **`session_context`**: "opening", "midday", "closing", "premarket", "afterhours" (or null)

### Example Outputs

**Example 1: S&P 500 with price and change**
```json
{
  "full_transcription": "It's in B500 up 23 points, that's 0.5% higher at 4212.",
  "standardized_quote": "S&P 500 @ 4212 +23 pts (+0.5%)",
  "index_name": "S&P 500",
  "quote_analysis": {
    "current_price": 4212,
    "change_points": 23,
    "change_percent": 0.5,
    "intraday_high": null,
    "intraday_low": null,
    "market_direction": "up",
    "session_context": null
  }
}
```

**Example 2: Dow Jones closing**
```json
{
  "full_transcription": "Dow Jones closing down 58 points at 34,020.",
  "standardized_quote": "DOW @ 34020 -58 pts CLOSING",
  "index_name": "DOW",
  "quote_analysis": {
    "current_price": 34020,
    "change_points": -58,
    "change_percent": null,
    "intraday_high": null,
    "intraday_low": null,
    "market_direction": "down",
    "session_context": "closing"
  }
}
```

**Example 3: Session high/low**
```json
{
  "full_transcription": "S&P session high, 4250, session low, 4200, currently at 4225.",
  "standardized_quote": "S&P 500 HIGH 4250 LOW 4200 @ 4225",
  "index_name": "S&P 500",
  "quote_analysis": {
    "current_price": 4225,
    "change_points": null,
    "change_percent": null,
    "intraday_high": 4250,
    "intraday_low": 4200,
    "market_direction": null,
    "session_context": null
  }
}
```

## ⚙️ Configuration

Edit `app/config.py` to customize:

```python
# Model selection
MODEL_TRANSCRIBE = "openai/whisper-small"  # Fast (default)
# Or use: "openai/whisper-medium" for better accuracy

# LLM model
LLM_MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"

# Device (auto-detected)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Performance targets
TARGET_LATENCY_SECONDS = 5.0
TARGET_TRANSCRIBE_SECONDS = 2.5
TARGET_LLM_SECONDS = 2.5
```

## 🔧 Requirements

- Python 3.8+
- 8GB+ RAM (16GB recommended for Llama 2)
- ~20GB disk space for models
- CUDA GPU (recommended, for faster processing)
- Hugging Face account with Llama 2 access

## 📦 Installation Details

### Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies:
- `torch` - PyTorch for model inference
- `transformers` - Hugging Face transformers
- `librosa` - Audio processing
- `streamlit` - Web interface (optional)
- `vllm` - GPU-optimized inference (optional, for GPU)

### Models

Models are automatically downloaded on first use:
- **Whisper Small**: ~500 MB (fast, default)
- **Whisper Medium**: ~1.5 GB (better accuracy)
- **Llama 2 7B Chat**: ~14 GB (for LLM extraction)

**Note**: Llama 2 requires:
1. Accepting Meta's license: https://huggingface.co/meta-llama/Llama-2-7b-chat-hf
2. Hugging Face token: https://huggingface.co/settings/tokens

## 🎓 Usage Examples

### CLI Examples

```bash
# Single file with JSON output
python extract_price.py audio.wav --prompt-file example_prompt.txt --json

# Verbose output with timing
python extract_price.py audio.wav --prompt-file example_prompt.txt --verbose

# Save to file
python extract_price.py audio.wav --prompt-file example_prompt.txt --output result.json
```

### Python Library Examples

```python
from app.models.transcribe import transcribe
from app.models.llm_extract import extract_with_long_prompt

# Process single file
result = transcribe("audio.wav")
transcript = result['result'] if isinstance(result, dict) else result

extraction = extract_with_long_prompt(transcript, prompt_file="example_prompt.txt")

# Access data
print(f"Index: {extraction['index_name']}")
print(f"Price: {extraction['quote_analysis']['current_price']}")
print(f"Change: {extraction['quote_analysis']['change_points']}")

# Batch processing
from pathlib import Path

results = {}
for audio_file in Path("audios").glob("*.wav"):
    result = transcribe(str(audio_file))
    transcript = result['result'] if isinstance(result, dict) else result
    extraction = extract_with_long_prompt(transcript, prompt_file="example_prompt.txt")
    results[audio_file.name] = extraction
```

## 🚀 Performance

**Target: < 5 seconds end-to-end processing per file**

### GPU (Recommended)
- **Transcription**: ~1-2 seconds (Whisper Small)
- **LLM Extraction**: ~2-3 seconds (Llama 2 7B)
- **Total**: ~3-5 seconds per file

### CPU
- **Transcription**: ~2-4 seconds
- **LLM Extraction**: ~5-10 seconds
- **Total**: ~7-14 seconds per file

Use `--verbose` flag to see detailed timing information.

## 📝 Prompt File

The `example_prompt.txt` file contains the extraction instructions for the LLM. It defines:
- Output JSON format
- Index name standardization rules
- Number extraction rules
- Market direction detection
- Session context extraction

**Important**: Do not modify the prompt structure unless you understand the impact. The prompt is optimized for the client's required output format.

## 🛠️ Development

### Test the Pipeline

```bash
# Test with verbose output
python extract_price.py test_audio.wav --prompt-file example_prompt.txt --verbose
```

### Batch Processing

```python
from pathlib import Path
import json
from app.models.transcribe import transcribe
from app.models.llm_extract import extract_with_long_prompt

audio_files = list(Path("audios").glob("*.wav"))
results = {}

for audio_file in audio_files:
    # Transcribe
    result = transcribe(str(audio_file))
    transcript = result['result'] if isinstance(result, dict) else result
    
    # Extract
    extraction = extract_with_long_prompt(transcript, prompt_file="example_prompt.txt")
    results[audio_file.name] = extraction

# Save results
with open("batch_results.json", "w") as f:
    json.dump(results, f, indent=2)
```

## 📚 Documentation

- **Configuration**: See `app/config.py` for model and performance settings
- **Model Caching**: See `MODEL_CACHING.md` for caching information
- **Speed Optimizations**: See `SPEED_OPTIMIZATIONS.md` for performance tips

## 📝 License

This project uses open-source models:
- **Whisper**: MIT License
- **Transformers**: Apache 2.0
- **Llama 2**: Custom License (requires acceptance)

## 🤝 Contributing

Contributions welcome! Feel free to submit issues or pull requests.

## 📞 Support

For questions or issues, please open an issue on the repository.

---

**Made for everyone** - Use it as a CLI tool, Python library, or web service! 🎉
