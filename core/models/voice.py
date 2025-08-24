"""
Core data models for voice processing.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
import uuid

class AudioFormat(str, Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"
    AAC = "aac"

class VoiceGender(str, Enum):
    """Voice gender options."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"

class SpeechQuality(str, Enum):
    """Speech quality levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"

class VoiceProcessingStatus(str, Enum):
    """Status of voice processing operations."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VoiceRequest(BaseModel):
    """Request for voice processing operations."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    conversation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Request type
    operation: str  # "tts", "stt", "voice_clone", etc.
    
    # Common parameters
    language: str = "en"
    quality: SpeechQuality = SpeechQuality.MEDIUM
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TTSRequest(VoiceRequest):
    """Text-to-speech request."""
    
    text: str
    voice_id: Optional[str] = None
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    output_format: AudioFormat = AudioFormat.WAV
    
    # Advanced TTS options
    emphasis: List[str] = Field(default_factory=list)
    pauses: Dict[int, float] = Field(default_factory=dict)  # position: pause_duration
    pronunciation: Dict[str, str] = Field(default_factory=dict)  # word: phonetic

class STTRequest(VoiceRequest):
    """Speech-to-text request."""
    
    audio_data: Optional[bytes] = None  # Will be set separately for security
    audio_url: Optional[str] = None
    audio_format: AudioFormat = AudioFormat.WAV
    
    # STT options
    enable_punctuation: bool = True
    enable_word_confidence: bool = False
    enable_speaker_diarization: bool = False
    custom_vocabulary: List[str] = Field(default_factory=list)

class VoiceResponse(BaseModel):
    """Response from voice processing operations."""
    
    request_id: str
    status: VoiceProcessingStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    
    # Results
    success: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TTSResponse(VoiceResponse):
    """Text-to-speech response."""
    
    audio_data: Optional[bytes] = None  # Will be handled separately
    audio_url: Optional[str] = None
    audio_format: AudioFormat = AudioFormat.WAV
    duration: Optional[float] = None
    
    # Generation metadata
    model_used: str
    voice_used: Optional[str] = None
    text_length: int = 0
    audio_size: int = 0

class STTResponse(VoiceResponse):
    """Speech-to-text response."""
    
    transcript: str = ""
    confidence: float = 0.0
    language_detected: Optional[str] = None
    
    # Advanced STT results
    word_timestamps: List[Dict[str, Any]] = Field(default_factory=list)
    speaker_segments: List[Dict[str, Any]] = Field(default_factory=list)
    alternative_transcripts: List[str] = Field(default_factory=list)
    
    # Processing metadata
    model_used: str
    audio_duration: Optional[float] = None
    processing_speed: Optional[float] = None  # realtime factor

class Voice(BaseModel):
    """Voice profile for TTS."""
    
    id: str
    name: str
    display_name: str
    language: str
    gender: VoiceGender
    accent: Optional[str] = None
    age_group: Optional[str] = None  # child, young_adult, adult, senior
    
    # Voice characteristics
    description: str = ""
    sample_rate: int = 22050
    supported_formats: List[AudioFormat] = Field(default_factory=lambda: [AudioFormat.WAV])
    
    # Quality and capabilities
    quality: SpeechQuality = SpeechQuality.MEDIUM
    supports_emotions: bool = False
    supports_speed_control: bool = True
    supports_pitch_control: bool = True
    
    # Availability
    is_available: bool = True
    is_premium: bool = False
    provider: str = "default"
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AudioFile(BaseModel):
    """Audio file metadata."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_filename: Optional[str] = None
    file_path: str
    url: Optional[str] = None
    
    # Audio properties
    format: AudioFormat
    duration: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    bitrate: Optional[int] = None
    file_size: int = 0
    
    # Processing metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    user_id: str
    conversation_id: Optional[str] = None
    
    # Content metadata
    transcript: Optional[str] = None
    language: Optional[str] = None
    confidence: Optional[float] = None
    
    # Storage metadata
    storage_provider: str = "local"
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class VoiceSettings(BaseModel):
    """User voice settings and preferences."""
    
    user_id: str
    
    # TTS preferences
    preferred_voice_id: Optional[str] = None
    default_speed: float = 1.0
    default_pitch: float = 1.0
    default_volume: float = 1.0
    preferred_format: AudioFormat = AudioFormat.WAV
    
    # STT preferences
    preferred_language: str = "en"
    enable_punctuation: bool = True
    enable_word_confidence: bool = False
    
    # Processing preferences
    preferred_quality: SpeechQuality = SpeechQuality.MEDIUM
    auto_play_tts: bool = True
    auto_transcribe: bool = True
    
    # Privacy settings
    save_audio_files: bool = False
    audio_retention_days: int = 7
    
    # Updated timestamp
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }