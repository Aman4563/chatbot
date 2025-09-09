"""Metadata Agent for user context and environment information."""

from typing import Dict, Any, List, Optional, AsyncIterator, TYPE_CHECKING
from datetime import datetime
import json
from langgraph.graph import StateGraph, END
from .base import BaseAgent
from tools.metadata_tools import TimezoneTool, LocationTool, DateTimeTool, UserAgentTool
from graphs.state import AgentState

if TYPE_CHECKING:
    from .communication import AgentMessage, MessageType, Priority, AgentOutput
    from .output_passing import OutputType, DataFormat


class MetadataAgent(BaseAgent):
    """Agent for collecting and providing user metadata for enhanced search and responses."""
    
    def __init__(self):
        super().__init__("metadata_agent", "Provides user metadata for enhanced search and responses")
        self.category = "metadata"
        self.priority = 2  # High priority for search enhancement
        self.metadata_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 3600  # 1 hour
    
    def _initialize_tools(self) -> None:
        """Initialize metadata tools."""
        self.tools = {
            "timezone_tool": TimezoneTool(),
            "location_tool": LocationTool(),
            "datetime_tool": DateTimeTool(),
            "user_agent_tool": UserAgentTool()
        }
    
    def _build_graph(self) -> None:
        """Build the metadata agent's LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_metadata_request", self._analyze_metadata_request)
        workflow.add_node("collect_timezone", self._collect_timezone)
        workflow.add_node("collect_location", self._collect_location)
        workflow.add_node("collect_datetime", self._collect_datetime)
        workflow.add_node("collect_device_info", self._collect_device_info)
        workflow.add_node("synthesize_metadata", self._synthesize_metadata)
        workflow.add_node("cache_metadata", self._cache_metadata)
        
        # Add edges
        workflow.set_entry_point("analyze_metadata_request")
        
        # Always go through the full collection process for comprehensive metadata
        workflow.add_edge("analyze_metadata_request", "collect_timezone")
        workflow.add_edge("collect_timezone", "collect_location")
        workflow.add_edge("collect_location", "collect_datetime")
        workflow.add_edge("collect_datetime", "collect_device_info")
        workflow.add_edge("collect_device_info", "synthesize_metadata")
        workflow.add_edge("synthesize_metadata", "cache_metadata")
        workflow.add_edge("cache_metadata", END)
        
        self.graph = workflow.compile()
    
    async def process(self, state: AgentState) -> AgentState:
        """Process metadata collection request."""
        try:
            if not await self.validate_state(state):
                return await self.handle_error(ValueError("Invalid state"), state)
            
            # Check cache first
            cache_key = self._generate_cache_key(state)
            if cache_key in self.metadata_cache:
                cached_data = self.metadata_cache[cache_key]
                if datetime.now().timestamp() - cached_data["timestamp"] < self.cache_ttl:
                    state["metadata"] = cached_data["data"]
                    state["metadata_source"] = "cache"
                    return state
            
            # Simplified direct processing instead of graph
            
            # Collect metadata directly
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "session_id": state.get("session_id"),
                "collection_time": 0.0
            }
            
            # Collect timezone
            try:
                timezone_tool = self.get_tool("timezone_tool")
                timezone_result = await timezone_tool.execute(
                    ip_address=state.get("ip_address"),
                    timezone_input=state.get("timezone_input"),
                    latitude=state.get("latitude"),
                    longitude=state.get("longitude")
                )
                if timezone_result.get("status") == "success":
                    metadata["timezone"] = timezone_result["timezone"]
                    print(f"✅ Timezone collected: {timezone_result['timezone']['value']}")
            except Exception as e:
                print(f"⚠️ Timezone collection failed: {e}")
                pass  # Silently handle errors
            
            # Collect location
            try:
                location_tool = self.get_tool("location_tool")
                location_result = await location_tool.execute(
                    ip_address=state.get("ip_address"),
                    latitude=state.get("latitude"),
                    longitude=state.get("longitude"),
                    address=state.get("address")
                )
                if location_result.get("status") == "success":
                    metadata["location"] = location_result["location"]
            except Exception as e:
                pass  # Silently handle errors
            
            # Collect datetime
            try:
                datetime_tool = self.get_tool("datetime_tool")
                datetime_result = await datetime_tool.execute()
                if datetime_result.get("status") == "success":
                    metadata["datetime"] = datetime_result["datetime"]
            except Exception as e:
                pass  # Silently handle errors
            
            # Collect device info
            try:
                user_agent_tool = self.get_tool("user_agent_tool")
                device_result = await user_agent_tool.execute(
                    user_agent=state.get("user_agent"),
                    client_hints=state.get("client_hints")
                )
                if device_result.get("status") == "success":
                    metadata["device"] = device_result["device"]
            except Exception as e:
                pass  # Silently handle errors
            
            # Add derived information
            metadata["derived"] = {
                "currency": "USD",
                "units": {"temperature": "F", "distance": "miles", "weight": "lbs"},
                "language": "en"
            }
            
            state["metadata"] = metadata
            return state
            
        except Exception as e:
            print(f"❌ MetadataAgent error: {e}")
            import traceback
            traceback.print_exc()
            return await self.handle_error(e, state)
    
    async def stream(self, state: AgentState) -> AsyncIterator[str]:
        """Stream metadata collection process."""
        try:
            async for chunk in self.graph.astream(state):
                if "metadata" in chunk:
                    yield f"data: {json.dumps(chunk['metadata'])}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    async def _analyze_metadata_request(self, state: AgentState) -> AgentState:
        """Analyze what metadata is needed."""
        print(f"🔍 Analyzing metadata request...")
        print(f"🔍 State keys before analysis: {list(state.keys())}")
        print(f"🔍 IP address before analysis: {state.get('ip_address')}")
        
        user_input = state.get("user_input", "").lower()
        session_id = state.get("session_id", "")
        
        # Determine metadata needs based on query analysis
        needs = {
            "timezone": any(keyword in user_input for keyword in [
                "time", "timezone", "local", "current time", "what time"
            ]),
            "location": any(keyword in user_input for keyword in [
                "location", "where", "near me", "local", "weather", "stores"
            ]),
            "datetime": any(keyword in user_input for keyword in [
                "date", "today", "tomorrow", "yesterday", "current date"
            ]),
            "device": any(keyword in user_input for keyword in [
                "device", "mobile", "desktop", "browser"
            ])
        }
        
        # If no specific needs detected, collect all metadata
        if not any(needs.values()):
            needs = {key: True for key in needs}
        
        state["metadata_needs"] = needs
        state["metadata_collection_start"] = datetime.now().isoformat()
        
        print(f"🔍 State keys after analysis: {list(state.keys())}")
        print(f"🔍 IP address after analysis: {state.get('ip_address')}")
        
        return state
    
    async def _route_metadata_collection(self, state: AgentState) -> str:
        """Route to appropriate metadata collection based on needs."""
        needs = state.get("metadata_needs", {})
        
        if needs.get("timezone") and not any(needs.get(k) for k in ["location", "datetime", "device"]):
            return "timezone"
        elif needs.get("location") and not any(needs.get(k) for k in ["timezone", "datetime", "device"]):
            return "location"
        elif needs.get("datetime") and not any(needs.get(k) for k in ["timezone", "location", "device"]):
            return "datetime"
        elif needs.get("device") and not any(needs.get(k) for k in ["timezone", "location", "datetime"]):
            return "device"
        else:
            return "all"
    
    async def _collect_timezone(self, state: AgentState) -> AgentState:
        """Collect timezone information."""
        try:
            print(f"🔍 Collecting timezone...")
            print(f"🔍 State type: {type(state)}")
            print(f"🔍 State keys: {list(state.keys())}")
            # Extract timezone info from request headers or user input
            timezone_input = state.get("timezone_input")
            ip_address = state.get("ip_address")
            latitude = state.get("latitude")
            longitude = state.get("longitude")
            
            print(f"🔍 IP address: {ip_address}")
            timezone_tool = self.get_tool("timezone_tool")
            result = await timezone_tool.execute(
                timezone_input=timezone_input,
                ip_address=ip_address,
                latitude=latitude,
                longitude=longitude
            )
            
            print(f"🔍 Timezone result: {result.get('status', 'No status')}")
            if result.get("status") == "success":
                state["timezone_data"] = result
            else:
                state["timezone_data"] = {"status": "error", "error": "Failed to collect timezone"}
            
            print(f"🔍 Timezone data stored in state: {state.get('timezone_data', {}).get('status', 'No data')}")
            return state
            
        except Exception as e:
            state["timezone_data"] = {"status": "error", "error": str(e)}
            return state
    
    async def _collect_location(self, state: AgentState) -> AgentState:
        """Collect location information."""
        try:
            print(f"🔍 Collecting location...")
            # Extract location info from request
            ip_address = state.get("ip_address")
            latitude = state.get("latitude")
            longitude = state.get("longitude")
            address = state.get("address")
            
            print(f"🔍 Location collection - IP: {ip_address}")
            location_tool = self.get_tool("location_tool")
            result = await location_tool.execute(
                ip_address=ip_address,
                latitude=latitude,
                longitude=longitude,
                address=address
            )
            
            if result.get("status") == "success":
                state["location_data"] = result
            else:
                state["location_data"] = {"status": "error", "error": "Failed to collect location"}
            
            return state
            
        except Exception as e:
            state["location_data"] = {"status": "error", "error": str(e)}
            return state
    
    async def _collect_datetime(self, state: AgentState) -> AgentState:
        """Collect current date and time information."""
        try:
            # Use timezone from previous step if available
            timezone_str = None
            if "timezone_data" in state and state["timezone_data"].get("status") == "success":
                timezone_str = state["timezone_data"]["timezone"]["value"]
            
            datetime_tool = self.get_tool("datetime_tool")
            result = await datetime_tool.execute(
                timezone_str=timezone_str,
                format_type="iso"
            )
            
            if result.get("status") == "success":
                state["datetime_data"] = result
            else:
                state["datetime_data"] = {"status": "error", "error": "Failed to collect datetime"}
            
            return state
            
        except Exception as e:
            state["datetime_data"] = {"status": "error", "error": str(e)}
            return state
    
    async def _collect_device_info(self, state: AgentState) -> AgentState:
        """Collect device and user agent information."""
        try:
            user_agent = state.get("user_agent")
            client_hints = state.get("client_hints")
            
            user_agent_tool = self.get_tool("user_agent_tool")
            result = await user_agent_tool.execute(
                user_agent=user_agent,
                client_hints=client_hints
            )
            
            if result.get("status") == "success":
                state["device_data"] = result
            else:
                state["device_data"] = {"status": "error", "error": "Failed to collect device info"}
            
            return state
            
        except Exception as e:
            state["device_data"] = {"status": "error", "error": str(e)}
            return state
    
    async def _synthesize_metadata(self, state: AgentState) -> AgentState:
        """Synthesize all collected metadata into a unified response."""
        try:
            print(f"🔍 Synthesizing metadata...")
            print(f"🔍 State keys: {list(state.keys())}")
            print(f"🔍 Timezone data: {state.get('timezone_data', {}).get('status', 'No data')}")
            print(f"🔍 Location data: {state.get('location_data', {}).get('status', 'No data')}")
            print(f"🔍 Datetime data: {state.get('datetime_data', {}).get('status', 'No data')}")
            print(f"🔍 Device data: {state.get('device_data', {}).get('status', 'No data')}")
            
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "session_id": state.get("session_id"),
                "collection_time": datetime.now().timestamp() - datetime.fromisoformat(
                    state.get("metadata_collection_start", datetime.now().isoformat())
                ).timestamp()
            }
            
            # Add timezone data
            if "timezone_data" in state and state["timezone_data"].get("status") == "success":
                metadata["timezone"] = state["timezone_data"]["timezone"]
            
            # Add location data
            if "location_data" in state and state["location_data"].get("status") == "success":
                metadata["location"] = state["location_data"]["location"]
            
            # Add datetime data
            if "datetime_data" in state and state["datetime_data"].get("status") == "success":
                metadata["datetime"] = state["datetime_data"]["datetime"]
            
            # Add device data
            if "device_data" in state and state["device_data"].get("status") == "success":
                metadata["device"] = state["device_data"]["device"]
            
            # Add derived information
            metadata["derived"] = self._derive_additional_info(metadata)
            
            state["metadata"] = metadata
            state["metadata_status"] = "success"
            
            return state
            
        except Exception as e:
            state["metadata"] = {"status": "error", "error": str(e)}
            state["metadata_status"] = "error"
            return state
    
    async def _cache_metadata(self, state: AgentState) -> AgentState:
        """Cache the collected metadata."""
        try:
            if "metadata" in state and state.get("metadata_status") == "success":
                cache_key = self._generate_cache_key(state)
                self.metadata_cache[cache_key] = {
                    "data": state["metadata"],
                    "timestamp": datetime.now().timestamp()
                }
                
                # Clean old cache entries
                self._clean_cache()
            
            return state
            
        except Exception as e:
            # Don't fail the whole process for cache errors
            return state
    
    def _derive_additional_info(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Derive additional information from collected metadata."""
        derived = {}
        
        # Currency based on country
        if "location" in metadata and "value" in metadata["location"]:
            country_code = metadata["location"]["value"].get("country_code")
            if country_code:
                derived["currency"] = self._get_currency_from_country(country_code)
        
        # Units based on country
        if "location" in metadata and "value" in metadata["location"]:
            country_code = metadata["location"]["value"].get("country_code")
            if country_code:
                derived["units"] = self._get_units_from_country(country_code)
        
        # Language preferences
        if "device" in metadata:
            derived["language"] = "en"  # Default, could be enhanced with browser language detection
        
        return derived
    
    def _get_currency_from_country(self, country_code: str) -> str:
        """Get currency code from country code."""
        currency_map = {
            "US": "USD", "GB": "GBP", "EU": "EUR", "JP": "JPY", "IN": "INR",
            "CA": "CAD", "AU": "AUD", "CH": "CHF", "CN": "CNY", "BR": "BRL"
        }
        return currency_map.get(country_code.upper(), "USD")
    
    def _get_units_from_country(self, country_code: str) -> Dict[str, str]:
        """Get unit preferences from country code."""
        metric_countries = {"US", "LR", "MM"}  # Countries using imperial units
        
        if country_code.upper() in metric_countries:
            return {"temperature": "F", "distance": "miles", "weight": "lbs"}
        else:
            return {"temperature": "C", "distance": "km", "weight": "kg"}
    
    def _generate_cache_key(self, state: AgentState) -> str:
        """Generate cache key for metadata."""
        session_id = state.get("session_id", "")
        ip_address = state.get("ip_address", "")
        user_agent = state.get("user_agent", "")
        
        # Create a hash of identifying information
        import hashlib
        key_data = f"{session_id}_{ip_address}_{user_agent}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _clean_cache(self) -> None:
        """Clean old cache entries."""
        current_time = datetime.now().timestamp()
        keys_to_remove = []
        
        for key, data in self.metadata_cache.items():
            if current_time - data["timestamp"] > self.cache_ttl:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.metadata_cache[key]
    
    async def get_metadata_for_search(self, state: AgentState) -> Dict[str, Any]:
        """Get metadata specifically formatted for search enhancement."""
        try:
            # Process metadata if not already available
            if "metadata" not in state:
                state = await self.process(state)
            
            metadata = state.get("metadata", {})
            
            # Format for search enhancement
            search_metadata = {
                "location": metadata.get("location", {}).get("value", {}),
                "timezone": metadata.get("timezone", {}).get("value", "UTC"),
                "datetime": metadata.get("datetime", {}).get("value"),
                "currency": metadata.get("derived", {}).get("currency", "USD"),
                "units": metadata.get("derived", {}).get("units", {"temperature": "C", "distance": "km"}),
                "device": metadata.get("device", {}).get("form_factor", "desktop")
            }
            
            return search_metadata
            
        except Exception as e:
            return {"error": str(e)}
    
    async def handle_agent_message(self, message: "AgentMessage") -> Optional["AgentOutput"]:
        """Handle incoming messages from other agents."""
        try:
            if message.content.get("type") == "metadata_request":
                # Process metadata request
                state = AgentState(
                    user_input=message.content.get("query", ""),
                    session_id=message.content.get("session_id", ""),
                    ip_address=message.content.get("ip_address"),
                    user_agent=message.content.get("user_agent"),
                    client_hints=message.content.get("client_hints"),
                    timezone_input=message.content.get("timezone_input"),
                    latitude=message.content.get("latitude"),
                    longitude=message.content.get("longitude")
                )
                
                result_state = await self.process(state)
                
                return AgentOutput(
                    agent_name=self.name,
                    status="success",
                    results={"metadata": result_state.get("metadata", {})}
                )
            
            return AgentOutput(
                agent_name=self.name,
                status="success",
                results={"message": "Metadata request processed"}
            )
            
        except Exception as e:
            return AgentOutput(
                agent_name=self.name,
                status="error",
                results={"error": str(e)}
            )
