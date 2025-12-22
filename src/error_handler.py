#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Error Handler Module for K2Think API Proxy
==========================================
Centralized error handling with retry logic, circuit breaker pattern,
and structured error responses.

Features:
- Exponential backoff retry decorator
- Circuit breaker for upstream service failures
- Error categorization (transient vs permanent)
- Structured error response formatting
- Rate limit backoff handling
"""

import time
import logging
import functools
from typing import Callable, Any, Optional, List, Set
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Error categories for proper handling"""
    TRANSIENT = "transient"  # Temporary, retry possible
    PERMANENT = "permanent"  # Permanent, no retry
    RATE_LIMIT = "rate_limit"  # Rate limited, backoff needed
    NETWORK = "network"  # Network connectivity issue
    AUTHENTICATION = "authentication"  # Auth failure
    VALIDATION = "validation"  # Input validation error


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failure threshold reached, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for upstream service protection.
    
    Prevents cascading failures by temporarily blocking requests to failing services.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        name: str = "default"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes to close circuit from half-open
            timeout: Seconds before attempting recovery (open -> half-open)
            name: Circuit breaker identifier
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.name = name
        
        self.failure_count = 0
        self.success_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_failure_time: Optional[datetime] = None
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker '{self.name}': Attempting reset (half-open)")
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable for {self.timeout}s after failures."
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return datetime.now() - self.last_failure_time >= timedelta(seconds=self.timeout)
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info(f"Circuit breaker '{self.name}': Closing (service recovered)")
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.warning(f"Circuit breaker '{self.name}': Re-opening (recovery failed)")
            self.state = CircuitBreakerState.OPEN
            self.success_count = 0
        elif self.failure_count >= self.failure_threshold:
            logger.error(
                f"Circuit breaker '{self.name}': Opening "
                f"(threshold {self.failure_threshold} reached)"
            )
            self.state = CircuitBreakerState.OPEN
    
    def reset(self):
        """Manually reset circuit breaker"""
        logger.info(f"Circuit breaker '{self.name}': Manual reset")
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
    
    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class RetryStrategy:
    """
    Retry strategy with exponential backoff.
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        backoff_multiplier: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        retry_on_status_codes: Optional[Set[int]] = None
    ):
        """
        Initialize retry strategy.
        
        Args:
            max_attempts: Maximum retry attempts
            backoff_multiplier: Exponential backoff multiplier
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
            retry_on_status_codes: HTTP status codes that trigger retry
        """
        self.max_attempts = max_attempts
        self.backoff_multiplier = backoff_multiplier
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.retry_on_status_codes = retry_on_status_codes or {429, 500, 502, 503, 504}
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        delay = self.initial_delay * (self.backoff_multiplier ** (attempt - 1))
        return min(delay, self.max_delay)
    
    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Determine if retry should be attempted"""
        if attempt >= self.max_attempts:
            return False
        
        # Check if it's an HTTP error with retryable status code
        if hasattr(error, 'status_code'):
            return error.status_code in self.retry_on_status_codes
        
        # Retry on network errors
        error_str = str(error).lower()
        network_indicators = ['timeout', 'connection', 'network', 'unreachable']
        return any(indicator in error_str for indicator in network_indicators)


def retry_with_backoff(
    max_attempts: int = 3,
    backoff_multiplier: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_on_status_codes: Optional[Set[int]] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_multiplier: Multiplier for exponential backoff
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        retry_on_status_codes: HTTP status codes that should trigger retry
        
    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def fetch_data():
            return requests.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            strategy = RetryStrategy(
                max_attempts=max_attempts,
                backoff_multiplier=backoff_multiplier,
                initial_delay=initial_delay,
                max_delay=max_delay,
                retry_on_status_codes=retry_on_status_codes
            )
            
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if not strategy.should_retry(attempt, e):
                        logger.warning(
                            f"{func.__name__}: Non-retryable error on attempt {attempt}: {e}"
                        )
                        raise
                    
                    if attempt < max_attempts:
                        delay = strategy.calculate_delay(attempt)
                        logger.warning(
                            f"{func.__name__}: Attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__}: All {max_attempts} attempts failed. "
                            f"Last error: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


class ErrorHandler:
    """
    Centralized error handling with categorization and formatting.
    """
    
    def __init__(self):
        """Initialize error handler"""
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60
    ) -> CircuitBreaker:
        """
        Get or create circuit breaker by name.
        
        Args:
            name: Circuit breaker identifier
            failure_threshold: Failures before opening
            success_threshold: Successes to close
            timeout: Timeout before retry (seconds)
            
        Returns:
            CircuitBreaker instance
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(
                failure_threshold=failure_threshold,
                success_threshold=success_threshold,
                timeout=timeout,
                name=name
            )
        return self.circuit_breakers[name]
    
    @staticmethod
    def categorize_error(error: Exception) -> ErrorCategory:
        """
        Categorize error for appropriate handling.
        
        Args:
            error: Exception to categorize
            
        Returns:
            ErrorCategory enum value
        """
        error_str = str(error).lower()
        
        # Rate limiting
        if '429' in error_str or 'rate limit' in error_str or 'too many requests' in error_str:
            return ErrorCategory.RATE_LIMIT
        
        # Authentication
        if any(x in error_str for x in ['401', '403', 'unauthorized', 'forbidden', 'authentication']):
            return ErrorCategory.AUTHENTICATION
        
        # Validation
        if any(x in error_str for x in ['400', 'bad request', 'invalid', 'validation']):
            return ErrorCategory.VALIDATION
        
        # Network issues
        if any(x in error_str for x in ['timeout', 'connection', 'network', 'unreachable', 'dns']):
            return ErrorCategory.NETWORK
        
        # Server errors (potentially transient)
        if any(x in error_str for x in ['500', '502', '503', '504', 'server error', 'gateway']):
            return ErrorCategory.TRANSIENT
        
        # Default to permanent
        return ErrorCategory.PERMANENT
    
    @staticmethod
    def format_error_response(
        error: Exception,
        category: Optional[ErrorCategory] = None,
        context: Optional[dict] = None
    ) -> dict:
        """
        Format error into structured response.
        
        Args:
            error: Exception to format
            category: Error category (auto-detected if None)
            context: Additional context information
            
        Returns:
            Structured error dictionary
        """
        if category is None:
            category = ErrorHandler.categorize_error(error)
        
        response = {
            "error": {
                "message": str(error),
                "type": category.value,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        if context:
            response["error"]["context"] = context
        
        # Add retry suggestion for transient errors
        if category in [ErrorCategory.TRANSIENT, ErrorCategory.RATE_LIMIT, ErrorCategory.NETWORK]:
            response["error"]["retryable"] = True
            if category == ErrorCategory.RATE_LIMIT:
                response["error"]["retry_after"] = 60  # Suggest 60s wait
        else:
            response["error"]["retryable"] = False
        
        return response
    
    def get_all_circuit_breaker_states(self) -> List[dict]:
        """Get states of all circuit breakers"""
        return [cb.get_state() for cb in self.circuit_breakers.values()]
    
    def reset_all_circuit_breakers(self):
        """Reset all circuit breakers"""
        for cb in self.circuit_breakers.values():
            cb.reset()
        logger.info("All circuit breakers reset")


# Global error handler instance
error_handler = ErrorHandler()


# Convenience functions
def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get or create circuit breaker"""
    return error_handler.get_circuit_breaker(name, **kwargs)


def categorize_error(error: Exception) -> ErrorCategory:
    """Categorize error"""
    return error_handler.categorize_error(error)


def format_error_response(error: Exception, **kwargs) -> dict:
    """Format error response"""
    return error_handler.format_error_response(error, **kwargs)

