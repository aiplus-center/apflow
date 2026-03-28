"""
LLM Key Injector

Injects LLM API keys into environment variables for LLM frameworks.
Supports multiple LLM providers by detecting provider from model name or explicit provider type.
"""

import os
from typing import Optional, Dict, Any
from apflow.logger import get_logger

logger = get_logger(__name__)

# Mapping of provider names to their environment variable names
# Based on LiteLLM's environment variable conventions
PROVIDER_ENV_VARS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "azure": "AZURE_API_KEY",
    "azure_openai": "AZURE_OPENAI_API_KEY",
    "cohere": "COHERE_API_KEY",
    "huggingface": "HUGGINGFACE_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
    "together": "TOGETHER_API_KEY",
    "ai21": "AI21_API_KEY",
    "replicate": "REPLICATE_API_KEY",
    "vertex": "VERTEX_PROJECT",
    "bedrock": "AWS_ACCESS_KEY_ID",  # AWS uses multiple env vars
    "sagemaker": "AWS_ACCESS_KEY_ID",
    "ollama": "OLLAMA_API_KEY",
    "deepinfra": "DEEPINFRA_API_KEY",
    "sambanova": "SAMBANOVA_API_KEY",
    "nvidia": "NVIDIA_API_KEY",
    "cloudflare": "CLOUDFLARE_API_KEY",
    "voyage": "VOYAGE_API_KEY",
}

# Model name patterns to provider mapping
MODEL_PROVIDER_PATTERNS = {
    "gpt-": "openai",
    "claude": "anthropic",
    "gemini": "google",
    "palm": "google",
    "command": "cohere",
    "mistral": "mistral",
    "llama": "groq",  # Common with Groq
    "mixtral": "mistral",
    "j2-": "ai21",
    "togethercomputer": "together",
    "replicate": "replicate",
    "ollama": "ollama",
    "deepinfra": "deepinfra",
    "sambanova": "sambanova",
    "nvidia": "nvidia",
    "cloudflare": "cloudflare",
    "voyage": "voyage",
}


def detect_provider_from_model(model_name: str) -> Optional[str]:
    """
    Detect LLM provider from model name

    Args:
        model_name: Model name (e.g., "openai/gpt-4", "gpt-4", "claude-3", "gemini-pro")

    Returns:
        Provider name if detected, None otherwise
    """
    if not model_name:
        return None

    model_lower = model_name.lower()

    # Check if model name contains provider prefix (e.g., "openai/gpt-4")
    if "/" in model_lower:
        provider = model_lower.split("/")[0]
        if provider in PROVIDER_ENV_VARS:
            return provider

    # Check model name patterns
    for pattern, provider in MODEL_PROVIDER_PATTERNS.items():
        if pattern in model_lower:
            return provider

    # Default to OpenAI if no pattern matches (common case)
    return "openai"


def inject_llm_key(
    api_key: str,
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    works: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Inject LLM API key into appropriate environment variable

    Priority for provider detection:
    1. Explicit provider parameter
    2. Model name from works configuration
    3. Model name parameter
    4. Default to OpenAI

    Args:
        api_key: LLM API key
        provider: Explicit provider name (e.g., "openai", "anthropic")
        model_name: Model name for auto-detection
        works: Agent works configuration (may contain model info)
    """
    if not api_key:
        return

    # Try to detect provider
    detected_provider = provider

    if not detected_provider:
        # Try to extract model name from works
        if works:
            # Check agents for LLM model
            agents = works.get("agents", {})
            for agent_config in agents.values():
                agent_llm = agent_config.get("llm")
                if isinstance(agent_llm, str):
                    detected_provider = detect_provider_from_model(agent_llm)
                    break
                elif hasattr(agent_llm, "model"):
                    detected_provider = detect_provider_from_model(agent_llm.model)
                    break

            # Check crew-level LLM if not found in agents
            if not detected_provider:
                crew_llm = works.get("llm")
                if isinstance(crew_llm, str):
                    detected_provider = detect_provider_from_model(crew_llm)

    if not detected_provider and model_name:
        detected_provider = detect_provider_from_model(model_name)

    # Default to OpenAI if still not detected
    if not detected_provider:
        detected_provider = "openai"
        logger.debug("Provider not detected, defaulting to OpenAI")

    # Get environment variable name for provider
    env_var = PROVIDER_ENV_VARS.get(detected_provider)
    if not env_var:
        # Fallback: use provider name in uppercase with _API_KEY suffix
        env_var = f"{detected_provider.upper()}_API_KEY"
        logger.warning(f"Unknown provider '{detected_provider}', using env var '{env_var}'")

    # Set environment variable
    os.environ[env_var] = api_key
    logger.debug(f"Injected LLM key for provider '{detected_provider}' using env var '{env_var}'")

    # Special handling for AWS Bedrock/SageMaker
    if detected_provider in ("bedrock", "sagemaker"):
        # AWS requires additional env vars, but we only set the API key
        # User should set AWS_SECRET_ACCESS_KEY and AWS_REGION separately
        logger.debug("AWS provider detected - ensure AWS_SECRET_ACCESS_KEY and AWS_REGION are set")
