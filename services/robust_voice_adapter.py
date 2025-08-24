"""
Robust Voice Service Adapter
Integrates enhanced voice capabilities with existing project architecture.
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from services.enhanced_voice_service import EnhancedVoiceService
except ImportError:
    EnhancedVoiceService = None

# Import existing voice interfaces if available
try:
    from core.interfaces.voice_provider import IVoiceInput, IVoiceOutput, VoiceFormat
    from core.models.voice import TTSRequest, TTSResponse, STTRequest, STTResponse
    HAS_VOICE_INTERFACES = True
except ImportError:
    HAS_VOICE_INTERFACES = False

# Import Intel optimizer if available
try:
    from services.intel_optimizer import IntelOptimizer
    HAS_INTEL_OPTIMIZER = True
except ImportError:
    HAS_INTEL_OPTIMIZER = False

logger = logging.getLogger(__name__)

class RobustVoiceAdapter:
    """Robust voice service adapter with fallback mechanisms."""
    
    def __init__(self, intel_optimizer: Optional['IntelOptimizer'] = None):
        self.intel_optimizer = intel_optimizer
        self.enhanced_voice = None
        self.is_available = False
        self.has_microphone = False
        self.has_tts = False
        
        # Status tracking
        self.initialization_status = {
            "enhanced_voice": False,
            "microphone": False,
            "tts": False,
            "error_count": 0,
            "last_error": None
        }
        
        # Initialize the service
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize voice service with comprehensive error handling."""
        try:
            if not EnhancedVoiceService:
                logger.warning("Enhanced voice service not available")
                return
            
            logger.info("Initializing robust voice adapter...")
            
            # Create enhanced voice service
            self.enhanced_voice = EnhancedVoiceService()
            
            # Check what components are available
            status = self.enhanced_voice.get_voice_status()
            
            self.has_microphone = status.get("microphone_available", False)
            self.has_tts = status.get("tts_available", False)
            self.is_available = self.has_microphone or self.has_tts
            
            # Update initialization status
            self.initialization_status.update({
                "enhanced_voice": True,
                "microphone": self.has_microphone,
                "tts": self.has_tts
            })
            
            logger.info(f"Voice adapter initialized - TTS: {self.has_tts}, STT: {self.has_microphone}")
            
        except Exception as e:
            logger.error(f"Voice adapter initialization failed: {e}")
            self.initialization_status.update({
                "error_count": self.initialization_status["error_count"] + 1,
                "last_error": str(e)
            })
    
    def speak(self, text: str, blocking: bool = False) -> bool:
        """Speak text with error handling."""
        if not self.has_tts or not self.enhanced_voice:
            print(f"🔊 {text}")  # Fallback to console output
            return False
        
        try:
            self.enhanced_voice.speak(text, blocking=blocking)
            return True
        except Exception as e:
            logger.error(f"TTS error: {e}")
            print(f"🔊 {text}")  # Fallback
            return False
    
    def listen_once(self, timeout: float = 5.0) -> Optional[str]:
        """Listen for speech once with error handling."""
        if not self.has_microphone or not self.enhanced_voice:
            return None
        
        try:
            return self.enhanced_voice.listen_once(timeout=timeout)
        except Exception as e:
            logger.error(f"STT error: {e}")
            return None
    
    def start_continuous_listening(self, callback=None) -> bool:
        """Start continuous listening with callback."""
        if not self.has_microphone or not self.enhanced_voice:
            return False
        
        try:
            if callback:
                self.enhanced_voice.on_speech_recognized = callback
            
            self.enhanced_voice.start_continuous_listening()
            return True
        except Exception as e:
            logger.error(f"Continuous listening error: {e}")
            return False
    
    def stop_continuous_listening(self) -> bool:
        """Stop continuous listening."""
        if not self.enhanced_voice:
            return False
        
        try:
            self.enhanced_voice.stop_continuous_listening()
            return True
        except Exception as e:
            logger.error(f"Stop listening error: {e}")
            return False
    
    def get_speech_from_queue(self) -> Optional[str]:
        """Get speech from queue."""
        if not self.enhanced_voice:
            return None
        
        try:
            return self.enhanced_voice.get_speech_from_queue()
        except Exception as e:
            logger.error(f"Queue error: {e}")
            return None
    
    def test_voice_capabilities(self) -> Dict[str, Any]:
        """Test voice capabilities and return results."""
        results = {
            "adapter_available": self.is_available,
            "microphone_available": self.has_microphone,
            "tts_available": self.has_tts,
            "tests_passed": 0,
            "tests_failed": 0,
            "test_results": {}
        }
        
        # Test TTS
        if self.has_tts:
            try:
                self.speak("Testing text to speech functionality", blocking=True)
                results["tests_passed"] += 1
                results["test_results"]["tts"] = "passed"
            except Exception as e:
                results["tests_failed"] += 1
                results["test_results"]["tts"] = f"failed: {e}"
        
        # Test STT (quick test without waiting for user input)
        if self.has_microphone:
            try:
                # Just test if we can initialize listening without timeout
                text = self.listen_once(timeout=0.1)  # Very short timeout
                results["tests_passed"] += 1
                results["test_results"]["stt"] = "passed"
            except Exception as e:
                results["tests_failed"] += 1
                results["test_results"]["stt"] = f"failed: {e}"
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive voice adapter status."""
        base_status = {
            "adapter_available": self.is_available,
            "microphone_available": self.has_microphone,
            "tts_available": self.has_tts,
            "initialization_status": self.initialization_status,
            "intel_optimizer_available": HAS_INTEL_OPTIMIZER,
            "voice_interfaces_available": HAS_VOICE_INTERFACES
        }
        
        # Add enhanced voice status if available
        if self.enhanced_voice:
            try:
                enhanced_status = self.enhanced_voice.get_voice_status()
                base_status["enhanced_voice_status"] = enhanced_status
            except Exception as e:
                base_status["enhanced_voice_error"] = str(e)
        
        return base_status
    
    def configure_for_intel_hardware(self) -> bool:
        """Configure voice service for Intel hardware optimization."""
        if not self.intel_optimizer:
            return False
        
        try:
            # Get Intel hardware information
            hardware_info = self.intel_optimizer.get_hardware_summary()
            
            # Configure voice settings based on hardware
            if hardware_info.get("npu_available"):
                logger.info("NPU available - could optimize voice processing")
                # Future: NPU voice optimization
            
            if hardware_info.get("gpu_available"):
                logger.info("GPU available - could optimize voice processing")
                # Future: GPU voice optimization
            
            return True
            
        except Exception as e:
            logger.error(f"Intel hardware configuration failed: {e}")
            return False
    
    def safe_shutdown(self):
        """Safely shutdown voice services."""
        try:
            if self.enhanced_voice:
                self.enhanced_voice.stop_continuous_listening()
            logger.info("Voice adapter shutdown complete")
        except Exception as e:
            logger.error(f"Voice adapter shutdown error: {e}")

# Factory function for easy integration
def create_voice_adapter(intel_optimizer: Optional['IntelOptimizer'] = None) -> RobustVoiceAdapter:
    """Create a robust voice adapter instance."""
    return RobustVoiceAdapter(intel_optimizer=intel_optimizer)

# Compatibility function for existing code
def get_voice_service(intel_optimizer: Optional['IntelOptimizer'] = None):
    """Get voice service compatible with existing architecture."""
    return create_voice_adapter(intel_optimizer)

# Example usage and testing
if __name__ == "__main__":
    # Create adapter
    adapter = create_voice_adapter()
    
    # Test capabilities
    print("🧪 Testing Voice Adapter")
    print("=" * 30)
    
    status = adapter.get_status()
    print(f"Adapter available: {status['adapter_available']}")
    print(f"Microphone: {status['microphone_available']}")
    print(f"TTS: {status['tts_available']}")
    
    if adapter.is_available:
        # Run tests
        test_results = adapter.test_voice_capabilities()
        print(f"\nTest results: {test_results['tests_passed']} passed, {test_results['tests_failed']} failed")
        
        # Interactive test if microphone is available
        if adapter.has_microphone:
            print("\n🎤 Say something (5 seconds):")
            result = adapter.listen_once(5.0)
            if result:
                print(f"You said: {result}")
                adapter.speak(f"I heard you say: {result}")
            else:
                print("No speech detected")
    
    # Cleanup
    adapter.safe_shutdown()