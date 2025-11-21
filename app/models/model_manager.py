"""
Model management utilities for uploading/downloading custom models
"""
import os
import shutil
import zipfile
from pathlib import Path
from typing import List, Dict, Optional
from ..config import MODELS_DIR, MODEL_CACHE_DIR


def list_available_models() -> List[Dict]:
    """List all available models"""
    models = []
    
    # Check Hugging Face cache
    cache_dir = Path(MODEL_CACHE_DIR)
    if cache_dir.exists():
        for model_dir in cache_dir.iterdir():
            if model_dir.is_dir() and "whisper" in model_dir.name.lower():
                models.append({
                    "name": model_dir.name,
                    "path": str(model_dir),
                    "type": "huggingface",
                    "size": _get_dir_size(model_dir)
                })
    
    # Check custom uploaded models
    custom_dir = MODELS_DIR / "custom"
    if custom_dir.exists():
        for model_dir in custom_dir.iterdir():
            if model_dir.is_dir():
                models.append({
                    "name": model_dir.name,
                    "path": str(model_dir),
                    "type": "custom",
                    "size": _get_dir_size(model_dir)
                })
    
    return models


def save_uploaded_model(model_name: str, model_files: List[bytes], filenames: List[str]) -> str:
    """
    Save uploaded model files
    
    Args:
        model_name: Name for the model
        model_files: List of file contents (bytes)
        filenames: List of filenames
        
    Returns:
        Path to saved model directory
    """
    custom_dir = MODELS_DIR / "custom" / model_name
    custom_dir.mkdir(parents=True, exist_ok=True)
    
    # Save all files
    for file_content, filename in zip(model_files, filenames):
        file_path = custom_dir / filename
        # Create subdirectories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(file_content)
    
    return str(custom_dir)


def extract_model_zip(zip_content: bytes, model_name: str) -> str:
    """
    Extract and save model from zip file
    
    Args:
        zip_content: Zip file content as bytes
        model_name: Name for the model
        
    Returns:
        Path to extracted model directory
    """
    custom_dir = MODELS_DIR / "custom" / model_name
    custom_dir.mkdir(parents=True, exist_ok=True)
    
    # Save zip temporarily
    zip_path = custom_dir / "temp_model.zip"
    with open(zip_path, "wb") as f:
        f.write(zip_content)
    
    # Extract zip
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(custom_dir)
    
    # Remove zip file
    zip_path.unlink()
    
    return str(custom_dir)


def get_model_path(model_name: str) -> Optional[str]:
    """Get path to a specific model"""
    # Check custom models first
    custom_path = MODELS_DIR / "custom" / model_name
    if custom_path.exists():
        return str(custom_path)
    
    # Check Hugging Face cache
    cache_dir = Path(MODEL_CACHE_DIR)
    if cache_dir.exists():
        for model_dir in cache_dir.iterdir():
            if model_name in model_dir.name:
                return str(model_dir)
    
    return None


def delete_model(model_name: str) -> bool:
    """Delete a custom model"""
    custom_path = MODELS_DIR / "custom" / model_name
    if custom_path.exists():
        shutil.rmtree(custom_path)
        return True
    return False


def download_model_as_zip(model_name: str) -> Optional[bytes]:
    """
    Download model as zip file
    
    Returns:
        Zip file content as bytes, or None if model not found
    """
    model_path = get_model_path(model_name)
    if not model_path or not Path(model_path).exists():
        return None
    
    # Create zip in memory
    import io
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        model_dir = Path(model_path)
        for file_path in model_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(model_dir)
                zip_file.write(file_path, arcname)
    
    zip_buffer.seek(0)
    return zip_buffer.read()


def _get_dir_size(path: Path) -> int:
    """Get total size of directory in bytes"""
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
    except:
        pass
    return total

