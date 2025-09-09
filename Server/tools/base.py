"""Base tool class for agent capabilities."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class BaseTool(ABC):
    """Base class for all tools in the system."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.enabled = True
        self.rate_limit = None
        self.timeout = 30
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get tool information."""
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "rate_limit": self.rate_limit,
            "timeout": self.timeout,
            "schema": self.get_schema()
        }
    
    async def validate_input(self, **kwargs) -> bool:
        """Validate input parameters."""
        schema = self.get_schema()
        required_params = schema.get("required", [])
        
        for param in required_params:
            if param not in kwargs:
                return False
        
        return True
    
    async def handle_error(self, error: Exception) -> str:
        """Handle errors during tool execution."""
        return f"Error in {self.name}: {str(error)}"


class ToolRegistry:
    """Registry for managing all tools in the system."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool in the registry."""
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool information by name."""
        tool = self.get_tool(name)
        return tool.get_info() if tool else None
    
    def get_all_tool_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information for all registered tools."""
        return {name: tool.get_info() for name, tool in self._tools.items()}
    
    def get_tools_by_category(self, category: str) -> List[str]:
        """Get tools by category."""
        return [
            name for name, tool in self._tools.items()
            if hasattr(tool, 'category') and tool.category == category
        ]


# Global tool registry
tool_registry = ToolRegistry()
