"""
Retry logic with exponential backoff for resilient API calls.

Uses Tenacity library for:
- Automatic retries on transient failures
- Exponential backoff (1s, 2s, 4s, 8s, 16s)
- Max 5 retry attempts
- Tracks retryable vs. non-retryable errors
"""
import logging
from typing import Callable
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    RetryError
)
from utils.exceptions import (
    HuggingFaceAPIError,
    APITimeoutError,
    APIConnectionError
)

logger = logging.getLogger(__name__)


def is_retryable_error(exception: Exception) -> bool:
    """Determine if an exception should trigger a retry"""
    # Only retry on specific transient errors
    if isinstance(exception, APITimeoutError):
        return True
    if isinstance(exception, APIConnectionError):
        return True
    if isinstance(exception, HuggingFaceAPIError):
        return getattr(exception, 'retryable', False)
    return False


def create_retry_decorator():
    """Create retry decorator with exponential backoff"""
    return retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=16),
        retry=retry_if_exception(is_retryable_error),
        reraise=True
    )


def with_retry(func: Callable) -> Callable:
    """Decorator to add retry logic to a function"""
    @create_retry_decorator()
    def wrapper(*args, **kwargs):
        logger.debug(f"Executing {func.__name__} with retry logic")
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def retry_with_backoff(func: Callable, *args, **kwargs):
    """Execute function with automatic retry on transient failures

    Args:
        func: Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Function result

    Raises:
        Original exception if all retries exhausted
    """
    decorated = with_retry(func)
    try:
        return decorated(*args, **kwargs)
    except RetryError as e:
        logger.error(f"Retries exhausted for {func.__name__}: {e.last_attempt.exception}")
        raise e.last_attempt.exception
