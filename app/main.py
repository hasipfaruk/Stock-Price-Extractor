from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import shutil
import uuid
import os
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional
import io
from .models.transcribe import transcribe
from .models.extract import extract_with_regex, extract_detailed
from .models.llm_extract import extract_with_long_prompt
from .models.model_manager import (
    list_available_models,
    save_uploaded_model,
    extract_model_zip,
    get_model_path,
    delete_model,
    download_model_as_zip
)


app = FastAPI(title="Stock Index Price Extractor")


class ExtractResponse(BaseModel):
    index: str | None
    price: str | None
    transcript: str
    timings: dict
    standardized_quote: str | None = None
    index_name: str | None = None
    change: str | None = None
    change_percent: str | None = None
    session: str | None = None


class BatchExtractResponse(BaseModel):
    results: List[dict]
    total_files: int
    successful: int
    failed: int


class ModelInfo(BaseModel):
    name: str
    path: str
    type: str
    size: int


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/extract", response_model=ExtractResponse)
async def extract_price(
    file: UploadFile = File(...),
    model_name: Optional[str] = Form(None),
    model_path: Optional[str] = Form(None),
    use_llm: Optional[bool] = Form(False),
    prompt_file: Optional[str] = Form(None),
    prompt_text: Optional[str] = Form(None)
):
    """
    Extract stock price from a single audio file
    
    - **file**: Audio file (WAV, MP3, FLAC, etc.)
    - **model_name**: Optional Hugging Face model name (e.g., "openai/whisper-base")
    - **model_path**: Optional path to custom uploaded model
    """
    tmp_name = None
    try:
        # Save to temp (cross-platform)
        temp_dir = tempfile.gettempdir()
        tmp_name = os.path.join(temp_dir, f"{uuid.uuid4().hex}.wav")
        with open(tmp_name, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Transcribe with optional custom model
        trans = transcribe(tmp_name, model_name=model_name, model_path=model_path)
        transcript = trans['result'] if isinstance(trans, dict) else trans
        trans_time = trans['time'] if isinstance(trans, dict) else None
        
        if not transcript:
            raise HTTPException(status_code=400, detail="Failed to transcribe audio")
        
        # Extract using LLM with long prompt if requested
        if use_llm and (prompt_file or prompt_text):
            llm_result = extract_with_long_prompt(
                transcript,
                prompt_file=prompt_file,
                prompt_text=prompt_text
            )
            if llm_result:
                return {
                    'index': llm_result.get('price'),
                    'price': llm_result.get('price'),
                    'index_name': llm_result.get('index_name'),
                    'change': llm_result.get('change'),
                    'change_percent': llm_result.get('change_percent'),
                    'session': llm_result.get('session'),
                    'standardized_quote': llm_result.get('standardized_quote'),
                    'transcript': transcript,
                    'timings': {'transcription_s': trans_time}
                }
        
        # Extract detailed information using regex
        detailed = extract_detailed(transcript)
        if detailed:
            return {
                'index': detailed.get('price'),
                'price': detailed.get('price'),
                'index_name': detailed.get('index_name'),
                'change': detailed.get('change'),
                'change_percent': detailed.get('change_percent'),
                'session': detailed.get('session'),
                'standardized_quote': detailed.get('standardized_quote'),
                'transcript': transcript,
                'timings': {'transcription_s': trans_time}
            }
        
        # Fallback to simple extraction
        extraction = extract_with_regex(transcript)
        if extraction:
            index, price = extraction
        else:
            index, price = None, None
        
        return {
            'index': index,
            'price': price,
            'index_name': index,
            'standardized_quote': f"{index} @ {price}" if index and price else None,
            'transcript': transcript,
            'timings': {'transcription_s': trans_time}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
    finally:
        # Cleanup
        if tmp_name and os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except:
                pass


@app.post("/extract/batch", response_model=BatchExtractResponse)
async def extract_batch(
    files: List[UploadFile] = File(...),
    model_name: Optional[str] = Form(None),
    model_path: Optional[str] = Form(None)
):
    """
    Extract stock prices from multiple audio files (folder upload)
    
    - **files**: Multiple audio files (can upload entire folder)
    - **model_name**: Optional Hugging Face model name
    - **model_path**: Optional path to custom uploaded model
    """
    results = []
    successful = 0
    failed = 0
    
    for file in files:
        tmp_name = None
        try:
            # Save to temp
            temp_dir = tempfile.gettempdir()
            tmp_name = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{file.filename}")
            with open(tmp_name, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            # Transcribe
            trans = transcribe(tmp_name, model_name=model_name, model_path=model_path)
            transcript = trans['result'] if isinstance(trans, dict) else trans
            trans_time = trans['time'] if isinstance(trans, dict) else None
            
            if not transcript:
                raise Exception("Failed to transcribe")
            
            # Extract detailed information
            detailed = extract_detailed(transcript)
            if detailed:
                results.append({
                    'filename': file.filename,
                    'index': detailed.get('price'),
                    'price': detailed.get('price'),
                    'index_name': detailed.get('index_name'),
                    'change': detailed.get('change'),
                    'change_percent': detailed.get('change_percent'),
                    'session': detailed.get('session'),
                    'standardized_quote': detailed.get('standardized_quote'),
                    'transcript': transcript,
                    'timings': {'transcription_s': trans_time} if trans_time else {}
                })
            else:
                # Fallback
                extraction = extract_with_regex(transcript)
                if extraction:
                    index, price = extraction
                else:
                    index, price = None, None
                
                results.append({
                    'filename': file.filename,
                    'index': index,
                    'price': price,
                    'index_name': index,
                    'standardized_quote': f"{index} @ {price}" if index and price else None,
                    'transcript': transcript,
                    'timings': {'transcription_s': trans_time} if trans_time else {}
                })
            successful += 1
            
        except Exception as e:
            results.append({
                'filename': file.filename,
                'error': str(e),
                'index': None,
                'price': None
            })
            failed += 1
        finally:
            # Cleanup
            if tmp_name and os.path.exists(tmp_name):
                try:
                    os.remove(tmp_name)
                except:
                    pass
    
    return {
        'results': results,
        'total_files': len(files),
        'successful': successful,
        'failed': failed
    }


@app.post("/extract/folder")
async def extract_folder(
    zip_file: UploadFile = File(...),
    model_name: Optional[str] = Form(None),
    model_path: Optional[str] = Form(None)
):
    """
    Extract stock prices from a zip file containing audio files
    
    - **zip_file**: Zip file containing audio files
    - **model_name**: Optional Hugging Face model name
    - **model_path**: Optional path to custom uploaded model
    """
    temp_dir = None
    try:
        # Extract zip to temp directory
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, zip_file.filename)
        
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(zip_file.file, f)
        
        # Extract zip
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Find all audio files
        audio_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.ogg'}
        audio_files = []
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if Path(file).suffix.lower() in audio_extensions:
                    audio_files.append(os.path.join(root, file))
        
        if not audio_files:
            raise HTTPException(status_code=400, detail="No audio files found in zip")
        
        # Process all files
        results = []
        successful = 0
        failed = 0
        
        for audio_file in audio_files:
            try:
                trans = transcribe(audio_file, model_name=model_name, model_path=model_path)
                transcript = trans['result'] if isinstance(trans, dict) else trans
                trans_time = trans['time'] if isinstance(trans, dict) else None
                
                if not transcript:
                    raise Exception("Failed to transcribe")
                
                extraction = extract_with_regex(transcript)
                if extraction:
                    index, price = extraction
                else:
                    index, price = None, None
                
                results.append({
                    'filename': os.path.basename(audio_file),
                    'index': index,
                    'price': price,
                    'transcript': transcript,
                    'timings': {'transcription_s': trans_time} if trans_time else {}
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    'filename': os.path.basename(audio_file),
                    'error': str(e),
                    'index': None,
                    'price': None
                })
                failed += 1
        
        return {
            'results': results,
            'total_files': len(audio_files),
            'successful': successful,
            'failed': failed
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing folder: {str(e)}")
    finally:
        # Cleanup
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass


# Model Management Endpoints

@app.get("/models", response_model=List[ModelInfo])
async def list_models():
    """List all available models"""
    models = list_available_models()
    return [
        ModelInfo(
            name=m['name'],
            path=m['path'],
            type=m['type'],
            size=m['size']
        )
        for m in models
    ]


@app.post("/models/upload")
async def upload_model(
    model_name: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Upload a custom model
    
    - **model_name**: Name for the model
    - **files**: Model files (config.json, pytorch_model.bin, etc.)
    """
    try:
        model_files = []
        filenames = []
        
        for file in files:
            content = await file.read()
            model_files.append(content)
            filenames.append(file.filename)
        
        model_path = save_uploaded_model(model_name, model_files, filenames)
        
        return {
            "message": "Model uploaded successfully",
            "model_name": model_name,
            "path": model_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading model: {str(e)}")


@app.post("/models/upload/zip")
async def upload_model_zip(
    model_name: str = Form(...),
    zip_file: UploadFile = File(...)
):
    """
    Upload a custom model as zip file
    
    - **model_name**: Name for the model
    - **zip_file**: Zip file containing model files
    """
    try:
        zip_content = await zip_file.read()
        model_path = extract_model_zip(zip_content, model_name)
        
        return {
            "message": "Model uploaded successfully",
            "model_name": model_name,
            "path": model_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading model: {str(e)}")


@app.get("/models/{model_name}/download")
async def download_model(model_name: str):
    """Download a model as zip file"""
    zip_content = download_model_as_zip(model_name)
    
    if zip_content is None:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return StreamingResponse(
        io.BytesIO(zip_content),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={model_name}.zip"}
    )


@app.delete("/models/{model_name}")
async def remove_model(model_name: str):
    """Delete a custom model"""
    if delete_model(model_name):
        return {"message": f"Model '{model_name}' deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Model not found")
