#!/usr/bin/env python3
"""
Test the 'im alive' internet search functionality as requested
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_im_alive_search():
    """Test the specific 'im alive' search as requested by user"""
    print("🔍 Testing 'im alive' Internet Search")
    print("=" * 40)
    
    try:
        from services.enhanced_web_search import EnhancedWebSearch
        
        search_service = EnhancedWebSearch()
        
        print("Searching for 'im alive'...")
        results = search_service.search("im alive", max_results=5)
        
        if results:
            print(f"✅ Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                url = result.get('url', 'No URL')
                snippet = result.get('snippet', 'No snippet')
                
                print(f"\n{i}. {title}")
                print(f"   URL: {url}")
                if snippet:
                    print(f"   Summary: {snippet[:100]}...")
        else:
            print("❌ No results found")
            
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_search_service():
    """Test the web search service generally"""
    print("\n🌐 Testing Web Search Service")
    print("=" * 40)
    
    try:
        from services.enhanced_web_search import EnhancedWebSearch
        
        search_service = EnhancedWebSearch()
        
        # Test different search engines
        print("1. Testing DuckDuckGo search...")
        ddg_results = search_service.search_duckduckgo("Python programming", max_results=2)
        print(f"   Found {len(ddg_results)} DDG results")
        
        print("2. Testing Wikipedia search...")
        wiki_results = search_service.search_wikipedia("Artificial Intelligence", max_results=2)
        print(f"   Found {len(wiki_results)} Wikipedia results")
        
        print("3. Testing combined search...")
        combined_results = search_service.search("Intel AI technology", max_results=3)
        print(f"   Found {len(combined_results)} combined results")
        
        return True
        
    except Exception as e:
        print(f"❌ Web search service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 Testing Internet Search Capabilities")
    print("Testing as requested: 'request it to go internet and search im alive'")
    print("=" * 60)
    
    # Test 'im alive' search specifically
    alive_success = test_im_alive_search()
    
    # Test general web search
    general_success = test_web_search_service()
    
    print("\n" + "=" * 60)
    print("🎯 SEARCH TEST RESULTS")
    print("=" * 60)
    print(f"'im alive' search:  {'✅ SUCCESS' if alive_success else '❌ FAILED'}")
    print(f"General web search: {'✅ SUCCESS' if general_success else '❌ FAILED'}")
    
    if alive_success and general_success:
        print("\n🚀 Internet search capabilities are working!")
        print("✅ Can search 'im alive' as requested")
        print("✅ Web search service is functional")
    else:
        print("\n⚠️  Some search functionality needs attention")