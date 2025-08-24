"""
Web Search Tool Provider
Provides web search capabilities using multiple search engines.
"""

import logging
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
import json
import time
from bs4 import BeautifulSoup

from core.interfaces.tool_provider import (
    IWebSearchTool, ToolCategory, ToolAuthType, ToolParameter, 
    ToolResult, ParameterType
)
from core.exceptions import ToolExecutionException, ToolAuthenticationException

logger = logging.getLogger(__name__)

class WebSearchTool(IWebSearchTool):
    """Web search tool using multiple search engines."""
    
    def __init__(self):
        self.name = "web_search"
        self.search_engines = {
            "duckduckgo": self._search_duckduckgo,
            "google": self._search_google,
            "bing": self._search_bing
        }
        self.default_engine = "duckduckgo"  # Privacy-focused default
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds
    
    def get_tool_name(self) -> str:
        return self.name
    
    def get_tool_description(self) -> str:
        return "Search the web for information using various search engines"
    
    def get_tool_category(self) -> ToolCategory:
        return ToolCategory.SEARCH
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type=ParameterType.STRING,
                description="Search query",
                required=True,
                min_length=1,
                max_length=500
            ),
            ToolParameter(
                name="num_results",
                type=ParameterType.INTEGER,
                description="Number of results to return",
                required=False,
                default=10,
                min_value=1,
                max_value=50
            ),
            ToolParameter(
                name="engine",
                type=ParameterType.STRING,
                description="Search engine to use",
                required=False,
                default=self.default_engine,
                enum_values=list(self.search_engines.keys())
            ),
            ToolParameter(
                name="safe_search",
                type=ParameterType.BOOLEAN,
                description="Enable safe search filtering",
                required=False,
                default=True
            )
        ]
    
    def get_auth_type(self) -> ToolAuthType:
        return ToolAuthType.NONE  # Most engines don't require auth for basic search
    
    def is_available(self) -> bool:
        """Check if web search is available."""
        try:
            # Test with a simple request
            response = requests.get("https://httpbin.org/status/200", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute web search."""
        try:
            # Rate limiting
            self._enforce_rate_limit()
            
            # Extract parameters
            query = parameters.get("query", "").strip()
            num_results = parameters.get("num_results", 10)
            engine = parameters.get("engine", self.default_engine)
            safe_search = parameters.get("safe_search", True)
            
            if not query:
                raise ToolExecutionException("Search query is required")
            
            # Execute search
            search_func = self.search_engines.get(engine, self.search_engines[self.default_engine])
            results = search_func(query, num_results, safe_search)
            
            return ToolResult(
                request_id="",
                tool_name=self.name,
                status="completed",
                success=True,
                data={
                    "query": query,
                    "engine": engine,
                    "results": results,
                    "total_results": len(results)
                },
                metadata={
                    "search_engine": engine,
                    "safe_search": safe_search,
                    "execution_time": time.time()
                }
            )
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return ToolResult(
                request_id="",
                tool_name=self.name,
                status="failed",
                success=False,
                error=str(e)
            )
    
    def search(self, query: str, num_results: int = 10) -> ToolResult:
        """Search the web for a query."""
        return self.execute({
            "query": query,
            "num_results": num_results,
            "engine": self.default_engine
        })
    
    def search_news(self, query: str, num_results: int = 10) -> ToolResult:
        """Search for news articles."""
        news_query = f"{query} news"
        return self.execute({
            "query": news_query,
            "num_results": num_results,
            "engine": self.default_engine
        })
    
    def search_images(self, query: str, num_results: int = 10) -> ToolResult:
        """Search for images."""
        # For now, return text results about images
        image_query = f"{query} images pictures"
        return self.execute({
            "query": image_query,
            "num_results": num_results,
            "engine": self.default_engine
        })
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate search parameters."""
        try:
            query = parameters.get("query", "")
            if not isinstance(query, str) or len(query.strip()) == 0:
                return False
            
            num_results = parameters.get("num_results", 10)
            if not isinstance(num_results, int) or num_results < 1 or num_results > 50:
                return False
            
            engine = parameters.get("engine", self.default_engine)
            if engine not in self.search_engines:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Parameter validation failed: {e}")
            return False
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _search_duckduckgo(self, query: str, num_results: int, safe_search: bool) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo."""
        try:
            # DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract results from different sections
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", "Abstract"),
                    "url": data.get("AbstractURL", ""),
                    "description": data.get("Abstract", ""),
                    "source": data.get("AbstractSource", "DuckDuckGo")
                })
            
            # Add related topics
            for topic in data.get("RelatedTopics", [])[:num_results-1]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "url": topic.get("FirstURL", ""),
                        "description": topic.get("Text", ""),
                        "source": "DuckDuckGo"
                    })
            
            # If we don't have enough results, try HTML scraping (fallback)
            if len(results) < num_results:
                html_results = self._search_duckduckgo_html(query, num_results - len(results))
                results.extend(html_results)
            
            return results[:num_results]
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    def _search_duckduckgo_html(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Fallback HTML scraping for DuckDuckGo."""
        try:
            url = "https://html.duckduckgo.com/html/"
            params = {"q": query}
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Find search result elements
            for result_div in soup.find_all('div', class_='result')[:num_results]:
                title_elem = result_div.find('a', class_='result__a')
                snippet_elem = result_div.find('a', class_='result__snippet')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    description = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        "title": title,
                        "url": url,
                        "description": description,
                        "source": "DuckDuckGo"
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo HTML search failed: {e}")
            return []
    
    def _search_google(self, query: str, num_results: int, safe_search: bool) -> List[Dict[str, Any]]:
        """Search using Google (requires API key)."""
        try:
            # This would require Google Custom Search API
            # For now, return a placeholder
            return [{
                "title": f"Google search for: {query}",
                "url": f"https://www.google.com/search?q={quote_plus(query)}",
                "description": "Google search requires API key configuration",
                "source": "Google"
            }]
            
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return []
    
    def _search_bing(self, query: str, num_results: int, safe_search: bool) -> List[Dict[str, Any]]:
        """Search using Bing (requires API key)."""
        try:
            # This would require Bing Search API
            # For now, return a placeholder
            return [{
                "title": f"Bing search for: {query}",
                "url": f"https://www.bing.com/search?q={quote_plus(query)}",
                "description": "Bing search requires API key configuration",
                "source": "Bing"
            }]
            
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return []