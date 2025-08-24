"""
Enhanced Web Search Service for Intel AI Assistant
Multi-engine web search with DuckDuckGo, Wikipedia, and web scraping.
"""

import requests
import json
import logging
import time
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urljoin
import asyncio
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class SearchResult:
    """Represents a search result."""
    
    def __init__(self, title: str, url: str, snippet: str, source: str):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source
        }

class EnhancedWebSearchService:
    """Enhanced web search service with multiple search engines."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Search engines configuration
        self.search_engines = {
            "duckduckgo": self.search_duckduckgo,
            "wikipedia": self.search_wikipedia,
            "web_scrape": self.search_web_scrape
        }
        
        self.default_engines = ["duckduckgo", "wikipedia"]
        self.max_retries = 3
        self.request_timeout = 10
    
    def search(self, query: str, max_results: int = 5, engines: List[str] = None) -> List[Dict[str, Any]]:
        """Search using multiple engines and return combined results."""
        if engines is None:
            engines = self.default_engines
        
        all_results = []
        
        for engine_name in engines:
            if engine_name in self.search_engines:
                try:
                    print(f"🔍 Searching {engine_name} for: {query}")
                    engine_results = self.search_engines[engine_name](query, max_results)
                    
                    for result in engine_results:
                        result_dict = result.to_dict() if isinstance(result, SearchResult) else result
                        all_results.append(result_dict)
                    
                    time.sleep(0.5)  # Be respectful to APIs
                    
                except Exception as e:
                    logger.error(f"Error searching {engine_name}: {e}")
                    print(f"⚠️  {engine_name} search failed: {e}")
        
        # Remove duplicates and limit results
        unique_results = self.remove_duplicates(all_results)
        return unique_results[:max_results]
    
    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search using DuckDuckGo."""
        try:
            # Try using duckduckgo-search library first
            try:
                from duckduckgo_search import DDGS
                
                results = []
                with DDGS() as ddgs:
                    for result in ddgs.text(query, max_results=max_results):
                        results.append(SearchResult(
                            title=result.get('title', ''),
                            url=result.get('href', ''),
                            snippet=result.get('body', ''),
                            source='duckduckgo'
                        ))
                
                return results
                
            except ImportError:
                # Fallback to direct API approach
                return self.search_duckduckgo_api(query, max_results)
                
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    def search_duckduckgo_api(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search DuckDuckGo using direct API calls."""
        try:
            # Get search token
            token_url = "https://duckduckgo.com/"
            token_response = self.session.get(token_url, timeout=self.request_timeout)
            
            # Extract vqd token from response
            vqd_token = None
            if 'vqd=' in token_response.text:
                start = token_response.text.find('vqd=') + 4
                end = token_response.text.find('&', start)
                if end == -1:
                    end = token_response.text.find('"', start)
                vqd_token = token_response.text[start:end]
            
            if not vqd_token:
                return []
            
            # Perform search
            search_url = "https://links.duckduckgo.com/d.js"
            params = {
                'q': query,
                'vqd': vqd_token,
                'kl': 'us-en',
                'l': 'us-en',
                'p': '1',
                's': '0',
                'df': '',
                'ex': '-1'
            }
            
            response = self.session.get(search_url, params=params, timeout=self.request_timeout)
            
            if response.status_code == 200:
                # Parse response (simplified)
                results = []
                # Note: DuckDuckGo API response format may vary
                # This is a basic implementation
                return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo API search error: {e}")
        
        return []
    
    def search_wikipedia(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """Search Wikipedia."""
        try:
            # Try using wikipedia library first
            try:
                import wikipedia
                
                results = []
                search_results = wikipedia.search(query, results=max_results)
                
                for title in search_results[:max_results]:
                    try:
                        page = wikipedia.page(title)
                        results.append(SearchResult(
                            title=page.title,
                            url=page.url,
                            snippet=page.summary[:300] + "..." if len(page.summary) > 300 else page.summary,
                            source='wikipedia'
                        ))
                    except Exception:
                        continue
                
                return results
                
            except ImportError:
                # Fallback to Wikipedia API
                return self.search_wikipedia_api(query, max_results)
                
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return []
    
    def search_wikipedia_api(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """Search Wikipedia using direct API calls."""
        try:
            # Search for articles
            search_url = "https://en.wikipedia.org/api/rest_v1/page/search"
            params = {
                'q': query,
                'limit': max_results
            }
            
            response = self.session.get(search_url, params=params, timeout=self.request_timeout)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('pages', []):
                    title = item.get('title', '')
                    snippet = item.get('extract', '')
                    page_id = item.get('key', '')
                    
                    url = f"https://en.wikipedia.org/wiki/{quote_plus(title)}"
                    
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source='wikipedia'
                    ))
                
                return results
            
        except Exception as e:
            logger.error(f"Wikipedia API search error: {e}")
        
        return []
    
    def search_web_scrape(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """Search by scraping web search results."""
        try:
            # Use a search engine that allows scraping (be respectful)
            search_url = f"https://html.duckduckgo.com/html/"
            params = {'q': query}
            
            response = self.session.get(search_url, params=params, timeout=self.request_timeout)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                results = []
                
                # Parse search results
                result_links = soup.find_all('a', class_='result__a')
                
                for link in result_links[:max_results]:
                    title = link.get_text().strip()
                    url = link.get('href', '')
                    
                    # Get snippet from nearby elements
                    snippet = ""
                    snippet_elem = link.find_next('a', class_='result__snippet')
                    if snippet_elem:
                        snippet = snippet_elem.get_text().strip()
                    
                    if title and url:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            source='web_scrape'
                        ))
                
                return results
            
        except Exception as e:
            logger.error(f"Web scraping search error: {e}")
        
        return []
    
    def get_page_content(self, url: str) -> Optional[str]:
        """Get the content of a web page."""
        try:
            response = self.session.get(url, timeout=self.request_timeout)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text content
                text = soup.get_text()
                
                # Clean up text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return text[:2000]  # Limit content length
            
        except Exception as e:
            logger.error(f"Error getting page content: {e}")
        
        return None
    
    def remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate search results."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    def search_and_summarize(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """Search and provide a summarized response."""
        results = self.search(query, max_results)
        
        summary = {
            "query": query,
            "total_results": len(results),
            "results": results,
            "summary": self.generate_search_summary(query, results)
        }
        
        return summary
    
    def generate_search_summary(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Generate a summary of search results."""
        if not results:
            return f"No results found for '{query}'"
        
        summary_parts = [f"Found {len(results)} results for '{query}':"]
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            snippet = result.get('snippet', 'No description')[:100]
            source = result.get('source', 'unknown')
            
            summary_parts.append(f"{i}. {title} (from {source})")
            if snippet:
                summary_parts.append(f"   {snippet}...")
        
        return '\n'.join(summary_parts)
    
    def test_search_engines(self):
        """Test all search engines."""
        print("🧪 Testing Web Search Engines")
        print("=" * 40)
        
        test_query = "artificial intelligence"
        
        for engine_name, engine_func in self.search_engines.items():
            print(f"\n🔍 Testing {engine_name}...")
            
            try:
                results = engine_func(test_query, 2)
                
                if results:
                    print(f"✅ {engine_name} working - found {len(results)} results")
                    for i, result in enumerate(results, 1):
                        if isinstance(result, SearchResult):
                            print(f"  {i}. {result.title[:50]}...")
                        else:
                            print(f"  {i}. {result.get('title', 'No title')[:50]}...")
                else:
                    print(f"⚠️  {engine_name} returned no results")
                    
            except Exception as e:
                print(f"❌ {engine_name} failed: {e}")
        
        print("\n✅ Search engine testing completed!")
    
    def search_live_demo(self, query: str = "im alive"):
        """Demonstrate live search with the specified query."""
        print(f"🌐 Live Search Demo: '{query}'")
        print("=" * 50)
        
        try:
            results = self.search(query, max_results=5)
            
            if results:
                print(f"✅ Found {len(results)} results:")
                print()
                
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result.get('title', 'No title')}")
                    print(f"   URL: {result.get('url', 'No URL')}")
                    print(f"   Source: {result.get('source', 'unknown')}")
                    print(f"   Description: {result.get('snippet', 'No description')[:150]}...")
                    print()
                
                # Get summary
                summary = self.generate_search_summary(query, results)
                print("📋 Summary:")
                print(summary)
                
            else:
                print(f"❌ No results found for '{query}'")
                
        except Exception as e:
            print(f"❌ Search demo failed: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Create search service
    search_service = EnhancedWebSearchService()
    
    # Test search engines
    search_service.test_search_engines()
    
    # Live demo with "im alive" query
    print("\n" + "="*60)
    search_service.search_live_demo("im alive")