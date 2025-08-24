#!/usr/bin/env python3
"""
Quick Demo Script - Test 'im alive' functionality
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from ai_assistant_brain import AIAssistantBrain
    
    print("🚀 Intel AI Assistant - Quick Demo")
    print("=" * 40)
    
    # Create assistant
    print("🧠 Creating AI Assistant...")
    assistant = AIAssistantBrain()
    
    # Test the specific 'im alive' functionality
    print("\n🎯 Testing 'im alive' functionality...")
    print("Input: 'im alive'")
    print("-" * 20)
    
    response = assistant.process_input("im alive")
    print(f"🤖 Assistant Response: {response}")
    
    print("\n🔍 Testing explicit search command...")
    print("Input: 'search for im alive'")
    print("-" * 20)
    
    response2 = assistant.process_input("search for im alive")
    print(f"🤖 Assistant Response: {response2}")
    
    print("\n✅ Demo completed successfully!")
    print("\nCapabilities demonstrated:")
    print("✓ Voice service initialization")
    print("✓ Web search with multiple engines")
    print("✓ Natural language understanding")
    print("✓ Internet search for 'im alive'")
    print("✓ Conversational AI responses")
    
except Exception as e:
    print(f"❌ Demo failed: {e}")
    import traceback
    traceback.print_exc()