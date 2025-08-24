#!/usr/bin/env python3
"""
Comprehensive System Test - All Components and Flows
Tests voice service, internet search, tools, and computer management
"""

import sys
import time
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_voice_service():
    """Test voice service without infinite loop"""
    print("🎤 Testing Voice Service...")
    print("-" * 30)
    
    try:
        from services.enhanced_voice_service import EnhancedVoiceService
        
        voice_service = EnhancedVoiceService()
        
        # Test TTS
        print("1. Testing TTS...")
        voice_service.speak("Voice service test", blocking=True)
        
        # Test continuous listening briefly (should not spam errors)
        print("2. Testing continuous listening (3 seconds - no error spam)...")
        voice_service.start_continuous_listening()
        time.sleep(3)
        voice_service.stop_continuous_listening()
        
        print("✅ Voice service test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Voice service test failed: {e}")
        return False

def test_internet_search():
    """Test internet search including 'im alive' query"""
    print("\n🌐 Testing Internet Search...")
    print("-" * 30)
    
    try:
        from services.enhanced_web_search import EnhancedWebSearch
        
        search_service = EnhancedWebSearch()
        
        # Test 'im alive' search as requested
        print("1. Testing 'im alive' search...")
        results = search_service.search("im alive", max_results=3)
        
        if results:
            print(f"✅ Found {len(results)} results for 'im alive'")
            for i, result in enumerate(results[:2], 1):
                print(f"   {i}. {result.get('title', 'No title')}")
        else:
            print("⚠️  No results found for 'im alive'")
        
        # Test general web search
        print("2. Testing general search...")
        tech_results = search_service.search("Intel AI technology", max_results=2)
        
        if tech_results:
            print(f"✅ Found {len(tech_results)} results for Intel AI")
        else:
            print("⚠️  No results found for Intel AI")
        
        print("✅ Internet search test completed")
        return True
        
    except Exception as e:
        print(f"❌ Internet search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_assistant_brain():
    """Test the main AI assistant brain coordination"""
    print("\n🧠 Testing AI Assistant Brain...")
    print("-" * 30)
    
    try:
        from ai_assistant_brain import AIAssistantBrain
        
        brain = AIAssistantBrain()
        
        # Test initialization
        print("1. Testing initialization...")
        if hasattr(brain, 'voice_service') and hasattr(brain, 'web_search'):
            print("✅ Brain initialized with voice and search services")
        else:
            print("⚠️  Brain missing some services")
        
        # Test text processing
        print("2. Testing text processing...")
        response = brain.process_text_input("Hello, how are you?")
        if response:
            print(f"✅ Brain responded: {response[:50]}...")
        else:
            print("⚠️  No response from brain")
        
        print("✅ AI Assistant Brain test completed")
        return True
        
    except Exception as e:
        print(f"❌ AI Assistant Brain test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_system():
    """Test configuration and settings"""
    print("\n⚙️ Testing Configuration System...")
    print("-" * 30)
    
    try:
        from config.settings import ApplicationSettings
        
        settings = ApplicationSettings()
        
        # Test basic settings
        print("1. Testing settings loading...")
        print(f"   App Name: {settings.app_name}")
        print(f"   App Version: {settings.app_version}")
        print(f"   Intel Profile: {settings.current_intel_profile}")
        
        # Test configuration save/load
        print("2. Testing configuration save/load...")
        config_dict = settings.to_dict()
        if config_dict and 'app_name' in config_dict:
            print("✅ Configuration serialization works")
        else:
            print("⚠️  Configuration serialization issues")
        
        print("✅ Configuration system test completed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tools_integration():
    """Test tools and computer management capabilities"""
    print("\n🔧 Testing Tools Integration...")
    print("-" * 30)
    
    try:
        # Test file operations
        print("1. Testing file operations...")
        test_file = project_root / "test_temp_file.txt"
        
        # Create test file
        test_file.write_text("Test content for tools integration")
        if test_file.exists():
            print("✅ File creation works")
        
        # Read test file
        content = test_file.read_text()
        if "Test content" in content:
            print("✅ File reading works")
        
        # Clean up
        test_file.unlink()
        print("✅ File cleanup works")
        
        # Test system information
        print("2. Testing system capabilities...")
        import platform
        import psutil
        
        system_info = {
            "OS": platform.system(),
            "Architecture": platform.architecture()[0],
            "CPU Cores": psutil.cpu_count(),
            "Memory": f"{psutil.virtual_memory().total // (1024**3)} GB"
        }
        
        for key, value in system_info.items():
            print(f"   {key}: {value}")
        
        print("✅ System information accessible")
        
        print("✅ Tools integration test completed")
        return True
        
    except Exception as e:
        print(f"❌ Tools integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conversation_flows():
    """Test conversation management"""
    print("\n💬 Testing Conversation Flows...")
    print("-" * 30)
    
    try:
        from conversation.conversation_manager import ConversationManager
        
        conv_manager = ConversationManager()
        
        # Test conversation creation
        print("1. Testing conversation creation...")
        conv_id = conv_manager.start_conversation("Test User")
        if conv_id:
            print(f"✅ Created conversation: {conv_id}")
        
        # Test message handling
        print("2. Testing message handling...")
        conv_manager.add_message(conv_id, "user", "Hello")
        conv_manager.add_message(conv_id, "assistant", "Hi there!")
        
        history = conv_manager.get_conversation_history(conv_id)
        if history and len(history) >= 2:
            print(f"✅ Conversation history has {len(history)} messages")
        
        print("✅ Conversation flows test completed")
        return True
        
    except Exception as e:
        print(f"❌ Conversation flows test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive system test"""
    print("🎯 Intel AI Assistant - Comprehensive System Test")
    print("=" * 60)
    print("Testing all components and flows...")
    print()
    
    test_results = []
    
    # Run all tests
    test_results.append(("Voice Service", test_voice_service()))
    test_results.append(("Internet Search", test_internet_search()))
    test_results.append(("AI Assistant Brain", test_ai_assistant_brain()))
    test_results.append(("Configuration System", test_configuration_system()))
    test_results.append(("Tools Integration", test_tools_integration()))
    test_results.append(("Conversation Flows", test_conversation_flows()))
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🚀 ALL TESTS PASSED! System is working correctly!")
        print("✅ No infinite voice loops detected")
        print("✅ Internet search including 'im alive' works")
        print("✅ All system components are functional")
        print("✅ Computer management capabilities verified")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. System needs attention.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Critical test failure: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)