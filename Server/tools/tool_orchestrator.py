"""Intelligent tool orchestrator for multi-step reasoning and tool chaining."""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from .base import BaseTool
from tools.llm_tools import LLMProviderTool


class ToolOrchestrator(BaseTool):
    """Orchestrates multi-step tool execution with intelligent reasoning and chaining."""
    
    def __init__(self, llm_provider_tool: LLMProviderTool):
        super().__init__("tool_orchestrator", "Orchestrate multi-step tool execution with intelligent reasoning")
        self.category = "orchestration"
        self.llm_provider = llm_provider_tool
        
        # Tool execution history for learning and context
        self.execution_history: List[Dict[str, Any]] = []
        
        # Result validation criteria
        self.validation_criteria = {
            "web_search": {
                "min_results": 1,
                "required_fields": ["title", "url", "snippet"],
                "quality_threshold": 0.6
            },
            "real_time_data": {
                "required_fields": ["status", "data_type"],
                "success_status": "success"
            },
            "location_tool": {
                "required_fields": ["status", "location"],
                "success_status": "success"
            }
        }
    
    async def execute(
        self,
        tool_plan: List[Dict[str, Any]],
        state: Dict[str, Any],
        available_tools: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a multi-step tool plan with intelligent reasoning and chaining."""
        if not await self.validate_input(tool_plan=tool_plan, state=state, available_tools=available_tools):
            raise ValueError("Invalid input parameters")
        
        try:
            execution_results = {
                "status": "success",
                "execution_plan": tool_plan,
                "tool_results": {},
                "execution_log": [],
                "final_synthesis": None,
                "reasoning_chain": []
            }
            
            # Sort tools by priority
            sorted_tools = sorted(tool_plan, key=lambda x: x.get("priority", 99))
            
            print(f"🎭 Starting tool orchestration with {len(sorted_tools)} tools")
            
            # Execute tools in sequence with intelligent reasoning
            for i, tool_config in enumerate(sorted_tools):
                tool_name = tool_config["tool_name"]
                tool_priority = tool_config.get("priority", 99)
                tool_reasoning = tool_config.get("reasoning", "")
                
                print(f"🔧 Executing tool {i+1}/{len(sorted_tools)}: {tool_name} (priority: {tool_priority})")
                print(f"   Reasoning: {tool_reasoning}")
                
                # Check if tool is available
                if tool_name not in available_tools:
                    error_msg = f"Tool '{tool_name}' not available"
                    execution_results["execution_log"].append({
                        "step": i + 1,
                        "tool": tool_name,
                        "status": "error",
                        "error": error_msg
                    })
                    print(f"❌ {error_msg}")
                    continue
                
                # Enhance tool parameters based on previous results
                enhanced_params = await self._enhance_tool_parameters(
                    tool_config, execution_results["tool_results"], state
                )
                
                # Execute the tool
                tool_result = await self._execute_single_tool(
                    tool_name, enhanced_params, available_tools[tool_name]
                )
                
                # Validate tool result
                validation_result = await self._validate_tool_result(
                    tool_name, tool_result, tool_config
                )
                
                # Store result
                execution_results["tool_results"][tool_name] = tool_result
                execution_results["execution_log"].append({
                    "step": i + 1,
                    "tool": tool_name,
                    "status": "success" if validation_result["is_valid"] else "warning",
                    "validation": validation_result,
                    "result_summary": self._summarize_tool_result(tool_result)
                })
                
                # Add to reasoning chain
                execution_results["reasoning_chain"].append({
                    "step": i + 1,
                    "tool": tool_name,
                    "reasoning": tool_reasoning,
                    "result_quality": validation_result["quality_score"],
                    "next_action": self._determine_next_action(tool_result, validation_result, sorted_tools[i+1:])
                })
                
                # Check if we should continue or stop early
                if await self._should_stop_early(tool_result, validation_result, sorted_tools[i+1:]):
                    print(f"🛑 Early termination after {tool_name} - sufficient results obtained")
                    break
                
                # Update state with new results for next tools
                state = await self._update_state_with_results(state, tool_name, tool_result)
            
            # Perform final synthesis if multiple tools were executed
            if len(execution_results["tool_results"]) > 1:
                execution_results["final_synthesis"] = await self._synthesize_results(
                    execution_results["tool_results"], execution_results["reasoning_chain"]
                )
            
            # Store execution in history for learning
            self.execution_history.append({
                "timestamp": self._get_timestamp(),
                "tool_plan": tool_plan,
                "results": execution_results,
                "success": execution_results["status"] == "success"
            })
            
            print(f"✅ Tool orchestration completed: {len(execution_results['tool_results'])} tools executed")
            return execution_results
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "execution_plan": tool_plan,
                "tool_results": {},
                "execution_log": []
            }
    
    async def _enhance_tool_parameters(
        self, 
        tool_config: Dict[str, Any], 
        previous_results: Dict[str, Any], 
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance tool parameters based on previous results and context."""
        tool_name = tool_config["tool_name"]
        base_params = tool_config.get("parameters", {})
        enhanced_params = base_params.copy()
        
        # Tool-specific parameter enhancement
        if tool_name == "web_search":
            # Enhance search query with location from previous results
            if "location_tool" in previous_results:
                location_result = previous_results["location_tool"]
                if location_result.get("status") == "success":
                    location_data = location_result.get("location", {})
                    city = location_data.get("city")
                    if city and "near me" in enhanced_params.get("query", "").lower():
                        enhanced_params["query"] = enhanced_params["query"].replace("near me", f"in {city}")
                        print(f"   🔍 Enhanced search query with location: {enhanced_params['query']}")
            
            # Enhance search query with time context
            if "real_time_data" in previous_results:
                time_result = previous_results["real_time_data"]
                if time_result.get("status") == "success":
                    data_type = time_result.get("data_type", "")
                    if data_type == "time" and "today" not in enhanced_params.get("query", "").lower():
                        enhanced_params["query"] += " today"
                        print(f"   ⏰ Enhanced search query with time context: {enhanced_params['query']}")
        
        elif tool_name == "real_time_data":
            # Use location from previous results
            if "location_tool" in previous_results:
                location_result = previous_results["location_tool"]
                if location_result.get("status") == "success":
                    location_data = location_result.get("location", {})
                    city = location_data.get("city")
                    if city and not enhanced_params.get("location"):
                        enhanced_params["location"] = city
                        print(f"   📍 Enhanced real-time data with location: {city}")
        
        elif tool_name == "location_tool":
            # Use coordinates from state if available
            if state.get("latitude") and state.get("longitude"):
                enhanced_params["latitude"] = state.get("latitude")
                enhanced_params["longitude"] = state.get("longitude")
                enhanced_params.pop("ip_address", None)
                print(f"   📍 Enhanced location tool with coordinates from state: {state.get('latitude')}, {state.get('longitude')}")
        
        return enhanced_params
    
    async def _execute_single_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        tool_instance: Any
    ) -> Dict[str, Any]:
        """Execute a single tool with error handling."""
        try:
            print(f"   ⚙️ Executing {tool_name} with parameters: {parameters}")
            result = await tool_instance.execute(**parameters)
            print(f"   ✅ {tool_name} completed successfully")
            return result
        except Exception as e:
            print(f"   ❌ {tool_name} failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "tool": tool_name
            }
    
    async def _validate_tool_result(
        self, 
        tool_name: str, 
        result: Dict[str, Any], 
        tool_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate tool result quality and completeness."""
        validation_criteria = self.validation_criteria.get(tool_name, {})
        
        validation_result = {
            "is_valid": True,
            "quality_score": 1.0,
            "issues": [],
            "suggestions": []
        }
        
        # Check status
        if result.get("status") != validation_criteria.get("success_status", "success"):
            validation_result["is_valid"] = False
            validation_result["quality_score"] = 0.0
            validation_result["issues"].append(f"Tool returned status: {result.get('status')}")
            return validation_result
        
        # Check required fields
        required_fields = validation_criteria.get("required_fields", [])
        for field in required_fields:
            if field not in result:
                validation_result["issues"].append(f"Missing required field: {field}")
                validation_result["quality_score"] *= 0.8
        
        # Tool-specific validation
        if tool_name == "web_search":
            results = result.get("results", [])
            min_results = validation_criteria.get("min_results", 1)
            if len(results) < min_results:
                validation_result["issues"].append(f"Insufficient results: {len(results)} < {min_results}")
                validation_result["quality_score"] *= 0.6
                validation_result["suggestions"].append("Consider trying different search terms or providers")
            
            # Check result quality
            quality_threshold = validation_criteria.get("quality_threshold", 0.6)
            if validation_result["quality_score"] < quality_threshold:
                validation_result["is_valid"] = False
        
        elif tool_name == "real_time_data":
            data_type = result.get("data_type", "")
            if not data_type:
                validation_result["issues"].append("No data type specified")
                validation_result["quality_score"] *= 0.7
        
        elif tool_name == "location_tool":
            location = result.get("location", {})
            if not location.get("city") and not location.get("country"):
                validation_result["issues"].append("Insufficient location data")
                validation_result["quality_score"] *= 0.5
                validation_result["suggestions"].append("Try using IP-based location detection")
        
        return validation_result
    
    def _summarize_tool_result(self, result: Dict[str, Any]) -> str:
        """Create a brief summary of tool result."""
        status = result.get("status", "unknown")
        
        if status == "success":
            if "results" in result:
                num_results = len(result["results"])
                return f"Success: {num_results} results"
            elif "data_type" in result:
                data_type = result["data_type"]
                return f"Success: {data_type} data"
            elif "location" in result:
                location = result["location"]
                city = location.get("city", "Unknown")
                return f"Success: Location {city}"
            else:
                return "Success: Data retrieved"
        else:
            error = result.get("error", "Unknown error")
            return f"Error: {error[:50]}..."
    
    def _determine_next_action(
        self, 
        tool_result: Dict[str, Any], 
        validation_result: Dict[str, Any], 
        remaining_tools: List[Dict[str, Any]]
    ) -> str:
        """Determine the next action based on current tool result."""
        if not remaining_tools:
            return "complete"
        
        if not validation_result["is_valid"]:
            return "retry_or_fallback"
        
        if validation_result["quality_score"] < 0.7:
            return "enhance_or_supplement"
        
        return "continue"
    
    async def _should_stop_early(
        self, 
        tool_result: Dict[str, Any], 
        validation_result: Dict[str, Any], 
        remaining_tools: List[Dict[str, Any]]
    ) -> bool:
        """Determine if execution should stop early based on current results."""
        # Stop if we have high-quality results and remaining tools are low priority
        if validation_result["quality_score"] >= 0.9:
            if remaining_tools and all(tool.get("priority", 99) > 5 for tool in remaining_tools):
                return True
        
        # Stop if we have sufficient results for the query type
        if tool_result.get("status") == "success":
            # For real-time data queries, if we got good time/weather data, we might not need search
            if "real_time_data" in tool_result and validation_result["quality_score"] >= 0.8:
                if remaining_tools and all(tool["tool_name"] == "web_search" for tool in remaining_tools):
                    return True
        
        return False
    
    async def _update_state_with_results(
        self, 
        state: Dict[str, Any], 
        tool_name: str, 
        tool_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update state with tool results for use by subsequent tools."""
        # Update tool_results
        if "tool_results" not in state:
            state["tool_results"] = {}
        state["tool_results"][tool_name] = tool_result
        
        # Update specific state fields based on tool type
        if tool_name == "location_tool" and tool_result.get("status") == "success":
            state["user_location"] = tool_result.get("location", {})
        
        elif tool_name == "real_time_data" and tool_result.get("status") == "success":
            state["real_time_data"] = tool_result
            state["has_real_time_data"] = True
        
        elif tool_name == "web_search" and tool_result.get("status") == "success":
            state["search_results"] = tool_result.get("results", [])
            state["has_search_results"] = True
        
        return state
    
    async def _synthesize_results(
        self, 
        tool_results: Dict[str, Any], 
        reasoning_chain: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize results from multiple tools using LLM reasoning."""
        try:
            # Create synthesis prompt
            synthesis_prompt = self._create_synthesis_prompt(tool_results, reasoning_chain)
            
            messages = [
                {"role": "system", "content": synthesis_prompt},
                {"role": "user", "content": "Please synthesize the results from the executed tools."}
            ]
            
            # Use LLM for synthesis
            synthesis_result = await self.llm_provider.execute(
                messages=messages,
                provider="google",
                model="gemini-2.0-flash-exp",
                temperature=0.3,
                max_tokens=1024
            )
            
            return {
                "status": "success",
                "synthesis": synthesis_result,
                "tool_count": len(tool_results),
                "reasoning_steps": len(reasoning_chain)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "fallback_synthesis": "Multiple tools executed successfully"
            }
    
    def _create_synthesis_prompt(
        self, 
        tool_results: Dict[str, Any], 
        reasoning_chain: List[Dict[str, Any]]
    ) -> str:
        """Create a prompt for synthesizing tool results."""
        prompt = """You are an intelligent result synthesizer. Your job is to analyze the results from multiple tools and create a coherent summary.

Tool Execution Results:
"""
        
        for tool_name, result in tool_results.items():
            prompt += f"\n{tool_name.upper()}:\n"
            if result.get("status") == "success":
                if "results" in result:
                    prompt += f"  - Found {len(result['results'])} results\n"
                elif "data_type" in result:
                    prompt += f"  - Retrieved {result['data_type']} data\n"
                elif "location" in result:
                    location = result["location"]
                    prompt += f"  - Location: {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}\n"
            else:
                prompt += f"  - Error: {result.get('error', 'Unknown error')}\n"
        
        prompt += f"\nReasoning Chain ({len(reasoning_chain)} steps):\n"
        for step in reasoning_chain:
            prompt += f"  {step['step']}. {step['tool']}: {step['reasoning']}\n"
        
        prompt += """
Please provide a concise synthesis that:
1. Summarizes what information was successfully retrieved
2. Identifies any gaps or issues
3. Suggests how the results work together
4. Provides confidence level for the overall result

Keep the synthesis under 200 words and focus on the most important findings.
"""
        
        return prompt
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "tool_plan": {
                    "type": "array",
                    "description": "List of tools to execute with their configurations",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string"},
                            "priority": {"type": "integer"},
                            "reasoning": {"type": "string"},
                            "parameters": {"type": "object"}
                        }
                    }
                },
                "state": {
                    "type": "object",
                    "description": "Current state with user input and metadata"
                },
                "available_tools": {
                    "type": "object",
                    "description": "Dictionary of available tool instances"
                }
            },
            "required": ["tool_plan", "state", "available_tools"]
        }
