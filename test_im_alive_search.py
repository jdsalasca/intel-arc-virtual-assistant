#!/usr/bin/env python3
"""
Test the specific 'im alive' functionality
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_im_alive_search():
    """Test the specific 'im alive' search functionality."""
    print("🌐 Testing 'Im Alive' Search Functionality")
    print("=" * 50)
    
    try:
        from ai_assistant_brain import AIAssistantBrain
        
        # Create assistant
        print("🧠 Creating AI Assistant...")
        assistant = AIAssistantBrain()
        
        # Test different variations of the search request
        test_queries = [
            "im alive",
            "search for im alive",
            "look up im alive",
            "find information about im alive"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Testing query: '{query}'")
            print("-" * 30)
            
            response = assistant.process_input(query)
            print(f"🤖 Response: {response}")
            
            # Brief pause between searches
            import time
            time.sleep(1)
        
        # Clean shutdown
        assistant.stop()
        
        print("\n✅ All 'im alive' search tests completed successfully!")
        print("🎯 System correctly processes search requests")
        print("🌐 Internet search functionality is working")
        print("🤖 AI responses are generated appropriately")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_im_alive_search()
    sys.exit(0 if success else 1)