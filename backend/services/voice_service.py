"""
Voice Service Implementation for Intel Virtual Assistant Backend
Handles text-to-speech and speech-to-text operations.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..interfaces.services import IVoiceService
from ..interfaces.providers import IVoiceProvider
from ..models.domain import VoiceRequest, VoiceResponse

logger = logging.getLogger(__name__)


class VoiceService(IVoiceService):
    """Service for voice synthesis and recognition with Intel optimization."""

    def __init__(
        self,
        tts_provider: IVoiceProvider,
        stt_provider: Optional[IVoiceProvider] = None
    ):
        """Initialize voice service with TTS and optional STT providers."""
        self._tts_provider = tts_provider
        self._stt_provider = stt_provider
        self._available_voices: Dict[str, Any] = {}
        self._voice_cache: Dict[str, VoiceResponse] = {}
        self._cache_enabled = True
        self._max_cache_size = 100
        self._lock = asyncio.Lock()

    async def synthesize_speech(self, request: VoiceRequest) -> VoiceResponse:
        """Convert text to speech."""
        try:
            logger.debug(f"Synthesizing speech for text: {request.text[:50]}...")
            
            # Check cache first
            cache_key = self._generate_cache_key(request)
            if self._cache_enabled and cache_key in self._voice_cache:
                logger.debug("Returning cached voice response")
                return self._voice_cache[cache_key]

            # Validate request
            if not request.text.strip():
                raise ValueError("Text cannot be empty")

            # Use TTS provider to synthesize speech
            audio_data = await self._tts_provider.synthesize(
                text=request.text,
                voice_id=request.voice_id,
                speed=request.speed,
                pitch=request.pitch,
                volume=request.volume
            )

            # Get audio format and metadata from provider
            metadata = await self._tts_provider.get_synthesis_metadata()
            
            response = VoiceResponse(
                audio_data=audio_data,
                format=metadata.get("format", "wav"),
                duration=metadata.get("duration", 0.0),
                sample_rate=metadata.get("sample_rate", 16000),
                metadata={
                    "voice_id": request.voice_id,
                    "synthesis_time": metadata.get("synthesis_time", 0.0),
                    "provider": self._tts_provider.__class__.__name__
                }
            )

            # Cache the response
            await self._cache_response(cache_key, response)

            logger.debug(f"Successfully synthesized speech, duration: {response.duration}s")
            return response

        except Exception as e:
            logger.error(f"Error synthesizing speech: {str(e)}")
            raise

    async def recognize_speech(self, audio_data: bytes) -> str:
        """Convert speech to text."""
        try:
            if not self._stt_provider:
                raise ValueError("Speech-to-text provider not available")

            logger.debug(f"Recognizing speech from {len(audio_data)} bytes of audio")

            # Use STT provider to recognize speech
            text = await self._stt_provider.recognize(audio_data)

            logger.debug(f"Successfully recognized speech: {text[:50]}...")
            return text

        except Exception as e:
            logger.error(f"Error recognizing speech: {str(e)}")
            raise

    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get available voice models."""
        try:
            if not self._available_voices:
                await self._load_available_voices()
            
            return list(self._available_voices.values())

        except Exception as e:
            logger.error(f"Error getting available voices: {str(e)}")
            return []

    async def is_voice_available(self) -> bool:
        """Check if voice services are available."""
        try:
            tts_available = await self._tts_provider.is_available()
            stt_available = (
                await self._stt_provider.is_available() 
                if self._stt_provider else False
            )
            
            return tts_available or stt_available

        except Exception as e:
            logger.error(f"Error checking voice availability: {str(e)}")
            return False

    async def get_voice_status(self) -> Dict[str, Any]:
        """Get detailed status of voice services."""
        try:
            tts_status = await self._tts_provider.get_status()
            stt_status = (
                await self._stt_provider.get_status() 
                if self._stt_provider else {"available": False}
            )

            return {
                "tts": {
                    "available": tts_status.get("available", False),
                    "provider": self._tts_provider.__class__.__name__,
                    "models_loaded": tts_status.get("models_loaded", []),
                    "device": tts_status.get("device", "unknown"),
                    "performance": tts_status.get("performance", {})
                },
                "stt": {
                    "available": stt_status.get("available", False),
                    "provider": self._stt_provider.__class__.__name__ if self._stt_provider else None,
                    "models_loaded": stt_status.get("models_loaded", []),
                    "device": stt_status.get("device", "unknown"),
                    "performance": stt_status.get("performance", {})
                },
                "cache": {
                    "enabled": self._cache_enabled,
                    "size": len(self._voice_cache),
                    "max_size": self._max_cache_size
                }
            }

        except Exception as e:
            logger.error(f"Error getting voice status: {str(e)}")
            return {
                "tts": {"available": False},
                "stt": {"available": False},
                "cache": {"enabled": False, "size": 0, "max_size": 0}
            }

    async def set_voice_settings(self, settings: Dict[str, Any]) -> bool:
        """Update voice service settings."""
        try:
            logger.info(f"Updating voice settings: {settings}")

            # Update cache settings
            if "cache_enabled" in settings:
                self._cache_enabled = settings["cache_enabled"]
            
            if "max_cache_size" in settings:
                self._max_cache_size = settings["max_cache_size"]
                await self._trim_cache()

            # Update provider settings
            if "tts_settings" in settings:
                await self._tts_provider.update_settings(settings["tts_settings"])

            if "stt_settings" in settings and self._stt_provider:
                await self._stt_provider.update_settings(settings["stt_settings"])

            return True

        except Exception as e:
            logger.error(f"Error updating voice settings: {str(e)}")
            return False

    async def clear_cache(self) -> bool:
        """Clear the voice response cache."""
        try:
            async with self._lock:
                self._voice_cache.clear()
            logger.info("Voice cache cleared")
            return True

        except Exception as e:
            logger.error(f"Error clearing voice cache: {str(e)}")
            return False

    async def preload_voices(self, voice_ids: List[str]) -> Dict[str, bool]:
        """Preload specific voices for faster synthesis."""
        try:
            results = {}
            for voice_id in voice_ids:
                try:
                    success = await self._tts_provider.preload_voice(voice_id)
                    results[voice_id] = success
                    logger.info(f"Preloaded voice {voice_id}: {success}")
                except Exception as e:
                    logger.error(f"Error preloading voice {voice_id}: {str(e)}")
                    results[voice_id] = False

            return results

        except Exception as e:
            logger.error(f"Error preloading voices: {str(e)}")
            return {voice_id: False for voice_id in voice_ids}

    async def benchmark_voice(
        self, 
        test_text: str = "This is a test of the voice synthesis system.",
        voice_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Benchmark voice synthesis performance."""
        try:
            logger.info("Running voice synthesis benchmark")
            
            start_time = datetime.now()
            
            request = VoiceRequest(
                text=test_text,
                voice_id=voice_id
            )
            
            response = await self.synthesize_speech(request)
            
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "total_time": total_time,
                "audio_duration": response.duration,
                "real_time_factor": response.duration / total_time if total_time > 0 else 0,
                "text_length": len(test_text),
                "audio_size": len(response.audio_data),
                "sample_rate": response.sample_rate,
                "voice_id": voice_id,
                "timestamp": start_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Error running voice benchmark: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _generate_cache_key(self, request: VoiceRequest) -> str:
        """Generate a cache key for a voice request."""
        return f"{hash(request.text)}_{request.voice_id}_{request.speed}_{request.pitch}_{request.volume}"

    async def _cache_response(self, key: str, response: VoiceResponse) -> None:
        """Cache a voice response."""
        if not self._cache_enabled:
            return

        async with self._lock:
            self._voice_cache[key] = response
            await self._trim_cache()

    async def _trim_cache(self) -> None:
        """Trim cache to maximum size."""
        if len(self._voice_cache) > self._max_cache_size:
            # Remove oldest entries (simple FIFO strategy)
            items_to_remove = len(self._voice_cache) - self._max_cache_size
            keys_to_remove = list(self._voice_cache.keys())[:items_to_remove]
            
            for key in keys_to_remove:
                del self._voice_cache[key]

    async def _load_available_voices(self) -> None:
        """Load available voices from the TTS provider."""
        try:
            voices = await self._tts_provider.get_available_voices()
            self._available_voices = {voice["id"]: voice for voice in voices}
            logger.info(f"Loaded {len(self._available_voices)} available voices")

        except Exception as e:
            logger.error(f"Error loading available voices: {str(e)}")
            self._available_voices = {}