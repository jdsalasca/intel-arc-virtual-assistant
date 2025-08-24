"""
AI Assistant Brain - Main Intelligence Coordinator
Integrates voice recognition, web search, and conversational AI.
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

# Import services
try:
    from services.enhanced_voice_service import EnhancedVoiceService
    from services.enhanced_web_search import EnhancedWebSearchService
except ImportError as e:
    print(f"⚠️  Import warning: {e}")
    EnhancedVoiceService = None
    EnhancedWebSearchService = None

logger = logging.getLogger(__name__)

class AIAssistantBrain:
    """Main AI Assistant coordinator."""
    
    def __init__(self):
        self.voice_service = None
        self.search_service = None
        self.is_running = False
        self.conversation_history = []
        
        # Configuration
        self.config = {
            "voice_enabled": True,
            "search_enabled": True,
            "auto_speak_responses": True,
            "max_conversation_history": 50
        }
        
        # Initialize services
        self.initialize_services()
        
        # Set up voice callbacks
        self.setup_voice_callbacks()
    
    def initialize_services(self):
        """Initialize voice and search services."""
        print("🧠 Initializing AI Assistant Brain...")
        
        # Initialize voice service
        if EnhancedVoiceService and self.config["voice_enabled"]:
            try:
                self.voice_service = EnhancedVoiceService()
                print("✅ Voice service initialized")
            except Exception as e:
                print(f"⚠️  Voice service failed to initialize: {e}")
                self.voice_service = None
        
        # Initialize search service
        if EnhancedWebSearchService and self.config["search_enabled"]:
            try:
                self.search_service = EnhancedWebSearchService()
                print("✅ Search service initialized")
            except Exception as e:
                print(f"⚠️  Search service failed to initialize: {e}")
                self.search_service = None
        
        print("🎯 AI Assistant Brain ready!")
    
    def setup_voice_callbacks(self):
        """Set up voice recognition callbacks."""
        if self.voice_service:
            self.voice_service.on_speech_recognized = self.handle_voice_input
            self.voice_service.on_speech_error = self.handle_voice_error
    
    def handle_voice_input(self, text: str):
        """Handle recognized voice input."""
        print(f"🎤 Voice input: {text}")
        response = self.process_input(text)
        
        if response and self.config["auto_speak_responses"]:
            self.speak(response)
    
    def handle_voice_error(self, error: str):
        """Handle voice recognition errors."""
        logger.error(f"Voice error: {error}")
    
    def speak(self, text: str):
        """Speak text using voice service."""
        if self.voice_service:
            self.voice_service.speak(text)
        else:
            print(f"🔊 {text}")
    
    def process_input(self, user_input: str) -> str:
        """Process user input and generate response."""
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
            "test voice", "test search"
        ]
        
        return any(keyword in text for keyword in system_keywords)
    
    def handle_search_command(self, text: str) -> str:
        """Handle search commands."""
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
            logger.error(f"Search error: {e}")
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
        
        elif "test voice" in text:
            if self.voice_service:
                threading.Thread(target=self.voice_service.test_voice_system, daemon=True).start()
                return "Running voice system test. Please follow the instructions."
            else:
                return "Voice service is not available."
        
        elif "test search" in text:
            if self.search_service:
                threading.Thread(target=self.search_service.test_search_engines, daemon=True).start()
                return "Running search engine test. Check the console for results."
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
            return "I'm doing great! I'm an AI assistant powered by Intel technology. How can I help you today?"
        
        if "your name" in text or "who are you" in text:
            return "I'm your Intel AI Assistant! I can help you search the internet, answer questions, and have conversations. I'm powered by Intel's advanced hardware optimization."
        
        if "im alive" in text or "i'm alive" in text:
            if self.search_service:
                # This is the specific test case requested
                threading.Thread(target=lambda: self.search_service.search_live_demo("im alive"), daemon=True).start()
                return "I'll search for 'im alive' on the internet for you! Check the console for detailed results."
            else:
                return "I heard you say 'I'm alive'! That's great. Unfortunately, my search capabilities aren't available right now."
        
        if "thank you" in text or "thanks" in text:
            return "You're welcome! Is there anything else I can help you with?"
        
        # Default response
        return "That's interesting! I can help you search for information on the internet. Just ask me to search for something, or say 'help' to see what I can do."
    
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
  • "Test voice" - Test voice recognition and speech
  • "Test search" - Test search engines
  • "Stop" or "Goodbye" - Exit the assistant

🎤 Voice Features:
  • Speak naturally - I'll understand you
  • I can respond with voice or text
  • Say "im alive" for a special search demo!

Just start talking or typing to begin!
        """
        
        return help_text.strip()
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        
        # Limit history size
        if len(self.conversation_history) > self.config["max_conversation_history"]:
            self.conversation_history = self.conversation_history[-self.config["max_conversation_history"]:]
    
    def start_interactive_mode(self):
        """Start interactive mode with both voice and text input."""
        print("\n🎯 Intel AI Assistant - Interactive Mode")
        print("=" * 50)
        print("Say something or type your message. Type 'quit' to exit.")
        print("For voice input, just speak naturally!")
        print()
        
        self.is_running = True
        
        # Start voice listening if available
        if self.voice_service:
            self.voice_service.start_continuous_listening()
            print("🎤 Voice recognition is active")
        
        # Welcome message
        welcome_msg = "Hello! I'm your Intel AI Assistant. How can I help you today?"
        print(f"🤖 Assistant: {welcome_msg}")
        self.speak(welcome_msg)
        
        try:
            while self.is_running:
                # Check for voice input
                if self.voice_service:
                    voice_input = self.voice_service.get_speech_from_queue()
                    if voice_input:
                        print(f"🎤 You (voice): {voice_input}")
                        response = self.process_input(voice_input)
                        print(f"🤖 Assistant: {response}")
                        continue
                
                # Check for text input (non-blocking)
                try:
                    import select
                    import sys
                    
                    # For Windows, use input with timeout
                    if sys.platform == "win32":
                        time.sleep(0.1)  # Small delay for voice input
                        continue
                    else:
                        # Unix-like systems
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            text_input = input().strip()
                            if text_input:
                                print(f"⌨️  You (text): {text_input}")
                                response = self.process_input(text_input)
                                print(f"🤖 Assistant: {response}")
                        
                except (EOFError, KeyboardInterrupt):
                    break
                
                # Small delay to prevent high CPU usage
                time.sleep(0.1)
                
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
                    
        finally:
            self.stop()
    
    def run_demo(self):
        """Run a quick demo of capabilities."""
        print("\n🎯 Intel AI Assistant - Demo Mode")
        print("=" * 40)
        
        # Test voice capabilities
        if self.voice_service:
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
            self.speak("Search completed! Check the console for detailed results.")
        
        # Interactive demo
        self.speak("Demo completed! You can now interact with me by speaking or typing.")
        print("\n🎮 Interactive demo starting...")
        self.start_text_only_mode()
    
    def stop(self):
        """Stop the assistant."""
        self.is_running = False
        
        if self.voice_service:
            self.voice_service.stop_continuous_listening()
        
        print("\n👋 Intel AI Assistant stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {
            "running": self.is_running,
            "voice_available": self.voice_service is not None,
            "search_available": self.search_service is not None,
            "conversation_history": len(self.conversation_history),
            "config": self.config
        }

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
            if assistant.voice_service:
                assistant.voice_service.test_voice_system()
            
            if assistant.search_service:
                assistant.search_service.test_search_engines()
                print("\n" + "="*50)
                assistant.search_service.search_live_demo("im alive")
        
        elif args.demo:
            assistant.run_demo()
        
        elif args.text_only:
            assistant.start_text_only_mode()
        
        else:
            # Default: try interactive mode with voice
            if assistant.voice_service:
                assistant.start_interactive_mode()
            else:
                print("🎤 Voice not available, starting text-only mode...")
                assistant.start_text_only_mode()
                
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    finally:
        assistant.stop()

if __name__ == "__main__":
    main()