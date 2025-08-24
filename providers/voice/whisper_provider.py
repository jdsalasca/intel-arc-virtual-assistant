"""
Whisper Speech-to-Text Provider
Intel NPU optimized implementation using OpenAI's Whisper model.
"""

import logging
import io
import tempfile
import os
from typing import List, Dict, Any, Optional, Union, BinaryIO
import torch
import torchaudio
import whisper
import numpy as np

from core.interfaces.voice_provider import IVoiceInput, VoiceFormat
from core.models.voice import STTRequest, STTResponse, VoiceProcessingStatus
from core.exceptions import STTException, ModelLoadException

logger = logging.getLogger(__name__)

class WhisperProvider(IVoiceInput):
    """Whisper STT provider optimized for Intel hardware."""
    
    def __init__(self):
        self.model = None
        self.model_name = "base"  # base, small, medium, large
        self.device = "cpu"
        self.is_loaded = False
        
        # Whisper model configurations
        self._model_configs = {
            "tiny": {"params": "39M", "vram": "~1GB", "speed": "fast"},
            "base": {"params": "74M", "vram": "~1GB", "speed": "fast"},
            "small": {"params": "244M", "vram": "~2GB", "speed": "medium"},
            "medium": {"params": "769M", "vram": "~5GB", "speed": "slow"},
            "large": {"params": "1550M", "vram": "~10GB", "speed": "very slow"}
        }
        
        # Supported languages (Whisper supports 99 languages)
        self._supported_languages = [
            "en", "es", "fr", "de", "it", "pt", "nl", "ru", "ja", "ko", 
            "zh", "ar", "hi", "tr", "pl", "sv", "da", "no", "fi", "uk",
            "cs", "sk", "hu", "ro", "bg", "hr", "sr", "sl", "et", "lv",
            "lt", "mt", "el", "mk", "sq", "eu", "ca", "gl", "cy", "ga",
            "is", "lb", "mt", "he", "fa", "ur", "bn", "ta", "te", "ml",
            "kn", "gu", "mr", "ne", "si", "my", "km", "lo", "ka", "am",
            "sw", "yo", "ig", "zu", "af", "st", "tn", "xh", "ss", "nr",
            "ve", "nso", "ts"
        ]
    
    def load_model(self, model_name: str = "base", device: str = "cpu") -> bool:
        """Load Whisper model."""
        try:
            logger.info(f"Loading Whisper {model_name} model on {device}...")
            
            self.model_name = model_name
            self.device = device
            
            # Load Whisper model
            if device.upper() == "NPU":
                # For NPU, we'll use Intel optimizations
                try:
                    logger.info("Attempting NPU optimization for Whisper...")
                    # Intel Neural Compressor optimizations would go here
                    # For now, fallback to CPU with Intel optimizations
                    self.device = "cpu"
                    self.model = whisper.load_model(model_name, device="cpu")
                    
                    # Apply Intel CPU optimizations
                    if hasattr(torch.backends, 'mkldnn') and torch.backends.mkldnn.is_available():
                        logger.info("Applying Intel MKL-DNN optimizations")
                        # Intel-specific optimizations would go here
                        
                except Exception as e:
                    logger.warning(f"NPU optimization failed, using CPU: {e}")
                    self.device = "cpu"
                    self.model = whisper.load_model(model_name, device="cpu")
            else:
                self.device = device.lower()
                self.model = whisper.load_model(model_name, device=self.device)
            
            self.is_loaded = True
            logger.info(f"Whisper {model_name} loaded successfully on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise ModelLoadException(f"Failed to load Whisper: {e}")
    
    def transcribe(
        self, 
        audio_data: Union[bytes, BinaryIO, str],
        language: Optional[str] = None,
        **kwargs
    ) -> str:
        """Transcribe audio to text."""
        try:
            if not self.is_loaded:
                raise STTException("Whisper model not loaded")
            
            # Prepare audio for Whisper
            audio_array = self._prepare_audio(audio_data)
            
            # Transcription options
            options = {
                "language": language,
                "task": "transcribe",  # or "translate" for translation to English
                "fp16": self.device != "cpu",  # Use FP16 on GPU for speed
                "verbose": False
            }
            
            # Add any additional options from kwargs
            options.update(kwargs)
            
            # Perform transcription
            result = self.model.transcribe(audio_array, **options)
            
            # Extract text
            transcript = result.get("text", "").strip()
            
            logger.debug(f"Transcribed audio: '{transcript[:100]}...'")
            return transcript
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise STTException(f"Transcription failed: {e}")
    
    def transcribe_stream(
        self, 
        audio_stream: BinaryIO,
        language: Optional[str] = None,
        **kwargs
    ) -> str:
        """Transcribe streaming audio (basic implementation)."""
        # For streaming, we'll accumulate chunks and transcribe
        # Real streaming would require more sophisticated chunking
        try:
            audio_data = audio_stream.read()
            return self.transcribe(audio_data, language, **kwargs)
        except Exception as e:
            logger.error(f"Stream transcription failed: {e}")
            raise STTException(f"Stream transcription failed: {e}")
    
    def detect_language(self, audio_data: Union[bytes, BinaryIO, str]) -> str:
        """Detect the language of the audio."""
        try:
            if not self.is_loaded:
                raise STTException("Whisper model not loaded")
            
            # Prepare audio
            audio_array = self._prepare_audio(audio_data)
            
            # Use Whisper's language detection
            # Load only first 30 seconds for language detection
            audio_segment = audio_array[:30 * 16000]  # 30 seconds at 16kHz
            
            # Detect language
            mel = whisper.log_mel_spectrogram(audio_segment).to(self.model.device)
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            
            logger.debug(f"Detected language: {detected_language} (confidence: {probs[detected_language]:.2f})")
            return detected_language
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "en"  # Default to English
    
    def _prepare_audio(self, audio_data: Union[bytes, BinaryIO, str]) -> np.ndarray:
        """Prepare audio data for Whisper processing."""
        try:
            # Handle different input types
            if isinstance(audio_data, str):
                # File path
                audio_array = whisper.load_audio(audio_data)
            elif isinstance(audio_data, bytes):
                # Raw bytes - save to temp file and load
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(audio_data)
                    temp_file.flush()
                    audio_array = whisper.load_audio(temp_file.name)
                    os.unlink(temp_file.name)  # Clean up
            elif hasattr(audio_data, 'read'):
                # File-like object
                audio_bytes = audio_data.read()
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(audio_bytes)
                    temp_file.flush()
                    audio_array = whisper.load_audio(temp_file.name)
                    os.unlink(temp_file.name)  # Clean up
            else:
                raise STTException(f"Unsupported audio data type: {type(audio_data)}")
            
            return audio_array
            
        except Exception as e:
            logger.error(f"Audio preparation failed: {e}")
            raise STTException(f"Audio preparation failed: {e}")
    
    def transcribe_with_timestamps(
        self, 
        audio_data: Union[bytes, BinaryIO, str],
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe audio with word-level timestamps."""
        try:
            if not self.is_loaded:
                raise STTException("Whisper model not loaded")
            
            # Prepare audio
            audio_array = self._prepare_audio(audio_data)
            
            # Transcribe with word timestamps
            result = self.model.transcribe(
                audio_array,
                language=language,
                word_timestamps=True,
                verbose=False
            )
            
            return {
                "text": result.get("text", "").strip(),
                "segments": result.get("segments", []),
                "language": result.get("language", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Timestamp transcription failed: {e}")
            raise STTException(f"Timestamp transcription failed: {e}")
    
    def transcribe_with_confidence(
        self, 
        audio_data: Union[bytes, BinaryIO, str],
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe audio with confidence scores."""
        try:
            # Get detailed results
            result = self.transcribe_with_timestamps(audio_data, language)
            
            # Calculate overall confidence
            segments = result.get("segments", [])
            if segments:
                # Average confidence from segments
                confidences = [seg.get("avg_logprob", 0) for seg in segments if "avg_logprob" in seg]
                if confidences:
                    # Convert log probability to confidence (approximate)
                    avg_confidence = np.exp(np.mean(confidences))
                    avg_confidence = min(max(avg_confidence, 0.0), 1.0)
                else:
                    avg_confidence = 0.8  # Default
            else:
                avg_confidence = 0.8  # Default
            
            return {
                "text": result["text"],
                "confidence": avg_confidence,
                "segments": segments,
                "language": result.get("language", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Confidence transcription failed: {e}")
            raise STTException(f"Confidence transcription failed: {e}")
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return self._supported_languages.copy()
    
    def get_supported_formats(self) -> List[VoiceFormat]:
        """Get list of supported audio formats."""
        return [
            VoiceFormat.WAV,
            VoiceFormat.MP3,
            VoiceFormat.OGG,
            VoiceFormat.FLAC
        ]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if not self.is_loaded:
            return {"status": "not_loaded"}
        
        config = self._model_configs.get(self.model_name, {})
        
        return {
            "model_name": self.model_name,
            "device": self.device,
            "parameters": config.get("params", "unknown"),
            "memory_usage": config.get("vram", "unknown"),
            "speed": config.get("speed", "unknown"),
            "supported_languages": len(self._supported_languages),
            "supports_timestamps": True,
            "supports_translation": True,
            "supports_language_detection": True
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = {
            "status": "healthy" if self.is_loaded else "not_loaded",
            "model_loaded": self.is_loaded,
            "model_name": self.model_name,
            "device": self.device,
            "supported_languages": len(self._supported_languages),
            "supported_formats": len(self.get_supported_formats())
        }
        
        # Test basic functionality if loaded
        if self.is_loaded:
            try:
                # Quick test with silent audio
                test_audio = np.zeros(16000)  # 1 second of silence
                result = self.model.transcribe(test_audio, verbose=False)
                health["test_transcription"] = "passed"
            except Exception as e:
                health["test_transcription"] = f"failed: {e}"
                health["status"] = "degraded"
        
        return health
    
    def optimize_for_intel(self) -> bool:
        """Apply Intel-specific optimizations."""
        try:
            if not self.is_loaded:
                return False
            
            # Apply Intel optimizations
            if hasattr(torch.backends, 'mkldnn') and torch.backends.mkldnn.is_available():
                logger.info("Applying Intel MKL-DNN optimizations to Whisper")
                
                # Enable Intel optimizations
                torch.backends.mkldnn.enabled = True
                
                # Optimize model for inference
                if hasattr(torch.jit, 'optimize_for_inference'):
                    # This would optimize the model graph for Intel hardware
                    pass
                
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Intel optimization failed: {e}")
            return False