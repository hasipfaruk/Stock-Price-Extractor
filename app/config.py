import torch
import os
from pathlib import Path

# Get project root directory (parent of app/)
PROJECT_ROOT = Path(__file__).parent.parent

# Model storage - store everything in project directory
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)  # Create models directory if it doesn't exist

# Whisper model for transcription (client requirement: Whisper family)
# Choose balance of speed and accuracy; medium is usually best trade-off.
MODEL_TRANSCRIBE = "openai/whisper-medium"  # Good accuracy, still reasonably fast on GPU
# Alternative options:
# "openai/whisper-small"     - Faster but slightly lower accuracy
# "openai/whisper-large-v2"  - Slowest but highest accuracy

# Local cache directory for models (stored in project)
MODEL_CACHE_DIR = str(MODELS_DIR / "cache")

# Device configuration - automatically detects CPU/GPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Force CPU mode (uncomment to force CPU even if GPU is available)
# DEVICE = "cpu"

# vLLM configuration for GPU-optimized inference (optimized for speed)
USE_VLLM = (DEVICE == "cuda")  # Use vLLM only on GPU
VLLM_TENSOR_PARALLEL_SIZE = 1  # Adjust based on GPU count
VLLM_MAX_MODEL_LEN = 2048  # Context length (sufficient for short transcripts)
VLLM_MAX_TOKENS = 100  # Limit output tokens for faster generation and <5s total latency

# LLM model configuration (client requirement: Llama 2)
# Use Llama 2 chat/instruct model for extraction.
# Requires accepting Meta's Llama 2 license and (usually) a Hugging Face token.
LLM_MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"

# Processing settings
# Keep clips short to guarantee latency bounds
MAX_AUDIO_LENGTH = 5  # seconds (hard cap used in transcribe())
SAMPLE_RATE = 16000

# CPU-specific optimizations
USE_CPU_OPTIMIZATIONS = (DEVICE == "cpu")

# Performance targets (GPU, Llama 2 7B + Whisper-medium, short audio)
TARGET_LATENCY_SECONDS = 5.0    # End-to-end latency target (<5s) on a good GPU
TARGET_TRANSCRIBE_SECONDS = 2.5  # Transcription target (<2.5s)
TARGET_LLM_SECONDS = 2.5        # LLM extraction target (<2.5s)

