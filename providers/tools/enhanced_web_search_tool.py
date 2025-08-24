"""
Enhanced Web Search Tool Provider
Supports multiple search engines with intelligent result processing and caching.
"""

import os
import logging
import asyncio
import aiohttp
import json
import hashlib
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from dataclasses import dataclass

from core.interfaces.tool_provider import (
    IWebSearchTool, ToolResult, ToolParameter, ToolCategory, ToolAuthType
)

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Structured search result."""
    title: str
    url: str
    snippet: str
    source: str
    timestamp: Optional[datetime] = None
    score: Optional[float] = None

class EnhancedWebSearchTool(IWebSearchTool):
    """Enhanced web search with multiple engines and intelligent processing."""
    
    def __init__(self):
        self.search_engines = {}
        self.cache = {}
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
        
        # Performance stats
        self.stats = {
            "total_searches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_response_time": 0.0
        }
        
        # Initialize search engines
        self._initialize_search_engines()
    
    def _initialize_search_engines(self):
        """Initialize available search engines."""
        # DuckDuckGo (no API key required)
        self.search_engines["duckduckgo"] = {
            "name": "DuckDuckGo",
            "requires_auth": False,
            "rate_limit": 50,  # requests per minute
            "search_func": self._search_duckduckgo
        }
        
        # Bing (requires API key)
        self.search_engines["bing"] = {
            "name": "Bing Web Search",
            "requires_auth": True,
            "api_key_env": "BING_SEARCH_API_KEY",
            "rate_limit": 1000,
            "search_func": self._search_bing
        }
        
        # Google Custom Search (requires API key and search engine ID)
        self.search_engines["google"] = {
            "name": "Google Custom Search",
            "requires_auth": True,
            "api_key_env": "GOOGLE_API_KEY",
            "search_engine_id_env": "GOOGLE_SEARCH_ENGINE_ID", 
            "rate_limit": 100,
            "search_func": self._search_google
        }
        
        # SearXNG (self-hosted or public instances)
        self.search_engines["searxng"] = {
            "name": "SearXNG",
            "requires_auth": False,
            "base_url": os.getenv("SEARXNG_URL", "https://searx.be"),
            "rate_limit": 60,
            "search_func": self._search_searxng
        }
    
    def get_tool_name(self) -> str:
        """Get the name of the tool."""
        return "enhanced_web_search"
    
    def get_tool_description(self) -> str:
        """Get a description of what the tool does."""
        return "Advanced web search with multiple engines, intelligent result processing, and caching"
    
    def get_tool_category(self) -> ToolCategory:
        """Get the category of the tool."""
        return ToolCategory.SEARCH
    
    def get_parameters(self) -> List[ToolParameter]:
        """Get the parameters required by this tool."""
        return [
            ToolParameter(
                name="query",
                type="string",
                description="Search query",
                required=True
            ),
            ToolParameter(
                name="num_results", 
                type="number",
                description="Number of results to return (1-20)",
                default=10
            ),
            ToolParameter(
                name="search_type",
                type="string", 
                description="Type of search",
                default="web",
                options=["web", "news", "images", "videos"]
            ),
            ToolParameter(
                name="engine",
                type="string",
                description="Preferred search engine",
                default="auto",
                options=["auto", "duckduckgo", "bing", "google", "searxng"]
            ),
            ToolParameter(
                name="language",
                type="string",
                description="Language for results",
                default="en"
            ),
            ToolParameter(
                name="region",
                type="string", 
                description="Region for results",
                default="us"
            ),
            ToolParameter(
                name="freshness",
                type="string",
                description="Freshness of results",
                default="any",
                options=["any", "day", "week", "month", "year"]
            )
        ]
    
    def get_auth_type(self) -> ToolAuthType:
        """Get the authentication type required."""
        return ToolAuthType.API_KEY  # Some engines require API keys
    
    def is_available(self) -> bool:
        """Check if the tool is available and configured."""
        # At least DuckDuckGo should always be available
        return True
    
    def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute the web search tool."""
        return asyncio.run(self._execute_async(parameters))
    
    async def _execute_async(self, parameters: Dict[str, Any]) -> ToolResult:
        """Async execution for better performance."""
        try:
            # Validate parameters
            if not self.validate_parameters(parameters):
                return ToolResult(
                    success=False,
                    error="Invalid parameters"
                )
            
            query = parameters["query"]
            num_results = min(parameters.get("num_results", 10), 20)
            search_type = parameters.get("search_type", "web")
            engine = parameters.get("engine", "auto")
            language = parameters.get("language", "en")
            region = parameters.get("region", "us")
            freshness = parameters.get("freshness", "any")
            
            # Check cache first
            cache_key = self._generate_cache_key(parameters)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.stats["cache_hits"] += 1
                return cached_result
            
            self.stats["cache_misses"] += 1
            start_time = time.time()
            
            # Select search engine
            selected_engine = self._select_engine(engine)
            if not selected_engine:
                return ToolResult(
                    success=False,
                    error="No available search engines"
                )
            
            # Perform search
            if search_type == "news":
                results = await self.search_news(query, num_results)
            elif search_type == "images":
                results = await self.search_images(query, num_results)
            else:
                results = await self.search(query, num_results)
            
            # Process and rank results
            processed_results = self._process_results(results.data if results.success else [])
            
            # Create result
            result = ToolResult(
                success=results.success,
                data={
                    "query": query,
                    "results": processed_results,
                    "total_results": len(processed_results),
                    "search_engine": selected_engine["name"],
                    "search_time": time.time() - start_time,
                    "cached": False
                },
                error=results.error if not results.success else None,
                metadata={
                    "search_type": search_type,
                    "engine": selected_engine["name"],
                    "language": language,
                    "region": region
                }
            )
            
            # Cache successful results
            if result.success:
                self._cache_result(cache_key, result)
            
            # Update stats
            self._update_stats(time.time() - start_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}"
            )
    
    def search(self, query: str, num_results: int = 10) -> ToolResult:
        """Search the web for a query."""
        return asyncio.run(self._search_web_async(query, num_results))
    
    async def _search_web_async(self, query: str, num_results: int) -> ToolResult:
        """Async web search."""
        # Select best available engine
        engine = self._select_engine("auto")
        if not engine:
            return ToolResult(success=False, error="No search engines available")
        
        # Execute search
        results = await engine["search_func"](query, num_results, "web")
        return results
    
    def search_news(self, query: str, num_results: int = 10) -> ToolResult:
        """Search for news articles."""
        return asyncio.run(self._search_news_async(query, num_results))
    
    async def _search_news_async(self, query: str, num_results: int) -> ToolResult:
        """Async news search."""
        engine = self._select_engine("auto")
        if not engine:
            return ToolResult(success=False, error="No search engines available")
        
        results = await engine["search_func"](query, num_results, "news")
        return results
    
    def search_images(self, query: str, num_results: int = 10) -> ToolResult:
        """Search for images.""" 
        return asyncio.run(self._search_images_async(query, num_results))
    
    async def _search_images_async(self, query: str, num_results: int) -> ToolResult:
        """Async image search."""
        engine = self._select_engine("auto")
        if not engine:
            return ToolResult(success=False, error="No search engines available")
        
        results = await engine["search_func"](query, num_results, "images")
        return results
    
    def _select_engine(self, preferred: str) -> Optional[Dict[str, Any]]:
        """Select the best available search engine."""
        if preferred != "auto" and preferred in self.search_engines:
            engine = self.search_engines[preferred]
            if self._is_engine_available(preferred, engine):
                return engine
        
        # Auto-select based on availability and preference
        preference_order = ["bing", "google", "duckduckgo", "searxng"]
        
        for engine_name in preference_order:
            if engine_name in self.search_engines:
                engine = self.search_engines[engine_name]
                if self._is_engine_available(engine_name, engine):
                    return engine
        
        return None
    
    def _is_engine_available(self, name: str, engine: Dict[str, Any]) -> bool:
        """Check if a search engine is available."""
        if not engine.get("requires_auth", False):
            return True
        
        # Check for required API keys
        api_key_env = engine.get("api_key_env")
        if api_key_env and os.getenv(api_key_env):
            return True
        
        return False
    
    async def _search_duckduckgo(self, query: str, num_results: int, search_type: str) -> ToolResult:
        """Search using DuckDuckGo Instant Answer API."""
        try:
            if search_type == "news":
                # Use DuckDuckGo news search (via web scraping approach)
                query = f"news {query}"
            
            # DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_redirect": "1",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = self._parse_duckduckgo_results(data, num_results)
                        return ToolResult(success=True, data=results)
                    else:
                        return ToolResult(success=False, error=f"API returned status {response.status}")
                        
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _parse_duckduckgo_results(self, data: Dict[str, Any], num_results: int) -> List[SearchResult]:
        """Parse DuckDuckGo API response."""
        results = []
        
        # Parse instant answer
        if data.get("Abstract"):
            results.append(SearchResult(
                title="Instant Answer",
                url=data.get("AbstractURL", ""),
                snippet=data.get("Abstract", ""),
                source="DuckDuckGo"
            ))
        
        # Parse related topics
        for topic in data.get("RelatedTopics", [])[:num_results]:
            if isinstance(topic, dict) and "Text" in topic:
                results.append(SearchResult(
                    title=topic.get("Text", "").split(" - ")[0],
                    url=topic.get("FirstURL", ""),
                    snippet=topic.get("Text", ""),
                    source="DuckDuckGo"
                ))
        
        return results[:num_results]
    
    async def _search_bing(self, query: str, num_results: int, search_type: str) -> ToolResult:
        """Search using Bing Web Search API."""
        try:
            api_key = os.getenv("BING_SEARCH_API_KEY")
            if not api_key:
                return ToolResult(success=False, error="Bing API key not configured")
            
            # Select endpoint based on search type
            if search_type == "news":
                endpoint = "https://api.bing.microsoft.com/v7.0/news/search"
            elif search_type == "images":
                endpoint = "https://api.bing.microsoft.com/v7.0/images/search"
            else:
                endpoint = "https://api.bing.microsoft.com/v7.0/search"
            
            headers = {"Ocp-Apim-Subscription-Key": api_key}
            params = {
                "q": query,
                "count": num_results,
                "mkt": "en-US",
                "safesearch": "moderate"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = self._parse_bing_results(data, search_type)
                        return ToolResult(success=True, data=results)
                    else:
                        error_text = await response.text()
                        return ToolResult(success=False, error=f"Bing API error: {error_text}")
                        
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _parse_bing_results(self, data: Dict[str, Any], search_type: str) -> List[SearchResult]:
        """Parse Bing API response."""
        results = []
        
        if search_type == "news":
            items = data.get("value", [])
            for item in items:
                results.append(SearchResult(
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source="Bing News",
                    timestamp=item.get("datePublished")
                ))
        elif search_type == "images":
            items = data.get("value", [])
            for item in items:
                results.append(SearchResult(
                    title=item.get("name", ""),
                    url=item.get("contentUrl", ""),
                    snippet=item.get("name", ""),
                    source="Bing Images"
                ))
        else:
            items = data.get("webPages", {}).get("value", [])
            for item in items:
                results.append(SearchResult(
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    source="Bing"
                ))
        
        return results
    
    async def _search_google(self, query: str, num_results: int, search_type: str) -> ToolResult:
        """Search using Google Custom Search API."""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
            
            if not api_key or not search_engine_id:
                return ToolResult(success=False, error="Google API credentials not configured")
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": api_key,
                "cx": search_engine_id,
                "q": query,
                "num": min(num_results, 10)  # Google limits to 10
            }
            
            # Add search type parameters
            if search_type == "images":
                params["searchType"] = "image"
            elif search_type == "news":
                params["tbm"] = "nws"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = self._parse_google_results(data, search_type)
                        return ToolResult(success=True, data=results)
                    else:
                        error_text = await response.text()
                        return ToolResult(success=False, error=f"Google API error: {error_text}")
                        
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _parse_google_results(self, data: Dict[str, Any], search_type: str) -> List[SearchResult]:
        """Parse Google Custom Search API response."""
        results = []
        
        items = data.get("items", [])
        for item in items:
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                source="Google"
            ))
        
        return results
    
    async def _search_searxng(self, query: str, num_results: int, search_type: str) -> ToolResult:
        """Search using SearXNG instance."""
        try:
            base_url = os.getenv("SEARXNG_URL", "https://searx.be")
            url = f"{base_url}/search"
            
            params = {
                "q": query,
                "format": "json",
                "categories": search_type if search_type != "web" else "general"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = self._parse_searxng_results(data, num_results)
                        return ToolResult(success=True, data=results)
                    else:
                        return ToolResult(success=False, error=f"SearXNG error: {response.status}")
                        
        except Exception as e:
            logger.error(f"SearXNG search failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _parse_searxng_results(self, data: Dict[str, Any], num_results: int) -> List[SearchResult]:
        """Parse SearXNG API response."""
        results = []
        
        items = data.get("results", [])
        for item in items[:num_results]:
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                source="SearXNG"
            ))
        
        return results
    
    def _process_results(self, results: List[SearchResult]) -> List[Dict[str, Any]]:
        """Process and enhance search results."""
        processed = []
        
        for result in results:
            processed_result = {
                "title": result.title,
                "url": result.url,
                "snippet": result.snippet,
                "source": result.source,
                "relevance_score": self._calculate_relevance_score(result),
            }
            
            if result.timestamp:
                processed_result["timestamp"] = result.timestamp
            
            processed.append(processed_result)
        
        # Sort by relevance score
        processed.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return processed
    
    def _calculate_relevance_score(self, result: SearchResult) -> float:
        """Calculate relevance score for ranking."""
        score = 0.5  # Base score
        
        # Boost score based on source reliability
        source_scores = {
            "Google": 0.9,
            "Bing": 0.8,
            "DuckDuckGo": 0.7,
            "SearXNG": 0.6
        }
        score *= source_scores.get(result.source, 0.5)
        
        # Boost based on content quality
        if result.snippet and len(result.snippet) > 100:
            score *= 1.1
        
        if result.title and len(result.title) > 20:
            score *= 1.05
        
        return min(score, 1.0)
    
    def _generate_cache_key(self, parameters: Dict[str, Any]) -> str:
        """Generate cache key for parameters."""
        cache_params = {
            "query": parameters.get("query", ""),
            "num_results": parameters.get("num_results", 10),
            "search_type": parameters.get("search_type", "web"),
            "engine": parameters.get("engine", "auto")
        }
        cache_string = json.dumps(cache_params, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[ToolResult]:
        """Get cached result if still valid."""
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                # Update cached flag in result
                cached_data.data["cached"] = True
                return cached_data
            else:
                # Remove expired cache
                del self.cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: ToolResult):
        """Cache a search result."""
        self.cache[cache_key] = (result, datetime.now())
        
        # Clean old cache entries periodically
        if len(self.cache) > 1000:  # Max cache size
            self._clean_cache()
    
    def _clean_cache(self):
        """Clean expired cache entries."""
        now = datetime.now()
        expired_keys = []
        
        for key, (_, timestamp) in self.cache.items():
            if now - timestamp > self.cache_duration:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
    
    def _update_stats(self, response_time: float):
        """Update performance statistics."""
        self.stats["total_searches"] += 1
        
        # Calculate running average
        total = self.stats["total_searches"]
        current_avg = self.stats["average_response_time"]
        self.stats["average_response_time"] = ((current_avg * (total - 1)) + response_time) / total
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters before execution."""
        if "query" not in parameters or not parameters["query"].strip():
            return False
        
        num_results = parameters.get("num_results", 10)
        if not isinstance(num_results, int) or num_results < 1 or num_results > 20:
            return False
        
        search_type = parameters.get("search_type", "web")
        if search_type not in ["web", "news", "images", "videos"]:
            return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance and usage statistics."""
        cache_hit_rate = 0.0
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        if total_requests > 0:
            cache_hit_rate = self.stats["cache_hits"] / total_requests
        
        return {
            "tool_name": self.get_tool_name(),
            "available_engines": list(self.search_engines.keys()),
            "cache_size": len(self.cache),
            "cache_hit_rate": cache_hit_rate,
            "performance": self.stats.copy()
        }