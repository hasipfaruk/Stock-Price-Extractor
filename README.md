# Stock Index Price Extractor

A fast, open-source solution for extracting stock index price information from audio recordings (5-10 seconds) with processing time under 3 seconds. Works with any audio source containing stock market information.

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Usage Options

#### 1. **Command Line (CLI)** - Easiest for single files
```bash
# Basic usage
python extract_price.py audio.wav

# JSON output
python extract_price.py audio.wav --json

# Verbose with timing
python extract_price.py audio.wav --verbose

# Save to file
python extract_price.py audio.wav --output result.json
```

#### 2. **Python Library** - Use in your own code
```python
from StockPriceExtractor import extract_price

# Quick one-liner
result = extract_price("audio.wav")
print(result['index'], result['price'])

# Or use the class
from StockPriceExtractor import StockPriceExtractor

extractor = StockPriceExtractor()
result = extractor.extract("audio.wav")
```

#### 3. **REST API Server** - For web services
```bash
# Start server
python run_server.py

# Single file
curl -X POST "http://localhost:8000/extract" -F "file=@audio.wav"

# Multiple files (folder)
curl -X POST "http://localhost:8000/extract/batch" \
  -F "files=@audio1.wav" -F "files=@audio2.wav"

# Upload folder as zip
curl -X POST "http://localhost:8000/extract/folder" \
  -F "zip_file=@audio_folder.zip"

# Upload custom model
curl -X POST "http://localhost:8000/models/upload" \
  -F "model_name=my-model" -F "files=@config.json" -F "files=@model.bin"

# Download model
curl -X GET "http://localhost:8000/models/my-model/download" \
  -o my-model.zip

# List models
curl -X GET "http://localhost:8000/models"
```

## 📋 Features

- ✅ **Multiple Usage Modes**: CLI, Library, or REST API
- ✅ **Fast Processing**: Optimized for < 3 second processing
- ✅ **Open-Source**: Uses Whisper (speech-to-text) and regex extraction
- ✅ **Cross-Platform**: Works on Windows, Linux, and macOS
- ✅ **CPU/GPU Support**: Auto-detects and optimizes for your hardware
- ✅ **Local Models**: All models stored in project directory
- ✅ **Model Management**: Upload/download custom models via API
- ✅ **Batch Processing**: Process single file, multiple files, or entire folders
- ✅ **Folder Upload**: Upload zip files containing multiple audio files
- ✅ **Easy Integration**: Use as library, CLI tool, or web service

## 📁 Project Structure

```
bloomberg-audio-price-extractor/
├── extract_price.py          # CLI tool (standalone)
├── StockPriceExtractor.py   # Python library
├── run_server.py            # REST API server
├── app/
│   ├── main.py             # FastAPI application
│   ├── config.py           # Configuration
│   └── models/
│       ├── transcribe.py   # Whisper transcription
│       └── extract.py       # Price extraction
├── models/                 # Downloaded models stored here
├── examples/               # Usage examples
├── client/                 # API client examples
└── benchmarks/             # Performance testing
```

## 🎯 Use Cases

### 1. Quick One-Time Extraction
```bash
python extract_price.py recording.wav
```

### 2. Batch Processing (Multiple Files)
```python
# Using API
import requests

files = [
    ("files", ("audio1.wav", open("audio1.wav", "rb"))),
    ("files", ("audio2.wav", open("audio2.wav", "rb")))
]
response = requests.post("http://localhost:8000/extract/batch", files=files)
results = response.json()
```

### 3. Folder Upload (Zip File)
```python
# Upload entire folder as zip
import requests

with open("audio_folder.zip", "rb") as f:
    files = {"zip_file": ("folder.zip", f, "application/zip")}
    response = requests.post("http://localhost:8000/extract/folder", files=files)
    results = response.json()
```

### 4. Custom Model Upload/Download
```python
# Upload your own fine-tuned model
import requests

files = [
    ("files", ("config.json", open("config.json", "rb"))),
    ("files", ("pytorch_model.bin", open("model.bin", "rb")))
]
data = {"model_name": "my-custom-model"}
requests.post("http://localhost:8000/models/upload", files=files, data=data)

# Download model
response = requests.get("http://localhost:8000/models/my-custom-model/download")
with open("downloaded_model.zip", "wb") as f:
    f.write(response.content)
```

### 5. Use Custom Model for Extraction
```python
# Extract using custom uploaded model
import requests

with open("audio.wav", "rb") as f:
    files = {"file": ("audio.wav", f)}
    data = {"model_path": "models/custom/my-custom-model"}
    response = requests.post("http://localhost:8000/extract", files=files, data=data)
```

## ⚙️ Configuration

Edit `app/config.py` to customize:

```python
# Model selection
MODEL_TRANSCRIBE = "openai/whisper-tiny"  # Fastest (CPU)
MODEL_TRANSCRIBE = "openai/whisper-base"  # Balanced (GPU)

# Device
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
```

## 📊 Output Format

### CLI Output
```
==================================================
STOCK PRICE EXTRACTION RESULTS
==================================================

📊 Index: S&P 500
💰 Price: 4500.25

📝 Transcript:
   The S&P 500 is trading at 4500.25...

⏱️  Processing Time: 1.234s
==================================================
```

### JSON Output
```json
{
  "index": "S&P 500",
  "price": "4500.25",
  "transcript": "The S&P 500 is trading at 4500.25...",
  "timing": {
    "transcription_s": 1.234
  }
}
```

## 🔧 Requirements

- Python 3.8+
- 4GB+ RAM (8GB recommended)
- ~500MB disk space for models
- CUDA GPU (optional, for faster processing)

## 📦 Installation Details

### Dependencies
- `torch` - PyTorch for model inference
- `transformers` - Hugging Face transformers
- `librosa` - Audio processing
- `fastapi` - Web framework (for API server)
- `uvicorn` - ASGI server

### Model Download
Models are automatically downloaded on first use to `models/cache/`:
- `whisper-tiny`: ~75 MB
- `whisper-base`: ~150 MB

## 🎓 Examples

### CLI Usage
```bash
python extract_price.py audio.wav --verbose
```

### Python Library
```python
from StockPriceExtractor import extract_price
result = extract_price("audio.wav")
```

### REST API
```bash
python run_server.py
curl -X POST "http://localhost:8000/extract" -F "file=@audio.wav"
```

## 🚀 Performance

### Target: < 3 seconds processing time

**CPU (whisper-tiny):**
- Typical: 1-2 seconds
- Maximum: 2-3 seconds

**GPU (whisper-base):**
- Typical: 0.5-1.5 seconds
- Maximum: 1-2 seconds

## 📚 Documentation

All documentation is in this README. Models are stored in `models/cache/` directory.

## 🛠️ Development

### Run Tests
```bash
python -m app.tests.test_pipeline
```

### Test Performance
Run the CLI tool with `--verbose` to see processing times:
```bash
python extract_price.py audio.wav --verbose
```

## 🤝 Contributing

Contributions welcome! Feel free to submit issues or pull requests.

## 📞 Support

For questions or issues, please open an issue on the repository.

---

**Made for everyone** - Use it as a CLI tool, Python library, or web service! 🎉

