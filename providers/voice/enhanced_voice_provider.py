"""
Enhanced Voice Provider with System Integration
Provides both TTS and STT capabilities with fallback options and error handling.
"""

import os
import logging
import asyncio
import io
import tempfile
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from core.interfaces.voice_provider import IVoiceOutput, IVoiceInput, VoiceFormat, VoiceGender

logger = logging.getLogger(__name__)

# Try multiple TTS engines for fallback
TTS_ENGINES = []
ENGINE_NAMES = []

# Primary: Intel-optimized SpeechT5
try:
    from providers.voice.speecht5_openvino_provider import SpeechT5OpenVINOProvider
    TTS_ENGINES.append(('speecht5', SpeechT5OpenVINOProvider))
    ENGINE_NAMES.append('SpeechT5-OpenVINO')
except ImportError:
    logger.warning("SpeechT5 OpenVINO provider not available")

# Fallback: pyttsx3 (system TTS)
try:
    import pyttsx3
    TTS_ENGINES.append(('pyttsx3', None))
    ENGINE_NAMES.append('pyttsx3')
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 not available")

# Fallback: Windows SAPI
try:
    import win32com.client
    TTS_ENGINES.append(('sapi', None))
    ENGINE_NAMES.append('Windows SAPI')
    SAPI_AVAILABLE = True
except ImportError:
    SAPI_AVAILABLE = False
    logger.warning("Windows SAPI not available")

# STT Engines
STT_ENGINES = []

# Try speech_recognition
try:
    import speech_recognition as sr
    STT_ENGINES.append(('speech_recognition', sr))
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logger.warning("speech_recognition not available")

class EnhancedVoiceProvider(IVoiceOutput, IVoiceInput):
    """Enhanced voice provider with multiple engine support and error handling."""
    
    def __init__(self):
        self.tts_engine = None
        self.tts_engine_name = None
        self.stt_engine = None
        self.is_initialized = False
        
        # Configuration
        self.voice_config = {
            "rate": 150,
            "volume": 0.8,
            "voice_index": 0
        }
        
        # Available voices cache
        self.available_voices = []
        
        # Performance stats
        self.stats = {
            "tts_requests": 0,
            "stt_requests": 0,
            "errors": 0,
            "engine_used": None
        }
    
    async def initialize(self, **kwargs) -> bool:
        """Initialize voice provider with fallback engines."""
        logger.info("🎙️ Initializing Enhanced Voice Provider...")
        
        # Update configuration
        self.voice_config.update(kwargs)
        
        # Initialize TTS
        tts_success = await self._initialize_tts()
        
        # Initialize STT
        stt_success = await self._initialize_stt()
        
        if tts_success or stt_success:
            self.is_initialized = True
            logger.info(f"✅ Voice provider initialized (TTS: {tts_success}, STT: {stt_success})")
            return True
        else:
            logger.error("❌ Failed to initialize any voice engines")
            return False
    
    async def _initialize_tts(self) -> bool:
        """Initialize Text-to-Speech engine with fallbacks."""
        for engine_name, engine_class in TTS_ENGINES:
            try:
                logger.info(f"Trying TTS engine: {engine_name}")
                
                if engine_name == 'speecht5' and engine_class:
                    # Intel-optimized SpeechT5
                    self.tts_engine = engine_class()
                    success = await self.tts_engine.initialize(
                        device="CPU",
                        **self.voice_config
                    )
                    if success:
                        self.tts_engine_name = engine_name
                        self.stats["engine_used"] = "SpeechT5-OpenVINO"
                        logger.info("✅ SpeechT5 OpenVINO TTS initialized")
                        await self._load_voices()
                        return True
                
                elif engine_name == 'pyttsx3' and PYTTSX3_AVAILABLE:
                    # System TTS fallback
                    self.tts_engine = pyttsx3.init()
                    self.tts_engine_name = engine_name
                    self.stats["engine_used"] = "pyttsx3"
                    
                    # Configure pyttsx3
                    self.tts_engine.setProperty('rate', self.voice_config["rate"])
                    self.tts_engine.setProperty('volume', self.voice_config["volume"])
                    
                    logger.info("✅ pyttsx3 TTS initialized")
                    await self._load_voices()
                    return True
                
                elif engine_name == 'sapi' and SAPI_AVAILABLE:
                    # Windows SAPI fallback
                    self.tts_engine = win32com.client.Dispatch("SAPI.SpVoice")
                    self.tts_engine_name = engine_name
                    self.stats["engine_used"] = "Windows SAPI"
                    
                    logger.info("✅ Windows SAPI TTS initialized")
                    await self._load_voices()
                    return True
                    
            except Exception as e:
                logger.warning(f"Failed to initialize {engine_name}: {e}")
                continue
        
        logger.error("Failed to initialize any TTS engine")
        return False
    
    async def _initialize_stt(self) -> bool:
        """Initialize Speech-to-Text engine."""
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                self.stt_engine = sr.Recognizer()
                logger.info("✅ Speech Recognition STT initialized")
                return True
            except Exception as e:
                logger.warning(f"Failed to initialize STT: {e}")
        
        return False
    
    async def _load_voices(self):
        """Load available voices for current engine."""
        self.available_voices = []
        
        try:
            if self.tts_engine_name == 'speecht5':
                # SpeechT5 voices
                self.available_voices = [
                    {
                        "id": "female_1",
                        "name": "Female Voice 1",
                        "gender": VoiceGender.FEMALE,
                        "language": "en-US"
                    },
                    {
                        "id": "male_1",
                        "name": "Male Voice 1", 
                        "gender": VoiceGender.MALE,
                        "language": "en-US"
                    }
                ]
            
            elif self.tts_engine_name == 'pyttsx3':
                # pyttsx3 voices
                voices = self.tts_engine.getProperty('voices')
                for i, voice in enumerate(voices):
                    self.available_voices.append({
                        "id": str(i),
                        "name": voice.name,
                        "gender": VoiceGender.FEMALE if 'female' in voice.name.lower() else VoiceGender.MALE,
                        "language": voice.languages[0] if voice.languages else "en-US"
                    })
            
            elif self.tts_engine_name == 'sapi':
                # Windows SAPI voices
                voices = self.tts_engine.GetVoices()
                for i in range(voices.Count):
                    voice = voices.Item(i)
                    self.available_voices.append({
                        "id": str(i),
                        "name": voice.GetDescription(),
                        "gender": VoiceGender.FEMALE if 'female' in voice.GetDescription().lower() else VoiceGender.MALE,
                        "language": "en-US"
                    })
            
            logger.info(f"Loaded {len(self.available_voices)} voices")
            
        except Exception as e:
            logger.warning(f"Failed to load voices: {e}")
    
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
        """Async text-to-speech synthesis."""
        if not self.is_initialized or not self.tts_engine:
            raise RuntimeError("TTS engine not initialized")
        
        try:
            self.stats["tts_requests"] += 1
            
            if self.tts_engine_name == 'speecht5':
                # Use SpeechT5 provider
                return await self.tts_engine.synthesize_async(
                    text, voice_id, speed, pitch, volume, output_format, **kwargs
                )
            
            elif self.tts_engine_name == 'pyttsx3':
                # Use pyttsx3 with file output
                return await self._synthesize_pyttsx3(text, voice_id, speed, volume)
            
            elif self.tts_engine_name == 'sapi':
                # Use Windows SAPI with file output
                return await self._synthesize_sapi(text, voice_id, speed, volume)
            
            else:
                raise RuntimeError(f"Unknown TTS engine: {self.tts_engine_name}")
                
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"TTS synthesis failed: {e}")
            raise
    
    async def _synthesize_pyttsx3(
        self, 
        text: str, 
        voice_id: Optional[str], 
        speed: float, 
        volume: float
    ) -> bytes:
        """Synthesize using pyttsx3."""
        # Configure voice
        if voice_id and voice_id.isdigit():
            voices = self.tts_engine.getProperty('voices')
            if int(voice_id) < len(voices):
                self.tts_engine.setProperty('voice', voices[int(voice_id)].id)
        
        # Configure speed and volume
        rate = int(self.voice_config["rate"] * speed)
        self.tts_engine.setProperty('rate', rate)
        self.tts_engine.setProperty('volume', volume)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Save to file
            self.tts_engine.save_to_file(text, tmp_path)
            self.tts_engine.runAndWait()
            
            # Read file content
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            return audio_data
            
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    async def _synthesize_sapi(
        self, 
        text: str, 
        voice_id: Optional[str], 
        speed: float, 
        volume: float
    ) -> bytes:
        """Synthesize using Windows SAPI."""
        # Configure voice
        if voice_id and voice_id.isdigit():
            voices = self.tts_engine.GetVoices()
            if int(voice_id) < voices.Count:
                self.tts_engine.Voice = voices.Item(int(voice_id))
        
        # Configure rate and volume
        self.tts_engine.Rate = int(speed * 5)  # SAPI rate range: -10 to 10
        self.tts_engine.Volume = int(volume * 100)  # SAPI volume range: 0 to 100
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Create file stream
            file_stream = win32com.client.Dispatch("SAPI.SpFileStream")
            file_stream.Open(tmp_path, 3)  # Write mode
            
            # Set output to file
            self.tts_engine.AudioOutputStream = file_stream
            
            # Speak to file
            self.tts_engine.Speak(text)
            
            # Close file stream
            file_stream.Close()
            
            # Read file content
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            return audio_data
            
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices."""
        return self.available_voices.copy()
    
    def get_supported_formats(self) -> List[VoiceFormat]:
        """Get supported output formats."""
        return [VoiceFormat.WAV]
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages."""
        languages = set()
        for voice in self.available_voices:
            languages.add(voice.get("language", "en-US"))
        return list(languages)
    
    # STT Methods
    async def recognize_from_audio(
        self,
        audio_data: bytes,
        language: str = "en-US",
        **kwargs
    ) -> Dict[str, Any]:
        """Recognize speech from audio data."""
        if not self.stt_engine:
            return {"error": "STT engine not initialized"}
        
        try:
            self.stats["stt_requests"] += 1
            
            # Convert audio data to AudioData object
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name
            
            try:
                with sr.AudioFile(tmp_path) as source:
                    audio = self.stt_engine.record(source)
                
                # Recognize speech
                text = self.stt_engine.recognize_google(audio, language=language)
                
                return {
                    "success": True,
                    "text": text,
                    "confidence": 1.0,  # Google API doesn't provide confidence
                    "language": language
                }
                
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except sr.UnknownValueError:
            return {"error": "Could not understand audio"}
        except sr.RequestError as e:
            return {"error": f"Speech recognition service error: {e}"}
        except Exception as e:
            self.stats["errors"] += 1
            return {"error": f"STT failed: {e}"}
    
    async def recognize_from_microphone(
        self,
        duration: float = 5.0,
        language: str = "en-US",
        **kwargs
    ) -> Dict[str, Any]:
        """Recognize speech from microphone."""
        if not self.stt_engine:
            return {"error": "STT engine not initialized"}
        
        try:
            with sr.Microphone() as source:
                logger.info("Listening...")
                # Adjust for ambient noise
                self.stt_engine.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for audio
                audio = self.stt_engine.listen(source, timeout=duration)
                
                logger.info("Processing speech...")
                text = self.stt_engine.recognize_google(audio, language=language)
                
                return {
                    "success": True,
                    "text": text,
                    "confidence": 1.0,
                    "language": language
                }
                
        except sr.WaitTimeoutError:
            return {"error": "No speech detected within timeout"}
        except sr.UnknownValueError:
            return {"error": "Could not understand audio"}
        except sr.RequestError as e:
            return {"error": f"Speech recognition service error: {e}"}
        except Exception as e:
            self.stats["errors"] += 1
            return {"error": f"Microphone STT failed: {e}"}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get voice provider information."""
        return {
            "name": "Enhanced Voice Provider",
            "tts_engine": self.stats.get("engine_used", "None"),
            "stt_engine": "Google Speech Recognition" if self.stt_engine else "None",
            "is_initialized": self.is_initialized,
            "available_voices": len(self.available_voices),
            "supported_formats": [fmt.value for fmt in self.get_supported_formats()],
            "supported_languages": self.get_supported_languages()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "provider": "Enhanced Voice",
            "tts_engine": self.stats.get("engine_used", "None"),
            "stats": self.stats.copy(),
            "is_initialized": self.is_initialized
        }