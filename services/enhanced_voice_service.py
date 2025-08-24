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
        
        self.initialize_voice_system()
    
    def initialize_voice_system(self):
        """Initialize speech recognition and TTS systems."""
        try:
            # Initialize microphone with error handling
            self.microphone = self._safe_initialize_microphone()
            
            # Initialize TTS engine
            self.tts_engine = self._safe_initialize_tts()
            
            # Report status
            if self.microphone and self.tts_engine:
                print("✅ Voice service initialized")
                logger.info("Voice system fully initialized")
            elif self.tts_engine:
                print("⚠️ Voice system partially initialized (TTS only)")
                logger.warning("Voice system initialized with TTS only - no microphone")
            else:
                print("❌ Voice system initialization failed")
                logger.error("Voice system initialization failed completely")
            
        except Exception as e:
            logger.error(f"Failed to initialize voice system: {e}")
            print(f"⚠️  Voice system initialization failed: {e}")
            
    def _safe_initialize_microphone(self):
        """Safely initialize microphone with proper error handling."""
        try:
            # Check if microphone devices are available
            print("🎤 Calibrating microphone for ambient noise...")
            
            try:
                microphone_list = sr.Microphone.list_microphone_names()
                if not microphone_list:
                    print("⚠️  No microphone devices found")
                    return None
            except Exception as e:
                print(f"⚠️  Could not enumerate microphones: {e}")
                # Continue anyway - maybe there's a default device
                
            # Try to initialize microphone with different approaches
            mic = None
            
            # Approach 1: Try default microphone
            try:
                mic = sr.Microphone()
                # Test that we can actually open and use it
                with mic as source:
                    if hasattr(source, 'stream') or hasattr(source, 'CHUNK'):
                        # Quick ambient noise adjustment
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                        print("✅ Microphone calibrated!")
                        return mic
                    else:
                        raise RuntimeError("Microphone source invalid")
            except Exception as e:
                print(f"⚠️  Default microphone failed: {e}")
                mic = None
            
            # Approach 2: Try specific device index if default failed
            if mic is None:
                try:
                    # Try device index 0 explicitly
                    mic = sr.Microphone(device_index=0)
                    with mic as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                        print("✅ Microphone calibrated (device 0)!")
                        return mic
                except Exception as e:
                    print(f"⚠️  Device 0 microphone failed: {e}")
                    mic = None
            
            # If all approaches failed
            if mic is None:
                print("⚠️  No working microphone found - voice input disabled")
                return None
                
        except Exception as e:
            print(f"⚠️  Microphone initialization failed: {e}")
            return None
            
    def _safe_initialize_tts(self):
        """Safely initialize TTS engine."""
        try:
            engine = pyttsx3.init()
            
            # Configure TTS settings with error handling
            try:
                engine.setProperty('rate', self.voice_rate)
                engine.setProperty('volume', self.voice_volume)
                
                # Try to set a better voice if available
                voices = engine.getProperty('voices')
                if voices:
                    # Prefer female voice if available
                    for voice in voices:
                        try:
                            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                                engine.setProperty('voice', voice.id)
                                break
                        except:
                            continue
                            
            except Exception as e:
                print(f"⚠️  TTS configuration warning: {e}")
                
            return engine
            
        except Exception as e:
            print(f"⚠️  TTS initialization failed: {e}")
            return None
    
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
            # Verify microphone is still valid before using
            if not hasattr(self.microphone, '__enter__') or not hasattr(self.microphone, '__exit__'):
                logger.error("Microphone object is invalid")
                self.microphone = None
                return None
            
            # Only print listening message if not in continuous mode
            if not self.is_listening:
                print("🎤 Listening...")
            
            # Use a more robust approach with better error handling
            audio = None
            try:
                with self.microphone as source:
                    # Validate the source object
                    if source is None:
                        logger.error("Microphone source is None")
                        self.microphone = None
                        return None
                    
                    # Quick ambient noise adjustment for non-continuous mode
                    if not self.is_listening:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.1)
                    
                    # Listen for audio
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                    
            except (OSError, AttributeError, RuntimeError) as mic_error:
                logger.error(f"Microphone context error: {mic_error}")
                self.microphone = None
                return None
            except Exception as mic_error:
                logger.error(f"Microphone error: {mic_error}")
                # For any other microphone error, disable it
                self.microphone = None
                return None
            
            # Process the audio if we got it
            if audio is None:
                return None
                
            if not self.is_listening:
                print("🔄 Processing speech...")
                
            text = self.recognizer.recognize_google(audio, language=self.voice_language)
            
            if not self.is_listening:
                print(f"🎯 Recognized: {text}")
                
            return text
            
        except sr.WaitTimeoutError:
            if not self.is_listening:
                print("⏱️  Listening timeout")
            return None
        except sr.UnknownValueError:
            if not self.is_listening:
                print("❓ Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            # Log the error but don't spam the user in continuous mode
            logger.error(f"Unexpected listening error: {e}")
            # If it's a critical error with the microphone, disable it
            if "'NoneType'" in str(e) or "close" in str(e):
                logger.warning("Disabling microphone due to critical error")
                self.microphone = None
            # Don't print error messages in continuous mode to avoid spam
            if not self.is_listening:
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
        """Worker thread for continuous listening with robust error handling."""
        microphone_failures = 0
        max_failures = 3  # Reduced max failures
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.is_listening:
            try:
                # If microphone is unavailable, try to reinitialize or stop
                if not self.microphone:
                    microphone_failures += 1
                    if microphone_failures >= max_failures:
                        logger.warning("Too many microphone failures, stopping continuous listening")
                        self.is_listening = False
                        break
                    
                    # Try to reinitialize microphone
                    logger.info("Attempting to reinitialize microphone...")
                    self.microphone = self._safe_initialize_microphone()
                    
                    if not self.microphone:
                        time.sleep(5.0)  # Wait longer when microphone is unavailable
                        continue
                
                # Reset failure counters on successful microphone detection
                microphone_failures = 0
                consecutive_errors = 0
                
                # Attempt speech recognition with timeout
                text = self.listen_once(timeout=1.0)
                if text:
                    self.voice_queue.put(text)
                    if self.on_speech_recognized:
                        self.on_speech_recognized(text)
                else:
                    # Brief pause between listening attempts
                    time.sleep(0.1)
                        
            except Exception as e:
                consecutive_errors += 1
                error_msg = str(e)
                
                # Log the error but avoid spamming
                if consecutive_errors <= 3:
                    logger.error(f"Continuous listening error: {e}")
                
                # Check for critical microphone errors
                if ("'NoneType'" in error_msg and "close" in error_msg) or "Microphone" in error_msg:
                    logger.warning("Critical microphone error detected, disabling microphone")
                    self.microphone = None
                    microphone_failures += 1
                
                # Call error handler if available
                if self.on_speech_error and consecutive_errors <= 3:
                    self.on_speech_error(error_msg)
                
                # If too many consecutive errors, stop listening
                if consecutive_errors >= max_consecutive_errors:
                    logger.error("Too many consecutive errors, stopping continuous listening")
                    self.is_listening = False
                    break
                
                # Exponential backoff with cap
                backoff_time = min(0.5 * consecutive_errors, 3.0)
                time.sleep(backoff_time)
        
        logger.info("Continuous listening worker stopped")
    
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
            "available_voices": len(self.get_available_voices())
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