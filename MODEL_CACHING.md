# Model Caching: Download Once, Use Many Times ✅

## Short Answer: **Models download ONLY on the 1st time** ✅

Once downloaded, models are cached and reused for all subsequent runs. **No re-downloading on every run!**

---

## How It Works

### **Whisper Model (Audio Transcription)**

**First Run:**
```
Loading Whisper model: openai/whisper-large-v2
Downloading... (⏳ 1-2 minutes)
✅ Model cached to: models/cache/
```

**Subsequent Runs:**
```
Loading Whisper model: openai/whisper-large-v2
✅ Using cached model (instant!)
```

**Code (transcribe.py):**
```python
# Lazy loading - models cached on first use
_processor = None
_model = None

def _load_models(model_name: str = None):
    global _processor, _model, _current_model_name
    
    # Only reload if model changed
    if _processor is None or _model is None or _current_model_name != use_model:
        # Load from cache_dir if exists, download if not
        _processor = AutoProcessor.from_pretrained(
            use_model,
            cache_dir=MODEL_CACHE_DIR  # ← Stores in models/cache/
        )
        _model = AutoModelForSpeechSeq2Seq.from_pretrained(
            use_model,
            cache_dir=MODEL_CACHE_DIR  # ← Reuses from cache
        )
    
    return _processor, _model
```

### **Llama 2 Model (Price Extraction)**

**First Run:**
```
Loading Llama 2 model: meta-llama/Llama-2-7b-chat-hf
Downloading... (⏳ 5-10 minutes, ~15 GB)
✅ Model cached
```

**Subsequent Runs:**
```
Loading Llama 2 model: meta-llama/Llama-2-7b-chat-hf
✅ Using cached model (instant!)
```

**Code (llm_extract.py):**
```python
# Global model cache
_vllm_llm = None
_transformers_model = None

def _load_vllm_model(model_name: str = None):
    global _vllm_llm, _current_model_name
    
    # Only load if not already loaded
    if _vllm_llm is None or _current_model_name != model_id:
        _vllm_llm = LLM(
            model=model_id,
            cache_dir=MODEL_CACHE_DIR  # ← Caches models
        )
        _current_model_name = model_id
    
    return _vllm_llm
```

---

## Model Storage Locations

### **Local (Web App / CLI)**
```
project/
  models/
    cache/
      models--openai--whisper-large-v2/
        ✅ Cached after first download
      models--meta-llama--Llama-2-7b-chat-hf/
        ✅ Cached after first download
```

**Path:** `models/cache/` (inside project)

### **Google Colab**
```
/root/.cache/huggingface/
  hub/
    models--openai--whisper-large-v2/
      ✅ Cached per Colab session
    models--meta-llama--Llama-2-7b-chat-hf/
      ✅ Cached per Colab session
```

**Note:** Colab session cache is cleared when you close the notebook

### **Kaggle**
```
/kaggle/working/models/cache/
  models--openai--whisper-large-v2/
    ✅ Cached during notebook run
  models--meta-llama--Llama-2-7b-chat-hf/
    ✅ Cached during notebook run
```

---

## First Run vs. Subsequent Runs

### **First Run Timeline**

```
1. Install dependencies:              ⏳ 1-2 minutes
2. Clone repository:                  ⏳ 30 seconds
3. Load Whisper model (download):     ⏳ 1-2 minutes (1-2 GB)
4. Load Llama 2 model (download):     ⏳ 5-10 minutes (15 GB)
5. Process audio file:                ⏳ 15-30 seconds
   - Transcribe:                      ~10-20s
   - Extract:                         ~5-10s

TOTAL FIRST RUN:                      ⏳ 10-15 minutes
```

### **Subsequent Runs Timeline**

```
1. Dependencies already installed:    ✅ instant
2. Repository already cloned:         ✅ instant
3. Whisper model (cached):            ✅ instant
4. Llama 2 model (cached):            ✅ instant
5. Process audio file:                ⏳ 15-30 seconds
   - Transcribe:                      ~10-20s
   - Extract:                         ~5-10s

TOTAL SUBSEQUENT RUNS:                ⏳ 15-30 seconds
```

### **Time Saved Per File After First Run:**
```
10-15 minutes downloaded → 0 minutes!
That's 100% time savings after first run! 🚀
```

---

## Processing Multiple Files

### **First File (1st run):**
```
Setup & downloads:   10-15 minutes (one-time)
Process file #1:     15-30 seconds
TOTAL:              10-15 minutes
```

### **File #2-10 (same session):**
```
Setup:               0 seconds (already done)
Process file #2:     15-30 seconds
Process file #3:     15-30 seconds
...
Process file #10:    15-30 seconds
TOTAL for 9 files:   2-4.5 minutes
```

### **Example: Batch of 10 Files**
```
First file:     10-15 min (includes downloads)
Files 2-10:     2-4.5 min (all cached)
TOTAL:          12-19.5 minutes for all 10 files
```

---

## How to Verify Caching

### **Check Cached Models Locally**
```bash
# List cached models
ls models/cache/

# Size of cached models
du -sh models/cache/
```

**Output Example:**
```
models/cache/
├── models--distil-whisper--distil-large-v2/   (800 MB)
├── models--openai--whisper-large-v2/           (1.5 GB)
└── models--meta-llama--Llama-2-7b-chat-hf/     (14 GB)

Total: ~16 GB
```

### **Check During Processing**
```
First run (no cache):
  Loading Whisper model: openai/whisper-large-v2
  Downloading... ⏳
  
Subsequent runs (with cache):
  Loading Whisper model: openai/whisper-large-v2
  (instant - no download message)
```

---

## Model Sizes

| Model | Size | Download Time |
|-------|------|---|
| Whisper-large-v2 | 1.5 GB | 1-2 min |
| Llama 2 7B | 14 GB | 5-10 min |
| **Total** | **~16 GB** | **~10-15 min** |

**After caching:** Instant load! ⚡

---

## Benefits of Caching

✅ **First run:** Full download, takes time
✅ **Runs 2+:** Instant model loading, fast processing
✅ **Bandwidth:** Download once, reuse many times
✅ **Storage:** Models stored in `models/cache/`
✅ **Performance:** Same processing speed every time

---

## Important Notes

### **Local/CLI/Web App:**
- Models cached in `models/cache/` (persists)
- Models persist between sessions
- No re-download unless manually deleted

### **Google Colab:**
- Models cached in Colab session
- Cache cleared when notebook closes
- Next Colab session will re-download (new session)
- Tip: Keep notebook running if processing batches

### **Kaggle:**
- Models cached during notebook execution
- Cache cleared when notebook ends
- Next run will re-download models
- Tip: Use persistent cache in `/kaggle/input` if needed

---

## Summary

| When | Download | Time |
|------|---|---|
| **1st file ever** | ✅ Yes (first time) | 10-15 min |
| **2nd file (same session)** | ❌ No (cached) | 15-30 sec |
| **10th file (same session)** | ❌ No (cached) | 15-30 sec |
| **100th file (same session)** | ❌ No (cached) | 15-30 sec |
| **New session** | ✅ Yes (cache reset) | 10-15 min |

**Answer: Models download ONLY on 1st time, then cached forever! 🎯**
