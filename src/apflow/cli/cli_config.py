"""
Configuration persistence module for APFlow CLI.

Handles saving/loading configuration with single unified YAML file support:

File Structure:
  config.cli.yaml  - Unified CLI configuration (all settings in one file)

Location Priority:
  1. APFLOW_CONFIG_DIR environment variable (highest priority)
  2. Project-local: <project_root>/.data/ (if in project)
  3. User-global: ~/.aiperceivable/apflow/ (default fallback)

Permissions:
  config.cli.yaml  - 600 (owner-only access, more secure)

Environment Variables:
  APFLOW_CONFIG_DIR: Override config directory location (highest priority)

Migration:
  Automatically migrates from config.json + secrets.json to config.cli.yaml
  on first access. Old files are backed up as .json.bak.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from apflow.logger import get_logger

logger = get_logger(__name__)

# Try to import yaml, fallback to None if not available
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None  # type: ignore

# User-global configuration (default)
USER_CONFIG_DIR = Path.home() / ".aiperceivable" / "apflow"

# Configuration file names
CLI_CONFIG_FILE = "config.cli.yaml"  # Unified CLI configuration
# Legacy file names (for migration)
LEGACY_CONFIG_FILE = "config.json"  # Legacy non-sensitive configuration
LEGACY_SECRETS_FILE = "secrets.json"  # Legacy sensitive configuration


def get_project_root() -> Optional[Path]:
    """
    Find project root by looking for pyproject.toml or .git directory.

    DEPRECATED: Use apflow.core.utils.project_detection.get_project_root() instead.
    This function is kept for backward compatibility.

    Walks up the directory tree from current working directory
    until it finds a project marker or reaches filesystem root.

    Returns:
        Project root path if found, None otherwise
    """
    from apflow.core.utils.project_detection import get_project_root as _get_project_root

    return _get_project_root()


def get_project_config_dir() -> Optional[Path]:
    """
    Get project-local config directory if in project context.

    Note: This returns .data for consistency with project_detection module,
    but CLI config still uses ~/.aiperceivable/apflow/ for user-global config.

    Returns:
        <project_root>/.data if in project, None otherwise
    """
    from apflow.core.utils.project_detection import get_project_data_dir

    return get_project_data_dir()


def get_config_dir() -> Path:
    """
    Get the appropriate config directory based on context and environment.

    Priority order:
    1. APFLOW_CONFIG_DIR environment variable
    2. Project-local <project_root>/.data (if in project)
    3. User-global ~/.aiperceivable/apflow (default)

    Returns:
        Path to config directory
    """
    # Check environment variable override
    env_config_dir = os.getenv("APFLOW_CONFIG_DIR")
    if env_config_dir:
        return Path(env_config_dir)

    # Check if we're in a project and use project-local config
    project_config_dir = get_project_config_dir()
    if project_config_dir:
        return project_config_dir

    # Default to user-global config
    return USER_CONFIG_DIR


def get_cli_config_file_path() -> Path:
    """
    Get the path to the unified CLI config file (config.cli.yaml).

    For reading: Returns path to first existing file in priority order
    For writing: Returns path where config should be saved (respects priority)

    Returns:
        Path to config.cli.yaml file
    """
    config_dir = get_config_dir()
    return config_dir / CLI_CONFIG_FILE


def get_all_cli_config_locations() -> list[Path]:
    """
    Get all possible CLI config file locations in priority order.

    Returns:
        List of config.cli.yaml paths in priority order
    """
    project_config_dir = get_project_config_dir()
    locations = []

    # Add project-local if applicable
    if project_config_dir:
        locations.append(project_config_dir / CLI_CONFIG_FILE)

    # Add user-global
    locations.append(USER_CONFIG_DIR / CLI_CONFIG_FILE)

    return locations


def is_localhost_url(url: str) -> bool:
    """
    Check if a URL is localhost.

    Args:
        url: URL string to check

    Returns:
        True if URL is localhost, False otherwise
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        return hostname in ("localhost", "127.0.0.1") or "localhost" in hostname
    except Exception:
        return False


def validate_cli_config(config: dict) -> None:
    """
    Validate CLI configuration.

    Rules:
    - No strict requirements, only warn if potential issues are detected

    Args:
        config: Configuration dictionary to validate

    Raises:
        ValueError: If validation fails (currently doesn't raise)
    """
    api_server_url = config.get("api_server_url")
    if api_server_url:
        # Warn if auth might be needed but not configured
        jwt_secret = config.get("jwt_secret")
        if not jwt_secret and not is_localhost_url(api_server_url):
            # This is OK - user might want authentication disabled
            # No validation error, just allow it
            pass

    # Set default jwt_algorithm if not specified
    if "jwt_algorithm" not in config:
        config["jwt_algorithm"] = "HS256"


def load_yaml_file(file_path: Path) -> dict:
    """
    Load YAML file.

    Args:
        file_path: Path to YAML file

    Returns:
        Dictionary with config, empty dict if file doesn't exist or error
    """
    if not YAML_AVAILABLE:
        logger.warning("PyYAML not installed, cannot load YAML config")
        return {}

    if not file_path.exists():
        return {}

    try:
        with open(file_path, "r") as f:
            config = yaml.safe_load(f) or {}
            logger.debug(f"Loaded YAML config from {file_path}")
            return config
    except Exception as e:
        logger.warning(f"Failed to load YAML config from {file_path}: {e}")
        return {}


def save_yaml_file(file_path: Path, config: dict) -> None:
    """
    Save configuration to YAML file.

    Args:
        file_path: Path to YAML file
        config: Configuration dictionary to save
    """
    if not YAML_AVAILABLE:
        raise RuntimeError("PyYAML not installed, cannot save YAML config")

    try:
        with open(file_path, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
        logger.debug(f"Saved YAML config to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save YAML config to {file_path}: {e}")
        raise


def ensure_config_dir() -> None:
    """Ensure the configuration directory exists."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)


def load_cli_config() -> dict:
    """
    Load CLI configuration from config.cli.yaml.

    Checks multiple locations in priority order:
    1. Project-local: .data/config.cli.yaml
    2. User-global: ~/.aiperceivable/apflow/config.cli.yaml

    Also attempts to migrate from legacy JSON files if YAML doesn't exist.

    Returns:
        Dictionary with config, empty dict if no config found
    """

    # Load YAML config
    for config_path in get_all_cli_config_locations():
        if config_path.exists():
            config = load_yaml_file(config_path)
            if config:
                # Validate config
                try:
                    validate_cli_config(config)
                except ValueError as e:
                    logger.warning(f"Config validation warning: {e}")
                return config

    logger.debug("No config found, using empty config")
    return {}


def save_cli_config_yaml(config: dict) -> None:
    """
    Save CLI configuration to config.cli.yaml.

    Saves to appropriate location based on context:
    - Project-local if in project context
    - User-global otherwise

    Sets file permissions to 600 (owner-only access).

    Args:
        config: Configuration dictionary to save
    """
    if not YAML_AVAILABLE:
        raise RuntimeError("PyYAML not installed, cannot save YAML config")

    # Validate before saving
    validate_cli_config(config)

    ensure_config_dir()
    config_file = get_cli_config_file_path()

    try:
        save_yaml_file(config_file, config)

        # Set restricted permissions (600 - owner only)
        config_file.chmod(0o600)
        logger.debug(f"Saved config to {config_file}")
    except Exception as e:
        logger.error(f"Failed to save config to {config_file}: {e}")
        raise


def get_config_value(key: str) -> Optional[str]:
    """
    Get a configuration value from config.cli.yaml.

    Args:
        key: Configuration key

    Returns:
        Configuration value or None if not found
    """
    config = load_cli_config()
    value = config.get(key)
    if value is not None:
        return str(value) if not isinstance(value, str) else value
    return None


def set_config_value(key: str, value: Optional[str], is_sensitive: bool = False) -> None:
    """
    Set a configuration value in config.cli.yaml.

    Note: is_sensitive parameter is kept for backward compatibility but
    all values are now stored in the same file with 600 permissions.

    Args:
        key: Configuration key
        value: Configuration value (None to delete)
        is_sensitive: Ignored (kept for backward compatibility)
    """
    config = load_cli_config()
    if value is None:
        config.pop(key, None)
    else:
        config[key] = value

    save_cli_config_yaml(config)


def list_config_values() -> dict:
    """
    List all configuration values.

    Sensitive values (tokens, secrets) are masked.

    Returns:
        Dictionary of configuration values with tokens masked
    """
    config = load_cli_config()

    # Sensitive keys that should be masked
    sensitive_keys = {
        "admin_auth_token",
        "api_auth_token",  # Legacy key
        "token",
        "api_key",
        "secret",
        "jwt_secret",
    }

    # Combine and mask
    display_config = {}

    for key, value in config.items():
        # Check if key contains sensitive keywords
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            if isinstance(value, str) and len(value) > 3:
                display_config[key] = f"{value[:3]}...***"
            else:
                display_config[key] = "***"
        else:
            display_config[key] = value

    return display_config


# Legacy functions for backward compatibility
def load_secrets_config() -> dict:
    """
    Legacy function: Load secrets from unified config.

    Returns empty dict. Use load_cli_config() instead.
    """
    logger.warning("load_secrets_config() is deprecated, use load_cli_config() instead")
    return {}


def save_secrets_config(secrets: dict) -> None:
    """
    Legacy function: Save secrets to unified config.

    Use save_cli_config_yaml() instead.
    """
    logger.warning("save_secrets_config() is deprecated, use save_cli_config_yaml() instead")
    config = load_cli_config()
    config.update(secrets)
    save_cli_config_yaml(config)


# Legacy constants for backward compatibility
CONFIG_FILE = LEGACY_CONFIG_FILE
SECRETS_FILE = LEGACY_SECRETS_FILE


def get_config_file_path(filename: str = CLI_CONFIG_FILE) -> Path:
    """
    Get the path to a config file.

    For backward compatibility, supports both legacy filenames and new CLI config file.

    Args:
        filename: Config file name

    Returns:
        Path to config file
    """
    if filename == CLI_CONFIG_FILE:
        return get_cli_config_file_path()
    else:
        # Default to CLI config file
        return get_cli_config_file_path()


def get_all_config_locations() -> list[Path]:
    """
    Legacy function: Get all possible config file locations.

    Returns CLI config locations for backward compatibility.
    """
    return get_all_cli_config_locations()


def get_all_secrets_locations() -> list[Path]:
    """
    Legacy function: Get all possible secrets file locations.

    Returns CLI config locations for backward compatibility.
    """
    return get_all_cli_config_locations()


def save_cli_config(config: dict) -> None:
    """
    Legacy function: Save CLI configuration.

    Use save_cli_config_yaml() instead.
    """
    save_cli_config_yaml(config)
