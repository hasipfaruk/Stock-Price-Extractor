# API Reference

Complete API documentation for Stock Index Price Extractor

## Base URL
```
http://localhost:8000
```

## Endpoints

### Health Check
```
GET /health
```
Returns server status.

**Response:**
```json
{"status": "healthy"}
```

---

### Extract from Single File
```
POST /extract
```

**Parameters:**
- `file` (required): Audio file (WAV, MP3, FLAC, etc.)
- `model_name` (optional): Hugging Face model name (e.g., "openai/whisper-base")
- `model_path` (optional): Path to custom uploaded model

**Example:**
```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@audio.wav" \
  -F "model_name=openai/whisper-tiny"
```

**Response:**
```json
{
  "index": "S&P 500",
  "price": "4500.25",
  "transcript": "The S&P 500 is trading at 4500.25...",
  "timings": {"transcription_s": 1.234}
}
```

---

### Extract from Multiple Files
```
POST /extract/batch
```

**Parameters:**
- `files` (required): Multiple audio files
- `model_name` (optional): Model name
- `model_path` (optional): Custom model path

**Example:**
```bash
curl -X POST "http://localhost:8000/extract/batch" \
  -F "files=@audio1.wav" \
  -F "files=@audio2.wav" \
  -F "files=@audio3.wav"
```

**Response:**
```json
{
  "results": [
    {
      "filename": "audio1.wav",
      "index": "S&P 500",
      "price": "4500.25",
      "transcript": "...",
      "timings": {"transcription_s": 1.2}
    },
    ...
  ],
  "total_files": 3,
  "successful": 2,
  "failed": 1
}
```

---

### Extract from Folder (Zip)
```
POST /extract/folder
```

**Parameters:**
- `zip_file` (required): Zip file containing audio files
- `model_name` (optional): Model name
- `model_path` (optional): Custom model path

**Example:**
```bash
curl -X POST "http://localhost:8000/extract/folder" \
  -F "zip_file=@audio_folder.zip"
```

**Response:**
Same as batch endpoint.

---

## Model Management

### List Models
```
GET /models
```

**Response:**
```json
[
  {
    "name": "openai--whisper-base",
    "path": "/path/to/model",
    "type": "huggingface",
    "size": 157286400
  },
  {
    "name": "my-custom-model",
    "path": "/path/to/custom/model",
    "type": "custom",
    "size": 100000000
  }
]
```

---

### Upload Model (Files)
```
POST /models/upload
```

**Parameters:**
- `model_name` (required): Name for the model
- `files` (required): Model files (config.json, pytorch_model.bin, etc.)

**Example:**
```bash
curl -X POST "http://localhost:8000/models/upload" \
  -F "model_name=my-custom-model" \
  -F "files=@config.json" \
  -F "files=@pytorch_model.bin" \
  -F "files=@tokenizer.json"
```

**Response:**
```json
{
  "message": "Model uploaded successfully",
  "model_name": "my-custom-model",
  "path": "/path/to/model"
}
```

---

### Upload Model (Zip)
```
POST /models/upload/zip
```

**Parameters:**
- `model_name` (required): Name for the model
- `zip_file` (required): Zip file containing model files

**Example:**
```bash
curl -X POST "http://localhost:8000/models/upload/zip" \
  -F "model_name=my-custom-model" \
  -F "zip_file=@model.zip"
```

**Response:**
Same as file upload.

---

### Download Model
```
GET /models/{model_name}/download
```

**Example:**
```bash
curl -X GET "http://localhost:8000/models/my-custom-model/download" \
  -o downloaded_model.zip
```

**Response:**
Zip file download.

---

### Delete Model
```
DELETE /models/{model_name}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/models/my-custom-model"
```

**Response:**
```json
{
  "message": "Model 'my-custom-model' deleted successfully"
}
```

---

## Python Client Examples

See `client_examples.py` for complete Python client code.

### Quick Examples

```python
import requests

# Single file
with open("audio.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/extract",
        files={"file": f}
    )
    print(response.json())

# Multiple files
files = [
    ("files", ("audio1.wav", open("audio1.wav", "rb"))),
    ("files", ("audio2.wav", open("audio2.wav", "rb")))
]
response = requests.post("http://localhost:8000/extract/batch", files=files)
print(response.json())

# Upload model
files = [
    ("files", ("config.json", open("config.json", "rb"))),
    ("files", ("model.bin", open("model.bin", "rb")))
]
data = {"model_name": "my-model"}
response = requests.post("http://localhost:8000/models/upload", files=files, data=data)
print(response.json())

# List models
response = requests.get("http://localhost:8000/models")
print(response.json())
```

---

## Interactive Documentation

Visit `http://localhost:8000/docs` for Swagger UI with interactive API testing.

