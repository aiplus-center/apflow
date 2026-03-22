from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable, List, Optional

from apflow.core.config.registry import ConfigRegistry, get_config
from apflow.core.types import TaskPostHook, TaskPreHook
from apflow.logger import get_logger

if TYPE_CHECKING:
    from apflow.core.storage.sqlalchemy.models import TaskModelTypel

logger = get_logger(__name__)

# Default API configuration values
DEFAULT_API_TIMEOUT = 30.0
DEFAULT_API_RETRY_ATTEMPTS = 3
DEFAULT_API_RETRY_BACKOFF = 1.0  # seconds


@dataclass
class ConfigManager:
    """
    Typed configuration manager wrapping the legacy ConfigRegistry.

    Provides a single entrypoint for loading environment variables, managing
    hooks, and controlling execution flags (demo scaling, task creator policy).

    API Configuration:
    - api_server_url: URL of the API server (e.g., http://localhost:8000)
    - admin_auth_token: Optional admin auth token for CLI API requests
    - use_local_db: Fallback to local DB if API unreachable (default: True)
    - api_timeout: Request timeout in seconds (default: 30.0)
    - api_retry_attempts: Number of retry attempts (default: 3)
    - api_retry_backoff: Initial backoff for exponential retry (default: 1.0)

    Usage examples
    --------------
    Prefer decorators for static hooks:
        from apflow import register_pre_hook

        @register_pre_hook
        async def normalize(task):
            ...

    Use ConfigManager for dynamic or test-time wiring:
        from apflow.core.config_manager import get_config_manager

        cm = get_config_manager()
        cm.register_pre_hook(lambda task: task.inputs.update({"ctx": "dynamic"}))
        cm.set_demo_sleep_scale(0.5)
        cm.load_env_files([Path.cwd()/".env"], override=False)

    Configure API gateway:
        cm = get_config_manager()
        cm.set_api_server_url("http://localhost:8000")
        cm.set_admin_auth_token("token-xyz")
        cm.set_api_timeout(60.0)

    Configure API gateway with validation:
        cm = get_config_manager()
        success = await cm.set_api_server_url_with_check("http://localhost:8000")
        if success:
            cm.set_admin_auth_token("token-xyz")

    """

    _registry: ConfigRegistry = field(default_factory=get_config)
    # API Gateway configuration
    _api_server_url: Optional[str] = field(default=None)
    _admin_auth_token: Optional[str] = field(default=None)
    _use_local_db: bool = field(default=True)
    _api_timeout: float = field(default=DEFAULT_API_TIMEOUT)
    _api_retry_attempts: int = field(default=DEFAULT_API_RETRY_ATTEMPTS)
    _api_retry_backoff: float = field(default=DEFAULT_API_RETRY_BACKOFF)

    def load_env_files(self, paths: Iterable[Path], override: bool = False) -> None:
        """Load the first existing .env file from the provided paths."""
        try:
            from dotenv import load_dotenv
        except ImportError:
            logger.debug("python-dotenv not installed; skipping .env load")
            return

        for env_path in paths:
            try:
                if env_path.exists():
                    load_dotenv(env_path, override=override)
                    logger.info(f"Loaded .env file from {env_path}")
                    # Log if APFLOW_JWT_SECRET is in the file
                    try:
                        env_content = env_path.read_text()
                        if "APFLOW_JWT_SECRET" in env_content:
                            logger.info("Found APFLOW_JWT_SECRET in .env file")
                    except Exception:
                        pass  # Ignore errors reading file content
                    return
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Failed to load .env from %s: %s", env_path, exc)
                continue

        logger.debug("No .env file found in any of the checked paths")

    def load_cli_config(self) -> None:
        """
        Load API configuration from CLI config file or environment variables.

        Loads unified configuration from config.cli.yaml (if exists):
        1. Project-local: <project>/.data/config.cli.yaml
        2. User-global: ~/.aiperceivable/apflow/config.cli.yaml

        Falls back to environment variables (.env) if config file doesn't exist:
        - APFLOW_BASE_URL: Full API server URL (e.g., http://localhost:8000)
        - APFLOW_API_HOST and APFLOW_API_PORT: Construct URL from host:port
        - APFLOW_ADMIN_AUTH_TOKEN: Admin auth token

        This enables users to connect without initializing config.cli.yaml.

        Note: URL accessibility checks are NOT performed here. URLs are loaded
        as-is. Validation happens automatically in CLI when needed (see should_use_api).
        """
        config = {}

        try:
            from apflow.cli.cli_config import load_cli_config as load_config

            config = load_config()
            logger.debug("Loaded API config from CLI config file")
        except ImportError:
            # cli_config module not available (shouldn't happen in CLI context)
            pass
        except Exception as e:
            logger.debug(f"CLI config file not found or failed to load: {e}")

        # Load API server URL (only if explicitly configured)
        if "api_server_url" in config:
            self.set_api_server_url(config["api_server_url"])
        else:
            # Check .env APFLOW_BASE_URL or APFLOW_API_HOST/APFLOW_API_PORT
            # Only set URL if explicitly configured, don't default to localhost:8000
            from apflow.core.utils.helpers import get_url_with_host_and_port

            base_url = os.getenv("APFLOW_BASE_URL")
            if base_url:
                self.set_api_server_url(base_url)
                logger.debug(f"Loaded API server URL from APFLOW_BASE_URL: {base_url}")
            else:
                # Only use APFLOW_API_HOST/APFLOW_API_PORT if explicitly set
                api_host = os.getenv("APFLOW_API_HOST") or os.getenv("API_HOST")
                api_port = os.getenv("APFLOW_API_PORT") or os.getenv("API_PORT")
                if api_host:
                    host = api_host
                    port = int(api_port or "8000")
                    base_url = get_url_with_host_and_port(host, port)
                    self.set_api_server_url(base_url)
                    logger.debug(f"Loaded API server URL from environment: {base_url}")

        # Load admin_auth_token (migrated from api_auth_token)
        if "admin_auth_token" in config:
            self.set_admin_auth_token(config["admin_auth_token"])
        elif "api_auth_token" in config:
            # Backward compatibility: migrate api_auth_token -> admin_auth_token
            self.set_admin_auth_token(config["api_auth_token"])
            logger.debug("Migrated api_auth_token -> admin_auth_token")
        else:
            # Check environment variable if not in config file
            auth_token = os.getenv("APFLOW_ADMIN_AUTH_TOKEN")
            if auth_token:
                self.set_admin_auth_token(auth_token)
                logger.debug("Loaded admin auth token from environment")

    def set_task_model_class(self, task_model_class: Optional["TaskModelTypel"]) -> None:
        self._registry.set_task_model_class(task_model_class)

    def get_task_model_class(self) -> "TaskModelTypel":
        return self._registry.get_task_model_class()

    def register_pre_hook(self, hook: TaskPreHook) -> None:
        self._registry.register_pre_hook(hook)

    def register_post_hook(self, hook: TaskPostHook) -> None:
        self._registry.register_post_hook(hook)

    def get_pre_hooks(self) -> List[TaskPreHook]:
        return self._registry.get_pre_hooks()

    def get_post_hooks(self) -> List[TaskPostHook]:
        return self._registry.get_post_hooks()

    def set_use_task_creator(self, enabled: bool) -> None:
        self._registry.set_use_task_creator(enabled)

    def get_use_task_creator(self) -> bool:
        return self._registry.get_use_task_creator()

    def set_require_existing_tasks(self, required: bool) -> None:
        self._registry.set_require_existing_tasks(required)

    def get_require_existing_tasks(self) -> bool:
        return self._registry.get_require_existing_tasks()

    def register_task_tree_hook(self, hook_type: str, hook: Callable) -> None:
        self._registry.register_task_tree_hook(hook_type, hook)

    def get_task_tree_hooks(self, hook_type: str) -> List[Callable]:
        return self._registry.get_task_tree_hooks(hook_type)

    def set_demo_sleep_scale(self, scale: float) -> None:
        self._registry.set_demo_sleep_scale(scale)

    def get_demo_sleep_scale(self) -> float:
        return self._registry.get_demo_sleep_scale()

    async def check_api_server_accessible(self, url: str, timeout: float = 5.0) -> bool:
        """
        Check if API server is accessible by making a health check request.

        Args:
            url: API server URL to check
            timeout: Request timeout in seconds (default: 5.0)

        Returns:
            True if server is accessible, False otherwise
        """
        try:
            import httpx

            headers = {}
            token = self.get_admin_auth_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"

            async with httpx.AsyncClient(timeout=timeout) as client:
                # Try to reach the health endpoint
                response = await client.post(f"{url.rstrip('/')}", json={}, headers=headers)
                return response.status_code == 200
        except Exception as exc:
            logger.debug(f"API server health check failed for {url}: {exc}")
            return False

    # API Gateway configuration methods
    def set_api_server_url(self, url: Optional[str]) -> None:
        """Set API server URL (e.g., http://localhost:8000)."""
        self._api_server_url = url
        if url:
            logger.debug(f"API server configured: {url}")

    def get_api_server_url(self) -> Optional[str]:
        """Get configured API server URL."""
        return self._api_server_url

    def set_admin_auth_token(self, token: Optional[str]) -> None:
        """Set admin auth token for CLI API requests."""
        self._admin_auth_token = token
        if token:
            logger.debug("Admin auth token configured")

    def get_admin_auth_token(self) -> Optional[str]:
        """Get admin auth token for CLI API requests."""
        return self._admin_auth_token

    # Backward compatibility aliases
    def set_api_auth_token(self, token: Optional[str]) -> None:
        """Set admin auth token (backward compatibility alias)."""
        logger.warning("set_api_auth_token() is deprecated, use set_admin_auth_token() instead")
        self.set_admin_auth_token(token)

    def get_api_auth_token(self) -> Optional[str]:
        """Get admin auth token (backward compatibility alias)."""
        return self.get_admin_auth_token()

    def set_use_local_db(self, enabled: bool) -> None:
        """Set whether to fallback to local DB if API unreachable."""
        self._use_local_db = enabled
        logger.debug(f"Local DB fallback: {enabled}")

    def get_use_local_db(self) -> bool:
        """Get whether to fallback to local DB if API unreachable."""
        return self._use_local_db

    def set_api_timeout(self, timeout: float) -> None:
        """Set API request timeout in seconds."""
        self._api_timeout = timeout
        logger.debug(f"API timeout: {timeout}s")

    def get_api_timeout(self) -> float:
        """Get API request timeout in seconds."""
        return self._api_timeout

    def set_api_retry_attempts(self, attempts: int) -> None:
        """Set number of API retry attempts."""
        self._api_retry_attempts = attempts
        logger.debug(f"API retry attempts: {attempts}")

    def get_api_retry_attempts(self) -> int:
        """Get number of API retry attempts."""
        return self._api_retry_attempts

    def set_api_retry_backoff(self, backoff: float) -> None:
        """Set initial backoff for exponential retry (seconds)."""
        self._api_retry_backoff = backoff
        logger.debug(f"API retry backoff: {backoff}s")

    def get_api_retry_backoff(self) -> float:
        """Get initial backoff for exponential retry."""
        return self._api_retry_backoff

    def is_api_configured(self) -> bool:
        """Check if API server is configured."""
        return self._api_server_url is not None

    # Property accessors for convenience (in addition to getter methods)
    @property
    def api_server_url(self) -> Optional[str]:
        """Get configured API server URL."""
        return self._api_server_url

    @property
    def admin_auth_token(self) -> Optional[str]:
        """Get admin auth token for CLI API requests."""
        return self._admin_auth_token

    @property
    def api_auth_token(self) -> Optional[str]:
        """Get admin auth token (backward compatibility alias)."""
        return self._admin_auth_token

    @property
    def use_local_db(self) -> bool:
        """Get whether to fallback to local DB if API unreachable."""
        return self._use_local_db

    @property
    def api_timeout(self) -> float:
        """Get API request timeout in seconds."""
        return self._api_timeout

    @property
    def api_retry_attempts(self) -> int:
        """Get number of API retry attempts."""
        return self._api_retry_attempts

    @property
    def api_retry_backoff(self) -> float:
        """Get initial backoff for exponential retry."""
        return self._api_retry_backoff

    def clear(self) -> None:
        self._registry.clear()
        # Reset API configuration
        self._api_server_url = None
        self._admin_auth_token = None
        self._use_local_db = True
        self._api_timeout = DEFAULT_API_TIMEOUT
        self._api_retry_attempts = DEFAULT_API_RETRY_ATTEMPTS
        self._api_retry_backoff = DEFAULT_API_RETRY_BACKOFF


_config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    return _config_manager


__all__ = ["ConfigManager", "get_config_manager"]
