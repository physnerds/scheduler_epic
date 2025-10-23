"""
Timing utilities for tracking function execution times.
"""

import time
import logging
from functools import wraps
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager


class FunctionTimer:
    """Class to track function execution times."""
    
    def __init__(self):
        self.function_times: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("FunctionTimer")
    
    def clear(self):
        """Clear all recorded times."""
        self.function_times.clear()
    
    def get_times(self) -> Dict[str, Dict[str, Any]]:
        """Get all recorded function times."""
        return self.function_times.copy()
    
    def record_function_time(self, function_name: str, start_time: datetime, end_time: datetime, duration: float):
        """Record timing information for a function."""
        self.function_times[function_name] = {
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": duration
        }
        self.logger.debug(f"Function '{function_name}' executed in {duration:.4f} seconds")


# Global timer instance
_global_timer = FunctionTimer()


def get_global_timer() -> FunctionTimer:
    """Get the global function timer instance."""
    return _global_timer


def time_function(timer: Optional[FunctionTimer] = None, function_name: Optional[str] = None):
    """
    Decorator to automatically time function execution.
    
    Args:
        timer: FunctionTimer instance to use (defaults to global timer)
        function_name: Custom name for the function (defaults to actual function name)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal timer, function_name
            
            if timer is None:
                timer = get_global_timer()
            
            if function_name is None:
                name = f"{func.__module__}.{func.__name__}" if hasattr(func, '__module__') else func.__name__
            else:
                name = function_name
            
            start_time = datetime.now()
            start_perf = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = datetime.now()
                end_perf = time.perf_counter()
                duration = end_perf - start_perf
                
                timer.record_function_time(name, start_time, end_time, duration)
        
        return wrapper
    return decorator


@contextmanager
def time_context(name: str, timer: Optional[FunctionTimer] = None):
    """
    Context manager to time a block of code.
    
    Args:
        name: Name for this timing context
        timer: FunctionTimer instance to use (defaults to global timer)
    """
    if timer is None:
        timer = get_global_timer()
    
    start_time = datetime.now()
    start_perf = time.perf_counter()
    
    try:
        yield timer
    finally:
        end_time = datetime.now()
        end_perf = time.perf_counter()
        duration = end_perf - start_perf
        
        timer.record_function_time(name, start_time, end_time, duration)