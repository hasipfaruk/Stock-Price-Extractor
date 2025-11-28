import time
import torch
import librosa
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
from .utils import timeit
from .post_process import fix_transcription_errors
from ..config import MODEL_TRANSCRIBE, DEVICE, MODEL_CACHE_DIR, TARGET_LATENCY_SECONDS

# Lazy loading - models will be loaded on first use
_processor = None
_model = None
_current_model_name = None


def _load_models(model_name: str = None, model_path: str = None):
    """
    Lazy load models on first use - stored in project models/ directory
    
    Args:
        model_name: Hugging Face model name (e.g., "openai/whisper-base")
        model_path: Local path to custom model directory
    """
    global _processor, _model, _current_model_name
    
    # Determine which model to use
    if model_path:
        # Use custom uploaded model
        use_model = model_path
        cache_dir = None
    elif model_name:
        # Use specified Hugging Face model
        use_model = model_name
        cache_dir = MODEL_CACHE_DIR
    else:
        # Use default model
        use_model = MODEL_TRANSCRIBE
        cache_dir = MODEL_CACHE_DIR
    
    # Only reload if model changed
    if _processor is None or _model is None or _current_model_name != use_model:
        if model_path:
            # Load from local path
            _processor = AutoProcessor.from_pretrained(model_path)
            _model = AutoModelForSpeechSeq2Seq.from_pretrained(model_path).to(DEVICE)
        else:
            # Load from Hugging Face
            # Whisper Large-v3 optimized for GPU
            try:
                _processor = AutoProcessor.from_pretrained(
                    use_model,
                    cache_dir=cache_dir
                )
                
                # Load model with optimizations for GPU
                # Use float32 to avoid GPU precision mismatches
                load_kwargs = {
                    "cache_dir": cache_dir,
                    "torch_dtype": torch.float32,
                }
                
                if DEVICE == "cuda":
                    # Use device_map for multi-GPU or single GPU
                    load_kwargs["device_map"] = "auto"
                    # Enable flash attention if available for speed
                    try:
                        load_kwargs["attn_implementation"] = "flash_attention_2"
                    except:
                        pass  # Fallback to default if flash attention not available
                
                _model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    use_model,
                    **load_kwargs
                )
                
                # Move to device if not using device_map
                if DEVICE == "cuda" and not hasattr(_model, 'hf_device_map'):
                    _model.to(DEVICE)
                elif DEVICE == "cpu":
                    _model.to(DEVICE)
                    
            except Exception as e:
                # Fallback to smaller model if Large-v2 fails
                print(f"Warning: {use_model} not available, falling back to whisper-medium")
                use_model = "openai/whisper-medium"
                _processor = AutoProcessor.from_pretrained(
                    use_model,
                    cache_dir=cache_dir
                )
                # Use float32 for fallback model to avoid GPU precision errors
                _model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    use_model,
                    cache_dir=cache_dir,
                    torch_dtype=torch.float32,
                ).to(DEVICE)
        
        _model.eval()
        _current_model_name = use_model
    
    return _processor, _model


@timeit
def transcribe(audio_path: str, model_name: str = None, model_path: str = None):
    """
    Transcribe audio file with Whisper Large-v3
    Optimized for <3s latency on GPU
    
    Args:
        audio_path: Path to audio file
        model_name: Hugging Face model name (optional)
        model_path: Local path to custom model (optional)
    
    Returns:
        Transcribed text string
    """
    start_time = time.time()
    
    processor, model = _load_models(model_name=model_name, model_path=model_path)
    
    # Load audio, resample if needed (optimized)
    audio, sr = librosa.load(audio_path, sr=16000, mono=True)
    
    # Process audio with optimized settings
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
    for k, v in inputs.items():
        inputs[k] = v.to(DEVICE)
    
    # Optimized generation settings for speed (< 3s requirement)
    # Whisper Large-v3 on GPU can achieve <1s transcription for short audio
    generation_kwargs = {
        "max_length": 448,  # Reduced from 512 for speed (sufficient for short financial audio)
        "language": "en",  # Specify English for better accuracy and speed
        "task": "transcribe",
        "return_timestamps": False,  # Disable timestamps for speed
    }
    
    # Optimize for speed based on device
    if DEVICE == "cuda":
        # GPU: Use greedy decoding for maximum speed
        # Large-v3 is accurate enough with greedy decoding
        generation_kwargs["num_beams"] = 1  # Greedy decoding for speed
        generation_kwargs["do_sample"] = False
        generation_kwargs["temperature"] = 0.0
        # Enable KV cache for faster inference
        generation_kwargs["use_cache"] = True
    else:
        # CPU: Use greedy decoding
        generation_kwargs["num_beams"] = 1
        generation_kwargs["do_sample"] = False
        generation_kwargs["temperature"] = 0.0
    
    # Generate transcription (optimized)
    with torch.no_grad():
        # Use torch.inference_mode() for additional speed on PyTorch 2.0+
        if hasattr(torch, 'inference_mode'):
            with torch.inference_mode():
                preds = model.generate(inputs["input_features"], **generation_kwargs)
        else:
            preds = model.generate(inputs["input_features"], **generation_kwargs)
        
        text = processor.batch_decode(preds, skip_special_tokens=True)[0]
    
    # Post-process to fix common transcription errors
    text = fix_transcription_errors(text)
    
    elapsed = time.time() - start_time
    if elapsed > TARGET_LATENCY_SECONDS * 0.5:  # Warn if transcription takes >50% of target
        print(f" Transcription took {elapsed:.2f}s (target: <{TARGET_LATENCY_SECONDS * 0.5:.2f}s)")
    
    return text