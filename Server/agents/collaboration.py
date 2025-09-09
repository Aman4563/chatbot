"""Collaborative Workflow Manager for multi-agent coordination."""

from typing import Dict, Any, List, Optional, AsyncIterator, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseAgent, AgentRegistry
    from .communication import AgentCommunicationLayer, AgentMessage, MessageType, Priority, AgentOutput
    from .selection import AgentSelector, TaskRequirement, SelectionStrategy
    from .output_passing import OutputPassingManager, AgentOutputData, OutputType, DataFormat, OutputMetadata
from config.agents import get_agent_collaboration_pattern, get_agent_routing_rules


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class WorkflowType(Enum):
    """Types of collaborative workflows."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    ITERATIVE = "iterative"
    PIPELINE = "pipeline"


@dataclass
class WorkflowStep:
    """Individual step in a workflow."""
    step_id: str
    agent_name: str
    method: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class CollaborativeWorkflow:
    """Collaborative workflow definition."""
    workflow_id: str
    name: str
    description: str
    workflow_type: WorkflowType
    steps: List[WorkflowStep]
    initiator: str
    participants: List[str]
    context: Dict[str, Any] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowExecutor:
    """Executes collaborative workflows."""
    
    def __init__(self, 
                 communication_layer: "AgentCommunicationLayer",
                 output_passing_manager: "OutputPassingManager",
                 agent_registry: "AgentRegistry"):
        self.communication_layer = communication_layer
        self.output_passing_manager = output_passing_manager
        self.agent_registry = agent_registry
        self.active_workflows: Dict[str, CollaborativeWorkflow] = {}
        self.workflow_history: List[CollaborativeWorkflow] = []
        self.max_history_size = 1000
    
    async def execute_workflow(self, workflow: CollaborativeWorkflow) -> Dict[str, Any]:
        """Execute a collaborative workflow."""
        try:
            # Validate workflow
            if not await self._validate_workflow(workflow):
                raise ValueError("Invalid workflow")
            
            # Add to active workflows
            self.active_workflows[workflow.workflow_id] = workflow
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.now()
            
            # Execute based on workflow type
            if workflow.workflow_type == WorkflowType.SEQUENTIAL:
                results = await self._execute_sequential_workflow(workflow)
            elif workflow.workflow_type == WorkflowType.PARALLEL:
                results = await self._execute_parallel_workflow(workflow)
            elif workflow.workflow_type == WorkflowType.CONDITIONAL:
                results = await self._execute_conditional_workflow(workflow)
            elif workflow.workflow_type == WorkflowType.ITERATIVE:
                results = await self._execute_iterative_workflow(workflow)
            elif workflow.workflow_type == WorkflowType.PIPELINE:
                results = await self._execute_pipeline_workflow(workflow)
            else:
                raise ValueError(f"Unsupported workflow type: {workflow.workflow_type}")
            
            # Update workflow status
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            workflow.results = results
            
            # Move to history
            self.workflow_history.append(workflow)
            if len(self.workflow_history) > self.max_history_size:
                self.workflow_history.pop(0)
            
            # Remove from active workflows
            if workflow.workflow_id in self.active_workflows:
                del self.active_workflows[workflow.workflow_id]
            
            return results
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.errors.append(str(e))
            workflow.completed_at = datetime.now()
            
            # Move to history even if failed
            self.workflow_history.append(workflow)
            if len(self.workflow_history) > self.max_history_size:
                self.workflow_history.pop(0)
            
            # Remove from active workflows
            if workflow.workflow_id in self.active_workflows:
                del self.active_workflows[workflow.workflow_id]
            
            raise
    
    async def _execute_sequential_workflow(self, workflow: CollaborativeWorkflow) -> Dict[str, Any]:
        """Execute workflow steps sequentially."""
        results = {}
        
        for step in workflow.steps:
            try:
                # Check dependencies
                if not await self._check_dependencies(step, results):
                    raise ValueError(f"Dependencies not met for step {step.step_id}")
                
                # Execute step
                step_result = await self._execute_step(step, workflow.context, results)
                results[step.step_id] = step_result
                
                # Store output if specified
                if step.outputs:
                    await self._store_step_outputs(step, step_result)
                
            except Exception as e:
                step.status = WorkflowStatus.FAILED
                step.error = str(e)
                raise
        
        return results
    
    async def _execute_parallel_workflow(self, workflow: CollaborativeWorkflow) -> Dict[str, Any]:
        """Execute workflow steps in parallel."""
        # Group steps by dependency level
        dependency_groups = self._group_steps_by_dependencies(workflow.steps)
        results = {}
        
        for group in dependency_groups:
            # Execute all steps in the group in parallel
            tasks = []
            for step in group:
                task = asyncio.create_task(self._execute_step(step, workflow.context, results))
                tasks.append((step, task))
            
            # Wait for all tasks in the group to complete
            for step, task in tasks:
                try:
                    step_result = await task
                    results[step.step_id] = step_result
                    
                    # Store output if specified
                    if step.outputs:
                        await self._store_step_outputs(step, step_result)
                        
                except Exception as e:
                    step.status = WorkflowStatus.FAILED
                    step.error = str(e)
                    raise
        
        return results
    
    async def _execute_conditional_workflow(self, workflow: CollaborativeWorkflow) -> Dict[str, Any]:
        """Execute workflow with conditional branching."""
        results = {}
        
        for step in workflow.steps:
            try:
                # Check if step should be executed based on conditions
                if not await self._evaluate_step_conditions(step, workflow.context, results):
                    step.status = WorkflowStatus.CANCELLED
                    continue
                
                # Check dependencies
                if not await self._check_dependencies(step, results):
                    raise ValueError(f"Dependencies not met for step {step.step_id}")
                
                # Execute step
                step_result = await self._execute_step(step, workflow.context, results)
                results[step.step_id] = step_result
                
                # Store output if specified
                if step.outputs:
                    await self._store_step_outputs(step, step_result)
                
            except Exception as e:
                step.status = WorkflowStatus.FAILED
                step.error = str(e)
                raise
        
        return results
    
    async def _execute_iterative_workflow(self, workflow: CollaborativeWorkflow) -> Dict[str, Any]:
        """Execute workflow with iterative steps."""
        results = {}
        iteration_count = 0
        max_iterations = workflow.metadata.get("max_iterations", 10)
        
        while iteration_count < max_iterations:
            iteration_results = {}
            
            for step in workflow.steps:
                try:
                    # Check if step should be executed in this iteration
                    if not await self._should_execute_in_iteration(step, iteration_count, results):
                        continue
                    
                    # Check dependencies
                    if not await self._check_dependencies(step, results):
                        continue
                    
                    # Execute step
                    step_result = await self._execute_step(step, workflow.context, results)
                    iteration_results[step.step_id] = step_result
                    
                    # Store output if specified
                    if step.outputs:
                        await self._store_step_outputs(step, step_result)
                    
                except Exception as e:
                    step.status = WorkflowStatus.FAILED
                    step.error = str(e)
                    raise
            
            # Merge iteration results
            results.update(iteration_results)
            
            # Check convergence criteria
            if await self._check_convergence(workflow, results):
                break
            
            iteration_count += 1
        
        return results
    
    async def _execute_pipeline_workflow(self, workflow: CollaborativeWorkflow) -> Dict[str, Any]:
        """Execute workflow as a pipeline."""
        results = {}
        
        # Sort steps by dependencies to create pipeline order
        pipeline_steps = self._sort_steps_for_pipeline(workflow.steps)
        
        for step in pipeline_steps:
            try:
                # Check dependencies
                if not await self._check_dependencies(step, results):
                    raise ValueError(f"Dependencies not met for step {step.step_id}")
                
                # Execute step
                step_result = await self._execute_step(step, workflow.context, results)
                results[step.step_id] = step_result
                
                # Store output if specified
                if step.outputs:
                    await self._store_step_outputs(step, step_result)
                
            except Exception as e:
                step.status = WorkflowStatus.FAILED
                step.error = str(e)
                raise
        
        return results
    
    async def _execute_step(self, step: WorkflowStep, context: Dict[str, Any], 
                          previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step."""
        step.status = WorkflowStatus.RUNNING
        step.start_time = datetime.now()
        
        try:
            # Get agent
            agent = self.agent_registry.get_agent(step.agent_name)
            if not agent:
                raise ValueError(f"Agent {step.agent_name} not found")
            
            # Prepare inputs
            inputs = self._prepare_step_inputs(step, context, previous_results)
            
            # Create request message
            message = AgentMessage(
                id=f"workflow_{step.step_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                sender="workflow_executor",
                recipient=step.agent_name,
                message_type=MessageType.REQUEST,
                content={
                    "method": step.method,
                    "inputs": inputs,
                    "step_id": step.step_id,
                    "context": context
                },
                priority=Priority.HIGH,
                requires_response=True,
                timeout=step.timeout or 30.0
            )
            
            # Send message and wait for response
            await self.communication_layer.send_message(message)
            response = await self.communication_layer.wait_for_response(message.id, timeout=step.timeout or 30.0)
            
            if not response:
                raise TimeoutError(f"Timeout waiting for response from {step.agent_name}")
            
            if response.status != "success":
                raise ValueError(f"Agent {step.agent_name} returned error: {response.error_message}")
            
            step.status = WorkflowStatus.COMPLETED
            step.end_time = datetime.now()
            step.result = response.results
            
            return response.results
            
        except Exception as e:
            step.status = WorkflowStatus.FAILED
            step.error = str(e)
            step.end_time = datetime.now()
            
            # Retry if possible
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = WorkflowStatus.PENDING
                await asyncio.sleep(1.0)  # Brief delay before retry
                return await self._execute_step(step, context, previous_results)
            
            raise
    
    async def _validate_workflow(self, workflow: CollaborativeWorkflow) -> bool:
        """Validate workflow before execution."""
        # Check if all agents exist
        for step in workflow.steps:
            if not self.agent_registry.get_agent(step.agent_name):
                return False
        
        # Check for circular dependencies
        if self._has_circular_dependencies(workflow.steps):
            return False
        
        return True
    
    async def _check_dependencies(self, step: WorkflowStep, results: Dict[str, Any]) -> bool:
        """Check if step dependencies are satisfied."""
        for dep in step.dependencies:
            if dep not in results:
                return False
        return True
    
    async def _store_step_outputs(self, step: WorkflowStep, step_result: Dict[str, Any]) -> None:
        """Store step outputs for other steps to use."""
        for output_name in step.outputs:
            if output_name in step_result:
                output_id = f"{step.step_id}_{output_name}"
                await self.output_passing_manager.store_output(
                    AgentOutputData(
                        metadata=OutputMetadata(
                            output_id=output_id,
                            agent_name=step.agent_name,
                            output_type=OutputType.DATA,
                            data_format=DataFormat.JSON,
                            size=len(str(step_result[output_name]))
                        ),
                        content=step_result[output_name]
                    )
                )
    
    def _prepare_step_inputs(self, step: WorkflowStep, context: Dict[str, Any], 
                           previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare inputs for a workflow step."""
        inputs = step.inputs.copy()
        
        # Add context
        inputs.update(context)
        
        # Add previous results
        for dep in step.dependencies:
            if dep in previous_results:
                inputs[f"result_{dep}"] = previous_results[dep]
        
        return inputs
    
    def _group_steps_by_dependencies(self, steps: List[WorkflowStep]) -> List[List[WorkflowStep]]:
        """Group steps by dependency level for parallel execution."""
        groups = []
        remaining_steps = steps.copy()
        
        while remaining_steps:
            # Find steps with no unsatisfied dependencies
            current_group = []
            for step in remaining_steps[:]:
                if all(dep in [s.step_id for s in steps if s not in remaining_steps] for dep in step.dependencies):
                    current_group.append(step)
                    remaining_steps.remove(step)
            
            if not current_group:
                # Circular dependency or error
                break
            
            groups.append(current_group)
        
        return groups
    
    def _sort_steps_for_pipeline(self, steps: List[WorkflowStep]) -> List[WorkflowStep]:
        """Sort steps for pipeline execution."""
        # Simple topological sort
        sorted_steps = []
        remaining_steps = steps.copy()
        
        while remaining_steps:
            # Find steps with no unsatisfied dependencies
            for step in remaining_steps[:]:
                if all(dep in [s.step_id for s in sorted_steps] for dep in step.dependencies):
                    sorted_steps.append(step)
                    remaining_steps.remove(step)
                    break
            else:
                # Circular dependency
                break
        
        return sorted_steps
    
    def _has_circular_dependencies(self, steps: List[WorkflowStep]) -> bool:
        """Check for circular dependencies in workflow steps."""
        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(step_id: str) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)
            
            # Find step by ID
            step = next((s for s in steps if s.step_id == step_id), None)
            if not step:
                return False
            
            for dep in step.dependencies:
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(step_id)
            return False
        
        for step in steps:
            if step.step_id not in visited:
                if has_cycle(step.step_id):
                    return True
        
        return False
    
    async def _evaluate_step_conditions(self, step: WorkflowStep, context: Dict[str, Any], 
                                      results: Dict[str, Any]) -> bool:
        """Evaluate conditions for conditional workflow steps."""
        # Default implementation - always execute
        # Override in subclasses for specific condition logic
        return True
    
    async def _should_execute_in_iteration(self, step: WorkflowStep, iteration_count: int, 
                                         results: Dict[str, Any]) -> bool:
        """Check if step should execute in current iteration."""
        # Default implementation - execute every iteration
        # Override in subclasses for specific iteration logic
        return True
    
    async def _check_convergence(self, workflow: CollaborativeWorkflow, results: Dict[str, Any]) -> bool:
        """Check if iterative workflow has converged."""
        # Default implementation - never converge
        # Override in subclasses for specific convergence logic
        return False
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow."""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            return {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "status": workflow.status.value,
                "created_at": workflow.created_at.isoformat(),
                "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                "participants": workflow.participants,
                "step_count": len(workflow.steps),
                "completed_steps": sum(1 for step in workflow.steps if step.status == WorkflowStatus.COMPLETED),
                "errors": workflow.errors
            }
        
        # Check history
        for workflow in self.workflow_history:
            if workflow.workflow_id == workflow_id:
                return {
                    "workflow_id": workflow.workflow_id,
                    "name": workflow.name,
                    "status": workflow.status.value,
                    "created_at": workflow.created_at.isoformat(),
                    "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                    "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                    "participants": workflow.participants,
                    "step_count": len(workflow.steps),
                    "completed_steps": sum(1 for step in workflow.steps if step.status == WorkflowStatus.COMPLETED),
                    "errors": workflow.errors
                }
        
        return None
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all active workflows."""
        return [self.get_workflow_status(wid) for wid in self.active_workflows.keys()]
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow execution statistics."""
        total_workflows = len(self.workflow_history) + len(self.active_workflows)
        completed_workflows = sum(1 for w in self.workflow_history if w.status == WorkflowStatus.COMPLETED)
        failed_workflows = sum(1 for w in self.workflow_history if w.status == WorkflowStatus.FAILED)
        
        return {
            "total_workflows": total_workflows,
            "active_workflows": len(self.active_workflows),
            "completed_workflows": completed_workflows,
            "failed_workflows": failed_workflows,
            "success_rate": completed_workflows / total_workflows if total_workflows > 0 else 0,
            "workflow_types": {
                wtype.value: sum(1 for w in self.workflow_history if w.workflow_type == wtype)
                for wtype in WorkflowType
            }
        }
