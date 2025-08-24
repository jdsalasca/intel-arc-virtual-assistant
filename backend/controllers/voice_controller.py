"""
Voice Controller for Intel Virtual Assistant Backend
FastAPI endpoints for text-to-speech and voice management.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
import base64

from ..interfaces.services import IVoiceService
from ..models.domain import VoiceRequest

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/voice", tags=["voice"])


from ..config.container import get_voice_service


# Dependency injection function is imported from container


@router.post("/tts")
async def text_to_speech(
    request: VoiceRequest,
    format: str = "wav",
    voice_service: IVoiceService = Depends(get_voice_service)
):
    """Convert text to speech."""
    try:
        logger.info(f"TTS request: {request.text[:50]}...")
        
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(request.text) > 5000:
            raise HTTPException(status_code=400, detail="Text too long (max 5000 characters)")
        
        if not (0.5 <= request.speed <= 2.0):
            raise HTTPException(status_code=400, detail="Speed must be between 0.5 and 2.0")
        
        if not (0.5 <= request.pitch <= 2.0):
            raise HTTPException(status_code=400, detail="Pitch must be between 0.5 and 2.0")
        
        if not (0.1 <= request.volume <= 2.0):
            raise HTTPException(status_code=400, detail="Volume must be between 0.1 and 2.0")
        
        # Check if voice service is available
        if not await voice_service.is_voice_available():
            raise HTTPException(status_code=503, detail="Voice service not available")
        
        # Synthesize speech
        voice_response = await voice_service.synthesize_speech(request)
        
        # Return audio response
        if format.lower() == "base64":
            # Return base64 encoded audio
            audio_b64 = base64.b64encode(voice_response.audio_data).decode('utf-8')
            return {
                "audio_base64": audio_b64,
                "format": voice_response.format,
                "duration": voice_response.duration,
                "sample_rate": voice_response.sample_rate,
                "metadata": voice_response.metadata
            }
        else:
            # Return raw audio data
            media_type = "audio/wav" if voice_response.format == "wav" else "audio/mpeg"
            return Response(
                content=voice_response.audio_data,
                media_type=media_type,
                headers={
                    "Content-Disposition": f"attachment; filename=speech.{voice_response.format}",
                    "X-Duration": str(voice_response.duration),
                    "X-Sample-Rate": str(voice_response.sample_rate)
                }
            )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid TTS request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in TTS: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stt")
async def speech_to_text(
    # This would typically receive audio data
    voice_service: IVoiceService = Depends(get_voice_service)
):
    """Convert speech to text (placeholder - would need audio upload handling)."""
    try:
        # This is a placeholder - real implementation would handle audio upload
        raise HTTPException(status_code=501, detail="Speech-to-text not yet implemented")
        
    except Exception as e:
        logger.error(f"Error in STT: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/voices", response_model=List[Dict[str, Any]])
async def get_available_voices(
    voice_service: IVoiceService = Depends(get_voice_service)
) -> List[Dict[str, Any]]:
    """Get list of available voice models."""
    try:
        logger.debug("Getting available voices")
        
        voices = await voice_service.get_available_voices()
        return voices
        
    except Exception as e:
        logger.error(f"Error getting available voices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status")
async def get_voice_status(
    voice_service: IVoiceService = Depends(get_voice_service)
) -> Dict[str, Any]:
    """Get voice service status."""
    try:
        logger.debug("Getting voice service status")
        
        status = await voice_service.get_voice_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting voice status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/voices/{voice_id}/preload")
async def preload_voice(
    voice_id: str,
    voice_service: IVoiceService = Depends(get_voice_service)
):
    """Preload a specific voice for faster synthesis."""
    try:
        logger.info(f"Preloading voice: {voice_id}")
        
        if not voice_id.strip():
            raise HTTPException(status_code=400, detail="Voice ID cannot be empty")
        
        success = await voice_service.preload_voices([voice_id])
        
        if not success.get(voice_id, False):
            raise HTTPException(status_code=404, detail="Voice not found or failed to preload")
        
        return {
            "message": f"Voice {voice_id} preloaded successfully",
            "voice_id": voice_id,
            "status": "preloaded"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error preloading voice {voice_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/settings")
async def update_voice_settings(
    settings: Dict[str, Any],
    voice_service: IVoiceService = Depends(get_voice_service)
):
    """Update voice service settings."""
    try:
        logger.info(f"Updating voice settings: {settings}")
        
        # Validate settings
        valid_settings = [
            "cache_enabled", "max_cache_size", "tts_settings", "stt_settings"
        ]
        
        for key in settings.keys():
            if key not in valid_settings:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid setting: {key}. Valid settings: {valid_settings}"
                )
        
        success = await voice_service.set_voice_settings(settings)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update settings")
        
        return {
            "message": "Voice settings updated successfully",
            "settings": settings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating voice settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/cache")
async def clear_voice_cache(
    voice_service: IVoiceService = Depends(get_voice_service)
):
    """Clear the voice response cache."""
    try:
        logger.info("Clearing voice cache")
        
        success = await voice_service.clear_cache()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
        
        return {"message": "Voice cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing voice cache: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/benchmark")
async def benchmark_voice(
    test_text: str = "This is a test of the voice synthesis system.",
    voice_id: Optional[str] = None,
    voice_service: IVoiceService = Depends(get_voice_service)
) -> Dict[str, Any]:
    """Benchmark voice synthesis performance."""
    try:
        logger.info("Running voice synthesis benchmark")
        
        if len(test_text) > 1000:
            raise HTTPException(status_code=400, detail="Test text too long (max 1000 characters)")
        
        benchmark_result = await voice_service.benchmark_voice(
            test_text=test_text,
            voice_id=voice_id
        )
        
        return benchmark_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running voice benchmark: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/synthesis/metadata")
async def get_synthesis_metadata(
    voice_service: IVoiceService = Depends(get_voice_service)
) -> Dict[str, Any]:
    """Get metadata from the last synthesis operation."""
    try:
        logger.debug("Getting synthesis metadata")
        
        metadata = await voice_service.get_synthesis_metadata()
        return metadata
        
    except Exception as e:
        logger.error(f"Error getting synthesis metadata: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/formats")
async def get_supported_formats() -> Dict[str, Any]:
    """Get supported audio formats and settings."""
    try:
        return {
            "output_formats": ["wav", "mp3", "base64"],
            "sample_rates": [16000, 22050, 44100, 48000],
            "bit_depths": [16, 24, 32],
            "channels": [1, 2],  # mono, stereo
            "speed_range": {"min": 0.5, "max": 2.0, "default": 1.0},
            "pitch_range": {"min": 0.5, "max": 2.0, "default": 1.0},
            "volume_range": {"min": 0.1, "max": 2.0, "default": 1.0}
        }
        
    except Exception as e:
        logger.error(f"Error getting supported formats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/test")
async def test_voice_synthesis(
    voice_service: IVoiceService = Depends(get_voice_service)
):
    """Test voice synthesis with a simple phrase."""
    try:
        logger.info("Testing voice synthesis")
        
        # Check if voice service is available
        if not await voice_service.is_voice_available():
            raise HTTPException(status_code=503, detail="Voice service not available")
        
        # Test with simple phrase
        test_request = VoiceRequest(
            text="Hello, this is a test of the voice synthesis system.",
            speed=1.0,
            pitch=1.0,
            volume=1.0
        )
        
        voice_response = await voice_service.synthesize_speech(test_request)
        
        return {
            "message": "Voice synthesis test completed successfully",
            "duration": voice_response.duration,
            "format": voice_response.format,
            "sample_rate": voice_response.sample_rate,
            "audio_size_bytes": len(voice_response.audio_data),
            "test_text": test_request.text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing voice synthesis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")