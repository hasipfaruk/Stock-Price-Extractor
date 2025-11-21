import time
import torch
import librosa
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
from .utils import timeit
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
            _processor = AutoProcessor.from_pretrained(
                use_model,
                cache_dir=cache_dir
            )
            _model = AutoModelForSpeechSeq2Seq.from_pretrained(
                use_model,
                cache_dir=cache_dir
            ).to(DEVICE)
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
    
    # CPU-optimized generation settings
    generation_kwargs = {
        "max_length": 512,
    }
    if DEVICE == "cpu":
        # Use fewer beams for faster CPU inference
        generation_kwargs["num_beams"] = 1
        generation_kwargs["do_sample"] = False
    
    with torch.no_grad():
        preds = model.generate(inputs["input_features"], **generation_kwargs)
        text = processor.batch_decode(preds, skip_special_tokens=True)[0]
    return text