"""
Voice Service for orchestrating TTS and STT operations.
Manages voice providers and handles Intel hardware optimization.
"""

import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid

from core.interfaces.voice_provider import IVoiceInput, IVoiceOutput, VoiceFormat
from core.models.voice import (
    TTSRequest, TTSResponse, STTRequest, STTResponse, 
    VoiceProcessingStatus
)
from core.exceptions import VoiceException, TTSException, STTException
from services.intel_optimizer import IntelOptimizer

logger = logging.getLogger(__name__)

class VoiceService:
    """Voice service for TTS and STT operations."""
    
    def __init__(self, intel_optimizer: IntelOptimizer):
        self.intel_optimizer = intel_optimizer
        
        # Voice providers
        self._tts_providers: Dict[str, IVoiceOutput] = {}
        self._stt_providers: Dict[str, IVoiceInput] = {}
        
        # Active requests tracking
        self._active_requests: Dict[str, Dict[str, Any]] = {}
        
        # Performance stats
        self._tts_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "total_characters": 0,
            "total_duration": 0.0,
            "average_speed": 0.0  # characters per second
        }
        
        self._stt_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "total_audio_duration": 0.0,
            "total_processing_time": 0.0,
            "average_realtime_factor": 0.0
        }
    
    def register_tts_provider(self, name: str, provider: IVoiceOutput) -> None:
        """Register a TTS provider."""
        self._tts_providers[name] = provider
        logger.info(f"Registered TTS provider: {name}")
    
    def register_stt_provider(self, name: str, provider: IVoiceInput) -> None:
        """Register an STT provider."""
        self._stt_providers[name] = provider
        logger.info(f"Registered STT provider: {name}")
    
    async def initialize_providers(self) -> None:
        """Initialize voice providers with optimal devices."""
        try:
            # Initialize TTS providers
            for name, provider in self._tts_providers.items():
                try:
                    # Get optimal device for TTS
                    device = self.intel_optimizer.select_optimal_device("speecht5-tts", "tts")
                    
                    # Load model if provider supports it
                    if hasattr(provider, 'load_model'):
                        success = provider.load_model(device)
                        if success:
                            logger.info(f"TTS provider {name} loaded on {device}")
                        else:
                            logger.warning(f"Failed to load TTS provider {name}")
                except Exception as e:
                    logger.error(f"Error initializing TTS provider {name}: {e}")
            
            # Initialize STT providers
            for name, provider in self._stt_providers.items():
                try:
                    # Get optimal device for STT
                    device = self.intel_optimizer.select_optimal_device("whisper-base", "stt")
                    
                    # Load model if provider supports it
                    if hasattr(provider, 'load_model'):
                        success = provider.load_model(device)
                        if success:
                            logger.info(f"STT provider {name} loaded on {device}")
                        else:
                            logger.warning(f"Failed to load STT provider {name}")
                except Exception as e:
                    logger.error(f"Error initializing STT provider {name}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to initialize voice providers: {e}")
            raise VoiceException(f"Provider initialization failed: {e}")
    
    async def text_to_speech(
        self,
        request: TTSRequest,
        provider_name: str = "speecht5"
    ) -> TTSResponse:
        """Convert text to speech."""
        try:
            # Get provider
            provider = self._tts_providers.get(provider_name)
            if not provider:
                raise TTSException(f"TTS provider {provider_name} not found")
            
            # Track request
            self._active_requests[request.id] = {
                "type": "tts",
                "provider": provider_name,
                "started_at": datetime.utcnow(),
                "status": VoiceProcessingStatus.PROCESSING
            }
            
            start_time = time.time()
            
            # Synthesize speech
            audio_data = provider.synthesize(
                text=request.text,
                voice_id=request.voice_id,
                speed=request.speed,
                pitch=request.pitch,
                volume=request.volume,
                output_format=request.output_format
            )
            
            processing_time = time.time() - start_time
            
            # Create response
            response = TTSResponse(
                request_id=request.id,
                status=VoiceProcessingStatus.COMPLETED,
                success=True,
                processing_time=processing_time,
                audio_data=audio_data,
                audio_format=request.output_format,
                duration=self._estimate_audio_duration(audio_data, request.output_format),
                model_used=provider_name,
                voice_used=request.voice_id,
                text_length=len(request.text),
                audio_size=len(audio_data),
                completed_at=datetime.utcnow()
            )
            
            # Update stats
            self._update_tts_stats(request, response, processing_time)
            
            # Clean up tracking
            if request.id in self._active_requests:
                del self._active_requests[request.id]
            
            logger.info(f"TTS completed in {processing_time:.2f}s for {len(request.text)} characters")
            return response
            
        except Exception as e:
            # Update tracking with error
            if request.id in self._active_requests:
                self._active_requests[request.id]["status"] = VoiceProcessingStatus.FAILED
            
            logger.error(f"TTS failed for request {request.id}: {e}")
            return TTSResponse(
                request_id=request.id,
                status=VoiceProcessingStatus.FAILED,
                success=False,
                error_message=str(e),
                model_used=provider_name,
                completed_at=datetime.utcnow()
            )
    
    async def speech_to_text(
        self,
        request: STTRequest,
        provider_name: str = "whisper"
    ) -> STTResponse:
        """Convert speech to text."""
        try:
            # Get provider
            provider = self._stt_providers.get(provider_name)
            if not provider:
                raise STTException(f"STT provider {provider_name} not found")
            
            # Track request
            self._active_requests[request.id] = {
                "type": "stt",
                "provider": provider_name,
                "started_at": datetime.utcnow(),
                "status": VoiceProcessingStatus.PROCESSING
            }
            
            start_time = time.time()
            
            # Transcribe audio
            if request.audio_data:
                transcript = provider.transcribe(
                    audio_data=request.audio_data,
                    language=request.language if request.language != "auto" else None
                )
            elif request.audio_url:
                transcript = provider.transcribe(
                    audio_data=request.audio_url,
                    language=request.language if request.language != "auto" else None
                )
            else:
                raise STTException("No audio data provided")
            
            processing_time = time.time() - start_time
            
            # Detect language if not specified
            detected_language = request.language
            if request.language == "auto" and hasattr(provider, 'detect_language'):
                try:
                    detected_language = provider.detect_language(request.audio_data or request.audio_url)
                except:
                    detected_language = "en"  # Default fallback
            
            # Create response
            response = STTResponse(
                request_id=request.id,
                status=VoiceProcessingStatus.COMPLETED,
                success=True,
                processing_time=processing_time,
                transcript=transcript,
                confidence=0.95,  # Default confidence - would come from actual model
                language_detected=detected_language,
                model_used=provider_name,
                completed_at=datetime.utcnow()
            )
            
            # Update stats
            self._update_stt_stats(request, response, processing_time)
            
            # Clean up tracking
            if request.id in self._active_requests:
                del self._active_requests[request.id]
            
            logger.info(f"STT completed in {processing_time:.2f}s: '{transcript[:50]}...'")
            return response
            
        except Exception as e:
            # Update tracking with error
            if request.id in self._active_requests:
                self._active_requests[request.id]["status"] = VoiceProcessingStatus.FAILED
            
            logger.error(f"STT failed for request {request.id}: {e}")
            return STTResponse(
                request_id=request.id,
                status=VoiceProcessingStatus.FAILED,
                success=False,
                error_message=str(e),
                model_used=provider_name,
                completed_at=datetime.utcnow()
            )
    
    def _estimate_audio_duration(self, audio_data: bytes, format: VoiceFormat) -> float:
        """Estimate audio duration from data size."""
        try:
            # Rough estimation based on format and size
            # These are approximations - actual duration would require audio parsing
            if format == VoiceFormat.WAV:
                # WAV: ~16kHz * 16bit * 1channel = ~32KB per second
                return len(audio_data) / 32000
            elif format == VoiceFormat.MP3:
                # MP3: ~128kbps = ~16KB per second
                return len(audio_data) / 16000
            else:
                # Default estimation
                return len(audio_data) / 20000
        except:
            return 0.0
    
    def _update_tts_stats(self, request: TTSRequest, response: TTSResponse, processing_time: float):
        """Update TTS performance statistics."""
        try:
            self._tts_stats["total_requests"] += 1
            if response.success:
                self._tts_stats["successful_requests"] += 1
                self._tts_stats["total_characters"] += len(request.text)
                self._tts_stats["total_duration"] += processing_time
                
                if self._tts_stats["total_duration"] > 0:
                    self._tts_stats["average_speed"] = (
                        self._tts_stats["total_characters"] / self._tts_stats["total_duration"]
                    )
        except Exception as e:
            logger.debug(f"Failed to update TTS stats: {e}")
    
    def _update_stt_stats(self, request: STTRequest, response: STTResponse, processing_time: float):
        """Update STT performance statistics."""
        try:
            self._stt_stats["total_requests"] += 1
            if response.success:
                self._stt_stats["successful_requests"] += 1
                self._stt_stats["total_processing_time"] += processing_time
                
                # Estimate audio duration (would be better to get from actual audio)
                estimated_audio_duration = 5.0  # Default estimate
                self._stt_stats["total_audio_duration"] += estimated_audio_duration
                
                if self._stt_stats["total_audio_duration"] > 0:
                    self._stt_stats["average_realtime_factor"] = (
                        self._stt_stats["total_processing_time"] / self._stt_stats["total_audio_duration"]
                    )
        except Exception as e:
            logger.debug(f"Failed to update STT stats: {e}")
    
    def get_available_voices(self, provider_name: str = "speecht5") -> List[Dict[str, Any]]:
        """Get available voices from a TTS provider."""
        try:
            provider = self._tts_providers.get(provider_name)
            if provider:
                return provider.get_available_voices()
            return []
        except Exception as e:
            logger.error(f"Failed to get voices from {provider_name}: {e}")
            return []
    
    def get_supported_languages(self, provider_name: str = "speecht5", provider_type: str = "tts") -> List[str]:
        """Get supported languages from a provider."""
        try:
            if provider_type == "tts":
                provider = self._tts_providers.get(provider_name)
            else:
                provider = self._stt_providers.get(provider_name)
                
            if provider:
                return provider.get_supported_languages()
            return []
        except Exception as e:
            logger.error(f"Failed to get languages from {provider_name}: {e}")
            return []
    
    def get_voice_stats(self) -> Dict[str, Any]:
        """Get voice processing statistics."""
        return {
            "tts": self._tts_stats.copy(),
            "stt": self._stt_stats.copy(),
            "active_requests": len(self._active_requests),
            "providers": {
                "tts": list(self._tts_providers.keys()),
                "stt": list(self._stt_providers.keys())
            }
        }
    
    def get_active_requests(self) -> Dict[str, Any]:
        """Get currently active voice processing requests."""
        return self._active_requests.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on voice service."""
        try:
            health = {
                "status": "healthy",
                "providers": {
                    "tts": {},
                    "stt": {}
                },
                "stats": self.get_voice_stats(),
                "errors": []
            }
            
            # Check TTS providers
            for name, provider in self._tts_providers.items():
                try:
                    if hasattr(provider, 'health_check'):
                        provider_health = provider.health_check()
                        health["providers"]["tts"][name] = provider_health
                    else:
                        health["providers"]["tts"][name] = {"status": "unknown"}
                except Exception as e:
                    health["providers"]["tts"][name] = {"status": "error", "error": str(e)}
                    health["errors"].append(f"TTS provider {name}: {e}")
            
            # Check STT providers
            for name, provider in self._stt_providers.items():
                try:
                    if hasattr(provider, 'health_check'):
                        provider_health = provider.health_check()
                        health["providers"]["stt"][name] = provider_health
                    else:
                        health["providers"]["stt"][name] = {"status": "unknown"}
                except Exception as e:
                    health["providers"]["stt"][name] = {"status": "error", "error": str(e)}
                    health["errors"].append(f"STT provider {name}: {e}")
            
            if health["errors"]:
                health["status"] = "degraded"
            
            return health
            
        except Exception as e:
            logger.error(f"Voice service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def cleanup_old_requests(self, max_age_minutes: int = 60) -> int:
        """Clean up old tracked requests."""
        try:
            cutoff_time = datetime.utcnow().timestamp() - (max_age_minutes * 60)
            
            requests_to_remove = []
            for request_id, request_info in self._active_requests.items():
                if request_info["started_at"].timestamp() < cutoff_time:
                    requests_to_remove.append(request_id)
            
            for request_id in requests_to_remove:
                del self._active_requests[request_id]
            
            if requests_to_remove:
                logger.info(f"Cleaned up {len(requests_to_remove)} old voice requests")
            
            return len(requests_to_remove)
            
        except Exception as e:
            logger.error(f"Failed to cleanup old requests: {e}")
            return 0