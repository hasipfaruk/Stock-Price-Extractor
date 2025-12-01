"""
Streamlit Web App for Stock Index Price Extractor
Simple interface: Upload audio + prompt = Get results
"""

# Suppress warnings before any imports
import warnings
import os
import logging

# Set environment variables to suppress transformers warnings
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# Disable flash-attention to avoid window_size compatibility issues
os.environ["DISABLE_FLASH_ATTN"] = "1"
# Prevent transformers from auto-detecting flash-attention
os.environ["TRANSFORMERS_USE_FLASH_ATTENTION_2"] = "0"

# Suppress specific warning messages
warnings.filterwarnings("ignore", message=".*flash-attention.*")
warnings.filterwarnings("ignore", message=".*window_size.*")
warnings.filterwarnings("ignore", message=".*attention mask.*")
warnings.filterwarnings("ignore", message=".*pad token.*")
warnings.filterwarnings("ignore", message=".*pad_token.*")
warnings.filterwarnings("ignore", message=".*eos_token.*")
warnings.filterwarnings("ignore", message=".*cannot be inferred.*")

# Suppress transformers logging
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)

import streamlit as st
import tempfile
import json
from pathlib import Path
import sys

# Initialize session state for model caching
if 'llm_model_loaded' not in st.session_state:
    st.session_state.llm_model_loaded = False

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.models.transcribe import transcribe
from app.models.llm_extract import extract_with_long_prompt

# Page config
st.set_page_config(
    page_title="Stock Price Extractor",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Stock Index Price Extractor")
st.markdown("Extract stock index prices from audio recordings using **LLM (Large Language Model)**")
st.info("🤖 **LLM Mode**: This app uses LLM to handle complex audio with multiple information. A prompt is required.")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.info("🤖 **LLM Mode Only**\n\nThis app uses LLM for extraction to handle complex audio with multiple information.")
    
    st.markdown("---")
    st.markdown("### 📝 About")
    st.markdown("""
    **How it works:**
    1. Upload audio file (5-10 seconds)
    2. **Provide prompt** (required)
    3. LLM extracts stock prices
    
    **Why LLM?**
    - Handles complex audio with multiple information
    - Uses your custom extraction rules
    - More accurate for detailed transcripts
    
    **Model Caching:**
    - First run: Downloads ~2GB model (5-10 min)
    - After that: Uses cached model (fast!)
    - Model stored in: `models/cache/`
    """)

# Processing mode selection
st.markdown("### 🎯 Choose Processing Mode")
mode_col1, mode_col2 = st.columns([1, 1])

with mode_col1:
    processing_mode = st.radio(
        "Processing Mode",
        ["Single File", "Batch (Multiple Files)"],
        horizontal=True,
        help="Process one file at a time or upload multiple files"
    )

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📁 Upload Audio")
    
    if processing_mode == "Single File":
        audio_file = st.file_uploader(
            "Choose audio file",
            type=['wav', 'mp3', 'flac', 'm4a', 'ogg'],
            help="Upload a 5-10 second audio file with stock market information"
        )
        audio_files = [audio_file] if audio_file else []
        
        if audio_file:
            st.audio(audio_file, format=audio_file.type)
            st.success(f"✅ File uploaded: {audio_file.name}")
    
    else:  # Batch mode
        audio_files = st.file_uploader(
            "Choose audio files (multiple)",
            type=['wav', 'mp3', 'flac', 'm4a', 'ogg'],
            accept_multiple_files=True,
            help="Upload multiple audio files to process them all at once"
        )
        
        if audio_files:
            st.success(f"✅ {len(audio_files)} files uploaded")
            with st.expander("View uploaded files"):
                for i, f in enumerate(audio_files, 1):
                    st.text(f"  {i}. {f.name}")

with col2:
    st.header("📝 Prompt (Required)")
    
    prompt_method = st.radio(
        "Prompt Input",
        ["Text Input", "File Upload"],
        horizontal=True,
        help="Provide prompt as text or upload a file (required for LLM extraction)"
    )
    
    prompt_text = None
    prompt_file = None
    
    if prompt_method == "Text Input":
        prompt_text = st.text_area(
            "Enter your extraction prompt *",
            height=200,
            help="Enter detailed instructions for the LLM on how to extract stock prices from complex audio. This is REQUIRED.",
            placeholder="Example:\nYou are an expert financial data extractor. Extract stock index price information from the transcript.\n\nExtract:\n1. Index name (e.g., S&P 500, NASDAQ, DOW, DAX, VIX)\n2. Current price\n3. Change in points\n4. Change percentage\n5. Session context\n\nReturn JSON with index_name, price, change, change_percent, session, standardized_quote."
        )
        if not prompt_text or prompt_text.strip() == "":
            st.warning("⚠️ Prompt is required for LLM extraction")
    else:
        prompt_file_upload = st.file_uploader(
            "Upload prompt file *",
            type=['txt', 'md'],
            help="Upload a text file with your extraction prompt (can be 500+ lines). This is REQUIRED."
        )
        if prompt_file_upload:
            # Save uploaded file temporarily
            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp_file:
                    content = prompt_file_upload.read()
                    if isinstance(content, bytes):
                        content = content.decode('utf-8')
                    tmp_file.write(content)
                    prompt_file = tmp_file.name
                st.success(f"✅ Prompt file uploaded: {prompt_file_upload.name}")
            except Exception as e:
                st.error(f"Error reading prompt file: {e}")
                prompt_file = None
        else:
            st.warning("⚠️ Please upload a prompt file")

# Process button
st.markdown("---")
process_button = st.button("🚀 Extract Stock Prices", type="primary", use_container_width=True)

if process_button:
    if not audio_files:
        st.error("❌ Please upload at least one audio file!")
        st.stop()
    
    # Check prompt is provided (required for LLM)
    if not prompt_text and not prompt_file:
        st.error("❌ Prompt is required! Please provide prompt text or upload a prompt file.")
        st.stop()
    
    if prompt_method == "Text Input" and (not prompt_text or prompt_text.strip() == ""):
        st.error("❌ Please enter a prompt in the text area!")
        st.stop()
    
    if prompt_method == "File Upload" and not prompt_file:
        st.error("❌ Please upload a prompt file!")
        st.stop()
    
    # Process files
    import gc
    import torch
    import time
    
    all_results = {}
    
    if processing_mode == "Single File":
        # Single file processing
        audio_file = audio_files[0]
        file_start_time = time.time()
        
        with st.spinner("🔄 Processing audio with LLM..."):
            # Save audio to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_audio:
                tmp_audio.write(audio_file.read())
                tmp_audio_path = tmp_audio.name
            
            try:
                # Transcribe
                st.info("🎤 Transcribing audio...")
                trans_start = time.time()
                trans_result = transcribe(tmp_audio_path)
                trans_total = time.time() - trans_start
                
                if isinstance(trans_result, dict):
                    transcript = trans_result['result']
                    trans_time = trans_result.get('time', trans_total)
                else:
                    transcript = trans_result
                    trans_time = trans_total
                
                if not transcript:
                    st.error("❌ Failed to transcribe audio")
                    st.stop()
                
                # Extract using LLM
                if not st.session_state.llm_model_loaded:
                    st.info("🤖 Loading LLM model (first time only, ~2GB download)...")
                    st.warning("⏳ This may take 5-10 minutes on first run. Model will be cached for future use.")
                else:
                    st.info("🤖 Using LLM for extraction...")
                
                extract_start = time.time()
                if prompt_file:
                    extraction = extract_with_long_prompt(transcript, prompt_file=prompt_file)
                else:
                    extraction = extract_with_long_prompt(transcript, prompt_text=prompt_text)
                extract_time = time.time() - extract_start
                
                # Mark model as loaded
                if extraction is not None:
                    st.session_state.llm_model_loaded = True
                
                total_time = time.time() - file_start_time
                
                # Display results
                st.markdown("---")
                st.header("📊 Extraction Results")
                
                # Results in columns with timing
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Status", "✅ Success" if extraction else "❌ Failed")
                
                with col2:
                    st.metric("📝 Transcription", f"{trans_time:.2f}s")
                
                with col3:
                    st.metric("🤖 Extraction", f"{extract_time:.2f}s")
                
                with col4:
                    st.metric("⏱️ Total", f"{total_time:.2f}s")
                
                with col5:
                    st.metric("Method", "LLM")
                
                if extraction:
                    # Main results
                    st.markdown("### 📈 Extracted Information")
                    
                    result_cols = st.columns(2)
                    
                    with result_cols[0]:
                        st.markdown("**Index Name:**")
                        st.info(extraction.get('index_name', 'N/A'))
                        
                        st.markdown("**Price:**")
                        st.info(extraction.get('price', 'N/A'))
                        
                        st.markdown("**Change:**")
                        st.info(extraction.get('change', 'N/A'))
                    
                    with result_cols[1]:
                        st.markdown("**Change %:**")
                        st.info(extraction.get('change_percent', 'N/A'))
                        
                        st.markdown("**Session:**")
                        st.info(extraction.get('session', 'N/A'))
                        
                        st.markdown("**Standardized Quote:**")
                        st.success(extraction.get('standardized_quote', 'N/A'))
                    
                    # Expandable sections
                    with st.expander("📝 View Transcript"):
                        st.text(transcript)
                    
                    with st.expander("📋 View Full JSON"):
                        st.json({
                            'index_name': extraction.get('index_name'),
                            'price': extraction.get('price'),
                            'change': extraction.get('change'),
                            'change_percent': extraction.get('change_percent'),
                            'session': extraction.get('session'),
                            'standardized_quote': extraction.get('standardized_quote'),
                            'transcript': transcript,
                            'method': 'LLM',
                            'timing': {
                                'transcription_s': round(trans_time, 3),
                                'extraction_s': round(extract_time, 3),
                                'total_s': round(total_time, 3)
                            }
                        })
                    
                    # Download results
                    results_json = json.dumps({
                        'index_name': extraction.get('index_name'),
                        'price': extraction.get('price'),
                        'change': extraction.get('change'),
                        'change_percent': extraction.get('change_percent'),
                        'session': extraction.get('session'),
                        'standardized_quote': extraction.get('standardized_quote'),
                        'transcript': transcript,
                        'method': 'LLM',
                        'timing': {
                            'transcription_s': round(trans_time, 3),
                            'extraction_s': round(extract_time, 3),
                            'total_s': round(total_time, 3)
                        }
                    }, indent=2)
                    
                    st.download_button(
                        label="💾 Download Results (JSON)",
                        data=results_json,
                        file_name="extraction_results.json",
                        mime="application/json"
                    )
                else:
                    st.warning("⚠️ No extraction possible. Please check your prompt and try again.")
                    st.markdown("**Transcript:**")
                    st.text(transcript)
                    st.info("💡 Tip: Make sure your prompt clearly instructs the LLM on what to extract and in what format.")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if st.checkbox("Show error details"):
                    st.exception(e)
            
            finally:
                # Cleanup temp files
                if os.path.exists(tmp_audio_path):
                    os.unlink(tmp_audio_path)
                if prompt_file and os.path.exists(prompt_file):
                    os.unlink(prompt_file)
    
    else:
        # Batch processing
        st.markdown("---")
        st.header("📊 Batch Processing Results")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_container = st.container()
        batch_start_time = time.time()
        
        for idx, audio_file in enumerate(audio_files, 1):
            file_start = time.time()
            status_text.text(f"Processing {idx}/{len(audio_files)}: {audio_file.name}...")
            progress = idx / len(audio_files)
            progress_bar.progress(progress)
            
            try:
                # Save audio to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_audio:
                    tmp_audio.write(audio_file.read())
                    tmp_audio_path = tmp_audio.name
                
                # Transcribe
                trans_start = time.time()
                trans_result = transcribe(tmp_audio_path)
                trans_time = time.time() - trans_start
                
                if isinstance(trans_result, dict):
                    transcript = trans_result['result']
                    trans_time = trans_result.get('time', trans_time)
                else:
                    transcript = trans_result
                
                # Extract
                extract_start = time.time()
                if prompt_file:
                    extraction = extract_with_long_prompt(transcript, prompt_file=prompt_file)
                else:
                    extraction = extract_with_long_prompt(transcript, prompt_text=prompt_text)
                extract_time = time.time() - extract_start
                
                # Mark model as loaded
                if extraction is not None:
                    st.session_state.llm_model_loaded = True
                
                file_total = time.time() - file_start
                
                all_results[audio_file.name] = {
                    "status": "success",
                    "data": extraction,
                    "transcript": transcript,
                    "timing": {
                        "transcription_s": round(trans_time, 3),
                        "extraction_s": round(extract_time, 3),
                        "total_s": round(file_total, 3)
                    }
                }
                
                # Cleanup
                if os.path.exists(tmp_audio_path):
                    os.unlink(tmp_audio_path)
                
                # Clear GPU memory
                torch.cuda.empty_cache()
                gc.collect()
                
            except Exception as e:
                file_total = time.time() - file_start
                all_results[audio_file.name] = {
                    "status": "error",
                    "error": str(e),
                    "timing": {
                        "total_s": round(file_total, 3)
                    }
                }
        
        batch_total_time = time.time() - batch_start_time
        status_text.text("✅ Processing complete!")
        progress_bar.progress(1.0)
        
        # Check for duplicate results (indicates LLM copying example values)
        success_results = [r for r in all_results.values() if r.get("status") == "success" and r.get("data")]
        if len(success_results) > 1:
            # Check if all data fields are identical
            first_data = success_results[0].get("data", {})
            all_identical = all(
                r.get("data", {}) == first_data 
                for r in success_results[1:]
            )
            if all_identical:
                st.error("⚠️ **WARNING: All extraction results are identical!**")
                st.warning("This suggests the LLM may be copying example values from the prompt instead of extracting from transcripts.")
                st.info("**Check:**\n- Verify the prompt file doesn't contain example JSON values\n- Ensure each transcript is being processed uniquely\n- Review the extracted values vs actual transcript content")
        
        # Display results
        st.markdown("### 📈 Results Summary")
        
        success_count = sum(1 for r in all_results.values() if r["status"] == "success")
        error_count = len(all_results) - success_count
        avg_time = sum(r.get("timing", {}).get("total_s", 0) for r in all_results.values() if r["status"] == "success") / max(success_count, 1)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Files", len(all_results))
        with col2:
            st.metric("✅ Success", success_count)
        with col3:
            st.metric("❌ Failed", error_count)
        with col4:
            st.metric("⏱️ Batch Total", f"{batch_total_time:.2f}s")
        
        st.info(f"📊 Average time per file: **{avg_time:.2f}s**")
        
        # Show individual results
        st.markdown("### 📋 Individual Results")
        
        for filename, result in all_results.items():
            if result["status"] == "success":
                timing = result.get("timing", {})
                with st.expander(f"✅ {filename} (⏱️ {timing.get('total_s', 0):.2f}s)"):
                    data = result["data"]
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Index:** {data.get('index_name', 'N/A')}")
                        st.write(f"**Price:** {data.get('price', 'N/A')}")
                    with col2:
                        st.write(f"**Change:** {data.get('change', 'N/A')}")
                        st.write(f"**Change %:** {data.get('change_percent', 'N/A')}")
                    
                    st.markdown("**Timing Details:**")
                    timing_col1, timing_col2, timing_col3 = st.columns(3)
                    with timing_col1:
                        st.write(f"🎤 Transcription: **{timing.get('transcription_s', 0):.3f}s**")
                    with timing_col2:
                        st.write(f"🤖 Extraction: **{timing.get('extraction_s', 0):.3f}s**")
                    with timing_col3:
                        st.write(f"⏱️ Total: **{timing.get('total_s', 0):.3f}s**")
            else:
                timing = result.get("timing", {})
                with st.expander(f"❌ {filename} (⏱️ {timing.get('total_s', 0):.2f}s)"):
                    st.error(f"Error: {result['error']}")
        
        # Download batch results with timing summary
        batch_summary = {
            "summary": {
                "total_files": len(all_results),
                "successful": success_count,
                "failed": error_count,
                "batch_total_time_s": round(batch_total_time, 3),
                "average_time_per_file_s": round(avg_time, 3)
            },
            "results": all_results
        }
        batch_results_json = json.dumps(batch_summary, indent=2)
        st.download_button(
            label="💾 Download All Results (JSON with Timing)",
            data=batch_results_json,
            file_name="batch_results.json",
            mime="application/json"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Stock Index Price Extractor | 100% LLM-Powered (Llama 2) + Whisper ASR</p>
</div>
""", unsafe_allow_html=True)

