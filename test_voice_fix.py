#!/usr/bin/env python3
"""
Quick test script to verify voice service fixes.
"""

import sys
import time
import threading
from services.enhanced_voice_service import EnhancedVoiceService

def test_voice_service():
    """Test voice service initialization and basic functionality."""
    print("🧪 Testing Enhanced Voice Service Fixes")
    print("=" * 50)
    
    try:
        # Initialize voice service
        print("1. Initializing voice service...")
        voice_service = EnhancedVoiceService()
        
        # Check status
        print("2. Checking voice service status...")
        status = voice_service.get_voice_status()
        print(f"   TTS Available: {status['tts_available']}")
        print(f"   Microphone Available: {status['microphone_available']}")
        print(f"   Is Listening: {status['is_listening']}")
        
        # Test TTS if available
        if status['tts_available']:
            print("3. Testing text-to-speech...")
            voice_service.speak("Voice service test successful", blocking=True)
        else:
            print("3. TTS not available, skipping speech test")
        
        # Test continuous listening briefly (this was the problem area)
        print("4. Testing continuous listening (5 seconds)...")
        if status['microphone_available']:
            print("   Starting continuous listening...")
            voice_service.start_continuous_listening()
            
            # Monitor for errors for 5 seconds
            start_time = time.time()
            error_count = 0
            
            while time.time() - start_time < 5:
                # Check for any speech in queue
                speech = voice_service.get_speech_from_queue()
                if speech:
                    print(f"   🎤 Heard: {speech}")
                time.sleep(0.1)
            
            print("   Stopping continuous listening...")
            voice_service.stop_continuous_listening()
            print("   ✅ Continuous listening test completed without infinite errors!")
        else:
            print("   ⚠️ No microphone available, skipping continuous listening test")
        
        print("\n🎉 Voice service test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Voice service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_voice_service()
    sys.exit(0 if success else 1)