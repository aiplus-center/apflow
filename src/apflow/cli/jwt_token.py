"""
JWT token generator for CLI authentication.

Provides secure token generation with JWT algorithm support.
Supports multiple config locations with priority:
1. APFLOW_CONFIG_DIR environment variable (highest priority)
2. Project-local: .data/config.cli.yaml (if in project)
3. User-global: ~/.aiperceivable/apflow/config.cli.yaml (fallback)
"""

from __future__ import annotations

import jwt
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from pathlib import Path

from apflow.logger import get_logger

logger = get_logger(__name__)

# Default JWT configuration
DEFAULT_JWT_ALGO = "HS256"
DEFAULT_JWT_EXPIRY_DAYS = 365
DEFAULT_JWT_ISSUER = "apflow-cli"
JWT_SECRET_KEY = "jwt_secret"


def get_jwt_secret_path() -> Path:
    """
    Get JWT secret file path (config.cli.yaml).

    Uses config directory priority:
    1. Project-local: .data/config.cli.yaml
    2. User-global: ~/.aiperceivable/apflow/config.cli.yaml

    Returns:
        Path to config.cli.yaml (project-local or user-global)
    """
    from apflow.cli.cli_config import get_cli_config_file_path

    return get_cli_config_file_path()


def ensure_local_jwt_secret() -> str:
    """
    Get or create local JWT secret.

    Stores secret in appropriate location:
    - Project-local: .data/config.cli.yaml (if in project)
    - User-global: ~/.aiperceivable/apflow/config.cli.yaml (fallback)

    Returns:
        JWT secret string
    """
    from apflow.cli.cli_config import (
        ensure_config_dir,
        load_cli_config,
        save_cli_config_yaml,
    )

    ensure_config_dir()
    secret_file = get_jwt_secret_path()

    # Load existing secret if file exists
    if secret_file.exists():
        try:
            config = load_cli_config()
            if JWT_SECRET_KEY in config:
                return config[JWT_SECRET_KEY]
        except Exception as e:
            logger.warning(f"Failed to load JWT secret from {secret_file}: {e}")

    # Generate new secret
    secret = _generate_jwt_secret()

    # Save for future use
    try:
        config = load_cli_config()
        config[JWT_SECRET_KEY] = secret
        save_cli_config_yaml(config)
        logger.debug(f"Saved JWT secret to {secret_file}")
    except Exception as e:
        logger.warning(f"Failed to save JWT secret to {secret_file}: {e}")

    return secret


def _generate_jwt_secret() -> str:
    """
    Generate a random JWT secret.

    Returns:
        Random secret string (32 bytes, hex encoded)
    """
    return secrets.token_hex(32)


def generate_token(
    subject: str = "apflow-user",
    secret: Optional[str] = None,
    algo: Optional[str] = None,
    expiry_days: int = DEFAULT_JWT_EXPIRY_DAYS,
    extra_claims: Optional[dict] = None,
) -> str:
    """
    Generate a JWT token.

    Args:
        subject: Token subject (typically username or app name)
        secret: JWT secret key. If None, uses local default
        algo: JWT algorithm (HS256, HS512, etc.). If None, reads from config or uses default
        expiry_days: Token expiration in days
        extra_claims: Additional JWT claims

    Returns:
        JWT token string
    """
    if secret is None:
        secret = ensure_local_jwt_secret()

    # Get algorithm from config if not provided
    if algo is None:
        try:
            from apflow.cli.cli_config import load_cli_config

            config = load_cli_config()
            algo = config.get("jwt_algorithm", DEFAULT_JWT_ALGO)
        except Exception:
            algo = DEFAULT_JWT_ALGO

    now = datetime.now(timezone.utc)
    expiry = now + timedelta(days=expiry_days)

    payload = {
        "sub": subject,
        "iss": DEFAULT_JWT_ISSUER,
        "iat": now,
        "exp": expiry,
        "jti": uuid.uuid4().hex,
    }

    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, secret, algorithm=algo)

    logger.debug(f"Generated JWT token with algo={algo}, expiry={expiry_days} days")

    return token


def verify_token(
    token: str,
    secret: Optional[str] = None,
    algo: Optional[str] = None,
) -> dict:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string
        secret: JWT secret key. If None, uses local default
        algo: JWT algorithm. If None, reads from config or uses default

    Returns:
        Decoded token payload

    Raises:
        jwt.InvalidTokenError: If token is invalid or expired
    """
    if secret is None:
        secret = ensure_local_jwt_secret()

    # Get algorithm from config if not provided
    if algo is None:
        try:
            from apflow.cli.cli_config import load_cli_config

            config = load_cli_config()
            algo = config.get("jwt_algorithm", DEFAULT_JWT_ALGO)
        except Exception:
            algo = DEFAULT_JWT_ALGO

    try:
        payload = jwt.decode(token, secret, algorithms=[algo])
        logger.debug("Successfully verified JWT token")
        return payload
    except jwt.ExpiredSignatureError:
        logger.error("JWT token has expired")
        raise
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid JWT token: {e}")
        raise


def get_token_info(token: str) -> dict:
    """
    Get information about a token without verifying signature.

    Useful for displaying token details.

    Args:
        token: JWT token string

    Returns:
        Dictionary with token info (subject, issuer, expiry, etc.)
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})

        info = {
            "subject": payload.get("sub"),
            "issuer": payload.get("iss"),
            "issued_at": payload.get("iat"),
            "expires_at": payload.get("exp"),
            "token_id": payload.get("jti"),
            "roles": payload.get("roles") or payload.get("role"),
        }

        # Format timestamps
        if info["issued_at"]:
            info["issued_at"] = datetime.fromtimestamp(
                info["issued_at"], tz=timezone.utc
            ).isoformat()

        if info["expires_at"]:
            expires = datetime.fromtimestamp(info["expires_at"], tz=timezone.utc)
            info["expires_at"] = expires.isoformat()
            info["expires_in_days"] = (expires - datetime.now(timezone.utc)).days

        return info
    except Exception as e:
        logger.error(f"Failed to decode token: {e}")
        return {}
