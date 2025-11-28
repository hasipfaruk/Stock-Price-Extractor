import torch
import os
from pathlib import Path

# Get project root directory (parent of app/)
PROJECT_ROOT = Path(__file__).parent.parent

# Model storage - store everything in project directory
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)  # Create models directory if it doesn't exist

# Whisper model for transcription - Optimized for speed (<6s total)
# Using distil-whisper for fastest transcription while maintaining good accuracy
MODEL_TRANSCRIBE = "distil-whisper/distil-large-v2"  # Fast, good accuracy
# Alternative options:
# "openai/whisper-medium" - Slower but more accurate
# "openai/whisper-large-v2" - Slowest but most accurate
# "openai/whisper-small" - Fastest but lower accuracy

# Local cache directory for models (stored in project)
MODEL_CACHE_DIR = str(MODELS_DIR / "cache")

# Device configuration - automatically detects CPU/GPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Force CPU mode (uncomment to force CPU even if GPU is available)
# DEVICE = "cpu"

# vLLM configuration for GPU-optimized inference (optimized for speed)
USE_VLLM = (DEVICE == "cuda")  # Use vLLM only on GPU
VLLM_TENSOR_PARALLEL_SIZE = 1  # Adjust based on GPU count
VLLM_MAX_MODEL_LEN = 2048  # Reduced for faster processing (sufficient for short transcripts)
VLLM_MAX_TOKENS = 150  # Limit output tokens for faster generation

# Mistral model configuration
# Using Mistral instruction-tuned models (7B or Mixtral based on GPU memory)
LLM_MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"  # Default: 7B model
# Alternative options:
# "mistralai/Mistral-7B-Instruct-v0.1" - Older version
# "mistralai/Mixtral-8x7B-Instruct-v0.1" - Mixtral (requires more GPU memory, ~47GB)
# "mistralai/Mistral-7B-Instruct-v0.3" - Latest version (if available)

# Processing settings
MAX_AUDIO_LENGTH = 10  # seconds
SAMPLE_RATE = 16000

# CPU-specific optimizations
USE_CPU_OPTIMIZATIONS = (DEVICE == "cpu")

# Performance targets
TARGET_LATENCY_SECONDS = 6.0  # End-to-end latency target (<6s)
TARGET_TRANSCRIBE_SECONDS = 2.0  # Transcription target (<2s)
TARGET_LLM_SECONDS = 3.0  # LLM extraction target (<3s)

