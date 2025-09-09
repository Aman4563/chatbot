"""Agent schemas for the agentic chat system."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentInfo(BaseModel):
    """Agent information and capabilities."""
    name: str = Field(..., description="Agent name")
    display_name: str = Field(..., description="Human-readable agent name")
    description: str = Field(..., description="Agent description")
    capabilities: List[str] = Field(..., description="List of agent capabilities")
    tools: List[str] = Field(..., description="List of tools available to the agent")
    status: str = Field(..., description="Current status of the agent")


class AgentStatus(BaseModel):
    """Agent status information."""
    name: str = Field(..., description="Agent name")
    status: str = Field(..., description="Current status")
    last_activity: Optional[str] = Field(default=None, description="Last activity timestamp")
    error_count: int = Field(default=0, description="Number of errors")
    success_count: int = Field(default=0, description="Number of successful operations")
    average_response_time: Optional[float] = Field(default=None, description="Average response time in seconds")
