"""Agent Communication Layer for inter-agent communication and collaboration."""

from typing import Dict, Any, List, Optional, AsyncIterator, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import json
from enum import Enum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseAgent, AgentRegistry
    from graphs.state import AgentState


class MessageType(Enum):
    """Types of messages between agents."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    STATUS_UPDATE = "status_update"


class Priority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class AgentMessage:
    """Message structure for agent communication."""
    id: str
    sender: str
    recipient: str
    message_type: MessageType
    content: Dict[str, Any]
    priority: Priority = Priority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    requires_response: bool = False
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type.value,
            "content": self.content,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "requires_response": self.requires_response,
            "timeout": self.timeout,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary."""
        return cls(
            id=data["id"],
            sender=data["sender"],
            recipient=data["recipient"],
            message_type=MessageType(data["message_type"]),
            content=data["content"],
            priority=Priority(data["priority"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data.get("correlation_id"),
            requires_response=data.get("requires_response", False),
            timeout=data.get("timeout"),
            metadata=data.get("metadata", {})
        )


@dataclass
class AgentOutput:
    """Output structure for agent processing results."""
    agent_name: str
    status: str  # "success", "error", "partial"
    results: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    
    def to_state(self) -> Dict[str, Any]:
        """Convert agent output to shared state format."""
        return {
            "agent_name": self.agent_name,
            "status": self.status,
            "results": self.results,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "processing_time": self.processing_time,
            "error_message": self.error_message
        }


class AgentCommunicationProtocol(ABC):
    """Protocol for agent communication."""
    
    @abstractmethod
    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message to another agent."""
        pass
    
    @abstractmethod
    async def receive_message(self, agent_name: str) -> Optional[AgentMessage]:
        """Receive a message for this agent."""
        pass
    
    @abstractmethod
    async def send_response(self, original_message: AgentMessage, response: AgentOutput) -> bool:
        """Send a response to a request message."""
        pass
    
    @abstractmethod
    async def broadcast_message(self, message: AgentMessage, exclude_sender: bool = True) -> List[bool]:
        """Broadcast a message to all agents."""
        pass


class AgentCommunicationLayer(AgentCommunicationProtocol):
    """Implementation of agent communication layer."""
    
    def __init__(self, agent_registry: "AgentRegistry"):
        self.agent_registry = agent_registry
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.message_history: List[AgentMessage] = []
        self.max_history_size = 1000
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the communication layer."""
        async with self._lock:
            # Create message queues for all registered agents
            for agent_name in self.agent_registry.list_agents():
                self.message_queues[agent_name] = asyncio.Queue(maxsize=100)
    
    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message to another agent."""
        try:
            async with self._lock:
                # Validate message
                if not self._validate_message(message):
                    return False
                
                # Add to history
                self.message_history.append(message)
                if len(self.message_history) > self.max_history_size:
                    self.message_history.pop(0)
                
                # Send to recipient's queue
                if message.recipient in self.message_queues:
                    await self.message_queues[message.recipient].put(message)
                    
                    # If response required, create future for response
                    if message.requires_response:
                        self.pending_responses[message.id] = asyncio.Future()
                    
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    async def receive_message(self, agent_name: str) -> Optional[AgentMessage]:
        """Receive a message for this agent."""
        try:
            if agent_name in self.message_queues:
                # Wait for message with timeout
                message = await asyncio.wait_for(
                    self.message_queues[agent_name].get(),
                    timeout=1.0
                )
                return message
            return None
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            print(f"Error receiving message: {e}")
            return None
    
    async def send_response(self, original_message: AgentMessage, response: AgentOutput) -> bool:
        """Send a response to a request message."""
        try:
            # Create response message
            response_message = AgentMessage(
                id=f"resp_{original_message.id}",
                sender=original_message.recipient,
                recipient=original_message.sender,
                message_type=MessageType.RESPONSE,
                content=response.to_state(),
                priority=original_message.priority,
                correlation_id=original_message.id,
                requires_response=False
            )
            
            # Send response
            success = await self.send_message(response_message)
            
            # Complete pending future if exists
            if original_message.id in self.pending_responses:
                future = self.pending_responses.pop(original_message.id)
                if not future.done():
                    future.set_result(response)
            
            return success
            
        except Exception as e:
            print(f"Error sending response: {e}")
            return False
    
    async def broadcast_message(self, message: AgentMessage, exclude_sender: bool = True) -> List[bool]:
        """Broadcast a message to all agents."""
        results = []
        for agent_name in self.agent_registry.list_agents():
            if exclude_sender and agent_name == message.sender:
                continue
            
            # Create copy of message for each recipient
            broadcast_message = AgentMessage(
                id=f"{message.id}_{agent_name}",
                sender=message.sender,
                recipient=agent_name,
                message_type=message.message_type,
                content=message.content,
                priority=message.priority,
                correlation_id=message.correlation_id,
                requires_response=message.requires_response,
                timeout=message.timeout,
                metadata=message.metadata
            )
            
            success = await self.send_message(broadcast_message)
            results.append(success)
        
        return results
    
    async def wait_for_response(self, message_id: str, timeout: Optional[float] = None) -> Optional[AgentOutput]:
        """Wait for a response to a specific message."""
        try:
            if message_id in self.pending_responses:
                future = self.pending_responses[message_id]
                if timeout:
                    response = await asyncio.wait_for(future, timeout=timeout)
                else:
                    response = await future
                return response
            return None
        except asyncio.TimeoutError:
            # Clean up pending response
            if message_id in self.pending_responses:
                del self.pending_responses[message_id]
            return None
        except Exception as e:
            print(f"Error waiting for response: {e}")
            return None
    
    def _validate_message(self, message: AgentMessage) -> bool:
        """Validate a message before sending."""
        if not message.id or not message.sender or not message.recipient:
            return False
        
        if message.sender not in self.agent_registry.list_agents():
            return False
        
        if message.recipient not in self.agent_registry.list_agents():
            return False
        
        return True
    
    def get_message_history(self, agent_name: Optional[str] = None, limit: int = 100) -> List[AgentMessage]:
        """Get message history, optionally filtered by agent."""
        if agent_name:
            filtered_history = [
                msg for msg in self.message_history
                if msg.sender == agent_name or msg.recipient == agent_name
            ]
            return filtered_history[-limit:]
        return self.message_history[-limit:]
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get communication statistics."""
        stats = {
            "total_messages": len(self.message_history),
            "pending_responses": len(self.pending_responses),
            "active_agents": len(self.message_queues),
            "queue_sizes": {
                agent: queue.qsize() for agent, queue in self.message_queues.items()
            }
        }
        return stats


class AgentCollaborationManager:
    """Manages collaborative workflows between agents."""
    
    def __init__(self, communication_layer: AgentCommunicationLayer, agent_registry: "AgentRegistry"):
        self.communication_layer = communication_layer
        self.agent_registry = agent_registry
        self.active_collaborations: Dict[str, Dict[str, Any]] = {}
        self.collaboration_patterns = self._load_collaboration_patterns()
    
    def _load_collaboration_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined collaboration patterns."""
        return {
            "file_analysis": {
                "primary": "file_agent",
                "secondary": ["chat_agent"],
                "workflow": [
                    "file_agent.extract_content",
                    "file_agent.analyze_content",
                    "chat_agent.synthesize_response"
                ],
                "data_flow": {
                    "file_agent": ["extraction_results", "analysis_results"],
                    "chat_agent": ["synthesized_response"]
                }
            },
            "research_task": {
                "primary": "search_agent",
                "secondary": ["chat_agent"],
                "workflow": [
                    "search_agent.search_web",
                    "search_agent.filter_results",
                    "chat_agent.synthesize_response"
                ],
                "data_flow": {
                    "search_agent": ["search_results", "synthesized_information"],
                    "chat_agent": ["synthesized_response"]
                }
            },
            "creative_task": {
                "primary": "image_agent",
                "secondary": ["chat_agent"],
                "workflow": [
                    "image_agent.optimize_prompt",
                    "image_agent.generate_image",
                    "chat_agent.synthesize_response"
                ],
                "data_flow": {
                    "image_agent": ["generated_images", "image_analysis"],
                    "chat_agent": ["synthesized_response"]
                }
            },
            "complex_analysis": {
                "primary": "file_agent",
                "secondary": ["search_agent", "chat_agent"],
                "workflow": [
                    "file_agent.extract_content",
                    "search_agent.search_web",
                    "file_agent.analyze_content",
                    "search_agent.synthesize_information",
                    "chat_agent.synthesize_response"
                ],
                "data_flow": {
                    "file_agent": ["extraction_results", "analysis_results"],
                    "search_agent": ["search_results", "synthesized_information"],
                    "chat_agent": ["synthesized_response"]
                }
            }
        }
    
    async def initiate_collaboration(self, pattern_name: str, initiator: str, context: Dict[str, Any]) -> str:
        """Initiate a collaborative workflow."""
        if pattern_name not in self.collaboration_patterns:
            raise ValueError(f"Unknown collaboration pattern: {pattern_name}")
        
        pattern = self.collaboration_patterns[pattern_name]
        collaboration_id = f"collab_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{initiator}"
        
        # Create collaboration record
        collaboration = {
            "id": collaboration_id,
            "pattern": pattern_name,
            "initiator": initiator,
            "participants": [pattern["primary"]] + pattern["secondary"],
            "workflow": pattern["workflow"],
            "data_flow": pattern["data_flow"],
            "status": "initiated",
            "context": context,
            "results": {},
            "start_time": datetime.now(),
            "end_time": None
        }
        
        self.active_collaborations[collaboration_id] = collaboration
        
        # Notify all participants
        notification_message = AgentMessage(
            id=f"collab_init_{collaboration_id}",
            sender=initiator,
            recipient="",  # Will be set per participant
            message_type=MessageType.NOTIFICATION,
            content={
                "collaboration_id": collaboration_id,
                "pattern": pattern_name,
                "role": "participant",
                "context": context
            },
            priority=Priority.HIGH,
            requires_response=True
        )
        
        # Send to all participants
        for participant in collaboration["participants"]:
            if participant != initiator:
                notification_message.recipient = participant
                await self.communication_layer.send_message(notification_message)
        
        return collaboration_id
    
    async def coordinate_workflow(self, collaboration_id: str) -> Dict[str, Any]:
        """Coordinate the execution of a collaborative workflow."""
        if collaboration_id not in self.active_collaborations:
            raise ValueError(f"Unknown collaboration: {collaboration_id}")
        
        collaboration = self.active_collaborations[collaboration_id]
        workflow = collaboration["workflow"]
        results = {}
        
        try:
            # Execute workflow steps
            for step in workflow:
                agent_name, method = step.split(".")
                
                # Send request to agent
                request_message = AgentMessage(
                    id=f"workflow_{collaboration_id}_{step}",
                    sender="collaboration_manager",
                    recipient=agent_name,
                    message_type=MessageType.REQUEST,
                    content={
                        "method": method,
                        "collaboration_id": collaboration_id,
                        "context": collaboration["context"],
                        "previous_results": results
                    },
                    priority=Priority.HIGH,
                    requires_response=True,
                    timeout=30.0
                )
                
                await self.communication_layer.send_message(request_message)
                
                # Wait for response
                response = await self.communication_layer.wait_for_response(
                    request_message.id, 
                    timeout=30.0
                )
                
                if response and response.status == "success":
                    results[step] = response.results
                    collaboration["results"][step] = response.results
                else:
                    collaboration["status"] = "error"
                    collaboration["error"] = response.error_message if response else "No response received"
                    break
            
            # Update collaboration status
            if collaboration["status"] != "error":
                collaboration["status"] = "completed"
                collaboration["end_time"] = datetime.now()
            
            return results
            
        except Exception as e:
            collaboration["status"] = "error"
            collaboration["error"] = str(e)
            raise
    
    async def handle_agent_response(self, message: AgentMessage, response: AgentOutput) -> None:
        """Handle response from an agent in a collaboration."""
        collaboration_id = message.content.get("collaboration_id")
        if not collaboration_id or collaboration_id not in self.active_collaborations:
            return
        
        collaboration = self.active_collaborations[collaboration_id]
        step = f"{message.recipient}.{message.content.get('method', 'unknown')}"
        
        # Store results
        collaboration["results"][step] = response.results
        
        # Check if workflow is complete
        completed_steps = len(collaboration["results"])
        total_steps = len(collaboration["workflow"])
        
        if completed_steps >= total_steps:
            collaboration["status"] = "completed"
            collaboration["end_time"] = datetime.now()
    
    def get_collaboration_status(self, collaboration_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a collaboration."""
        return self.active_collaborations.get(collaboration_id)
    
    def get_active_collaborations(self) -> Dict[str, Dict[str, Any]]:
        """Get all active collaborations."""
        return self.active_collaborations.copy()
    
    def cleanup_completed_collaborations(self) -> int:
        """Clean up completed collaborations older than 1 hour."""
        cutoff_time = datetime.now().timestamp() - 3600  # 1 hour ago
        to_remove = []
        
        for collab_id, collaboration in self.active_collaborations.items():
            if (collaboration["status"] in ["completed", "error"] and 
                collaboration["end_time"] and 
                collaboration["end_time"].timestamp() < cutoff_time):
                to_remove.append(collab_id)
        
        for collab_id in to_remove:
            del self.active_collaborations[collab_id]
        
        return len(to_remove)


class AgentNegotiationManager:
    """Manages negotiation between agents for task assignment."""
    
    def __init__(self, communication_layer: AgentCommunicationLayer, agent_registry: "AgentRegistry"):
        self.communication_layer = communication_layer
        self.agent_registry = agent_registry
        self.active_negotiations: Dict[str, Dict[str, Any]] = {}
    
    async def initiate_negotiation(self, task_description: str, initiator: str, required_capabilities: List[str]) -> str:
        """Initiate negotiation for task assignment."""
        negotiation_id = f"negotiation_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{initiator}"
        
        # Find potential agents
        potential_agents = []
        for agent_name in self.agent_registry.list_agents():
            agent = self.agent_registry.get_agent(agent_name)
            if agent and self._agent_has_capabilities(agent, required_capabilities):
                potential_agents.append(agent_name)
        
        # Create negotiation record
        negotiation = {
            "id": negotiation_id,
            "initiator": initiator,
            "task_description": task_description,
            "required_capabilities": required_capabilities,
            "potential_agents": potential_agents,
            "bids": {},
            "status": "active",
            "start_time": datetime.now(),
            "selected_agent": None
        }
        
        self.active_negotiations[negotiation_id] = negotiation
        
        # Send bid requests to potential agents
        for agent_name in potential_agents:
            bid_request = AgentMessage(
                id=f"bid_request_{negotiation_id}_{agent_name}",
                sender=initiator,
                recipient=agent_name,
                message_type=MessageType.REQUEST,
                content={
                    "negotiation_id": negotiation_id,
                    "task_description": task_description,
                    "required_capabilities": required_capabilities,
                    "bid_deadline": (datetime.now().timestamp() + 10.0)  # 10 seconds
                },
                priority=Priority.HIGH,
                requires_response=True,
                timeout=10.0
            )
            
            await self.communication_layer.send_message(bid_request)
        
        return negotiation_id
    
    async def collect_bids(self, negotiation_id: str, timeout: float = 10.0) -> Dict[str, Any]:
        """Collect bids from agents and select the best one."""
        if negotiation_id not in self.active_negotiations:
            raise ValueError(f"Unknown negotiation: {negotiation_id}")
        
        negotiation = self.active_negotiations[negotiation_id]
        start_time = datetime.now()
        
        # Wait for bids
        while (datetime.now() - start_time).total_seconds() < timeout:
            # Check for bid responses
            for agent_name in negotiation["potential_agents"]:
                message_id = f"bid_request_{negotiation_id}_{agent_name}"
                response = await self.communication_layer.wait_for_response(message_id, timeout=1.0)
                
                if response and response.status == "success":
                    bid_data = response.results
                    negotiation["bids"][agent_name] = {
                        "capability_score": bid_data.get("capability_score", 0),
                        "estimated_time": bid_data.get("estimated_time", 0),
                        "confidence": bid_data.get("confidence", 0),
                        "cost": bid_data.get("cost", 0)
                    }
            
            # Check if we have enough bids
            if len(negotiation["bids"]) >= len(negotiation["potential_agents"]) * 0.5:  # At least 50% response
                break
        
        # Select best agent
        if negotiation["bids"]:
            best_agent = self._select_best_agent(negotiation["bids"])
            negotiation["selected_agent"] = best_agent
            negotiation["status"] = "completed"
        else:
            negotiation["status"] = "failed"
        
        return negotiation
    
    def _agent_has_capabilities(self, agent: "BaseAgent", required_capabilities: List[str]) -> bool:
        """Check if agent has required capabilities."""
        # This is a simplified check - in production, you'd have more sophisticated capability matching
        agent_info = agent.get_info()
        agent_tools = agent_info.get("tools", [])
        
        for capability in required_capabilities:
            if capability not in agent_tools:
                return False
        return True
    
    def _select_best_agent(self, bids: Dict[str, Dict[str, Any]]) -> str:
        """Select the best agent based on bids."""
        best_agent = None
        best_score = -1
        
        for agent_name, bid in bids.items():
            # Calculate composite score
            score = (
                bid.get("capability_score", 0) * 0.4 +
                bid.get("confidence", 0) * 0.3 +
                (1.0 / max(bid.get("estimated_time", 1), 1)) * 0.2 +
                (1.0 / max(bid.get("cost", 1), 1)) * 0.1
            )
            
            if score > best_score:
                best_score = score
                best_agent = agent_name
        
        return best_agent
    
    def get_negotiation_status(self, negotiation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a negotiation."""
        return self.active_negotiations.get(negotiation_id)
