"""
Advanced Error Handling for K2Think API Proxy
Implements circuit breaker, retry logic, and automatic fallback
"""

import time
import logging
import asyncio
from typing import Callable, Any, Optional, Dict, List
from enum import Enum
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    Prevents cascading failures by temporarily blocking calls to failing services
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        name: str = "default"
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes to close circuit
            timeout: Seconds before attempting recovery (half-open)
            name: Circuit breaker identifier
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.name = name
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker '{self.name}': Attempting recovery (half-open)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Retry after {self._time_until_retry():.0f} seconds"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Async version of call"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker '{self.name}': Attempting recovery (half-open)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Retry after {self._time_until_retry():.0f} seconds"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info(f"Circuit breaker '{self.name}': Closing (recovered)")
                self.state = CircuitState.CLOSED
                self.success_count = 0
                self.last_state_change = datetime.now()
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit breaker '{self.name}': Opening (recovery failed)")
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()
        elif self.failure_count >= self.failure_threshold:
            logger.error(
                f"Circuit breaker '{self.name}': Opening "
                f"(threshold reached: {self.failure_count} failures)"
            )
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset"""
        if self.last_failure_time is None:
            return False
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout
    
    def _time_until_retry(self) -> float:
        """Calculate seconds until retry allowed"""
        if self.last_failure_time is None:
            return 0
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return max(0, self.timeout - elapsed)
    
    def reset(self):
        """Manually reset circuit breaker"""
        logger.info(f"Circuit breaker '{self.name}': Manual reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = datetime.now()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_state_change': self.last_state_change.isoformat(),
            'time_until_retry': self._time_until_retry() if self.state == CircuitState.OPEN else 0
        }


class RetryStrategy:
    """
    Retry logic with exponential backoff
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        backoff_multiplier: float = 2.0,
        max_backoff: int = 60,
        retry_on_exceptions: Optional[List[type]] = None,
        retry_on_status_codes: Optional[List[int]] = None
    ):
        """
        Initialize retry strategy
        
        Args:
            max_attempts: Maximum number of attempts
            backoff_multiplier: Exponential backoff multiplier
            max_backoff: Maximum backoff time in seconds
            retry_on_exceptions: List of exception types to retry on
            retry_on_status_codes: List of HTTP status codes to retry on
        """
        self.max_attempts = max_attempts
        self.backoff_multiplier = backoff_multiplier
        self.max_backoff = max_backoff
        self.retry_on_exceptions = retry_on_exceptions or [Exception]
        self.retry_on_status_codes = retry_on_status_codes or [429, 500, 502, 503, 504]
    
    def calculate_backoff(self, attempt: int) -> float:
        """Calculate backoff time for given attempt"""
        backoff = min(
            self.backoff_multiplier ** attempt,
            self.max_backoff
        )
        return backoff
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Check if should retry based on exception and attempt number"""
        if attempt >= self.max_attempts:
            return False
        
        # Check if exception type is retryable
        for exc_type in self.retry_on_exceptions:
            if isinstance(exception, exc_type):
                return True
        
        # Check HTTP status code if available
        if hasattr(exception, 'status_code'):
            if exception.status_code in self.retry_on_status_codes:
                return True
        
        return False
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Retry succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt + 1):
                    logger.error(f"Not retrying after attempt {attempt + 1}: {e}")
                    raise
                
                backoff = self.calculate_backoff(attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_attempts} failed: {e}. "
                    f"Retrying in {backoff:.2f}s..."
                )
                time.sleep(backoff)
        
        # All retries exhausted
        logger.error(f"All {self.max_attempts} retry attempts exhausted")
        raise last_exception
    
    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """Async version of execute"""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                result = await func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Retry succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt + 1):
                    logger.error(f"Not retrying after attempt {attempt + 1}: {e}")
                    raise
                
                backoff = self.calculate_backoff(attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_attempts} failed: {e}. "
                    f"Retrying in {backoff:.2f}s..."
                )
                await asyncio.sleep(backoff)
        
        # All retries exhausted
        logger.error(f"All {self.max_attempts} retry attempts exhausted")
        raise last_exception


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


def with_circuit_breaker(circuit_breaker: CircuitBreaker):
    """Decorator to apply circuit breaker to function"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return circuit_breaker.call(func, *args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await circuit_breaker.call_async(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


def with_retry(retry_strategy: RetryStrategy):
    """Decorator to apply retry logic to function"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_strategy.execute(func, *args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await retry_strategy.execute_async(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


# Global circuit breakers and retry strategies
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_retry_strategies: Dict[str, RetryStrategy] = {}


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get or create circuit breaker by name"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name=name, **kwargs)
    return _circuit_breakers[name]


def get_retry_strategy(name: str, **kwargs) -> RetryStrategy:
    """Get or create retry strategy by name"""
    if name not in _retry_strategies:
        _retry_strategies[name] = RetryStrategy(**kwargs)
    return _retry_strategies[name]


def reset_all_circuit_breakers():
    """Reset all circuit breakers"""
    for cb in _circuit_breakers.values():
        cb.reset()


def get_all_circuit_breaker_states() -> List[Dict[str, Any]]:
    """Get states of all circuit breakers"""
    return [cb.get_state() for cb in _circuit_breakers.values()]


if __name__ == '__main__':
    # Test circuit breaker and retry logic
    logging.basicConfig(level=logging.INFO)
    
    # Test circuit breaker
    cb = CircuitBreaker(failure_threshold=3, timeout=5, name="test")
    
    def failing_function():
        raise Exception("Test failure")
    
    # Trigger circuit breaker
    for i in range(5):
        try:
            cb.call(failing_function)
        except Exception as e:
            print(f"Attempt {i + 1}: {e}")
        
        print(f"State: {cb.get_state()}")
        time.sleep(1)

