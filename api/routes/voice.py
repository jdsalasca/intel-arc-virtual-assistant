"""
Voice API Routes
Endpoints for text-to-speech and speech-to-text operations.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import Response

from core.models.voice import (
    TTSRequest, TTSResponse, STTRequest, STTResponse,
    VoiceFormat, VoiceGender, SpeechQuality
)
from services.voice_service import VoiceService
from api.schemas.voice_schemas import (
    TTSRequestSchema, STTRequestSchema, VoiceListSchema,
    TTSResponseSchema, STTResponseSchema
)

logger = logging.getLogger(__name__)

router = APIRouter()

# This will be injected by the main app
voice_service: Optional[VoiceService] = None

def get_voice_service() -> VoiceService:
    """Dependency to get voice service."""
    if voice_service is None:
        raise HTTPException(status_code=503, detail="Voice service not available")
    return voice_service

@router.post("/tts", response_model=TTSResponseSchema)
async def text_to_speech(
    request: TTSRequestSchema,
    service: VoiceService = Depends(get_voice_service)
):
    """Convert text to speech."""
    try:
        # Convert schema to internal request
        tts_request = TTSRequest(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            text=request.text,
            voice_id=request.voice_id,
            speed=request.speed,
            pitch=request.pitch,
            volume=request.volume,
            output_format=VoiceFormat(request.output_format),
            language=request.language,
            quality=SpeechQuality(request.quality)
        )
        
        # Process TTS
        response = await service.text_to_speech(tts_request, request.provider)
        
        return TTSResponseSchema(
            request_id=response.request_id,
            status=response.status.value,
            success=response.success,
            processing_time=response.processing_time,
            audio_url=f"/api/v1/voice/audio/{response.request_id}",  # Will serve audio separately
            duration=response.duration,
            model_used=response.model_used,
            voice_used=response.voice_used,
            error_message=response.error_message
        )
        
    except Exception as e:
        logger.error(f"TTS endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")

@router.post("/stt", response_model=STTResponseSchema)
async def speech_to_text(
    audio: UploadFile = File(...),
    language: str = Form("auto"),
    provider: str = Form("whisper"),
    user_id: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    enable_punctuation: bool = Form(True),
    enable_word_confidence: bool = Form(False),
    service: VoiceService = Depends(get_voice_service)
):
    """Convert speech to text."""
    try:
        # Read audio data
        audio_data = await audio.read()
        
        # Determine audio format from filename
        audio_format = VoiceFormat.WAV  # Default
        if audio.filename:
            if audio.filename.endswith('.mp3'):
                audio_format = VoiceFormat.MP3
            elif audio.filename.endswith('.ogg'):
                audio_format = VoiceFormat.OGG
            elif audio.filename.endswith('.flac'):
                audio_format = VoiceFormat.FLAC
        
        # Create STT request
        stt_request = STTRequest(
            user_id=user_id,
            conversation_id=conversation_id,
            audio_data=audio_data,
            audio_format=audio_format,
            language=language,
            enable_punctuation=enable_punctuation,
            enable_word_confidence=enable_word_confidence
        )
        
        # Process STT
        response = await service.speech_to_text(stt_request, provider)
        
        return STTResponseSchema(
            request_id=response.request_id,
            status=response.status.value,
            success=response.success,
            processing_time=response.processing_time,
            transcript=response.transcript,
            confidence=response.confidence,
            language_detected=response.language_detected,
            model_used=response.model_used,
            error_message=response.error_message
        )
        
    except Exception as e:
        logger.error(f"STT endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"STT failed: {e}")

@router.get("/voices", response_model=VoiceListSchema)
async def list_voices(
    provider: str = "speecht5",
    service: VoiceService = Depends(get_voice_service)
):
    """Get available voices for TTS."""
    try:
        voices = service.get_available_voices(provider)
        return VoiceListSchema(voices=voices)
        
    except Exception as e:
        logger.error(f"List voices failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list voices: {e}")

@router.get("/languages")
async def list_languages(
    provider: str = "speecht5",
    provider_type: str = "tts",  # tts or stt
    service: VoiceService = Depends(get_voice_service)
):
    """Get supported languages for a provider."""
    try:
        languages = service.get_supported_languages(provider, provider_type)
        return {"languages": languages}
        
    except Exception as e:
        logger.error(f"List languages failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list languages: {e}")

@router.get("/preview/{voice_id}")
async def preview_voice(
    voice_id: str,
    text: str = "Hello, this is a voice preview.",
    provider: str = "speecht5",
    service: VoiceService = Depends(get_voice_service)
):
    """Generate a voice preview."""
    try:
        # Create TTS request for preview
        tts_request = TTSRequest(
            user_id="preview",
            text=text,
            voice_id=voice_id,
            output_format=VoiceFormat.WAV
        )
        
        # Generate preview
        response = await service.text_to_speech(tts_request, provider)
        
        if response.success and response.audio_data:
            return Response(
                content=response.audio_data,
                media_type="audio/wav",
                headers={"Content-Disposition": f"attachment; filename=preview_{voice_id}.wav"}
            )
        else:
            raise HTTPException(status_code=500, detail="Preview generation failed")
            
    except Exception as e:
        logger.error(f"Voice preview failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {e}")

@router.get("/audio/{request_id}")
async def get_audio(
    request_id: str,
    service: VoiceService = Depends(get_voice_service)
):
    """Get generated audio file."""
    try:
        # In a real implementation, you'd store audio files and retrieve them
        # For now, return an error indicating this needs implementation
        raise HTTPException(
            status_code=501, 
            detail="Audio file storage not implemented yet"
        )
        
    except Exception as e:
        logger.error(f"Get audio failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audio retrieval failed: {e}")

@router.get("/stats")
async def get_voice_stats(
    service: VoiceService = Depends(get_voice_service)
):
    """Get voice processing statistics."""
    try:
        stats = service.get_voice_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Get voice stats failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {e}")

@router.get("/health")
async def voice_health_check(
    service: VoiceService = Depends(get_voice_service)
):
    """Voice service health check."""
    try:
        health = await service.health_check()
        return health
        
    except Exception as e:
        logger.error(f"Voice health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.post("/tts/simple")
async def simple_tts(
    text: str,
    voice_id: str = "female_1",
    provider: str = "speecht5",
    service: VoiceService = Depends(get_voice_service)
):
    """Simple TTS endpoint that returns audio directly."""
    try:
        # Create simple TTS request
        tts_request = TTSRequest(
            user_id="simple",
            text=text,
            voice_id=voice_id,
            output_format=VoiceFormat.WAV
        )
        
        # Generate speech
        response = await service.text_to_speech(tts_request, provider)
        
        if response.success and response.audio_data:
            return Response(
                content=response.audio_data,
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "attachment; filename=speech.wav",
                    "X-Processing-Time": str(response.processing_time),
                    "X-Model-Used": response.model_used or "unknown"
                }
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=response.error_message or "TTS generation failed"
            )
            
    except Exception as e:
        logger.error(f"Simple TTS failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")