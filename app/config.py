import torch
import os
from pathlib import Path

# Get project root directory (parent of app/)
PROJECT_ROOT = Path(__file__).parent.parent

# Model storage - store everything in project directory
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)  # Create models directory if it doesn't exist

# Whisper model for transcription - Using Large-v3 for high accuracy on GPU
# For < 3s latency requirement on GPU, Large-v3 is optimal
MODEL_TRANSCRIBE = "openai/whisper-large-v3"  # High accuracy, optimized for GPU
# Alternative options if speed is critical:
# "distil-whisper/distil-large-v2" - Faster, slightly lower accuracy
# "openai/whisper-medium" - Good balance

# Local cache directory for models (stored in project)
MODEL_CACHE_DIR = str(MODELS_DIR / "cache")

# Device configuration - automatically detects CPU/GPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Force CPU mode (uncomment to force CPU even if GPU is available)
# DEVICE = "cpu"

# vLLM configuration for GPU-optimized inference
USE_VLLM = (DEVICE == "cuda")  # Use vLLM only on GPU
VLLM_TENSOR_PARALLEL_SIZE = 1  # Adjust based on GPU count
VLLM_MAX_MODEL_LEN = 4096  # Maximum sequence length for Llama 2

# Llama 2 model configuration
# Using Llama 2 instruction-tuned models (7B or 13B based on GPU memory)
LLM_MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"  # Default: 7B model
# Alternative options:
# "meta-llama/Llama-2-13b-chat-hf" - Larger, more accurate (requires more GPU memory)
# "meta-llama/Llama-2-70b-chat-hf" - Largest (requires multiple GPUs)

# Processing settings
MAX_AUDIO_LENGTH = 10  # seconds
SAMPLE_RATE = 16000

# CPU-specific optimizations
USE_CPU_OPTIMIZATIONS = (DEVICE == "cpu")

# Performance targets
TARGET_LATENCY_SECONDS = 3.0  # End-to-end latency target

