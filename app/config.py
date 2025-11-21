import torch
import os
from pathlib import Path

# Get project root directory (parent of app/)
PROJECT_ROOT = Path(__file__).parent.parent

# Model storage - store everything in project directory
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)  # Create models directory if it doesn't exist

# Whisper model for transcription
# Options for accuracy (best to worst):
#   "distil-whisper/distil-large-v2" - BEST BALANCE: High accuracy + fast (RECOMMENDED)
#   "openai/whisper-large-v3" - HIGHEST ACCURACY: Best quality, slower
#   "openai/whisper-medium" - High accuracy, good speed
#   "openai/whisper-small" - Good accuracy, fast
#   "openai/whisper-base" - Good balance, fast
#   "openai/whisper-tiny" - Fastest, lower accuracy
#
# For < 3s requirement with high accuracy: Use "distil-whisper/distil-large-v2"
# For < 3s requirement on CPU, use smaller model
# For GPU, can use larger model for better accuracy
MODEL_TRANSCRIBE = "openai/whisper-small"  # Better balance for CPU: Good accuracy + faster than large-v2
# Alternative options:
# "openai/whisper-base" - Fastest, lower accuracy
# "openai/whisper-small" - Good balance (current)
# "openai/whisper-medium" - Better accuracy, slower
# "distil-whisper/distil-large-v2" - Best accuracy but slower on CPU

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

