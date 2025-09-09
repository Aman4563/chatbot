"""Context-aware tool selection system that learns from user history and adapts tool selection."""

import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from .base import BaseTool
from tools.llm_tools import LLMProviderTool


class ContextAwareSelector(BaseTool):
    """Context-aware tool selection that adapts based on user history and preferences."""
    
    def __init__(self, llm_provider_tool: LLMProviderTool):
        super().__init__("context_aware_selector", "Context-aware tool selection with learning capabilities")
        self.category = "tool_selection"
        self.llm_provider = llm_provider_tool
        
        # User preference learning
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        self.query_patterns: Dict[str, List[Dict[str, Any]]] = {}
        self.tool_performance_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Context analysis cache
        self.context_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 3600  # 1 hour
    
    async def execute(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]] = None,
        user_metadata: Dict[str, Any] = None,
        available_tools: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Select optimal tools based on context, user history, and preferences."""
        if not await self.validate_input(user_input=user_input):
            raise ValueError("Invalid input parameters")
        
        try:
            # Analyze context
            context_analysis = await self._analyze_context(
                user_input, conversation_history, user_metadata
            )
            
            # Get user preferences
            user_id = user_metadata.get("user_id", "default") if user_metadata else "default"
            user_prefs = self._get_user_preferences(user_id)
            
            # Analyze query patterns
            query_pattern = await self._analyze_query_pattern(user_input, context_analysis)
            
            # Get tool performance history
            tool_performance = self._get_tool_performance_history(query_pattern)
            
            # Generate context-aware tool recommendations
            tool_recommendations = await self._generate_tool_recommendations(
                user_input, context_analysis, user_prefs, tool_performance, available_tools
            )
            
            # Create adaptive tool plan
            adaptive_plan = await self._create_adaptive_tool_plan(
                tool_recommendations, context_analysis, user_prefs
            )
            
            # Update learning data
            await self._update_learning_data(user_id, user_input, context_analysis, tool_recommendations)
            
            return {
                "status": "success",
                "user_input": user_input,
                "context_analysis": context_analysis,
                "user_preferences": user_prefs,
                "tool_recommendations": tool_recommendations,
                "adaptive_plan": adaptive_plan,
                "confidence": self._calculate_selection_confidence(context_analysis, user_prefs),
                "learning_insights": self._generate_learning_insights(user_id, query_pattern)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "fallback_plan": self._create_fallback_plan(user_input, available_tools)
            }
    
    async def _analyze_context(
        self, 
        user_input: str, 
        conversation_history: List[Dict[str, Any]] = None,
        user_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze the context of the user query."""
        # Check cache first
        cache_key = f"context_{hash(user_input)}"
        if cache_key in self.context_cache:
            cached_data = self.context_cache[cache_key]
            if self._is_cache_valid(cached_data):
                return cached_data["analysis"]
        
        try:
            # Create context analysis prompt
            context_prompt = self._create_context_analysis_prompt(
                user_input, conversation_history, user_metadata
            )
            
            messages = [
                {"role": "system", "content": context_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # Use LLM for context analysis
            analysis_result = await self.llm_provider.execute(
                messages=messages,
                provider="google",
                model="gemini-2.0-flash-exp",
                temperature=0.2,
                max_tokens=1024
            )
            
            # Parse and structure the analysis
            context_analysis = self._parse_context_analysis(analysis_result, user_input, user_metadata)
            
            # Cache the result
            self.context_cache[cache_key] = {
                "analysis": context_analysis,
                "timestamp": self._get_timestamp()
            }
            
            return context_analysis
            
        except Exception as e:
            # Fallback to rule-based context analysis
            return self._create_fallback_context_analysis(user_input, user_metadata)
    
    def _create_context_analysis_prompt(
        self, 
        user_input: str, 
        conversation_history: List[Dict[str, Any]] = None,
        user_metadata: Dict[str, Any] = None
    ) -> str:
        """Create a prompt for context analysis."""
        
        context_info = ""
        if conversation_history:
            context_info += f"\nRecent Conversation:\n{json.dumps(conversation_history[-3:], indent=2)}"
        
        if user_metadata:
            context_info += f"\nUser Metadata:\n{json.dumps(user_metadata, indent=2)}"
        
        prompt = f"""You are a context analysis expert. Analyze the user query and provide structured context information.

Available Tools:
- web_search: For current information, news, facts, research
- real_time_data: For time, weather, current data
- location_tool: For location detection and geocoding
- timezone_tool: For timezone handling
- llm_provider: For general conversation and analysis

Context Information:{context_info}

Analyze the query and provide a JSON response with this structure:
{{
    "query_classification": {{
        "primary_type": "one of: information_seeking, real_time_data, location_based, conversational, analytical",
        "secondary_types": ["list of additional types"],
        "complexity_level": "one of: simple, moderate, complex",
        "urgency": "one of: low, medium, high",
        "requires_context": true/false
    }},
    "user_context": {{
        "location_relevant": true/false,
        "time_relevant": true/false,
        "history_relevant": true/false,
        "preference_indicators": ["list of preference indicators"],
        "expertise_level": "one of: beginner, intermediate, advanced"
    }},
    "tool_requirements": {{
        "must_have": ["list of essential tools"],
        "should_have": ["list of recommended tools"],
        "nice_to_have": ["list of optional tools"],
        "avoid": ["list of tools to avoid"]
    }},
    "contextual_factors": {{
        "time_sensitivity": "how time-sensitive is this query",
        "location_dependency": "how location-dependent is this query",
        "personalization_level": "how much personalization is needed",
        "data_freshness": "how fresh does the data need to be"
    }},
    "adaptation_suggestions": {{
        "parameter_optimizations": ["suggestions for tool parameters"],
        "execution_strategy": "suggested execution approach",
        "fallback_options": ["alternative approaches if primary fails"]
    }}
}}

Analyze this query: "{user_input}"
"""
        return prompt
    
    def _parse_context_analysis(
        self, 
        analysis_result: str, 
        user_input: str, 
        user_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Parse the LLM context analysis result."""
        try:
            # Try to extract JSON from the response
            if "```json" in analysis_result:
                json_start = analysis_result.find("```json") + 7
                json_end = analysis_result.find("```", json_start)
                json_str = analysis_result[json_start:json_end].strip()
            elif "{" in analysis_result and "}" in analysis_result:
                json_start = analysis_result.find("{")
                json_end = analysis_result.rfind("}") + 1
                json_str = analysis_result[json_start:json_end]
            else:
                return self._create_fallback_context_analysis(user_input, user_metadata)
            
            analysis = json.loads(json_str)
            
            # Enhance with metadata
            if user_metadata:
                analysis["user_metadata"] = user_metadata
            
            return analysis
            
        except (json.JSONDecodeError, ValueError):
            return self._create_fallback_context_analysis(user_input, user_metadata)
    
    def _create_fallback_context_analysis(
        self, 
        user_input: str, 
        user_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create fallback context analysis using rule-based approach."""
        user_input_lower = user_input.lower()
        
        # Basic classification
        if any(keyword in user_input_lower for keyword in ["time", "date", "weather", "current"]):
            primary_type = "real_time_data"
        elif any(keyword in user_input_lower for keyword in ["near me", "local", "restaurant", "store"]):
            primary_type = "location_based"
        elif any(keyword in user_input_lower for keyword in ["what", "how", "why", "latest", "news"]):
            primary_type = "information_seeking"
        else:
            primary_type = "conversational"
        
        return {
            "query_classification": {
                "primary_type": primary_type,
                "secondary_types": [],
                "complexity_level": "moderate",
                "urgency": "medium",
                "requires_context": "near me" in user_input_lower
            },
            "user_context": {
                "location_relevant": "near me" in user_input_lower,
                "time_relevant": any(keyword in user_input_lower for keyword in ["time", "date", "current"]),
                "history_relevant": False,
                "preference_indicators": [],
                "expertise_level": "intermediate"
            },
            "tool_requirements": {
                "must_have": ["llm_provider"],
                "should_have": [],
                "nice_to_have": [],
                "avoid": []
            },
            "contextual_factors": {
                "time_sensitivity": "high" if "current" in user_input_lower else "medium",
                "location_dependency": "high" if "near me" in user_input_lower else "low",
                "personalization_level": "medium",
                "data_freshness": "high" if any(keyword in user_input_lower for keyword in ["latest", "current", "today"]) else "medium"
            },
            "adaptation_suggestions": {
                "parameter_optimizations": [],
                "execution_strategy": "sequential",
                "fallback_options": ["rule_based_fallback"]
            },
            "user_metadata": user_metadata or {}
        }
    
    def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences and learning data."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                "preferred_tools": {},
                "tool_success_rates": {},
                "query_patterns": {},
                "response_preferences": {
                    "detail_level": "medium",
                    "response_format": "conversational",
                    "include_sources": True
                },
                "last_updated": self._get_timestamp()
            }
        
        return self.user_preferences[user_id]
    
    async def _analyze_query_pattern(
        self, 
        user_input: str, 
        context_analysis: Dict[str, Any]
    ) -> str:
        """Analyze and categorize the query pattern."""
        # Create a pattern signature based on key characteristics
        pattern_elements = []
        
        # Add primary type
        primary_type = context_analysis.get("query_classification", {}).get("primary_type", "unknown")
        pattern_elements.append(primary_type)
        
        # Add complexity
        complexity = context_analysis.get("query_classification", {}).get("complexity_level", "moderate")
        pattern_elements.append(complexity)
        
        # Add location relevance
        if context_analysis.get("user_context", {}).get("location_relevant", False):
            pattern_elements.append("location")
        
        # Add time relevance
        if context_analysis.get("user_context", {}).get("time_relevant", False):
            pattern_elements.append("time")
        
        return "_".join(pattern_elements)
    
    def _get_tool_performance_history(self, query_pattern: str) -> Dict[str, Any]:
        """Get tool performance history for the query pattern."""
        if query_pattern not in self.tool_performance_history:
            return {}
        
        history = self.tool_performance_history[query_pattern]
        
        # Calculate performance metrics
        tool_metrics = {}
        for entry in history:
            tool_name = entry.get("tool_name")
            if tool_name not in tool_metrics:
                tool_metrics[tool_name] = {"success_count": 0, "total_count": 0, "avg_quality": 0.0}
            
            tool_metrics[tool_name]["total_count"] += 1
            if entry.get("success", False):
                tool_metrics[tool_name]["success_count"] += 1
                tool_metrics[tool_name]["avg_quality"] += entry.get("quality_score", 0.5)
        
        # Calculate success rates and average quality
        for tool_name, metrics in tool_metrics.items():
            if metrics["total_count"] > 0:
                metrics["success_rate"] = metrics["success_count"] / metrics["total_count"]
                metrics["avg_quality"] = metrics["avg_quality"] / metrics["success_count"] if metrics["success_count"] > 0 else 0.0
        
        return tool_metrics
    
    async def _generate_tool_recommendations(
        self, 
        user_input: str, 
        context_analysis: Dict[str, Any], 
        user_prefs: Dict[str, Any], 
        tool_performance: Dict[str, Any], 
        available_tools: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate context-aware tool recommendations."""
        recommendations = []
        
        # Get tool requirements from context analysis
        tool_requirements = context_analysis.get("tool_requirements", {})
        must_have = tool_requirements.get("must_have", [])
        should_have = tool_requirements.get("should_have", [])
        nice_to_have = tool_requirements.get("nice_to_have", [])
        avoid = tool_requirements.get("avoid", [])
        
        # Filter available tools
        if available_tools:
            must_have = [tool for tool in must_have if tool in available_tools]
            should_have = [tool for tool in should_have if tool in available_tools]
            nice_to_have = [tool for tool in nice_to_have if tool in available_tools]
        
        # Create recommendations with priority and reasoning
        priority = 1
        
        # Must-have tools
        for tool_name in must_have:
            if tool_name not in avoid:
                recommendation = await self._create_tool_recommendation(
                    tool_name, priority, "essential", context_analysis, user_prefs, tool_performance
                )
                recommendations.append(recommendation)
                priority += 1
        
        # Should-have tools
        for tool_name in should_have:
            if tool_name not in avoid and tool_name not in [r["tool_name"] for r in recommendations]:
                recommendation = await self._create_tool_recommendation(
                    tool_name, priority, "recommended", context_analysis, user_prefs, tool_performance
                )
                recommendations.append(recommendation)
                priority += 1
        
        # Nice-to-have tools
        for tool_name in nice_to_have:
            if tool_name not in avoid and tool_name not in [r["tool_name"] for r in recommendations]:
                recommendation = await self._create_tool_recommendation(
                    tool_name, priority, "optional", context_analysis, user_prefs, tool_performance
                )
                recommendations.append(recommendation)
                priority += 1
        
        # Always include LLM provider if not already included
        if "llm_provider" not in [r["tool_name"] for r in recommendations]:
            recommendation = await self._create_tool_recommendation(
                "llm_provider", priority, "synthesis", context_analysis, user_prefs, tool_performance
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _create_tool_recommendation(
        self, 
        tool_name: str, 
        priority: int, 
        category: str, 
        context_analysis: Dict[str, Any], 
        user_prefs: Dict[str, Any], 
        tool_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a detailed tool recommendation."""
        recommendation = {
            "tool_name": tool_name,
            "priority": priority,
            "category": category,
            "reasoning": f"Recommended as {category} tool for this query type",
            "confidence": 0.8,
            "parameters": {},
            "expected_outcome": f"Execute {tool_name} to fulfill query requirements"
        }
        
        # Enhance with performance data
        if tool_name in tool_performance:
            perf_data = tool_performance[tool_name]
            recommendation["performance_data"] = perf_data
            recommendation["confidence"] = min(0.95, 0.6 + (perf_data.get("success_rate", 0.5) * 0.4))
        
        # Enhance with user preferences
        if tool_name in user_prefs.get("preferred_tools", {}):
            recommendation["user_preference"] = user_prefs["preferred_tools"][tool_name]
            recommendation["confidence"] = min(0.95, recommendation["confidence"] + 0.1)
        
        # Add tool-specific parameters
        recommendation["parameters"] = self._get_tool_parameters(tool_name, context_analysis, user_prefs)
        
        return recommendation
    
    def _get_tool_parameters(
        self, 
        tool_name: str, 
        context_analysis: Dict[str, Any], 
        user_prefs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get optimized parameters for a tool based on context and preferences."""
        base_params = {}
        
        if tool_name == "web_search":
            base_params = {
                "num_results": 10,
                "search_provider": "auto"
            }
            
            # Adjust based on complexity
            complexity = context_analysis.get("query_classification", {}).get("complexity_level", "moderate")
            if complexity == "complex":
                base_params["num_results"] = 15
            elif complexity == "simple":
                base_params["num_results"] = 5
        
        elif tool_name == "real_time_data":
            base_params = {
                "data_type": "auto"
            }
            
            # Add location if relevant
            if context_analysis.get("user_context", {}).get("location_relevant", False):
                user_metadata = context_analysis.get("user_metadata", {})
                location = user_metadata.get("location", {})
                if location:
                    base_params["location"] = location.get("city", "")
        
        elif tool_name == "location_tool":
            base_params = {
                "ip_address": None
            }
        
        elif tool_name == "llm_provider":
            base_params = {
                "model": "auto",
                "temperature": 0.7
            }
            
            # Adjust temperature based on user preferences
            response_format = user_prefs.get("response_preferences", {}).get("response_format", "conversational")
            if response_format == "technical":
                base_params["temperature"] = 0.3
            elif response_format == "creative":
                base_params["temperature"] = 0.9
        
        return base_params
    
    async def _create_adaptive_tool_plan(
        self, 
        tool_recommendations: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any], 
        user_prefs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create an adaptive tool execution plan."""
        adaptive_plan = []
        
        # Sort recommendations by priority and confidence
        sorted_recommendations = sorted(
            tool_recommendations, 
            key=lambda x: (x["priority"], -x["confidence"])
        )
        
        for rec in sorted_recommendations:
            plan_item = {
                "tool_name": rec["tool_name"],
                "priority": rec["priority"],
                "reasoning": rec["reasoning"],
                "parameters": rec["parameters"],
                "expected_outcome": rec["expected_outcome"],
                "confidence": rec["confidence"],
                "category": rec["category"],
                "adaptation_rules": self._get_adaptation_rules(rec, context_analysis, user_prefs)
            }
            
            adaptive_plan.append(plan_item)
        
        return adaptive_plan
    
    def _get_adaptation_rules(
        self, 
        recommendation: Dict[str, Any], 
        context_analysis: Dict[str, Any], 
        user_prefs: Dict[str, Any]
    ) -> List[str]:
        """Get adaptation rules for the tool recommendation."""
        rules = []
        
        tool_name = recommendation["tool_name"]
        
        # Context-based adaptation rules
        if context_analysis.get("user_context", {}).get("location_relevant", False):
            if tool_name == "web_search":
                rules.append("Enhance search query with location context")
            elif tool_name == "real_time_data":
                rules.append("Use location-specific parameters")
        
        if context_analysis.get("user_context", {}).get("time_relevant", False):
            if tool_name == "web_search":
                rules.append("Add time context to search query")
        
        # User preference-based adaptation rules
        detail_level = user_prefs.get("response_preferences", {}).get("detail_level", "medium")
        if detail_level == "high" and tool_name == "web_search":
            rules.append("Increase number of results for detailed response")
        elif detail_level == "low" and tool_name == "web_search":
            rules.append("Reduce number of results for concise response")
        
        return rules
    
    def _calculate_selection_confidence(
        self, 
        context_analysis: Dict[str, Any], 
        user_prefs: Dict[str, Any]
    ) -> float:
        """Calculate confidence in the tool selection."""
        base_confidence = 0.7
        
        # Increase confidence based on context clarity
        complexity = context_analysis.get("query_classification", {}).get("complexity_level", "moderate")
        if complexity == "simple":
            base_confidence += 0.1
        elif complexity == "complex":
            base_confidence -= 0.1
        
        # Increase confidence based on user preference data
        if user_prefs.get("preferred_tools"):
            base_confidence += 0.1
        
        # Increase confidence based on clear tool requirements
        tool_requirements = context_analysis.get("tool_requirements", {})
        if tool_requirements.get("must_have"):
            base_confidence += 0.1
        
        return min(0.95, max(0.3, base_confidence))
    
    def _generate_learning_insights(self, user_id: str, query_pattern: str) -> Dict[str, Any]:
        """Generate insights for learning and improvement."""
        insights = {
            "user_id": user_id,
            "query_pattern": query_pattern,
            "preference_confidence": 0.5,
            "learning_opportunities": [],
            "recommendations": []
        }
        
        # Analyze user preferences
        user_prefs = self.user_preferences.get(user_id, {})
        if user_prefs.get("preferred_tools"):
            insights["preference_confidence"] = 0.8
        else:
            insights["learning_opportunities"].append("Collect more user preference data")
        
        # Analyze query patterns
        if query_pattern in self.query_patterns:
            pattern_count = len(self.query_patterns[query_pattern])
            if pattern_count > 5:
                insights["recommendations"].append("Sufficient data for pattern-based optimization")
            else:
                insights["learning_opportunities"].append("Need more examples of this query pattern")
        
        return insights
    
    async def _update_learning_data(
        self, 
        user_id: str, 
        user_input: str, 
        context_analysis: Dict[str, Any], 
        tool_recommendations: List[Dict[str, Any]]
    ) -> None:
        """Update learning data with new information."""
        # Update query patterns
        query_pattern = await self._analyze_query_pattern(user_input, context_analysis)
        if query_pattern not in self.query_patterns:
            self.query_patterns[query_pattern] = []
        
        self.query_patterns[query_pattern].append({
            "user_input": user_input,
            "context_analysis": context_analysis,
            "tool_recommendations": tool_recommendations,
            "timestamp": self._get_timestamp()
        })
        
        # Keep only recent patterns (last 100)
        if len(self.query_patterns[query_pattern]) > 100:
            self.query_patterns[query_pattern] = self.query_patterns[query_pattern][-100:]
    
    def _is_cache_valid(self, cached_data: Dict[str, Any]) -> bool:
        """Check if cached data is still valid."""
        import time
        timestamp = cached_data.get("timestamp", 0)
        return time.time() - timestamp < self.cache_ttl
    
    def _create_fallback_plan(self, user_input: str, available_tools: List[str] = None) -> List[Dict[str, Any]]:
        """Create a fallback tool plan when context analysis fails."""
        fallback_plan = []
        
        # Basic rule-based tool selection
        user_input_lower = user_input.lower()
        
        if any(keyword in user_input_lower for keyword in ["time", "date", "weather", "current"]):
            fallback_plan.append({
                "tool_name": "real_time_data",
                "priority": 1,
                "reasoning": "Real-time data query detected",
                "parameters": {"data_type": "auto"},
                "expected_outcome": "Current time/date/weather information"
            })
        
        if any(keyword in user_input_lower for keyword in ["near me", "local", "restaurant", "store"]):
            fallback_plan.append({
                "tool_name": "location_tool",
                "priority": 1,
                "reasoning": "Location-based query detected",
                "parameters": {"ip_address": None},
                "expected_outcome": "User location information"
            })
            fallback_plan.append({
                "tool_name": "web_search",
                "priority": 2,
                "reasoning": "Search for local information",
                "parameters": {"query": user_input, "num_results": 10},
                "expected_outcome": "Local business/information results"
            })
        
        if any(keyword in user_input_lower for keyword in ["what", "how", "why", "latest", "news"]):
            fallback_plan.append({
                "tool_name": "web_search",
                "priority": 1,
                "reasoning": "Information-seeking query detected",
                "parameters": {"query": user_input, "num_results": 10},
                "expected_outcome": "Relevant information and facts"
            })
        
        # Always add LLM provider
        fallback_plan.append({
            "tool_name": "llm_provider",
            "priority": 99,
            "reasoning": "Generate final response",
            "parameters": {"model": "auto", "temperature": 0.7},
            "expected_outcome": "Coherent response to user query"
        })
        
        return fallback_plan
    
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
                    "description": "Previous conversation messages for context"
                },
                "user_metadata": {
                    "type": "object",
                    "description": "User metadata and preferences"
                },
                "available_tools": {
                    "type": "array",
                    "description": "List of available tool names"
                }
            },
            "required": ["user_input"]
        }
