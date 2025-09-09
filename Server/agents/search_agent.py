"""Search Agent implementation for web search and information retrieval."""

from typing import Dict, Any, List, Optional, AsyncIterator
from langgraph.graph import StateGraph, END
from .base import BaseAgent
from graphs.state import SearchState
from tools.web_tools import WebSearchTool, URLFetcherTool, SearchResultAnalyzerTool, RealTimeDataTool
from tools.llm_tools import LLMProviderTool, ResponseSynthesisTool


class SearchAgent(BaseAgent):
    """Specialized agent for web search and information retrieval."""
    
    def __init__(self):
        super().__init__("search_agent", "Web search and information retrieval specialist")
        self.category = "web_search"
        self.priority = 3
    
    def _initialize_tools(self) -> None:
        """Initialize tools available to this agent."""
        self.tools = {
            "web_search": WebSearchTool(),
            "url_fetcher": URLFetcherTool(),
            "search_analyzer": SearchResultAnalyzerTool(),
            "real_time_data": RealTimeDataTool(),
            "llm_provider": LLMProviderTool(),
            "response_synthesis": ResponseSynthesisTool()
        }
    
    def _build_graph(self) -> None:
        """Build the agent's LangGraph workflow."""
        workflow = StateGraph(SearchState)
        
        # Add nodes
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("optimize_query", self._optimize_query)
        workflow.add_node("execute_search", self._execute_search)
        workflow.add_node("fetch_content", self._fetch_content)
        workflow.add_node("analyze_results", self._analyze_results)
        workflow.add_node("synthesize_information", self._synthesize_information)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("finalize_search", self._finalize_search)
        
        # Add edges
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "optimize_query")
        workflow.add_edge("optimize_query", "execute_search")
        
        # Conditional routing based on search results
        workflow.add_conditional_edges(
            "execute_search",
            self._should_fetch_content,
            {
                "fetch": "fetch_content",
                "analyze": "analyze_results"
            }
        )
        
        workflow.add_edge("fetch_content", "analyze_results")
        workflow.add_edge("analyze_results", "synthesize_information")
        workflow.add_edge("synthesize_information", "generate_response")
        workflow.add_edge("generate_response", "finalize_search")
        workflow.add_edge("finalize_search", END)
        
        self.graph = workflow.compile()
    
    async def process(self, state: SearchState) -> SearchState:
        """Process the current state and return updated state."""
        try:
            if not await self.validate_state(state):
                raise ValueError("Invalid state for SearchAgent")
            
            # Run the graph
            result = await self.graph.ainvoke(state)
            return result
        
        except Exception as e:
            return await self.handle_error(e, state)
    
    async def stream(self, state: SearchState) -> AsyncIterator[str]:
        """Stream processing results."""
        try:
            if not await self.validate_state(state):
                yield "Error: Invalid state for SearchAgent"
                return
            
            # Run the graph with streaming
            async for chunk in self.graph.astream(state):
                if "finalize_search" in chunk:
                    response = chunk["finalize_search"].get("final_response", "")
                    if response:
                        yield response
                elif "execute_search" in chunk:
                    search_results = chunk["execute_search"].get("search_results", [])
                    if search_results:
                        yield f"Found {len(search_results)} search results..."
                elif "analyze_results" in chunk:
                    analysis = chunk["analyze_results"].get("result_analysis", {})
                    if analysis:
                        yield f"Analyzing results: {analysis.get('summary', '')}"
        
        except Exception as e:
            yield f"Error in SearchAgent: {str(e)}"
    
    async def _analyze_query(self, state: SearchState) -> Dict[str, Any]:
        """Analyze the search query to understand intent and requirements."""
        user_input = state.get("user_input", "")
        
        # Analyze query characteristics
        query_analysis = {
            "original_query": user_input,
            "query_type": self._classify_query_type(user_input),
            "search_intent": self._determine_search_intent(user_input),
            "complexity": self._assess_query_complexity(user_input),
            "entities": self._extract_entities(user_input),
            "keywords": self._extract_keywords(user_input),
            "temporal_requirements": self._detect_temporal_requirements(user_input),
            "geographic_requirements": self._detect_geographic_requirements(user_input),
            "domain_preferences": self._detect_domain_preferences(user_input)
        }
        
        state["query_analysis"] = query_analysis
        return state
    
    async def _optimize_query(self, state: SearchState) -> Dict[str, Any]:
        """Optimize the search query for better results."""
        query_analysis = state.get("query_analysis", {})
        original_query = query_analysis.get("original_query", "")
        
        # Generate optimized queries
        optimized_queries = self._generate_optimized_queries(original_query, query_analysis)
        
        # Select best query
        primary_query = optimized_queries[0] if optimized_queries else original_query
        
        state["search_queries"] = optimized_queries
        state["primary_query"] = primary_query
        
        return state
    
    async def _execute_search(self, state: SearchState) -> Dict[str, Any]:
        """Execute web search with optimized queries."""
        search_queries = state.get("search_queries", [])
        primary_query = state.get("primary_query", "")
        query_analysis = state.get("query_analysis", {})
        
        all_results = []
        search_errors = []
        
        # Check if this is a real-time query that should use RealTimeDataTool
        if self._is_real_time_query(primary_query, query_analysis):
            try:
                real_time_tool = self.tools["real_time_data"]
                real_time_result = await real_time_tool.execute(
                    query=primary_query,
                    data_type="auto"
                )
                
                if real_time_result["status"] == "success":
                    # Convert real-time data to search result format
                    real_time_result_formatted = {
                        "title": f"Real-time Data: {primary_query}",
                        "url": "https://real-time-data",
                        "snippet": real_time_result.get("time_info", real_time_result.get("weather_data", real_time_result.get("date_info", ""))),
                        "rank": 1,
                        "provider": "real_time",
                        "type": "real_time_data"
                    }
                    all_results.append(real_time_result_formatted)
                    print(f"✅ Real-time data retrieved for: {primary_query}")
                else:
                    search_errors.append(f"Real-time data failed: {real_time_result.get('error', 'Unknown error')}")
            except Exception as e:
                search_errors.append(f"Real-time data error: {str(e)}")
        
        # Execute web search for each query
        for query in search_queries[:3]:  # Limit to 3 queries
            try:
                search_tool = self.tools["web_search"]
                result = await search_tool.execute(
                    query=query,
                    num_results=10,
                    search_provider="auto"  # Use intelligent fallback
                )
                
                if result["status"] == "success":
                    all_results.extend(result["results"])
                else:
                    search_errors.append(f"Query '{query}': {result.get('error', 'Search failed')}")
            
            except Exception as e:
                search_errors.append(f"Query '{query}': {str(e)}")
        
        # Remove duplicates and rank results
        unique_results = self._deduplicate_results(all_results)
        ranked_results = self._rank_results(unique_results, primary_query)
        
        state["search_results"] = ranked_results
        state["search_errors"] = search_errors
        
        return state
    
    async def _fetch_content(self, state: SearchState) -> Dict[str, Any]:
        """Fetch content from top search results."""
        search_results = state.get("search_results", [])
        fetched_content = []
        fetch_errors = []
        
        # Fetch content from top 5 results
        for result in search_results[:5]:
            try:
                url = result.get("url", "")
                if url:
                    fetcher_tool = self.tools["url_fetcher"]
                    content_result = await fetcher_tool.execute(
                        url=url,
                        fetch_type="content"
                    )
                    
                    if content_result["status"] == "success":
                        fetched_content.append({
                            "url": url,
                            "title": result.get("title", ""),
                            "content": content_result.get("content", ""),
                            "content_length": content_result.get("content_length", 0),
                            "content_type": content_result.get("content_type", "")
                        })
                    else:
                        fetch_errors.append(f"Failed to fetch {url}: {content_result.get('error', '')}")
            
            except Exception as e:
                fetch_errors.append(f"Error fetching {result.get('url', '')}: {str(e)}")
        
        state["fetched_content"] = fetched_content
        state["fetch_errors"] = fetch_errors
        
        return state
    
    async def _analyze_results(self, state: SearchState) -> Dict[str, Any]:
        """Analyze search results and fetched content."""
        search_results = state.get("search_results", [])
        fetched_content = state.get("fetched_content", [])
        query_analysis = state.get("query_analysis", {})
        
        try:
            # Analyze search results
            analyzer_tool = self.tools["search_analyzer"]
            result_analysis = await analyzer_tool.execute(
                search_results=search_results,
                analysis_type="filter",
                min_relevance=0.3,
                max_results=10
            )
            
            # Analyze content quality
            content_analysis = self._analyze_content_quality(fetched_content)
            
            # Generate insights
            insights = self._generate_search_insights(
                search_results, 
                fetched_content, 
                query_analysis
            )
            
            state["result_analysis"] = result_analysis
            state["content_analysis"] = content_analysis
            state["search_insights"] = insights
            
        except Exception as e:
            state["tool_errors"]["result_analysis"] = str(e)
        
        return state
    
    async def _synthesize_information(self, state: SearchState) -> Dict[str, Any]:
        """Synthesize information from search results and content."""
        search_results = state.get("search_results", [])
        fetched_content = state.get("fetched_content", [])
        query_analysis = state.get("query_analysis", {})
        
        try:
            # Prepare sources for synthesis
            sources = []
            
            # Add search result snippets
            for result in search_results:
                sources.append({
                    "content": f"{result.get('title', '')}: {result.get('snippet', '')}",
                    "source_type": "search_result",
                    "metadata": {
                        "url": result.get("url", ""),
                        "relevance": result.get("relevance_score", 0)
                    }
                })
            
            # Add fetched content with enhanced information
            for content in fetched_content:
                if content.get("content"):
                    # Use clean text if available, otherwise use main content
                    content_text = content.get("clean_text", content.get("main_content", content["content"]))
                    
                    # Create comprehensive source with metadata
                    source = {
                        "content": content_text[:3000],  # Increased limit for better context
                        "source_type": "web_content",
                        "metadata": {
                            "url": content["url"],
                            "title": content.get("title", ""),
                            "description": content.get("description", ""),
                            "content_length": content.get("content_length", 0),
                            "domain": content.get("extraction_metadata", {}).get("domain", ""),
                            "author": content.get("extraction_metadata", {}).get("author"),
                            "publication_date": content.get("extraction_metadata", {}).get("publication_date"),
                            "language": content.get("extraction_metadata", {}).get("language", "en")
                        }
                    }
                    sources.append(source)
            
            # Synthesize information with enhanced context
            synthesis_tool = self.tools["response_synthesis"]
            synthesized_info = await synthesis_tool.execute(
                sources=sources,
                synthesis_type="summarize",
                query_context=query_analysis
            )
            
            state["synthesized_information"] = synthesized_info
            
        except Exception as e:
            state["tool_errors"]["information_synthesis"] = str(e)
        
        return state
    
    async def _generate_response(self, state: SearchState) -> Dict[str, Any]:
        """Generate final response using LLM."""
        try:
            # Prepare context for LLM
            query_analysis = state.get("query_analysis", {})
            synthesized_info = state.get("synthesized_information", "")
            search_insights = state.get("search_insights", {})
            
            # Build prompt for LLM
            prompt = self._build_search_prompt(
                query_analysis, 
                synthesized_info, 
                search_insights
            )
            
            # Generate response using LLM
            llm_tool = self.tools["llm_provider"]
            llm_response = await llm_tool.execute(
                messages=[{"role": "user", "content": prompt}],
                provider="openai",
                model="gpt-4o",
                temperature=0.3,  # Lower temperature for factual responses
                max_tokens=2000
            )
            
            state["llm_response"] = llm_response
            
        except Exception as e:
            state["tool_errors"]["llm_generation"] = str(e)
            state["llm_response"] = "Error generating response from search results"
        
        return state
    
    async def _finalize_search(self, state: SearchState) -> Dict[str, Any]:
        """Finalize the search response with citations."""
        try:
            # Get the LLM response
            llm_response = state.get("llm_response", "")
            search_results = state.get("search_results", [])
            search_insights = state.get("search_insights", {})
            
            # Add citations
            citations = self._generate_citations(search_results)
            
            # Compile final response
            final_response = self._compile_final_response(
                llm_response, 
                citations, 
                search_insights
            )
            
            state["final_response"] = final_response
            state["citations"] = citations
            
        except Exception as e:
            state["tool_errors"]["response_finalization"] = str(e)
            state["final_response"] = "Error finalizing search response"
        
        return state
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of search query."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["what is", "define", "definition"]):
            return "definition"
        elif any(word in query_lower for word in ["how to", "tutorial", "guide"]):
            return "how_to"
        elif any(word in query_lower for word in ["when", "date", "time"]):
            return "temporal"
        elif any(word in query_lower for word in ["where", "location", "place"]):
            return "geographic"
        elif any(word in query_lower for word in ["who", "person", "biography"]):
            return "person"
        elif any(word in query_lower for word in ["why", "reason", "cause"]):
            return "explanation"
        elif any(word in query_lower for word in ["compare", "vs", "versus"]):
            return "comparison"
        else:
            return "general"
    
    def _determine_search_intent(self, query: str) -> str:
        """Determine the search intent."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["news", "latest", "recent", "current"]):
            return "current_events"
        elif any(word in query_lower for word in ["research", "study", "analysis"]):
            return "research"
        elif any(word in query_lower for word in ["buy", "price", "cost", "purchase"]):
            return "commercial"
        elif any(word in query_lower for word in ["learn", "education", "course"]):
            return "educational"
        else:
            return "informational"
    
    def _assess_query_complexity(self, query: str) -> str:
        """Assess the complexity of the search query."""
        word_count = len(query.split())
        
        if word_count < 3:
            return "simple"
        elif word_count < 10:
            return "medium"
        else:
            return "complex"
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from the query."""
        # Simple entity extraction - in production, use NER models
        entities = []
        words = query.split()
        
        for word in words:
            if word.istitle() and len(word) > 2:
                entities.append(word)
        
        return entities
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from the query."""
        # Remove stop words and extract meaningful keywords
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = query.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords
    
    def _detect_temporal_requirements(self, query: str) -> bool:
        """Detect if query has temporal requirements."""
        temporal_words = ["recent", "latest", "current", "today", "yesterday", "this week", "this month", "2024", "2023"]
        return any(word in query.lower() for word in temporal_words)
    
    def _detect_geographic_requirements(self, query: str) -> bool:
        """Detect if query has geographic requirements."""
        geographic_words = ["where", "location", "place", "city", "country", "state", "region"]
        return any(word in query.lower() for word in geographic_words)
    
    def _detect_domain_preferences(self, query: str) -> List[str]:
        """Detect domain preferences from the query."""
        domains = []
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["tech", "technology", "software", "programming"]):
            domains.append("technology")
        if any(word in query_lower for word in ["health", "medical", "medicine", "disease"]):
            domains.append("health")
        if any(word in query_lower for word in ["business", "finance", "economy", "market"]):
            domains.append("business")
        if any(word in query_lower for word in ["science", "research", "study", "experiment"]):
            domains.append("science")
        
        return domains
    
    def _generate_optimized_queries(self, original_query: str, analysis: Dict[str, Any]) -> List[str]:
        """Generate optimized search queries."""
        queries = [original_query]
        
        # Add variations based on query type
        query_type = analysis.get("query_type", "general")
        
        if query_type == "definition":
            queries.append(f"define {original_query}")
            queries.append(f"{original_query} meaning")
        elif query_type == "how_to":
            queries.append(f"how to {original_query}")
            queries.append(f"{original_query} tutorial")
        elif query_type == "temporal":
            queries.append(f"{original_query} 2024")
            queries.append(f"latest {original_query}")
        
        # Add keyword variations
        keywords = analysis.get("keywords", [])
        if keywords:
            queries.append(" ".join(keywords))
        
        return queries[:3]  # Limit to 3 queries
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate search results."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    def _rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank search results by relevance."""
        # Simple ranking based on title and snippet relevance
        for result in results:
            relevance_score = self._calculate_relevance_score(result, query)
            result["relevance_score"] = relevance_score
        
        # Sort by relevance score
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return results
    
    def _calculate_relevance_score(self, result: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for a search result."""
        query_words = set(query.lower().split())
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        
        # Count word matches
        title_matches = len(query_words.intersection(set(title.split())))
        snippet_matches = len(query_words.intersection(set(snippet.split())))
        
        # Calculate score
        total_words = len(query_words)
        if total_words == 0:
            return 0.5
        
        score = (title_matches * 2 + snippet_matches) / (total_words * 3)
        return min(score, 1.0)
    
    def _analyze_content_quality(self, fetched_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the quality of fetched content."""
        if not fetched_content:
            return {"average_quality": 0, "total_content": 0}
        
        quality_scores = []
        total_content_length = 0
        
        for content in fetched_content:
            content_length = content.get("content_length", 0)
            total_content_length += content_length
            
            # Simple quality scoring
            score = 0.5  # Base score
            
            if content_length > 1000:
                score += 0.2
            elif content_length > 500:
                score += 0.1
            
            if content.get("content_type", "").startswith("text/html"):
                score += 0.1
            
            quality_scores.append(min(score, 1.0))
        
        return {
            "average_quality": sum(quality_scores) / len(quality_scores),
            "total_content": total_content_length,
            "content_count": len(fetched_content)
        }
    
    def _generate_search_insights(self, search_results: List[Dict[str, Any]], fetched_content: List[Dict[str, Any]], query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from search results."""
        insights = {
            "total_results": len(search_results),
            "content_fetched": len(fetched_content),
            "query_complexity": query_analysis.get("complexity", "unknown"),
            "search_intent": query_analysis.get("search_intent", "unknown"),
            "top_domains": self._extract_top_domains(search_results),
            "result_types": self._categorize_results(search_results),
            "coverage_assessment": self._assess_coverage(search_results, query_analysis)
        }
        
        return insights
    
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
            "news": 0,
            "academic": 0,
            "commercial": 0,
            "other": 0
        }
        
        for result in search_results:
            url = result.get("url", "").lower()
            title = result.get("title", "").lower()
            
            if any(word in url for word in ["docs", "documentation", "api"]):
                categories["documentation"] += 1
            elif any(word in url for word in ["news", "blog", "article"]):
                categories["news"] += 1
            elif any(word in url for word in ["edu", "academic", "research"]):
                categories["academic"] += 1
            elif any(word in url for word in ["shop", "buy", "store", "amazon"]):
                categories["commercial"] += 1
            else:
                categories["other"] += 1
        
        return categories
    
    def _assess_coverage(self, search_results: List[Dict[str, Any]], query_analysis: Dict[str, Any]) -> str:
        """Assess the coverage of search results."""
        if not search_results:
            return "no_results"
        
        result_count = len(search_results)
        query_complexity = query_analysis.get("complexity", "medium")
        
        if query_complexity == "simple" and result_count >= 5:
            return "good_coverage"
        elif query_complexity == "medium" and result_count >= 10:
            return "good_coverage"
        elif query_complexity == "complex" and result_count >= 15:
            return "good_coverage"
        else:
            return "limited_coverage"
    
    def _build_search_prompt(self, query_analysis: Dict[str, Any], synthesized_info: str, search_insights: Dict[str, Any]) -> str:
        """Build prompt for LLM response generation."""
        original_query = query_analysis.get("original_query", "")
        query_type = query_analysis.get("query_type", "general")
        search_intent = query_analysis.get("search_intent", "informational")
        
        prompt = f"""Based on the search results for the query "{original_query}", provide a comprehensive and accurate response.

Query Type: {query_type}
Search Intent: {search_intent}

Search Results Summary:
{synthesized_info}

Search Insights:
- Total Results: {search_insights.get('total_results', 0)}
- Coverage: {search_insights.get('coverage_assessment', 'unknown')}
- Top Domains: {', '.join(search_insights.get('top_domains', [])[:3])}

Please provide a well-structured response that:
1. Directly answers the user's question
2. Includes relevant details from the search results
3. Maintains accuracy and objectivity
4. Is organized and easy to read
5. Includes proper citations when referencing specific information

Response:"""
        
        return prompt
    
    def _generate_citations(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generate citations for search results."""
        citations = []
        
        for i, result in enumerate(search_results[:5], 1):  # Top 5 results
            citation = {
                "number": i,
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", "")[:200] + "..." if len(result.get("snippet", "")) > 200 else result.get("snippet", "")
            }
            citations.append(citation)
        
        return citations
    
    def _compile_final_response(self, llm_response: str, citations: List[Dict[str, str]], search_insights: Dict[str, Any]) -> str:
        """Compile the final search response."""
        response_parts = []
        
        # Add main response
        response_parts.append(llm_response)
        
        # Add citations
        if citations:
            response_parts.append("\n\n## Sources:")
            for citation in citations:
                response_parts.append(f"{citation['number']}. [{citation['title']}]({citation['url']})")
                if citation['snippet']:
                    response_parts.append(f"   {citation['snippet']}")
        
        # Add search summary
        response_parts.append(f"\n\n*Search completed with {search_insights.get('total_results', 0)} results*")
        
        return "\n".join(response_parts)
    
    def _should_fetch_content(self, state: SearchState) -> str:
        """Determine if content should be fetched from URLs."""
        search_results = state.get("search_results", [])
        query_analysis = state.get("query_analysis", {})
        
        # Fetch content for complex queries or when we have good results
        if query_analysis.get("complexity") == "complex" and len(search_results) >= 3:
            return "fetch"
        elif len(search_results) >= 5:
            return "fetch"
        else:
            return "analyze"
    
    def _is_real_time_query(self, query: str, query_analysis: Dict[str, Any]) -> bool:
        """Check if query requires real-time data."""
        query_lower = query.lower()
        
        # Check for real-time keywords
        real_time_keywords = [
            "current", "recent", "latest", "today", "now", "live", "real-time",
            "what time", "what date", "current time", "current date", "time now",
            "date today", "weather", "temperature", "forecast"
        ]
        
        # Check query type
        query_type = query_analysis.get("query_type", "")
        if query_type in ["temporal", "geographic"]:
            return True
        
        # Check for real-time keywords
        return any(keyword in query_lower for keyword in real_time_keywords)
