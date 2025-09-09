"""Base agent class for agentic chat system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, AsyncIterator, Optional, TYPE_CHECKING
from datetime import datetime
import asyncio
from langgraph.graph import StateGraph
from graphs.state import AgentState

if TYPE_CHECKING:
    from .communication import AgentCommunicationLayer, AgentMessage, MessageType, Priority, AgentOutput
    from .output_passing import OutputPassingManager, AgentOutputData, OutputType, DataFormat, OutputMetadata


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.tools: Dict[str, Any] = {}
        self.graph: Optional[StateGraph] = None
        self.communication_layer: Optional[AgentCommunicationLayer] = None
        self.output_passing_manager: Optional[OutputPassingManager] = None
        self.is_communicating = False
        self._initialize_tools()
        self._build_graph()
    
    @abstractmethod
    def _initialize_tools(self) -> None:
        """Initialize tools available to this agent."""
        pass
    
    @abstractmethod
    def _build_graph(self) -> None:
        """Build the agent's LangGraph workflow."""
        pass
    
    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """Process the current state and return updated state."""
        pass
    
    @abstractmethod
    async def stream(self, state: AgentState) -> AsyncIterator[str]:
        """Stream processing results."""
        pass
    
    def get_available_tools(self) -> List[str]:
        """Return list of tools this agent can use."""
        return list(self.tools.keys())
    
    def get_tool(self, tool_name: str) -> Any:
        """Get a specific tool by name."""
        return self.tools.get(tool_name)
    
    def add_tool(self, name: str, tool: Any) -> None:
        """Add a tool to this agent."""
        self.tools[name] = tool
    
    def remove_tool(self, name: str) -> None:
        """Remove a tool from this agent."""
        if name in self.tools:
            del self.tools[name]
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.get_available_tools(),
            "graph_built": self.graph is not None
        }
    
    async def validate_state(self, state: AgentState) -> bool:
        """Validate the input state for this agent."""
        required_fields = ["user_input", "current_agent", "session_id"]
        return all(field in state for field in required_fields)
    
    async def handle_error(self, error: Exception, state: AgentState) -> AgentState:
        """Handle errors during processing."""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "agent": self.name,
            "timestamp": str(datetime.now())
        }
        
        if "tool_errors" not in state:
            state["tool_errors"] = {}
        state["tool_errors"][self.name] = error_info
        state["final_response"] = f"Error in {self.name}: {str(error)}"
        
        return state
    
    def set_communication_layer(self, communication_layer: "AgentCommunicationLayer") -> None:
        """Set the communication layer for this agent."""
        self.communication_layer = communication_layer
        self.is_communicating = True
    
    def set_output_passing_manager(self, output_passing_manager: "OutputPassingManager") -> None:
        """Set the output passing manager for this agent."""
        self.output_passing_manager = output_passing_manager
    
    async def send_message_to_agent(self, recipient: str, content: Dict[str, Any], 
                                  message_type: "MessageType" = None,
                                  priority: "Priority" = None,
                                  requires_response: bool = False) -> bool:
        """Send a message to another agent."""
        if not self.communication_layer:
            return False
        
        # Import here to avoid circular import
        from .communication import AgentMessage, MessageType, Priority
        
        if message_type is None:
            message_type = MessageType.REQUEST
        if priority is None:
            priority = Priority.NORMAL
            
        message = AgentMessage(
            id=f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            sender=self.name,
            recipient=recipient,
            message_type=message_type,
            content=content,
            priority=priority,
            requires_response=requires_response
        )
        
        return await self.communication_layer.send_message(message)
    
    async def receive_messages(self) -> List["AgentMessage"]:
        """Receive messages for this agent."""
        if not self.communication_layer:
            return []
        
        messages = []
        while True:
            message = await self.communication_layer.receive_message(self.name)
            if message:
                messages.append(message)
            else:
                break
        
        return messages
    
    async def store_output(self, content: Any, output_type: "OutputType", 
                         data_format: "DataFormat" = None,
                         tags: List[str] = None,
                         dependencies: List[str] = None) -> Optional[str]:
        """Store output for other agents to use."""
        if not self.output_passing_manager:
            return None
        
        # Import here to avoid circular import
        from .output_passing import OutputMetadata, AgentOutputData, DataFormat
        
        if data_format is None:
            data_format = DataFormat.JSON
        
        output_id = f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        metadata = OutputMetadata(
            output_id=output_id,
            agent_name=self.name,
            output_type=output_type,
            data_format=data_format,
            size=len(str(content)),
            tags=tags or [],
            dependencies=dependencies or []
        )
        
        output_data = AgentOutputData(
            metadata=metadata,
            content=content
        )
        
        success = await self.output_passing_manager.store_output(output_data)
        return output_id if success else None
    
    async def retrieve_output(self, output_id: str) -> Optional["AgentOutputData"]:
        """Retrieve output from another agent."""
        if not self.output_passing_manager:
            return None
        
        return await self.output_passing_manager.retrieve_output(output_id)
    
    async def pass_output_to_agent(self, output_id: str, target_agent: str, 
                                 transformation: Optional["DataFormat"] = None) -> bool:
        """Pass output to another agent."""
        if not self.output_passing_manager:
            return False
        
        return await self.output_passing_manager.pass_output_to_agent(
            output_id, target_agent, transformation
        )
    
    async def handle_agent_message(self, message: "AgentMessage") -> Optional["AgentOutput"]:
        """Handle incoming messages from other agents."""
        # Default implementation - override in subclasses
        # Import here to avoid circular import
        from .communication import AgentOutput
        
        return AgentOutput(
            agent_name=self.name,
            status="success",
            results={"message": "Message received", "content": message.content}
        )
    
    async def start_communication_loop(self) -> None:
        """Start the communication loop for this agent."""
        if not self.communication_layer:
            return
        
        while self.is_communicating:
            try:
                messages = await self.receive_messages()
                for message in messages:
                    response = await self.handle_agent_message(message)
                    if response and message.requires_response:
                        await self.communication_layer.send_response(message, response)
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Error in communication loop for {self.name}: {e}")
                await asyncio.sleep(1.0)
    
    def stop_communication(self) -> None:
        """Stop the communication loop."""
        self.is_communicating = False


class AgentRegistry:
    """Registry for managing all agents in the system."""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent in the registry."""
        self._agents[agent.name] = agent
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get an agent by name."""
        return self._agents.get(name)
    
    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())
    
    def get_agent_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get agent information by name."""
        agent = self.get_agent(name)
        return agent.get_info() if agent else None
    
    def get_all_agent_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information for all registered agents."""
        return {name: agent.get_info() for name, agent in self._agents.items()}
