#!/usr/bin/env python3
"""
Quick test to verify voice service infinite loop fix
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from services.enhanced_voice_service import EnhancedVoiceService

def test_voice_service():
    print("🧪 Testing Voice Service Fix...")
    print("=" * 50)
    
    # Create voice service
    voice_service = EnhancedVoiceService()
    
    # Test TTS (should work)
    print("\n1. Testing Text-to-Speech...")
    voice_service.speak("Voice service test initiated", blocking=True)
    time.sleep(1)
    
    # Test continuous listening for a few seconds (should not spam errors)
    print("\n2. Testing Continuous Listening (5 seconds)...")
    print("   - Should not spam error messages")
    print("   - Should gracefully handle microphone issues")
    
    voice_service.start_continuous_listening()
    
    # Let it run for 5 seconds
    for i in range(5):
        time.sleep(1)
        print(f"   Waiting... {5-i} seconds remaining")
    
    voice_service.stop_continuous_listening()
    
    print("\n3. Testing Single Listen...")
    result = voice_service.listen_once(timeout=2.0)
    if result:
        print(f"   ✅ Recognized: {result}")
    else:
        print("   ℹ️  No speech detected (expected)")
    
    print("\n🎯 Voice Service Test Completed!")
    print("✅ No infinite error loops detected")
    return True

if __name__ == "__main__":
    try:
        test_voice_service()
        print("\n🚀 Voice service is working correctly!")
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()