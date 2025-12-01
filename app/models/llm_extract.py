"""
LLM-based extraction using Mistral with vLLM for optimized GPU inference
Optimized for <3s end-to-end latency
"""

from typing import Optional, Dict
import json
import re
import warnings
import os
import logging
import time
from ..config import DEVICE, MODEL_CACHE_DIR, USE_VLLM, LLM_MODEL_NAME, VLLM_MAX_MODEL_LEN, VLLM_MAX_TOKENS, TARGET_LLM_SECONDS
from .normalize import validate_and_normalize_extraction

# Suppress transformers warnings at module level
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Set up comprehensive warning filters
warnings.filterwarnings("ignore", message=".*flash-attention.*")
warnings.filterwarnings("ignore", message=".*window_size.*")
warnings.filterwarnings("ignore", message=".*attention mask.*")
warnings.filterwarnings("ignore", message=".*pad token.*")
warnings.filterwarnings("ignore", message=".*pad_token.*")
warnings.filterwarnings("ignore", message=".*eos_token.*")
warnings.filterwarnings("ignore", message=".*cannot be inferred.*")

# Suppress transformers library logging
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)

# Global variables for model caching
_vllm_llm = None
_vllm_tokenizer = None
_transformers_model = None
_transformers_tokenizer = None
_current_model_name = None


def _load_vllm_model(model_name: str = None):
    """Load Mistral model using vLLM for GPU-optimized inference"""
    global _vllm_llm, _current_model_name
    
    model_id = model_name or LLM_MODEL_NAME
    
    if _vllm_llm is None or _current_model_name != model_id:
        try:
            from vllm import LLM
            
            print(f"Loading Mistral 3B model with vLLM: {model_id}")
            print("This may take a few minutes on first run...")
            print("💡 Using smallest model (3B) for fastest processing (~6GB memory)")
            
            # Configure vLLM for optimal speed (<6s target)
            vllm_kwargs = {
                "model": model_id,
                "trust_remote_code": True,
                "max_model_len": VLLM_MAX_MODEL_LEN,  # Reduced for speed
                "tensor_parallel_size": 1,  # Adjust based on GPU count
                "gpu_memory_utilization": 0.85,  # Slightly reduced for stability
                "dtype": "float16",  # Use FP16 for speed
                "enable_prefix_caching": True,  # Cache prompts for faster inference
            }
            
            # Add optional speed optimizations (may not be available in all vLLM versions)
            try:
                vllm_kwargs["enable_chunked_prefill"] = True  # Enable chunked prefill for speed
                vllm_kwargs["max_num_seqs"] = 256  # Increase batch capacity
            except:
                pass  # Skip if not supported
            
            _vllm_llm = LLM(**vllm_kwargs)
            
            _current_model_name = model_id
            print(" vLLM model loaded successfully!")
            
        except ImportError:
            print(" vLLM not available, falling back to transformers")
            return None
        except Exception as e:
            print(f" Error loading vLLM model: {e}")
            return None
    
    return _vllm_llm


def _load_transformers_model(model_name: str = None):
    """Fallback: Load Mistral model using transformers (for CPU or when vLLM unavailable)"""
    global _transformers_model, _transformers_tokenizer, _current_model_name
    
    model_id = model_name or LLM_MODEL_NAME
    
    if _transformers_model is None or _current_model_name != model_id:
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            print(f"Loading Llama 2 model with transformers: {model_id}")
            print("This may take a few minutes on first run...")
            print("💡 Using Llama-2-7B for extraction (~14GB memory on GPU)")
            
            # Load tokenizer
            _transformers_tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                cache_dir=MODEL_CACHE_DIR,
                trust_remote_code=True
            )
            
            # Set pad token
            if _transformers_tokenizer.pad_token is None:
                _transformers_tokenizer.pad_token = _transformers_tokenizer.eos_token
                _transformers_tokenizer.pad_token_id = _transformers_tokenizer.eos_token_id
            
            # Load model
            load_kwargs = {
                "cache_dir": MODEL_CACHE_DIR,
                "trust_remote_code": True,
                "torch_dtype": torch.float16 if DEVICE == "cuda" else torch.float32,
                "low_cpu_mem_usage": True,
            }
            
            if DEVICE == "cuda":
                load_kwargs["device_map"] = "auto"
            
            _transformers_model = AutoModelForCausalLM.from_pretrained(
                model_id,
                **load_kwargs
            )
            
            if DEVICE == "cpu" and not hasattr(_transformers_model, 'hf_device_map'):
                _transformers_model.to(DEVICE)
            
            _transformers_model.eval()
            _current_model_name = model_id
            print(" Transformers model loaded successfully!")
            
        except Exception as e:
            print(f" Error loading transformers model: {e}")
            return None, None
    
    return _transformers_model, _transformers_tokenizer


def _format_llama2_prompt(instruction: str, transcript: str, tokenizer=None) -> str:
    """
    Format prompt for Llama 2 Chat model - matches working code format
    Embeds transcript in prompt to ensure proper extraction
    """
    # Escape special characters in transcript
    safe_transcript = transcript.replace('\\', '\\\\').replace('"', '\\"')
    
    # Build prompt matching the working code format
    prompt_text = (
        '<s>[INST] <<SYS>>\n'
        f'{instruction}\n'
        '<</SYS>>\n\n'
        f'Transcript: "{safe_transcript}"\n\n'
        'Return only the JSON now:[/INST]'
    )
    
    return prompt_text


def extract_with_llm(transcript: str, prompt: str, model_name: str = None) -> Optional[Dict]:
    """
    Extract stock price information using Llama 2 with vLLM (GPU) or transformers (CPU)
    Optimized for <3s latency
    
    Args:
        transcript: Transcribed text from audio
        prompt: Extraction prompt/instructions
        model_name: Optional model name override
    
    Returns:
        Dictionary with extracted and normalized information
    """
    start_time = time.time()
    
    # Try vLLM first if on GPU
    if USE_VLLM and DEVICE == "cuda":
        llm = _load_vllm_model(model_name)
        if llm is not None:
            try:
                # Format prompt for Llama 2 (vLLM doesn't need tokenizer for formatting)
                full_prompt = _format_llama2_prompt(prompt, transcript, tokenizer=None)
                
                # Generate with vLLM (matching working code parameters)
                outputs = llm.generate(
                    [full_prompt],
                    sampling_params={
                        "temperature": 0.0,  # Deterministic output
                        "max_tokens": 400,  # Match working code
                        "stop": ["</s>", "[INST]", "\n\n\n"],  # Stop sequences
                        "skip_special_tokens": True,  # Skip special tokens
                    },
                    use_tqdm=False,  # Disable progress bar
                )
                
                # Extract response
                response = outputs[0].outputs[0].text.strip()
                
                # Parse JSON from response
                extracted_data = _parse_json_response(response)
                
                if extracted_data:
                    # Normalize and validate (pass transcript for full_transcription field)
                    normalized = validate_and_normalize_extraction(extracted_data, transcript=transcript)
                    elapsed = time.time() - start_time
                    if elapsed > TARGET_LLM_SECONDS:
                        print(f"⚠️ LLM extraction took {elapsed:.2f}s (target: <{TARGET_LLM_SECONDS:.2f}s)")
                    else:
                        print(f"⚡ LLM extraction completed in {elapsed:.2f}s")
                    return normalized
                    
            except Exception as e:
                print(f" vLLM inference error: {e}, falling back to transformers")
    
    # Fallback to transformers
    model, tokenizer = _load_transformers_model(model_name)
    
    if model is None or tokenizer is None:
        return None
    
    try:
        # Format prompt for Llama 2 (use tokenizer's chat template if available)
        full_prompt = _format_llama2_prompt(prompt, transcript, tokenizer=tokenizer)
        
        # Debug: Print first 200 chars of transcript to verify uniqueness (only in verbose mode)
        if len(transcript) > 0:
            transcript_preview = transcript[:200] + ("..." if len(transcript) > 200 else "")
            # Only print if we're in a debug context (can be controlled by env var)
            if os.environ.get("DEBUG_TRANSCRIPTS", "0") == "1":
                print(f"  [DEBUG] Transcript preview: {transcript_preview}")
        
        # Tokenize
        inputs = tokenizer(
            full_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=VLLM_MAX_MODEL_LEN,
            padding=False,
        )
        
        # Move to device
        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
        
        # Generate (matching working code parameters)
        import torch
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=400,  # Match working code
                do_sample=False,  # Greedy decoding
                temperature=0.0,  # Deterministic
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.eos_token_id,  # Use eos as pad
                use_cache=True,  # Enable KV cache for speed
            )
        
        # Decode
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract JSON from response
        extracted_data = _parse_json_response(response)
        
        if extracted_data:
            # Normalize and validate (pass transcript for full_transcription field)
            normalized = validate_and_normalize_extraction(extracted_data, transcript=transcript)
            elapsed = time.time() - start_time
            if elapsed > TARGET_LLM_SECONDS:
                print(f"⚠️ LLM extraction took {elapsed:.2f}s (target: <{TARGET_LLM_SECONDS:.2f}s)")
            else:
                print(f"⚡ LLM extraction completed in {elapsed:.2f}s")
            return normalized
            
    except Exception as e:
        print(f" Error during LLM extraction: {e}")
        return None
    
    return None


def _parse_json_response(response: str) -> Optional[Dict]:
    """Extract and parse JSON from LLM response - matches working code"""
    # Extract text after [/INST] if present (matching working code)
    text = response.split("[/INST]")[-1].strip() if "[/INST]" in response else response
    
    # Find JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    
    json_str = match.group(0)
    
    try:
        # Clean up JSON
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        data = json.loads(json_str)
        
        # Normalize numeric fields in quote_analysis (matching working code)
        if "quote_analysis" in data and isinstance(data["quote_analysis"], dict):
            q = data["quote_analysis"]
            for k in ["current_price", "change_points", "change_percent", "intraday_high", "intraday_low"]:
                if k in q and q[k] is not None:
                    val = str(q[k]).replace(",", "").strip()
                    try:
                        q[k] = float(val) if "." in val else int(val)
                    except (ValueError, TypeError):
                        q[k] = None
        
        return data
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        print(f" JSON parsing error: {e}")
        return None


def _extract_key_value_pairs(text: str) -> Optional[Dict]:
    """Fallback: Extract key-value pairs from text when JSON parsing fails"""
    result = {}
    
    # Common patterns
    patterns = {
        'index_name': r'(?:index_name|index)[":\s]+([^",}\n]+)',
        'price': r'(?:price)[":\s]+([^",}\n]+)',
        'change': r'(?:change)[":\s]+([^",}\n]+)',
        'change_percent': r'(?:change_percent|change_percentage|percent)[":\s]+([^",}\n]+)',
        'session': r'(?:session)[":\s]+([^",}\n]+)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip().strip('"').strip("'")
            if value and value.lower() != 'null':
                result[key] = value
    
    return result if result else None


def extract_with_long_prompt(transcript: str, prompt_file: str = None, prompt_text: str = None) -> Optional[Dict]:
    """
    Extract using long prompt (500+ lines)
    
    Args:
        transcript: Transcribed text
        prompt_file: Path to prompt file (500+ lines)
        prompt_text: Prompt text directly
    
    Returns:
        Extracted and normalized information dictionary
    """
    if prompt_file:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
    elif prompt_text:
        prompt = prompt_text
    else:
        return None
    
    # Use Llama 2 for extraction
    return extract_with_llm(transcript, prompt)
