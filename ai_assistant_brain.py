"""
AI Assistant Brain - Main Intelligence Coordinator (Clean Version)
Integrates voice recognition, web search, and conversational AI with robust error handling.
"""

import sys
import os
import time
import threading
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import services with fallback
try:
    from services.robust_voice_adapter import create_voice_adapter
    from services.enhanced_web_search import EnhancedWebSearchService
except ImportError as e:
    print(f"⚠️  Import warning: {e}")
    create_voice_adapter = None
    EnhancedWebSearchService = None

# Import Intel optimizer if available
try:
    from services.intel_optimizer import IntelOptimizer
except ImportError:
    IntelOptimizer = None

logger = logging.getLogger(__name__)

class AIAssistantBrain:
    """Main AI Assistant coordinator with robust error handling."""
    
    def __init__(self):
        self.voice_adapter = None
        self.search_service = None
        self.intel_optimizer = None
        self.is_running = False
        self.conversation_history = []
        
        # Configuration
        self.config = {
            "voice_enabled": True,
            "search_enabled": True,
            "auto_speak_responses": True,
            "max_conversation_history": 50,
            "safe_mode": True,
            "error_recovery": True
        }
        
        # Error tracking
        self.error_count = 0
        self.last_error = None
        
        # Initialize services
        self.initialize_services()
        
        # Set up voice callbacks
        self.setup_voice_callbacks()
    
    def initialize_services(self):
        """Initialize voice and search services with comprehensive error handling."""
        print("🧠 Initializing AI Assistant Brain...")
        
        # Initialize Intel optimizer if available
        if IntelOptimizer:
            try:
                self.intel_optimizer = IntelOptimizer()
                print("✅ Intel optimizer initialized")
            except Exception as e:
                print(f"⚠️  Intel optimizer failed: {e}")
                self.intel_optimizer = None
        
        # Initialize voice adapter
        if create_voice_adapter and self.config["voice_enabled"]:
            try:
                self.voice_adapter = create_voice_adapter(self.intel_optimizer)
                
                # Check voice adapter status
                status = self.voice_adapter.get_status()
                if status["adapter_available"]:
                    capabilities = []
                    if status["microphone_available"]:
                        capabilities.append("speech recognition")
                    if status["tts_available"]:
                        capabilities.append("text-to-speech")
                    
                    if capabilities:
                        print(f"✅ Voice service initialized ({', '.join(capabilities)})")
                    else:
                        print("⚠️  Voice service initialized but no capabilities available")
                else:
                    print("⚠️  Voice service failed to initialize")
                    
            except Exception as e:
                print(f"⚠️  Voice service failed to initialize: {e}")
                self.voice_adapter = None
                self._log_error("voice_initialization", e)
        
        # Initialize search service
        if EnhancedWebSearchService and self.config["search_enabled"]:
            try:
                self.search_service = EnhancedWebSearchService()
                print("✅ Search service initialized")
            except Exception as e:
                print(f"⚠️  Search service failed to initialize: {e}")
                self.search_service = None
                self._log_error("search_initialization", e)
        
        print("🎯 AI Assistant Brain ready!")
    
    def setup_voice_callbacks(self):
        """Set up voice recognition callbacks with error handling."""
        if self.voice_adapter and hasattr(self.voice_adapter, 'enhanced_voice'):
            try:
                if self.voice_adapter.enhanced_voice:
                    self.voice_adapter.enhanced_voice.on_speech_recognized = self.handle_voice_input
                    self.voice_adapter.enhanced_voice.on_speech_error = self.handle_voice_error
            except Exception as e:
                self._log_error("voice_callback_setup", e)
    
    def handle_voice_input(self, text: str):
        """Handle recognized voice input with error recovery."""
        try:
            print(f"🎤 Voice input: {text}")
            response = self.process_input(text)
            
            if response and self.config["auto_speak_responses"]:
                self.speak(response)
        except Exception as e:
            self._log_error("voice_input_handling", e)
            if self.config["error_recovery"]:
                self.speak("Sorry, I had trouble processing that. Could you try again?")
    
    def handle_voice_error(self, error: str):
        """Handle voice recognition errors."""
        # Don't spam with microphone errors - these are now handled gracefully
        if "NoneType" in error or "close" in error:
            # Critical microphone error - switch to text mode if needed
            if self.config.get("auto_switch_to_text", False):
                logger.info("Switching to text-only mode due to voice errors")
                self.config["voice_enabled"] = False
            return
        
        # Log other voice errors
        if "timeout" not in error.lower():
            logger.warning(f"Voice error: {error}")
    
    def speak(self, text: str):
        """Speak text using voice adapter with fallback."""
        try:
            if self.voice_adapter:
                success = self.voice_adapter.speak(text)
                if not success and self.config["safe_mode"]:
                    # Fallback already handled in adapter
                    pass
            else:
                print(f"🔊 {text}")
        except Exception as e:
            self._log_error("speech_output", e)
            print(f"🔊 {text}")  # Always fallback to text
    
    def process_input(self, user_input: str) -> str:
        """Process user input and generate response with error handling."""
        try:
            user_input = user_input.strip().lower()
            
            # Add to conversation history
            self.add_to_history("user", user_input)
            
            # Check for commands
            if self.is_search_command(user_input):
                response = self.handle_search_command(user_input)
            elif self.is_system_command(user_input):
                response = self.handle_system_command(user_input)
            else:
                response = self.generate_conversational_response(user_input)
            
            # Add response to history
            self.add_to_history("assistant", response)
            
            return response
            
        except Exception as e:
            self._log_error("input_processing", e)
            return "I apologize, but I encountered an error processing your request. Please try again."
    
    def is_search_command(self, text: str) -> bool:
        """Check if input is a search command."""
        search_keywords = [
            "search", "find", "look up", "google", "internet",
            "web search", "search for", "find information about"
        ]
        
        return any(keyword in text for keyword in search_keywords)
    
    def is_system_command(self, text: str) -> bool:
        """Check if input is a system command."""
        system_keywords = [
            "stop", "quit", "exit", "goodbye", "bye",
            "help", "commands", "what can you do",
            "test voice", "test search", "status"
        ]
        
        return any(keyword in text for keyword in system_keywords)
    
    def handle_search_command(self, text: str) -> str:
        """Handle search commands with error handling."""
        if not self.search_service:
            return "Sorry, web search is not available right now."
        
        # Extract search query
        search_query = self.extract_search_query(text)
        
        if not search_query:
            return "What would you like me to search for?"
        
        try:
            print(f"🔍 Searching for: {search_query}")
            results = self.search_service.search(search_query, max_results=3)
            
            if results:
                response = f"I found {len(results)} results for '{search_query}':\n\n"
                
                for i, result in enumerate(results, 1):
                    title = result.get('title', 'No title')
                    snippet = result.get('snippet', 'No description')[:150]
                    
                    response += f"{i}. {title}\n"
                    if snippet:
                        response += f"   {snippet}...\n\n"
                
                return response.strip()
            else:
                return f"I couldn't find any results for '{search_query}'. Try a different search term."
                
        except Exception as e:
            self._log_error("search_command", e)
            return f"I encountered an error while searching for '{search_query}'. Please try again."
    
    def extract_search_query(self, text: str) -> str:
        """Extract search query from user input."""
        # Remove common search prefixes
        prefixes = [
            "search for", "look up", "find", "google", "search",
            "find information about", "tell me about", "what is"
        ]
        
        query = text
        for prefix in prefixes:
            if query.startswith(prefix):
                query = query[len(prefix):].strip()
                break
        
        return query
    
    def handle_system_command(self, text: str) -> str:
        """Handle system commands."""
        if any(keyword in text for keyword in ["stop", "quit", "exit", "goodbye", "bye"]):
            self.stop()
            return "Goodbye! It was nice talking with you."
        
        elif "help" in text or "commands" in text or "what can you do" in text:
            return self.get_help_message()
        
        elif "status" in text:
            return self.get_status_message()
        
        elif "test voice" in text:
            if self.voice_adapter:
                def run_voice_test():
                    try:
                        results = self.voice_adapter.test_voice_capabilities()
                        print(f"\n🧪 Voice test results:")
                        print(f"   Tests passed: {results['tests_passed']}")
                        print(f"   Tests failed: {results['tests_failed']}")
                        for test_name, result in results['test_results'].items():
                            print(f"   {test_name}: {result}")
                    except Exception as e:
                        print(f"Voice test failed: {e}")
                        
                threading.Thread(target=run_voice_test, daemon=True).start()
                return "Running voice system test. Check console for results."
            else:
                return "Voice service is not available."
        
        elif "test search" in text:
            if self.search_service:
                def run_search_test():
                    try:
                        self.search_service.test_search_engines()
                    except Exception as e:
                        print(f"Search test failed: {e}")
                        
                threading.Thread(target=run_search_test, daemon=True).start()
                return "Running search engine test. Check console for results."
            else:
                return "Search service is not available."
        
        return "I'm not sure how to help with that. Try asking me to search for something or say 'help' for available commands."
    
    def generate_conversational_response(self, text: str) -> str:
        """Generate a conversational response."""
        # Simple conversational responses
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
        if any(greeting in text for greeting in greetings):
            return "Hello! I'm your Intel AI Assistant. I can help you search the internet or chat with you. What would you like to do?"
        
        if "how are you" in text:
            return "I'm doing great! I'm an AI assistant with voice and search capabilities. How can I help you today?"
        
        if "your name" in text or "who are you" in text:
            return "I'm your Intel AI Assistant! I can help you search the internet, answer questions, and have conversations. I'm optimized for Intel hardware."
        
        if "im alive" in text or "i'm alive" in text:
            if self.search_service:
                # This is the specific test case requested
                def search_demo():
                    try:
                        self.search_service.search_live_demo("im alive")
                    except Exception as e:
                        print(f"Search demo failed: {e}")
                        
                threading.Thread(target=search_demo, daemon=True).start()
                return "I'll search for 'im alive' on the internet for you! Check the console for detailed results."
            else:
                return "I heard you say 'I'm alive'! That's great. Unfortunately, my search capabilities aren't available right now."
        
        if "thank you" in text or "thanks" in text:
            return "You're welcome! Is there anything else I can help you with?"
        
        # Default response
        return "That's interesting! I can help you search for information on the internet or answer questions. Just ask me to search for something, or say 'help' to see what I can do."
    
    def get_help_message(self) -> str:
        """Get help message with available commands."""
        help_text = """
🤖 Intel AI Assistant - Available Commands:

🔍 Search Commands:
  • "Search for [topic]" - Search the internet
  • "Find information about [topic]"
  • "Look up [topic]"

💬 Conversation:
  • Just talk to me naturally!
  • Ask questions or have a chat

🛠️ System Commands:
  • "Help" - Show this help message
  • "Status" - Show system status
  • "Test voice" - Test voice capabilities
  • "Test search" - Test search engines
  • "Stop" or "Goodbye" - Exit the assistant

🎤 Voice Features:
  • Speak naturally - I'll understand you
  • I can respond with voice or text
  • Say "im alive" for a special search demo!

Just start talking or typing to begin!
        """
        
        return help_text.strip()
    
    def get_status_message(self) -> str:
        """Get system status message."""
        status = self.get_status()
        
        msg = "🔧 System Status:\n"
        msg += f"  • Voice available: {'✅' if status['voice_available'] else '❌'}\n"
        msg += f"  • Search available: {'✅' if status['search_available'] else '❌'}\n"
        msg += f"  • Intel optimizer: {'✅' if status['intel_optimizer_available'] else '❌'}\n"
        msg += f"  • Conversations: {status['conversation_history']}\n"
        
        if 'voice_status' in status:
            voice_status = status['voice_status']
            msg += f"  • Microphone: {'✅' if voice_status['microphone_available'] else '❌'}\n"
            msg += f"  • Text-to-speech: {'✅' if voice_status['tts_available'] else '❌'}\n"
        
        if self.error_count > 0:
            msg += f"  • Errors: {self.error_count} (last: {self.last_error})\n"
        
        return msg
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history."""
        try:
            self.conversation_history.append({
                "role": role,
                "content": content,
                "timestamp": time.time()
            })
            
            # Limit history size
            if len(self.conversation_history) > self.config["max_conversation_history"]:
                self.conversation_history = self.conversation_history[-self.config["max_conversation_history"]:]
        except Exception as e:
            self._log_error("history_management", e)
    
    def start_interactive_mode(self):
        """Start interactive mode with both voice and text input."""
        print("\n🎯 Intel AI Assistant - Interactive Mode")
        print("=" * 50)
        print("Say something or type your message. Type 'quit' to exit.")
        print("For voice input, just speak naturally!")
        print()
        
        self.is_running = True
        
        # Start voice listening if available
        if self.voice_adapter and self.voice_adapter.has_microphone:
            try:
                listening_started = self.voice_adapter.start_continuous_listening()
                if listening_started:
                    print("🎤 Voice recognition is active")
                else:
                    print("⚠️  Voice recognition failed to start")
            except Exception as e:
                print(f"⚠️  Voice recognition error: {e}")
        
        # Welcome message
        welcome_msg = "Hello! I'm your Intel AI Assistant. How can I help you today?"
        print(f"🤖 Assistant: {welcome_msg}")
        self.speak(welcome_msg)
        
        try:
            while self.is_running:
                try:
                    # Check for voice input
                    if self.voice_adapter:
                        voice_input = self.voice_adapter.get_speech_from_queue()
                        if voice_input:
                            print(f"🎤 You (voice): {voice_input}")
                            response = self.process_input(voice_input)
                            print(f"🤖 Assistant: {response}")
                            continue
                    
                    # Small delay to prevent high CPU usage
                    time.sleep(0.1)
                    
                except (EOFError, KeyboardInterrupt):
                    break
                except Exception as e:
                    self._log_error("interactive_loop", e)
                    time.sleep(0.5)  # Brief pause on error
                
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def start_text_only_mode(self):
        """Start text-only interactive mode."""
        print("\n💬 Intel AI Assistant - Text Mode")
        print("=" * 40)
        print("Type your messages. Type 'quit' to exit.")
        print()
        
        self.is_running = True
        
        # Welcome message
        welcome_msg = "Hello! I'm your Intel AI Assistant. How can I help you today?"
        print(f"🤖 Assistant: {welcome_msg}")
        
        try:
            while self.is_running:
                try:
                    user_input = input("You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() in ['quit', 'exit', 'stop']:
                        break
                    
                    response = self.process_input(user_input)
                    print(f"🤖 Assistant: {response}")
                    
                except (EOFError, KeyboardInterrupt):
                    break
                except Exception as e:
                    self._log_error("text_mode", e)
                    print("Sorry, I encountered an error. Please try again.")
                    
        finally:
            self.stop()
    
    def run_demo(self):
        """Run a quick demo of capabilities."""
        print("\n🎯 Intel AI Assistant - Demo Mode")
        print("=" * 40)
        
        try:
            # Test voice capabilities
            if self.voice_adapter and self.voice_adapter.has_tts:
                print("🎤 Testing voice capabilities...")
                self.speak("Hello! I am your Intel AI Assistant. Let me demonstrate my capabilities.")
                time.sleep(2)
            
            # Test search capabilities
            if self.search_service:
                print("🔍 Testing search capabilities...")
                self.speak("Now I'll search the internet for 'im alive' as requested.")
                
                # Perform the specific search requested
                response = self.process_input("search for im alive")
                print(f"🤖 Search result: {response}")
                if self.voice_adapter:
                    self.speak("Search completed! Check the console for detailed results.")
            
            # Interactive demo
            if self.voice_adapter:
                self.speak("Demo completed! You can now interact with me by speaking or typing.")
            
            print("\n🎮 Interactive demo starting...")
            self.start_text_only_mode()
            
        except Exception as e:
            print(f"Demo failed: {e}")
            self._log_error("demo_mode", e)
    
    def stop(self):
        """Stop the assistant safely."""
        self.is_running = False
        
        try:
            if self.voice_adapter:
                self.voice_adapter.safe_shutdown()
        except Exception as e:
            self._log_error("shutdown", e)
        
        print("\n👋 Intel AI Assistant stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        status = {
            "running": self.is_running,
            "voice_available": self.voice_adapter is not None,
            "search_available": self.search_service is not None,
            "intel_optimizer_available": self.intel_optimizer is not None,
            "conversation_history": len(self.conversation_history),
            "error_count": self.error_count,
            "config": self.config
        }
        
        # Add detailed voice status if available
        if self.voice_adapter:
            try:
                status["voice_status"] = self.voice_adapter.get_status()
            except Exception as e:
                status["voice_error"] = str(e)
                
        return status
    
    def _log_error(self, component: str, error: Exception):
        """Log error for debugging."""
        self.error_count += 1
        self.last_error = f"{component}: {str(error)}"
        logger.error(f"AI Brain error in {component}: {error}")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Intel AI Assistant")
    parser.add_argument("--text-only", action="store_true", help="Run in text-only mode")
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    parser.add_argument("--test", action="store_true", help="Run tests only")
    
    args = parser.parse_args()
    
    # Create assistant
    assistant = AIAssistantBrain()
    
    try:
        if args.test:
            # Run tests
            print("🧪 Running system tests...")
            
            status = assistant.get_status()
            print("System Status:")
            for key, value in status.items():
                if key != "config":
                    print(f"  {key}: {value}")
            
            # Test voice if available
            if assistant.voice_adapter:
                print("\nTesting voice capabilities...")
                try:
                    results = assistant.voice_adapter.test_voice_capabilities()
                    print(f"Voice tests: {results['tests_passed']} passed, {results['tests_failed']} failed")
                except Exception as e:
                    print(f"Voice test error: {e}")
            
            # Test search if available
            if assistant.search_service:
                print("\nTesting search capabilities...")
                try:
                    results = assistant.search_service.search("test query", 1)
                    print(f"Search test: {'✅ Working' if results else '⚠️ No results'}")
                except Exception as e:
                    print(f"Search test: ❌ Failed ({e})")
            
            # Test the specific "im alive" functionality
            print("\nTesting 'im alive' functionality...")
            try:
                response = assistant.process_input("im alive")
                print(f"'Im alive' response: {response}")
            except Exception as e:
                print(f"'Im alive' test failed: {e}")
        
        elif args.demo:
            assistant.run_demo()
        
        elif args.text_only:
            assistant.start_text_only_mode()
        
        else:
            # Default: try interactive mode with voice
            if assistant.voice_adapter and assistant.voice_adapter.has_microphone:
                assistant.start_interactive_mode()
            else:
                print("🎤 Voice not available, starting text-only mode...")
                assistant.start_text_only_mode()
                
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Assistant failed: {e}")
        logger.error(f"Main execution error: {e}")
    finally:
        assistant.stop()

if __name__ == "__main__":
    main()