"""Chat Agent implementation for main conversation orchestration."""

import subprocess
from typing import Dict, Any, List, Optional, AsyncIterator, Self
from datetime import datetime
from langgraph.graph import StateGraph, END
from .base import BaseAgent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .communication import AgentMessage, MessageType, Priority, AgentOutput
    from .output_passing import OutputType, DataFormat
from graphs.state import ChatState
from tools.llm_tools import LLMProviderTool, ConversationTool, ResponseSynthesisTool
from tools.file_tools import DocumentProcessorTool, ImageAnalysisTool
from tools.web_tools import WebSearchTool, SearchResultAnalyzerTool, RealTimeDataTool
from tools.image_tools import ImageGenerationTool
from tools.metadata_tools import TimezoneTool, LocationTool, DateTimeTool, UserAgentTool
from tools.intent_analysis_tool import IntentAnalysisTool
from tools.tool_orchestrator import ToolOrchestrator
from tools.context_aware_selector import ContextAwareSelector
from tools.dynamic_configurator import DynamicConfigurator


class ChatAgent(BaseAgent):
    """Main conversation orchestrator and coordinator."""
    
    def __init__(self, providers=None):
        self.providers = providers
        super().__init__("chat_agent", "Main conversation orchestrator and coordinator")
        self.category = "conversation"
        self.priority = 1  # Highest priority
    
    def _initialize_tools(self) -> None:
        """Initialize tools available to this agent."""
        # Initialize LLM provider first for intent analysis
        llm_provider_tool = LLMProviderTool(providers=self.providers)
        
        self.tools = {
            "llm_provider": llm_provider_tool,
            "intent_analysis": IntentAnalysisTool(llm_provider_tool),
            "tool_orchestrator": ToolOrchestrator(llm_provider_tool),
            "context_aware_selector": ContextAwareSelector(llm_provider_tool),
            "dynamic_configurator": DynamicConfigurator(llm_provider_tool),
            "conversation": ConversationTool(),
            "response_synthesis": ResponseSynthesisTool(),
            "document_processor": DocumentProcessorTool(),
            "image_analyzer": ImageAnalysisTool(),
            "web_search": WebSearchTool(),
            "search_analyzer": SearchResultAnalyzerTool(),
            "real_time_data": RealTimeDataTool(),
            "image_generator": ImageGenerationTool(),
            "timezone_tool": TimezoneTool(),
            "location_tool": LocationTool(),
            "datetime_tool": DateTimeTool(),
            "user_agent_tool": UserAgentTool()
        }
    
    def _build_graph(self) -> None:
        """Build the agent's LangGraph workflow."""
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("analyze_input", self._analyze_input)
        workflow.add_node("llm_intent_analysis", self._llm_intent_analysis)
        workflow.add_node("context_aware_selection", self._context_aware_selection)
        workflow.add_node("dynamic_configuration", self._dynamic_configuration)
        workflow.add_node("collect_metadata", self._collect_metadata)
        workflow.add_node("determine_agent_collaboration", self._determine_agent_collaboration)
        workflow.add_node("coordinate_with_agents", self._coordinate_with_agents)
        workflow.add_node("tool_orchestration", self._tool_orchestration)
        workflow.add_node("process_files", self._process_files)
        workflow.add_node("web_search", self._web_search)
        workflow.add_node("real_time_data", self._real_time_data)
        workflow.add_node("get_location", self._get_location)
        workflow.add_node("generate_image", self._generate_image)
        workflow.add_node("execute_llm", self._execute_llm)
        workflow.add_node("synthesize_response", self._synthesize_response)
        workflow.add_node("finalize_response", self._finalize_response)
        
        # Add edges
        workflow.set_entry_point("analyze_input")
        workflow.add_edge("analyze_input", "llm_intent_analysis")
        workflow.add_edge("llm_intent_analysis", "context_aware_selection")
        workflow.add_edge("context_aware_selection", "dynamic_configuration")
        workflow.add_edge("dynamic_configuration", "collect_metadata")
        workflow.add_edge("collect_metadata", "determine_agent_collaboration")
        
        # Conditional routing based on collaboration needs
        workflow.add_conditional_edges(
            "determine_agent_collaboration",
            self._route_based_on_collaboration,
            {
                "collaborate": "coordinate_with_agents",
                "direct": "route_to_tools"
            }
        )
        
        # Add routing node for direct processing
        workflow.add_node("route_to_tools", self._route_to_tools)
        workflow.add_conditional_edges(
            "route_to_tools",
            self._route_to_appropriate_tool,
            {
                "orchestrate": "tool_orchestration",
                "files": "process_files",
                "search": "web_search",
                "real_time": "real_time_data",
                "location": "get_location",
                "image": "generate_image",
                "llm": "execute_llm"
            }
        )
        
        workflow.add_edge("coordinate_with_agents", "synthesize_response")
        workflow.add_edge("tool_orchestration", "synthesize_response")
        workflow.add_edge("process_files", "execute_llm")
        workflow.add_edge("web_search", "execute_llm")
        workflow.add_edge("real_time_data", "execute_llm")
        workflow.add_edge("get_location", "execute_llm")
        workflow.add_edge("generate_image", "execute_llm")
        workflow.add_edge("execute_llm", "synthesize_response")
        workflow.add_edge("synthesize_response", "finalize_response")
        workflow.add_edge("finalize_response", END)
        

        self.graph = workflow.compile()
        # Save the graph as PNG in assets folder
        # try:
        #     import os
        #     from PIL import Image
        #     import io
        #     # Create assets directory if it doesn't exist
        #     assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
        #     os.makedirs(assets_dir, exist_ok=True)
        #     # Generate and save the graph
        #     graph_png = self.graph.get_graph().draw_mermaid_png()
        #     graph_path = os.path.join(assets_dir, "1S_new_chat_agent_workflow.png")
        #     with open(graph_path, "wb") as f:
        #         f.write(graph_png)
        #     print(f":white_check_mark: Chat agent workflow graph saved to: {graph_path}")
        # except Exception as e:
        #     print(f":warning: Could not save workflow graph: {e}")









    async def process(self, state: ChatState) -> ChatState:
        """Process the current state and return updated state."""
        try:
            if not await self.validate_state(state):
                raise ValueError("Invalid state for ChatAgent")


            
            # Run the graph
            result = await self.graph.ainvoke(state)
            
            return result
        
        except Exception as e:
            print(f"❌ ChatAgent error: {e}")
            import traceback
            traceback.print_exc()
            return await self.handle_error(e, state)
    
    async def stream(self, state: ChatState) -> AsyncIterator[str]:
        """Stream processing results."""
        try:
            if not await self.validate_state(state):
                yield "Error: Invalid state for ChatAgent"
                return
            
            # Run the graph with streaming
            async for chunk in self.graph.astream(state):
                # Only yield the final response to avoid duplication
                if "finalize_response" in chunk:
                    response = chunk["finalize_response"].get("final_response", "")
                    if response:
                        yield response
        
        except Exception as e:
            yield f"Error in ChatAgent: {str(e)}"
    
    async def _analyze_input(self, state: ChatState) -> ChatState:
        """Analyze user input to determine required tools and processing."""
        user_input = state.get("user_input", "")
        
        # Basic analysis for initial state setup
        analysis = {
            "has_files": len(state.get("attachments", [])) > 0,
            "needs_file_processing": len(state.get("attachments", [])) > 0,
            "user_input_length": len(user_input),
            "contains_questions": "?" in user_input,
            "contains_commands": any(word in user_input.lower() for word in ["show", "find", "get", "search", "tell"])
        }
        
        state["metadata"]["input_analysis"] = analysis
        return state
    
    async def _llm_intent_analysis(self, state: ChatState) -> ChatState:
        """Perform LLM-powered intent analysis and tool planning."""
        user_input = state.get("user_input", "")
        
        try:
            # Get conversation history for context
            conversation_history = []
            messages = state.get("messages", [])
            for msg in messages[-5:]:  # Last 5 messages for context
                if hasattr(msg, 'content'):
                    conversation_history.append({
                        "role": getattr(msg, 'type', 'user'),
                        "content": msg.content
                    })
            
            # Get available metadata
            available_metadata = state.get("metadata", {}).get("user_metadata", {})
            
            # Perform LLM intent analysis
            intent_tool = self.tools["intent_analysis"]
            analysis_result = await intent_tool.execute(
                user_input=user_input,
                conversation_history=conversation_history,
                available_metadata=available_metadata
            )
            
            if analysis_result.get("status") == "success":
                # Store the LLM analysis results
                state["metadata"]["llm_intent_analysis"] = analysis_result["intent_analysis"]
                state["metadata"]["tool_plan"] = analysis_result["tool_plan"]
                state["metadata"]["analysis_confidence"] = analysis_result["confidence"]
                state["metadata"]["analysis_reasoning"] = analysis_result["reasoning"]
                
                # Update the basic analysis with LLM insights
                llm_analysis = analysis_result["intent_analysis"]
                state["metadata"]["input_analysis"].update({
                    "needs_web_search": any(tool["tool_name"] == "web_search" for tool in analysis_result["tool_plan"]),
                    "needs_real_time_data": any(tool["tool_name"] == "real_time_data" for tool in analysis_result["tool_plan"]),
                    "needs_image_generation": any(tool["tool_name"] == "image_generator" for tool in analysis_result["tool_plan"]),
                    "intent": llm_analysis.get("intent_classification", {}).get("primary_intent", "conversational"),
                    "entities": llm_analysis.get("entity_extraction", {}),
                    "complexity": llm_analysis.get("intent_classification", {}).get("complexity", "moderate"),
                    "requires_metadata": analysis_result["intent_analysis"].get("requires_metadata", False),
                    "metadata_needed": analysis_result["intent_analysis"].get("metadata_needed", [])
                })
                
                print(f"🧠 LLM Intent Analysis completed:")
                print(f"   - Primary Intent: {llm_analysis.get('intent_classification', {}).get('primary_intent', 'unknown')}")
                print(f"   - Tool Plan: {len(analysis_result['tool_plan'])} tools planned")
                print(f"   - Confidence: {analysis_result['confidence']}")
                
            else:
                # Fallback to rule-based analysis
                print(f"⚠️ LLM Intent Analysis failed, using fallback: {analysis_result.get('error', 'Unknown error')}")
                state["metadata"]["llm_intent_analysis"] = analysis_result.get("fallback_analysis", {})
                state["metadata"]["tool_plan"] = analysis_result.get("fallback_analysis", {}).get("tool_plan", [])
                state["metadata"]["analysis_confidence"] = 0.5
                state["metadata"]["analysis_reasoning"] = "Fallback analysis due to LLM failure"
                
                # Update with fallback analysis
                fallback_analysis = analysis_result.get("fallback_analysis", {})
                state["metadata"]["input_analysis"].update({
                    "needs_web_search": any(tool["tool_name"] == "web_search" for tool in fallback_analysis.get("tool_plan", [])),
                    "needs_real_time_data": any(tool["tool_name"] == "real_time_data" for tool in fallback_analysis.get("tool_plan", [])),
                    "needs_image_generation": any(tool["tool_name"] == "image_generator" for tool in fallback_analysis.get("tool_plan", [])),
                    "intent": fallback_analysis.get("intent_classification", {}).get("primary_intent", "conversational"),
                    "entities": fallback_analysis.get("entity_extraction", {}),
                    "complexity": fallback_analysis.get("intent_classification", {}).get("complexity", "moderate")
                })
            
            return state
            
        except Exception as e:
            print(f"❌ LLM Intent Analysis error: {str(e)}")
            # Fallback to basic rule-based analysis
            state["metadata"]["llm_intent_analysis"] = {"error": str(e)}
            state["metadata"]["tool_plan"] = []
            state["metadata"]["analysis_confidence"] = 0.3
            state["metadata"]["analysis_reasoning"] = f"Error in LLM analysis: {str(e)}"
            
            # Use original rule-based methods as fallback
            state["metadata"]["input_analysis"].update({
            "needs_web_search": self._detect_search_intent(user_input),
            "needs_real_time_data": self._is_real_time_query(user_input),
            "needs_image_generation": self._detect_image_intent(user_input),
            "intent": self._classify_intent(user_input),
            "entities": self._extract_entities(user_input),
            "complexity": self._assess_complexity(user_input)
            })
            
            return state
    
    async def _context_aware_selection(self, state: ChatState) -> ChatState:
        """Perform context-aware tool selection based on user history and preferences."""
        user_input = state.get("user_input", "")
        
        try:
            # Get conversation history for context
            conversation_history = []
            messages = state.get("messages", [])
            for msg in messages[-5:]:  # Last 5 messages for context
                if hasattr(msg, 'content'):
                    conversation_history.append({
                        "role": getattr(msg, 'type', 'user'),
                        "content": msg.content
                    })
            
            # Get available metadata and user preferences
            available_metadata = state.get("metadata", {}).get("user_metadata", {})
            available_tools = list(self.tools.keys())
            
            # Perform context-aware selection
            selector_tool = self.tools["context_aware_selector"]
            selection_result = await selector_tool.execute(
                user_input=user_input,
                conversation_history=conversation_history,
                user_metadata=available_metadata,
                available_tools=available_tools
            )
            
            if selection_result.get("status") == "success":
                # Store the context-aware selection results
                state["metadata"]["context_aware_selection"] = selection_result
                state["metadata"]["adaptive_tool_plan"] = selection_result.get("adaptive_plan", [])
                state["metadata"]["selection_confidence"] = selection_result.get("confidence", 0.8)
                
                print(f"🎯 Context-aware selection completed:")
                print(f"   - Selection confidence: {selection_result.get('confidence', 0.8)}")
                print(f"   - Adaptive plan: {len(selection_result.get('adaptive_plan', []))} tools")
                
            else:
                # Fallback to LLM intent analysis results
                print(f"⚠️ Context-aware selection failed, using LLM intent analysis: {selection_result.get('error', 'Unknown error')}")
                state["metadata"]["context_aware_selection"] = {"error": selection_result.get("error", "Unknown error")}
                state["metadata"]["adaptive_tool_plan"] = state.get("metadata", {}).get("tool_plan", [])
                state["metadata"]["selection_confidence"] = 0.5
            
            return state
            
        except Exception as e:
            print(f"❌ Context-aware selection error: {str(e)}")
            # Fallback to LLM intent analysis results
            state["metadata"]["context_aware_selection"] = {"error": str(e)}
            state["metadata"]["adaptive_tool_plan"] = state.get("metadata", {}).get("tool_plan", [])
            state["metadata"]["selection_confidence"] = 0.3
            return state
    
    async def _dynamic_configuration(self, state: ChatState) -> ChatState:
        """Dynamically configure tool parameters based on context and complexity."""
        try:
            # Get the adaptive tool plan from context-aware selection
            adaptive_plan = state.get("metadata", {}).get("adaptive_tool_plan", [])
            context_analysis = state.get("metadata", {}).get("llm_intent_analysis", {})
            
            if not adaptive_plan:
                print(f"⚠️ No adaptive plan available, skipping dynamic configuration")
                return state
            
            # Get available data for configuration
            available_data = {
                "location": state.get("metadata", {}).get("user_metadata", {}).get("location"),
                "timezone": state.get("metadata", {}).get("user_metadata", {}).get("timezone"),
                "conversation_history": state.get("messages", [])[-3:] if state.get("messages") else [],
                "previous_results": state.get("tool_results", {}),
                "metadata": state.get("metadata", {}),
                # Add direct access to frontend metadata
                "latitude": state.get("latitude"),
                "longitude": state.get("longitude"),
                "address": state.get("address")
            }
            
            # Define performance requirements based on context
            performance_requirements = {
                "max_latency": 30.0,  # 30 seconds max
                "accuracy_priority": 0.8,
                "volume_priority": 0.6
            }
            
            # Perform dynamic configuration
            configurator_tool = self.tools["dynamic_configurator"]
            config_result = await configurator_tool.execute(
                tool_plan=adaptive_plan,
                context_analysis=context_analysis,
                available_data=available_data,
                performance_requirements=performance_requirements
            )
            
            if config_result.get("status") == "success":
                # Store the dynamic configuration results
                state["metadata"]["dynamic_configuration"] = config_result
                state["metadata"]["configured_tool_plan"] = config_result.get("dynamic_configurations", [])
                state["metadata"]["configuration_confidence"] = config_result.get("configuration_confidence", 0.8)
                
                print(f"⚙️ Dynamic configuration completed:")
                print(f"   - Configuration confidence: {config_result.get('configuration_confidence', 0.8)}")
                print(f"   - Configured tools: {len(config_result.get('dynamic_configurations', []))}")
                
            else:
                # Fallback to original adaptive plan
                print(f"⚠️ Dynamic configuration failed, using original plan: {config_result.get('error', 'Unknown error')}")
                state["metadata"]["dynamic_configuration"] = {"error": config_result.get("error", "Unknown error")}
                state["metadata"]["configured_tool_plan"] = adaptive_plan
                state["metadata"]["configuration_confidence"] = 0.5
            
            return state
            
        except Exception as e:
            print(f"❌ Dynamic configuration error: {str(e)}")
            # Fallback to original adaptive plan
            state["metadata"]["dynamic_configuration"] = {"error": str(e)}
            state["metadata"]["configured_tool_plan"] = state.get("metadata", {}).get("adaptive_tool_plan", [])
            state["metadata"]["configuration_confidence"] = 0.3
            return state
    
    async def _tool_orchestration(self, state: ChatState) -> ChatState:
        """Orchestrate multi-step tool execution with intelligent reasoning and chaining."""
        try:
            # Get the configured tool plan
            configured_plan = state.get("metadata", {}).get("configured_tool_plan", [])
            
            if not configured_plan:
                print(f"⚠️ No configured tool plan available, skipping orchestration")
                return state
            
            # Prepare tool plan for orchestration
            orchestration_plan = []
            for tool_config in configured_plan:
                orchestration_plan.append({
                    "tool_name": tool_config["tool_name"],
                    "priority": tool_config.get("priority", 99),
                    "reasoning": tool_config.get("reasoning", ""),
                    "parameters": tool_config.get("dynamic_parameters", tool_config.get("parameters", {}))
                })
            
            # Perform tool orchestration
            orchestrator_tool = self.tools["tool_orchestrator"]
            orchestration_result = await orchestrator_tool.execute(
                tool_plan=orchestration_plan,
                state=state,
                available_tools=self.tools
            )
            
            if orchestration_result.get("status") == "success":
                # Store orchestration results
                state["metadata"]["tool_orchestration"] = orchestration_result
                state["tool_results"] = orchestration_result.get("tool_results", {})
                state["metadata"]["execution_log"] = orchestration_result.get("execution_log", [])
                state["metadata"]["reasoning_chain"] = orchestration_result.get("reasoning_chain", [])
                
                # Update state with orchestration results
                if orchestration_result.get("final_synthesis"):
                    state["metadata"]["orchestration_synthesis"] = orchestration_result["final_synthesis"]
                
                print(f"🎭 Tool orchestration completed:")
                print(f"   - Tools executed: {len(orchestration_result.get('tool_results', {}))}")
                print(f"   - Execution log: {len(orchestration_result.get('execution_log', []))} entries")
                
            else:
                # Fallback to individual tool execution
                print(f"⚠️ Tool orchestration failed, using individual execution: {orchestration_result.get('error', 'Unknown error')}")
                state["metadata"]["tool_orchestration"] = {"error": orchestration_result.get("error", "Unknown error")}
                # Continue with individual tool execution in the workflow
            
            return state
            
        except Exception as e:
            print(f"❌ Tool orchestration error: {str(e)}")
            # Fallback to individual tool execution
            state["metadata"]["tool_orchestration"] = {"error": str(e)}
        return state
    
    async def _collect_metadata(self, state: ChatState) -> ChatState:
        """Collect user metadata for enhanced search and responses."""
        try:
            # Check if we need metadata for this query using LLM analysis
            llm_analysis = state.get("metadata", {}).get("llm_intent_analysis", {})
            analysis = state.get("metadata", {}).get("input_analysis", {})
            user_input = state.get("user_input", "").lower()
            
            # Use LLM analysis to determine metadata needs
            needs_metadata = (
                analysis.get("requires_metadata", False) or
                any(keyword in user_input for keyword in [
                "near me", "local", "weather", "time", "date", "stores", "restaurants",
                "current", "today", "now", "location", "where", "nearby", "my current",
                "what's my", "my location", "my date", "my time", "current location",
                "where am i", "what's my current"
                ]) or 
                analysis.get("needs_web_search", False) or 
                analysis.get("needs_real_time_data", False)
            )
            
            print(f"🔍 Metadata collection needed: {needs_metadata}")
            print(f"🔍 User input: {user_input}")
            print(f"🔍 Analysis: {analysis}")
            
            if needs_metadata:
                # Try to get metadata agent from registry
                try:
                    from agents.metadata_agent import MetadataAgent
                    metadata_agent = MetadataAgent()
                    
                    # Create metadata state
                    metadata_state = {
                        "user_input": state.get("user_input", ""),
                        "current_agent": "metadata_agent",
                        "session_id": state.get("session_id", ""),
                        "ip_address": state.get("ip_address"),
                        "user_agent": state.get("user_agent"),
                        "client_hints": state.get("client_hints"),
                        "timezone_input": state.get("timezone_input"),
                        "latitude": state.get("latitude"),
                        "longitude": state.get("longitude"),
                        "address": state.get("address"),
                        "metadata": {}
                    }
                    
                    print(f"📱 Processing metadata with MetadataAgent...")
                    # Process metadata
                    metadata_result = await metadata_agent.process(metadata_state)
                    state["metadata"]["user_metadata"] = metadata_result.get("metadata", {})
                    print(f"✅ Metadata collected: {bool(state['metadata']['user_metadata'])}")
                    
                except Exception as e:
                    print(f"⚠️ MetadataAgent failed, using fallback: {e}")
                    # Fallback to basic metadata collection
                    state["metadata"]["user_metadata"] = await self._collect_basic_metadata(state)
            else:
                # No metadata needed for this query
                state["metadata"]["user_metadata"] = {"status": "skipped", "reason": "not_needed"}
                print(f"⏭️ Metadata collection skipped")
            
            return state
            
        except Exception as e:
            # Fallback to basic metadata collection
            state["metadata"]["user_metadata"] = await self._collect_basic_metadata(state)
            if "tool_errors" not in state:
                state["tool_errors"] = {}
            state["tool_errors"]["metadata_collection"] = str(e)
            print(f"❌ Metadata collection error: {e}")
            return state
    
    async def _collect_basic_metadata(self, state: ChatState) -> Dict[str, Any]:
        """Collect basic metadata as fallback."""
        try:
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "session_id": state.get("session_id", ""),
                "timezone": "UTC",  # Default timezone
                "datetime": datetime.now().isoformat(),
                "source": "fallback"
            }
            
            # Add timezone from frontend if available
            if state.get("timezone_input"):
                metadata["timezone"] = {
                    "value": state.get("timezone_input"),
                    "source": "frontend"
                }
                print(f"✅ Timezone from frontend: {state.get('timezone_input')}")
            
            # Add location from frontend if available
            if state.get("latitude") and state.get("longitude"):
                # Use LocationTool to reverse geocode coordinates to get city/country
                try:
                    location_tool = self.tools.get("location_tool")
                    if location_tool:
                        location_result = await location_tool.execute(
                            latitude=state.get("latitude"),
                            longitude=state.get("longitude")
                        )
                        if location_result.get("status") == "success":
                            metadata["location"] = location_result.get("location", {})
                            print(f"✅ Location from frontend with reverse geocoding: {location_result.get('location', {}).get('value', {}).get('city', 'Unknown')}, {location_result.get('location', {}).get('value', {}).get('country', 'Unknown')}")
                        else:
                            # Fallback to basic coordinates
                            metadata["location"] = {
                                "value": {
                                    "lat": state.get("latitude"),
                                    "lon": state.get("longitude"),
                                    "city": "Unknown",
                                    "country": "Unknown"
                                },
                                "source": "frontend-coordinates"
                            }
                            print(f"⚠️ Location reverse geocoding failed, using coordinates only: {state.get('latitude')}, {state.get('longitude')}")
                    else:
                        # Fallback to basic coordinates
                        metadata["location"] = {
                            "value": {
                                "lat": state.get("latitude"),
                                "lon": state.get("longitude"),
                                "city": "Unknown",
                                "country": "Unknown"
                            },
                            "source": "frontend-coordinates"
                        }
                        print(f"⚠️ LocationTool not available, using coordinates only: {state.get('latitude')}, {state.get('longitude')}")
                except Exception as e:
                    # Fallback to basic coordinates
                    metadata["location"] = {
                        "value": {
                            "lat": state.get("latitude"),
                            "lon": state.get("longitude"),
                            "city": "Unknown",
                            "country": "Unknown"
                        },
                        "source": "frontend-coordinates"
                    }
                    print(f"⚠️ Location reverse geocoding error: {e}, using coordinates only: {state.get('latitude')}, {state.get('longitude')}")
            
            # Add IP-based location if available and no frontend location
            elif state.get("ip_address"):
                try:
                    location_tool = self.tools.get("location_tool")
                    if location_tool:
                        location_result = await location_tool.execute(
                            ip_address=state.get("ip_address")
                        )
                        if location_result.get("status") == "success":
                            metadata["location"] = location_result.get("location", {})
                            print(f"✅ Location from IP: {location_result.get('location', {}).get('city', 'Unknown')}")
                except Exception:
                    pass  # Ignore location errors in fallback
            
            return metadata
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _route_to_tools(self, state: ChatState) -> ChatState:
        """Route to appropriate tools based on LLM analysis and tool plan."""
        tool_plan = state.get("metadata", {}).get("tool_plan", [])
        analysis = state.get("metadata", {}).get("input_analysis", {})
        
        # Use LLM-generated tool plan if available
        if tool_plan:
            # Sort tools by priority
            sorted_tools = sorted(tool_plan, key=lambda x: x.get("priority", 99))
            active_tools = [tool["tool_name"] for tool in sorted_tools if tool["tool_name"] in self.tools]
            
            print(f"🎯 Using LLM tool plan: {[tool['tool_name'] for tool in sorted_tools]}")
        else:
            # Fallback to rule-based tool selection
            active_tools = []
        
        if analysis.get("needs_file_processing", False):
            active_tools.append("document_processor")
            active_tools.append("image_analyzer")
        
        if analysis.get("needs_web_search", False):
            active_tools.append("web_search")
            active_tools.append("search_analyzer")
        
        if analysis.get("needs_real_time_data", False):
            active_tools.append("real_time_data")
        
        if analysis.get("needs_image_generation", False):
            active_tools.append("image_generator")
        
            print(f"🎯 Using fallback tool selection: {active_tools}")
        
        # Always add response synthesis at the end
        if "response_synthesis" not in active_tools:
            active_tools.append("response_synthesis")
        
        state["active_tools"] = active_tools
        state["tool_plan"] = tool_plan  # Store the full plan for reference
        return state
    
    async def _process_files(self, state: ChatState) -> ChatState:
        """Process uploaded files."""
        attachments = state.get("attachments", [])
        processed_files = {}
        
        for attachment in attachments:
            try:
                if attachment.get("mime_type", "").startswith("image/"):
                    # Process image
                    tool = self.tools["image_analyzer"]
                    result = await tool.execute(
                        image_data=attachment["data"],
                        filename=attachment["filename"],
                        mime_type=attachment["mime_type"],
                        analysis_type="describe"
                    )
                    processed_files[attachment["filename"]] = result
                else:
                    # Process document
                    tool = self.tools["document_processor"]
                    result = await tool.execute(
                        file_data=attachment["data"],
                        filename=attachment["filename"],
                        mime_type=attachment["mime_type"],
                        processing_type="extract"
                    )
                    processed_files[attachment["filename"]] = result
            
            except Exception as e:
                if "tool_errors" not in state:
                    state["tool_errors"] = {}
                state["tool_errors"][f"file_processing_{attachment['filename']}"] = str(e)
        
        state["processed_files"] = processed_files
        return state
    
    async def _real_time_data(self, state: ChatState) -> ChatState:
        """Process real-time data queries like time, weather, etc."""
        user_input = state.get("user_input", "")
        tool_plan = state.get("tool_plan", [])
        
        try:
            # Get real-time data parameters from tool plan if available
            real_time_tool_plan = None
            for tool in tool_plan:
                if tool["tool_name"] == "real_time_data":
                    real_time_tool_plan = tool
                    break
            
            # Use enhanced parameters from tool plan or check if this is a real-time query
            if real_time_tool_plan or self._is_real_time_query(user_input):
                print(f"🕐 Processing real-time query: {user_input}")
                
                # Get user metadata for enhanced responses
                user_metadata = state.get("metadata", {}).get("user_metadata", {})
                print(f"🕐 User metadata available: {bool(user_metadata)}")
                print(f"🕐 User metadata content: {user_metadata}")
                
                # Also check if metadata is in the state directly
                if not user_metadata:
                    print(f"🕐 Checking state directly for metadata...")
                    print(f"🕐 State keys: {list(state.keys())}")
                    print(f"🕐 Metadata keys: {list(state.get('metadata', {}).keys())}")
                    print(f"🕐 Timezone input: {state.get('timezone_input')}")
                    print(f"🕐 Latitude: {state.get('latitude')}")
                    print(f"🕐 Longitude: {state.get('longitude')}")
                
                # Location queries are now handled in the specific location-only section below
                
                # Handle time/date queries
                elif any(keyword in user_input.lower() for keyword in ["time", "date", "current time", "current date", "what time", "what date"]):
                    timezone_str = None
                    
                    # Try to get timezone from user metadata first
                    if user_metadata.get("timezone"):
                        timezone_data = user_metadata["timezone"]
                        timezone_str = timezone_data["value"]
                        print(f"✅ Timezone from user metadata: {timezone_str}")
                    # Fallback to state directly
                    elif state.get("timezone_input"):
                        timezone_str = state.get("timezone_input")
                        print(f"✅ Timezone from state: {timezone_str}")
                    
                    if timezone_str:
                        # Use datetime tool to get current time in user's timezone
                        datetime_tool = self.tools["datetime_tool"]
                        datetime_result = await datetime_tool.execute(
                            timezone_str=timezone_str,
                            format_type="readable"
                        )
                        
                        if datetime_result["status"] == "success":
                            current_time = datetime_result["datetime"]["value"]
                            day_of_week = datetime_result["datetime"]["day_of_week"]
                            
                            time_response = f"Current date and time in your timezone ({timezone_str}):\n\n**{current_time}**\n\nToday is **{day_of_week}**."
                            state["real_time_data"] = {
                                "status": "success",
                                "data_type": "datetime",
                                "response": time_response,
                                "datetime": datetime_result["datetime"]
                            }
                            state["has_real_time_data"] = True
                            print(f"✅ Time data provided for timezone: {timezone_str}")
                        else:
                            state["real_time_data"] = {
                                "status": "error",
                                "error": "Unable to get current time information."
                            }
                    else:
                        # Fallback to UTC
                        datetime_tool = self.tools["datetime_tool"]
                        datetime_result = await datetime_tool.execute(format_type="readable")
                        
                        if datetime_result["status"] == "success":
                            current_time = datetime_result["datetime"]["value"]
                            day_of_week = datetime_result["datetime"]["day_of_week"]
                            
                            time_response = f"Current date and time (UTC):\n\n**{current_time}**\n\nToday is **{day_of_week}**.\n\n*Note: Your timezone information is not available. Please enable location services for more accurate local time.*"
                            state["real_time_data"] = {
                                "status": "success",
                                "data_type": "datetime",
                                "response": time_response,
                                "datetime": datetime_result["datetime"]
                            }
                            state["has_real_time_data"] = True
                            print("✅ Time data provided (UTC fallback)")
                        else:
                            state["real_time_data"] = {
                                "status": "error",
                                "error": "Unable to get current time information."
                            }
                
                # Handle location-only queries
                elif any(keyword in user_input.lower() for keyword in ["current location", "my location", "where am i", "whats my location", "what's my location", "address", "exact address", "accurate address", "precise address", "detailed address", "street address", "full address", "complete address", "more accurate", "more exact"]):
                    # Get location data
                    location_data = None
                    if user_metadata.get("location"):
                        location_data = user_metadata["location"]["value"]
                    elif state.get("latitude") and state.get("longitude"):
                        # Try to reverse geocode coordinates to get city/country
                        try:
                            location_tool = self.tools.get("location_tool")
                            if location_tool:
                                location_result = await location_tool.execute(
                                    latitude=state.get("latitude"),
                                    longitude=state.get("longitude")
                                )
                                if location_result.get("status") == "success":
                                    location_data = location_result.get("location", {}).get("value", {})
                                else:
                                    # Fallback to basic coordinates
                                    location_data = {
                                        "lat": state.get("latitude"),
                                        "lon": state.get("longitude"),
                                        "city": "Unknown",
                                        "country": "Unknown"
                                    }
                            else:
                                # Fallback to basic coordinates
                                location_data = {
                                    "lat": state.get("latitude"),
                                    "lon": state.get("longitude"),
                                    "city": "Unknown",
                                    "country": "Unknown"
                                }
                        except Exception as e:
                            # Fallback to basic coordinates
                            location_data = {
                                "lat": state.get("latitude"),
                                "lon": state.get("longitude"),
                                "city": "Unknown",
                                "country": "Unknown"
                            }
                    
                    if location_data and location_data.get("city") != "Unknown":
                        city = location_data.get("city", "Unknown")
                        country = location_data.get("country", "Unknown")
                        region = location_data.get("region", "")
                        
                        # Check if we have detailed street address information
                        street_address = location_data.get("street_address", "")
                        street_number = location_data.get("street_number", "")
                        street_name = location_data.get("street_name", "")
                        neighbourhood = location_data.get("neighbourhood", "")
                        postcode = location_data.get("postcode", "")
                        formatted_address = location_data.get("formatted_address", "")
                        
                        # Build detailed location response
                        if formatted_address:
                            # Use the complete formatted address if available
                            location_response = f"Your current location is:\n\n**{formatted_address}**"
                        elif street_address:
                            # Build address from components
                            location_response = f"Your current location is:\n\n**{street_address}"
                            if neighbourhood and neighbourhood != city:
                                location_response += f", {neighbourhood}"
                            location_response += f", {city}"
                            if region and region != city:
                                location_response += f", {region}"
                            location_response += f", {country}**"
                        else:
                            # Fallback to basic city/country
                            location_response = f"Your current location is **{city}"
                            if region and region != city:
                                location_response += f", {region}"
                            location_response += f", {country}**"
                        
                        # Add coordinates if available
                        if location_data.get("lat") and location_data.get("lon"):
                            location_response += f"\n\nCoordinates: {location_data['lat']:.4f}, {location_data['lon']:.4f}"
                        
                        # Add quality information if available
                        address_quality = location_data.get("address_quality", {})
                        if address_quality.get("quality_level"):
                            quality_level = address_quality.get("quality_level", "")
                            quality_percentage = address_quality.get("quality_percentage", 0)
                            location_response += f"\n\n*Address accuracy: {quality_level} ({quality_percentage}%)*"
                        
                        state["real_time_data"] = {
                            "status": "success",
                            "data_type": "location",
                            "response": location_response
                        }
                        state["has_real_time_data"] = True
                        print("✅ Location data provided")
                    else:
                        state["real_time_data"] = {
                            "status": "error",
                            "error": "Location data not available. Please enable location services and grant permission to access your current location."
                            }
                
                # Handle combined queries (location + time/date)
                elif any(keyword in user_input.lower() for keyword in ["my current", "what's my", "whats my", "my date", "my time"]):
                    response_parts = []
                    
                    # Add location if available
                    location_data = None
                    if user_metadata.get("location"):
                        location_data = user_metadata["location"]["value"]
                    elif state.get("latitude") and state.get("longitude"):
                        # Try to reverse geocode coordinates to get city/country
                        try:
                            location_tool = self.tools.get("location_tool")
                            if location_tool:
                                location_result = await location_tool.execute(
                                    latitude=state.get("latitude"),
                                    longitude=state.get("longitude")
                                )
                                if location_result.get("status") == "success":
                                    location_data = location_result.get("location", {}).get("value", {})
                                else:
                                    # Fallback to basic coordinates
                                    location_data = {
                                        "lat": state.get("latitude"),
                                        "lon": state.get("longitude"),
                                        "city": "Unknown",
                                        "country": "Unknown"
                                    }
                            else:
                                # Fallback to basic coordinates
                                location_data = {
                                    "lat": state.get("latitude"),
                                    "lon": state.get("longitude"),
                                    "city": "Unknown",
                                    "country": "Unknown"
                                }
                        except Exception as e:
                            # Fallback to basic coordinates
                            location_data = {
                                "lat": state.get("latitude"),
                                "lon": state.get("longitude"),
                                "city": "Unknown",
                                "country": "Unknown"
                            }
                    
                    if location_data:
                        city = location_data.get("city", "Unknown")
                        country = location_data.get("country", "Unknown")
                        lat = location_data.get("lat")
                        lon = location_data.get("lon")
                        
                        # Check for detailed address information
                        formatted_address = location_data.get("formatted_address", "")
                        street_address = location_data.get("street_address", "")
                        neighbourhood = location_data.get("neighbourhood", "")
                        
                        if formatted_address:
                            response_parts.append(f"**Location:** {formatted_address}")
                        elif street_address:
                            location_str = street_address
                            if neighbourhood and neighbourhood != city:
                                location_str += f", {neighbourhood}"
                            location_str += f", {city}, {country}"
                            response_parts.append(f"**Location:** {location_str}")
                        elif city != "Unknown" and country != "Unknown":
                            response_parts.append(f"**Location:** {city}, {country}")
                        elif lat and lon:
                            response_parts.append(f"**Location:** Coordinates {lat:.4f}, {lon:.4f}")
                        else:
                            response_parts.append(f"**Location:** Location data available but details not accessible")
                    
                    # Add time if available
                    timezone_str = None
                    if user_metadata.get("timezone"):
                        timezone_str = user_metadata["timezone"]["value"]
                    elif state.get("timezone_input"):
                        timezone_str = state.get("timezone_input")
                    
                    if timezone_str:
                        datetime_tool = self.tools["datetime_tool"]
                        datetime_result = await datetime_tool.execute(
                            timezone_str=timezone_str,
                            format_type="readable"
                        )
                        
                        if datetime_result["status"] == "success":
                            current_time = datetime_result["datetime"]["value"]
                            day_of_week = datetime_result["datetime"]["day_of_week"]
                            response_parts.append(f"**Date & Time:** {current_time} ({day_of_week})")
                    
                    if response_parts:
                        combined_response = "Here's your current information:\n\n" + "\n\n".join(response_parts)
                        state["real_time_data"] = {
                            "status": "success",
                            "data_type": "combined",
                            "response": combined_response
                        }
                        state["has_real_time_data"] = True
                        print("✅ Combined location and time data provided")
                    else:
                        state["real_time_data"] = {
                            "status": "error",
                            "error": "Location and time data not available. Please enable location services and grant permission."
                        }
                
                # Use real-time tool for other queries
                else:
                    real_time_tool = self.tools["real_time_data"]
                    real_time_result = await real_time_tool.execute(
                        query=user_input,
                        data_type="auto"
                    )
                    
                    if real_time_result["status"] == "success":
                        state["real_time_data"] = real_time_result
                        state["has_real_time_data"] = True
                    else:
                        state["real_time_data"] = {
                            "status": "error",
                            "error": real_time_result.get("error", "Real-time data failed")
                        }
                
                if "tool_results" not in state:
                    state["tool_results"] = {}
                state["tool_results"]["real_time_data"] = state["real_time_data"]
                
        
        except Exception as e:
            print(f"❌ Real-time data error: {e}")
            if "tool_errors" not in state:
                state["tool_errors"] = {}
            state["tool_errors"]["real_time_data"] = str(e)
            state["real_time_data"] = {
                "status": "error",
                "error": str(e)
            }
        
        return state
    
    def _is_real_time_query(self, query: str) -> bool:
        """Check if query requires real-time data."""
        query_lower = query.lower()
        real_time_keywords = [
            "current", "recent", "latest", "today", "now", "live", "real-time",
            "weather", "temperature", "forecast", "rain", "sunny", "cloudy",
            "date", "time", "what time", "what date", "current time", "current date",
            "clock", "hour", "minute", "second", "location", "where am i", "my location",
            "current location", "what's my", "my current", "my date", "my time",
            "address", "exact address", "accurate address", "precise address", "detailed address",
            "street address", "full address", "complete address", "more accurate", "more exact"
        ]
        return any(keyword in query_lower for keyword in real_time_keywords)
    
    async def _enhance_query_with_metadata(self, query: str, state: ChatState) -> str:
        """Enhance search query with user metadata for better results."""
        try:
            # Get metadata from the state - it could be in different places
            user_metadata = state.get("metadata", {}).get("user_metadata", {})
            if not user_metadata:
                # Try to get metadata directly from state
                user_metadata = state.get("metadata", {})
            
            enhanced_query = query
            
            # Add location context for local queries
            if any(keyword in query.lower() for keyword in ["near me", "local", "nearby", "stores", "restaurants", "weather"]):
                location = user_metadata.get("location", {}).get("value", {})
                if location:
                    city = location.get("city")
                    country = location.get("country")
                    if city and country:
                        enhanced_query = f"{query} in {city}, {country}"
                    elif city:
                        enhanced_query = f"{query} in {city}"
            
            # Add time context for time-sensitive queries
            if any(keyword in query.lower() for keyword in ["today", "now", "current", "latest", "recent"]):
                datetime_info = user_metadata.get("datetime", {})
                if datetime_info:
                    current_date = datetime_info.get("value", "").split("T")[0]  # Get date part
                    if current_date:
                        enhanced_query = f"{query} {current_date}"
            
            # Add timezone context for time-related queries
            if any(keyword in query.lower() for keyword in ["time", "date", "schedule", "hours"]):
                timezone_info = user_metadata.get("timezone", {})
                if timezone_info:
                    timezone = timezone_info.get("value", "")
                    if timezone and timezone != "UTC":
                        enhanced_query = f"{query} {timezone}"
            
            # Store the enhancement for transparency
            state["query_enhancement"] = {
                "original_query": query,
                "enhanced_query": enhanced_query,
                "enhancements_applied": {
                    "location": bool(user_metadata.get("location")),
                    "datetime": bool(user_metadata.get("datetime")),
                    "timezone": bool(user_metadata.get("timezone"))
                }
            }
            
            return enhanced_query
            
        except Exception as e:
            # Return original query if enhancement fails
            if "tool_errors" not in state:
                state["tool_errors"] = {}
            state["tool_errors"]["query_enhancement"] = str(e)
            return query
    
    async def _web_search(self, state: ChatState) -> ChatState:
        """Perform web search if needed."""
        user_input = state.get("user_input", "")
        tool_plan = state.get("tool_plan", [])
        
        try:
            # Get web search parameters from tool plan if available
            web_search_tool = None
            for tool in tool_plan:
                if tool["tool_name"] == "web_search":
                    web_search_tool = tool
                    break
            
            # Use enhanced parameters from tool plan or defaults
            if web_search_tool:
                search_params = web_search_tool.get("parameters", {})
                query = search_params.get("query", user_input)
                num_results = search_params.get("num_results", 10)
                search_provider = search_params.get("search_provider", "auto")
                
                print(f"🔍 Using LLM-planned web search parameters:")
                print(f"   - Query: {query}")
                print(f"   - Results: {num_results}")
                print(f"   - Provider: {search_provider}")
            else:
                # Fallback to enhanced query with metadata
                query = await self._enhance_query_with_metadata(user_input, state)
                num_results = 10
                search_provider = "auto"
                
                print(f"🔍 Using fallback web search parameters:")
                print(f"   - Enhanced Query: {query}")
            
            # Perform web search
            search_tool = self.tools["web_search"]
            search_result = await search_tool.execute(
                query=query,
                num_results=num_results,
                search_provider=search_provider
            )
            
            if search_result["status"] == "success":
                # Store search results and mark real-time data availability
                state["search_results"] = search_result.get("results", [])
                state["tool_results"]["web_search"] = search_result
                
                # Mark that we have real-time data available
                if search_result.get("results"):
                    state["has_real_time_data"] = True
                    state["search_provider_used"] = search_result.get("provider", "unknown")
                
                # Analyze search results for additional processing
                try:
                    analyzer_tool = self.tools["search_analyzer"]
                    analysis_result = await analyzer_tool.execute(
                        search_results=search_result["results"],
                        analysis_type="filter",
                        min_relevance=0.5,
                        max_results=5
                    )
                    state["tool_results"]["search_analysis"] = analysis_result
                except Exception as e:
                    # Analysis is optional, don't fail the whole process
                    state["tool_results"]["search_analysis"] = {"error": str(e)}
            else:
                if "tool_errors" not in state:
                    state["tool_errors"] = {}
                state["tool_errors"]["web_search"] = search_result.get("error", "Search failed")
        
        except Exception as e:
            if "tool_errors" not in state:
                state["tool_errors"] = {}
            state["tool_errors"]["web_search"] = str(e)
        
        return state
    
    async def _get_location(self, state: ChatState) -> ChatState:
        """Process location queries to get user's current location."""
        user_input = state.get("user_input", "")
        
        try:
            print(f"📍 Processing location query: {user_input}")
            
            # Get location data from metadata or state
            user_metadata = state.get("metadata", {}).get("user_metadata", {})
            location_data = None
            
            # Try to get location from frontend coordinates first
            if state.get("latitude") and state.get("longitude"):
                try:
                    location_tool = self.tools.get("location_tool")
                    if location_tool:
                        location_result = await location_tool.execute(
                            latitude=state.get("latitude"),
                            longitude=state.get("longitude")
                        )
                        if location_result.get("status") == "success":
                            location_data = location_result.get("location", {}).get("value", {})
                            print(f"✅ Location from coordinates: {location_data.get('city', 'Unknown')}, {location_data.get('country', 'Unknown')}")
                        else:
                            # Fallback to basic coordinates
                            location_data = {
                                "lat": state.get("latitude"),
                                "lon": state.get("longitude"),
                                "city": "Unknown",
                                "country": "Unknown",
                                "address": "Coordinates available but reverse geocoding failed"
                            }
                            print(f"⚠️ Using coordinates only: {state.get('latitude')}, {state.get('longitude')}")
                except Exception as e:
                    print(f"❌ Location tool error: {e}")
                    location_data = {
                        "lat": state.get("latitude"),
                        "lon": state.get("longitude"),
                        "city": "Unknown",
                        "country": "Unknown",
                        "address": f"Coordinates: {state.get('latitude')}, {state.get('longitude')}"
                    }
            
            # Try IP-based location if no coordinates
            elif state.get("ip_address"):
                try:
                    location_tool = self.tools.get("location_tool")
                    if location_tool:
                        location_result = await location_tool.execute(
                            ip_address=state.get("ip_address")
                        )
                        if location_result.get("status") == "success":
                            location_data = location_result.get("location", {}).get("value", {})
                            print(f"✅ Location from IP: {location_data.get('city', 'Unknown')}, {location_data.get('country', 'Unknown')}")
                except Exception as e:
                    print(f"❌ IP location error: {e}")
            
            # Try metadata location
            elif user_metadata.get("location"):
                location_data = user_metadata["location"]["value"]
                print(f"✅ Location from metadata: {location_data.get('city', 'Unknown')}, {location_data.get('country', 'Unknown')}")
            
            # Generate location response
            if location_data:
                city = location_data.get("city", "Unknown")
                country = location_data.get("country", "Unknown")
                lat = location_data.get("lat")
                lon = location_data.get("lon")
                address = location_data.get("address", "")
                
                if city != "Unknown" and country != "Unknown":
                    location_response = f"📍 **Your Current Location:**\n\n**City:** {city}\n**Country:** {country}"
                    
                    if lat and lon:
                        location_response += f"\n**Coordinates:** {lat}, {lon}"
                    
                    if address and address != f"Coordinates: {lat}, {lon}":
                        location_response += f"\n**Address:** {address}"
                    
                    location_response += f"\n\n*Location detected via {'coordinates' if lat and lon else 'IP address'}*"
                else:
                    location_response = f"📍 **Your Current Location:**\n\n**Coordinates:** {lat}, {lon}\n\n*Exact location coordinates available, but city/country information could not be determined.*"
                
                state["location_data"] = {
                    "status": "success",
                    "location": location_data,
                    "response": location_response
                }
                print(f"✅ Location response generated successfully")
            else:
                # No location data available
                location_response = "📍 **Location Information Unavailable**\n\nI cannot determine your current location. This could be because:\n\n• Location services are disabled\n• No GPS coordinates are available\n• IP-based location detection failed\n\nTo get your location, please:\n• Enable location services in your browser\n• Allow location access when prompted\n• Try refreshing the page"
                
                state["location_data"] = {
                    "status": "error",
                    "error": "No location data available",
                    "response": location_response
                }
                print(f"⚠️ No location data available")
            
            return state
            
        except Exception as e:
            print(f"❌ Location processing error: {str(e)}")
            error_response = f"📍 **Location Error**\n\nSorry, I encountered an error while trying to determine your location: {str(e)}\n\nPlease try again or check your location settings."
            
            state["location_data"] = {
                "status": "error",
                "error": str(e),
                "response": error_response
            }
            
            if "tool_errors" not in state:
                state["tool_errors"] = {}
            state["tool_errors"]["location"] = str(e)
            
            return state
    
    async def _generate_image(self, state: ChatState) -> ChatState:
        """Generate image if requested."""
        user_input = state.get("user_input", "")
        
        try:
            # Extract image prompt from user input
            image_prompt = self._extract_image_prompt(user_input)
            
            if image_prompt:
                image_tool = self.tools["image_generator"]
                result = await image_tool.execute(
                    prompt=image_prompt,
                    provider="openai",
                    model="dall-e-3",
                    size="1024x1024"
                )
                
                if result["status"] == "success":
                    state["generated_images"] = [result]
                    state["tool_results"]["image_generation"] = result
                else:
                    if "tool_errors" not in state:
                        state["tool_errors"] = {}
                    state["tool_errors"]["image_generation"] = result.get("error", "Image generation failed")
        
        except Exception as e:
            if "tool_errors" not in state:
                state["tool_errors"] = {}
            state["tool_errors"]["image_generation"] = str(e)
        
        return state
    
    async def _execute_llm(self, state: ChatState) -> ChatState:
        """Execute LLM generation with context and real-time data integration."""
        try:
            # Check if we have real-time data that should be used directly
            has_real_time_data = state.get("has_real_time_data", False)
            real_time_data = state.get("real_time_data", {})
            search_results = state.get("search_results", [])
            user_input = state.get("user_input", "")
            
            # Check for location data
            location_data = state.get("location_data", {})
            
            # Also check tool_results for real-time data (fallback)
            tool_results = state.get("tool_results", {})
            if not has_real_time_data and tool_results.get("real_time_data"):
                real_time_data = tool_results["real_time_data"]
                has_real_time_data = True
                print(f"🔍 Found real-time data in tool_results")
            
            # If we have location data with a direct response, use it
            if location_data.get("status") == "success" and location_data.get("response"):
                print(f"🎯 Using direct location response")
                state["llm_response"] = location_data["response"]
                return state
            
            # If we have real-time data with a direct response, use it
            if has_real_time_data and real_time_data.get("status") == "success" and real_time_data.get("response"):
                print(f"🎯 Using direct real-time response: {real_time_data.get('data_type', 'unknown')}")
                state["llm_response"] = real_time_data["response"]
                if "tool_results" not in state:
                    state["tool_results"] = {}
                state["tool_results"]["llm_generation"] = {
                    "response": real_time_data["response"],
                    "used_real_time_data": True,
                    "data_type": real_time_data.get("data_type", "unknown")
                }
            elif has_real_time_data and search_results:
                # Use response synthesis to generate response based on search results
                synthesis_tool = self.tools["response_synthesis"]
                synthesis_tool.set_llm_provider(self.tools["llm_provider"])
                
                # Convert search results to sources format
                sources = []
                for result in search_results:
                    sources.append({
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "url": result.get("url", ""),
                        "content": result.get("snippet", ""),
                        "type": "search_result",
                        "provider": result.get("provider", "unknown")
                    })
                
                # Generate response using real-time data
                llm_response = await synthesis_tool.execute(
                    sources=sources,
                    synthesis_type="real_time_response",
                    user_query=user_input
                )
                
                state["llm_response"] = llm_response
                state["tool_results"]["llm_generation"] = {
                    "response": llm_response,
                    "used_real_time_data": True,
                    "search_provider": state.get("search_provider_used", "unknown")
                }
            else:
                # Use standard LLM generation without search results
                messages = self._build_messages_with_context(state)
                
                # Execute LLM
                llm_tool = self.tools["llm_provider"]
                
                # Use the provider and model selected by the user from the frontend
                selected_provider = state.get("selected_provider")
                selected_model = state.get("selected_model", "mistral-large-latest")
                
                # If no provider is selected, use a default fallback
                if not selected_provider:
                    # Only use fallback if no provider is specified by user
                    for provider_name in ["google", "mistral", "anthropic", "openai"]:
                        if provider_name in llm_tool.providers:
                            selected_provider = provider_name
                            # Set appropriate model for the provider
                            if provider_name == "google":
                                selected_model = "gemini-2.0-flash"  # Use the free model as per workspace rules
                            elif provider_name == "mistral":
                                selected_model = "mistral-large-latest"
                            elif provider_name == "anthropic":
                                selected_model = "claude-3-5-sonnet"
                            elif provider_name == "openai":
                                selected_model = "gpt-4o"
                            break
                
                llm_response = await llm_tool.execute(
                    messages=messages,
                    provider=selected_provider,
                    model=selected_model,
                    temperature=0.7,
                    max_tokens=8192,
                    stream=False
                )
                
                state["llm_response"] = llm_response
                state["tool_results"]["llm_generation"] = {
                    "response": llm_response,
                    "used_real_time_data": False
                }
        
        except Exception as e:
            if "tool_errors" not in state:
                state["tool_errors"] = {}
            state["tool_errors"]["llm_generation"] = str(e)
            
            # Generate a fallback response when LLM providers fail
            user_input = state.get("user_input", "")
            fallback_response = self._generate_fallback_response(user_input, str(e))
            state["llm_response"] = fallback_response
        
        return state
    
    async def _synthesize_response(self, state: ChatState) -> ChatState:
        """Synthesize final response from all sources."""
        try:
            # Collect all response sources
            sources = []
            
            # Add LLM response
            llm_response = state.get("llm_response", "")
            if llm_response:
                sources.append({
                    "content": llm_response,
                    "source_type": "llm_response",
                    "metadata": {"provider": state.get("selected_provider", "openai")}
                })
            
            # Add search results
            search_results = state.get("search_results", [])
            if search_results:
                search_content = "\n".join([
                    f"- {result.get('title', '')}: {result.get('snippet', '')}"
                    for result in search_results
                ])
                sources.append({
                    "content": search_content,
                    "source_type": "search_results",
                    "metadata": {"result_count": len(search_results)}
                })
            
            # Add file processing results
            processed_files = state.get("processed_files", {})
            if processed_files:
                file_content = "\n".join([
                    f"File: {filename}\n{result.get('content', '')}"
                    for filename, result in processed_files.items()
                ])
                sources.append({
                    "content": file_content,
                    "source_type": "file_processing",
                    "metadata": {"file_count": len(processed_files)}
                })
            
            # Add generated images
            generated_images = state.get("generated_images", [])
            if generated_images:
                image_content = "\n".join([
                    f"Generated image: {img.get('prompt', '')} - {img.get('image_url', '')}"
                    for img in generated_images
                ])
                sources.append({
                    "content": image_content,
                    "source_type": "image_generation",
                    "metadata": {"image_count": len(generated_images)}
                })
            
            # Check for direct location response
            user_input = state.get("user_input", "").lower()
            if "location" in user_input and ("what" in user_input or "where" in user_input):
                # Check tool_results first
                location_result = state.get("tool_results", {}).get("location_tool")
                if location_result and location_result.get("status") == "success":
                    location_data = location_result.get("location", {})
                    if location_data:
                        # Generate a direct location response
                        direct_response = self._generate_location_response(location_data, user_input)
                        state["synthesized_response"] = direct_response
                        return state
                
                # Check metadata for location data (from metadata collection)
                metadata = state.get("metadata", {})
                user_metadata = metadata.get("user_metadata", {})
                if user_metadata.get("location"):
                    location_data = user_metadata["location"]
                    if location_data:
                        # Generate a direct location response
                        direct_response = self._generate_location_response(location_data, user_input)
                        state["synthesized_response"] = direct_response
                        return state
            
            # Synthesize response
            if sources:
                synthesis_tool = self.tools["response_synthesis"]
                synthesized_response = await synthesis_tool.execute(
                    sources=sources,
                    synthesis_type="combine"
                )
                state["synthesized_response"] = synthesized_response
            else:
                state["synthesized_response"] = state.get("llm_response", "No response generated")
        
        except Exception as e:
            if "tool_errors" not in state:
                state["tool_errors"] = {}
            state["tool_errors"]["response_synthesis"] = str(e)
            state["synthesized_response"] = state.get("llm_response", "Error synthesizing response")
        
        return state
    
    def _generate_location_response(self, location_data: Dict[str, Any], user_input: str) -> str:
        """Generate a direct location response from location data."""
        try:
            # Extract location information
            city = location_data.get("city", "Unknown")
            country = location_data.get("country", "Unknown")
            state = location_data.get("state", "")
            street_address = location_data.get("street_address", "")
            neighbourhood = location_data.get("neighbourhood", "")
            postcode = location_data.get("postcode", "")
            
            # Build location string
            location_parts = []
            
            if street_address:
                location_parts.append(street_address)
            elif neighbourhood and neighbourhood != city:
                location_parts.append(neighbourhood)
            
            if city and city != "Unknown":
                location_parts.append(city)
            
            if state and state != city:
                location_parts.append(state)
            
            if country and country != "Unknown":
                location_parts.append(country)
            
            if postcode:
                location_parts.append(postcode)
            
            location_string = ", ".join(location_parts)
            
            # Generate response based on query type
            if "what is my location" in user_input or "where am i" in user_input:
                response = f"Based on your device's location data, you are currently at:\n\n**{location_string}**"
                
                # Add additional details if available
                if street_address:
                    response += f"\n\n📍 **Street Address:** {street_address}"
                if neighbourhood and neighbourhood != city:
                    response += f"\n🏘️ **Neighborhood:** {neighbourhood}"
                if postcode:
                    response += f"\n📮 **Postal Code:** {postcode}"
                
                response += f"\n\n*Location accuracy: High (GPS coordinates)*"
                
            else:
                response = f"Your current location is: **{location_string}**"
            
            return response
            
        except Exception as e:
            return f"Your location data is available, but I encountered an error formatting it: {str(e)}"
    
    async def _finalize_response(self, state: ChatState) -> ChatState:
        """Finalize the response for output."""
        try:
            # Get the final response
            final_response = state.get("synthesized_response", state.get("llm_response", ""))
            
            # Add any generated images to the response
            generated_images = state.get("generated_images", [])
            if generated_images:
                image_markdown = "\n\n".join([
                    f"![Generated Image]({img.get('image_url', '')})"
                    for img in generated_images
                ])
                final_response = f"{final_response}\n\n{image_markdown}"
            
            # Add search citations if available
            search_results = state.get("search_results", [])
            if search_results:
                citations = "\n\n**Sources:**\n" + "\n".join([
                    f"- [{result.get('title', '')}]({result.get('url', '')})"
                    for result in search_results
                ])
                final_response = f"{final_response}\n{citations}"
            
            state["final_response"] = final_response
            state["response_mode"] = "completed"
        
        except Exception as e:
            if "tool_errors" not in state:
                state["tool_errors"] = {}
            state["tool_errors"]["response_finalization"] = str(e)
            state["final_response"] = "Error finalizing response"
        
        return state
    
    async def _determine_agent_collaboration(self, state: ChatState) -> ChatState:
        """Determine if agent collaboration is needed."""
        analysis = state.get("metadata", {}).get("input_analysis", {})
        user_input = state.get("user_input", "")
        
        # Determine if collaboration is needed
        collaboration_needed = False
        collaboration_reason = ""
        
        # Check for complex multi-modal requests
        if (analysis.get("needs_file_processing", False) and 
            analysis.get("needs_web_search", False)):
            collaboration_needed = True
            collaboration_reason = "Multi-modal request requiring file processing and web search"
        
        # Check for complex analysis requests
        elif (analysis.get("needs_file_processing", False) and 
              analysis.get("needs_image_generation", False)):
            collaboration_needed = True
            collaboration_reason = "Complex request requiring file analysis and image generation"
        
        # Check for research and analysis combination
        elif (analysis.get("needs_web_search", False) and 
              analysis.get("complexity") == "complex"):
            collaboration_needed = True
            collaboration_reason = "Complex research request requiring multiple agents"
        
        # Check for explicit collaboration requests
        elif any(keyword in user_input.lower() for keyword in 
                ["analyze and search", "process and generate", "research and create", "comprehensive analysis"]):
            collaboration_needed = True
            collaboration_reason = "Explicit collaboration request detected"
        
        state["metadata"]["collaboration_needed"] = collaboration_needed
        state["metadata"]["collaboration_reason"] = collaboration_reason
        
        return state
    
    async def _coordinate_with_agents(self, state: ChatState) -> ChatState:
        """Coordinate with other agents for collaborative processing."""
        try:
            analysis = state.get("metadata", {}).get("input_analysis", {})
            user_input = state.get("user_input", "")
            collaboration_reason = state.get("metadata", {}).get("collaboration_reason", "")
            
            # Determine which agents to involve
            agents_to_involve = []
            agent_results = {}
            
            # File processing agent
            if analysis.get("needs_file_processing", False):
                agents_to_involve.append("file_agent")
                file_result = await self._request_agent_processing(
                    "file_agent", "process_files", {
                        "attachments": state.get("attachments", []),
                        "user_input": user_input
                    }
                )
                if file_result:
                    agent_results["file_agent"] = file_result
                    # Store output for other agents to use
                    if self.output_passing_manager:
                        # Import here to avoid circular import
                        from .output_passing import OutputType
                        
                        output_id = await self.store_output(
                            file_result, OutputType.DATA, 
                            tags=["file_processing", "collaboration"]
                        )
                        state["metadata"]["file_processing_output_id"] = output_id
            
            # Search agent
            if analysis.get("needs_web_search", False):
                agents_to_involve.append("search_agent")
                search_result = await self._request_agent_processing(
                    "search_agent", "search_web", {
                        "user_input": user_input,
                        "context": agent_results.get("file_agent", {})
                    }
                )
                if search_result:
                    agent_results["search_agent"] = search_result
                    # Store output for other agents to use
                    if self.output_passing_manager:
                        # Import here to avoid circular import
                        from .output_passing import OutputType
                        
                        output_id = await self.store_output(
                            search_result, OutputType.DATA,
                            tags=["web_search", "collaboration"]
                        )
                        state["metadata"]["search_output_id"] = output_id
            
            # Image agent
            if analysis.get("needs_image_generation", False):
                agents_to_involve.append("image_agent")
                image_result = await self._request_agent_processing(
                    "image_agent", "generate_image", {
                        "user_input": user_input,
                        "context": agent_results
                    }
                )
                if image_result:
                    agent_results["image_agent"] = image_result
                    # Store output for other agents to use
                    if self.output_passing_manager:
                        # Import here to avoid circular import
                        from .output_passing import OutputType
                        
                        output_id = await self.store_output(
                            image_result, OutputType.IMAGE,
                            tags=["image_generation", "collaboration"]
                        )
                        state["metadata"]["image_output_id"] = output_id
            
            # Store collaboration results
            state["agent_collaboration_results"] = agent_results
            state["metadata"]["collaboration_summary"] = {
                "agents_involved": agents_to_involve,
                "collaboration_reason": collaboration_reason,
                "successful_agents": list(agent_results.keys()),
                "total_agents": len(agents_to_involve)
            }
            
        except Exception as e:
            state["tool_errors"]["agent_collaboration"] = str(e)
            state["agent_collaboration_results"] = {}
        
        return state
    
    async def _request_agent_processing(self, agent_name: str, method: str, 
                                      context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Request processing from another agent."""
        try:
            if not self.communication_layer:
                return None
            
            # Import here to avoid circular import
            from .communication import AgentMessage, MessageType, Priority
            
            # Create request message
            message = AgentMessage(
                id=f"collab_request_{self.name}_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                sender=self.name,
                recipient=agent_name,
                message_type=MessageType.REQUEST,
                content={
                    "method": method,
                    "context": context,
                    "collaboration_request": True
                },
                priority=Priority.HIGH,
                requires_response=True,
                timeout=60.0
            )
            
            # Send message and wait for response
            await self.communication_layer.send_message(message)
            response = await self.communication_layer.wait_for_response(message.id, timeout=60.0)
            
            if response and response.status == "success":
                return response.results
            else:
                return None
                
        except Exception as e:
            print(f"Error requesting processing from {agent_name}: {e}")
            return None
    
    async def handle_agent_message(self, message: "AgentMessage") -> Optional["AgentOutput"]:
        """Handle incoming messages from other agents."""
        try:
            content = message.content
            
            if content.get("collaboration_request", False):
                # Handle collaboration request
                method = content.get("method", "process")
                context = content.get("context", {})
                
                # Process based on method
                if method == "synthesize_response":
                    # Synthesize response from multiple agent outputs
                    agent_outputs = context.get("agent_outputs", {})
                    synthesized = await self._synthesize_collaborative_response(agent_outputs)
                    
                    # Import here to avoid circular import
                    from .communication import AgentOutput
                    
                    return AgentOutput(
                        agent_name=self.name,
                        status="success",
                        results={"synthesized_response": synthesized}
                    )
                
                elif method == "coordinate_workflow":
                    # Coordinate a multi-agent workflow
                    workflow_data = context.get("workflow_data", {})
                    coordination_result = await self._coordinate_workflow(workflow_data)
                    
                    # Import here to avoid circular import
                    from .communication import AgentOutput
                    
                    return AgentOutput(
                        agent_name=self.name,
                        status="success",
                        results={"coordination_result": coordination_result}
                    )
            
            # Default handling
            return await super().handle_agent_message(message)
            
        except Exception as e:
            # Import here to avoid circular import
            from .communication import AgentOutput
            
            return AgentOutput(
                agent_name=self.name,
                status="error",
                results={"error": str(e)}
            )
    
    async def _synthesize_collaborative_response(self, agent_outputs: Dict[str, Any]) -> str:
        """Synthesize response from multiple agent outputs."""
        try:
            # Collect all outputs
            synthesis_sources = []
            
            for agent_name, output in agent_outputs.items():
                if output and output.get("status") == "success":
                    results = output.get("results", {})
                    
                    if agent_name == "file_agent":
                        synthesis_sources.append({
                            "content": results.get("final_response", ""),
                            "source_type": "file_analysis",
                            "metadata": {"agent": agent_name}
                        })
                    
                    elif agent_name == "search_agent":
                        synthesis_sources.append({
                            "content": results.get("final_response", ""),
                            "source_type": "search_results",
                            "metadata": {"agent": agent_name}
                        })
                    
                    elif agent_name == "image_agent":
                        synthesis_sources.append({
                            "content": results.get("final_response", ""),
                            "source_type": "image_generation",
                            "metadata": {"agent": agent_name}
                        })
            
            # Use response synthesis tool
            if synthesis_sources and "response_synthesis" in self.tools:
                synthesis_tool = self.tools["response_synthesis"]
                synthesized = await synthesis_tool.execute(
                    sources=synthesis_sources,
                    synthesis_type="combine"
                )
                return synthesized
            
            # Fallback synthesis
            return self._fallback_synthesis(agent_outputs)
            
        except Exception as e:
            return f"Error synthesizing collaborative response: {str(e)}"
    
    def _fallback_synthesis(self, agent_outputs: Dict[str, Any]) -> str:
        """Fallback synthesis when tools are not available."""
        response_parts = []
        
        for agent_name, output in agent_outputs.items():
            if output and output.get("status") == "success":
                results = output.get("results", {})
                final_response = results.get("final_response", "")
                
                if final_response:
                    response_parts.append(f"**{agent_name.replace('_', ' ').title()} Results:**\n{final_response}")
        
        if response_parts:
            return "\n\n".join(response_parts)
        else:
            return "Collaborative processing completed, but no results were generated."
    
    async def _coordinate_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate a multi-agent workflow."""
        try:
            # This would integrate with the WorkflowExecutor
            # For now, return a simple coordination result
            return {
                "status": "coordinated",
                "workflow_id": workflow_data.get("workflow_id", "unknown"),
                "participants": workflow_data.get("participants", []),
                "coordination_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _route_based_on_collaboration(self, state: ChatState) -> str:
        """Route based on collaboration needs."""
        collaboration_needed = state.get("metadata", {}).get("collaboration_needed", False)
        
        if collaboration_needed:
            return "collaborate"
        else:
            return "direct"
    
    def _generate_fallback_response(self, user_input: str, error_message: str) -> str:
        """Generate a fallback response when LLM providers are not available."""
        # Simple rule-based responses for common inputs
        user_input_lower = user_input.lower().strip()
        
        if user_input_lower in ["hello", "hi", "hey", "hii"]:
            return "Hello! I'm Xbot, your AI assistant. I'm currently running in fallback mode because the LLM providers are not configured with API keys. To get full AI capabilities, please configure your API keys in the environment variables."
        
        elif "how are you" in user_input_lower:
            return "I'm doing well, thank you for asking! I'm currently running in fallback mode. To enable full AI capabilities, please configure your API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or MISTRAL_API_KEY) in your environment variables."
        
        elif "what" in user_input_lower and "you" in user_input_lower:
            return "I'm Xbot, an AI assistant powered by an agentic architecture with LangGraph. I can help with various tasks including document processing, web search, image generation, and general conversation. Currently running in fallback mode - configure API keys for full functionality."
        
        elif "help" in user_input_lower:
            return "I'm here to help! I can assist with:\n- General conversation\n- Document processing (PDF, DOCX, etc.)\n- Web search\n- Image generation\n- Code analysis\n\nNote: I'm currently in fallback mode. Configure API keys for full AI capabilities."
        
        elif "error" in user_input_lower or "problem" in user_input_lower:
            return f"I see you're having an issue. The current error is: {error_message}. This is likely because the LLM providers are not configured with valid API keys. Please check your environment variables."
        
        else:
            return f"I understand you said: '{user_input}'. I'm currently running in fallback mode because the LLM providers are not configured with API keys. To get intelligent responses, please configure your API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or MISTRAL_API_KEY) in your environment variables."
    
    def _detect_search_intent(self, user_input: str) -> bool:
        """Detect if user input requires web search."""
        user_input_lower = user_input.lower()
        
        # Real-time information keywords that should NOT trigger web search
        real_time_only_keywords = [
            "my current", "what's my", "my location", "my date", "my time",
            "current location", "where am i", "what's my current"
        ]
        
        # Check if this is a personal real-time query that shouldn't use web search
        if any(keyword in user_input_lower for keyword in real_time_only_keywords):
            return False
        
        # Real-time information keywords that might need web search
        real_time_keywords = [
            "current", "recent", "latest", "today", "now", "live", "real-time",
            "stock price", "share price", "market", "trading", "news", "weather",
            "date", "time", "when will", "release date", "premiere", "launch"
        ]
        
        # General search keywords
        search_keywords = [
            "search", "find", "look up", "what is", "who is", "when did", 
            "where is", "how to", "why", "explain", "tell me about"
        ]
        
        # Check for real-time information needs
        if any(keyword in user_input_lower for keyword in real_time_keywords):
            return True
            
        # Check for general search needs
        if any(keyword in user_input_lower for keyword in search_keywords):
            return True
            
        # Check for specific patterns that indicate real-time data needs
        real_time_patterns = [
            "current date", "current time", "what time", "what date",
            "stock price", "share price", "market price", "trading price",
            "latest news", "recent news", "breaking news", "today's news",
            "when will", "release date", "premiere date", "launch date",
            "weather", "forecast", "temperature", "live score", "match score"
        ]
        
        return any(pattern in user_input_lower for pattern in real_time_patterns)
    
    def _detect_image_intent(self, user_input: str) -> bool:
        """Detect if user input requires image generation."""
        image_keywords = [
            "generate image", "create image", "draw", "illustration", "picture",
            "visual", "diagram", "chart", "graph", "logo", "artwork"
        ]
        return any(keyword in user_input.lower() for keyword in image_keywords)
    
    def _classify_intent(self, user_input: str) -> str:
        """Classify the intent of user input."""
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ["explain", "what is", "define"]):
            return "explanation"
        elif any(word in user_input_lower for word in ["how to", "tutorial", "guide"]):
            return "instruction"
        elif any(word in user_input_lower for word in ["analyze", "review", "evaluate"]):
            return "analysis"
        elif any(word in user_input_lower for word in ["create", "generate", "make"]):
            return "creation"
        else:
            return "general"
    
    def _extract_entities(self, user_input: str) -> List[str]:
        """Extract entities from user input."""
        # Simple entity extraction - in production, use NER models
        entities = []
        words = user_input.split()
        
        for word in words:
            if word.istitle() and len(word) > 2:
                entities.append(word)
        
        return entities
    
    def _assess_complexity(self, user_input: str) -> str:
        """Assess the complexity of user input."""
        word_count = len(user_input.split())
        
        if word_count < 10:
            return "simple"
        elif word_count < 50:
            return "medium"
        else:
            return "complex"
    
    def _extract_image_prompt(self, user_input: str) -> Optional[str]:
        """Extract image generation prompt from user input."""
        # Simple prompt extraction - in production, use more sophisticated parsing
        if "generate image" in user_input.lower():
            return user_input.replace("generate image", "").strip()
        elif "create image" in user_input.lower():
            return user_input.replace("create image", "").strip()
        elif "draw" in user_input.lower():
            return user_input.replace("draw", "").strip()
        return None
    
    def _build_messages_with_context(self, state: ChatState) -> List[Dict[str, Any]]:
        """Build messages with context from tools and files."""
        messages = []
        
        # Add system prompt
        system_prompt = state.get("system_prompt", "You are a helpful AI assistant.")
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        conversation_history = state.get("conversation_history", [])
        for msg in conversation_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # Add current user input with context
        user_input = state.get("user_input", "")
        
        # Add file processing results
        processed_files = state.get("processed_files", {})
        if processed_files:
            file_context = "\n\nFile Analysis:\n"
            for filename, result in processed_files.items():
                if result.get("status") == "success":
                    file_context += f"\n{filename}:\n{result.get('content', '')[:500]}...\n"
            user_input += file_context
        
        # Add search results
        search_results = state.get("search_results", [])
        if search_results:
            search_context = "\n\nSearch Results:\n"
            for result in search_results:
                search_context += f"\n- {result.get('title', '')}: {result.get('snippet', '')}\n"
            user_input += search_context
        
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _route_to_appropriate_tool(self, state: ChatState) -> str:
        """Route to the appropriate tool based on input analysis."""
        # Check if we have orchestration results
        orchestration_result = state.get("metadata", {}).get("tool_orchestration", {})
        if orchestration_result.get("status") == "success":
            return "orchestrate"
        
        # Check tool plan for specific tool routing
        tool_plan = state.get("metadata", {}).get("tool_plan", [])
        if tool_plan:
            # Check if location_tool is in the plan
            for tool in tool_plan:
                if tool.get("tool_name") == "location_tool":
                    return "location"
        
        # Fallback to individual tool routing
        analysis = state.get("metadata", {}).get("input_analysis", {})
        
        # Priority order: files > location > real_time > search > image > llm
        if analysis.get("needs_file_processing", False):
            return "files"
        elif analysis.get("needs_location", False) or analysis.get("intent") == "location_based":
            return "location"
        elif analysis.get("needs_real_time_data", False):
            return "real_time"
        elif analysis.get("needs_web_search", False):
            return "search"
        elif analysis.get("needs_image_generation", False):
            return "image"
        else:
            return "llm"
    
    def _should_process_files(self, state: ChatState) -> str:
        """Determine if files should be processed."""
        analysis = state.get("metadata", {}).get("input_analysis", {})
        return "files" if analysis.get("needs_file_processing", False) else "continue"
    
    def _should_web_search(self, state: ChatState) -> str:
        """Determine if web search should be performed."""
        analysis = state.get("metadata", {}).get("input_analysis", {})
        return "search" if analysis.get("needs_web_search", False) else "continue"
    
    def _should_generate_image(self, state: ChatState) -> str:
        """Determine if image should be generated."""
        analysis = state.get("metadata", {}).get("input_analysis", {})
        return "image" if analysis.get("needs_image_generation", False) else "continue"
