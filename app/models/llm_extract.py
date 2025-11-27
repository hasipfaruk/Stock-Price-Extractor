"""
LLM-based extraction using Llama 2 with vLLM for optimized GPU inference
Optimized for <3s end-to-end latency
"""

from typing import Optional, Dict
import json
import re
import warnings
import os
import logging
import time
from ..config import DEVICE, MODEL_CACHE_DIR, USE_VLLM, LLM_MODEL_NAME, VLLM_MAX_MODEL_LEN
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
    """Load Llama 2 model using vLLM for GPU-optimized inference"""
    global _vllm_llm, _current_model_name
    
    model_id = model_name or LLM_MODEL_NAME
    
    if _vllm_llm is None or _current_model_name != model_id:
        try:
            from vllm import LLM
            
            print(f"Loading Llama 2 model with vLLM: {model_id}")
            print("This may take a few minutes on first run...")
            
            # Configure vLLM for optimal performance
            _vllm_llm = LLM(
                model=model_id,
                trust_remote_code=True,
                max_model_len=VLLM_MAX_MODEL_LEN,
                tensor_parallel_size=1,  # Adjust based on GPU count
                gpu_memory_utilization=0.9,  # Use 90% of GPU memory
                dtype="float16",  # Use FP16 for speed
                enable_prefix_caching=True,  # Cache prompts for faster inference
            )
            
            _current_model_name = model_id
            print("✅ vLLM model loaded successfully!")
            
        except ImportError:
            print("⚠️ vLLM not available, falling back to transformers")
            return None
        except Exception as e:
            print(f"❌ Error loading vLLM model: {e}")
            return None
    
    return _vllm_llm


def _load_transformers_model(model_name: str = None):
    """Fallback: Load Llama 2 model using transformers (for CPU or when vLLM unavailable)"""
    global _transformers_model, _transformers_tokenizer, _current_model_name
    
    model_id = model_name or LLM_MODEL_NAME
    
    if _transformers_model is None or _current_model_name != model_id:
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            print(f"Loading Llama 2 model with transformers: {model_id}")
            print("This may take a few minutes on first run...")
            
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
            print("✅ Transformers model loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error loading transformers model: {e}")
            return None, None
    
    return _transformers_model, _transformers_tokenizer


def _format_llama2_prompt(instruction: str, transcript: str) -> str:
    """
    Format prompt for Llama 2 chat model
    Llama 2 uses a specific chat format
    """
    # Llama 2 chat template
    prompt = f"""<s>[INST] <<SYS>>
{instruction}
<</SYS>>

Transcript:
{transcript}

Extract the information and return as JSON with the following structure:
{{
    "index_name": "S&P 500",
    "price": "5234.12",
    "change": "+23",
    "change_percent": "+0.5",
    "session": "CLOSING",
    "session_high": null,
    "session_low": null
}}

Return only valid JSON, no additional text. [/INST]"""
    
    return prompt


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
                # Format prompt for Llama 2
                full_prompt = _format_llama2_prompt(prompt, transcript)
                
                # Generate with vLLM (optimized for speed)
                outputs = llm.generate(
                    [full_prompt],
                    sampling_params={
                        "temperature": 0.1,  # Low temperature for deterministic output
                        "max_tokens": 200,  # Limit output length for speed
                        "stop": ["</s>", "[INST]", "\n\n\n"],  # Stop sequences
                    },
                    use_tqdm=False,  # Disable progress bar for speed
                )
                
                # Extract response
                response = outputs[0].outputs[0].text.strip()
                
                # Parse JSON from response
                extracted_data = _parse_json_response(response)
                
                if extracted_data:
                    # Normalize and validate
                    normalized = validate_and_normalize_extraction(extracted_data)
                    elapsed = time.time() - start_time
                    print(f"⚡ LLM extraction completed in {elapsed:.2f}s")
                    return normalized
                    
            except Exception as e:
                print(f"⚠️ vLLM inference error: {e}, falling back to transformers")
    
    # Fallback to transformers
    model, tokenizer = _load_transformers_model(model_name)
    
    if model is None or tokenizer is None:
        return None
    
    try:
        # Format prompt for Llama 2
        full_prompt = _format_llama2_prompt(prompt, transcript)
        
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
        
        # Generate (optimized for speed)
        import torch
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.1,
                do_sample=False,  # Greedy decoding for speed
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                use_cache=True,  # Enable KV cache for speed
            )
        
        # Decode
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract JSON from response
        extracted_data = _parse_json_response(response)
        
        if extracted_data:
            # Normalize and validate
            normalized = validate_and_normalize_extraction(extracted_data)
            elapsed = time.time() - start_time
            print(f"⚡ LLM extraction completed in {elapsed:.2f}s")
            return normalized
            
    except Exception as e:
        print(f"❌ Error during LLM extraction: {e}")
        return None
    
    return None


def _parse_json_response(response: str) -> Optional[Dict]:
    """Extract and parse JSON from LLM response"""
    # Try to find JSON in response
    # Look for JSON object
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
    
    if json_match:
        try:
            json_str = json_match.group(0)
            # Clean up common JSON issues
            json_str = json_str.replace('\n', ' ').replace('\t', ' ')
            # Remove trailing commas
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            
            extracted_data = json.loads(json_str)
            return extracted_data
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing error: {e}")
            # Try to extract key-value pairs manually
            return _extract_key_value_pairs(response)
    
    # If no JSON found, try to extract key-value pairs
    return _extract_key_value_pairs(response)


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
