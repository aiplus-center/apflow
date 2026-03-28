"""
LLM Key Context Manager

Provides thread-local context for LLM API keys during task execution.
Supports multiple sources with configurable priority order:
- API context: header -> LLMKeyConfigManager -> env
- CLI context: params -> LLMKeyConfigManager -> env

Note: Environment variables (OPENAI_API_KEY) are automatically read by LLM frameworks,
but we also support them here for executors that need explicit key passing.
"""

import os
import threading
from typing import Optional, Literal, Callable
from apflow.logger import get_logger

logger = get_logger(__name__)

# Thread-local storage for LLM key context
_context = threading.local()


def set_llm_key_from_header(api_key: Optional[str], provider: Optional[str] = None) -> None:
    """
    Set LLM API key and provider from request header

    Args:
        api_key: LLM API key from request header
        provider: Optional provider name from request header
    """
    _context.llm_key_header = api_key
    if provider:
        _context.llm_provider_header = provider
    if api_key:
        logger.debug(f"Set LLM key from request header (provider: {provider or 'auto'})")


def get_llm_key_from_header() -> Optional[str]:
    """
    Get LLM API key from request header

    Returns:
        LLM API key if set, None otherwise
    """
    return getattr(_context, "llm_key_header", None)


def get_llm_provider_from_header() -> Optional[str]:
    """
    Get LLM provider from request header

    Returns:
        LLM provider name if set, None otherwise
    """
    return getattr(_context, "llm_provider_header", None)


def set_llm_key_from_cli_params(api_key: Optional[str], provider: Optional[str] = None) -> None:
    """
    Set LLM API key and provider from CLI params

    Args:
        api_key: LLM API key from CLI params
        provider: Optional provider name from CLI params
    """
    _context.llm_key_cli = api_key
    if provider:
        _context.llm_provider_cli = provider
    if api_key:
        logger.debug(f"Set LLM key from CLI params (provider: {provider or 'auto'})")


def get_llm_key_from_cli_params() -> Optional[str]:
    """
    Get LLM API key from CLI params

    Returns:
        LLM API key if set, None otherwise
    """
    return getattr(_context, "llm_key_cli", None)


def get_llm_provider_from_cli_params() -> Optional[str]:
    """
    Get LLM provider from CLI params

    Returns:
        LLM provider name if set, None otherwise
    """
    return getattr(_context, "llm_provider_cli", None)


def _get_key_from_user_config(user_id: str, provider: Optional[str] = None) -> Optional[str]:
    """
    Get LLM API key from user config (LLMKeyConfigManager)

    Args:
        user_id: User ID for config lookup
        provider: Optional provider name

    Returns:
        API key from user config, or None if not found
    """
    try:
        from apflow.extensions.llm_key_config import LLMKeyConfigManager

        config_manager = LLMKeyConfigManager()
        user_key = config_manager.get_key(user_id, provider=provider)
        if not user_key and provider:
            user_key = config_manager.get_key(user_id, provider=None)
        if user_key:
            logger.debug(
                f"Using LLM key from user config for user {user_id}, provider {provider or 'default'}"
            )
            return user_key
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Failed to get LLM key from user config: {e}")
    return None


def _get_key_from_source(
    get_key_func: Callable[[], Optional[str]],
    get_provider_func: Callable[[], Optional[str]],
    source_name: str,
    provider: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """
    Get LLM key and provider from a source (header or CLI params)

    Args:
        get_key_func: Function to get key from source
        get_provider_func: Function to get provider from source
        source_name: Name of the source (for logging)
        provider: Optional provider name (may be updated from source)

    Returns:
        Tuple of (api_key, updated_provider)
    """
    api_key = get_key_func()
    if api_key:
        source_provider = get_provider_func()
        updated_provider = provider or source_provider
        logger.debug(f"Using LLM key from {source_name} (provider: {updated_provider or 'auto'})")
        return api_key, updated_provider
    return None, provider


def get_llm_key(
    user_id: Optional[str] = None,
    provider: Optional[str] = None,
    context: Literal["api", "cli", "auto"] = "auto",
) -> Optional[str]:
    """
    Get LLM API key with configurable priority order based on context

    Priority order:
    - API context: header -> LLMKeyConfigManager -> env
    - CLI context: params -> LLMKeyConfigManager -> env
    - auto: detect context automatically (header first, then CLI params)

    Args:
        user_id: Optional user ID for user config lookup
        provider: Optional provider name for provider-specific key lookup.
                   If None, will use provider from header/CLI params if available.
        context: Execution context ("api", "cli", or "auto" for auto-detection)

    Returns:
        LLM API key, or None if not found
    """
    # Auto-detect context if not specified
    if context == "auto":
        # Check header first (API context)
        if get_llm_key_from_header():
            context = "api"
        # Check CLI params (CLI context)
        elif get_llm_key_from_cli_params():
            context = "cli"
        else:
            # Default to API context (most common)
            context = "api"

    # Priority 1: Get key from source (header or CLI params)
    if context == "api":
        api_key, provider = _get_key_from_source(
            get_llm_key_from_header, get_llm_provider_from_header, "request header", provider
        )
    else:  # context == "cli"
        api_key, provider = _get_key_from_source(
            get_llm_key_from_cli_params, get_llm_provider_from_cli_params, "CLI params", provider
        )

    if api_key:
        return api_key

    # Priority 2: User config (LLMKeyConfigManager)
    if user_id:
        user_key = _get_key_from_user_config(user_id, provider)
        if user_key:
            return user_key

    # Priority 3: Environment variables
    env_key = _get_key_from_env(provider)
    if env_key:
        logger.debug(f"Using LLM key from environment variable (provider: {provider or 'auto'})")
        return env_key

    # Return None - some executors will automatically use env vars
    return None


def _get_key_from_env(provider: Optional[str] = None) -> Optional[str]:
    """
    Get LLM API key from environment variables

    Args:
        provider: Optional provider name

    Returns:
        API key from environment variable, or None if not found
    """
    if provider:
        # Provider-specific env vars
        provider_upper = provider.upper()
        env_vars = [
            f"{provider_upper}_API_KEY",
            f"{provider_upper}_KEY",
        ]
        for env_var in env_vars:
            api_key = os.getenv(env_var)
            if api_key:
                return api_key

    # Common env vars (try in order)
    common_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "LLM_API_KEY",
    ]
    for env_var in common_vars:
        api_key = os.getenv(env_var)
        if api_key:
            return api_key

    return None


def clear_llm_key_context() -> None:
    """
    Clear LLM key context (mainly for testing)

    Clears both API (header) and CLI (params) contexts.
    This should be called at the start of each request/execution
    to prevent using stale keys from previous requests.
    """
    if hasattr(_context, "llm_key_header"):
        delattr(_context, "llm_key_header")
    if hasattr(_context, "llm_provider_header"):
        delattr(_context, "llm_provider_header")
    if hasattr(_context, "llm_key_cli"):
        delattr(_context, "llm_key_cli")
    if hasattr(_context, "llm_provider_cli"):
        delattr(_context, "llm_provider_cli")
