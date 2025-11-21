"""
Streamlit Web App for Stock Index Price Extractor
Simple interface: Upload audio + prompt = Get results
"""

import streamlit as st
import tempfile
import os
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.models.transcribe import transcribe
from app.models.extract import extract_detailed
from app.models.llm_extract import extract_with_long_prompt

# Page config
st.set_page_config(
    page_title="Stock Price Extractor",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Stock Index Price Extractor")
st.markdown("Extract stock index prices from audio recordings using AI")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    extraction_method = st.radio(
        "Extraction Method",
        ["Auto (LLM if prompt provided)", "Regex (Fast)", "LLM (Advanced)"],
        help="Auto: Uses LLM if prompt is provided, otherwise uses regex"
    )
    
    st.markdown("---")
    st.markdown("### 📝 About")
    st.markdown("""
    **How it works:**
    1. Upload audio file (5-10 seconds)
    2. Provide prompt (optional for LLM)
    3. Get extracted stock prices
    
    **Methods:**
    - **Regex**: Fast (< 3s), works automatically
    - **LLM**: Advanced, uses your custom prompt
    """)

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📁 Upload Audio")
    audio_file = st.file_uploader(
        "Choose audio file",
        type=['wav', 'mp3', 'flac', 'm4a', 'ogg'],
        help="Upload a 5-10 second audio file with stock market information"
    )
    
    if audio_file:
        st.audio(audio_file, format=audio_file.type)
        st.success(f"✅ File uploaded: {audio_file.name}")

with col2:
    st.header("📝 Prompt (Optional for LLM)")
    
    prompt_method = st.radio(
        "Prompt Input",
        ["Text Input", "File Upload"],
        horizontal=True,
        help="Provide prompt as text or upload a file"
    )
    
    prompt_text = None
    prompt_file = None
    
    if prompt_method == "Text Input":
        prompt_text = st.text_area(
            "Enter your extraction prompt",
            height=200,
            help="Enter instructions for the LLM on how to extract stock prices. Leave empty to use regex.",
            placeholder="Example:\nExtract stock index price information from the transcript.\nReturn JSON with index_name, price, change, change_percent."
        )
    else:
        prompt_file_upload = st.file_uploader(
            "Upload prompt file",
            type=['txt', 'md'],
            help="Upload a text file with your extraction prompt (can be 500+ lines)"
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

# Process button
st.markdown("---")
process_button = st.button("🚀 Extract Stock Prices", type="primary", use_container_width=True)

if process_button:
    if not audio_file:
        st.error("❌ Please upload an audio file first!")
        st.stop()
    
    # Determine extraction method
    use_llm = False
    if extraction_method == "LLM (Advanced)":
        use_llm = True
        if not prompt_text and not prompt_file:
            st.error("❌ LLM mode requires a prompt! Please provide prompt text or file.")
            st.stop()
    elif extraction_method == "Auto (LLM if prompt provided)":
        use_llm = (prompt_text is not None and prompt_text.strip() != "") or prompt_file is not None
    
    # Show processing status
    with st.spinner("🔄 Processing audio..."):
        # Save audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_audio:
            tmp_audio.write(audio_file.read())
            tmp_audio_path = tmp_audio.name
        
        try:
            # Transcribe
            st.info("🎤 Transcribing audio...")
            trans_result = transcribe(tmp_audio_path)
            
            if isinstance(trans_result, dict):
                transcript = trans_result['result']
                trans_time = trans_result.get('time', 0)
            else:
                transcript = trans_result
                trans_time = 0
            
            if not transcript:
                st.error("❌ Failed to transcribe audio")
                st.stop()
            
            # Extract
            if use_llm:
                st.info("🤖 Using LLM for extraction...")
                if prompt_file:
                    extraction = extract_with_long_prompt(transcript, prompt_file=prompt_file)
                else:
                    extraction = extract_with_long_prompt(transcript, prompt_text=prompt_text)
                method_used = "LLM"
            else:
                st.info("⚡ Using regex for extraction...")
                extraction = extract_detailed(transcript)
                method_used = "Regex"
            
            # Display results
            st.markdown("---")
            st.header("📊 Extraction Results")
            
            # Results in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Extraction Method", method_used)
            
            with col2:
                if trans_time:
                    st.metric("Transcription Time", f"{trans_time:.2f}s")
            
            with col3:
                if extraction:
                    st.metric("Status", "✅ Success")
                else:
                    st.metric("Status", "❌ Failed")
            
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
                        'method': method_used,
                        'transcription_time_s': trans_time
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
                    'method': method_used,
                    'transcription_time_s': trans_time
                }, indent=2)
                
                st.download_button(
                    label="💾 Download Results (JSON)",
                    data=results_json,
                    file_name="extraction_results.json",
                    mime="application/json"
                )
            else:
                st.warning("⚠️ No extraction possible. Try using LLM with a custom prompt.")
                st.markdown("**Transcript:**")
                st.text(transcript)
        
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

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Stock Index Price Extractor | Powered by OpenAI Whisper & Microsoft Phi-3</p>
</div>
""", unsafe_allow_html=True)

