"""Dynamic Agent Selection Logic for intelligent agent routing."""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime, timedelta

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseAgent, AgentRegistry
    from .communication import AgentCommunicationLayer, AgentMessage, MessageType, Priority
from config.agents import get_agent_config, get_agent_routing_rules, get_agent_collaboration_pattern


class SelectionStrategy(Enum):
    """Agent selection strategies."""
    CAPABILITY_BASED = "capability_based"
    LOAD_BALANCED = "load_balanced"
    PERFORMANCE_BASED = "performance_based"
    COLLABORATIVE = "collaborative"
    HYBRID = "hybrid"


@dataclass
class AgentCapability:
    """Agent capability definition."""
    name: str
    capabilities: List[str]
    tools: List[str]
    priority: int
    performance_metrics: Dict[str, float]
    current_load: float
    availability: bool
    last_used: Optional[datetime] = None


@dataclass
class TaskRequirement:
    """Task requirement definition."""
    task_type: str
    required_capabilities: List[str]
    required_tools: List[str]
    complexity: str  # "simple", "medium", "complex"
    priority: int
    estimated_duration: Optional[float] = None
    collaboration_needed: bool = False
    data_requirements: Dict[str, Any] = None


@dataclass
class SelectionResult:
    """Result of agent selection."""
    selected_agents: List[str]
    primary_agent: str
    secondary_agents: List[str]
    selection_strategy: SelectionStrategy
    confidence_score: float
    reasoning: str
    estimated_completion_time: Optional[float] = None
    collaboration_pattern: Optional[str] = None


class AgentSelector:
    """Dynamic agent selection system."""
    
    def __init__(self, agent_registry: "AgentRegistry", communication_layer: "AgentCommunicationLayer"):
        self.agent_registry = agent_registry
        self.communication_layer = communication_layer
        self.agent_capabilities: Dict[str, AgentCapability] = {}
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
        self.load_tracker: Dict[str, List[float]] = {}
        self.selection_history: List[SelectionResult] = []
        self.max_history_size = 1000
        
        # Initialize agent capabilities
        self._initialize_agent_capabilities()
    
    def _initialize_agent_capabilities(self) -> None:
        """Initialize agent capabilities from configuration."""
        for agent_name in self.agent_registry.list_agents():
            agent = self.agent_registry.get_agent(agent_name)
            if agent:
                config = get_agent_config(agent_name)
                capability = AgentCapability(
                    name=agent_name,
                    capabilities=config.get("capabilities", []),
                    tools=config.get("tools", []),
                    priority=config.get("priority", 999),
                    performance_metrics=config.get("performance_metrics", {}),
                    current_load=0.0,
                    availability=True,
                    last_used=None
                )
                self.agent_capabilities[agent_name] = capability
                self.performance_history[agent_name] = []
                self.load_tracker[agent_name] = []
    
    async def select_agents(self, 
                          task_requirement: TaskRequirement, 
                          strategy: SelectionStrategy = SelectionStrategy.HYBRID,
                          context: Optional[Dict[str, Any]] = None) -> SelectionResult:
        """Select the best agents for a given task."""
        
        # Update agent load information
        await self._update_agent_loads()
        
        # Apply selection strategy
        if strategy == SelectionStrategy.CAPABILITY_BASED:
            result = await self._capability_based_selection(task_requirement)
        elif strategy == SelectionStrategy.LOAD_BALANCED:
            result = await self._load_balanced_selection(task_requirement)
        elif strategy == SelectionStrategy.PERFORMANCE_BASED:
            result = await self._performance_based_selection(task_requirement)
        elif strategy == SelectionStrategy.COLLABORATIVE:
            result = await self._collaborative_selection(task_requirement)
        else:  # HYBRID
            result = await self._hybrid_selection(task_requirement)
        
        # Store selection in history
        self.selection_history.append(result)
        if len(self.selection_history) > self.max_history_size:
            self.selection_history.pop(0)
        
        return result
    
    async def _capability_based_selection(self, task_requirement: TaskRequirement) -> SelectionResult:
        """Select agents based on their capabilities."""
        suitable_agents = []
        
        for agent_name, capability in self.agent_capabilities.items():
            if not capability.availability:
                continue
            
            # Check if agent has required capabilities
            has_capabilities = all(
                cap in capability.capabilities 
                for cap in task_requirement.required_capabilities
            )
            
            # Check if agent has required tools
            has_tools = all(
                tool in capability.tools 
                for tool in task_requirement.required_tools
            )
            
            if has_capabilities and has_tools:
                # Calculate capability score
                capability_score = self._calculate_capability_score(capability, task_requirement)
                suitable_agents.append((agent_name, capability_score))
        
        # Sort by capability score
        suitable_agents.sort(key=lambda x: x[1], reverse=True)
        
        if not suitable_agents:
            return SelectionResult(
                selected_agents=[],
                primary_agent="",
                secondary_agents=[],
                selection_strategy=SelectionStrategy.CAPABILITY_BASED,
                confidence_score=0.0,
                reasoning="No suitable agents found with required capabilities"
            )
        
        # Select primary agent (best capability score)
        primary_agent = suitable_agents[0][0]
        
        # Select secondary agents if collaboration is needed
        secondary_agents = []
        if task_requirement.collaboration_needed and len(suitable_agents) > 1:
            secondary_agents = [agent[0] for agent in suitable_agents[1:3]]  # Top 2 secondary agents
        
        confidence_score = suitable_agents[0][1]
        
        return SelectionResult(
            selected_agents=[primary_agent] + secondary_agents,
            primary_agent=primary_agent,
            secondary_agents=secondary_agents,
            selection_strategy=SelectionStrategy.CAPABILITY_BASED,
            confidence_score=confidence_score,
            reasoning=f"Selected based on capability matching. Primary: {primary_agent} (score: {confidence_score:.2f})"
        )
    
    async def _load_balanced_selection(self, task_requirement: TaskRequirement) -> SelectionResult:
        """Select agents based on current load balancing."""
        available_agents = []
        
        for agent_name, capability in self.agent_capabilities.items():
            if not capability.availability:
                continue
            
            # Check basic requirements
            has_capabilities = all(
                cap in capability.capabilities 
                for cap in task_requirement.required_capabilities
            )
            
            if has_capabilities:
                # Calculate load score (lower is better)
                load_score = 1.0 - capability.current_load
                available_agents.append((agent_name, load_score))
        
        if not available_agents:
            return SelectionResult(
                selected_agents=[],
                primary_agent="",
                secondary_agents=[],
                selection_strategy=SelectionStrategy.LOAD_BALANCED,
                confidence_score=0.0,
                reasoning="No available agents found"
            )
        
        # Sort by load score (higher is better)
        available_agents.sort(key=lambda x: x[1], reverse=True)
        
        primary_agent = available_agents[0][0]
        secondary_agents = [agent[0] for agent in available_agents[1:2]] if task_requirement.collaboration_needed else []
        
        confidence_score = available_agents[0][1]
        
        return SelectionResult(
            selected_agents=[primary_agent] + secondary_agents,
            primary_agent=primary_agent,
            secondary_agents=secondary_agents,
            selection_strategy=SelectionStrategy.LOAD_BALANCED,
            confidence_score=confidence_score,
            reasoning=f"Selected based on load balancing. Primary: {primary_agent} (load: {1.0 - confidence_score:.2f})"
        )
    
    async def _performance_based_selection(self, task_requirement: TaskRequirement) -> SelectionResult:
        """Select agents based on historical performance."""
        performance_scores = []
        
        for agent_name, capability in self.agent_capabilities.items():
            if not capability.availability:
                continue
            
            # Check basic requirements
            has_capabilities = all(
                cap in capability.capabilities 
                for cap in task_requirement.required_capabilities
            )
            
            if has_capabilities:
                # Calculate performance score
                performance_score = self._calculate_performance_score(agent_name, task_requirement)
                performance_scores.append((agent_name, performance_score))
        
        if not performance_scores:
            return SelectionResult(
                selected_agents=[],
                primary_agent="",
                secondary_agents=[],
                selection_strategy=SelectionStrategy.PERFORMANCE_BASED,
                confidence_score=0.0,
                reasoning="No agents found with performance history"
            )
        
        # Sort by performance score
        performance_scores.sort(key=lambda x: x[1], reverse=True)
        
        primary_agent = performance_scores[0][0]
        secondary_agents = [agent[0] for agent in performance_scores[1:2]] if task_requirement.collaboration_needed else []
        
        confidence_score = performance_scores[0][1]
        
        return SelectionResult(
            selected_agents=[primary_agent] + secondary_agents,
            primary_agent=primary_agent,
            secondary_agents=secondary_agents,
            selection_strategy=SelectionStrategy.PERFORMANCE_BASED,
            confidence_score=confidence_score,
            reasoning=f"Selected based on performance history. Primary: {primary_agent} (score: {confidence_score:.2f})"
        )
    
    async def _collaborative_selection(self, task_requirement: TaskRequirement) -> SelectionResult:
        """Select agents for collaborative workflows."""
        # Check for predefined collaboration patterns
        collaboration_pattern = self._find_collaboration_pattern(task_requirement)
        
        if collaboration_pattern:
            pattern = get_agent_collaboration_pattern(collaboration_pattern)
            if pattern:
                primary_agent = pattern.get("primary", "")
                secondary_agents = pattern.get("secondary", [])
                
                # Verify agents are available
                available_agents = []
                if primary_agent in self.agent_capabilities and self.agent_capabilities[primary_agent].availability:
                    available_agents.append(primary_agent)
                
                for agent in secondary_agents:
                    if agent in self.agent_capabilities and self.agent_capabilities[agent].availability:
                        available_agents.append(agent)
                
                if available_agents:
                    return SelectionResult(
                        selected_agents=available_agents,
                        primary_agent=available_agents[0] if available_agents else "",
                        secondary_agents=available_agents[1:] if len(available_agents) > 1 else [],
                        selection_strategy=SelectionStrategy.COLLABORATIVE,
                        confidence_score=0.9,
                        reasoning=f"Selected based on collaboration pattern: {collaboration_pattern}",
                        collaboration_pattern=collaboration_pattern
                    )
        
        # Fallback to capability-based selection
        return await self._capability_based_selection(task_requirement)
    
    async def _hybrid_selection(self, task_requirement: TaskRequirement) -> SelectionResult:
        """Hybrid selection combining multiple strategies."""
        # Get results from different strategies
        capability_result = await self._capability_based_selection(task_requirement)
        load_result = await self._load_balanced_selection(task_requirement)
        performance_result = await self._performance_based_selection(task_requirement)
        
        # Weight the strategies
        weights = {
            "capability": 0.4,
            "load": 0.3,
            "performance": 0.3
        }
        
        # Calculate composite scores
        agent_scores = {}
        
        for result in [capability_result, load_result, performance_result]:
            if result.selected_agents:
                for agent in result.selected_agents:
                    if agent not in agent_scores:
                        agent_scores[agent] = 0.0
                    
                    if result.selection_strategy == SelectionStrategy.CAPABILITY_BASED:
                        agent_scores[agent] += result.confidence_score * weights["capability"]
                    elif result.selection_strategy == SelectionStrategy.LOAD_BALANCED:
                        agent_scores[agent] += result.confidence_score * weights["load"]
                    elif result.selection_strategy == SelectionStrategy.PERFORMANCE_BASED:
                        agent_scores[agent] += result.confidence_score * weights["performance"]
        
        if not agent_scores:
            return SelectionResult(
                selected_agents=[],
                primary_agent="",
                secondary_agents=[],
                selection_strategy=SelectionStrategy.HYBRID,
                confidence_score=0.0,
                reasoning="No suitable agents found with hybrid selection"
            )
        
        # Sort by composite score
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        
        primary_agent = sorted_agents[0][0]
        secondary_agents = [agent[0] for agent in sorted_agents[1:2]] if task_requirement.collaboration_needed else []
        
        confidence_score = sorted_agents[0][1]
        
        return SelectionResult(
            selected_agents=[primary_agent] + secondary_agents,
            primary_agent=primary_agent,
            secondary_agents=secondary_agents,
            selection_strategy=SelectionStrategy.HYBRID,
            confidence_score=confidence_score,
            reasoning=f"Selected using hybrid approach. Primary: {primary_agent} (composite score: {confidence_score:.2f})"
        )
    
    def _calculate_capability_score(self, capability: AgentCapability, task_requirement: TaskRequirement) -> float:
        """Calculate capability score for an agent."""
        score = 0.0
        
        # Capability matching
        capability_match = sum(
            1 for cap in task_requirement.required_capabilities 
            if cap in capability.capabilities
        ) / len(task_requirement.required_capabilities)
        score += capability_match * 0.4
        
        # Tool matching
        tool_match = sum(
            1 for tool in task_requirement.required_tools 
            if tool in capability.tools
        ) / len(task_requirement.required_tools) if task_requirement.required_tools else 1.0
        score += tool_match * 0.3
        
        # Priority factor (lower priority number = higher priority)
        priority_factor = 1.0 - (capability.priority / 10.0)
        score += priority_factor * 0.2
        
        # Load factor (lower load = better)
        load_factor = 1.0 - capability.current_load
        score += load_factor * 0.1
        
        return min(score, 1.0)
    
    def _calculate_performance_score(self, agent_name: str, task_requirement: TaskRequirement) -> float:
        """Calculate performance score based on historical data."""
        if agent_name not in self.performance_history:
            return 0.5  # Default score for new agents
        
        history = self.performance_history[agent_name]
        if not history:
            return 0.5
        
        # Calculate average performance metrics
        recent_history = history[-10:]  # Last 10 tasks
        
        avg_success_rate = sum(
            task.get("success", False) for task in recent_history
        ) / len(recent_history)
        
        avg_response_time = sum(
            task.get("response_time", 1.0) for task in recent_history
        ) / len(recent_history)
        
        avg_quality_score = sum(
            task.get("quality_score", 0.5) for task in recent_history
        ) / len(recent_history)
        
        # Normalize response time (lower is better)
        normalized_response_time = max(0, 1.0 - (avg_response_time / 10.0))
        
        # Calculate composite score
        score = (
            avg_success_rate * 0.4 +
            normalized_response_time * 0.3 +
            avg_quality_score * 0.3
        )
        
        return min(score, 1.0)
    
    def _find_collaboration_pattern(self, task_requirement: TaskRequirement) -> Optional[str]:
        """Find appropriate collaboration pattern for the task."""
        task_type = task_requirement.task_type.lower()
        
        if "file" in task_type or "document" in task_type:
            return "file_analysis"
        elif "search" in task_type or "research" in task_type:
            return "research_task"
        elif "image" in task_type or "generate" in task_type:
            return "creative_task"
        elif "complex" in task_type or "analysis" in task_type:
            return "complex_analysis"
        
        return None
    
    async def _update_agent_loads(self) -> None:
        """Update current load information for all agents."""
        current_time = datetime.now()
        
        for agent_name in self.agent_capabilities:
            # Get recent load data
            recent_loads = self.load_tracker.get(agent_name, [])
            
            # Remove old load data (older than 5 minutes)
            cutoff_time = current_time - timedelta(minutes=5)
            recent_loads = [
                load for load in recent_loads 
                if load.get("timestamp", current_time) > cutoff_time
            ]
            
            # Calculate current load
            if recent_loads:
                current_load = sum(load.get("load", 0) for load in recent_loads) / len(recent_loads)
            else:
                current_load = 0.0
            
            self.agent_capabilities[agent_name].current_load = current_load
            self.load_tracker[agent_name] = recent_loads
    
    async def record_task_completion(self, agent_name: str, task_result: Dict[str, Any]) -> None:
        """Record task completion for performance tracking."""
        if agent_name not in self.performance_history:
            self.performance_history[agent_name] = []
        
        # Add to performance history
        self.performance_history[agent_name].append({
            "timestamp": datetime.now(),
            "success": task_result.get("status") == "success",
            "response_time": task_result.get("processing_time", 0),
            "quality_score": task_result.get("quality_score", 0.5),
            "task_type": task_result.get("task_type", "unknown"),
            "error_message": task_result.get("error_message")
        })
        
        # Keep only recent history
        if len(self.performance_history[agent_name]) > 100:
            self.performance_history[agent_name] = self.performance_history[agent_name][-100:]
        
        # Update load tracker
        if agent_name not in self.load_tracker:
            self.load_tracker[agent_name] = []
        
        self.load_tracker[agent_name].append({
            "timestamp": datetime.now(),
            "load": 1.0 if task_result.get("status") == "success" else 0.5
        })
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics about agent performance and selection."""
        stats = {
            "total_agents": len(self.agent_capabilities),
            "available_agents": sum(1 for cap in self.agent_capabilities.values() if cap.availability),
            "average_load": sum(cap.current_load for cap in self.agent_capabilities.values()) / len(self.agent_capabilities),
            "selection_history_count": len(self.selection_history),
            "agent_performance": {}
        }
        
        for agent_name, history in self.performance_history.items():
            if history:
                recent_history = history[-10:]
                stats["agent_performance"][agent_name] = {
                    "success_rate": sum(task.get("success", False) for task in recent_history) / len(recent_history),
                    "avg_response_time": sum(task.get("response_time", 0) for task in recent_history) / len(recent_history),
                    "avg_quality_score": sum(task.get("quality_score", 0.5) for task in recent_history) / len(recent_history),
                    "total_tasks": len(history)
                }
        
        return stats
    
    def get_selection_recommendations(self, task_requirement: TaskRequirement) -> List[Dict[str, Any]]:
        """Get recommendations for agent selection."""
        recommendations = []
        
        # Check for agents with high success rate for similar tasks
        for agent_name, history in self.performance_history.items():
            if not history:
                continue
            
            similar_tasks = [
                task for task in history 
                if task.get("task_type", "").lower() in task_requirement.task_type.lower()
            ]
            
            if similar_tasks:
                success_rate = sum(task.get("success", False) for task in similar_tasks) / len(similar_tasks)
                if success_rate > 0.8:
                    recommendations.append({
                        "agent": agent_name,
                        "reason": f"High success rate ({success_rate:.2f}) for similar tasks",
                        "confidence": success_rate
                    })
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        
        return recommendations[:5]  # Top 5 recommendations
