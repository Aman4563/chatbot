"""LLM-powered intent analysis and planning tool for intelligent decision making."""

import json
from typing import Dict, Any, List, Optional
from .base import BaseTool
from tools.llm_tools import LLMProviderTool


class IntentAnalysisTool(BaseTool):
    """Tool for LLM-powered intent analysis and tool planning."""
    
    def __init__(self, llm_provider_tool: LLMProviderTool):
        super().__init__("intent_analysis", "Analyze user intent and plan tool usage using LLM")
        self.category = "intent_analysis"
        self.llm_provider = llm_provider_tool
        
        # Define available tools and their capabilities
        self.available_tools = {
            "web_search": {
                "description": "Search the web for current information, news, facts, and real-time data",
                "use_cases": ["current events", "news", "weather", "stock prices", "latest information", "facts", "research"],
                "parameters": {"num_results": 10, "search_provider": "auto"}
            },
            "real_time_data": {
                "description": "Get real-time data like current time, date, weather, and location-specific information",
                "use_cases": ["current time", "current date", "weather", "timezone conversion", "location-based queries"],
                "parameters": {"data_type": "auto", "location": None}
            },
            "location_tool": {
                "description": "Detect and process location information from IP, coordinates, or addresses",
                "use_cases": ["location detection", "geocoding", "near me queries", "local information"],
                "parameters": {"ip_address": None, "latitude": None, "longitude": None, "address": None}
            },
            "timezone_tool": {
                "description": "Handle timezone detection and conversion",
                "use_cases": ["timezone detection", "time conversion", "location-based time"],
                "parameters": {"timezone": None, "location": None}
            },
            "llm_provider": {
                "description": "Generate responses using language models for general conversation and analysis",
                "use_cases": ["general conversation", "explanations", "analysis", "creative tasks", "reasoning"],
                "parameters": {"model": "auto", "temperature": 0.7}
            }
        }
    
    async def execute(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]] = None,
        available_metadata: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute LLM-powered intent analysis and tool planning."""
        if not await self.validate_input(user_input=user_input):
            raise ValueError("Invalid input parameters")
        
        try:
            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(
                user_input, conversation_history, available_metadata
            )
            
            # Get LLM analysis
            messages = [
                {"role": "system", "content": analysis_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # Use the LLM provider to analyze intent
            llm_response = await self.llm_provider.execute(
                messages=messages,
                provider="google",  # Use Gemini for analysis
                model="gemini-2.0-flash-exp",
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=2048
            )
            
            # Parse the LLM response
            analysis_result = self._parse_llm_response(llm_response)
            
            # Enhance analysis with additional context
            enhanced_analysis = self._enhance_analysis(analysis_result, user_input, available_metadata)
            
            return {
                "status": "success",
                "user_input": user_input,
                "intent_analysis": enhanced_analysis,
                "tool_plan": enhanced_analysis.get("tool_plan", []),
                "confidence": enhanced_analysis.get("confidence", 0.8),
                "reasoning": enhanced_analysis.get("reasoning", ""),
                "metadata": {
                    "analysis_timestamp": self._get_timestamp(),
                    "llm_model_used": "gemini-2.0-flash-exp",
                    "analysis_version": "1.0"
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "user_input": user_input,
                "error": str(e),
                "fallback_analysis": self._create_fallback_analysis(user_input)
            }
    
    def _create_analysis_prompt(
        self, 
        user_input: str, 
        conversation_history: List[Dict[str, Any]] = None,
        available_metadata: Dict[str, Any] = None
    ) -> str:
        """Create a comprehensive prompt for intent analysis."""
        
        # Build context information
        context_info = ""
        if conversation_history:
            context_info += f"\nConversation History: {json.dumps(conversation_history[-3:], indent=2)}"
        
        if available_metadata:
            context_info += f"\nAvailable Metadata: {json.dumps(available_metadata, indent=2)}"
        
        prompt = f"""You are an intelligent intent analysis system. Your job is to analyze user queries and determine the best tools and approach to answer them.

Available Tools:
{json.dumps(self.available_tools, indent=2)}

Context Information:{context_info}

For the user query, analyze and provide a JSON response with the following structure:
{{
    "intent_classification": {{
        "primary_intent": "one of: information_seeking, real_time_data, location_based, creative, analytical, conversational",
        "secondary_intents": ["list of additional intents"],
        "query_type": "one of: factual, procedural, creative, analytical, conversational",
        "complexity": "one of: simple, moderate, complex"
    }},
    "entity_extraction": {{
        "locations": ["list of locations mentioned"],
        "time_references": ["list of time-related terms"],
        "entities": ["list of other important entities"],
        "keywords": ["list of key terms for search"]
    }},
    "tool_plan": [
        {{
            "tool_name": "name of tool to use",
            "priority": 1,
            "reasoning": "why this tool is needed",
            "parameters": {{"param": "value"}},
            "expected_outcome": "what this tool should provide"
        }}
    ],
    "confidence": 0.85,
    "reasoning": "detailed explanation of your analysis and tool selection",
    "requires_metadata": true/false,
    "metadata_needed": ["list of metadata types needed"],
    "search_strategy": "description of how to approach the search/query"
}}

Guidelines:
1. Always prioritize real-time data tools for time, weather, and current information queries
2. Use location tools for "near me" or location-specific queries
3. Use web search for current events, news, and factual information
4. Consider conversation context when available
5. Plan tool usage in logical sequence (metadata first, then search, then synthesis)
6. Be specific about parameters and reasoning
7. High confidence (0.8+) for clear queries, lower for ambiguous ones

Analyze this query: "{user_input}"
"""
        return prompt
    
    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse the LLM response and extract structured analysis."""
        try:
            # Try to extract JSON from the response
            if "```json" in llm_response:
                json_start = llm_response.find("```json") + 7
                json_end = llm_response.find("```", json_start)
                json_str = llm_response[json_start:json_end].strip()
            elif "{" in llm_response and "}" in llm_response:
                json_start = llm_response.find("{")
                json_end = llm_response.rfind("}") + 1
                json_str = llm_response[json_start:json_end]
            else:
                # Fallback: create basic analysis from text
                return self._create_fallback_analysis_from_text(llm_response)
            
            analysis = json.loads(json_str)
            return analysis
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback to text-based analysis
            return self._create_fallback_analysis_from_text(llm_response)
    
    def _enhance_analysis(
        self, 
        analysis: Dict[str, Any], 
        user_input: str, 
        available_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Enhance the analysis with additional context and validation."""
        
        # Validate and enhance tool plan
        tool_plan = analysis.get("tool_plan", [])
        enhanced_tool_plan = []
        
        for tool in tool_plan:
            tool_name = tool.get("tool_name")
            if tool_name in self.available_tools:
                # Enhance parameters based on available metadata
                enhanced_tool = tool.copy()
                enhanced_tool["parameters"] = self._enhance_tool_parameters(
                    tool_name, tool.get("parameters", {}), available_metadata
                )
                enhanced_tool_plan.append(enhanced_tool)
        
        # Add metadata collection if needed
        if analysis.get("requires_metadata", False):
            metadata_needed = analysis.get("metadata_needed", [])
            if "location" in metadata_needed and not self._has_location_metadata(available_metadata):
                enhanced_tool_plan.insert(0, {
                    "tool_name": "location_tool",
                    "priority": 0,
                    "reasoning": "Location metadata needed for query",
                    "parameters": {"ip_address": None},
                    "expected_outcome": "User location information"
                })
        
        analysis["tool_plan"] = enhanced_tool_plan
        
        # Add query enhancement suggestions
        analysis["query_enhancement"] = self._suggest_query_enhancement(
            user_input, analysis.get("entity_extraction", {})
        )
        
        return analysis
    
    def _enhance_tool_parameters(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        available_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Enhance tool parameters based on available metadata."""
        if not available_metadata:
            return parameters
        
        enhanced_params = parameters.copy()
        
        if tool_name == "real_time_data":
            # Add location if available
            location = available_metadata.get("location", {}).get("value", {})
            if location and not enhanced_params.get("location"):
                city = location.get("city")
                if city:
                    enhanced_params["location"] = city
        
        elif tool_name == "web_search":
            # Enhance search query with location context
            location = available_metadata.get("location", {}).get("value", {})
            if location and "near me" in enhanced_params.get("query", "").lower():
                city = location.get("city")
                if city:
                    enhanced_params["query"] = enhanced_params.get("query", "").replace("near me", f"in {city}")
        
        return enhanced_params
    
    def _has_location_metadata(self, available_metadata: Dict[str, Any] = None) -> bool:
        """Check if location metadata is available."""
        if not available_metadata:
            return False
        
        location = available_metadata.get("location", {}).get("value", {})
        return bool(location.get("city") or location.get("country"))
    
    def _suggest_query_enhancement(
        self, 
        user_input: str, 
        entity_extraction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest query enhancements for better results."""
        suggestions = {
            "original_query": user_input,
            "enhanced_query": user_input,
            "search_keywords": entity_extraction.get("keywords", []),
            "location_context": entity_extraction.get("locations", []),
            "time_context": entity_extraction.get("time_references", [])
        }
        
        # Enhance query based on detected entities
        enhanced_query = user_input
        
        # Add location context if locations are detected
        locations = entity_extraction.get("locations", [])
        if locations and "near me" in user_input.lower():
            enhanced_query = user_input.replace("near me", f"in {locations[0]}")
        
        # Add time context for real-time queries
        time_refs = entity_extraction.get("time_references", [])
        if time_refs and any(ref in user_input.lower() for ref in ["latest", "current", "now"]):
            enhanced_query += " today"
        
        suggestions["enhanced_query"] = enhanced_query
        
        return suggestions
    
    def _create_fallback_analysis(self, user_input: str) -> Dict[str, Any]:
        """Create fallback analysis when LLM analysis fails."""
        user_input_lower = user_input.lower()
        
        # Basic rule-based fallback
        tool_plan = []
        
        # Check for real-time data needs
        if any(keyword in user_input_lower for keyword in ["time", "date", "weather", "current"]):
            tool_plan.append({
                "tool_name": "real_time_data",
                "priority": 1,
                "reasoning": "Real-time data query detected",
                "parameters": {"data_type": "auto"},
                "expected_outcome": "Current time/date/weather information"
            })
        
        # Check for location needs
        if any(keyword in user_input_lower for keyword in ["near me", "local", "restaurant", "store", "current location", "my location", "where am i", "whats my location", "what's my location", "address", "exact address", "accurate address", "precise address", "detailed address", "street address", "full address", "complete address", "more accurate", "more exact"]):
            tool_plan.append({
                "tool_name": "location_tool",
                "priority": 0,
                "reasoning": "Location-based query detected",
                "parameters": {"ip_address": None},
                "expected_outcome": "User location information"
            })
            tool_plan.append({
                "tool_name": "web_search",
                "priority": 2,
                "reasoning": "Search for local information",
                "parameters": {"query": user_input, "num_results": 10},
                "expected_outcome": "Local business/information results"
            })
        
        # Check for general information needs
        elif any(keyword in user_input_lower for keyword in ["what", "how", "why", "latest", "news"]):
            tool_plan.append({
                "tool_name": "web_search",
                "priority": 1,
                "reasoning": "Information-seeking query detected",
                "parameters": {"query": user_input, "num_results": 10},
                "expected_outcome": "Relevant information and facts"
            })
        
        # Always add LLM provider for response synthesis
        tool_plan.append({
            "tool_name": "llm_provider",
            "priority": 99,
            "reasoning": "Generate final response",
            "parameters": {"model": "auto", "temperature": 0.7},
            "expected_outcome": "Coherent response to user query"
        })
        
        return {
            "intent_classification": {
                "primary_intent": "information_seeking",
                "secondary_intents": [],
                "query_type": "factual",
                "complexity": "moderate"
            },
            "entity_extraction": {
                "locations": [],
                "time_references": [],
                "entities": [],
                "keywords": user_input.split()
            },
            "tool_plan": tool_plan,
            "confidence": 0.6,
            "reasoning": "Fallback analysis using rule-based detection",
            "requires_metadata": "near me" in user_input_lower or "local" in user_input_lower,
            "metadata_needed": ["location"] if "near me" in user_input_lower else [],
            "search_strategy": "Basic keyword-based search approach"
        }
    
    def _create_fallback_analysis_from_text(self, llm_response: str) -> Dict[str, Any]:
        """Create analysis from unstructured LLM response."""
        # Extract key information from text response
        analysis = self._create_fallback_analysis("")
        analysis["reasoning"] = llm_response[:500] + "..." if len(llm_response) > 500 else llm_response
        analysis["confidence"] = 0.5
        return analysis
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "user_input": {
                    "type": "string",
                    "description": "User query to analyze"
                },
                "conversation_history": {
                    "type": "array",
                    "description": "Previous conversation messages for context",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string"},
                            "content": {"type": "string"}
                        }
                    }
                },
                "available_metadata": {
                    "type": "object",
                    "description": "Available user metadata (location, timezone, etc.)"
                }
            },
            "required": ["user_input"]
        }
