"""
SpeechT5 Text-to-Speech Provider with OpenVINO Optimization
High-quality neural TTS optimized for Intel hardware.
"""

import os
import logging
import asyncio
import time
import io
import numpy as np
from typing import Dict, List, Any, Optional, BinaryIO, Union
from pathlib import Path

from core.interfaces.voice_provider import (
    IVoiceOutput, VoiceFormat, VoiceGender, SpeechQuality
)

logger = logging.getLogger(__name__)

try:
    import openvino as ov
    from optimum.intel import OVModelForSpeechSeq2Seq
    from transformers import SpeechT5Processor, SpeechT5HifiGan
    import torch
    import torchaudio
    import scipy.io.wavfile as wav
    from datasets import load_dataset
    OPENVINO_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OpenVINO/SpeechT5 dependencies not available: {e}")
    OPENVINO_AVAILABLE = False
    ov = None
    OVModelForSpeechSeq2Seq = None
    SpeechT5Processor = None
    SpeechT5HifiGan = None
    torch = None
    torchaudio = None
    wav = None
    load_dataset = None

class SpeechT5OpenVINOProvider(IVoiceOutput):
    """OpenVINO-optimized SpeechT5 TTS provider for Intel hardware."""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.vocoder = None
        self.device = None
        self.is_model_loaded = False
        self.core = None
        
        # Voice embeddings for different speakers
        self.speaker_embeddings = {}
        self.current_speaker = "default"
        
        # Intel-specific optimizations
        self.intel_config = {}
        
        # Performance tracking
        self.tts_stats = {
            "total_requests": 0,
            "total_audio_seconds": 0.0,
            "total_inference_time": 0.0,
            "average_rtf": 0.0  # Real-time factor
        }
        
        # Model configuration
        self.model_config = {
            "model_name": "microsoft/speecht5_tts",
            "vocoder_name": "microsoft/speecht5_hifigan",
            "sample_rate": 16000,
            "supports_streaming": False,
            "max_text_length": 600,  # SpeechT5 limitation
        }
        
        # Available voices
        self.available_voices = [
            {
                "id": "female_1",
                "name": "Female Voice 1", 
                "gender": VoiceGender.FEMALE,
                "language": "en-US",
                "description": "Clear female voice"
            },
            {
                "id": "male_1", 
                "name": "Male Voice 1",
                "gender": VoiceGender.MALE,
                "language": "en-US", 
                "description": "Clear male voice"
            },
            {
                "id": "neutral_1",
                "name": "Neutral Voice 1",
                "gender": VoiceGender.NEUTRAL,
                "language": "en-US",
                "description": "Neutral voice"
            }
        ]
    
    async def initialize(self, device: str = "CPU", **kwargs) -> bool:
        """Initialize the SpeechT5 TTS provider."""
        if not OPENVINO_AVAILABLE:
            logger.error("OpenVINO/SpeechT5 dependencies not available")
            return False
        
        try:
            self.device = device
            self.intel_config = kwargs
            
            logger.info(f"Initializing SpeechT5 TTS on device: {device}")
            
            # Initialize OpenVINO core
            self.core = ov.Core()
            
            # Configure Intel optimizations
            self._configure_intel_optimizations(device, **kwargs)
            
            # Load models
            await self._load_models(device)
            
            # Load speaker embeddings
            await self._load_speaker_embeddings()
            
            if self.model and self.processor and self.vocoder:
                self.is_model_loaded = True
                logger.info("✅ SpeechT5 TTS initialized successfully")
                
                # Test synthesis
                await self._warmup_model()
                return True
            else:
                logger.error("Failed to initialize SpeechT5 TTS")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize SpeechT5 TTS: {e}")
            return False
    
    def _configure_intel_optimizations(self, device: str, **kwargs):
        """Configure Intel-specific optimizations."""
        # CPU optimizations
        if device in ["CPU", "AUTO"]:
            self.core.set_property("CPU", {"PERFORMANCE_HINT": "LATENCY"})
            self.core.set_property("CPU", {"CPU_THREADS_NUM": str(kwargs.get("num_threads", 4))})
            
        # GPU optimizations
        if device in ["GPU", "AUTO"]:
            self.core.set_property("GPU", {"PERFORMANCE_HINT": "LATENCY"})
            
        # NPU optimizations
        if device in ["NPU", "AUTO"]:
            self.core.set_property("NPU", {"PERFORMANCE_HINT": "LATENCY"})
    
    async def _load_models(self, device: str):
        """Load SpeechT5 model and vocoder."""
        try:
            # Check for pre-converted OpenVINO models
            ov_model_path = Path("models/speecht5_tts_ov")
            
            if ov_model_path.exists() and (ov_model_path / "openvino_model.xml").exists():
                logger.info("Loading pre-converted OpenVINO SpeechT5 model")
                self.model = OVModelForSpeechSeq2Seq.from_pretrained(
                    ov_model_path,
                    device=device,
                    compile=True
                )
            else:
                logger.info("Converting and loading SpeechT5 model")
                # Convert from HuggingFace
                self.model = OVModelForSpeechSeq2Seq.from_pretrained(
                    self.model_config["model_name"],
                    export=True,
                    device=device,
                    compile=True
                )
                
                # Save converted model
                ov_model_path.mkdir(parents=True, exist_ok=True)
                self.model.save_pretrained(ov_model_path)
                logger.info(f"Converted model saved to: {ov_model_path}")
            
            # Load processor
            self.processor = SpeechT5Processor.from_pretrained(
                self.model_config["model_name"]
            )
            
            # Load vocoder (HiFiGAN)
            self.vocoder = SpeechT5HifiGan.from_pretrained(
                self.model_config["vocoder_name"]
            )
            
            logger.info("SpeechT5 models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load SpeechT5 models: {e}")
            raise
    
    async def _load_speaker_embeddings(self):
        """Load speaker embeddings for voice variety."""
        try:
            # Load CMU Arctic dataset for speaker embeddings
            # This provides variety in voices
            embeddings_dataset = load_dataset(
                "Matthijs/cmu-arctic-xvectors",
                split="validation"
            )
            
            # Load a few different speaker embeddings
            speakers = ["awb", "bdl", "clb", "jmk", "ksp", "rms", "slt"]  # Different speakers
            
            for i, speaker in enumerate(speakers[:len(self.available_voices)]):
                # Find embedding for this speaker
                speaker_embedding = None
                for item in embeddings_dataset:
                    if item["speaker"] == speaker:
                        speaker_embedding = torch.tensor(item["xvector"]).unsqueeze(0)
                        break
                
                if speaker_embedding is not None:
                    voice_id = self.available_voices[i]["id"]
                    self.speaker_embeddings[voice_id] = speaker_embedding
                    logger.debug(f"Loaded embedding for voice: {voice_id}")
            
            # Default speaker embedding (first one)
            if self.speaker_embeddings:
                self.speaker_embeddings["default"] = list(self.speaker_embeddings.values())[0]
            
            logger.info(f"Loaded {len(self.speaker_embeddings)} speaker embeddings")
            
        except Exception as e:
            logger.warning(f"Failed to load speaker embeddings: {e}")
            # Create a default embedding if loading fails
            self.speaker_embeddings["default"] = torch.randn(1, 512)
    
    async def _warmup_model(self):
        """Warm up the model with test synthesis."""
        try:
            test_text = "Hello, this is a test."
            _ = await self.synthesize_async(test_text)
            logger.info("SpeechT5 model warmed up successfully")
        except Exception as e:
            logger.warning(f"Model warmup failed: {e}")
    
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
        return asyncio.run(self.synthesize_async(
            text, voice_id, speed, pitch, volume, output_format, **kwargs
        ))
    
    async def synthesize_async(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0, 
        volume: float = 1.0,
        output_format: VoiceFormat = VoiceFormat.WAV,
        **kwargs
    ) -> bytes:
        """Async synthesis for better performance."""
        if not self.is_model_loaded:
            raise RuntimeError("SpeechT5 model not loaded")
        
        start_time = time.time()
        
        try:
            # Clean and prepare text
            text = self._preprocess_text(text)
            
            # Handle long text by chunking
            if len(text) > self.model_config["max_text_length"]:
                return await self._synthesize_long_text(text, voice_id, speed, pitch, volume, output_format)
            
            # Get speaker embedding
            speaker_embedding = self._get_speaker_embedding(voice_id or "default")
            
            # Tokenize input
            inputs = self.processor(text=text, return_tensors="pt")
            
            # Generate speech
            with torch.no_grad():
                speech = self.model.generate_speech(
                    inputs["input_ids"], 
                    speaker_embedding,
                    vocoder=self.vocoder
                )
            
            # Apply audio effects
            speech = self._apply_audio_effects(speech, speed, pitch, volume)
            
            # Convert to desired format
            audio_bytes = self._convert_to_format(speech, output_format)
            
            # Update stats
            audio_duration = len(speech) / self.model_config["sample_rate"]
            inference_time = time.time() - start_time
            self._update_stats(audio_duration, inference_time)
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            raise
    
    async def _synthesize_long_text(
        self, 
        text: str, 
        voice_id: Optional[str],
        speed: float, 
        pitch: float, 
        volume: float, 
        output_format: VoiceFormat
    ) -> bytes:
        """Synthesize long text by chunking."""
        # Split text into chunks
        chunks = self._split_text_into_chunks(text)
        audio_segments = []
        
        for chunk in chunks:
            chunk_audio = await self.synthesize_async(
                chunk, voice_id, speed, pitch, volume, output_format
            )
            audio_segments.append(chunk_audio)
        
        # Concatenate audio segments
        return self._concatenate_audio(audio_segments, output_format)
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better synthesis."""
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Handle common abbreviations
        replacements = {
            "Dr.": "Doctor",
            "Mr.": "Mister", 
            "Mrs.": "Misses",
            "Ms.": "Miss",
            "Prof.": "Professor",
            "&": "and",
            "@": "at",
            "%": "percent",
            "$": "dollars",
            "USD": "US dollars",
            "URL": "U R L",
            "API": "A P I",
            "AI": "A I",
            "ML": "M L",
            "TTS": "T T S",
            "STT": "S T T"
        }
        
        for abbr, full in replacements.items():
            text = text.replace(abbr, full)
        
        return text
    
    def _split_text_into_chunks(self, text: str, max_length: int = None) -> List[str]:
        """Split long text into chunks suitable for synthesis."""
        max_length = max_length or self.model_config["max_text_length"]
        
        # Split by sentences first
        sentences = text.replace("!", ".").replace("?", ".").split(".")
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + " " + sentence) <= max_length:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _get_speaker_embedding(self, voice_id: str) -> torch.Tensor:
        """Get speaker embedding for voice ID."""
        if voice_id in self.speaker_embeddings:
            return self.speaker_embeddings[voice_id]
        else:
            logger.warning(f"Voice ID {voice_id} not found, using default")
            return self.speaker_embeddings.get("default", torch.randn(1, 512))
    
    def _apply_audio_effects(
        self, 
        audio: torch.Tensor, 
        speed: float, 
        pitch: float, 
        volume: float
    ) -> torch.Tensor:
        """Apply speed, pitch, and volume modifications."""
        try:
            # Volume adjustment
            if volume != 1.0:
                audio = audio * volume
            
            # Speed adjustment (using resampling)
            if speed != 1.0:
                # Resample to change speed
                original_length = audio.shape[0]
                new_length = int(original_length / speed)
                audio = torch.nn.functional.interpolate(
                    audio.unsqueeze(0).unsqueeze(0),
                    size=new_length,
                    mode='linear',
                    align_corners=False
                ).squeeze()
            
            # Pitch adjustment (simplified - in production would use more sophisticated methods)
            if pitch != 1.0:
                # Basic pitch shifting (this is simplified)
                audio = audio * (1.0 + (pitch - 1.0) * 0.1)
            
            # Clamp to prevent clipping
            audio = torch.clamp(audio, -1.0, 1.0)
            
            return audio
            
        except Exception as e:
            logger.warning(f"Failed to apply audio effects: {e}")
            return audio
    
    def _convert_to_format(self, audio: torch.Tensor, format: VoiceFormat) -> bytes:
        """Convert audio tensor to specified format."""
        # Convert to numpy
        audio_np = audio.cpu().numpy()
        
        # Ensure correct range for 16-bit audio
        if audio_np.dtype != np.int16:
            audio_np = (audio_np * 32767).astype(np.int16)
        
        if format == VoiceFormat.WAV:
            # Create WAV bytes
            buffer = io.BytesIO()
            wav.write(buffer, self.model_config["sample_rate"], audio_np)
            return buffer.getvalue()
        
        elif format == VoiceFormat.MP3:
            # For MP3, would need additional libraries like pydub
            # Fallback to WAV for now
            logger.warning("MP3 format not implemented, using WAV")
            return self._convert_to_format(audio, VoiceFormat.WAV)
        
        else:
            # Default to WAV
            return self._convert_to_format(audio, VoiceFormat.WAV)
    
    def _concatenate_audio(self, audio_segments: List[bytes], format: VoiceFormat) -> bytes:
        """Concatenate multiple audio segments."""
        if not audio_segments:
            return b""
        
        if len(audio_segments) == 1:
            return audio_segments[0]
        
        try:
            # For WAV format
            if format == VoiceFormat.WAV:
                # Read first segment to get parameters
                first_buffer = io.BytesIO(audio_segments[0])
                sample_rate, first_audio = wav.read(first_buffer)
                
                # Concatenate all segments
                concatenated = [first_audio]
                for segment_bytes in audio_segments[1:]:
                    buffer = io.BytesIO(segment_bytes)
                    _, segment_audio = wav.read(buffer)
                    concatenated.append(segment_audio)
                
                # Combine
                final_audio = np.concatenate(concatenated)
                
                # Create output
                output_buffer = io.BytesIO()
                wav.write(output_buffer, sample_rate, final_audio)
                return output_buffer.getvalue()
            
            else:
                # For other formats, return first segment
                return audio_segments[0]
                
        except Exception as e:
            logger.error(f"Failed to concatenate audio: {e}")
            return audio_segments[0]
    
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
        """Synthesize text to speech with streaming (not supported by SpeechT5)."""
        # SpeechT5 doesn't support streaming, so return full synthesis
        audio_bytes = self.synthesize(text, voice_id, speed, pitch, volume, output_format, **kwargs)
        return io.BytesIO(audio_bytes)
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices."""
        return self.available_voices.copy()
    
    def preview_voice(self, voice_id: str, text: str = "Hello, this is a voice preview.") -> bytes:
        """Generate a preview of a voice."""
        return self.synthesize(text, voice_id=voice_id)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return ["en-US", "en-GB", "en-CA", "en-AU"]  # SpeechT5 primarily supports English
    
    def get_supported_formats(self) -> List[VoiceFormat]:
        """Get list of supported output formats."""
        return [VoiceFormat.WAV]  # Primary format
    
    def _update_stats(self, audio_duration: float, inference_time: float):
        """Update performance statistics."""
        self.tts_stats["total_requests"] += 1
        self.tts_stats["total_audio_seconds"] += audio_duration
        self.tts_stats["total_inference_time"] += inference_time
        
        # Calculate real-time factor (lower is better)
        if audio_duration > 0:
            rtf = inference_time / audio_duration
            # Running average
            total_requests = self.tts_stats["total_requests"]
            self.tts_stats["average_rtf"] = (
                (self.tts_stats["average_rtf"] * (total_requests - 1) + rtf) / total_requests
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            "provider": "SpeechT5-OpenVINO",
            "device": self.device,
            "is_loaded": self.is_model_loaded,
            "performance": self.tts_stats.copy(),
            "available_voices": len(self.available_voices)
        }