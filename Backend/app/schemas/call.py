from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class SentimentResponse(BaseModel):
    label: str = Field(..., description="positive, neutral, or negative")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")

class CallCreate(BaseModel):
    filename: str
    duration: float = 0.0

class CallResponse(BaseModel):
    call_id: str
    filename: str
    upload_time: datetime
    duration: float
    transcript: Optional[str] = None
    sentiment_label: Optional[str] = None
    sentiment_confidence: Optional[float] = None
    detected_issue: Optional[str] = None
    priority: Optional[str] = None
    processing_status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CallUpdate(BaseModel):
    transcript: Optional[str] = None
    sentiment_label: Optional[str] = None
    sentiment_confidence: Optional[float] = None
    detected_issue: Optional[str] = None
    priority: Optional[str] = None
    processing_status: Optional[str] = None
    error_message: Optional[str] = None
    duration: Optional[float] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
