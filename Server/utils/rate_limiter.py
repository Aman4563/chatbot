"""Simple rate limiter to prevent API quota exhaustion."""

import time
from typing import Dict, Optional
from collections import defaultdict, deque


class RateLimiter:
    """Simple rate limiter to prevent excessive API calls."""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, key: str = "default") -> bool:
        """
        Check if request is allowed.
        
        Args:
            key: Unique key for rate limiting (e.g., user_id, provider_name)
            
        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()
        request_times = self.requests[key]
        
        # Remove old requests outside the time window
        while request_times and request_times[0] <= now - self.time_window:
            request_times.popleft()
        
        # Check if we're under the limit
        if len(request_times) < self.max_requests:
            request_times.append(now)
            return True
        
        return False
    
    def get_remaining_requests(self, key: str = "default") -> int:
        """Get remaining requests in the current time window."""
        now = time.time()
        request_times = self.requests[key]
        
        # Remove old requests outside the time window
        while request_times and request_times[0] <= now - self.time_window:
            request_times.popleft()
        
        return max(0, self.max_requests - len(request_times))
    
    def get_reset_time(self, key: str = "default") -> Optional[float]:
        """Get time when the rate limit resets."""
        if not self.requests[key]:
            return None
        
        oldest_request = self.requests[key][0]
        return oldest_request + self.time_window


# Global rate limiter instance
api_rate_limiter = RateLimiter(max_requests=5, time_window=60)  # 5 requests per minute
