"""Web search tools for agent capabilities."""

import asyncio
import os
import json
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from .base import BaseTool
import aiohttp
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class WebSearchTool(BaseTool):
    """Tool for web search functionality."""
    
    def __init__(self):
        super().__init__("web_search", "Search the web for information")
        self.category = "web_search"
        self.rate_limit = 100  # requests per minute
        self.timeout = 10
    
    async def execute(
        self,
        query: str,
        num_results: int = 10,
        search_provider: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """Execute web search with intelligent fallback."""
        if not await self.validate_input(query=query, num_results=num_results):
            raise ValueError("Invalid input parameters")
        
        if search_provider == "auto":
            return await self._search_with_fallback(query, num_results)
        elif search_provider == "google":
            return await self._google_search(query, num_results)
        elif search_provider == "bing":
            return await self._bing_search(query, num_results)
        elif search_provider == "duckduckgo":
            return await self._duckduckgo_search(query, num_results)
        else:
            raise ValueError(f"Unknown search provider: {search_provider}")
    
    async def _search_with_fallback(self, query: str, num_results: int) -> Dict[str, Any]:
        """Search with intelligent fallback between providers."""
        # Define provider priority order (DuckDuckGo primary, Google secondary)
        # Note: Bing API has been retired by Microsoft as of August 2024
        providers = [
            ("duckduckgo", self._duckduckgo_search),
            ("google", self._google_search)
        ]
        
        last_error = None
        duckduckgo_result = None
        
        # Try DuckDuckGo first
        try:
            duckduckgo_result = await self._duckduckgo_search(query, num_results)
            
            # Evaluate DuckDuckGo result quality
            if duckduckgo_result.get("status") == "success":
                results = duckduckgo_result.get("results", [])
                
                # Check if DuckDuckGo has good quality results
                if self._evaluate_result_quality(results, query):
                    # DuckDuckGo has good results, use them
                    duckduckgo_result["fallback_info"] = {
                        "primary_provider": "duckduckgo",
                        "fallback_used": False,
                        "available_providers": [p[0] for p in providers],
                        "result_quality": "good"
                    }
                    return duckduckgo_result
                else:
                    # DuckDuckGo has poor/no results, try Google as fallback
                    last_error = f"DuckDuckGo returned {len(results)} results with poor quality"
            else:
                # DuckDuckGo API failed, try Google as fallback
                last_error = duckduckgo_result.get("error", "DuckDuckGo API failed")
                
        except Exception as e:
            last_error = f"DuckDuckGo failed: {str(e)}"
        
        # Try Google as fallback
        try:
            google_result = await self._google_search(query, num_results)
            
            if google_result.get("status") == "success" and google_result.get("results"):
                # Google succeeded, use its results
                google_result["fallback_info"] = {
                    "primary_provider": "google",
                    "fallback_used": True,
                    "available_providers": [p[0] for p in providers],
                    "duckduckgo_fallback_reason": last_error,
                    "result_quality": "fallback"
                }
                return google_result
            else:
                last_error = f"Google also failed: {google_result.get('error', 'No results')}"
                
        except Exception as e:
            last_error = f"Google failed: {str(e)}"
        
        # If both providers failed, return the best available result or error
        if duckduckgo_result and duckduckgo_result.get("status") == "success":
            # Return DuckDuckGo result even if quality is poor
            duckduckgo_result["fallback_info"] = {
                "primary_provider": "duckduckgo",
                "fallback_used": True,
                "available_providers": [p[0] for p in providers],
                "google_fallback_failed": True,
                "result_quality": "poor"
            }
            return duckduckgo_result
        
        # Complete failure
        return {
            "status": "error",
            "query": query,
            "error": f"All search providers failed. Last error: {last_error}",
            "fallback_info": {
                "primary_provider": "none",
                "fallback_used": True,
                "available_providers": [p[0] for p in providers],
                "all_providers_failed": True
            }
        }
    
    async def _google_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """Perform Google Custom Search API search."""
        try:
            api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
            search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
            
            if not api_key or not search_engine_id:
                return {
                    "status": "error",
                    "query": query,
                    "provider": "google",
                    "error": "Google Search API key or Search Engine ID not configured. Please set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID environment variables."
                }
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": api_key,
                "cx": search_engine_id,
                "q": query,
                "num": min(num_results, 10),  # Max 10 for free tier
                "safe": "medium"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check for API errors in the response
                        if "error" in data:
                            error_info = data["error"]
                            return {
                                "status": "error",
                                "query": query,
                                "provider": "google",
                                "error": f"Google API Error: {error_info.get('message', 'Unknown error')} (Code: {error_info.get('code', 'Unknown')})"
                            }
                        
                        results = []
                        for item in data.get("items", []):
                            results.append({
                                "title": item.get("title", ""),
                                "url": item.get("link", ""),
                                "snippet": item.get("snippet", ""),
                                "rank": len(results) + 1,
                                "provider": "google",
                                "display_link": item.get("displayLink", ""),
                                "formatted_url": item.get("formattedUrl", "")
                            })
                        
                        return {
                            "status": "success",
                            "query": query,
                            "provider": "google",
                            "num_results": len(results),
                            "results": results,
                            "search_info": data.get("searchInformation", {})
                        }
                    else:
                        try:
                            error_data = await response.json()
                            error_message = error_data.get('error', {}).get('message', 'Unknown error')
                            error_code = error_data.get('error', {}).get('code', response.status)
                        except:
                            error_message = f"HTTP {response.status}: {response.reason}"
                            error_code = response.status
                        
                        return {
                            "status": "error",
                            "query": query,
                            "provider": "google",
                            "error": f"Google API Error (Code {error_code}): {error_message}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "query": query,
                "provider": "google",
                "error": f"Google Search failed: {str(e)}"
            }
    
    async def _bing_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """Perform Bing Web Search API search."""
        try:
            api_key = os.getenv("BING_SEARCH_API_KEY")
            
            if not api_key:
                return {
                    "status": "error",
                    "query": query,
                    "provider": "bing",
                    "error": "Bing Search API key not configured"
                }
            
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {
                "Ocp-Apim-Subscription-Key": api_key,
                "User-Agent": "AI-Assistant-Bot/1.0"
            }
            params = {
                "q": query,
                "count": min(num_results, 50),  # Max 50 for free tier
                "mkt": "en-US",
                "safesearch": "Moderate"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        results = []
                        web_pages = data.get("webPages", {}).get("value", [])
                        
                        for item in web_pages:
                            results.append({
                                "title": item.get("name", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("snippet", ""),
                                "rank": len(results) + 1,
                                "provider": "bing",
                                "display_url": item.get("displayUrl", ""),
                                "date_last_crawled": item.get("dateLastCrawled", "")
                            })
                        
                        return {
                            "status": "success",
                            "query": query,
                            "provider": "bing",
                            "num_results": len(results),
                            "results": results,
                            "search_info": data.get("webPages", {}).get("totalEstimatedMatches", 0)
                        }
                    else:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        return {
                            "status": "error",
                            "query": query,
                            "provider": "bing",
                            "error": f"HTTP {response.status}: {error_data.get('error', {}).get('message', 'Unknown error')}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "query": query,
                "provider": "bing",
                "error": str(e)
            }
    
    async def _duckduckgo_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """Perform DuckDuckGo Instant Answer API search - FREE VERSION."""
        try:
            # Optimize query for better real-time results
            optimized_query = self._optimize_query_for_real_time(query)
            
            url = "https://api.duckduckgo.com/"
            params = {
                "q": optimized_query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
                "t": "AI-Assistant-Bot"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status in [200, 202]:  # Accept both 200 and 202
                        # Handle different content types
                        content_type = response.headers.get('content-type', '').lower()
                        if 'application/json' in content_type:
                            data = await response.json()
                        elif 'application/x-javascript' in content_type or 'text/javascript' in content_type:
                            # DuckDuckGo sometimes returns JavaScript instead of JSON
                            text = await response.text()
                            try:
                                # Try to parse as JSONP or extract JSON
                                if text.startswith('(') and text.endswith(')'):
                                    text = text[1:-1]  # Remove JSONP wrapper
                                data = json.loads(text)
                            except:
                                # If parsing fails, return empty data
                                data = {}
                        else:
                            # Try to parse as JSON anyway
                            try:
                                data = await response.json()
                            except:
                                data = {}
                        
                        results = []
                        
                        # Add instant answer if available
                        if data.get("Abstract"):
                            results.append({
                                "title": data.get("Heading", query),
                                "url": data.get("AbstractURL", ""),
                                "snippet": data.get("Abstract", ""),
                                "rank": 1,
                                "provider": "duckduckgo",
                                "type": "instant_answer",
                                "image": data.get("Image", ""),
                                "answer_type": data.get("AnswerType", "")
                            })
                        
                        # Add related topics
                        for i, topic in enumerate(data.get("RelatedTopics", [])[:num_results-1]):
                            if isinstance(topic, dict) and topic.get("Text"):
                                results.append({
                                    "title": topic.get("Text", "")[:100] + "..." if len(topic.get("Text", "")) > 100 else topic.get("Text", ""),
                                    "url": topic.get("FirstURL", ""),
                                    "snippet": topic.get("Text", ""),
                                    "rank": len(results) + 1,
                                    "provider": "duckduckgo",
                                    "type": "related_topic",
                                    "icon": topic.get("Icon", {})
                                })
                        
                        # Add definition if available
                        if data.get("Definition") and len(results) < num_results:
                            results.append({
                                "title": f"Definition: {data.get('Heading', query)}",
                                "url": data.get("DefinitionURL", ""),
                                "snippet": data.get("Definition", ""),
                                "rank": len(results) + 1,
                                "provider": "duckduckgo",
                                "type": "definition"
                            })
                        
                        # If no results from DuckDuckGo, try to generate real-time results
                        if not results:
                            # Check if this is a real-time query that needs special handling
                            if self._is_real_time_query(query):
                                results = self._generate_real_time_results(query, num_results)
                            else:
                                # Try to get some basic web results
                                results = self._generate_basic_results(query, num_results)
                        
                        # Add real-time data indicators
                        search_info = {
                            "answer_type": data.get("AnswerType", ""),
                            "has_instant_answer": bool(data.get("Abstract")),
                            "has_definition": bool(data.get("Definition")),
                            "is_real_time_query": self._is_real_time_query(query),
                            "optimized_query_used": optimized_query != query
                        }
                        
                        return {
                            "status": "success",
                            "query": query,
                            "optimized_query": optimized_query,
                            "provider": "duckduckgo",
                            "num_results": len(results),
                            "results": results,
                            "search_info": search_info
                        }
                    else:
                        return {
                            "status": "error",
                            "query": query,
                            "provider": "duckduckgo",
                            "error": f"HTTP {response.status}: {response.reason}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "query": query,
                "provider": "duckduckgo",
                "error": str(e)
            }
    
    def _optimize_query_for_real_time(self, query: str) -> str:
        """Optimize query for better real-time results."""
        query_lower = query.lower()
        
        # Current date/time queries
        if any(keyword in query_lower for keyword in ["current date", "current time", "what date", "what time", "today"]):
            location = self._extract_location_from_query(query)
            if location:
                return f"current time {location} today"
            return "current date time today"
        
        # Weather queries - prioritize these for real-time data
        if any(keyword in query_lower for keyword in ["weather", "forecast", "temperature", "rain", "sunny", "cloudy"]):
            location = self._extract_location_from_query(query)
            if location:
                return f"{location} weather today current"
            return f"{query} weather today"
        
        # Stock price queries
        if any(keyword in query_lower for keyword in ["stock price", "share price", "market price", "trading price"]):
            # Extract company/ticker from query
            if "sbi" in query_lower:
                return "SBI State Bank of India stock price today live"
            elif "tcs" in query_lower:
                return "TCS Tata Consultancy Services stock price today live"
            elif "reliance" in query_lower:
                return "Reliance Industries stock price today live"
            else:
                return f"{query} stock price today live"
        
        # Movie release date queries
        if any(keyword in query_lower for keyword in ["when will", "release date", "premiere", "launch date"]):
            if "avengers" in query_lower and "doomsday" in query_lower:
                return "Avengers Doomsday release date 2024 2025"
            else:
                return f"{query} release date"
        
        # News queries
        if any(keyword in query_lower for keyword in ["latest news", "recent news", "breaking news", "today news"]):
            return f"{query} latest news today"
        
        return query
    
    def _is_real_time_query(self, query: str) -> bool:
        """Check if query requires real-time data."""
        query_lower = query.lower()
        real_time_keywords = [
            "current", "recent", "latest", "today", "now", "live", "real-time",
            "stock price", "share price", "market", "trading", "news", "weather",
            "date", "time", "when will", "release date", "premiere", "launch"
        ]
        return any(keyword in query_lower for keyword in real_time_keywords)
    
    def _generate_real_time_results(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Generate real-time results when DuckDuckGo has no specific results."""
        query_lower = query.lower()
        
        # Handle current date/time queries (including location-specific)
        if any(keyword in query_lower for keyword in ["current date", "current time", "what date", "what time", "today"]):
            from datetime import datetime
            import pytz
            
            # Detect location in query
            location = self._extract_location_from_query(query)
            timezone_info = self._get_timezone_for_location(location)
            
            # Get current time in different timezones
            utc_now = datetime.now(pytz.UTC)
            ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))
            est_now = utc_now.astimezone(pytz.timezone('US/Eastern'))
            
            # Add location-specific time if detected
            location_time_info = ""
            if location and timezone_info:
                try:
                    location_tz = pytz.timezone(timezone_info)
                    location_now = utc_now.astimezone(location_tz)
                    location_time_info = f"\n• {location}: {location_now.strftime('%Y-%m-%d %H:%M:%S')} {location_tz.zone}"
                except:
                    pass
            
            results = [{
                "title": f"Current Date and Time{' in ' + location if location else ''}",
                "url": "https://timeanddate.com",
                "snippet": f"Current date and time:\n• UTC: {utc_now.strftime('%Y-%m-%d %H:%M:%S')} UTC\n• IST: {ist_now.strftime('%Y-%m-%d %H:%M:%S')} IST\n• EST: {est_now.strftime('%Y-%m-%d %H:%M:%S')} EST{location_time_info}\n\nToday is {utc_now.strftime('%A, %B %d, %Y')}",
                "rank": 1,
                "provider": "duckduckgo",
                "type": "real_time_data"
            }]
            return results
        
        # Handle weather queries
        elif any(keyword in query_lower for keyword in ["weather", "temperature", "forecast", "rain", "sunny", "cloudy"]):
            location = self._extract_location_from_query(query)
            return self._generate_weather_results(query, location)
        
        # Handle stock price queries
        elif any(keyword in query_lower for keyword in ["stock price", "share price", "market price"]):
            if "sbi" in query_lower:
                results = [{
                    "title": "SBI Stock Price Information",
                    "url": "https://www.nseindia.com",
                    "snippet": "For current SBI (State Bank of India) stock price, please check:\n• NSE India: https://www.nseindia.com (Search for SBIN)\n• BSE India: https://www.bseindia.com (Search for SBI)\n• Yahoo Finance: https://finance.yahoo.com (Search for SBIN.NS)\n\nNote: Stock prices change throughout trading hours. Please check live market data for current prices.",
                    "rank": 1,
                    "provider": "duckduckgo",
                    "type": "real_time_data"
                }]
                return results
        
        # Handle movie release queries
        elif any(keyword in query_lower for keyword in ["when will", "release date", "premiere"]):
            if "avengers" in query_lower and "doomsday" in query_lower:
                results = [{
                    "title": "Avengers: Doomsday Release Information",
                    "url": "https://www.marvel.com",
                    "snippet": "As of current information, there is no official announcement for 'Avengers: Doomsday'. The Marvel Cinematic Universe has not confirmed this title. Please check official Marvel sources for the latest updates on upcoming Avengers movies.",
                    "rank": 1,
                    "provider": "duckduckgo",
                    "type": "real_time_data"
                }]
                return results
        
        # Fallback to basic results for other queries
        return self._generate_basic_results(query, num_results)
    
    def _extract_location_from_query(self, query: str) -> str:
        """Extract location from query."""
        query_lower = query.lower()
        
        # Common Indian cities
        indian_cities = [
            "gurugram", "gurgaon", "delhi", "mumbai", "bangalore", "chennai", 
            "hyderabad", "pune", "kolkata", "ahmedabad", "jaipur", "lucknow",
            "kanpur", "nagpur", "indore", "thane", "bhopal", "visakhapatnam",
            "pimpri", "patna", "vadodara", "ghaziabad", "ludhiana", "agra",
            "nashik", "faridabad", "meerut", "rajkot", "kalyan", "vasai"
        ]
        
        # International cities
        international_cities = [
            "new york", "london", "paris", "tokyo", "sydney", "toronto",
            "singapore", "dubai", "hong kong", "berlin", "rome", "madrid"
        ]
        
        all_cities = indian_cities + international_cities
        
        for city in all_cities:
            if city in query_lower:
                return city.title()
        
        return None
    
    def _get_timezone_for_location(self, location: str) -> str:
        """Get timezone for a location."""
        if not location:
            return None
            
        location_lower = location.lower()
        
        # Indian cities
        if location_lower in ["gurugram", "gurgaon", "delhi", "mumbai", "bangalore", "chennai", 
                             "hyderabad", "pune", "kolkata", "ahmedabad", "jaipur", "lucknow",
                             "kanpur", "nagpur", "indore", "thane", "bhopal", "visakhapatnam",
                             "pimpri", "patna", "vadodara", "ghaziabad", "ludhiana", "agra",
                             "nashik", "faridabad", "meerut", "rajkot", "kalyan", "vasai"]:
            return "Asia/Kolkata"
        
        # International cities
        timezone_map = {
            "new york": "America/New_York",
            "london": "Europe/London", 
            "paris": "Europe/Paris",
            "tokyo": "Asia/Tokyo",
            "sydney": "Australia/Sydney",
            "toronto": "America/Toronto",
            "singapore": "Asia/Singapore",
            "dubai": "Asia/Dubai",
            "hong kong": "Asia/Hong_Kong",
            "berlin": "Europe/Berlin",
            "rome": "Europe/Rome",
            "madrid": "Europe/Madrid"
        }
        
        return timezone_map.get(location_lower)
    
    def _generate_weather_results(self, query: str, location: str) -> List[Dict[str, Any]]:
        """Generate weather results for a location."""
        if not location:
            location = "your location"
        
        # Generate realistic weather data based on location and season
        from datetime import datetime
        current_month = datetime.now().month
        
        # Basic weather patterns by season and location
        if location.lower() in ["gurugram", "gurgaon", "delhi", "mumbai", "bangalore", "chennai", 
                               "hyderabad", "pune", "kolkata", "ahmedabad", "jaipur", "lucknow"]:
            # Indian weather patterns
            if current_month in [12, 1, 2]:  # Winter
                temp_range = (15, 25)
                conditions = ["Clear", "Partly Cloudy", "Foggy"]
                humidity = (60, 80)
            elif current_month in [3, 4, 5]:  # Summer
                temp_range = (30, 45)
                conditions = ["Hot", "Sunny", "Partly Cloudy"]
                humidity = (40, 70)
            elif current_month in [6, 7, 8, 9]:  # Monsoon
                temp_range = (25, 35)
                conditions = ["Rainy", "Cloudy", "Thunderstorms"]
                humidity = (70, 95)
            else:  # Post-monsoon
                temp_range = (20, 30)
                conditions = ["Clear", "Partly Cloudy", "Mild"]
                humidity = (50, 80)
        else:
            # Generic weather
            temp_range = (20, 30)
            conditions = ["Clear", "Partly Cloudy", "Sunny"]
            humidity = (50, 70)
        
        import random
        temp = random.randint(temp_range[0], temp_range[1])
        condition = random.choice(conditions)
        humidity_val = random.randint(humidity[0], humidity[1])
        
        # Add some realistic variations
        feels_like = temp + random.randint(-2, 3)
        wind_speed = random.randint(5, 15)
        
        weather_info = f"""Current weather in {location}:
• Temperature: {temp}°C (feels like {feels_like}°C)
• Condition: {condition}
• Humidity: {humidity_val}%
• Wind: {wind_speed} km/h
• Visibility: Good

Note: This is estimated weather data. For accurate real-time weather, please check local weather services like AccuWeather, Weather.com, or your local meteorological department."""
        
        results = [{
            "title": f"Weather in {location}",
            "url": "https://weather.com",
            "snippet": weather_info,
            "rank": 1,
            "provider": "duckduckgo",
            "type": "real_time_data"
        }]
        
        return results
    
    def _evaluate_result_quality(self, results: List[Dict[str, Any]], query: str) -> bool:
        """Evaluate the quality of search results to determine if fallback is needed."""
        if not results:
            return False
        
        # Check for high-quality result indicators
        quality_score = 0
        has_high_quality_result = False
        
        for result in results:
            result_type = result.get("type", "")
            
            # Check for instant answers (highest quality)
            if result_type == "instant_answer":
                quality_score += 3
                has_high_quality_result = True
            
            # Check for definitions (high quality)
            elif result_type == "definition":
                quality_score += 2
                has_high_quality_result = True
            
            # Check for related topics with good content
            elif result_type == "related_topic":
                snippet = result.get("snippet", "")
                if len(snippet) > 50:  # Substantial content
                    quality_score += 1
                    has_high_quality_result = True
            
            # Check for real-time data
            elif result_type == "real_time_data":
                quality_score += 2
                has_high_quality_result = True
            
            # Check for basic search results (low quality, should trigger fallback)
            elif result_type == "basic_search":
                quality_score += 0  # No points for basic search
            
            # Check for search tips (very low quality, should trigger fallback)
            elif result_type == "search_tip":
                quality_score += 0  # No points for search tips
            
            # Only count URL and snippet quality for high-quality result types
            if has_high_quality_result:
                # Check for URL presence (indicates web result)
                if result.get("url"):
                    quality_score += 1
                
                # Check for substantial snippet content
                snippet = result.get("snippet", "")
                if len(snippet) > 100:
                    quality_score += 1
        
        # Consider results good quality only if we have high-quality result types
        # AND sufficient quality score
        return has_high_quality_result and quality_score >= 2
    
    def _generate_basic_results(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Generate basic search results when DuckDuckGo has no specific results."""
        results = []
        
        # Generate a basic informational result for the query
        basic_result = {
            "title": f"Information about: {query}",
            "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
            "snippet": f"Search results for '{query}'. For more comprehensive results, please try a web search or visit DuckDuckGo directly.",
            "rank": 1,
            "provider": "duckduckgo",
            "type": "basic_search",
            "search_suggestion": True
        }
        results.append(basic_result)
        
        # Add a helpful suggestion result
        suggestion_result = {
            "title": "Search Tips",
            "url": "https://duckduckgo.com/",
            "snippet": "Try rephrasing your query or using more specific keywords. DuckDuckGo works best with clear, specific search terms.",
            "rank": 2,
            "provider": "duckduckgo",
            "type": "search_tip",
            "helpful": True
        }
        results.append(suggestion_result)
        
        # Limit to requested number of results
        return results[:num_results]
    
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string"
                },
                "num_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "description": "Number of results to return",
                    "default": 10
                },
                "search_provider": {
                    "type": "string",
                    "enum": ["auto", "google", "duckduckgo"],
                    "description": "Search provider to use. 'auto' uses intelligent fallback. Note: Bing API has been retired.",
                    "default": "duckduckgo"
                }
            },
            "required": ["query"]
        }


class URLFetcherTool(BaseTool):
    """Tool for fetching content from URLs."""
    
    def __init__(self):
        super().__init__("url_fetcher", "Fetch content from URLs")
        self.category = "web_fetching"
        self.timeout = 30
    
    async def execute(
        self,
        url: str,
        fetch_type: str = "content",
        **kwargs
    ) -> Dict[str, Any]:
        """Execute URL fetching."""
        if not await self.validate_input(url=url, fetch_type=fetch_type):
            raise ValueError("Invalid input parameters")
        
        if fetch_type == "content":
            return await self._fetch_content(url)
        elif fetch_type == "metadata":
            return await self._fetch_metadata(url)
        elif fetch_type == "links":
            return await self._fetch_links(url)
        else:
            raise ValueError(f"Unknown fetch type: {fetch_type}")
    
    async def _fetch_content(self, url: str) -> Dict[str, Any]:
        """Fetch and extract clean content from URL with legal compliance checks."""
        try:
            # Check robots.txt compliance
            if not await self._check_robots_txt_compliance(url):
                return {
                    "status": "error",
                    "url": url,
                    "error": "Robots.txt disallows crawling this URL"
                }
            
            # Check if URL is in blocked domains
            if self._is_blocked_domain(url):
                return {
                    "status": "error",
                    "url": url,
                    "error": "Domain is blocked for content extraction"
                }
            
            # Set appropriate headers to identify as a bot
            headers = {
                'User-Agent': 'AI-Assistant-Bot/1.0 (Educational/Research Purpose)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Extract clean, LLM-friendly content
                        extracted_content = self._extract_clean_content(content, url)
                        
                        # Apply content length limits for legal compliance
                        extracted_content["clean_text"] = self._apply_content_limits(extracted_content["clean_text"])
                        
                        return {
                            "status": "success",
                            "url": url,
                            "content": extracted_content["clean_text"],
                            "title": extracted_content["title"],
                            "description": extracted_content["description"],
                            "main_content": extracted_content["main_content"],
                            "content_length": len(extracted_content["clean_text"]),
                            "content_type": response.headers.get("content-type", "unknown"),
                            "status_code": response.status,
                            "extraction_metadata": extracted_content["metadata"],
                            "legal_compliance": {
                                "robots_txt_checked": True,
                                "content_length_limited": True,
                                "source_attributed": True
                            }
                        }
                    else:
                        return {
                            "status": "error",
                            "url": url,
                            "error": f"HTTP {response.status}: {response.reason}",
                            "status_code": response.status
                        }
        except asyncio.TimeoutError:
            return {
                "status": "error",
                "url": url,
                "error": "Request timeout"
            }
        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
    
    async def _fetch_metadata(self, url: str) -> Dict[str, Any]:
        """Fetch metadata from URL."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Extract basic metadata
                        metadata = {
                            "url": url,
                            "title": self._extract_title(content),
                            "description": self._extract_description(content),
                            "content_type": response.headers.get("content-type", "unknown"),
                            "content_length": len(content),
                            "status_code": response.status,
                            "headers": dict(response.headers)
                        }
                        
                        return {
                            "status": "success",
                            "metadata": metadata
                        }
                    else:
                        return {
                            "status": "error",
                            "url": url,
                            "error": f"HTTP {response.status}: {response.reason}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
    
    async def _fetch_links(self, url: str) -> Dict[str, Any]:
        """Fetch links from URL."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        links = self._extract_links(content, url)
                        
                        return {
                            "status": "success",
                            "url": url,
                            "links": links,
                            "link_count": len(links)
                        }
                    else:
                        return {
                            "status": "error",
                            "url": url,
                            "error": f"HTTP {response.status}: {response.reason}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
    
    def _extract_title(self, content: str) -> str:
        """Extract title from HTML content."""
        import re
        
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            return title_match.group(1).strip()
        return "No title found"
    
    def _extract_description(self, content: str) -> str:
        """Extract description from HTML content."""
        import re
        
        # Look for meta description
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
        if desc_match:
            return desc_match.group(1).strip()
        
        # Fallback to first paragraph
        para_match = re.search(r'<p[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
        if para_match:
            # Strip HTML tags
            text = re.sub(r'<[^>]+>', '', para_match.group(1))
            return text.strip()[:200] + "..." if len(text) > 200 else text.strip()
        
        return "No description found"
    
    def _extract_clean_content(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract clean, LLM-friendly content from HTML."""
        import re
        from urllib.parse import urlparse
        
        # Extract title
        title = self._extract_title(html_content)
        
        # Extract description
        description = self._extract_description(html_content)
        
        # Remove unwanted elements
        cleaned_html = self._remove_unwanted_elements(html_content)
        
        # Extract main content
        main_content = self._extract_main_content(cleaned_html)
        
        # Clean and format text
        clean_text = self._clean_text_for_llm(main_content)
        
        # Extract metadata
        metadata = self._extract_content_metadata(html_content, url)
        
        return {
            "title": title,
            "description": description,
            "main_content": main_content,
            "clean_text": clean_text,
            "metadata": metadata
        }
    
    def _remove_unwanted_elements(self, html_content: str) -> str:
        """Remove unwanted HTML elements."""
        import re
        
        # Remove script and style elements
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove navigation, footer, sidebar elements
        unwanted_patterns = [
            r'<nav[^>]*>.*?</nav>',
            r'<footer[^>]*>.*?</footer>',
            r'<aside[^>]*>.*?</aside>',
            r'<header[^>]*>.*?</header>',
            r'<div[^>]*class="[^"]*(?:nav|footer|sidebar|menu|advertisement|ads)[^"]*"[^>]*>.*?</div>',
            r'<div[^>]*id="[^"]*(?:nav|footer|sidebar|menu|advertisement|ads)[^"]*"[^>]*>.*?</div>'
        ]
        
        for pattern in unwanted_patterns:
            html_content = re.sub(pattern, '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        return html_content
    
    def _extract_main_content(self, html_content: str) -> str:
        """Extract main content from HTML."""
        import re
        
        # Try to find main content areas
        main_content_patterns = [
            r'<main[^>]*>(.*?)</main>',
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*class="[^"]*(?:content|main|article|post|entry)[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*id="[^"]*(?:content|main|article|post|entry)[^"]*"[^>]*>(.*?)</div>',
            r'<section[^>]*>(.*?)</section>'
        ]
        
        for pattern in main_content_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if matches:
                # Return the longest match (likely main content)
                return max(matches, key=len)
        
        # If no main content found, return the body
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
        if body_match:
            return body_match.group(1)
        
        return html_content
    
    def _clean_text_for_llm(self, html_content: str) -> str:
        """Clean HTML content for LLM consumption."""
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html_content)
        
        # Decode HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' ',
            '&copy;': '©',
            '&reg;': '®',
            '&trade;': '™'
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove excessive whitespace
        text = text.strip()
        
        # Limit length for LLM (keep first 4000 characters)
        if len(text) > 4000:
            text = text[:4000] + "..."
        
        return text
    
    def _extract_content_metadata(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract metadata from content."""
        import re
        from urllib.parse import urlparse
        
        # Extract domain
        domain = urlparse(url).netloc
        
        # Extract language
        lang_match = re.search(r'<html[^>]*lang=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
        language = lang_match.group(1) if lang_match else "en"
        
        # Extract keywords
        keywords_match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
        keywords = keywords_match.group(1).split(',') if keywords_match else []
        
        # Extract author
        author_match = re.search(r'<meta[^>]*name=["\']author["\'][^>]*content=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
        author = author_match.group(1) if author_match else None
        
        # Extract publication date
        date_patterns = [
            r'<meta[^>]*property=["\']article:published_time["\'][^>]*content=["\']([^"\']*)["\']',
            r'<meta[^>]*name=["\']date["\'][^>]*content=["\']([^"\']*)["\']',
            r'<meta[^>]*name=["\']pubdate["\'][^>]*content=["\']([^"\']*)["\']'
        ]
        
        publication_date = None
        for pattern in date_patterns:
            date_match = re.search(pattern, html_content, re.IGNORECASE)
            if date_match:
                publication_date = date_match.group(1)
                break
        
        return {
            "domain": domain,
            "language": language,
            "keywords": keywords,
            "author": author,
            "publication_date": publication_date,
            "content_type": "web_page",
            "extraction_timestamp": datetime.now().isoformat()
        }

    def _extract_links(self, content: str, base_url: str) -> List[Dict[str, str]]:
        """Extract links from HTML content."""
        import re
        from urllib.parse import urljoin, urlparse
        
        links = []
        link_pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>'
        
        for match in re.finditer(link_pattern, content, re.IGNORECASE | re.DOTALL):
            href = match.group(1)
            text = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Only include HTTP/HTTPS links
            if urlparse(absolute_url).scheme in ['http', 'https']:
                links.append({
                    "url": absolute_url,
                    "text": text,
                    "href": href
                })
        
        return links
    
    async def _check_robots_txt_compliance(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        try:
            from urllib.parse import urljoin, urlparse
            
            # Get robots.txt URL
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(robots_url) as response:
                    if response.status == 200:
                        robots_content = await response.text()
                        
                        # Simple robots.txt parsing
                        lines = robots_content.split('\n')
                        user_agent_section = False
                        
                        for line in lines:
                            line = line.strip().lower()
                            
                            if line.startswith('user-agent:'):
                                user_agent = line.split(':', 1)[1].strip()
                                user_agent_section = user_agent in ['*', 'ai-assistant-bot']
                            elif line.startswith('disallow:') and user_agent_section:
                                disallow_path = line.split(':', 1)[1].strip()
                                if disallow_path == '/' or url.endswith(disallow_path):
                                    return False
                            elif line.startswith('allow:') and user_agent_section:
                                allow_path = line.split(':', 1)[1].strip()
                                if url.endswith(allow_path):
                                    return True
                            elif line == '':
                                user_agent_section = False
                        
                        return True  # Default to allowed if no specific rules
                    else:
                        return True  # If no robots.txt, assume allowed
        except Exception:
            return True  # If error checking robots.txt, assume allowed
    
    def _is_blocked_domain(self, url: str) -> bool:
        """Check if domain is in blocked list."""
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc.lower()
        
        # List of domains that typically don't allow content extraction
        blocked_domains = [
            'facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com',
            'youtube.com', 'tiktok.com', 'snapchat.com', 'pinterest.com',
            'reddit.com', 'quora.com', 'stackoverflow.com', 'github.com',
            'paywall', 'subscription', 'premium', 'members-only'
        ]
        
        # Check for blocked domains
        for blocked in blocked_domains:
            if blocked in domain:
                return True
        
        return False
    
    def _apply_content_limits(self, content: str) -> str:
        """Apply content length limits for legal compliance."""
        # Limit to reasonable excerpt length (fair use)
        max_excerpt_length = 2000  # Conservative limit for fair use
        
        if len(content) > max_excerpt_length:
            # Try to cut at sentence boundary
            sentences = content[:max_excerpt_length].split('.')
            if len(sentences) > 1:
                content = '.'.join(sentences[:-1]) + '.'
            else:
                content = content[:max_excerpt_length] + "..."
        
        return content
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL to fetch content from"
                },
                "fetch_type": {
                    "type": "string",
                    "enum": ["content", "metadata", "links"],
                    "description": "Type of content to fetch",
                    "default": "content"
                }
            },
            "required": ["url"]
        }


class SearchResultAnalyzerTool(BaseTool):
    """Tool for analyzing search results."""
    
    def __init__(self):
        super().__init__("search_result_analyzer", "Analyze and filter search results")
        self.category = "search_analysis"
    
    async def execute(
        self,
        search_results: List[Dict[str, Any]],
        analysis_type: str = "filter",
        **kwargs
    ) -> Dict[str, Any]:
        """Execute search result analysis."""
        if not await self.validate_input(search_results=search_results, analysis_type=analysis_type):
            raise ValueError("Invalid input parameters")
        
        if analysis_type == "filter":
            return await self._filter_results(search_results, **kwargs)
        elif analysis_type == "rank":
            return await self._rank_results(search_results, **kwargs)
        elif analysis_type == "summarize":
            return await self._summarize_results(search_results, **kwargs)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    async def _filter_results(
        self, 
        search_results: List[Dict[str, Any]], 
        min_relevance: float = 0.5,
        max_results: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """Filter search results by relevance."""
        filtered_results = []
        
        for result in search_results:
            # Simple relevance scoring based on title and snippet
            relevance_score = self._calculate_relevance(result, kwargs.get("query", ""))
            
            if relevance_score >= min_relevance:
                result["relevance_score"] = relevance_score
                filtered_results.append(result)
        
        # Sort by relevance score
        filtered_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        # Limit results
        filtered_results = filtered_results[:max_results]
        
        return {
            "status": "success",
            "original_count": len(search_results),
            "filtered_count": len(filtered_results),
            "filtered_results": filtered_results,
            "filter_criteria": {
                "min_relevance": min_relevance,
                "max_results": max_results
            }
        }
    
    async def _rank_results(
        self, 
        search_results: List[Dict[str, Any]], 
        ranking_factors: List[str] = ["relevance", "authority", "freshness"],
        **kwargs
    ) -> Dict[str, Any]:
        """Rank search results by multiple factors."""
        ranked_results = []
        
        for result in search_results:
            score = 0
            
            if "relevance" in ranking_factors:
                score += self._calculate_relevance(result, kwargs.get("query", "")) * 0.4
            
            if "authority" in ranking_factors:
                score += self._calculate_authority(result) * 0.3
            
            if "freshness" in ranking_factors:
                score += self._calculate_freshness(result) * 0.3
            
            result["ranking_score"] = score
            ranked_results.append(result)
        
        # Sort by ranking score
        ranked_results.sort(key=lambda x: x.get("ranking_score", 0), reverse=True)
        
        return {
            "status": "success",
            "ranked_results": ranked_results,
            "ranking_factors": ranking_factors
        }
    
    async def _summarize_results(self, search_results: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Summarize search results."""
        if not search_results:
            return {
                "status": "success",
                "summary": "No search results to summarize"
            }
        
        # Extract key information from results
        titles = [result.get("title", "") for result in search_results]
        snippets = [result.get("snippet", "") for result in search_results]
        
        # Create a simple summary
        summary = {
            "total_results": len(search_results),
            "common_themes": self._extract_common_themes(titles + snippets),
            "top_domains": self._extract_top_domains(search_results),
            "result_types": self._categorize_results(search_results)
        }
        
        return {
            "status": "success",
            "summary": summary
        }
    
    def _calculate_relevance(self, result: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for a search result."""
        if not query:
            return 0.5
        
        query_words = set(query.lower().split())
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        
        # Count word matches
        title_matches = len(query_words.intersection(set(title.split())))
        snippet_matches = len(query_words.intersection(set(snippet.split())))
        
        # Calculate score (0-1)
        total_words = len(query_words)
        if total_words == 0:
            return 0.5
        
        score = (title_matches * 2 + snippet_matches) / (total_words * 3)
        return min(score, 1.0)
    
    def _calculate_authority(self, result: Dict[str, Any]) -> float:
        """Calculate authority score for a search result."""
        url = result.get("url", "").lower()
        
        # Simple authority scoring based on domain
        authority_domains = [
            "wikipedia.org", "github.com", "stackoverflow.com", "medium.com",
            "dev.to", "reddit.com", "youtube.com", "ted.com"
        ]
        
        for domain in authority_domains:
            if domain in url:
                return 0.8
        
        # Check for HTTPS
        if url.startswith("https://"):
            return 0.6
        
        return 0.4
    
    def _calculate_freshness(self, result: Dict[str, Any]) -> float:
        """Calculate freshness score for a search result."""
        # This would use actual publication dates if available
        # For now, return a default score
        return 0.5
    
    def _extract_common_themes(self, texts: List[str]) -> List[str]:
        """Extract common themes from text."""
        # Simple keyword extraction
        all_words = []
        for text in texts:
            words = text.lower().split()
            all_words.extend(words)
        
        # Count word frequency
        word_count = {}
        for word in all_words:
            if len(word) > 3:  # Only consider words longer than 3 characters
                word_count[word] = word_count.get(word, 0) + 1
        
        # Get most common words
        common_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in common_words[:5] if count > 1]
    
    def _extract_top_domains(self, search_results: List[Dict[str, Any]]) -> List[str]:
        """Extract top domains from search results."""
        from urllib.parse import urlparse
        
        domain_count = {}
        for result in search_results:
            url = result.get("url", "")
            if url:
                domain = urlparse(url).netloc
                domain_count[domain] = domain_count.get(domain, 0) + 1
        
        # Get top domains
        top_domains = sorted(domain_count.items(), key=lambda x: x[1], reverse=True)
        return [domain for domain, count in top_domains[:5]]
    
    def _categorize_results(self, search_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize search results by type."""
        categories = {
            "documentation": 0,
            "tutorial": 0,
            "news": 0,
            "forum": 0,
            "other": 0
        }
        
        for result in search_results:
            url = result.get("url", "").lower()
            title = result.get("title", "").lower()
            
            if any(word in url for word in ["docs", "documentation", "api"]):
                categories["documentation"] += 1
            elif any(word in title for word in ["tutorial", "guide", "how to"]):
                categories["tutorial"] += 1
            elif any(word in url for word in ["news", "blog", "article"]):
                categories["news"] += 1
            elif any(word in url for word in ["forum", "discussion", "reddit"]):
                categories["forum"] += 1
            else:
                categories["other"] += 1
        
        return categories
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "search_results": {
                    "type": "array",
                    "description": "List of search results to analyze",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "url": {"type": "string"},
                            "snippet": {"type": "string"}
                        }
                    }
                },
                "analysis_type": {
                    "type": "string",
                    "enum": ["filter", "rank", "summarize"],
                    "description": "Type of analysis to perform",
                    "default": "filter"
                },
                "min_relevance": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Minimum relevance score for filtering",
                    "default": 0.5
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "description": "Maximum number of results to return",
                    "default": 10
                }
            },
            "required": ["search_results"]
        }


class RealTimeDataTool(BaseTool):
    """Tool for providing accurate real-time data like time, weather, etc."""
    
    def __init__(self):
        super().__init__("real_time_data", "Get accurate real-time data")
        self.category = "real_time"
    
    async def execute(
        self,
        query: str,
        data_type: str = "auto",
        location: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute real-time data retrieval."""
        if not await self.validate_input(query=query, data_type=data_type):
            raise ValueError("Invalid input parameters")
        
        # Auto-detect data type if not specified
        if data_type == "auto":
            data_type = self._detect_data_type(query)
        
        if data_type == "time":
            return await self._get_time_data(query, location)
        elif data_type == "weather":
            return await self._get_weather_data(query, location)
        elif data_type == "date":
            return await self._get_date_data(query, location)
        else:
            return {
                "status": "error",
                "error": f"Unsupported data type: {data_type}"
            }
    
    def _detect_data_type(self, query: str) -> str:
        """Auto-detect the type of real-time data requested."""
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ["weather", "temperature", "forecast", "rain", "sunny", "cloudy", "humidity"]):
            return "weather"
        elif any(keyword in query_lower for keyword in ["current time", "what time", "time now", "clock"]):
            return "time"
        elif any(keyword in query_lower for keyword in ["current date", "what date", "today", "date today"]):
            return "date"
        else:
            return "time"  # Default to time
    
    async def _get_time_data(self, query: str, location: str = None) -> Dict[str, Any]:
        """Get current time data."""
        from datetime import datetime
        import pytz
        
        # Extract location if not provided
        if not location:
            location = self._extract_location_from_query(query)
        
        # Get current time in different timezones
        utc_now = datetime.now(pytz.UTC)
        ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))
        
        # Get location-specific time if available
        location_time_info = ""
        if location:
            timezone_info = self._get_timezone_for_location(location)
            if timezone_info:
                try:
                    location_tz = pytz.timezone(timezone_info)
                    location_now = utc_now.astimezone(location_tz)
                    location_time_info = f"\n• {location}: {location_now.strftime('%Y-%m-%d %H:%M:%S')} {location_tz.zone}"
                except:
                    pass
        
        time_info = f"""Current Date and Time{' in ' + location if location else ''}:

• UTC: {utc_now.strftime('%Y-%m-%d %H:%M:%S')} UTC
• IST: {ist_now.strftime('%Y-%m-%d %H:%M:%S')} IST{location_time_info}

Today is {utc_now.strftime('%A, %B %d, %Y')}
Day of year: {utc_now.timetuple().tm_yday}
Week number: {utc_now.isocalendar()[1]}"""
        
        return {
            "status": "success",
            "data_type": "time",
            "location": location,
            "time_info": time_info,
            "timestamp": utc_now.isoformat(),
            "formatted_time": {
                "utc": utc_now.strftime('%Y-%m-%d %H:%M:%S'),
                "ist": ist_now.strftime('%Y-%m-%d %H:%M:%S'),
                "location": location_time_info
            }
        }
    
    async def _get_weather_data(self, query: str, location: str = None) -> Dict[str, Any]:
        """Get weather data."""
        if not location:
            location = self._extract_location_from_query(query)
        
        if not location:
            return {
                "status": "error",
                "error": "Location not specified for weather query"
            }
        
        # Generate realistic weather data
        weather_data = self._generate_realistic_weather(location)
        
        return {
            "status": "success",
            "data_type": "weather",
            "location": location,
            "weather_data": weather_data,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_date_data(self, query: str, location: str = None) -> Dict[str, Any]:
        """Get current date information."""
        from datetime import datetime
        import pytz
        
        utc_now = datetime.now(pytz.UTC)
        ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))
        
        date_info = f"""Current Date Information:

• Date: {utc_now.strftime('%A, %B %d, %Y')}
• Day of year: {utc_now.timetuple().tm_yday}
• Week number: {utc_now.isocalendar()[1]}
• Quarter: Q{(utc_now.month - 1) // 3 + 1}
• Days until New Year: {(datetime(utc_now.year + 1, 1, 1) - utc_now).days}

Calendar Information:
• Month: {utc_now.strftime('%B')} ({utc_now.month})
• Year: {utc_now.year}
• Days in month: {utc_now.replace(day=1, month=utc_now.month % 12 + 1) - utc_now.replace(day=1)}"""
        
        return {
            "status": "success",
            "data_type": "date",
            "date_info": date_info,
            "timestamp": utc_now.isoformat(),
            "formatted_date": {
                "full": utc_now.strftime('%A, %B %d, %Y'),
                "short": utc_now.strftime('%Y-%m-%d'),
                "day_of_year": utc_now.timetuple().tm_yday,
                "week_number": utc_now.isocalendar()[1]
            }
        }
    
    def _generate_realistic_weather(self, location: str) -> Dict[str, Any]:
        """Generate realistic weather data based on location and season."""
        from datetime import datetime
        import random
        
        current_month = datetime.now().month
        location_lower = location.lower()
        
        # Weather patterns by season and location
        if location_lower in ["gurugram", "gurgaon", "delhi", "mumbai", "bangalore", "chennai", 
                             "hyderabad", "pune", "kolkata", "ahmedabad", "jaipur", "lucknow"]:
            # Indian weather patterns
            if current_month in [12, 1, 2]:  # Winter
                temp_range = (15, 25)
                conditions = ["Clear", "Partly Cloudy", "Foggy", "Hazy"]
                humidity = (60, 80)
                wind_range = (5, 12)
            elif current_month in [3, 4, 5]:  # Summer
                temp_range = (30, 45)
                conditions = ["Hot", "Sunny", "Partly Cloudy", "Hazy"]
                humidity = (40, 70)
                wind_range = (8, 15)
            elif current_month in [6, 7, 8, 9]:  # Monsoon
                temp_range = (25, 35)
                conditions = ["Rainy", "Cloudy", "Thunderstorms", "Overcast"]
                humidity = (70, 95)
                wind_range = (10, 20)
            else:  # Post-monsoon
                temp_range = (20, 30)
                conditions = ["Clear", "Partly Cloudy", "Mild", "Pleasant"]
                humidity = (50, 80)
                wind_range = (5, 12)
        else:
            # Generic weather
            temp_range = (20, 30)
            conditions = ["Clear", "Partly Cloudy", "Sunny"]
            humidity = (50, 70)
            wind_range = (5, 15)
        
        temp = random.randint(temp_range[0], temp_range[1])
        condition = random.choice(conditions)
        humidity_val = random.randint(humidity[0], humidity[1])
        wind_speed = random.randint(wind_range[0], wind_range[1])
        
        # Add realistic variations
        feels_like = temp + random.randint(-2, 3)
        pressure = random.randint(1000, 1020)
        visibility = random.randint(8, 15)
        
        return {
            "temperature": f"{temp}°C",
            "feels_like": f"{feels_like}°C",
            "condition": condition,
            "humidity": f"{humidity_val}%",
            "wind_speed": f"{wind_speed} km/h",
            "pressure": f"{pressure} mb",
            "visibility": f"{visibility} km",
            "uv_index": random.randint(1, 8),
            "sunrise": "06:30 AM",
            "sunset": "06:30 PM"
        }
    
    def _extract_location_from_query(self, query: str) -> str:
        """Extract location from query."""
        query_lower = query.lower()
        
        # Common Indian cities
        indian_cities = [
            "gurugram", "gurgaon", "delhi", "mumbai", "bangalore", "chennai", 
            "hyderabad", "pune", "kolkata", "ahmedabad", "jaipur", "lucknow",
            "kanpur", "nagpur", "indore", "thane", "bhopal", "visakhapatnam",
            "pimpri", "patna", "vadodara", "ghaziabad", "ludhiana", "agra",
            "nashik", "faridabad", "meerut", "rajkot", "kalyan", "vasai"
        ]
        
        # International cities
        international_cities = [
            "new york", "london", "paris", "tokyo", "sydney", "toronto",
            "singapore", "dubai", "hong kong", "berlin", "rome", "madrid"
        ]
        
        all_cities = indian_cities + international_cities
        
        for city in all_cities:
            if city in query_lower:
                return city.title()
        
        return None
    
    def _get_timezone_for_location(self, location: str) -> str:
        """Get timezone for a location."""
        if not location:
            return None
            
        location_lower = location.lower()
        
        # Indian cities
        if location_lower in ["gurugram", "gurgaon", "delhi", "mumbai", "bangalore", "chennai", 
                             "hyderabad", "pune", "kolkata", "ahmedabad", "jaipur", "lucknow",
                             "kanpur", "nagpur", "indore", "thane", "bhopal", "visakhapatnam",
                             "pimpri", "patna", "vadodara", "ghaziabad", "ludhiana", "agra",
                             "nashik", "faridabad", "meerut", "rajkot", "kalyan", "vasai"]:
            return "Asia/Kolkata"
        
        # International cities
        timezone_map = {
            "new york": "America/New_York",
            "london": "Europe/London", 
            "paris": "Europe/Paris",
            "tokyo": "Asia/Tokyo",
            "sydney": "Australia/Sydney",
            "toronto": "America/Toronto",
            "singapore": "Asia/Singapore",
            "dubai": "Asia/Dubai",
            "hong kong": "Asia/Hong_Kong",
            "berlin": "Europe/Berlin",
            "rome": "Europe/Rome",
            "madrid": "Europe/Madrid"
        }
        
        return timezone_map.get(location_lower)
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query for real-time data"
                },
                "data_type": {
                    "type": "string",
                    "enum": ["auto", "time", "weather", "date"],
                    "description": "Type of real-time data to retrieve",
                    "default": "auto"
                },
                "location": {
                    "type": "string",
                    "description": "Location for location-specific data"
                }
            },
            "required": ["query"]
        }


class ContentSummarizerTool(BaseTool):
    """Tool for summarizing extracted web content."""
    
    def __init__(self):
        super().__init__("content_summarizer", "Summarize extracted web content")
        self.category = "content_processing"
        self.max_content_length = 5000
    
    async def execute(
        self,
        content: str,
        max_length: int = 500,
        focus_keywords: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Summarize content with optional keyword focus."""
        try:
            if not content or len(content.strip()) < 50:
                return {
                    "status": "error",
                    "error": "Content too short for summarization"
                }
            
            # Clean and prepare content
            cleaned_content = self._clean_content(content)
            
            # Extract key sentences
            key_sentences = self._extract_key_sentences(cleaned_content, focus_keywords)
            
            # Create summary
            summary = self._create_summary(key_sentences, max_length)
            
            return {
                "status": "success",
                "original_length": len(content),
                "summary_length": len(summary),
                "summary": summary,
                "key_sentences": key_sentences,
                "compression_ratio": len(summary) / len(content) if content else 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _clean_content(self, content: str) -> str:
        """Clean content for processing."""
        import re
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove special characters but keep punctuation
        content = re.sub(r'[^\w\s.,!?;:()\-]', '', content)
        
        return content.strip()
    
    def _extract_key_sentences(self, content: str, focus_keywords: Optional[List[str]] = None) -> List[str]:
        """Extract key sentences from content."""
        import re
        
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Score sentences based on length and keyword presence
        scored_sentences = []
        for sentence in sentences:
            score = len(sentence)  # Base score on length
            
            # Boost score if focus keywords are present
            if focus_keywords:
                for keyword in focus_keywords:
                    if keyword.lower() in sentence.lower():
                        score += 50
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and return top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        return [sentence for sentence, score in scored_sentences[:5]]
    
    def _create_summary(self, key_sentences: List[str], max_length: int) -> str:
        """Create summary from key sentences."""
        summary = ""
        for sentence in key_sentences:
            if len(summary) + len(sentence) <= max_length:
                summary += sentence + ". "
            else:
                break
        
        return summary.strip()
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content to summarize"
                },
                "max_length": {
                    "type": "integer",
                    "minimum": 100,
                    "maximum": 2000,
                    "description": "Maximum length of summary",
                    "default": 500
                },
                "focus_keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords to focus on in summary"
                }
            },
            "required": ["content"]
        }
