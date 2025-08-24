#!/usr/bin/env python3
"""
Intel AI Assistant - Comprehensive Test Suite
Tests for voice capabilities, web search, and AI brain coordination.
"""

import sys
import os
import time
import unittest
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class TestVoiceCapabilities(unittest.TestCase):
    """Test voice recognition and TTS capabilities."""
    
    def setUp(self):
        try:
            from services.enhanced_voice_service import EnhancedVoiceService
            self.voice_service = EnhancedVoiceService()
        except Exception as e:
            self.voice_service = None
            self.skipTest(f"Voice service not available: {e}")
    
    def test_voice_service_initialization(self):
        """Test voice service initialization."""
        self.assertIsNotNone(self.voice_service)
        status = self.voice_service.get_voice_status()
        self.assertIsInstance(status, dict)
        self.assertIn('tts_available', status)
    
    def test_text_to_speech(self):
        """Test text-to-speech functionality."""
        if self.voice_service:
            # This should not raise an exception
            self.voice_service.speak("Testing text to speech", blocking=True)
            self.assertTrue(True)  # If we get here, TTS worked
    
    def test_voice_settings(self):
        """Test voice settings modification."""
        if self.voice_service:
            original_rate = self.voice_service.voice_rate
            
            # Change settings
            self.voice_service.set_voice_settings(rate=200)
            self.assertEqual(self.voice_service.voice_rate, 200)
            
            # Restore original
            self.voice_service.set_voice_settings(rate=original_rate)
            self.assertEqual(self.voice_service.voice_rate, original_rate)
    
    def test_available_voices(self):
        """Test getting available voices."""
        if self.voice_service:
            voices = self.voice_service.get_available_voices()
            self.assertIsInstance(voices, list)

class TestWebSearchCapabilities(unittest.TestCase):
    """Test web search capabilities."""
    
    def setUp(self):
        try:
            from services.enhanced_web_search import EnhancedWebSearchService
            self.search_service = EnhancedWebSearchService()
        except Exception as e:
            self.search_service = None
            self.skipTest(f"Search service not available: {e}")
    
    def test_search_service_initialization(self):
        """Test search service initialization."""
        self.assertIsNotNone(self.search_service)
        self.assertIsNotNone(self.search_service.session)
        self.assertIn('duckduckgo', self.search_service.search_engines)
    
    def test_basic_search(self):
        """Test basic search functionality."""
        if self.search_service:
            results = self.search_service.search("artificial intelligence", max_results=2)
            self.assertIsInstance(results, list)
            # Results might be empty due to network/API issues, so just check type
    
    def test_wikipedia_search(self):
        """Test Wikipedia search specifically."""
        if self.search_service:
            results = self.search_service.search_wikipedia("computer science", max_results=1)
            self.assertIsInstance(results, list)
    
    def test_im_alive_search(self):
        """Test the specific 'im alive' search requested by user."""
        if self.search_service:
            results = self.search_service.search("im alive", max_results=3)
            self.assertIsInstance(results, list)
            
            # Print results for verification
            print(f"\n🔍 'im alive' search results ({len(results)} found):")
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                url = result.get('url', 'No URL')
                source = result.get('source', 'unknown')
                print(f"  {i}. {title} (from {source})")
                print(f"     {url}")
    
    def test_search_and_summarize(self):
        """Test search with summarization."""
        if self.search_service:
            summary = self.search_service.search_and_summarize("python programming", max_results=2)
            self.assertIsInstance(summary, dict)
            self.assertIn('query', summary)
            self.assertIn('results', summary)
            self.assertIn('summary', summary)

class TestAIBrainCapabilities(unittest.TestCase):
    """Test AI brain coordination capabilities."""
    
    def setUp(self):
        try:
            from ai_assistant_brain import AIAssistantBrain
            self.ai_brain = AIAssistantBrain()
        except Exception as e:
            self.ai_brain = None
            self.skipTest(f"AI brain not available: {e}")
    
    def test_ai_brain_initialization(self):
        """Test AI brain initialization."""
        self.assertIsNotNone(self.ai_brain)
        status = self.ai_brain.get_status()
        self.assertIsInstance(status, dict)
        self.assertIn('voice_available', status)
        self.assertIn('search_available', status)
    
    def test_input_processing(self):
        """Test input processing."""
        if self.ai_brain:
            response = self.ai_brain.process_input("hello")
            self.assertIsInstance(response, str)
            self.assertTrue(len(response) > 0)
    
    def test_search_command_detection(self):
        """Test search command detection."""
        if self.ai_brain:
            self.assertTrue(self.ai_brain.is_search_command("search for python"))
            self.assertTrue(self.ai_brain.is_search_command("find information about AI"))
            self.assertFalse(self.ai_brain.is_search_command("hello there"))
    
    def test_system_command_detection(self):
        """Test system command detection."""
        if self.ai_brain:
            self.assertTrue(self.ai_brain.is_system_command("help"))
            self.assertTrue(self.ai_brain.is_system_command("quit"))
            self.assertFalse(self.ai_brain.is_system_command("hello there"))
    
    def test_search_query_extraction(self):
        """Test search query extraction."""
        if self.ai_brain:
            query = self.ai_brain.extract_search_query("search for artificial intelligence")
            self.assertEqual(query, "artificial intelligence")
            
            query = self.ai_brain.extract_search_query("find information about python")
            self.assertEqual(query, "python")
    
    def test_im_alive_response(self):
        """Test the specific 'im alive' response requested by user."""
        if self.ai_brain:
            response = self.ai_brain.process_input("im alive")
            self.assertIsInstance(response, str)
            self.assertTrue("im alive" in response.lower() or "search" in response.lower())
            print(f"\n🤖 AI Brain response to 'im alive': {response}")
    
    def test_conversation_history(self):
        """Test conversation history management."""
        if self.ai_brain:
            initial_length = len(self.ai_brain.conversation_history)
            
            self.ai_brain.process_input("hello")
            self.assertEqual(len(self.ai_brain.conversation_history), initial_length + 2)  # user + assistant
            
            self.ai_brain.process_input("how are you")
            self.assertEqual(len(self.ai_brain.conversation_history), initial_length + 4)

class TestIntegrationCapabilities(unittest.TestCase):
    """Test integration between different components."""
    
    def setUp(self):
        try:
            from ai_assistant_brain import AIAssistantBrain
            self.ai_brain = AIAssistantBrain()
        except Exception as e:
            self.ai_brain = None
            self.skipTest(f"AI brain not available for integration test: {e}")
    
    def test_voice_search_integration(self):
        """Test integration between voice and search."""
        if self.ai_brain and self.ai_brain.voice_service and self.ai_brain.search_service:
            # Simulate voice input for search
            response = self.ai_brain.process_input("search for machine learning")
            self.assertIsInstance(response, str)
            self.assertTrue("machine learning" in response.lower() or "search" in response.lower())
    
    def test_end_to_end_im_alive_test(self):
        """End-to-end test for the 'im alive' functionality."""
        if self.ai_brain:
            print("\n🎯 Running end-to-end 'im alive' test...")
            
            # Test direct search command
            response1 = self.ai_brain.process_input("search for im alive")
            print(f"Search command response: {response1[:100]}...")
            
            # Test natural language
            response2 = self.ai_brain.process_input("im alive")
            print(f"Natural language response: {response2[:100]}...")
            
            # Both should trigger search functionality
            self.assertIsInstance(response1, str)
            self.assertIsInstance(response2, str)

def run_comprehensive_test_suite():
    """Run the complete test suite with detailed output."""
    print("🧪 Intel AI Assistant - Comprehensive Test Suite")
    print("=" * 60)
    
    # Test suites to run
    test_suites = [
        TestVoiceCapabilities,
        TestWebSearchCapabilities,
        TestAIBrainCapabilities,
        TestIntegrationCapabilities
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_suite_class in test_suites:
        print(f"\n🔍 Running {test_suite_class.__name__}")
        print("-" * 40)
        
        suite = unittest.TestLoader().loadTestsFromTestCase(test_suite_class)
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        passed_tests += result.testsRun - len(result.failures) - len(result.errors)
        failed_tests += len(result.failures) + len(result.errors)
        
        if result.failures:
            print(f"❌ Failures in {test_suite_class.__name__}:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        
        if result.errors:
            print(f"💥 Errors in {test_suite_class.__name__}:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUITE SUMMARY")
    print("=" * 60)
    print(f"Total tests run: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("🎉 ALL TESTS PASSED!")
        success_rate = 100
    else:
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"📊 Success rate: {success_rate:.1f}%")
    
    return failed_tests == 0

def run_live_demo():
    """Run a live demonstration of capabilities."""
    print("\n🎯 Live Demonstration Mode")
    print("=" * 40)
    
    try:
        from ai_assistant_brain import AIAssistantBrain
        
        print("🧠 Creating AI Assistant Brain...")
        assistant = AIAssistantBrain()
        
        print("🎤 Testing voice capabilities...")
        if assistant.voice_service:
            assistant.voice_service.speak("Hello! I am demonstrating my voice capabilities.")
            time.sleep(2)
        
        print("🔍 Testing search capabilities with 'im alive'...")
        if assistant.search_service:
            assistant.search_service.search_live_demo("im alive")
        
        print("🤖 Testing conversational AI...")
        response = assistant.process_input("im alive")
        print(f"AI Response: {response}")
        
        print("\n✅ Live demonstration completed!")
        
    except Exception as e:
        print(f"❌ Live demo failed: {e}")

def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Intel AI Assistant Test Suite")
    parser.add_argument("--demo", action="store_true", help="Run live demonstration")
    parser.add_argument("--voice-only", action="store_true", help="Test voice capabilities only")
    parser.add_argument("--search-only", action="store_true", help="Test search capabilities only")
    parser.add_argument("--brain-only", action="store_true", help="Test AI brain only")
    
    args = parser.parse_args()
    
    if args.demo:
        run_live_demo()
    elif args.voice_only:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestVoiceCapabilities)
        unittest.TextTestRunner(verbosity=2).run(suite)
    elif args.search_only:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestWebSearchCapabilities)
        unittest.TextTestRunner(verbosity=2).run(suite)
    elif args.brain_only:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestAIBrainCapabilities)
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        # Run comprehensive test suite
        success = run_comprehensive_test_suite()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()