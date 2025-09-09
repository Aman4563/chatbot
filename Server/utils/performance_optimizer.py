"""Performance optimization utilities for the chatbot system."""

import asyncio
import time
from typing import Dict, Any, List, Optional, Union, Callable
from functools import wraps, lru_cache
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import weakref
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PerformanceTracker:
    """Track and analyze performance metrics."""
    
    def __init__(self, max_metrics: int = 1000):
        self.metrics: List[PerformanceMetrics] = []
        self.max_metrics = max_metrics
        self._lock = asyncio.Lock()
    
    async def start_operation(self, operation_name: str, metadata: Dict[str, Any] = None) -> str:
        """Start tracking an operation."""
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        metric = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            metadata=metadata or {}
        )
        metric.metadata["operation_id"] = operation_id
        
        async with self._lock:
            self.metrics.append(metric)
            if len(self.metrics) > self.max_metrics:
                self.metrics.pop(0)
        
        return operation_id
    
    async def end_operation(self, operation_id: str, success: bool = True, error: str = None):
        """End tracking an operation."""
        end_time = time.time()
        
        async with self._lock:
            for metric in reversed(self.metrics):
                if metric.metadata.get("operation_id") == operation_id:
                    metric.end_time = end_time
                    metric.duration = end_time - metric.start_time
                    metric.success = success
                    metric.error = error
                    break
    
    def get_operation_stats(self, operation_name: str) -> Dict[str, Any]:
        """Get statistics for a specific operation."""
        relevant_metrics = [m for m in self.metrics if m.operation_name == operation_name and m.duration is not None]
        
        if not relevant_metrics:
            return {"count": 0}
        
        durations = [m.duration for m in relevant_metrics]
        success_count = sum(1 for m in relevant_metrics if m.success)
        
        return {
            "count": len(relevant_metrics),
            "success_count": success_count,
            "success_rate": success_count / len(relevant_metrics),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_duration": sum(durations)
        }


class ResponseCache:
    """Intelligent response caching system."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._lock = asyncio.Lock()
    
    def _generate_key(self, operation: str, params: Dict[str, Any]) -> str:
        """Generate cache key from operation and parameters."""
        # Sort parameters for consistent keys
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        key_string = f"{operation}:{sorted_params}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get(self, operation: str, params: Dict[str, Any]) -> Optional[Any]:
        """Get cached result."""
        key = self._generate_key(operation, params)
        
        async with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                if time.time() - entry["timestamp"] < self.ttl_seconds:
                    entry["access_count"] += 1
                    entry["last_accessed"] = time.time()
                    return entry["data"]
                else:
                    # Expired, remove it
                    del self.cache[key]
        
        return None
    
    async def set(self, operation: str, params: Dict[str, Any], data: Any):
        """Cache a result."""
        key = self._generate_key(operation, params)
        
        async with self._lock:
            # Remove oldest entries if cache is full
            if len(self.cache) >= self.max_size:
                # Remove least recently accessed entries
                sorted_items = sorted(
                    self.cache.items(),
                    key=lambda x: x[1].get("last_accessed", 0)
                )
                for old_key, _ in sorted_items[:self.max_size // 4]:  # Remove 25%
                    del self.cache[old_key]
            
            self.cache[key] = {
                "data": data,
                "timestamp": time.time(),
                "access_count": 1,
                "last_accessed": time.time()
            }
    
    async def clear(self):
        """Clear all cached data."""
        async with self._lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_accesses = sum(entry["access_count"] for entry in self.cache.values())
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "total_accesses": total_accesses,
            "hit_rate": total_accesses / max(len(self.cache), 1)
        }


class ConnectionPool:
    """HTTP connection pool for provider calls."""
    
    def __init__(self, max_connections: int = 100, max_connections_per_host: int = 30):
        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self._connector = None
        self._session = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with connection pooling."""
        if self._session is None or self._session.closed:
            self._connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=self.max_connections_per_host,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=aiohttp.ClientTimeout(total=30, connect=10)
            )
        return self._session
    
    async def close(self):
        """Close the connection pool."""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._connector:
            await self._connector.close()


class ParallelExecutor:
    """Execute operations in parallel with intelligent batching."""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    async def execute_parallel(
        self, 
        operations: List[Callable], 
        args_list: List[tuple] = None,
        kwargs_list: List[dict] = None,
        fail_fast: bool = False
    ) -> List[Any]:
        """Execute multiple operations in parallel."""
        if args_list is None:
            args_list = [()] * len(operations)
        if kwargs_list is None:
            kwargs_list = [{}] * len(operations)
        
        async def execute_with_semaphore(func, args, kwargs):
            async with self._semaphore:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return await asyncio.get_event_loop().run_in_executor(
                        self._executor, func, *args, **kwargs
                    )
        
        tasks = [
            execute_with_semaphore(func, args, kwargs)
            for func, args, kwargs in zip(operations, args_list, kwargs_list)
        ]
        
        if fail_fast:
            return await asyncio.gather(*tasks)
        else:
            return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def execute_batch(
        self,
        operation: Callable,
        batch_data: List[Any],
        batch_size: int = 5
    ) -> List[Any]:
        """Execute operation on batches of data."""
        results = []
        
        for i in range(0, len(batch_data), batch_size):
            batch = batch_data[i:i + batch_size]
            batch_tasks = [
                asyncio.create_task(operation(item))
                for item in batch
            ]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
        
        return results


def performance_monitor(operation_name: str = None):
    """Decorator to monitor function performance."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            tracker = get_performance_tracker()
            operation_id = await tracker.start_operation(name)
            
            try:
                result = await func(*args, **kwargs)
                await tracker.end_operation(operation_id, success=True)
                return result
            except Exception as e:
                await tracker.end_operation(operation_id, success=False, error=str(e))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                # Log sync performance (could be enhanced with proper logging)
                return result
            except Exception as e:
                duration = time.time() - start_time
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def cached_response(operation_name: str, ttl_seconds: int = 3600):
    """Decorator to cache function responses."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_response_cache()
            
            # Create cache key from function name and arguments
            cache_params = {
                "function": func.__name__,
                "args": args,
                "kwargs": kwargs
            }
            
            # Try to get from cache
            cached_result = await cache.get(operation_name, cache_params)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(operation_name, cache_params, result)
            
            return result
        
        return wrapper
    return decorator


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
):
    """Decorator for retry logic with exponential backoff."""
    def decorator(func):
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=base_delay, max=max_delay),
            retry=retry_if_exception_type((Exception,))
        )
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Global instances
_performance_tracker = None
_response_cache = None
_connection_pool = None
_parallel_executor = None


def get_performance_tracker() -> PerformanceTracker:
    """Get global performance tracker instance."""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker


def get_response_cache() -> ResponseCache:
    """Get global response cache instance."""
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache()
    return _response_cache


def get_connection_pool() -> ConnectionPool:
    """Get global connection pool instance."""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = ConnectionPool()
    return _connection_pool


def get_parallel_executor() -> ParallelExecutor:
    """Get global parallel executor instance."""
    global _parallel_executor
    if _parallel_executor is None:
        _parallel_executor = ParallelExecutor()
    return _parallel_executor


async def cleanup_resources():
    """Cleanup all global resources."""
    global _connection_pool
    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None
