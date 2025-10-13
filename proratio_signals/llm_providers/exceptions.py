"""
Custom exceptions for LLM providers.

Provides specific exception types for common API errors,
allowing orchestrator to handle errors programmatically instead of
string parsing.
"""


class ProviderError(Exception):
    """
    Base exception for all LLM provider errors.

    All custom provider exceptions inherit from this class,
    allowing catch-all handling when needed.
    """

    pass


class APIKeyError(ProviderError):
    """
    Raised when API key is invalid, missing, or unauthorized.

    This typically indicates:
    - API key not set in environment
    - API key format is invalid
    - API key has been revoked
    - Insufficient permissions for the requested operation

    Action required: Check API key in .env file
    """

    pass


class QuotaError(ProviderError):
    """
    Raised when API quota or credits are exceeded.

    This typically indicates:
    - Monthly quota exhausted
    - Insufficient credits/balance
    - Usage limit reached

    Action required: Check account quota/billing or wait for reset
    """

    pass


class RateLimitError(ProviderError):
    """
    Raised when rate limit is exceeded (temporary).

    This is a transient error that should be retried after a delay.
    Distinct from QuotaError which indicates exhausted quota.

    Action required: Retry after delay (automatic)
    """

    def __init__(self, message: str, retry_after: int = 60):
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying (default 60)
        """
        super().__init__(message)
        self.retry_after = retry_after


class ModelNotFoundError(ProviderError):
    """
    Raised when the requested model doesn't exist or is unavailable.

    This typically indicates:
    - Model name is incorrect
    - Model has been deprecated
    - Model not available in current region
    - Insufficient permissions for model access

    Action required: Check model name in configuration
    """

    pass


class InvalidResponseError(ProviderError):
    """
    Raised when API returns invalid or unexpected response format.

    This typically indicates:
    - Response is not valid JSON
    - Response missing required fields
    - Response format changed (API update)
    - Empty or malformed response

    Action required: Check API version or report issue
    """

    pass


class TimeoutError(ProviderError):
    """
    Raised when API request times out.

    This typically indicates:
    - Network issues
    - API server overloaded
    - Request taking too long to process
    - Connection problems

    Action required: Retry or check network connectivity
    """

    pass


class InvalidPromptError(ProviderError):
    """
    Raised when prompt violates provider's content policy.

    This typically indicates:
    - Prompt contains blocked keywords
    - Prompt too long (exceeds token limit)
    - Prompt violates safety guidelines
    - Content moderation triggered

    Action required: Modify prompt or check content policy
    """

    pass


# Convenience mapping for error classification
# Used to convert string-based errors into specific exception types
ERROR_KEYWORDS = {
    APIKeyError: [
        "api key",
        "api_key",
        "unauthorized",
        "authentication",
        "invalid_api_key",
        "invalid_key",
        "not authorized",
        "auth failed",
        "invalid credentials",
    ],
    QuotaError: [
        "quota",
        "insufficient_quota",
        "credits",
        "balance",
        "billing",
        "exceeded quota",
        "usage limit",
        "out of credits",
    ],
    RateLimitError: [
        "rate limit",
        "rate_limit",
        "too many requests",
        "throttled",
        "retry after",
        "requests per",
    ],
    ModelNotFoundError: [
        "model not found",
        "model_not_found",
        "invalid model",
        "model does not exist",
        "model unavailable",
        "unknown model",
    ],
    TimeoutError: [
        "timeout",
        "timed out",
        "connection timeout",
        "read timeout",
        "request timeout",
        "deadline exceeded",
    ],
    InvalidPromptError: [
        "content policy",
        "safety",
        "blocked",
        "inappropriate",
        "violates",
        "not allowed",
        "token limit",
        "too long",
    ],
}


def classify_error(error_message: str) -> type[ProviderError]:
    """
    Classify a generic error message into a specific exception type.

    Useful for wrapping third-party library exceptions that don't have
    specific exception classes.

    Args:
        error_message: Error message to classify

    Returns:
        Most specific exception class that matches the error message.
        Returns ProviderError as fallback if no match found.

    Example:
        >>> exc_class = classify_error("Invalid API key provided")
        >>> raise exc_class("API key error")
        APIKeyError: API key error
    """
    error_lower = error_message.lower()

    # Check each exception type's keywords
    for exception_class, keywords in ERROR_KEYWORDS.items():
        if any(keyword in error_lower for keyword in keywords):
            return exception_class

    # No match found - return generic ProviderError
    return ProviderError
