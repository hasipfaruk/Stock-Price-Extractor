"""
LLM-based extraction for complex cases and long prompts
Supports 500+ line prompts for detailed extraction rules
"""

from typing import Optional, Dict
import json
import re
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from ..config import DEVICE


# LLM models that support long prompts
LLM_MODELS = {
    "phi3": "microsoft/Phi-3-mini-128k-instruct",  # 128k context
    "mistral": "mistralai/Mistral-7B-Instruct-v0.2",  # 32k context
    "llama3": "meta-llama/Meta-Llama-3-8B-Instruct",  # 128k context (requires approval)
}

_llm_model = None
_llm_tokenizer = None
_current_llm = None


def _load_llm(model_name: str = "phi3"):
    """Load LLM for extraction with long prompt support"""
    global _llm_model, _llm_tokenizer, _current_llm
    
    if _llm_model is None or _current_llm != model_name:
        model_id = LLM_MODELS.get(model_name, LLM_MODELS["phi3"])
        
        try:
            _llm_tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
            _llm_model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
                device_map="auto" if DEVICE == "cuda" else None,
                trust_remote_code=True
            )
            if DEVICE == "cpu":
                _llm_model.to(DEVICE)
            _current_llm = model_name
        except Exception as e:
            print(f"Warning: Could not load LLM {model_id}: {e}")
            return None, None
    
    return _llm_model, _llm_tokenizer


def extract_with_llm(transcript: str, prompt: str, model_name: str = "phi3") -> Optional[Dict]:
    """
    Extract stock price information using LLM with long prompt support
    
    Args:
        transcript: Transcribed text from audio
        prompt: Long prompt (can be 500+ lines) with extraction rules
        model_name: LLM model to use ("phi3", "mistral", "llama3")
    
    Returns:
        Dictionary with extracted information
    """
    model, tokenizer = _load_llm(model_name)
    
    if model is None or tokenizer is None:
        return None
    
    # Combine prompt and transcript
    full_prompt = f"{prompt}\n\nTranscript:\n{transcript}\n\nExtract the information and return as JSON:"
    
    # Tokenize
    inputs = tokenizer(
        full_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=tokenizer.model_max_length if hasattr(tokenizer, 'model_max_length') else 8192
    ).to(DEVICE)
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.1,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    
    # Decode
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract JSON from response
    json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
    if json_match:
        try:
            extracted_data = json.loads(json_match.group())
            return extracted_data
        except json.JSONDecodeError:
            pass
    
    return None


def extract_with_long_prompt(transcript: str, prompt_file: str = None, prompt_text: str = None) -> Optional[Dict]:
    """
    Extract using long prompt (500+ lines)
    
    Args:
        transcript: Transcribed text
        prompt_file: Path to prompt file (500+ lines)
        prompt_text: Prompt text directly
    
    Returns:
        Extracted information dictionary
    """
    if prompt_file:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
    elif prompt_text:
        prompt = prompt_text
    else:
        return None
    
    # Use Phi-3 for long context (128k tokens)
    return extract_with_llm(transcript, prompt, model_name="phi3")

