# Action 5: LLM Provider Error Handling Implementation Guide

**Priority**: HIGH
**Estimated Time**: 1 day
**Status**: Pending (Phase 3.5 - Technical Debt Resolution)
**Based on**: [technical_debt_gemini_review.md](technical_debt_gemini_review.md) Section 3.2

---

## Problem Statement

Currently, LLM providers have **inconsistent error handling**:

### Issues:
1. **Generic exceptions**: All errors raised as generic `Exception`
2. **String parsing**: Orchestrator parses exception messages to determine error type
3. **Code duplication**: Same try/except patterns repeated across providers
4. **Verbose orchestrator**: 50+ lines of error handling code
5. **Hard to extend**: Adding new providers requires duplicating error logic

### Current Code Example:

```python
# In SignalOrchestrator.generate_signal()
try:
    signal = provider.generate_signal(pair)
except Exception as e:
    error_msg = str(e).lower()
    if "api key" in error_msg or "unauthorized" in error_msg:
        failure_reasons[provider_name] = "API key error"
    elif "quota" in error_msg or "rate limit" in error_msg:
        failure_reasons[provider_name] = "Quota/rate limit exceeded"
    else:
        failure_reasons[provider_name] = f"Unknown error: {str(e)}"
```

**Problems**:
- Fragile string matching
- Can't distinguish between error types programmatically
- Hard to add new error types
- Error messages inconsistent

---

## Solution: Custom Exception Hierarchy

Create specific exception classes that providers can raise, allowing the orchestrator to catch and handle them explicitly.

### Benefits:
- ✅ Type-safe error handling
- ✅ Consistent error messages
- ✅ Easier to add new error types
- ✅ Simplified orchestrator code
- ✅ Better logging and debugging

---

## Implementation Plan

### Step 1: Create Exception Hierarchy (1 hour)

**File**: `proratio_signals/llm_providers/exceptions.py` (NEW)

```python
"""
Custom exceptions for LLM providers.

Provides specific exception types for common API errors,
allowing orchestrator to handle errors programmatically.
"""


class ProviderError(Exception):
    """Base exception for all LLM provider errors."""
    pass


class APIKeyError(ProviderError):
    """
    Raised when API key is invalid, missing, or unauthorized.

    This typically indicates:
    - API key not set in environment
    - API key format is invalid
    - API key has been revoked
    - Insufficient permissions for the requested operation
    """
    pass


class QuotaError(ProviderError):
    """
    Raised when API quota or credits are exceeded.

    This typically indicates:
    - Monthly quota exhausted
    - Rate limit exceeded (should retry)
    - Insufficient credits/balance
    """
    pass


class RateLimitError(ProviderError):
    """
    Raised when rate limit is exceeded (temporary).

    This is a transient error that should be retried after a delay.
    Distinct from QuotaError which indicates exhausted quota.
    """
    def __init__(self, message: str, retry_after: int = 60):
        """
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
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
    """
    pass


class InvalidResponseError(ProviderError):
    """
    Raised when API returns invalid or unexpected response format.

    This typically indicates:
    - Response is not valid JSON
    - Response missing required fields
    - Response format changed (API update)
    """
    pass


class TimeoutError(ProviderError):
    """
    Raised when API request times out.

    This typically indicates:
    - Network issues
    - API server overloaded
    - Request taking too long to process
    """
    pass


class InvalidPromptError(ProviderError):
    """
    Raised when prompt violates provider's content policy.

    This typically indicates:
    - Prompt contains blocked keywords
    - Prompt too long
    - Prompt violates safety guidelines
    """
    pass


# Convenience mapping for common error detection
ERROR_KEYWORDS = {
    APIKeyError: [
        "api key", "api_key", "unauthorized", "authentication",
        "invalid_api_key", "invalid_key", "not authorized"
    ],
    QuotaError: [
        "quota", "insufficient_quota", "credits", "balance",
        "billing", "exceeded quota", "usage limit"
    ],
    RateLimitError: [
        "rate limit", "rate_limit", "too many requests",
        "throttled", "retry after"
    ],
    ModelNotFoundError: [
        "model not found", "model_not_found", "invalid model",
        "model does not exist", "model unavailable"
    ],
    TimeoutError: [
        "timeout", "timed out", "connection timeout",
        "read timeout", "request timeout"
    ],
    InvalidPromptError: [
        "content policy", "safety", "blocked", "inappropriate",
        "violates", "not allowed"
    ]
}


def classify_error(error_message: str) -> type[ProviderError]:
    """
    Classify a generic error message into a specific exception type.

    Useful for wrapping third-party library exceptions.

    Args:
        error_message: Error message to classify

    Returns:
        Most specific exception class that matches
    """
    error_lower = error_message.lower()

    for exception_class, keywords in ERROR_KEYWORDS.items():
        if any(keyword in error_lower for keyword in keywords):
            return exception_class

    return ProviderError  # Default fallback
```

---

### Step 2: Update Base Provider (1 hour)

**File**: `proratio_signals/llm_providers/base.py`

Add helper method for error wrapping:

```python
from .exceptions import (
    ProviderError, APIKeyError, QuotaError, RateLimitError,
    ModelNotFoundError, InvalidResponseError, TimeoutError,
    classify_error
)

class BaseLLMProvider:
    """Base class for LLM providers."""

    def _wrap_api_error(self, original_error: Exception, context: str = "") -> ProviderError:
        """
        Wrap a third-party API error into our custom exception hierarchy.

        Args:
            original_error: Original exception from API client
            context: Additional context about what operation failed

        Returns:
            Appropriate ProviderError subclass

        Raises:
            ProviderError: Always raises (never returns)
        """
        error_msg = str(original_error)
        full_msg = f"{context}: {error_msg}" if context else error_msg

        # Classify and raise appropriate exception
        exception_class = classify_error(error_msg)
        raise exception_class(full_msg) from original_error

    # ... rest of base class
```

---

### Step 3: Refactor ChatGPT Provider (1 hour)

**File**: `proratio_signals/llm_providers/chatgpt.py`

**Before**:
```python
def _call_api(self, prompt: str) -> str:
    try:
        response = self.client.chat.completions.create(...)
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"ChatGPT API error: {str(e)}")
```

**After**:
```python
from .exceptions import (
    APIKeyError, QuotaError, RateLimitError, TimeoutError,
    ModelNotFoundError, InvalidResponseError
)

def _call_api(self, prompt: str) -> str:
    try:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content

    except openai.AuthenticationError as e:
        raise APIKeyError(f"OpenAI authentication failed: {str(e)}") from e

    except openai.RateLimitError as e:
        # Extract retry-after if available
        retry_after = getattr(e, 'retry_after', 60)
        raise RateLimitError(
            f"OpenAI rate limit exceeded: {str(e)}",
            retry_after=retry_after
        ) from e

    except openai.APIStatusError as e:
        if e.status_code == 429:
            raise QuotaError(f"OpenAI quota exceeded: {str(e)}") from e
        elif e.status_code == 404:
            raise ModelNotFoundError(f"OpenAI model not found: {str(e)}") from e
        else:
            raise self._wrap_api_error(e, "OpenAI API error")

    except openai.APITimeoutError as e:
        raise TimeoutError(f"OpenAI request timeout: {str(e)}") from e

    except openai.APIError as e:
        # Generic OpenAI error - try to classify
        raise self._wrap_api_error(e, "OpenAI error")

    except Exception as e:
        # Unexpected error
        raise self._wrap_api_error(e, "Unexpected ChatGPT error")
```

---

### Step 4: Refactor Claude Provider (1 hour)

**File**: `proratio_signals/llm_providers/claude.py`

```python
from .exceptions import (
    APIKeyError, QuotaError, RateLimitError, TimeoutError,
    InvalidResponseError
)
import anthropic

def _call_api(self, prompt: str) -> str:
    try:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    except anthropic.AuthenticationError as e:
        raise APIKeyError(f"Anthropic authentication failed: {str(e)}") from e

    except anthropic.RateLimitError as e:
        raise RateLimitError(
            f"Anthropic rate limit exceeded: {str(e)}",
            retry_after=60
        ) from e

    except anthropic.APIStatusError as e:
        if e.status_code == 429:
            raise QuotaError(f"Anthropic quota exceeded: {str(e)}") from e
        elif e.status_code == 404:
            raise ModelNotFoundError(f"Claude model not found: {str(e)}") from e
        else:
            raise self._wrap_api_error(e, "Anthropic API error")

    except anthropic.APITimeoutError as e:
        raise TimeoutError(f"Anthropic request timeout: {str(e)}") from e

    except anthropic.APIError as e:
        raise self._wrap_api_error(e, "Anthropic error")

    except Exception as e:
        raise self._wrap_api_error(e, "Unexpected Claude error")
```

---

### Step 5: Refactor Gemini Provider (1 hour)

**File**: `proratio_signals/llm_providers/gemini.py`

```python
from .exceptions import (
    APIKeyError, QuotaError, RateLimitError, TimeoutError,
    InvalidResponseError
)
import google.generativeai as genai

def _call_api(self, prompt: str) -> str:
    try:
        response = self.model.generate_content(prompt)
        return response.text

    except Exception as e:
        error_msg = str(e).lower()

        # Google doesn't have specific exception types, so we classify
        if "api key" in error_msg or "unauthorized" in error_msg:
            raise APIKeyError(f"Google authentication failed: {str(e)}") from e

        elif "quota" in error_msg or "limit" in error_msg:
            if "rate" in error_msg:
                raise RateLimitError(f"Google rate limit: {str(e)}", retry_after=60) from e
            else:
                raise QuotaError(f"Google quota exceeded: {str(e)}") from e

        elif "timeout" in error_msg:
            raise TimeoutError(f"Google request timeout: {str(e)}") from e

        elif "model" in error_msg and "not found" in error_msg:
            raise ModelNotFoundError(f"Gemini model not found: {str(e)}") from e

        else:
            raise self._wrap_api_error(e, "Google Gemini error")
```

---

### Step 6: Simplify Orchestrator (2 hours)

**File**: `proratio_signals/orchestrator.py`

**Before** (50+ lines):
```python
for provider_name, provider in self.providers.items():
    try:
        signal = provider.generate_signal(pair, ohlcv_data)
        signals.append(signal)
    except Exception as e:
        error_msg = str(e).lower()
        if "api key" in error_msg or "unauthorized" in error_msg:
            failure_reasons[provider_name] = "API key error"
        elif "quota" in error_msg or "rate limit" in error_msg:
            failure_reasons[provider_name] = "Quota/rate limit exceeded"
        # ... many more elif blocks ...
        else:
            failure_reasons[provider_name] = f"Unknown error: {str(e)}"
```

**After** (20 lines):
```python
from .llm_providers.exceptions import (
    ProviderError, APIKeyError, QuotaError, RateLimitError,
    TimeoutError, ModelNotFoundError
)

for provider_name, provider in self.providers.items():
    try:
        signal = provider.generate_signal(pair, ohlcv_data)
        signals.append(signal)

    except APIKeyError as e:
        failed_providers.append(provider_name)
        failure_reasons[provider_name] = f"API Key Error: {str(e)}"
        logger.error(f"{provider_name} authentication failed: {e}")

    except QuotaError as e:
        failed_providers.append(provider_name)
        failure_reasons[provider_name] = f"Quota Exceeded: {str(e)}"
        logger.warning(f"{provider_name} quota exhausted: {e}")

    except RateLimitError as e:
        failed_providers.append(provider_name)
        failure_reasons[provider_name] = f"Rate Limited (retry after {e.retry_after}s)"
        logger.warning(f"{provider_name} rate limited: {e}")

    except TimeoutError as e:
        failed_providers.append(provider_name)
        failure_reasons[provider_name] = f"Timeout: {str(e)}"
        logger.warning(f"{provider_name} timeout: {e}")

    except ModelNotFoundError as e:
        failed_providers.append(provider_name)
        failure_reasons[provider_name] = f"Model Error: {str(e)}"
        logger.error(f"{provider_name} model not found: {e}")

    except ProviderError as e:
        # Generic provider error (catch-all)
        failed_providers.append(provider_name)
        failure_reasons[provider_name] = f"Provider Error: {str(e)}"
        logger.error(f"{provider_name} error: {e}")

    except Exception as e:
        # Unexpected error (should rarely happen now)
        failed_providers.append(provider_name)
        failure_reasons[provider_name] = f"Unexpected Error: {str(e)}"
        logger.exception(f"{provider_name} unexpected error: {e}")
```

---

### Step 7: Update Tests (1 hour)

**File**: `tests/test_signals/test_providers.py`

Add tests for new exceptions:

```python
from proratio_signals.llm_providers.exceptions import (
    APIKeyError, QuotaError, RateLimitError
)

def test_chatgpt_invalid_api_key():
    """Test that invalid API key raises APIKeyError"""
    with pytest.raises(APIKeyError):
        provider = ChatGPTProvider(api_key="invalid-key")
        provider.generate_signal("BTC/USDT", mock_data)

def test_claude_quota_exceeded():
    """Test that quota exceeded raises QuotaError"""
    # Mock the API to return 429 status
    with mock.patch('anthropic.Client') as mock_client:
        mock_client.side_effect = anthropic.APIStatusError(status_code=429)

        with pytest.raises(QuotaError):
            provider = ClaudeProvider(api_key="test-key")
            provider.generate_signal("BTC/USDT", mock_data)

def test_orchestrator_handles_rate_limit():
    """Test that orchestrator handles rate limit gracefully"""
    with mock.patch.object(ChatGPTProvider, 'generate_signal') as mock_gen:
        mock_gen.side_effect = RateLimitError("Rate limited", retry_after=30)

        orchestrator = SignalOrchestrator()
        result = orchestrator.generate_signal("BTC/USDT")

        # Should still return result with partial signals
        assert result is not None
        assert 'chatgpt' in result.failed_providers
```

---

## Testing Checklist

- [ ] All providers raise specific exceptions
- [ ] Orchestrator catches specific exceptions
- [ ] Error messages are clear and actionable
- [ ] Retry logic works for `RateLimitError`
- [ ] Logging includes appropriate detail
- [ ] Tests cover all exception types
- [ ] All existing tests still pass (186+)

---

## Validation

```bash
# Check old string-based error handling removed
grep -r "api key.*in.*error_msg" proratio_signals/
# Should return no results

# Run tests
pytest tests/test_signals/ -v

# Test error handling manually
python scripts/test_llm_errors.py
```

---

## Benefits After Implementation

### Code Quality:
- **-60% lines** in orchestrator error handling (50 → 20 lines)
- **+Type safety**: Can catch specific exceptions
- **+Maintainability**: Easy to add new error types

### User Experience:
- **Clear error messages**: "API Key Error" vs "Unknown error"
- **Actionable**: User knows exactly what to fix
- **Retry logic**: Automatic for rate limits

### Debugging:
- **Better logging**: Structured error information
- **Stack traces**: Preserved via `raise ... from e`
- **Monitoring**: Can alert on specific error types

---

## Completion Criteria

- ✅ `exceptions.py` created with full hierarchy
- ✅ All 3 providers refactored (ChatGPT, Claude, Gemini)
- ✅ Orchestrator simplified (50 → 20 lines)
- ✅ Tests updated and passing
- ✅ Error messages improved
- ✅ Documentation updated

---

**Estimated Total Time**: 1 day (8 hours)
**Priority**: HIGH (improves AI signal reliability)
**Status**: Ready to implement
