"""
Example client code for using the Stock Index Price Extractor API
Shows how to upload/download models and process single files or folders
"""

import requests
import os
from pathlib import Path


# API base URL
BASE_URL = "http://localhost:8000"


# ============================================================================
# MODEL MANAGEMENT
# ============================================================================

def list_models():
    """List all available models"""
    response = requests.get(f"{BASE_URL}/models")
    return response.json()


def upload_model(model_name: str, model_files: dict):
    """
    Upload a custom model
    
    Args:
        model_name: Name for the model
        model_files: Dictionary of {filename: file_path} or {filename: file_content}
    
    Example:
        upload_model("my-whisper-model", {
            "config.json": "path/to/config.json",
            "pytorch_model.bin": "path/to/model.bin"
        })
    """
    files = []
    for filename, file_path in model_files.items():
        if isinstance(file_path, str):
            files.append(("files", (filename, open(file_path, "rb"))))
        else:
            files.append(("files", (filename, file_path)))
    
    data = {"model_name": model_name}
    response = requests.post(f"{BASE_URL}/models/upload", files=files, data=data)
    
    # Close file handles
    for _, (_, file_obj) in files:
        if hasattr(file_obj, "close"):
            file_obj.close()
    
    return response.json()


def upload_model_zip(model_name: str, zip_path: str):
    """Upload a model as zip file"""
    with open(zip_path, "rb") as f:
        files = {"zip_file": (os.path.basename(zip_path), f, "application/zip")}
        data = {"model_name": model_name}
        response = requests.post(f"{BASE_URL}/models/upload/zip", files=files, data=data)
    return response.json()


def download_model(model_name: str, save_path: str):
    """Download a model as zip file"""
    response = requests.get(f"{BASE_URL}/models/{model_name}/download")
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        return True
    return False


def delete_model(model_name: str):
    """Delete a custom model"""
    response = requests.delete(f"{BASE_URL}/models/{model_name}")
    return response.json()


# ============================================================================
# AUDIO PROCESSING
# ============================================================================

def extract_single_file(audio_path: str, model_name: str = None, model_path: str = None):
    """
    Extract price from a single audio file
    
    Args:
        audio_path: Path to audio file
        model_name: Optional Hugging Face model name
        model_path: Optional custom model path
    """
    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f)}
        data = {}
        if model_name:
            data["model_name"] = model_name
        if model_path:
            data["model_path"] = model_path
        
        response = requests.post(f"{BASE_URL}/extract", files=files, data=data)
    return response.json()


def extract_multiple_files(audio_files: list, model_name: str = None):
    """
    Extract prices from multiple audio files
    
    Args:
        audio_files: List of paths to audio files
        model_name: Optional model name
    """
    files = []
    for audio_path in audio_files:
        files.append(("files", (os.path.basename(audio_path), open(audio_path, "rb"))))
    
    data = {}
    if model_name:
        data["model_name"] = model_name
    
    response = requests.post(f"{BASE_URL}/extract/batch", files=files, data=data)
    
    # Close file handles
    for _, file_obj in files:
        file_obj[1][1].close()
    
    return response.json()


def extract_folder(folder_path: str, model_name: str = None):
    """
    Extract prices from all audio files in a folder
    
    Args:
        folder_path: Path to folder containing audio files
        model_name: Optional model name
    """
    # Create zip file from folder
    import zipfile
    import tempfile
    
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    temp_zip.close()
    
    # Create zip
    audio_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.ogg'}
    with zipfile.ZipFile(temp_zip.name, "w") as zipf:
        folder = Path(folder_path)
        for file_path in folder.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                zipf.write(file_path, file_path.name)
    
    # Upload and process
    with open(temp_zip.name, "rb") as f:
        files = {"zip_file": (f"{folder.name}.zip", f, "application/zip")}
        data = {}
        if model_name:
            data["model_name"] = model_name
        
        response = requests.post(f"{BASE_URL}/extract/folder", files=files, data=data)
    
    # Cleanup
    os.unlink(temp_zip.name)
    
    return response.json()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("Stock Index Price Extractor - Client Examples\n")
    
    # Example 1: List available models
    print("1. Listing available models:")
    models = list_models()
    for model in models:
        print(f"   - {model['name']} ({model['type']})")
    print()
    
    # Example 2: Extract from single file
    print("2. Extracting from single file:")
    if os.path.exists("sample.wav"):
        result = extract_single_file("sample.wav")
        print(f"   Index: {result.get('index')}")
        print(f"   Price: {result.get('price')}")
    else:
        print("   (No sample.wav file found)")
    print()
    
    # Example 3: Extract from multiple files
    print("3. Extracting from multiple files:")
    audio_files = [f for f in os.listdir(".") if f.endswith((".wav", ".mp3"))]
    if audio_files:
        result = extract_multiple_files(audio_files[:3])  # Process first 3
        print(f"   Processed: {result['successful']}/{result['total_files']} files")
    else:
        print("   (No audio files found)")
    print()
    
    # Example 4: Upload custom model
    print("4. Uploading custom model:")
    print("   # upload_model('my-model', {'config.json': 'path/to/config.json'})")
    print()
    
    # Example 5: Download model
    print("5. Downloading model:")
    print("   # download_model('my-model', 'downloaded_model.zip')")
    print()

