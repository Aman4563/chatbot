# Agent Communication System

## Overview

The Agent Communication System enables true inter-agent communication and collaboration in the chatbot project. This system transforms the previous hierarchical tool-based approach into a dynamic multi-agent system where agents can communicate directly, share outputs, and collaborate on complex tasks.

## Architecture

### Core Components

1. **Agent Communication Layer** (`communication.py`)
   - Manages message passing between agents
   - Handles request/response patterns
   - Supports broadcasting and negotiation

2. **Agent Selection System** (`selection.py`)
   - Dynamic agent selection based on capabilities
   - Multiple selection strategies (capability-based, load-balanced, performance-based, hybrid)
   - Intelligent routing for optimal agent assignment

3. **Output Passing Manager** (`output_passing.py`)
   - Manages data flow between agents
   - Supports different output types and formats
   - Handles output validation and transformation

4. **Collaborative Workflow Manager** (`collaboration.py`)
   - Executes multi-agent workflows
   - Supports sequential, parallel, conditional, and iterative workflows
   - Manages workflow dependencies and coordination

5. **Agent Coordinator** (`coordinator.py`)
   - Main orchestration system
   - Coordinates requests across multiple agents
   - Manages system-wide communication and collaboration

## Key Features

### ✅ True Agent Communication
- **Direct Agent-to-Agent Communication**: Agents can send messages directly to each other
- **Request/Response Patterns**: Structured communication with timeouts and error handling
- **Message Broadcasting**: Send messages to multiple agents simultaneously
- **Negotiation Support**: Agents can negotiate task assignments

### ✅ Dynamic Agent Selection
- **Capability-Based Selection**: Choose agents based on their capabilities and tools
- **Load Balancing**: Distribute tasks based on current agent load
- **Performance-Based Selection**: Select agents based on historical performance
- **Hybrid Selection**: Combine multiple strategies for optimal results

### ✅ Output Passing & Data Flow
- **Structured Output Management**: Store and retrieve outputs between agents
- **Data Validation**: Validate outputs before passing to other agents
- **Format Transformation**: Convert outputs between different formats
- **Dependency Tracking**: Track data dependencies across agent interactions

### ✅ Collaborative Workflows
- **Sequential Workflows**: Execute agents in sequence with data passing
- **Parallel Workflows**: Execute multiple agents simultaneously
- **Conditional Workflows**: Execute agents based on conditions
- **Iterative Workflows**: Repeat workflows until convergence

### ✅ Advanced Coordination
- **Multi-Agent Orchestration**: Coordinate complex multi-agent tasks
- **Workflow Management**: Create and execute sophisticated workflows
- **Error Handling**: Robust error handling and recovery
- **Performance Monitoring**: Track system performance and agent statistics

## Usage Examples

### Basic Agent Communication

```python
from agents import AgentCoordinator, CoordinationRequest, TaskRequirement

# Initialize coordinator
coordinator = AgentCoordinator()
await coordinator.initialize()

# Create a request
request = CoordinationRequest(
    request_id="example_001",
    user_input="Analyze this document and search for related information",
    context={"attachments": [...]},
    requirements=TaskRequirement(
        task_type="file_analysis_with_search",
        required_capabilities=["document_analysis", "web_search"],
        required_tools=["document_processor", "web_search"],
        complexity="complex",
        collaboration_needed=True
    )
)

# Coordinate the request
result = await coordinator.coordinate_request(request)
print(f"Status: {result.status}")
print(f"Selected agents: {result.selected_agents}")
```

### Agent Selection Strategies

```python
from agents import SelectionStrategy

# Different selection strategies
strategies = [
    SelectionStrategy.CAPABILITY_BASED,    # Based on agent capabilities
    SelectionStrategy.LOAD_BALANCED,       # Based on current load
    SelectionStrategy.PERFORMANCE_BASED,   # Based on historical performance
    SelectionStrategy.COLLABORATIVE,       # Based on collaboration patterns
    SelectionStrategy.HYBRID              # Combined approach
]

for strategy in strategies:
    result = await coordinator.agent_selector.select_agents(requirement, strategy)
    print(f"{strategy.value}: {result.selected_agents}")
```

### Collaborative Workflows

```python
from agents import WorkflowType, WorkflowStep

# Create workflow steps
steps = [
    WorkflowStep(
        step_id="step_1",
        agent_name="file_agent",
        method="process",
        inputs={"file_data": "..."},
        outputs=["processed_content"]
    ),
    WorkflowStep(
        step_id="step_2",
        agent_name="search_agent",
        method="search",
        inputs={"query": "..."},
        outputs=["search_results"],
        dependencies=["step_1"]
    )
]

# Create and execute workflow
workflow = CollaborativeWorkflow(
    workflow_id="example_workflow",
    name="Example Workflow",
    workflow_type=WorkflowType.SEQUENTIAL,
    steps=steps,
    initiator="user",
    participants=["file_agent", "search_agent"]
)

results = await coordinator.workflow_executor.execute_workflow(workflow)
```

## Agent Types

### ChatAgent
- **Role**: Main conversation orchestrator
- **Capabilities**: Conversation management, context awareness, multi-modal processing
- **Tools**: LLM provider, response synthesis, conversation tools
- **Communication**: Coordinates with other agents for complex tasks

### FileAgent
- **Role**: Document and file processing specialist
- **Capabilities**: Document analysis, content extraction, file validation
- **Tools**: PDF processor, DOCX processor, image analyzer, code analyzer
- **Communication**: Receives files from ChatAgent, passes processed content to other agents

### SearchAgent
- **Role**: Web search and information retrieval specialist
- **Capabilities**: Web search, result filtering, information synthesis
- **Tools**: Web search, result analyzer, citation extractor
- **Communication**: Receives search queries, passes results to other agents

### ImageAgent
- **Role**: Image generation and processing specialist
- **Capabilities**: Image generation, prompt optimization, image analysis
- **Tools**: Image generator, image analyzer, prompt optimizer
- **Communication**: Generates images based on requests, analyzes images for other agents

## Communication Patterns

### 1. Request-Response Pattern
```
ChatAgent -> FileAgent: "Process this document"
FileAgent -> ChatAgent: "Here's the processed content"
```

### 2. Broadcast Pattern
```
ChatAgent -> [All Agents]: "System status update"
```

### 3. Pipeline Pattern
```
FileAgent -> SearchAgent -> ChatAgent: Sequential processing with data flow
```

### 4. Collaborative Pattern
```
ChatAgent coordinates:
  - FileAgent processes document
  - SearchAgent finds related info
  - ChatAgent synthesizes final response
```

## Configuration

### Agent Configuration
```python
# config/agents.py
AGENT_CONFIG = {
    "chat_agent": {
        "name": "Chat Agent",
        "capabilities": ["conversation_management", "context_awareness"],
        "tools": ["llm_provider", "response_synthesis"],
        "priority": 1,
        "enabled": True
    },
    # ... other agents
}
```

### Collaboration Patterns
```python
AGENT_COLLABORATION = {
    "file_analysis": {
        "primary": "file_agent",
        "secondary": ["chat_agent"],
        "workflow": [
            "file_agent.extract_content",
            "file_agent.analyze_content",
            "chat_agent.synthesize_response"
        ]
    }
}
```

## Performance Monitoring

### System Statistics
```python
stats = coordinator.get_system_statistics()
print(f"Total agents: {stats['total_agents']}")
print(f"Active requests: {stats['active_requests']}")
print(f"Communication stats: {stats['communication_stats']}")
```

### Agent Performance
```python
agent_stats = coordinator.agent_selector.get_agent_statistics()
print(f"Success rate: {agent_stats['success_rate']}")
print(f"Average response time: {agent_stats['avg_response_time']}")
```

## Error Handling

The system includes comprehensive error handling:

- **Agent Communication Errors**: Timeout handling, retry mechanisms
- **Workflow Execution Errors**: Step failure recovery, dependency resolution
- **Output Validation Errors**: Data validation, format conversion errors
- **Selection Errors**: Fallback strategies, agent availability checks

## Testing

Run the test suite to verify the system:

```bash
cd Server
python test_agent_communication.py
```

Run examples to see the system in action:

```bash
python example_agent_usage.py
```

## Migration from Previous System

### Before (Tool-Based)
```python
# Old approach - ChatAgent contains all tools
class ChatAgent:
    def _initialize_tools(self):
        self.tools = {
            "document_processor": DocumentProcessorTool(),
            "web_search": WebSearchTool(),
            "image_generator": ImageGenerationTool()
        }
```

### After (Agent Communication)
```python
# New approach - True agent communication
class ChatAgent:
    async def _coordinate_with_agents(self, state):
        # Request processing from specialized agents
        file_result = await self._request_agent_processing(
            "file_agent", "process_files", context
        )
        search_result = await self._request_agent_processing(
            "search_agent", "search_web", context
        )
```

## Benefits

1. **Scalability**: Easy to add new agents and capabilities
2. **Modularity**: Each agent has specific responsibilities
3. **Flexibility**: Dynamic agent selection and collaboration
4. **Performance**: Parallel processing and load balancing
5. **Maintainability**: Clear separation of concerns
6. **Extensibility**: Easy to add new communication patterns

## Future Enhancements

- **Agent Learning**: Agents learn from interactions and improve performance
- **Dynamic Workflow Creation**: AI-generated workflows based on task requirements
- **Advanced Negotiation**: More sophisticated agent negotiation protocols
- **Distributed Processing**: Support for distributed agent execution
- **Real-time Collaboration**: Live collaboration between agents

## Conclusion

The Agent Communication System transforms the chatbot from a simple tool-based system into a sophisticated multi-agent platform. Agents can now communicate directly, collaborate on complex tasks, and provide more intelligent and comprehensive responses to user requests.

This system enables:
- **True Multi-Agent Collaboration**: Agents work together on complex tasks
- **Dynamic Task Assignment**: Optimal agent selection based on capabilities and load
- **Flexible Workflows**: Support for various workflow patterns
- **Robust Communication**: Reliable message passing and error handling
- **Performance Optimization**: Load balancing and performance-based selection

The system is designed to be extensible, maintainable, and scalable, providing a solid foundation for advanced AI agent interactions.
