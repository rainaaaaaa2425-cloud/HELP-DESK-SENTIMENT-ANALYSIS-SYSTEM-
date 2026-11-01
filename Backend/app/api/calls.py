import logging
import uuid
import os
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Query, status

from app.core.config import settings
from app.core.database import db
from app.schemas.call import CallResponse
from app.utils.file_handler import sanitize_filename, validate_audio_file, estimate_audio_duration
from app.services.speech_to_text import stt_service
from app.services.sentiment import sentiment_service
from app.services.issue_detection import issue_detector
from app.services.priority import priority_calculator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calls", tags=["calls"])

async def process_call_pipeline(call_id: str, file_path: str, pre_transcribed_text: Optional[str] = None):
    collection = db.get_collection("calls")
    try:
        # Step 1: Update status to transcribing
        await collection.update_one(
            {"call_id": call_id},
            {"$set": {"processing_status": "transcribing", "updated_at": datetime.utcnow()}}
        )
        logger.info(f"[{call_id}] Starting transcription...")
        
        # Step 2: Speech-to-Text
        if pre_transcribed_text:
            transcript = pre_transcribed_text
            logger.info(f"[{call_id}] Using pre-transcribed text: '{transcript[:40]}...'")
        else:
            transcript = await stt_service.transcribe(file_path)
            logger.info(f"[{call_id}] Transcription complete: '{transcript[:40]}...'")
        
        # Step 3: Update status to analyzing
        await collection.update_one(
            {"call_id": call_id},
            {"$set": {
                "transcript": transcript,
                "processing_status": "analyzing",
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Step 4: Sentiment Analysis
        sentiment_res = await sentiment_service.analyze(transcript)
        label = sentiment_res["label"]
        confidence = sentiment_res["confidence"]
        logger.info(f"[{call_id}] Sentiment analysis: {label} (conf={confidence:.2f})")
        
        # Step 5: Issue Detection
        detected_issue = issue_detector.detect_issue(transcript)
        logger.info(f"[{call_id}] Issue detected: {detected_issue}")
        
        # Step 6: Priority Calculation
        priority = priority_calculator.calculate_priority(
            sentiment=label,
            confidence=confidence,
            issue=detected_issue,
            transcript=transcript
        )
        
        # Step 7: Save final analysis to MongoDB
        await collection.update_one(
            {"call_id": call_id},
            {"$set": {
                "sentiment_label": label,
                "sentiment_confidence": confidence,
                "detected_issue": detected_issue,
                "priority": priority,
                "processing_status": "completed",
                "updated_at": datetime.utcnow()
            }}
        )
        logger.info(f"[{call_id}] Call processing pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"[{call_id}] Error in call processing pipeline: {e}", exc_info=True)
        await collection.update_one(
            {"call_id": call_id},
            {"$set": {
                "processing_status": "failed",
                "error_message": str(e),
                "updated_at": datetime.utcnow()
            }}
        )

@router.post("/upload", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio(
    file: UploadFile = File(...), 
    transcript: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None
):
    # Read to measure size
    contents = await file.read()
    file_size = len(contents)
    await file.seek(0)
    
    if not validate_audio_file(file.filename, file_size):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported audio format or file exceeds 10MB size limit."
        )
        
    sanitized_name = sanitize_filename(file.filename)
    call_id = str(uuid.uuid4())
    
    # Store audio file on disk
    upload_path = settings.upload_path
    upload_path.mkdir(parents=True, exist_ok=True)
    save_file_path = upload_path / f"{call_id}_{sanitized_name}"
    
    try:
        with open(save_file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        logger.error(f"Failed to write audio file to disk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal disk write error."
        )
        
    # Estimate audio length
    duration = estimate_audio_duration(str(save_file_path))
    
    # Create record in DB
    now = datetime.utcnow()
    call_doc = {
        "call_id": call_id,
        "filename": sanitized_name,
        "filepath": str(save_file_path),
        "upload_time": now,
        "duration": duration,
        "transcript": None,
        "sentiment_label": None,
        "sentiment_confidence": None,
        "detected_issue": None,
        "priority": None,
        "processing_status": "uploading",
        "error_message": None,
        "created_at": now,
        "updated_at": now
    }
    
    await db.get_collection("calls").insert_one(call_doc)
    
    # Trigger async background tasks
    if background_tasks:
        background_tasks.add_task(process_call_pipeline, call_id, str(save_file_path), transcript)
        
    return call_doc

@router.get("", response_model=dict)
async def get_calls(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    sentiment: Optional[str] = None,
    priority: Optional[str] = None,
    issue: Optional[str] = None,
):
    query = {}
    if search:
        query["$or"] = [
            {"filename": {"$regex": search, "$options": "i"}},
            {"transcript": {"$regex": search, "$options": "i"}}
        ]
    if sentiment:
        query["sentiment_label"] = sentiment
    if priority:
        query["priority"] = priority
    if issue:
        query["detected_issue"] = issue
        
    collection = db.get_collection("calls")
    total = await collection.count_documents(query)
    
    skip = (page - 1) * limit
    cursor = collection.find(query).sort("upload_time", -1).skip(skip).limit(limit)
    calls = await cursor.to_list(length=limit)
    
    # Convert MongoDB IDs
    for call in calls:
        call["_id"] = str(call["_id"])
        
    return {
        "calls": calls,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit if total > 0 else 1
    }

@router.get("/high-priority", response_model=List[CallResponse])
async def get_high_priority_calls():
    collection = db.get_collection("calls")
    cursor = collection.find({"priority": "HIGH"}).sort("upload_time", -1)
    calls = await cursor.to_list(length=100)
    return calls

@router.get("/{call_id}", response_model=CallResponse)
async def get_call_details(call_id: str):
    call = await db.get_collection("calls").find_one({"call_id": call_id})
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call record '{call_id}' not found."
        )
    return call

@router.post("/{call_id}/process", response_model=CallResponse)
async def reprocess_call(call_id: str, background_tasks: BackgroundTasks):
    call = await db.get_collection("calls").find_one({"call_id": call_id})
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call record not found."
        )
        
    file_path = call.get("filepath")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source audio file has been deleted from disk."
        )
        
    # Reset processing status
    await db.get_collection("calls").update_one(
        {"call_id": call_id},
        {
            "$set": {
                "processing_status": "uploading",
                "error_message": None,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    background_tasks.add_task(process_call_pipeline, call_id, file_path)
    
    updated_call = await db.get_collection("calls").find_one({"call_id": call_id})
    return updated_call
