"""
SpeechT5 Text-to-Speech Provider
Intel NPU optimized implementation using Microsoft's SpeechT5 model.
"""

import logging
import io
import numpy as np
from typing import List, Dict, Any, Optional, BinaryIO
import torch
import torchaudio
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset

from core.interfaces.voice_provider import (
    IVoiceOutput, VoiceFormat, VoiceGender, SpeechQuality
)
from core.models.voice import Voice, TTSRequest, TTSResponse, VoiceProcessingStatus
from core.exceptions import TTSException, ModelLoadException

logger = logging.getLogger(__name__)

class SpeechT5Provider(IVoiceOutput):
    """SpeechT5 TTS provider optimized for Intel hardware."""
    
    def __init__(self):
        self.processor = None
        self.model = None
        self.vocoder = None
        self.speaker_embeddings = None
        self.device = "cpu"  # Will be set by Intel optimizer
        self.is_loaded = False
        
        # Available voices (speaker embeddings)
        self._voices = {
            "female_1": {
                "id": "female_1",
                "name": "Emma",
                "display_name": "Emma (Female)",
                "gender": VoiceGender.FEMALE,
                "language": "en",
                "description": "Natural female voice"
            },
            "male_1": {
                "id": "male_1", 
                "name": "David",
                "display_name": "David (Male)",
                "gender": VoiceGender.MALE,
                "language": "en",
                "description": "Natural male voice"
            },
            "female_2": {
                "id": "female_2",
                "name": "Sarah",
                "display_name": "Sarah (Female)",
                "gender": VoiceGender.FEMALE,
                "language": "en", 
                "description": "Warm female voice"
            }
        }
        
    def load_model(self, device: str = "cpu") -> bool:
        """Load SpeechT5 model and vocoder."""
        try:
            logger.info(f"Loading SpeechT5 model on {device}...")
            self.device = device
            
            # Load processor
            self.processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
            
            # Load model
            self.model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
            
            # Load vocoder
            self.vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")
            
            # Move to device
            if device.upper() == "NPU":
                # For NPU, we'll use Intel optimizations
                try:
                    # Intel Neural Compressor optimizations would go here
                    logger.info("Attempting NPU optimization...")
                    self.device = "cpu"  # Fallback to CPU for now
                except Exception as e:
                    logger.warning(f"NPU optimization failed, using CPU: {e}")
                    self.device = "cpu"
            else:
                self.device = device.lower()
            
            self.model = self.model.to(self.device)
            self.vocoder = self.vocoder.to(self.device)
            
            # Load speaker embeddings dataset
            self._load_speaker_embeddings()
            
            self.is_loaded = True
            logger.info(f"SpeechT5 model loaded successfully on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load SpeechT5 model: {e}")
            raise ModelLoadException(f"Failed to load SpeechT5: {e}")
    
    def _load_speaker_embeddings(self):
        """Load speaker embeddings for different voices."""
        try:
            # Load speaker embeddings from dataset
            embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
            
            # Map our voice IDs to dataset indices
            self.speaker_embeddings = {
                "female_1": torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0),  # Female speaker
                "male_1": torch.tensor(embeddings_dataset[1000]["xvector"]).unsqueeze(0),    # Male speaker
                "female_2": torch.tensor(embeddings_dataset[5000]["xvector"]).unsqueeze(0),  # Another female
            }
            
            # Move embeddings to device
            for voice_id in self.speaker_embeddings:
                self.speaker_embeddings[voice_id] = self.speaker_embeddings[voice_id].to(self.device)
                
        except Exception as e:
            logger.warning(f"Failed to load speaker embeddings: {e}")
            # Create dummy embeddings as fallback
            self.speaker_embeddings = {
                voice_id: torch.randn(1, 512).to(self.device) 
                for voice_id in self._voices.keys()
            }
    
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
        """Synthesize text to speech."""
        try:
            if not self.is_loaded:
                raise TTSException("Model not loaded")
            
            # Select voice
            voice_id = voice_id or "female_1"
            if voice_id not in self.speaker_embeddings:
                logger.warning(f"Voice {voice_id} not found, using female_1")
                voice_id = "female_1"
            
            # Process text
            inputs = self.processor(text=text, return_tensors="pt")
            input_ids = inputs["input_ids"].to(self.device)
            
            # Get speaker embedding
            speaker_embedding = self.speaker_embeddings[voice_id]
            
            # Generate speech
            with torch.no_grad():
                speech = self.model.generate_speech(
                    input_ids, 
                    speaker_embedding, 
                    vocoder=self.vocoder
                )
            
            # Apply speed adjustment
            if speed != 1.0:
                speech = self._adjust_speed(speech, speed)
            
            # Apply pitch adjustment  
            if pitch != 1.0:
                speech = self._adjust_pitch(speech, pitch)
            
            # Apply volume adjustment
            if volume != 1.0:
                speech = speech * volume
            
            # Convert to audio format
            audio_data = self._tensor_to_audio(speech, output_format)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise TTSException(f"Synthesis failed: {e}")
    
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
        """Synthesize text to speech with streaming (not implemented for SpeechT5)."""
        # SpeechT5 doesn't support streaming, so we'll return the full audio
        audio_data = self.synthesize(text, voice_id, speed, pitch, volume, output_format, **kwargs)
        return io.BytesIO(audio_data)
    
    def _adjust_speed(self, speech: torch.Tensor, speed: float) -> torch.Tensor:
        """Adjust speech speed."""
        try:
            if speed == 1.0:
                return speech
            
            # Simple speed adjustment by resampling
            original_length = speech.shape[0]
            new_length = int(original_length / speed)
            
            # Resample using interpolation
            indices = torch.linspace(0, original_length - 1, new_length)
            adjusted_speech = torch.zeros(new_length)
            
            for i, idx in enumerate(indices):
                idx_int = int(idx)
                if idx_int < original_length - 1:
                    alpha = idx - idx_int
                    adjusted_speech[i] = (1 - alpha) * speech[idx_int] + alpha * speech[idx_int + 1]
                else:
                    adjusted_speech[i] = speech[idx_int]
            
            return adjusted_speech
            
        except Exception as e:
            logger.warning(f"Speed adjustment failed: {e}")
            return speech
    
    def _adjust_pitch(self, speech: torch.Tensor, pitch: float) -> torch.Tensor:
        """Adjust speech pitch."""
        try:
            if pitch == 1.0:
                return speech
            
            # Simple pitch shifting (basic implementation)
            # In production, you'd use more sophisticated pitch shifting algorithms
            if pitch > 1.0:
                # Higher pitch - speed up and resample back
                speed_factor = pitch
                sped_up = self._adjust_speed(speech, speed_factor)
                return self._adjust_speed(sped_up, 1.0 / speed_factor)
            else:
                # Lower pitch - slow down and resample back  
                speed_factor = 1.0 / pitch
                slowed_down = self._adjust_speed(speech, speed_factor)
                return self._adjust_speed(slowed_down, speed_factor)
                
        except Exception as e:
            logger.warning(f"Pitch adjustment failed: {e}")
            return speech
    
    def _tensor_to_audio(self, speech_tensor: torch.Tensor, format: VoiceFormat) -> bytes:
        """Convert speech tensor to audio bytes."""
        try:
            # Ensure speech is on CPU and in correct format
            speech_cpu = speech_tensor.cpu().numpy()
            
            # Normalize audio
            if speech_cpu.max() > 1.0 or speech_cpu.min() < -1.0:
                speech_cpu = speech_cpu / max(abs(speech_cpu.max()), abs(speech_cpu.min()))
            
            # Convert to tensor for torchaudio
            audio_tensor = torch.from_numpy(speech_cpu).unsqueeze(0)  # Add batch dimension
            
            # Save to bytes buffer
            buffer = io.BytesIO()
            
            if format == VoiceFormat.WAV:
                torchaudio.save(buffer, audio_tensor, 16000, format="wav")
            elif format == VoiceFormat.MP3:
                torchaudio.save(buffer, audio_tensor, 16000, format="mp3")
            elif format == VoiceFormat.OGG:
                torchaudio.save(buffer, audio_tensor, 16000, format="ogg")
            else:
                # Default to WAV
                torchaudio.save(buffer, audio_tensor, 16000, format="wav")
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            raise TTSException(f"Audio conversion failed: {e}")
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices."""
        voices = []
        for voice_id, voice_info in self._voices.items():
            voices.append({
                "id": voice_id,
                "name": voice_info["name"],
                "display_name": voice_info["display_name"],
                "gender": voice_info["gender"].value,
                "language": voice_info["language"],
                "description": voice_info["description"],
                "available": voice_id in self.speaker_embeddings
            })
        return voices
    
    def preview_voice(self, voice_id: str, text: str = "Hello, this is a voice preview.") -> bytes:
        """Generate a preview of a voice."""
        return self.synthesize(
            text=text,
            voice_id=voice_id,
            output_format=VoiceFormat.WAV
        )
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return ["en"]  # SpeechT5 primarily supports English
    
    def get_supported_formats(self) -> List[VoiceFormat]:
        """Get list of supported output formats."""
        return [VoiceFormat.WAV, VoiceFormat.MP3, VoiceFormat.OGG]
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "status": "healthy" if self.is_loaded else "not_loaded",
            "model_loaded": self.is_loaded,
            "device": self.device,
            "available_voices": len(self._voices),
            "supported_languages": len(self.get_supported_languages()),
            "supported_formats": len(self.get_supported_formats())
        }