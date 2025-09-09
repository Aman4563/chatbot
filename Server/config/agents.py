"""Agent configurations for the agentic chat system."""

from typing import Dict, Any, List


# Agent configurations
AGENT_CONFIG: Dict[str, Dict[str, Any]] = {
    "chat_agent": {
        "name": "Chat Agent",
        "description": "Main conversation orchestrator and coordinator",
        "capabilities": [
            "conversation_management",
            "context_awareness",
            "multi_modal_processing",
            "tool_orchestration",
            "response_synthesis"
        ],
        "tools": [
            "llm_provider",
            "document_processor",
            "web_search",
            "image_generation"
        ],
        "default_model": "mistral-large",
        "max_context_length": 8192,
        "temperature": 0.7,
        "streaming": True,
        "enabled": True,
        "priority": 1,  # Highest priority
    },
    "file_agent": {
        "name": "File Processing Agent",
        "description": "Specialized agent for document and file processing",
        "capabilities": [
            "document_analysis",
            "content_extraction",
            "file_validation",
            "format_conversion",
            "metadata_extraction"
        ],
        "tools": [
            "pdf_processor",
            "docx_processor",
            "image_analyzer",
            "code_analyzer",
            "csv_processor"
        ],
        "default_model": "gpt-4o",  # Better for document analysis
        "max_file_size": 50 * 1024 * 1024,  # 50MB
        "supported_formats": [
            "pdf", "docx", "txt", "csv", "json", "xml", "md",
            "jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff",
            "py", "js", "ts", "java", "cpp", "go", "rs"
        ],
        "enabled": True,
        "priority": 2,
    },
    "search_agent": {
        "name": "Search Agent",
        "description": "Specialized agent for web search and information retrieval",
        "capabilities": [
            "web_search",
            "result_filtering",
            "information_synthesis",
            "citation_management",
            "query_optimization"
        ],
        "tools": [
            "web_search",
            "result_analyzer",
            "citation_extractor"
        ],
        "default_model": "gemini-1.5-flash",  # Fast and efficient
        "max_results": 10,
        "search_providers": ["duckduckgo", "google"],
        "enabled": True,
        "priority": 3,
    },
    "image_agent": {
        "name": "Image Generation Agent",
        "description": "Specialized agent for image generation and processing",
        "capabilities": [
            "image_generation",
            "prompt_optimization",
            "image_analysis",
            "style_transfer",
            "image_editing"
        ],
        "tools": [
            "image_generator",
            "image_analyzer",
            "prompt_optimizer"
        ],
        "default_model": "gpt-4o",  # Good for prompt understanding
        "image_providers": ["openai", "stability", "midjourney"],
        "max_images_per_request": 4,
        "enabled": True,
        "priority": 4,
    },
    "code_agent": {
        "name": "Code Analysis Agent",
        "description": "Specialized agent for code analysis and generation",
        "capabilities": [
            "code_analysis",
            "code_generation",
            "bug_detection",
            "code_explanation",
            "refactoring_suggestions"
        ],
        "tools": [
            "code_analyzer",
            "syntax_highlighter",
            "code_formatter",
            "dependency_analyzer"
        ],
        "default_model": "gpt-4o",  # Best for code understanding
        "supported_languages": [
            "python", "javascript", "typescript", "java", "cpp", "go", "rust",
            "html", "css", "sql", "bash", "powershell"
        ],
        "enabled": True,
        "priority": 5,
    },
    "data_agent": {
        "name": "Data Analysis Agent",
        "description": "Specialized agent for data analysis and visualization",
        "capabilities": [
            "data_analysis",
            "statistical_computing",
            "data_visualization",
            "pattern_recognition",
            "predictive_modeling"
        ],
        "tools": [
            "data_processor",
            "statistical_analyzer",
            "chart_generator",
            "csv_analyzer"
        ],
        "default_model": "gpt-4o",  # Good for data analysis
        "max_data_size": 100 * 1024 * 1024,  # 100MB
        "supported_formats": ["csv", "json", "xlsx", "parquet"],
        "enabled": True,
        "priority": 6,
    },
    "metadata_agent": {
        "name": "Metadata Agent",
        "description": "Specialized agent for collecting and providing user metadata",
        "capabilities": [
            "timezone_detection",
            "location_detection",
            "datetime_processing",
            "device_detection",
            "user_context_analysis",
            "metadata_caching"
        ],
        "tools": [
            "timezone_tool",
            "location_tool",
            "datetime_tool",
            "user_agent_tool"
        ],
        "default_model": "gemini-2.0-flash",  # Fast and efficient for metadata
        "cache_ttl": 3600,  # 1 hour
        "max_cache_size": 1000,
        "enabled": True,
        "priority": 2,  # High priority for search enhancement
    },
}

# Agent routing rules
AGENT_ROUTING_RULES: Dict[str, List[str]] = {
    "file_processing": [
        "file_agent",
        "chat_agent"
    ],
    "web_search": [
        "search_agent",
        "chat_agent"
    ],
    "image_generation": [
        "image_agent",
        "chat_agent"
    ],
    "code_analysis": [
        "code_agent",
        "chat_agent"
    ],
    "data_analysis": [
        "data_agent",
        "chat_agent"
    ],
    "general_chat": [
        "chat_agent"
    ],
    "metadata_collection": [
        "metadata_agent",
        "chat_agent"
    ],
}

# Agent collaboration patterns
AGENT_COLLABORATION: Dict[str, Dict[str, Any]] = {
    "file_analysis": {
        "primary": "file_agent",
        "secondary": ["chat_agent"],
        "workflow": [
            "file_agent.extract_content",
            "file_agent.analyze_content",
            "chat_agent.synthesize_response"
        ]
    },
    "research_task": {
        "primary": "search_agent",
        "secondary": ["chat_agent"],
        "workflow": [
            "search_agent.search_web",
            "search_agent.filter_results",
            "chat_agent.synthesize_response"
        ]
    },
    "creative_task": {
        "primary": "image_agent",
        "secondary": ["chat_agent"],
        "workflow": [
            "image_agent.optimize_prompt",
            "image_agent.generate_image",
            "chat_agent.synthesize_response"
        ]
    },
    "code_review": {
        "primary": "code_agent",
        "secondary": ["chat_agent"],
        "workflow": [
            "code_agent.analyze_code",
            "code_agent.detect_issues",
            "chat_agent.synthesize_response"
        ]
    },
    "enhanced_search": {
        "primary": "metadata_agent",
        "secondary": ["search_agent", "chat_agent"],
        "workflow": [
            "metadata_agent.collect_metadata",
            "search_agent.enhanced_search",
            "chat_agent.synthesize_response"
        ]
    },
}

# Agent performance metrics
AGENT_METRICS: Dict[str, Dict[str, Any]] = {
    "chat_agent": {
        "response_time_target": 2.0,  # seconds
        "accuracy_target": 0.95,
        "user_satisfaction_target": 0.9,
        "error_rate_target": 0.05,
    },
    "file_agent": {
        "response_time_target": 5.0,  # seconds
        "accuracy_target": 0.98,
        "user_satisfaction_target": 0.9,
        "error_rate_target": 0.02,
    },
    "search_agent": {
        "response_time_target": 3.0,  # seconds
        "accuracy_target": 0.9,
        "user_satisfaction_target": 0.85,
        "error_rate_target": 0.1,
    },
    "image_agent": {
        "response_time_target": 10.0,  # seconds
        "accuracy_target": 0.85,
        "user_satisfaction_target": 0.8,
        "error_rate_target": 0.15,
    },
    "code_agent": {
        "response_time_target": 4.0,  # seconds
        "accuracy_target": 0.92,
        "user_satisfaction_target": 0.88,
        "error_rate_target": 0.08,
    },
    "data_agent": {
        "response_time_target": 6.0,  # seconds
        "accuracy_target": 0.95,
        "user_satisfaction_target": 0.9,
        "error_rate_target": 0.05,
    },
    "metadata_agent": {
        "response_time_target": 1.0,  # seconds - should be very fast
        "accuracy_target": 0.9,
        "user_satisfaction_target": 0.85,
        "error_rate_target": 0.1,
    },
}


def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """Get configuration for a specific agent."""
    return AGENT_CONFIG.get(agent_name, {})


def get_available_agents() -> List[str]:
    """Get list of all available agent names."""
    return list(AGENT_CONFIG.keys())


def get_enabled_agents() -> List[str]:
    """Get list of enabled agent names."""
    return [
        name for name, config in AGENT_CONFIG.items()
        if config.get("enabled", False)
    ]


def get_agents_by_capability(capability: str) -> List[str]:
    """Get list of agents that support a specific capability."""
    return [
        name for name, config in AGENT_CONFIG.items()
        if capability in config.get("capabilities", [])
    ]


def get_agent_routing_rules(intent: str) -> List[str]:
    """Get agent routing rules for a specific intent."""
    return AGENT_ROUTING_RULES.get(intent, ["chat_agent"])


def get_agent_collaboration_pattern(pattern_name: str) -> Dict[str, Any]:
    """Get agent collaboration pattern by name."""
    return AGENT_COLLABORATION.get(pattern_name, {})


def get_agent_metrics(agent_name: str) -> Dict[str, Any]:
    """Get performance metrics for a specific agent."""
    return AGENT_METRICS.get(agent_name, {})


def validate_agent_config(agent_name: str) -> bool:
    """Validate that an agent configuration is complete."""
    config = get_agent_config(agent_name)
    if not config:
        return False
    
    required_fields = [
        "name", "description", "capabilities", "tools", "enabled"
    ]
    
    return all(field in config for field in required_fields)


def get_agent_priority(agent_name: str) -> int:
    """Get priority for a specific agent (lower number = higher priority)."""
    config = get_agent_config(agent_name)
    return config.get("priority", 999)


def get_agents_by_priority() -> List[str]:
    """Get list of agents sorted by priority."""
    return sorted(
        get_available_agents(),
        key=get_agent_priority
    )


def get_default_agent() -> str:
    """Get the default agent name."""
    return "chat_agent"


def get_fallback_agents() -> List[str]:
    """Get list of fallback agents in order of preference."""
    return [
        "chat_agent",
        "file_agent",
        "search_agent"
    ]
