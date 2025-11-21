import torch
import os
from pathlib import Path

# Get project root directory (parent of app/)
PROJECT_ROOT = Path(__file__).parent.parent

# Model storage - store everything in project directory
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)  # Create models directory if it doesn't exist

# Whisper model for transcription
# Options: "openai/whisper-tiny", "openai/whisper-base", "openai/whisper-small"
# For CPU: Use "openai/whisper-tiny" for < 3s processing (recommended)
# For GPU: Use "openai/whisper-base" for < 3s processing (recommended)
MODEL_TRANSCRIBE = "openai/whisper-base"  # Optimized for CPU - change to "whisper-base" if using GPU

# Local cache directory for models (stored in project)
MODEL_CACHE_DIR = str(MODELS_DIR / "cache")

# Device configuration - automatically detects CPU/GPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Force CPU mode (uncomment to force CPU even if GPU is available)
# DEVICE = "cpu"

# Processing settings
MAX_AUDIO_LENGTH = 10  # seconds
SAMPLE_RATE = 16000

# CPU-specific optimizations
USE_CPU_OPTIMIZATIONS = (DEVICE == "cpu")

