# Streamlit App Guide

## Quick Start

### 1. Install Streamlit (if not already installed)

```bash
pip install streamlit
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Run the Streamlit App

```bash
streamlit run streamlit_app.py
```

The app will open automatically in your browser at `http://localhost:8501`

## How to Use

### Simple Workflow

1. **Upload Audio File**
   - Click "Choose audio file"
   - Select your audio file (WAV, MP3, FLAC, etc.)
   - Audio will play automatically

2. **Provide Prompt (Optional)**
   - **Text Input**: Type your prompt directly
   - **File Upload**: Upload a prompt file (txt or md)
   - **Leave empty**: Uses fast regex extraction

3. **Select Method**
   - **Auto**: Uses LLM if prompt provided, regex otherwise (Recommended)
   - **Regex**: Always uses fast regex (no prompt needed)
   - **LLM**: Always uses LLM (requires prompt)

4. **Click "Extract Stock Prices"**
   - Wait for processing
   - View results
   - Download results as JSON

## Features

✅ **Simple Interface**: Just upload and go
✅ **Auto Mode**: Automatically chooses best method
✅ **Real-time Processing**: See progress as it works
✅ **Multiple Formats**: Supports WAV, MP3, FLAC, M4A, OGG
✅ **Download Results**: Export as JSON
✅ **View Transcript**: See what was transcribed
✅ **Full Details**: See all extracted information

## Example Prompts

### Simple Prompt (Text Input)
```
Extract stock index price information from the transcript.
Return JSON with index_name, price, change, change_percent, session.
```

### Detailed Prompt (File Upload)
Create a file with detailed instructions (can be 500+ lines):
```
You are an expert financial data extractor. Extract stock index price information from the given transcript.

Extract the following information:
1. Index name (e.g., S&P 500, NASDAQ, DOW, DAX, VIX)
2. Current price
3. Change in points (if mentioned)
4. Change percentage (if mentioned)
5. Session context (e.g., CLOSING, PREMARKET, SESSION HIGH, SESSION LOW)

Return the result as JSON in this format:
{
  "index_name": "S&P 500",
  "price": "4212",
  "change": "+23",
  "change_percent": "+0.5",
  "session": null,
  "standardized_quote": "S&P 500 @ 4212 +23 pts (+0.5%)"
}
```

## Tips

- **For Speed**: Use "Regex" mode or leave prompt empty
- **For Accuracy**: Use "LLM" mode with detailed prompt
- **For Flexibility**: Use "Auto" mode (recommended)
- **First LLM Run**: Will download model (~2GB, one-time, 5-10 minutes)

## Troubleshooting

**App won't start:**
```bash
pip install streamlit
streamlit run streamlit_app.py
```

**LLM not working:**
- Check internet connection (needs to download model first time)
- Ensure prompt is provided when using LLM mode
- Check console for error messages

**Slow processing:**
- First LLM run downloads model (one-time)
- LLM is slower than regex (expected)
- Use regex mode for faster results

## Screenshots Layout

```
┌─────────────────────────────────────────────────┐
│  📊 Stock Index Price Extractor                 │
├─────────────────────────────────────────────────┤
│  [Settings Sidebar]  │  [Main Content]         │
│                      │                          │
│  ⚙️ Settings        │  📁 Upload Audio        │
│  - Method: Auto     │  [File Upload]           │
│                     │  [Audio Player]          │
│  📝 About           │                          │
│                     │  📝 Prompt              │
│                     │  [Text Input/File]      │
│                     │                          │
│                     │  [🚀 Extract Button]     │
│                     │                          │
│                     │  📊 Results             │
│                     │  - Index, Price, etc.   │
└─────────────────────────────────────────────────┘
```

