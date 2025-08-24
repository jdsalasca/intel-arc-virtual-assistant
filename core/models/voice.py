"""
Voice Models
Basic models for voice processing requests and responses.
"""

import uuid
from typing import Optional, List, Any, Dict
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from core.interfaces.voice_provider import VoiceFormat, VoiceGender, SpeechQuality

@dataclass
class TTSRequest:
    """Text-to-speech request."""
    user_id: str
    text: str
    voice_id: Optional[str] = None
    conversation_id: Optional[str] = None
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    output_format: VoiceFormat = VoiceFormat.WAV
    language: str = "en"
    quality: SpeechQuality = SpeechQuality.MEDIUM
    id: str = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())

@dataclass
class TTSResponse:
    """Text-to-speech response."""
    request_id: str
    success: bool
    audio_data: Optional[bytes] = None
    duration: Optional[float] = None
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    voice_used: Optional[str] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None

@dataclass
class STTRequest:
    """Speech-to-text request."""
    user_id: str
    audio_data: Optional[bytes] = None
    audio_url: Optional[str] = None
    audio_format: VoiceFormat = VoiceFormat.WAV
    conversation_id: Optional[str] = None
    language: str = "auto"
    enable_punctuation: bool = True
    enable_word_confidence: bool = False
    id: str = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())

@dataclass 
class STTResponse:
    """Speech-to-text response."""
    request_id: str
    success: bool
    transcript: Optional[str] = None
    confidence: Optional[float] = None
    language_detected: Optional[str] = None
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None

class VoiceProcessingStatus(str, Enum):
    """Status of voice processing operations."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"