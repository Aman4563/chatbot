"""Agent Output Passing Mechanisms for data flow between agents."""

from typing import Dict, Any, List, Optional, Union, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import asyncio
from abc import ABC, abstractmethod

from .base import BaseAgent
from .communication import AgentMessage, MessageType, Priority, AgentOutput
from graphs.state import AgentState


class OutputType(Enum):
    """Types of agent outputs."""
    TEXT = "text"
    DATA = "data"
    FILE = "file"
    IMAGE = "image"
    STRUCTURED = "structured"
    STREAM = "stream"
    ERROR = "error"


class DataFormat(Enum):
    """Data format types."""
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    MARKDOWN = "markdown"
    HTML = "html"
    BINARY = "binary"
    BASE64 = "base64"


@dataclass
class OutputMetadata:
    """Metadata for agent outputs."""
    output_id: str
    agent_name: str
    output_type: OutputType
    data_format: DataFormat
    size: int
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    quality_score: Optional[float] = None
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
    error_info: Optional[Dict[str, Any]] = None


@dataclass
class AgentOutputData:
    """Structured agent output data."""
    metadata: OutputMetadata
    content: Any
    context: Dict[str, Any] = field(default_factory=dict)
    validation_results: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "metadata": {
                "output_id": self.metadata.output_id,
                "agent_name": self.metadata.agent_name,
                "output_type": self.metadata.output_type.value,
                "data_format": self.metadata.data_format.value,
                "size": self.metadata.size,
                "timestamp": self.metadata.timestamp.isoformat(),
                "expires_at": self.metadata.expires_at.isoformat() if self.metadata.expires_at else None,
                "tags": self.metadata.tags,
                "dependencies": self.metadata.dependencies,
                "quality_score": self.metadata.quality_score,
                "confidence_score": self.metadata.confidence_score,
                "processing_time": self.metadata.processing_time,
                "error_info": self.metadata.error_info
            },
            "content": self.content,
            "context": self.context,
            "validation_results": self.validation_results
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentOutputData":
        """Create from dictionary."""
        metadata_data = data["metadata"]
        metadata = OutputMetadata(
            output_id=metadata_data["output_id"],
            agent_name=metadata_data["agent_name"],
            output_type=OutputType(metadata_data["output_type"]),
            data_format=DataFormat(metadata_data["data_format"]),
            size=metadata_data["size"],
            timestamp=datetime.fromisoformat(metadata_data["timestamp"]),
            expires_at=datetime.fromisoformat(metadata_data["expires_at"]) if metadata_data.get("expires_at") else None,
            tags=metadata_data.get("tags", []),
            dependencies=metadata_data.get("dependencies", []),
            quality_score=metadata_data.get("quality_score"),
            confidence_score=metadata_data.get("confidence_score"),
            processing_time=metadata_data.get("processing_time"),
            error_info=metadata_data.get("error_info")
        )
        
        return cls(
            metadata=metadata,
            content=data["content"],
            context=data.get("context", {}),
            validation_results=data.get("validation_results")
        )


class OutputValidator(ABC):
    """Abstract base class for output validation."""
    
    @abstractmethod
    async def validate(self, output_data: AgentOutputData) -> Dict[str, Any]:
        """Validate agent output data."""
        pass


class TextOutputValidator(OutputValidator):
    """Validator for text outputs."""
    
    async def validate(self, output_data: AgentOutputData) -> Dict[str, Any]:
        """Validate text output."""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "metrics": {}
        }
        
        content = output_data.content
        
        if not isinstance(content, str):
            validation_result["is_valid"] = False
            validation_result["errors"].append("Content must be a string")
            return validation_result
        
        # Check content length
        content_length = len(content)
        validation_result["metrics"]["content_length"] = content_length
        
        if content_length == 0:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Content cannot be empty")
        elif content_length > 1000000:  # 1MB limit
            validation_result["warnings"].append("Content is very large")
        
        # Check for basic text quality
        word_count = len(content.split())
        validation_result["metrics"]["word_count"] = word_count
        
        if word_count < 10:
            validation_result["warnings"].append("Content is very short")
        
        # Check for encoding issues
        try:
            content.encode('utf-8')
        except UnicodeEncodeError:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Content contains invalid characters")
        
        return validation_result


class DataOutputValidator(OutputValidator):
    """Validator for structured data outputs."""
    
    async def validate(self, output_data: AgentOutputData) -> Dict[str, Any]:
        """Validate structured data output."""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "metrics": {}
        }
        
        content = output_data.content
        
        # Check if content is serializable
        try:
            json.dumps(content)
            validation_result["metrics"]["is_serializable"] = True
        except (TypeError, ValueError):
            validation_result["is_valid"] = False
            validation_result["errors"].append("Content is not JSON serializable")
            return validation_result
        
        # Check data structure
        if isinstance(content, dict):
            validation_result["metrics"]["data_type"] = "dict"
            validation_result["metrics"]["key_count"] = len(content)
        elif isinstance(content, list):
            validation_result["metrics"]["data_type"] = "list"
            validation_result["metrics"]["item_count"] = len(content)
        else:
            validation_result["metrics"]["data_type"] = type(content).__name__
        
        # Check data size
        data_size = len(json.dumps(content))
        validation_result["metrics"]["data_size"] = data_size
        
        if data_size > 10000000:  # 10MB limit
            validation_result["warnings"].append("Data size is very large")
        
        return validation_result


class OutputTransformer(ABC):
    """Abstract base class for output transformation."""
    
    @abstractmethod
    async def transform(self, output_data: AgentOutputData, target_format: DataFormat) -> AgentOutputData:
        """Transform output to target format."""
        pass


class JSONTransformer(OutputTransformer):
    """Transformer for JSON data."""
    
    async def transform(self, output_data: AgentOutputData, target_format: DataFormat) -> AgentOutputData:
        """Transform to JSON format."""
        if target_format == DataFormat.JSON:
            return output_data
        
        # Convert to JSON
        try:
            if isinstance(output_data.content, str):
                # Try to parse as JSON first
                try:
                    json_content = json.loads(output_data.content)
                except json.JSONDecodeError:
                    # If not JSON, wrap in object
                    json_content = {"text": output_data.content}
            else:
                json_content = output_data.content
            
            # Create new output data
            new_metadata = OutputMetadata(
                output_id=f"{output_data.metadata.output_id}_json",
                agent_name=output_data.metadata.agent_name,
                output_type=output_data.metadata.output_type,
                data_format=DataFormat.JSON,
                size=len(json.dumps(json_content)),
                timestamp=datetime.now(),
                tags=output_data.metadata.tags + ["transformed"],
                dependencies=[output_data.metadata.output_id],
                quality_score=output_data.metadata.quality_score,
                confidence_score=output_data.metadata.confidence_score
            )
            
            return AgentOutputData(
                metadata=new_metadata,
                content=json_content,
                context=output_data.context,
                validation_results=output_data.validation_results
            )
            
        except Exception as e:
            # Return error output
            error_metadata = OutputMetadata(
                output_id=f"{output_data.metadata.output_id}_error",
                agent_name=output_data.metadata.agent_name,
                output_type=OutputType.ERROR,
                data_format=DataFormat.JSON,
                size=0,
                error_info={"transformation_error": str(e)}
            )
            
            return AgentOutputData(
                metadata=error_metadata,
                content={"error": str(e)},
                context=output_data.context
            )


class OutputPassingManager:
    """Manages output passing between agents."""
    
    def __init__(self):
        self.output_storage: Dict[str, AgentOutputData] = {}
        self.output_validators: Dict[OutputType, OutputValidator] = {
            OutputType.TEXT: TextOutputValidator(),
            OutputType.DATA: DataOutputValidator(),
            OutputType.STRUCTURED: DataOutputValidator()
        }
        self.output_transformers: Dict[DataFormat, OutputTransformer] = {
            DataFormat.JSON: JSONTransformer()
        }
        self.output_dependencies: Dict[str, List[str]] = {}
        self.passing_history: List[Dict[str, Any]] = []
        self.max_storage_size = 1000
        self.max_history_size = 10000
    
    async def store_output(self, output_data: AgentOutputData) -> bool:
        """Store agent output for later retrieval."""
        try:
            # Validate output
            validator = self.output_validators.get(output_data.metadata.output_type)
            if validator:
                validation_results = await validator.validate(output_data)
                output_data.validation_results = validation_results
                
                if not validation_results.get("is_valid", True):
                    print(f"Output validation failed: {validation_results.get('errors', [])}")
                    return False
            
            # Store output
            self.output_storage[output_data.metadata.output_id] = output_data
            
            # Track dependencies
            for dep in output_data.metadata.dependencies:
                if dep not in self.output_dependencies:
                    self.output_dependencies[dep] = []
                self.output_dependencies[dep].append(output_data.metadata.output_id)
            
            # Clean up old outputs
            await self._cleanup_old_outputs()
            
            return True
            
        except Exception as e:
            print(f"Error storing output: {e}")
            return False
    
    async def retrieve_output(self, output_id: str) -> Optional[AgentOutputData]:
        """Retrieve stored output by ID."""
        output_data = self.output_storage.get(output_id)
        
        if not output_data:
            return None
        
        # Check if output has expired
        if output_data.metadata.expires_at and datetime.now() > output_data.metadata.expires_at:
            del self.output_storage[output_id]
            return None
        
        return output_data
    
    async def pass_output_to_agent(self, 
                                 output_id: str, 
                                 target_agent: str,
                                 transformation: Optional[DataFormat] = None) -> bool:
        """Pass output from one agent to another."""
        try:
            # Retrieve output
            output_data = await self.retrieve_output(output_id)
            if not output_data:
                return False
            
            # Transform if needed
            if transformation and transformation != output_data.metadata.data_format:
                transformer = self.output_transformers.get(transformation)
                if transformer:
                    output_data = await transformer.transform(output_data, transformation)
            
            # Create message for target agent
            message = AgentMessage(
                id=f"output_pass_{output_id}_{target_agent}",
                sender=output_data.metadata.agent_name,
                recipient=target_agent,
                message_type=MessageType.NOTIFICATION,
                content={
                    "output_id": output_id,
                    "output_data": output_data.to_dict(),
                    "passing_context": {
                        "source_agent": output_data.metadata.agent_name,
                        "target_agent": target_agent,
                        "transformation": transformation.value if transformation else None,
                        "timestamp": datetime.now().isoformat()
                    }
                },
                priority=Priority.NORMAL,
                requires_response=False
            )
            
            # Record passing
            self.passing_history.append({
                "output_id": output_id,
                "source_agent": output_data.metadata.agent_name,
                "target_agent": target_agent,
                "timestamp": datetime.now(),
                "transformation": transformation.value if transformation else None
            })
            
            # Clean up history
            if len(self.passing_history) > self.max_history_size:
                self.passing_history = self.passing_history[-self.max_history_size:]
            
            return True
            
        except Exception as e:
            print(f"Error passing output to agent: {e}")
            return False
    
    async def get_outputs_by_agent(self, agent_name: str) -> List[AgentOutputData]:
        """Get all outputs from a specific agent."""
        outputs = []
        for output_data in self.output_storage.values():
            if output_data.metadata.agent_name == agent_name:
                outputs.append(output_data)
        
        # Sort by timestamp
        outputs.sort(key=lambda x: x.metadata.timestamp, reverse=True)
        return outputs
    
    async def get_outputs_by_type(self, output_type: OutputType) -> List[AgentOutputData]:
        """Get all outputs of a specific type."""
        outputs = []
        for output_data in self.output_storage.values():
            if output_data.metadata.output_type == output_type:
                outputs.append(output_data)
        
        # Sort by timestamp
        outputs.sort(key=lambda x: x.metadata.timestamp, reverse=True)
        return outputs
    
    async def get_output_dependencies(self, output_id: str) -> List[str]:
        """Get outputs that depend on the given output."""
        return self.output_dependencies.get(output_id, [])
    
    async def get_output_lineage(self, output_id: str) -> List[str]:
        """Get the lineage of an output (all dependencies)."""
        lineage = []
        visited = set()
        
        def _get_lineage_recursive(current_id: str):
            if current_id in visited:
                return
            visited.add(current_id)
            
            output_data = self.output_storage.get(current_id)
            if output_data:
                lineage.append(current_id)
                for dep in output_data.metadata.dependencies:
                    _get_lineage_recursive(dep)
        
        _get_lineage_recursive(output_id)
        return lineage
    
    async def _cleanup_old_outputs(self) -> None:
        """Clean up old and expired outputs."""
        current_time = datetime.now()
        to_remove = []
        
        for output_id, output_data in self.output_storage.items():
            # Remove expired outputs
            if output_data.metadata.expires_at and current_time > output_data.metadata.expires_at:
                to_remove.append(output_id)
            # Remove outputs older than 1 hour
            elif (current_time - output_data.metadata.timestamp).total_seconds() > 3600:
                to_remove.append(output_id)
        
        for output_id in to_remove:
            del self.output_storage[output_id]
            if output_id in self.output_dependencies:
                del self.output_dependencies[output_id]
        
        # Limit storage size
        if len(self.output_storage) > self.max_storage_size:
            # Remove oldest outputs
            sorted_outputs = sorted(
                self.output_storage.items(),
                key=lambda x: x[1].metadata.timestamp
            )
            
            excess_count = len(self.output_storage) - self.max_storage_size
            for i in range(excess_count):
                output_id = sorted_outputs[i][0]
                del self.output_storage[output_id]
                if output_id in self.output_dependencies:
                    del self.output_dependencies[output_id]
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get statistics about output storage."""
        stats = {
            "total_outputs": len(self.output_storage),
            "outputs_by_type": {},
            "outputs_by_agent": {},
            "total_size": 0,
            "passing_history_count": len(self.passing_history)
        }
        
        for output_data in self.output_storage.values():
            # Count by type
            output_type = output_data.metadata.output_type.value
            stats["outputs_by_type"][output_type] = stats["outputs_by_type"].get(output_type, 0) + 1
            
            # Count by agent
            agent_name = output_data.metadata.agent_name
            stats["outputs_by_agent"][agent_name] = stats["outputs_by_agent"].get(agent_name, 0) + 1
            
            # Total size
            stats["total_size"] += output_data.metadata.size
        
        return stats


class StreamingOutputManager:
    """Manages streaming outputs between agents."""
    
    def __init__(self):
        self.active_streams: Dict[str, AsyncIterator[str]] = {}
        self.stream_metadata: Dict[str, Dict[str, Any]] = {}
        self.stream_subscribers: Dict[str, List[str]] = {}
    
    async def create_stream(self, 
                          stream_id: str, 
                          source_agent: str, 
                          stream_type: str = "text") -> bool:
        """Create a new streaming output."""
        try:
            self.stream_metadata[stream_id] = {
                "source_agent": source_agent,
                "stream_type": stream_type,
                "created_at": datetime.now(),
                "status": "active",
                "subscriber_count": 0
            }
            self.stream_subscribers[stream_id] = []
            return True
        except Exception as e:
            print(f"Error creating stream: {e}")
            return False
    
    async def subscribe_to_stream(self, stream_id: str, agent_name: str) -> bool:
        """Subscribe an agent to a stream."""
        if stream_id not in self.stream_metadata:
            return False
        
        if agent_name not in self.stream_subscribers[stream_id]:
            self.stream_subscribers[stream_id].append(agent_name)
            self.stream_metadata[stream_id]["subscriber_count"] += 1
        
        return True
    
    async def publish_to_stream(self, stream_id: str, data: str) -> bool:
        """Publish data to a stream."""
        if stream_id not in self.stream_metadata:
            return False
        
        # Update stream metadata
        self.stream_metadata[stream_id]["last_update"] = datetime.now()
        
        return True
    
    async def close_stream(self, stream_id: str) -> bool:
        """Close a stream."""
        if stream_id in self.stream_metadata:
            self.stream_metadata[stream_id]["status"] = "closed"
            self.stream_metadata[stream_id]["closed_at"] = datetime.now()
            return True
        return False
    
    def get_stream_info(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a stream."""
        return self.stream_metadata.get(stream_id)
    
    def get_active_streams(self) -> List[str]:
        """Get list of active streams."""
        return [
            stream_id for stream_id, metadata in self.stream_metadata.items()
            if metadata["status"] == "active"
        ]
