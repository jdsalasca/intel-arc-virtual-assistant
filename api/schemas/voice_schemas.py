"""
Voice API Schemas
Pydantic schemas for voice API request/response validation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class TTSRequestSchema(BaseModel):
    """Schema for TTS requests."""
    
    user_id: str
    conversation_id: Optional[str] = None
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: Optional[str] = "female_1"
    speed: float = Field(1.0, ge=0.25, le=4.0)
    pitch: float = Field(1.0, ge=0.5, le=2.0)
    volume: float = Field(1.0, ge=0.1, le=2.0)
    output_format: str = "wav"
    language: str = "en"
    quality: str = "medium"
    provider: str = "speecht5"

class TTSResponseSchema(BaseModel):
    """Schema for TTS responses."""
    
    request_id: str
    status: str
    success: bool
    processing_time: Optional[float] = None
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    model_used: Optional[str] = None
    voice_used: Optional[str] = None
    error_message: Optional[str] = None

class STTRequestSchema(BaseModel):
    """Schema for STT requests."""
    
    user_id: str
    conversation_id: Optional[str] = None
    language: str = "auto"
    enable_punctuation: bool = True
    enable_word_confidence: bool = False
    provider: str = "whisper"

class STTResponseSchema(BaseModel):
    """Schema for STT responses."""
    
    request_id: str
    status: str
    success: bool
    processing_time: Optional[float] = None
    transcript: str = ""
    confidence: Optional[float] = None
    language_detected: Optional[str] = None
    model_used: Optional[str] = None
    error_message: Optional[str] = None

class VoiceSchema(BaseModel):
    """Schema for voice information."""
    
    id: str
    name: str
    display_name: str
    gender: str
    language: str
    description: str
    available: bool = True

class VoiceListSchema(BaseModel):
    """Schema for voice list response."""
    
    voices: List[Dict[str, Any]]