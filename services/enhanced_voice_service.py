"""
Enhanced Voice Service for Intel AI Assistant
Speech recognition, text-to-speech, and voice interaction capabilities.
"""

import speech_recognition as sr
import pyttsx3
import threading
import queue
import time
import logging
from typing import Optional, Dict, Any, Callable
import json

logger = logging.getLogger(__name__)

class EnhancedVoiceService:
    """Enhanced voice service with speech recognition and TTS."""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.tts_engine = None
        self.is_listening = False
        self.voice_queue = queue.Queue()
        self.listen_thread = None
        
        # Voice settings
        self.voice_rate = 150
        self.voice_volume = 0.8
        self.voice_language = "en-US"
        
        # Callbacks
        self.on_speech_recognized: Optional[Callable[[str], None]] = None
        self.on_speech_error: Optional[Callable[[str], None]] = None
        
        # System capabilities
        self.capabilities = self.check_system_capabilities()
        
        self.initialize_voice_system()
    
    def check_system_capabilities(self) -> Dict[str, bool]:
        """Check what voice capabilities are available on the system."""
        capabilities = {
            "microphone_devices": False,
            "tts_engine": False,
            "speech_recognition": False,
            "audio_drivers": False
        }
        
        try:
            # Check for microphone devices
            mic_list = sr.Microphone.list_microphone_names()
            capabilities["microphone_devices"] = len(mic_list) > 0
            logger.info(f"Found {len(mic_list)} microphone devices")
        except Exception as e:
            logger.warning(f"Could not enumerate microphone devices: {e}")
        
        try:
            # Check TTS engine availability
            test_engine = pyttsx3.init()
            if test_engine:
                test_engine.stop()
                capabilities["tts_engine"] = True
        except Exception as e:
            logger.warning(f"TTS engine not available: {e}")
        
        try:
            # Check speech recognition (basic test)
            test_recognizer = sr.Recognizer()
            capabilities["speech_recognition"] = True
        except Exception as e:
            logger.warning(f"Speech recognition not available: {e}")
        
        # Check audio drivers (basic test)
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            capabilities["audio_drivers"] = pa.get_device_count() > 0
            pa.terminate()
        except Exception as e:
            logger.warning(f"Audio drivers check failed: {e}")
        
        return capabilities
    
    def initialize_voice_system(self):
        """Initialize speech recognition and TTS systems."""
        # Initialize TTS engine first (more likely to work)
        try:
            self.tts_engine = pyttsx3.init()
            
            # Configure TTS settings
            self.tts_engine.setProperty('rate', self.voice_rate)
            self.tts_engine.setProperty('volume', self.voice_volume)
            
            # Try to set a better voice if available
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Prefer female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            logger.info("TTS engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            print(f"⚠️  TTS engine initialization failed: {e}")
            self.tts_engine = None
        
        # Initialize microphone (more likely to fail)
        try:
            # Check if microphone devices are available
            mic_list = sr.Microphone.list_microphone_names()
            if not mic_list:
                raise RuntimeError("No microphone devices found")
            
            self.microphone = sr.Microphone()
            
            # Calibrate for ambient noise with timeout
            print("🎤 Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✅ Microphone calibrated!")
            
            logger.info("Microphone initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize microphone: {e}")
            print(f"⚠️  Microphone initialization failed: {e}")
            self.microphone = None
        
        # Final status
        if self.tts_engine and self.microphone:
            print("✅ Voice system fully initialized")
        elif self.tts_engine:
            print("⚠️  Voice system partially initialized (TTS only)")
        elif self.microphone:
            print("⚠️  Voice system partially initialized (Speech recognition only)")
        else:
            print("❌ Voice system initialization failed")
    
    def speak(self, text: str, blocking: bool = False):
        """Convert text to speech."""
        if not self.tts_engine:
            print(f"🔊 {text}")  # Fallback to text output
            return
        
        try:
            if blocking:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            else:
                # Non-blocking speech
                def speak_async():
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                
                threading.Thread(target=speak_async, daemon=True).start()
                
        except Exception as e:
            logger.error(f"TTS error: {e}")
            print(f"🔊 {text}")  # Fallback
    
    def listen_once(self, timeout: float = 5.0) -> Optional[str]:
        """Listen for speech once and return recognized text."""
        if not self.microphone:
            logger.warning("Microphone not available for speech recognition")
            return None
        
        try:
            print("🎤 Listening...")
            with self.microphone as source:
                # Add error handling for microphone context
                if source is None:
                    logger.error("Microphone source is None")
                    return None
                
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            print("🔄 Processing speech...")
            text = self.recognizer.recognize_google(audio, language=self.voice_language)
            print(f"🎯 Recognized: {text}")
            return text
            
        except sr.WaitTimeoutError:
            print("⏱️  Listening timeout")
            return None
        except sr.UnknownValueError:
            print("❓ Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            logger.error(f"Speech recognition service error: {e}")
            return None
        except AttributeError as e:
            if "'NoneType' object has no attribute 'close'" in str(e):
                logger.error("Microphone context manager error - microphone may be unavailable")
                self.microphone = None  # Reset microphone to prevent further errors
                return None
            else:
                logger.error(f"Attribute error in speech recognition: {e}")
                return None
        except Exception as e:
            logger.error(f"Unexpected error in speech recognition: {e}")
            print(f"❌ Unexpected error: {e}")
            return None
    
    def start_continuous_listening(self):
        """Start continuous speech recognition in background."""
        if self.is_listening:
            return
        
        self.is_listening = True
        self.listen_thread = threading.Thread(target=self._continuous_listen_worker, daemon=True)
        self.listen_thread.start()
        
        print("🎤 Started continuous listening...")
    
    def stop_continuous_listening(self):
        """Stop continuous speech recognition."""
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
        
        print("🛑 Stopped continuous listening")
    
    def _continuous_listen_worker(self):
        """Worker thread for continuous listening."""
        failed_attempts = 0
        max_failed_attempts = 5
        
        while self.is_listening:
            try:
                # Check if microphone is still available
                if not self.microphone:
                    logger.warning("Microphone not available, stopping continuous listening")
                    break
                
                text = self.listen_once(timeout=1.0)
                if text:
                    failed_attempts = 0  # Reset counter on success
                    self.voice_queue.put(text)
                    if self.on_speech_recognized:
                        self.on_speech_recognized(text)
                        
            except Exception as e:
                failed_attempts += 1
                logger.error(f"Continuous listening error (attempt {failed_attempts}): {e}")
                
                if self.on_speech_error:
                    self.on_speech_error(str(e))
                
                # If too many failures, stop listening
                if failed_attempts >= max_failed_attempts:
                    logger.error(f"Too many failed attempts ({max_failed_attempts}), stopping continuous listening")
                    self.is_listening = False
                    break
                
                # Exponential backoff for retries
                sleep_time = min(0.5 * (2 ** failed_attempts), 5.0)
                time.sleep(sleep_time)
    
    def get_speech_from_queue(self) -> Optional[str]:
        """Get recognized speech from queue (non-blocking)."""
        try:
            return self.voice_queue.get_nowait()
        except queue.Empty:
            return None
    
    def set_voice_settings(self, rate: int = None, volume: float = None):
        """Update voice settings."""
        if self.tts_engine:
            if rate is not None:
                self.voice_rate = rate
                self.tts_engine.setProperty('rate', rate)
            
            if volume is not None:
                self.voice_volume = volume
                self.tts_engine.setProperty('volume', volume)
    
    def test_voice_system(self):
        """Test voice system functionality."""
        print("🧪 Testing Voice System")
        print("=" * 30)
        
        # Test TTS
        print("1. Testing Text-to-Speech...")
        self.speak("Hello! I am your Intel AI Assistant. Can you hear me clearly?", blocking=True)
        
        # Test speech recognition
        print("\n2. Testing Speech Recognition...")
        print("Please say something (you have 5 seconds):")
        
        recognized_text = self.listen_once(timeout=5.0)
        if recognized_text:
            print(f"✅ Successfully recognized: '{recognized_text}'")
            self.speak(f"I heard you say: {recognized_text}")
        else:
            print("❌ No speech recognized")
        
        # Test voice settings
        print("\n3. Testing Voice Settings...")
        self.speak("Testing normal speed.", blocking=True)
        
        # Temporarily change speed
        original_rate = self.voice_rate
        self.set_voice_settings(rate=200)
        self.speak("Testing faster speed.", blocking=True)
        
        self.set_voice_settings(rate=100)
        self.speak("Testing slower speed.", blocking=True)
        
        # Restore original settings
        self.set_voice_settings(rate=original_rate)
        self.speak("Voice settings test completed!", blocking=True)
        
        print("✅ Voice system test completed!")
    
    def interactive_voice_test(self):
        """Interactive voice test session."""
        print("🎤 Interactive Voice Test")
        print("Say 'stop' to end the test")
        print("=" * 30)
        
        self.speak("Starting interactive voice test. Say something, and I will repeat it back. Say stop to end the test.")
        
        while True:
            print("\n🎤 Listening... (say 'stop' to exit)")
            text = self.listen_once(timeout=10.0)
            
            if not text:
                continue
            
            if 'stop' in text.lower() or 'exit' in text.lower():
                self.speak("Goodbye! Voice test completed.")
                break
            
            # Repeat back what was heard
            response = f"You said: {text}"
            print(f"🔊 {response}")
            self.speak(response)
    
    def get_available_voices(self) -> list:
        """Get list of available TTS voices."""
        if not self.tts_engine:
            return []
        
        try:
            voices = self.tts_engine.getProperty('voices')
            return [{"id": voice.id, "name": voice.name} for voice in voices] if voices else []
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []
    
    def set_voice_by_name(self, voice_name: str) -> bool:
        """Set TTS voice by name."""
        if not self.tts_engine:
            return False
        
        try:
            voices = self.tts_engine.getProperty('voices')
            if not voices:
                return False
            
            for voice in voices:
                if voice_name.lower() in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    logger.info(f"Voice changed to: {voice.name}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error setting voice: {e}")
            return False
    
    def get_voice_status(self) -> Dict[str, Any]:
        """Get current voice system status."""
        return {
            "tts_available": self.tts_engine is not None,
            "microphone_available": self.microphone is not None,
            "is_listening": self.is_listening,
            "voice_rate": self.voice_rate,
            "voice_volume": self.voice_volume,
            "voice_language": self.voice_language,
            "available_voices": len(self.get_available_voices()),
            "system_capabilities": self.capabilities,
            "initialization_status": {
                "tts_initialized": self.tts_engine is not None,
                "microphone_initialized": self.microphone is not None,
                "full_voice_system": self.tts_engine is not None and self.microphone is not None
            }
        }
    
    def save_voice_settings(self, file_path: str = "config/voice_settings.json"):
        """Save voice settings to file."""
        settings = {
            "voice_rate": self.voice_rate,
            "voice_volume": self.voice_volume,
            "voice_language": self.voice_language
        }
        
        try:
            import os
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(settings, f, indent=2)
            
            logger.info(f"Voice settings saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save voice settings: {e}")
            return False
    
    def load_voice_settings(self, file_path: str = "config/voice_settings.json"):
        """Load voice settings from file."""
        try:
            with open(file_path, 'r') as f:
                settings = json.load(f)
            
            self.set_voice_settings(
                rate=settings.get("voice_rate", self.voice_rate),
                volume=settings.get("voice_volume", self.voice_volume)
            )
            
            self.voice_language = settings.get("voice_language", self.voice_language)
            
            logger.info(f"Voice settings loaded from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load voice settings: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    # Create voice service
    voice_service = EnhancedVoiceService()
    
    # Run tests
    voice_service.test_voice_system()
    
    # Interactive test (uncomment to run)
    # voice_service.interactive_voice_test()