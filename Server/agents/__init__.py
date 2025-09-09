"""Agent system initialization and integration."""

from .base import BaseAgent, AgentRegistry
from .communication import (
    AgentCommunicationLayer, 
    AgentMessage, 
    MessageType, 
    Priority, 
    AgentOutput,
    AgentCollaborationManager,
    AgentNegotiationManager
)
from .selection import AgentSelector, TaskRequirement, SelectionStrategy
from .output_passing import (
    OutputPassingManager, 
    AgentOutputData, 
    OutputType, 
    DataFormat,
    StreamingOutputManager
)
from .collaboration import (
    WorkflowExecutor, 
    CollaborativeWorkflow, 
    WorkflowType, 
    WorkflowStep, 
    WorkflowStatus
)
from .coordinator import AgentCoordinator, CoordinationRequest, CoordinationResult
from .chat_agent import ChatAgent
from .file_agent import FileAgent
from .search_agent import SearchAgent
from .image_agent import ImageAgent
from .metadata_agent import MetadataAgent

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentRegistry",
    
    # Communication
    "AgentCommunicationLayer",
    "AgentMessage",
    "MessageType",
    "Priority",
    "AgentOutput",
    "AgentCollaborationManager",
    "AgentNegotiationManager",
    
    # Selection
    "AgentSelector",
    "TaskRequirement",
    "SelectionStrategy",
    
    # Output passing
    "OutputPassingManager",
    "AgentOutputData",
    "OutputType",
    "DataFormat",
    "StreamingOutputManager",
    
    # Collaboration
    "WorkflowExecutor",
    "CollaborativeWorkflow",
    "WorkflowType",
    "WorkflowStep",
    "WorkflowStatus",
    
    # Coordination
    "AgentCoordinator",
    "CoordinationRequest",
    "CoordinationResult",
    
    # Specific agents
    "ChatAgent",
    "FileAgent",
    "SearchAgent",
    "ImageAgent",
    "MetadataAgent"
]