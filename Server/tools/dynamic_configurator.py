"""Dynamic tool configuration system that adapts tool parameters based on query complexity and available data."""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from .base import BaseTool
from tools.llm_tools import LLMProviderTool


class DynamicConfigurator(BaseTool):
    """Dynamically configures tool parameters based on query complexity, context, and available data."""
    
    def __init__(self, llm_provider_tool: LLMProviderTool):
        super().__init__("dynamic_configurator", "Dynamic tool configuration based on context and complexity")
        self.category = "configuration"
        self.llm_provider = llm_provider_tool
        
        # Configuration templates for different scenarios
        self.configuration_templates = {
            "simple_query": {
                "web_search": {"num_results": 5, "search_provider": "auto"},
                "real_time_data": {"data_type": "auto"},
                "llm_provider": {"temperature": 0.7, "max_tokens": 1024}
            },
            "moderate_query": {
                "web_search": {"num_results": 10, "search_provider": "auto"},
                "real_time_data": {"data_type": "auto"},
                "llm_provider": {"temperature": 0.7, "max_tokens": 2048}
            },
            "complex_query": {
                "web_search": {"num_results": 15, "search_provider": "auto"},
                "real_time_data": {"data_type": "auto"},
                "llm_provider": {"temperature": 0.5, "max_tokens": 4096}
            },
            "location_sensitive": {
                "web_search": {"num_results": 8, "search_provider": "auto"},
                "location_tool": {"ip_address": None},
                "real_time_data": {"data_type": "auto", "location": None}
            },
            "time_sensitive": {
                "web_search": {"num_results": 12, "search_provider": "auto"},
                "real_time_data": {"data_type": "auto"},
                "llm_provider": {"temperature": 0.6, "max_tokens": 1536}
            }
        }
        
        # Performance optimization rules
        self.optimization_rules = {
            "high_volume": {
                "web_search": {"num_results": 8, "search_provider": "duckduckgo"},
                "llm_provider": {"temperature": 0.5, "max_tokens": 1024}
            },
            "high_accuracy": {
                "web_search": {"num_results": 15, "search_provider": "auto"},
                "llm_provider": {"temperature": 0.3, "max_tokens": 3072}
            },
            "fast_response": {
                "web_search": {"num_results": 5, "search_provider": "duckduckgo"},
                "llm_provider": {"temperature": 0.7, "max_tokens": 512}
            }
        }
    
    async def execute(
        self,
        tool_plan: List[Dict[str, Any]],
        context_analysis: Dict[str, Any],
        available_data: Dict[str, Any] = None,
        performance_requirements: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Dynamically configure tool parameters based on context and requirements."""
        if not await self.validate_input(tool_plan=tool_plan, context_analysis=context_analysis):
            raise ValueError("Invalid input parameters")
        
        try:
            # Analyze configuration requirements
            config_requirements = await self._analyze_configuration_requirements(
                tool_plan, context_analysis, available_data, performance_requirements
            )
            
            # Generate dynamic configurations
            dynamic_configs = await self._generate_dynamic_configurations(
                tool_plan, config_requirements, available_data
            )
            
            # Optimize configurations
            optimized_configs = await self._optimize_configurations(
                dynamic_configs, performance_requirements, context_analysis
            )
            
            # Validate configurations
            validated_configs = await self._validate_configurations(
                optimized_configs, tool_plan, available_data
            )
            
            return {
                "status": "success",
                "original_plan": tool_plan,
                "configuration_requirements": config_requirements,
                "dynamic_configurations": validated_configs,
                "optimization_applied": performance_requirements or {},
                "configuration_confidence": self._calculate_config_confidence(validated_configs, context_analysis)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "fallback_configurations": self._create_fallback_configurations(tool_plan)
            }
    
    async def _analyze_configuration_requirements(
        self, 
        tool_plan: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any], 
        available_data: Dict[str, Any] = None,
        performance_requirements: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze what configuration requirements are needed."""
        requirements = {
            "complexity_level": context_analysis.get("query_classification", {}).get("complexity_level", "moderate"),
            "urgency": context_analysis.get("query_classification", {}).get("urgency", "medium"),
            "data_availability": self._assess_data_availability(available_data or {}),
            "performance_mode": self._determine_performance_mode(performance_requirements),
            "tool_specific_requirements": {},
            "resource_constraints": self._assess_resource_constraints(context_analysis, available_data)
        }
        
        # Analyze tool-specific requirements
        for tool_config in tool_plan:
            tool_name = tool_config["tool_name"]
            requirements["tool_specific_requirements"][tool_name] = await self._analyze_tool_requirements(
                tool_name, tool_config, context_analysis, available_data
            )
        
        return requirements
    
    def _assess_data_availability(self, available_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess what data is available for configuration."""
        availability = {
            "location_data": bool(available_data.get("location")),
            "timezone_data": bool(available_data.get("timezone")),
            "user_preferences": bool(available_data.get("user_preferences")),
            "conversation_history": bool(available_data.get("conversation_history")),
            "previous_results": bool(available_data.get("previous_results")),
            "metadata": bool(available_data.get("metadata"))
        }
        
        # Calculate overall data richness
        available_count = sum(1 for v in availability.values() if v)
        availability["richness_score"] = available_count / len(availability)
        
        return availability
    
    def _determine_performance_mode(self, performance_requirements: Dict[str, Any] = None) -> str:
        """Determine the performance optimization mode."""
        if not performance_requirements:
            return "balanced"
        
        # Check for specific performance requirements
        if performance_requirements.get("max_latency") and performance_requirements["max_latency"] < 2.0:
            return "fast_response"
        elif performance_requirements.get("accuracy_priority") and performance_requirements["accuracy_priority"] > 0.8:
            return "high_accuracy"
        elif performance_requirements.get("volume_priority") and performance_requirements["volume_priority"] > 0.8:
            return "high_volume"
        else:
            return "balanced"
    
    async def _analyze_tool_requirements(
        self, 
        tool_name: str, 
        tool_config: Dict[str, Any], 
        context_analysis: Dict[str, Any], 
        available_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze specific requirements for a tool."""
        requirements = {
            "base_parameters": tool_config.get("parameters", {}),
            "context_enhancements": [],
            "data_dependencies": [],
            "optimization_opportunities": []
        }
        
        # Tool-specific requirement analysis
        if tool_name == "web_search":
            requirements.update(await self._analyze_web_search_requirements(
                tool_config, context_analysis, available_data
            ))
        elif tool_name == "real_time_data":
            requirements.update(await self._analyze_real_time_requirements(
                tool_config, context_analysis, available_data
            ))
        elif tool_name == "location_tool":
            requirements.update(await self._analyze_location_requirements(
                tool_config, context_analysis, available_data
            ))
        elif tool_name == "llm_provider":
            requirements.update(await self._analyze_llm_requirements(
                tool_config, context_analysis, available_data
            ))
        
        return requirements
    
    async def _analyze_web_search_requirements(
        self, 
        tool_config: Dict[str, Any], 
        context_analysis: Dict[str, Any], 
        available_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze web search specific requirements."""
        requirements = {
            "query_enhancement_needed": False,
            "location_context_available": False,
            "time_context_available": False,
            "complexity_adjustment": "none"
        }
        
        # Check for query enhancement opportunities
        base_query = tool_config.get("parameters", {}).get("query", "")
        if "near me" in base_query.lower() and available_data and available_data.get("location"):
            requirements["query_enhancement_needed"] = True
            requirements["location_context_available"] = True
        
        if any(keyword in base_query.lower() for keyword in ["today", "current", "latest"]) and available_data:
            requirements["time_context_available"] = True
        
        # Check complexity adjustment needs
        complexity = context_analysis.get("query_classification", {}).get("complexity_level", "moderate")
        if complexity == "complex":
            requirements["complexity_adjustment"] = "increase_results"
        elif complexity == "simple":
            requirements["complexity_adjustment"] = "decrease_results"
        
        return requirements
    
    async def _analyze_real_time_requirements(
        self, 
        tool_config: Dict[str, Any], 
        context_analysis: Dict[str, Any], 
        available_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze real-time data specific requirements."""
        requirements = {
            "location_enhancement_needed": False,
            "timezone_enhancement_needed": False,
            "data_type_optimization": "auto"
        }
        
        # Check for location enhancement
        if available_data and available_data.get("location"):
            requirements["location_enhancement_needed"] = True
        
        # Check for timezone enhancement
        if available_data and available_data.get("timezone"):
            requirements["timezone_enhancement_needed"] = True
        
        # Determine optimal data type
        user_context = context_analysis.get("user_context", {})
        if user_context.get("time_relevant", False):
            requirements["data_type_optimization"] = "time"
        elif user_context.get("location_relevant", False):
            requirements["data_type_optimization"] = "weather"
        
        return requirements
    
    async def _analyze_location_requirements(
        self, 
        tool_config: Dict[str, Any], 
        context_analysis: Dict[str, Any], 
        available_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze location tool specific requirements."""
        requirements = {
            "ip_detection_needed": True,
            "coordinate_enhancement_available": False,
            "address_enhancement_available": False
        }
        
        # Check for coordinate enhancement (direct coordinates)
        if available_data and (available_data.get("latitude") or available_data.get("longitude")):
            requirements["coordinate_enhancement_available"] = True
            requirements["ip_detection_needed"] = False
        
        # Check for coordinate enhancement (nested in location object)
        elif available_data and available_data.get("location"):
            location_data = available_data["location"]
            if isinstance(location_data, dict) and (location_data.get("latitude") or location_data.get("longitude")):
                requirements["coordinate_enhancement_available"] = True
                requirements["ip_detection_needed"] = False
        
        # Check for address enhancement
        if available_data and available_data.get("address"):
            requirements["address_enhancement_available"] = True
            requirements["ip_detection_needed"] = False
        
        return requirements
    
    async def _analyze_llm_requirements(
        self, 
        tool_config: Dict[str, Any], 
        context_analysis: Dict[str, Any], 
        available_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze LLM provider specific requirements."""
        requirements = {
            "temperature_optimization": "default",
            "token_limit_optimization": "default",
            "model_selection": "auto",
            "context_enhancement_needed": False
        }
        
        # Analyze complexity for temperature optimization
        complexity = context_analysis.get("query_classification", {}).get("complexity_level", "moderate")
        if complexity == "complex":
            requirements["temperature_optimization"] = "lower"  # More focused
        elif complexity == "simple":
            requirements["temperature_optimization"] = "higher"  # More creative
        
        # Analyze urgency for token limit optimization
        urgency = context_analysis.get("query_classification", {}).get("urgency", "medium")
        if urgency == "high":
            requirements["token_limit_optimization"] = "shorter"  # Faster response
        elif urgency == "low":
            requirements["token_limit_optimization"] = "longer"  # More detailed
        
        # Check for context enhancement
        if available_data and available_data.get("conversation_history"):
            requirements["context_enhancement_needed"] = True
        
        return requirements
    
    def _assess_resource_constraints(
        self, 
        context_analysis: Dict[str, Any], 
        available_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Assess resource constraints for configuration."""
        constraints = {
            "api_quota_available": True,  # Assume available unless specified
            "processing_time_limit": 30.0,  # Default 30 seconds
            "memory_constraints": False,
            "network_constraints": False
        }
        
        # Adjust based on context
        complexity = context_analysis.get("query_classification", {}).get("complexity_level", "moderate")
        if complexity == "complex":
            constraints["processing_time_limit"] = 45.0  # Allow more time for complex queries
        
        return constraints
    
    async def _generate_dynamic_configurations(
        self, 
        tool_plan: List[Dict[str, Any]], 
        config_requirements: Dict[str, Any], 
        available_data: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Generate dynamic configurations for each tool."""
        dynamic_configs = []
        
        for tool_config in tool_plan:
            tool_name = tool_config["tool_name"]
            tool_requirements = config_requirements["tool_specific_requirements"].get(tool_name, {})
            
            # Start with base configuration
            dynamic_config = tool_config.copy()
            dynamic_config["dynamic_parameters"] = tool_config.get("parameters", {}).copy()
            
            # Apply dynamic enhancements
            if tool_name == "web_search":
                dynamic_config["dynamic_parameters"] = await self._configure_web_search(
                    dynamic_config["dynamic_parameters"], tool_requirements, available_data
                )
            elif tool_name == "real_time_data":
                dynamic_config["dynamic_parameters"] = await self._configure_real_time_data(
                    dynamic_config["dynamic_parameters"], tool_requirements, available_data
                )
            elif tool_name == "location_tool":
                dynamic_config["dynamic_parameters"] = await self._configure_location_tool(
                    dynamic_config["dynamic_parameters"], tool_requirements, available_data
                )
            elif tool_name == "llm_provider":
                dynamic_config["dynamic_parameters"] = await self._configure_llm_provider(
                    dynamic_config["dynamic_parameters"], tool_requirements, available_data
                )
            
            # Add configuration metadata
            dynamic_config["configuration_metadata"] = {
                "enhancements_applied": tool_requirements.get("context_enhancements", []),
                "data_dependencies_met": tool_requirements.get("data_dependencies", []),
                "optimization_opportunities": tool_requirements.get("optimization_opportunities", [])
            }
            
            dynamic_configs.append(dynamic_config)
        
        return dynamic_configs
    
    async def _configure_web_search(
        self, 
        base_params: Dict[str, Any], 
        requirements: Dict[str, Any], 
        available_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Configure web search parameters dynamically."""
        enhanced_params = base_params.copy()
        
        # Apply complexity adjustment
        complexity_adjustment = requirements.get("complexity_adjustment", "none")
        if complexity_adjustment == "increase_results":
            enhanced_params["num_results"] = min(20, enhanced_params.get("num_results", 10) + 5)
        elif complexity_adjustment == "decrease_results":
            enhanced_params["num_results"] = max(3, enhanced_params.get("num_results", 10) - 3)
        
        # Apply query enhancement
        if requirements.get("query_enhancement_needed", False) and available_data:
            query = enhanced_params.get("query", "")
            
            # Add location context
            if requirements.get("location_context_available", False):
                location = available_data.get("location", {})
                city = location.get("city", "")
                if city and "near me" in query.lower():
                    enhanced_params["query"] = query.replace("near me", f"in {city}")
            
            # Add time context
            if requirements.get("time_context_available", False):
                if "today" not in query.lower() and any(keyword in query.lower() for keyword in ["current", "latest"]):
                    enhanced_params["query"] = query + " today"
        
        return enhanced_params
    
    async def _configure_real_time_data(
        self, 
        base_params: Dict[str, Any], 
        requirements: Dict[str, Any], 
        available_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Configure real-time data parameters dynamically."""
        enhanced_params = base_params.copy()
        
        # Apply data type optimization
        data_type_optimization = requirements.get("data_type_optimization", "auto")
        if data_type_optimization != "auto":
            enhanced_params["data_type"] = data_type_optimization
        
        # Add location enhancement
        if requirements.get("location_enhancement_needed", False) and available_data:
            location = available_data.get("location", {})
            city = location.get("city", "")
            if city:
                enhanced_params["location"] = city
        
        return enhanced_params
    
    async def _configure_location_tool(
        self, 
        base_params: Dict[str, Any], 
        requirements: Dict[str, Any], 
        available_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Configure location tool parameters dynamically."""
        enhanced_params = base_params.copy()
        
        # Use coordinate enhancement if available
        if requirements.get("coordinate_enhancement_available", False) and available_data:
            enhanced_params["latitude"] = available_data.get("latitude")
            enhanced_params["longitude"] = available_data.get("longitude")
            enhanced_params.pop("ip_address", None)  # Remove IP if coordinates available
        
        # Use address enhancement if available
        elif requirements.get("address_enhancement_available", False) and available_data:
            enhanced_params["address"] = available_data.get("address")
            enhanced_params.pop("ip_address", None)  # Remove IP if address available
        
        # Check for location data in nested structure (from frontend metadata)
        elif available_data and available_data.get("location"):
            location_data = available_data["location"]
            if isinstance(location_data, dict):
                if location_data.get("latitude") and location_data.get("longitude"):
                    enhanced_params["latitude"] = location_data["latitude"]
                    enhanced_params["longitude"] = location_data["longitude"]
                    enhanced_params.pop("ip_address", None)
                    print(f"   📍 Enhanced location tool with coordinates: {location_data['latitude']}, {location_data['longitude']}")
                elif location_data.get("address"):
                    enhanced_params["address"] = location_data["address"]
                    enhanced_params.pop("ip_address", None)
        
        return enhanced_params
    
    async def _configure_llm_provider(
        self, 
        base_params: Dict[str, Any], 
        requirements: Dict[str, Any], 
        available_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Configure LLM provider parameters dynamically."""
        enhanced_params = base_params.copy()
        
        # Apply temperature optimization
        temp_optimization = requirements.get("temperature_optimization", "default")
        if temp_optimization == "lower":
            enhanced_params["temperature"] = 0.3
        elif temp_optimization == "higher":
            enhanced_params["temperature"] = 0.9
        
        # Apply token limit optimization
        token_optimization = requirements.get("token_limit_optimization", "default")
        if token_optimization == "shorter":
            enhanced_params["max_tokens"] = 1024
        elif token_optimization == "longer":
            enhanced_params["max_tokens"] = 4096
        
        return enhanced_params
    
    async def _optimize_configurations(
        self, 
        dynamic_configs: List[Dict[str, Any]], 
        performance_requirements: Dict[str, Any] = None,
        context_analysis: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Apply performance optimizations to configurations."""
        if not performance_requirements:
            return dynamic_configs
        
        performance_mode = self._determine_performance_mode(performance_requirements)
        optimization_template = self.optimization_rules.get(performance_mode, {})
        
        optimized_configs = []
        for config in dynamic_configs:
            tool_name = config["tool_name"]
            optimized_config = config.copy()
            
            # Apply performance optimizations
            if tool_name in optimization_template:
                tool_optimizations = optimization_template[tool_name]
                for param, value in tool_optimizations.items():
                    if param in optimized_config["dynamic_parameters"]:
                        optimized_config["dynamic_parameters"][param] = value
                        optimized_config["configuration_metadata"]["optimizations_applied"] = tool_optimizations
            
            optimized_configs.append(optimized_config)
        
        return optimized_configs
    
    async def _validate_configurations(
        self, 
        optimized_configs: List[Dict[str, Any]], 
        original_plan: List[Dict[str, Any]], 
        available_data: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Validate the optimized configurations."""
        validated_configs = []
        
        for config in optimized_configs:
            tool_name = config["tool_name"]
            params = config["dynamic_parameters"]
            
            # Tool-specific validation
            validation_result = await self._validate_tool_configuration(tool_name, params, available_data)
            
            if validation_result["is_valid"]:
                config["validation_status"] = "valid"
                config["validation_issues"] = []
            else:
                config["validation_status"] = "invalid"
                config["validation_issues"] = validation_result["issues"]
                # Apply fallback configuration
                config["dynamic_parameters"] = self._get_fallback_parameters(tool_name)
            
            validated_configs.append(config)
        
        return validated_configs
    
    async def _validate_tool_configuration(
        self, 
        tool_name: str, 
        params: Dict[str, Any], 
        available_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Validate configuration for a specific tool."""
        validation_result = {"is_valid": True, "issues": []}
        
        if tool_name == "web_search":
            # Validate web search parameters
            if params.get("num_results", 0) < 1 or params.get("num_results", 0) > 50:
                validation_result["is_valid"] = False
                validation_result["issues"].append("Invalid num_results: must be between 1 and 50")
        
        elif tool_name == "real_time_data":
            # Validate real-time data parameters
            valid_data_types = ["auto", "time", "weather", "date"]
            if params.get("data_type") not in valid_data_types:
                validation_result["is_valid"] = False
                validation_result["issues"].append(f"Invalid data_type: must be one of {valid_data_types}")
        
        elif tool_name == "llm_provider":
            # Validate LLM parameters
            if params.get("temperature", 0) < 0 or params.get("temperature", 0) > 2:
                validation_result["is_valid"] = False
                validation_result["issues"].append("Invalid temperature: must be between 0 and 2")
            
            if params.get("max_tokens", 0) < 1 or params.get("max_tokens", 0) > 8192:
                validation_result["is_valid"] = False
                validation_result["issues"].append("Invalid max_tokens: must be between 1 and 8192")
        
        return validation_result
    
    def _get_fallback_parameters(self, tool_name: str) -> Dict[str, Any]:
        """Get fallback parameters for a tool if validation fails."""
        fallback_templates = {
            "web_search": {"num_results": 10, "search_provider": "auto"},
            "real_time_data": {"data_type": "auto"},
            "location_tool": {"ip_address": None},
            "llm_provider": {"temperature": 0.7, "max_tokens": 2048}
        }
        
        return fallback_templates.get(tool_name, {})
    
    def _calculate_config_confidence(
        self, 
        validated_configs: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any]
    ) -> float:
        """Calculate confidence in the dynamic configurations."""
        if not validated_configs:
            return 0.0
        
        # Base confidence
        base_confidence = 0.7
        
        # Increase confidence for valid configurations
        valid_count = sum(1 for config in validated_configs if config.get("validation_status") == "valid")
        validation_confidence = valid_count / len(validated_configs)
        
        # Increase confidence for complex queries (more configuration needed)
        complexity = context_analysis.get("query_classification", {}).get("complexity_level", "moderate")
        if complexity == "complex":
            complexity_bonus = 0.1
        elif complexity == "simple":
            complexity_bonus = 0.05
        else:
            complexity_bonus = 0.0
        
        final_confidence = base_confidence + (validation_confidence * 0.2) + complexity_bonus
        return min(0.95, max(0.3, final_confidence))
    
    def _create_fallback_configurations(self, tool_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create fallback configurations when dynamic configuration fails."""
        fallback_configs = []
        
        for tool_config in tool_plan:
            tool_name = tool_config["tool_name"]
            fallback_config = tool_config.copy()
            fallback_config["dynamic_parameters"] = self._get_fallback_parameters(tool_name)
            fallback_config["configuration_metadata"] = {
                "enhancements_applied": [],
                "data_dependencies_met": [],
                "optimization_opportunities": [],
                "fallback_used": True
            }
            fallback_configs.append(fallback_config)
        
        return fallback_configs
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "type": "object",
            "properties": {
                "tool_plan": {
                    "type": "array",
                    "description": "List of tools to configure"
                },
                "context_analysis": {
                    "type": "object",
                    "description": "Context analysis results"
                },
                "available_data": {
                    "type": "object",
                    "description": "Available data for configuration"
                },
                "performance_requirements": {
                    "type": "object",
                    "description": "Performance requirements and constraints"
                }
            },
            "required": ["tool_plan", "context_analysis"]
        }
