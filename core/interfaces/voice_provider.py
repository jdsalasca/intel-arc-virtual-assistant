"""
Core interfaces for voice providers.
Defines abstractions for text-to-speech and speech-to-text engines.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, BinaryIO
from enum import Enum
import io

class VoiceFormat(Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"

class VoiceGender(Enum):
    """Voice gender options."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"

class SpeechQuality(Enum):
    """Speech quality levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"

class IVoiceInput(ABC):
    """Abstract interface for speech-to-text providers."""
    
    @abstractmethod
    def transcribe(
        self, 
        audio_data: Union[bytes, BinaryIO, str],
        language: Optional[str] = None,
        **kwargs
    ) -> str:
        """Transcribe audio to text."""
        pass
    
    @abstractmethod
    def transcribe_stream(
        self, 
        audio_stream: BinaryIO,
        language: Optional[str] = None,
        **kwargs
    ) -> str:
        """Transcribe streaming audio to text."""
        pass
    
    @abstractmethod
    def detect_language(self, audio_data: Union[bytes, BinaryIO, str]) -> str:
        """Detect the language of the audio."""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[VoiceFormat]:
        """Get list of supported audio formats."""
        pass

class IVoiceOutput(ABC):
    """Abstract interface for text-to-speech providers."""
    
    @abstractmethod
    def synthesize(
        self, 
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0,
        volume: float = 1.0,
        output_format: VoiceFormat = VoiceFormat.WAV,
        **kwargs
    ) -> bytes:
        """Synthesize text to speech audio."""
        pass
    
    @abstractmethod
    def synthesize_stream(
        self, 
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0,
        volume: float = 1.0,
        output_format: VoiceFormat = VoiceFormat.WAV,
        **kwargs
    ) -> BinaryIO:
        """Synthesize text to speech with streaming."""
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices."""
        pass
    
    @abstractmethod
    def preview_voice(self, voice_id: str, text: str = "Hello, this is a voice preview.") -> bytes:
        """Generate a preview of a voice."""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[VoiceFormat]:
        """Get list of supported output formats."""
        pass

class IVoiceProcessor(ABC):
    """Abstract interface for voice processing utilities."""
    
    @abstractmethod
    def convert_format(
        self, 
        audio_data: bytes, 
        source_format: VoiceFormat, 
        target_format: VoiceFormat
    ) -> bytes:
        """Convert audio between formats."""
        pass
    
    @abstractmethod
    def adjust_volume(self, audio_data: bytes, volume_factor: float) -> bytes:
        """Adjust audio volume."""
        pass
    
    @abstractmethod
    def normalize_audio(self, audio_data: bytes) -> bytes:
        """Normalize audio levels."""
        pass
    
    @abstractmethod
    def trim_silence(self, audio_data: bytes, threshold: float = 0.01) -> bytes:
        """Remove silence from beginning and end."""
        pass
    
    @abstractmethod
    def get_audio_duration(self, audio_data: bytes) -> float:
        """Get duration of audio in seconds."""
        pass
    
    @abstractmethod
    def extract_features(self, audio_data: bytes) -> Dict[str, Any]:
        """Extract audio features for analysis."""
        pass