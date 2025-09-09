"""Main Agent Coordination System for orchestrating multi-agent workflows."""

from typing import Dict, Any, List, Optional, AsyncIterator, Union
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseAgent, AgentRegistry
    from .communication import AgentCommunicationLayer, AgentMessage, MessageType, Priority, AgentOutput
    from .selection import AgentSelector, TaskRequirement, SelectionStrategy
    from .output_passing import OutputPassingManager, AgentOutputData, OutputType, DataFormat
    from .collaboration import WorkflowExecutor, CollaborativeWorkflow, WorkflowType, WorkflowStep, WorkflowStatus
from config.agents import get_agent_collaboration_pattern, get_agent_routing_rules


@dataclass
class CoordinationRequest:
    """Request for agent coordination."""
    request_id: str
    user_input: str
    context: Dict[str, Any]
    requirements: "TaskRequirement"
    initiator: str = "user"
    priority: int = 1
    collaboration_needed: bool = False
    workflow_type: Optional["WorkflowType"] = None


@dataclass
class CoordinationResult:
    """Result of agent coordination."""
    request_id: str
    status: str  # "success", "error", "partial"
    selected_agents: List[str]
    workflow_id: Optional[str] = None
    results: Dict[str, Any] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    coordination_strategy: Optional[str] = None


class AgentCoordinator:
    """Main coordinator for multi-agent system."""
    
    def __init__(self):
        # Import here to avoid circular imports
        from .base import AgentRegistry
        from .communication import AgentCommunicationLayer
        from .output_passing import OutputPassingManager
        from .selection import AgentSelector
        from .collaboration import WorkflowExecutor
        
        self.agent_registry = AgentRegistry()
        self.communication_layer = AgentCommunicationLayer(self.agent_registry)
        self.output_passing_manager = OutputPassingManager()
        self.agent_selector = AgentSelector(self.agent_registry, self.communication_layer)
        self.workflow_executor = WorkflowExecutor(
            self.communication_layer,
            self.output_passing_manager,
            self.agent_registry
        )
        self.active_requests: Dict[str, CoordinationRequest] = {}
        self.coordination_history: List[CoordinationResult] = []
        self.agents: Dict[str, "BaseAgent"] = {}
        self.is_running = False
        self._coordination_tasks: List[asyncio.Task] = []
    
    async def initialize(self) -> None:
        """Initialize the coordination system."""
        try:
            # Initialize communication layer
            await self.communication_layer.initialize()
            
            # Register and initialize agents
            await self._register_agents()
            
            # Set up communication for all agents
            for agent in self.agents.values():
                agent.set_communication_layer(self.communication_layer)
                agent.set_output_passing_manager(self.output_passing_manager)
            
            # Start agent communication loops
            await self._start_agent_communication_loops()
            
            self.is_running = True
            print("Agent coordination system initialized successfully")
            
        except Exception as e:
            print(f"Error initializing coordination system: {e}")
            raise
    
    async def _register_agents(self) -> None:
        """Register all available agents."""
        from .chat_agent import ChatAgent
        from .file_agent import FileAgent
        from .search_agent import SearchAgent
        from .image_agent import ImageAgent
        from .metadata_agent import MetadataAgent
        
        # Create and register agents
        agents_to_register = [
            ChatAgent(),
            FileAgent(),
            SearchAgent(),
            ImageAgent(),
            MetadataAgent()
        ]
        
        for agent in agents_to_register:
            self.agents[agent.name] = agent
            self.agent_registry.register_agent(agent)
    
    async def _start_agent_communication_loops(self) -> None:
        """Start communication loops for all agents."""
        for agent in self.agents.values():
            if agent.is_communicating:
                task = asyncio.create_task(agent.start_communication_loop())
                self._coordination_tasks.append(task)
    
    async def coordinate_request(self, request: CoordinationRequest) -> CoordinationResult:
        """Coordinate a user request across multiple agents."""
        start_time = datetime.now()
        
        try:
            # Add to active requests
            self.active_requests[request.request_id] = request
            
            # Analyze request and determine coordination strategy
            coordination_strategy = await self._determine_coordination_strategy(request)
            
            # Select agents based on requirements
            selection_result = await self.agent_selector.select_agents(
                request.requirements,
                strategy=SelectionStrategy.HYBRID
            )
            
            if not selection_result.selected_agents:
                return CoordinationResult(
                    request_id=request.request_id,
                    status="error",
                    selected_agents=[],
                    error_message="No suitable agents found for the request",
                    coordination_strategy=coordination_strategy
                )
            
            # Execute coordination based on strategy
            if coordination_strategy == "collaborative_workflow":
                result = await self._execute_collaborative_workflow(request, selection_result)
            elif coordination_strategy == "sequential_processing":
                result = await self._execute_sequential_processing(request, selection_result)
            elif coordination_strategy == "parallel_processing":
                result = await self._execute_parallel_processing(request, selection_result)
            else:
                result = await self._execute_single_agent(request, selection_result)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            result.coordination_strategy = coordination_strategy
            
            # Add to history
            self.coordination_history.append(result)
            
            # Remove from active requests
            if request.request_id in self.active_requests:
                del self.active_requests[request.request_id]
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = CoordinationResult(
                request_id=request.request_id,
                status="error",
                selected_agents=[],
                error_message=str(e),
                execution_time=execution_time,
                coordination_strategy=coordination_strategy if 'coordination_strategy' in locals() else "unknown"
            )
            
            # Add to history
            self.coordination_history.append(result)
            
            # Remove from active requests
            if request.request_id in self.active_requests:
                del self.active_requests[request.request_id]
            
            return result
    
    async def _determine_coordination_strategy(self, request: CoordinationRequest) -> str:
        """Determine the best coordination strategy for a request."""
        # Check for predefined collaboration patterns
        collaboration_pattern = self._find_collaboration_pattern(request)
        if collaboration_pattern:
            return "collaborative_workflow"
        
        # Check if multiple agents are needed
        if len(request.requirements.required_capabilities) > 3:
            return "collaborative_workflow"
        
        # Check if parallel processing is beneficial
        if request.requirements.collaboration_needed:
            return "parallel_processing"
        
        # Check complexity
        if request.requirements.complexity == "complex":
            return "collaborative_workflow"
        
        # Default to single agent
        return "single_agent"
    
    def _find_collaboration_pattern(self, request: CoordinationRequest) -> Optional[str]:
        """Find appropriate collaboration pattern for the request."""
        task_type = request.requirements.task_type.lower()
        
        if "file" in task_type or "document" in task_type:
            return "file_analysis"
        elif "search" in task_type or "research" in task_type:
            return "research_task"
        elif "image" in task_type or "generate" in task_type:
            return "creative_task"
        elif "complex" in task_type or "analysis" in task_type:
            return "complex_analysis"
        
        return None
    
    async def _execute_collaborative_workflow(self, request: CoordinationRequest, 
                                            selection_result) -> CoordinationResult:
        """Execute a collaborative workflow."""
        try:
            # Create workflow
            workflow = await self._create_workflow_from_request(request, selection_result)
            
            # Execute workflow
            workflow_results = await self.workflow_executor.execute_workflow(workflow)
            
            return CoordinationResult(
                request_id=request.request_id,
                status="success",
                selected_agents=selection_result.selected_agents,
                workflow_id=workflow.workflow_id,
                results=workflow_results
            )
            
        except Exception as e:
            return CoordinationResult(
                request_id=request.request_id,
                status="error",
                selected_agents=selection_result.selected_agents,
                error_message=f"Workflow execution failed: {str(e)}"
            )
    
    async def _execute_sequential_processing(self, request: CoordinationRequest, 
                                           selection_result) -> CoordinationResult:
        """Execute agents sequentially."""
        try:
            results = {}
            
            for agent_name in selection_result.selected_agents:
                # Send request to agent
                success = await self._send_request_to_agent(
                    agent_name, request, results
                )
                
                if not success:
                    return CoordinationResult(
                        request_id=request.request_id,
                        status="partial",
                        selected_agents=selection_result.selected_agents,
                        results=results,
                        error_message=f"Failed to process with agent {agent_name}"
                    )
            
            return CoordinationResult(
                request_id=request.request_id,
                status="success",
                selected_agents=selection_result.selected_agents,
                results=results
            )
            
        except Exception as e:
            return CoordinationResult(
                request_id=request.request_id,
                status="error",
                selected_agents=selection_result.selected_agents,
                error_message=str(e)
            )
    
    async def _execute_parallel_processing(self, request: CoordinationRequest, 
                                         selection_result) -> CoordinationResult:
        """Execute agents in parallel."""
        try:
            # Create tasks for all agents
            tasks = []
            for agent_name in selection_result.selected_agents:
                task = asyncio.create_task(
                    self._send_request_to_agent(agent_name, request, {})
                )
                tasks.append((agent_name, task))
            
            # Wait for all tasks to complete
            results = {}
            for agent_name, task in tasks:
                try:
                    result = await task
                    results[agent_name] = result
                except Exception as e:
                    results[agent_name] = {"error": str(e)}
            
            # Check if any agents succeeded
            successful_agents = [
                name for name, result in results.items() 
                if "error" not in result
            ]
            
            if successful_agents:
                return CoordinationResult(
                    request_id=request.request_id,
                    status="success" if len(successful_agents) == len(selection_result.selected_agents) else "partial",
                    selected_agents=selection_result.selected_agents,
                    results=results
                )
            else:
                return CoordinationResult(
                    request_id=request.request_id,
                    status="error",
                    selected_agents=selection_result.selected_agents,
                    results=results,
                    error_message="All agents failed to process the request"
                )
            
        except Exception as e:
            return CoordinationResult(
                request_id=request.request_id,
                status="error",
                selected_agents=selection_result.selected_agents,
                error_message=str(e)
            )
    
    async def _execute_single_agent(self, request: CoordinationRequest, 
                                  selection_result) -> CoordinationResult:
        """Execute with a single agent."""
        try:
            primary_agent = selection_result.primary_agent
            
            # Send request to primary agent
            result = await self._send_request_to_agent(primary_agent, request, {})
            
            if result:
                return CoordinationResult(
                    request_id=request.request_id,
                    status="success",
                    selected_agents=[primary_agent],
                    results={primary_agent: result}
                )
            else:
                return CoordinationResult(
                    request_id=request.request_id,
                    status="error",
                    selected_agents=[primary_agent],
                    error_message=f"Agent {primary_agent} failed to process the request"
                )
            
        except Exception as e:
            return CoordinationResult(
                request_id=request.request_id,
                status="error",
                selected_agents=selection_result.selected_agents,
                error_message=str(e)
            )
    
    async def _create_workflow_from_request(self, request: CoordinationRequest, 
                                          selection_result) -> "CollaborativeWorkflow":
        """Create a collaborative workflow from a request."""
        workflow_id = f"workflow_{request.request_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create workflow steps
        steps = []
        for i, agent_name in enumerate(selection_result.selected_agents):
            step = WorkflowStep(
                step_id=f"step_{i+1}",
                agent_name=agent_name,
                method="process",
                inputs=request.context,
                dependencies=[f"step_{j+1}" for j in range(i)] if i > 0 else []
            )
            steps.append(step)
        
        # Determine workflow type
        workflow_type = WorkflowType.SEQUENTIAL
        if request.workflow_type:
            workflow_type = request.workflow_type
        elif len(selection_result.selected_agents) > 1:
            workflow_type = WorkflowType.PARALLEL
        
        # Import here to avoid circular import
        from .collaboration import CollaborativeWorkflow
        
        workflow = CollaborativeWorkflow(
            workflow_id=workflow_id,
            name=f"Workflow for {request.request_id}",
            description=f"Collaborative workflow for: {request.user_input}",
            workflow_type=workflow_type,
            steps=steps,
            initiator=request.initiator,
            participants=selection_result.selected_agents,
            context=request.context
        )
        
        return workflow
    
    async def _send_request_to_agent(self, agent_name: str, request: CoordinationRequest, 
                                   previous_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a request to a specific agent."""
        try:
            # Prepare message content
            content = {
                "user_input": request.user_input,
                "context": request.context,
                "requirements": {
                    "task_type": request.requirements.task_type,
                    "required_capabilities": request.requirements.required_capabilities,
                    "required_tools": request.requirements.required_tools,
                    "complexity": request.requirements.complexity
                },
                "previous_results": previous_results
            }
            
            # Create message
            message = AgentMessage(
                id=f"coord_request_{request.request_id}_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                sender="coordinator",
                recipient=agent_name,
                message_type=MessageType.REQUEST,
                content=content,
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
            print(f"Error sending request to agent {agent_name}: {e}")
            return None
    
    async def get_coordination_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a coordination request."""
        # Check active requests
        if request_id in self.active_requests:
            request = self.active_requests[request_id]
            return {
                "request_id": request_id,
                "status": "active",
                "user_input": request.user_input,
                "initiator": request.initiator,
                "priority": request.priority,
                "created_at": datetime.now().isoformat()
            }
        
        # Check history
        for result in self.coordination_history:
            if result.request_id == request_id:
                return {
                    "request_id": request_id,
                    "status": result.status,
                    "selected_agents": result.selected_agents,
                    "workflow_id": result.workflow_id,
                    "execution_time": result.execution_time,
                    "coordination_strategy": result.coordination_strategy,
                    "error_message": result.error_message
                }
        
        return None
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics."""
        return {
            "total_agents": len(self.agents),
            "active_requests": len(self.active_requests),
            "coordination_history_count": len(self.coordination_history),
            "communication_stats": self.communication_layer.get_agent_stats(),
            "output_storage_stats": self.output_passing_manager.get_storage_statistics(),
            "agent_selector_stats": self.agent_selector.get_agent_statistics(),
            "workflow_stats": self.workflow_executor.get_workflow_statistics()
        }
    
    async def shutdown(self) -> None:
        """Shutdown the coordination system."""
        self.is_running = False
        
        # Stop all agent communication
        for agent in self.agents.values():
            agent.stop_communication()
        
        # Cancel all coordination tasks
        for task in self._coordination_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._coordination_tasks:
            await asyncio.gather(*self._coordination_tasks, return_exceptions=True)
        
        print("Agent coordination system shutdown complete")
