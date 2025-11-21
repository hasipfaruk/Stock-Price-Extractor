import time
import torch
import librosa
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
from .utils import timeit
from .post_process import fix_transcription_errors
from ..config import MODEL_TRANSCRIBE, DEVICE, MODEL_CACHE_DIR

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
            # Distil-Whisper uses same processor/model structure as Whisper
            try:
                _processor = AutoProcessor.from_pretrained(
                    use_model,
                    cache_dir=cache_dir
                )
                _model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    use_model,
                    cache_dir=cache_dir
                ).to(DEVICE)
            except Exception as e:
                # Fallback to Whisper if Distil-Whisper fails
                if "distil-whisper" in use_model.lower():
                    print(f"Warning: {use_model} not available, falling back to whisper-base")
                    use_model = "openai/whisper-base"
                    _processor = AutoProcessor.from_pretrained(
                        use_model,
                        cache_dir=cache_dir
                    )
                    _model = AutoModelForSpeechSeq2Seq.from_pretrained(
                        use_model,
                        cache_dir=cache_dir
                    ).to(DEVICE)
                else:
                    raise e
        _model.eval()
        _current_model_name = use_model
    
    return _processor, _model


@timeit
def transcribe(audio_path: str, model_name: str = None, model_path: str = None):
    """
    Transcribe audio file
    
    Args:
        audio_path: Path to audio file
        model_name: Hugging Face model name (optional)
        model_path: Local path to custom model (optional)
    """
    processor, model = _load_models(model_name=model_name, model_path=model_path)
    # load audio, resample if needed
    audio, sr = librosa.load(audio_path, sr=16000)
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
    for k, v in inputs.items():
        inputs[k] = v.to(DEVICE)
    
    # Optimized generation settings for speed (< 3s requirement)
    generation_kwargs = {
        "max_length": 512,
        "language": "en",  # Specify English for better accuracy
        "task": "transcribe",
    }
    
    # For < 3s requirement, prioritize speed
    if DEVICE == "cpu":
        # CPU: Use greedy decoding for speed
        generation_kwargs["num_beams"] = 1
        generation_kwargs["do_sample"] = False
        generation_kwargs["temperature"] = 0.0
    else:
        # GPU: Can use small beam search
        if "large" in str(_current_model_name).lower() or "distil" in str(_current_model_name).lower():
            generation_kwargs["num_beams"] = 2  # Reduced from 5 for speed
        else:
            generation_kwargs["num_beams"] = 1  # Greedy for speed
        generation_kwargs["temperature"] = 0.0
        generation_kwargs["do_sample"] = False
    
    with torch.no_grad():
        preds = model.generate(inputs["input_features"], **generation_kwargs)
        text = processor.batch_decode(preds, skip_special_tokens=True)[0]
    
    # Post-process to fix common transcription errors
    text = fix_transcription_errors(text)
    
    return text