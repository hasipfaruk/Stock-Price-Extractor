# Audio Processing Timing Features

## Overview
Added comprehensive timing tracking to monitor how long each audio file takes to process. The system now displays **detailed timing for each phase** of processing:
- 🎤 **Transcription** - Time to convert audio to text
- 🤖 **Extraction** - Time to extract prices using LLM
- ⏱️ **Total** - Total processing time per file

---

## Web App (streamlit_app.py)

### Single File Mode
When processing a single audio file, you'll see:

```
📊 Extraction Results

Status          | 🎤 Transcription | 🤖 Extraction | ⏱️ Total | Method
✅ Success      | 15.234s          | 8.456s        | 23.69s  | LLM
```

**Detailed timing is also shown in:**
- 📝 View Transcript expandable section
- 📋 View Full JSON expandable section
- 💾 Downloaded JSON file

**Sample JSON output:**
```json
{
  "index_name": "S&P 500",
  "price": "5,234.50",
  "timing": {
    "transcription_s": 15.234,
    "extraction_s": 8.456,
    "total_s": 23.69
  }
}
```

### Batch Processing Mode
When processing multiple files, you'll see:

**Summary Dashboard:**
```
Total Files | ✅ Success | ❌ Failed | ⏱️ Batch Total
10          | 10         | 0         | 156.23s
```

**Average time per file:**
```
💼 Average time per file: **15.62s**
```

**Individual File Results:**
Each file shows timing in the expandable section header:
```
✅ audio1.wav (⏱️ 14.25s)
  🎤 Transcription: 9.123s
  🤖 Extraction: 5.127s
  ⏱️ Total: 14.25s

✅ audio2.wav (⏱️ 15.89s)
  🎤 Transcription: 10.234s
  🤖 Extraction: 5.656s
  ⏱️ Total: 15.89s
```

**Batch JSON Download:**
```json
{
  "summary": {
    "total_files": 10,
    "successful": 10,
    "failed": 0,
    "batch_total_time_s": 156.23,
    "average_time_per_file_s": 15.623
  },
  "results": {
    "audio1.wav": {
      "status": "success",
      "timing": {
        "transcription_s": 9.123,
        "extraction_s": 5.127,
        "total_s": 14.25
      },
      "data": { ... }
    }
  }
}
```

---

## CLI Tool (extract_price.py)

### Command Examples

**Basic with timing display:**
```bash
python extract_price.py audio.wav --prompt-file prompt.txt
```

**Output:**
```
============================================================
STOCK PRICE EXTRACTION RESULTS (100% LLM-POWERED)
============================================================

[INDEX] Index: S&P 500
[PRICE] Price: 5,234.50
[CHANGE] Change: +45.25
[CHANGE %] Change %: +0.87%
[SESSION] Session: US Markets

[TIMING]
  🎤 Transcription: 15.234s
  🤖 Extraction: 8.456s
  ⏱️ Total: 23.69s

[EXTRACTION METHOD] LLM (Llama 2)
[MODEL] meta-llama/Llama-2-7b-chat-hf
[NOTE] 100% LLM-powered extraction. No regex fallback.
============================================================
```

**Verbose output (shows transcript + detailed timing):**
```bash
python extract_price.py audio.wav --prompt-file prompt.txt --verbose
```

**JSON output (includes timing):**
```bash
python extract_price.py audio.wav --prompt-file prompt.txt --json
```

**Save to file (with timing included):**
```bash
python extract_price.py audio.wav --prompt-file prompt.txt --output result.json
```

Result file will contain:
```json
{
  "index_name": "S&P 500",
  "price": "5,234.50",
  "change": "+45.25",
  "change_percent": "+0.87%",
  "session": "US Markets",
  "standardized_quote": "S&P 500 at 5,234.50 (+45.25 pts, +0.87%)",
  "timing": {
    "transcription_s": 15.234,
    "extraction_s": 8.456,
    "total_s": 23.69
  },
  "extraction_method": "LLM (Llama 2)",
  "model": "meta-llama/Llama-2-7b-chat-hf"
}
```

---

## Expected Processing Times

### Single Audio File (5-10 seconds of audio)
- **Transcription (🎤):** 10-20 seconds
  - Depends on audio quality and duration
  - GPU accelerated (much faster than CPU)

- **Extraction (🤖):** 5-10 seconds
  - LLM inference time
  - Depends on prompt complexity
  - GPU accelerated

- **Total:** 15-30 seconds per file

### Batch Processing (10 files)
- **First file:** 15-30s (including model loading)
- **Subsequent files:** 15-25s each
- **Batch total for 10 files:** 2-4 minutes
- **Average per file:** 15-25s

### Performance Factors
- **GPU vs CPU:** GPU is ~10x faster
- **Audio quality:** Clean audio = faster transcription
- **Prompt complexity:** Simpler prompts = faster extraction
- **File size:** Longer audio = longer processing

---

## Features Added

✅ **Transcription Timing** - Tracks audio-to-text conversion time
✅ **Extraction Timing** - Tracks LLM extraction time
✅ **Total Timing** - Complete processing time
✅ **Batch Summary** - Average time per file in batch mode
✅ **JSON Export** - All timing data included in downloads
✅ **Real-time Display** - Web app shows timing immediately after processing
✅ **CLI Output** - Detailed timing in command-line results
✅ **Expandable Details** - View detailed timing breakdown for each file

---

## Usage Tips

1. **Track performance over time** - Save JSON results to monitor improvements
2. **Optimize prompts** - Simpler prompts = faster extraction
3. **GPU usage** - Ensures fastest possible processing
4. **Batch processing** - More efficient for multiple files
5. **Monitor averages** - Use batch summary to track consistency

---

## Recent Changes

**Modified Files:**
- `streamlit_app.py` - Added timing to single and batch modes
- `extract_price.py` - Added timing to CLI tool

**Timing Data:**
- All timing values are in seconds with 3 decimal places (e.g., 15.234s)
- JSON exports include full timing breakdown
- Web app displays timing in human-readable format
