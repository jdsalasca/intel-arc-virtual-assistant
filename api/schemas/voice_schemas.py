"""
Voice API Schemas
Pydantic schemas for voice API endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class TTSRequestSchema(BaseModel):
    """TTS request schema."""
    text: str = Field(..., min_length=1, max_length=5000)
    user_id: str
    conversation_id: Optional[str] = None
    voice_id: Optional[str] = "default"
    speed: float = Field(1.0, ge=0.5, le=2.0)
    pitch: float = Field(1.0, ge=0.5, le=2.0)
    volume: float = Field(1.0, ge=0.1, le=2.0)
    output_format: str = "wav"
    language: str = "en"
    quality: str = "medium"
    provider: str = "speecht5"

class TTSResponseSchema(BaseModel):
    """TTS response schema."""
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
    """STT request schema."""
    user_id: str
    conversation_id: Optional[str] = None
    language: str = "auto"
    enable_punctuation: bool = True
    enable_word_confidence: bool = False

class STTResponseSchema(BaseModel):
    """STT response schema."""
    request_id: str
    status: str
    success: bool
    processing_time: Optional[float] = None
    transcript: Optional[str] = None
    confidence: Optional[float] = None
    language_detected: Optional[str] = None
    model_used: Optional[str] = None
    error_message: Optional[str] = None

class VoiceInfo(BaseModel):
    """Voice information."""
    id: str
    name: str
    display_name: str
    gender: str
    language: str
    description: str
    available: bool = True

class VoiceListSchema(BaseModel):
    """Voice list response."""
    voices: List[VoiceInfo]