"""Utilities module for common functionality."""

# Import only what exists
try:
    from .performance_optimizer import (
        get_performance_tracker, get_response_cache, get_connection_pool,
        get_parallel_executor, cleanup_resources, performance_monitor
    )
    __all__ = [
        "get_performance_tracker", "get_response_cache", "get_connection_pool",
        "get_parallel_executor", "cleanup_resources", "performance_monitor"
    ]
except ImportError:
    __all__ = []
