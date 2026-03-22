"""
CLI configuration management command.

Provides commands to manage CLI configuration including:
- Basic config operations: set, get, unset, list, reset
- Token management: gen-token, verify-token
- Quick setup: init, init-server
- Utilities: path, edit, validate
"""

import typer
import json
from typing import Optional

from apflow.cli.cli_config import (
    get_config_value,
    set_config_value,
    list_config_values,
    get_config_file_path,
    load_cli_config,
)
from apflow.cli.jwt_token import generate_token, get_token_info, verify_token
from apflow.logger import get_logger

logger = get_logger(__name__)

app = typer.Typer(
    name="config",
    help="Manage CLI configuration",
    no_args_is_help=True,
)


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="Configuration value"),
):
    """
    Set a configuration value.

    Supports common aliases for convenience:
        api-server, api-url -> api_server_url
        api-token, token -> admin_auth_token
        log-level -> log_level

    Examples:
        apflow config set api_server_url http://localhost:8000
        apflow config set api-server http://localhost:8000
        apflow config set admin_auth_token my-token-xyz
        apflow config set api-token my-token-xyz
        apflow config set log-level DEBUG
    """
    try:
        # Resolve aliases for convenience
        alias_map = {
            "api-server": "api_server_url",
            "api-url": "api_server_url",
            "api-token": "admin_auth_token",
            "token": "admin_auth_token",
            "log-level": "log_level",
        }
        actual_key = alias_map.get(key, key)

        # Determine if this is a sensitive value
        is_sensitive = "token" in actual_key.lower() or "secret" in actual_key.lower()
        set_config_value(actual_key, value, is_sensitive=is_sensitive)
        typer.echo(f"✅ Configuration '{actual_key}' set successfully")

        # Display masked value for tokens
        if "token" in actual_key.lower():
            masked = f"{value[:8]}...***" if len(value) > 8 else "***"
            typer.echo(f"   Value: {masked}")
        else:
            typer.echo(f"   Value: {value}")

        # Show path
        from apflow.cli.cli_config import get_cli_config_file_path

        typer.echo(f"   Location: {get_cli_config_file_path()}")

    except Exception as e:
        typer.echo(f"❌ Error setting configuration: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command("get")
def get_config(
    key: str = typer.Argument(..., help="Configuration key"),
):
    """
    Get a configuration value.

    Supports common aliases for convenience:
        api-server, api-url -> api_server_url
        api-token, token -> admin_auth_token
        log-level -> log_level

    Examples:
        apflow config get api_server_url
        apflow config get api-server
        apflow config get admin_auth_token
        apflow config get api-token
        apflow config get log-level
    """
    try:
        # Resolve aliases for convenience
        alias_map = {
            "api-server": "api_server_url",
            "api-url": "api_server_url",
            "api-token": "admin_auth_token",
            "token": "admin_auth_token",
            "log-level": "log_level",
        }
        actual_key = alias_map.get(key, key)

        value = get_config_value(actual_key)

        if value is None:
            typer.echo(f"⚠️  Configuration '{actual_key}' not found")
            raise typer.Exit(1)

        # Mask tokens in output (only show first char + ...)
        if "token" in actual_key.lower():
            if len(value) > 1:
                masked = f"{value[0]}...***"
            else:
                masked = "***"
            typer.echo(f"{actual_key}={masked}")
        else:
            typer.echo(f"{actual_key}={value}")

    except Exception as e:
        if "Configuration" not in str(e):
            typer.echo(f"❌ Error getting configuration: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command("list")
def list_config(
    format: str = typer.Option("table", "--format", "-f", help="Output format: table or json"),
):
    """
    List all configuration values.

    Sensitive values (tokens) are masked for security.

    Examples:
        apflow config list
        apflow config list -f json
    """
    try:
        config = list_config_values()

        if not config:
            typer.echo("No configuration found.")
            typer.echo(f"Configuration file: {get_config_file_path()}")
            return

        if format == "json":
            typer.echo(json.dumps(config, indent=2))
        else:
            # Table format
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(title="CLI Configuration")
            table.add_column("Key", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            for key, value in sorted(config.items()):
                table.add_row(key, str(value))

            console.print(table)
            console.print(f"\n📁 Location: {get_config_file_path()}")

    except Exception as e:
        typer.echo(f"❌ Error listing configuration: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command("unset")
def unset_config(
    key: str = typer.Argument(..., help="Configuration key to delete"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """
    Delete a configuration value.

    Supports common aliases for convenience:
        api-server, api-url -> api_server_url
        api-token, token -> admin_auth_token
        log-level -> log_level

    Examples:
        apflow config unset api_server_url
        apflow config unset api-server
        apflow config unset admin_auth_token --yes
        apflow config unset api-token --yes
        apflow config unset log-level --yes
    """
    try:
        # Resolve aliases for convenience
        alias_map = {
            "api-server": "api_server_url",
            "api-url": "api_server_url",
            "api-token": "admin_auth_token",
            "token": "admin_auth_token",
            "log-level": "log_level",
        }
        actual_key = alias_map.get(key, key)

        current = get_config_value(actual_key)

        if current is None:
            typer.echo(f"⚠️  Configuration '{actual_key}' not found")
            raise typer.Exit(1)

        if not confirm:
            if not typer.confirm(f"Delete '{actual_key}'?"):
                typer.echo("Cancelled")
                raise typer.Exit(0)

        set_config_value(actual_key, None)
        typer.echo(f"✅ Configuration '{actual_key}' deleted successfully")

    except Exception as e:
        if "Cancelled" not in str(e):
            typer.echo(f"❌ Error deleting configuration: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command("gen-token")
def gen_token(
    subject: str = typer.Option(
        "apflow-user",
        "--subject",
        "-s",
        help="Token subject (typically username or app name)",
    ),
    algo: str = typer.Option(
        "HS256",
        "--algo",
        "-a",
        help="JWT algorithm (HS256, HS512, etc.)",
    ),
    expiry_days: int = typer.Option(
        365,
        "--expiry",
        "-e",
        help="Token expiration in days",
    ),
    role: Optional[str] = typer.Option(
        None,
        "--role",
        "-r",
        help="Role claim (e.g., admin, user)",
    ),
    save: Optional[str] = typer.Option(
        None,
        "--save",
        help="Save token to config key (e.g., admin_auth_token)",
    ),
):
    """
    Generate a JWT token for API authentication.

    By default, generates a user token. Use --role admin for admin token.
    Can optionally save to config using --save.

    Examples:
        apflow config gen-token
        apflow config gen-token --role admin
        apflow config gen-token --subject my-app --expiry 30
        apflow config gen-token --role admin --save admin_auth_token
    """
    try:
        # Build extra claims
        extra_claims = {}
        if role:
            extra_claims["roles"] = [role]

        # Generate token
        token = generate_token(
            subject=subject,
            algo=algo,
            expiry_days=expiry_days,
            extra_claims=extra_claims,
        )

        # Display token
        typer.echo("✅ JWT token generated successfully!\n")
        typer.echo(f"Token: {token}\n")

        # Display token info
        info = get_token_info(token)
        typer.echo("Token details:")
        typer.echo(f"  Subject: {info.get('subject')}")
        typer.echo(f"  Issuer: {info.get('issuer')}")
        typer.echo(f"  Issued: {info.get('issued_at')}")
        typer.echo(f"  Expires: {info.get('expires_at')}")
        if info.get("expires_in_days") is not None:
            typer.echo(f"  Expires in: {info.get('expires_in_days')} days")
        if role:
            typer.echo(f"  Role: {role}")

        # Optionally save to config (with alias resolution)
        if save:
            # Resolve aliases for convenience
            alias_map = {
                "api-server": "api_server_url",
                "api-url": "api_server_url",
                "api-token": "admin_auth_token",
                "token": "admin_auth_token",
            }
            actual_key = alias_map.get(save, save)

            # Determine if this is a sensitive value
            is_sensitive = "token" in actual_key.lower() or "secret" in actual_key.lower()
            set_config_value(actual_key, token, is_sensitive=is_sensitive)
            typer.echo(f"\n✅ Token saved to config key: {actual_key}")
            from apflow.cli.cli_config import get_cli_config_file_path

            typer.echo(f"   Location: {get_cli_config_file_path()}")

    except Exception as e:
        typer.echo(f"❌ Error generating token: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command("init-server")
def init_server(
    url: str = typer.Option(
        "http://localhost:8000",
        "--url",
        "-u",
        help="API server URL",
    ),
    role: str = typer.Option(
        "admin",
        "--role",
        "-r",
        help="Role for the token",
    ),
):
    """
    Initialize API server configuration with auto-generated JWT token.

    This command generates a local admin_auth_token using CLI's own jwt_secret.
    The token is signed with CLI's jwt_algorithm (default: HS256).

    JWT Secret Synchronization:
    - If .env file contains APFLOW_JWT_SECRET, it will be used for jwt_secret
    - This ensures CLI and API server use the same secret for authentication
    - If .env doesn't have APFLOW_JWT_SECRET, a new secret will be generated
    - When APFLOW_JWT_SECRET is not set, the API server disables authentication

    For the token to work with an API server, that server's APFLOW_JWT_SECRET
    must match CLI's jwt_secret. For localhost, this usually works automatically.

    Equivalent to running:
        apflow config set api-server <url>
        apflow config gen-token --role <role> --save admin_auth_token

    Config saved to:
        config.cli.yaml (unified CLI configuration)

    Examples:
        apflow config init-server
        apflow config init-server --url http://prod-server.com:8000
        apflow config init-server --url http://localhost:8000 --role user
    """
    try:
        from pathlib import Path

        from apflow.cli.cli_config import (
            get_cli_config_file_path,
            load_cli_config,
            save_cli_config_yaml,
        )

        # Normalize URL (remove trailing slash)
        url = url.rstrip("/")

        # Load existing config
        config = load_cli_config()

        # Set server URL
        config["api_server_url"] = url

        # Check for APFLOW_JWT_SECRET directly from .env file
        # Don't use os.getenv() as it may have cached values from previous runs
        env_path = Path.cwd() / ".env"
        env_jwt_secret = None

        if env_path.exists():
            try:
                env_content = env_path.read_text()
                for line in env_content.splitlines():
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith("#"):
                        if line.startswith("APFLOW_JWT_SECRET="):
                            env_jwt_secret = line.split("=", 1)[1].strip()
                            break
            except Exception as e:
                typer.echo(f"⚠️  Warning: Could not read .env file: {e}", err=True)

        # Use env value if present, otherwise clear auth-related config
        if env_jwt_secret:
            config["jwt_secret"] = env_jwt_secret
            config["jwt_algorithm"] = "HS256"
            typer.echo("✅ Using JWT secret from .env file (APFLOW_JWT_SECRET)")
        else:
            # .env doesn't have APFLOW_JWT_SECRET, clear auth config
            # This means API server has authentication disabled
            config.pop("jwt_secret", None)
            config.pop("admin_auth_token", None)
            # Keep jwt_algorithm as it's a harmless default setting
            config["jwt_algorithm"] = "HS256"
            typer.echo("ℹ️  No APFLOW_JWT_SECRET in .env - authentication disabled")

        # Save config
        save_cli_config_yaml(config)

        # Generate token only if we have jwt_secret
        if env_jwt_secret:
            from apflow.cli.jwt_token import generate_token

            token = generate_token(
                subject="apflow-cli",
                secret=config.get("jwt_secret"),
                algo=config.get("jwt_algorithm", "HS256"),
                extra_claims={"roles": [role]},
                expiry_days=365,
            )
            config["admin_auth_token"] = token

            # Save unified config again with the new token
            save_cli_config_yaml(config)

        typer.echo("✅ API server configuration initialized!")
        typer.echo(f"   Server: {url}")
        if env_jwt_secret:
            typer.echo(f"   Token: {config['admin_auth_token'][:20]}...***")
            typer.echo(f"   Role: {role}")
        typer.echo(f"\n📁 Saved to: {get_cli_config_file_path()}")
        typer.echo()
        if env_jwt_secret:
            typer.echo("💡 Note: This token is generated using CLI's local jwt_secret.")
            typer.echo("   JWT secret synced from .env file (APFLOW_JWT_SECRET).")
            typer.echo("   API server will use the same secret from .env for authentication.")
            typer.echo()
            typer.echo("You can now run:")
            typer.echo("   apflow tasks list     # Use CLI with API")
        else:
            typer.echo("💡 Note: API server authentication is disabled.")
            typer.echo("   To enable authentication, set APFLOW_JWT_SECRET in .env file.")
            typer.echo()
            typer.echo("You can now run:")
            typer.echo("   apflow tasks list     # Use CLI with API (no auth required)")
        typer.echo()
        if env_jwt_secret:
            typer.echo("Or manually configure using:")
            typer.echo(f"   apflow config set api-server {url}")
            typer.echo("   apflow config gen-token --role admin --save admin_auth_token")

    except Exception as e:
        typer.echo(f"❌ Error initializing server: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command("show-path")
def show_path():
    """
    Show configuration file paths.

    Displays all possible config locations and which one is active.

    [Alias: path]
    """
    from apflow.cli.cli_config import (
        get_all_cli_config_locations,
        get_config_dir,
        get_cli_config_file_path,
    )

    active_config = get_cli_config_file_path()
    active_config_dir = get_config_dir()

    typer.echo("📁 Configuration Structure\n")

    typer.echo("CLI config (config.cli.yaml):")
    for i, location in enumerate(get_all_cli_config_locations(), 1):
        exists = "✅" if location.exists() else "⚪"
        active = "🔵 ACTIVE" if location == active_config else ""
        typer.echo(f"  {i}. {exists} {location} {active}")

    typer.echo("\nActive config directory:")
    typer.echo(f"  {active_config_dir}")

    if active_config.exists():
        import datetime

        mtime = datetime.datetime.fromtimestamp(active_config.stat().st_mtime)
        typer.echo("\nActive config details:")
        typer.echo(f"  Size: {active_config.stat().st_size} bytes")
        typer.echo(f"  Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        typer.echo("\n⚠️  No config file exists yet (will be created on first set)")

    typer.echo("\n💡 Priority (highest to lowest):")
    typer.echo("  1. APFLOW_CONFIG_DIR environment variable")
    typer.echo("  2. Project-local: <project>/.data/")
    typer.echo("  3. User-global: ~/.aiperceivable/apflow/ (default)")

    typer.echo("\n🔒 File Permissions:")
    typer.echo("  config.cli.yaml: 600 (owner-only access)")


@app.command("path")
def path_alias():
    """Show configuration file path (alias for show-path)."""
    show_path()


@app.command("reset")
def reset_config(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """
    Reset all configuration (delete config file).

    ⚠️  This will delete all configuration including API server and tokens.

    Examples:
        apflow config reset
        apflow config reset --yes
    """
    try:
        from apflow.cli.cli_config import get_cli_config_file_path

        path = get_cli_config_file_path()

        if not path.exists():
            typer.echo("⚠️  No configuration file found")
            return

        if not confirm:
            typer.echo(f"This will delete: {path}")
            if not typer.confirm("Are you sure you want to reset all configuration?"):
                typer.echo("Cancelled")
                raise typer.Exit(0)

        path.unlink()
        typer.echo("✅ Configuration reset successfully")
        typer.echo(f"   Deleted: {path}")

    except Exception as e:
        if "Cancelled" not in str(e):
            typer.echo(f"❌ Error resetting configuration: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command("verify-token")
def verify_token_cmd(
    token: Optional[str] = typer.Argument(
        None, help="Token to verify (if not provided, uses admin_auth_token from config)"
    ),
):
    """
    Verify and display JWT token information.

    Can verify a specific token or the configured admin_auth_token.

    Examples:
        apflow config verify-token                    # Verify configured token
        apflow config verify-token eyJhbGci...       # Verify specific token
    """
    try:
        # If no token provided, get from config (try admin_auth_token first, then legacy api_auth_token)
        if not token:
            token = get_config_value("admin_auth_token")
            if not token:
                token = get_config_value("api_auth_token")  # Backward compatibility
            if not token:
                typer.echo("❌ No token provided and no admin_auth_token in config")
                typer.echo("   Use: apflow config verify-token <token>")
                raise typer.Exit(1)
            typer.echo("Verifying configured admin_auth_token...\n")

        # Get token info (without verification)
        info = get_token_info(token)

        typer.echo("✅ Token Information:")
        typer.echo(f"   Subject: {info.get('subject')}")
        typer.echo(f"   Issuer: {info.get('issuer')}")
        typer.echo(f"   Issued: {info.get('issued_at')}")
        typer.echo(f"   Expires: {info.get('expires_at')}")

        if info.get("expires_in_days") is not None:
            days = info.get("expires_in_days")
            if days < 0:
                typer.echo(f"   Status: ⚠️  EXPIRED ({abs(days)} days ago)")
            elif days < 7:
                typer.echo(f"   Status: ⚠️  Expiring soon ({days} days remaining)")
            else:
                typer.echo(f"   Status: ✅ Valid ({days} days remaining)")

        # Show role if present
        roles = info.get("roles")
        if roles:
            if not isinstance(roles, list):
                roles = [roles]
            typer.echo(f"   Roles: {', '.join(roles)}")

        # Try to verify with local secret (if available)
        try:
            verify_token(token)
            typer.echo("\n✅ Token signature verified with local secret")
        except Exception as verify_error:
            typer.echo(f"\n⚠️  Could not verify signature: {str(verify_error)}")

    except Exception as e:
        typer.echo(f"❌ Error verifying token: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command("validate")
def validate_config():
    """
    Validate configuration file integrity and settings.

    Checks:
    - JSON syntax
    - Required fields
    - API server connectivity (if configured)
    - Token validity

    Example:
        apflow config validate
    """
    try:
        from apflow.cli.cli_config import (
            get_cli_config_file_path,
            is_localhost_url,
            validate_cli_config,
        )

        path = get_cli_config_file_path()

        if not path.exists():
            typer.echo("⚠️  No configuration file found")
            typer.echo(f"   Expected: {path}")
            typer.echo("\n💡 Run: apflow config init-server")
            return

        typer.echo("🔍 Validating configuration...\n")

        # Check YAML syntax
        try:
            config = load_cli_config()
            typer.echo("✅ YAML syntax valid")
        except Exception as e:
            typer.echo(f"❌ YAML syntax error: {str(e)}")
            raise typer.Exit(1)

        # Check if config is empty
        if not config:
            typer.echo("⚠️  Configuration is empty")
            typer.echo("\n💡 Run: apflow config init-server")
            return

        typer.echo(f"✅ Found {len(config)} configuration key(s)")

        # Validate configuration rules
        try:
            validate_cli_config(config)
            typer.echo("✅ Configuration validation passed")
        except ValueError as e:
            typer.echo(f"❌ Configuration validation failed: {str(e)}")
            raise typer.Exit(1)

        # Check API server URL
        api_url = config.get("api_server_url")
        if api_url:
            typer.echo(f"✅ API server configured: {api_url}")
            is_localhost = is_localhost_url(api_url)
            if is_localhost:
                typer.echo("   ℹ️  Localhost detected - jwt_secret is optional")
            else:
                typer.echo("   ℹ️  Remote server - jwt_secret is required")
        else:
            typer.echo("⚠️  No API server URL configured")

        # Check jwt_secret
        jwt_secret = config.get("jwt_secret")
        if jwt_secret:
            typer.echo("✅ jwt_secret configured")

            # Check if .env file has APFLOW_JWT_SECRET and if it matches
            import os
            from pathlib import Path
            from apflow.core.config_manager import get_config_manager

            env_path = Path.cwd() / ".env"
            config_manager = get_config_manager()
            config_manager.load_env_files([env_path], override=False)

            env_jwt_secret = os.getenv("APFLOW_JWT_SECRET")
            if env_jwt_secret:
                if env_jwt_secret == jwt_secret:
                    typer.echo("   ✅ JWT secret matches .env file (APFLOW_JWT_SECRET)")
                else:
                    typer.echo("   ⚠️  JWT secret does NOT match .env file!")
                    typer.echo("   💡 CLI and API server may use different secrets")
                    typer.echo("   💡 Run: apflow config init-server to sync")
            else:
                typer.echo("   ℹ️  APFLOW_JWT_SECRET not found in .env file")
                typer.echo("   💡 API server will not require authentication")
                typer.echo("   💡 Set APFLOW_JWT_SECRET in .env to enable authentication")
        else:
            if api_url and not is_localhost_url(api_url):
                typer.echo("❌ jwt_secret is REQUIRED for non-localhost URLs")
            else:
                typer.echo("ℹ️  jwt_secret not configured (optional for localhost)")

                # Check if .env has APFLOW_JWT_SECRET
                import os
                from pathlib import Path
                from apflow.core.config_manager import get_config_manager

                env_path = Path.cwd() / ".env"
                config_manager = get_config_manager()
                config_manager.load_env_files([env_path], override=False)

                env_jwt_secret = os.getenv("APFLOW_JWT_SECRET")
                if env_jwt_secret:
                    typer.echo("   ⚠️  Found APFLOW_JWT_SECRET in .env but not in CLI config")
                    typer.echo("   💡 Run: apflow config init-server to sync")

        # Check jwt_algorithm
        jwt_algorithm = config.get("jwt_algorithm", "HS256")
        typer.echo(f"✅ jwt_algorithm: {jwt_algorithm}")

        # Check and validate token
        token = config.get("admin_auth_token") or config.get("api_auth_token")
        if token:
            typer.echo("✅ Admin auth token configured")

            # Check token expiry
            try:
                info = get_token_info(token)
                days = info.get("expires_in_days")
                if days is not None:
                    if days < 0:
                        typer.echo(f"   ⚠️  Token EXPIRED ({abs(days)} days ago)")
                    elif days < 7:
                        typer.echo(f"   ⚠️  Token expiring soon ({days} days)")
                    else:
                        typer.echo(f"   ✅ Token valid ({days} days remaining)")

                # Try to verify token with current jwt_secret
                if jwt_secret:
                    try:
                        verify_token(token, secret=jwt_secret, algo=jwt_algorithm)
                        typer.echo("   ✅ Token can be verified with current jwt_secret")
                    except Exception as e:
                        typer.echo(
                            f"   ❌ Token verification FAILED with current jwt_secret: {str(e)}"
                        )
                        typer.echo("   💡 This means API server may be using a different secret")
                        typer.echo("   💡 Solution: Restart API server or check .env file")
            except Exception as e:
                typer.echo(f"   ⚠️  Could not parse token: {str(e)}")
        else:
            typer.echo("ℹ️  No admin auth token configured (optional)")

        # Summary
        typer.echo("\n" + "=" * 50)
        if api_url:
            if not is_localhost_url(api_url) and not jwt_secret:
                typer.echo("❌ Configuration incomplete (jwt_secret required)")
            else:
                typer.echo("✅ Configuration looks good!")
        else:
            typer.echo("⚠️  Configuration incomplete")
            typer.echo("\n💡 Run: apflow config init-server")

    except Exception as e:
        if "Configuration" not in str(e):
            typer.echo(f"❌ Error validating configuration: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command("init")
def init_interactive():
    """
    Interactive configuration wizard.

    Guides you through setting up API server and authentication.

    Example:
        apflow config init
    """
    try:
        typer.echo("🚀 APFlow Configuration Wizard\n")

        # Check if already configured
        existing_config = load_cli_config()
        if existing_config:
            typer.echo("⚠️  Configuration already exists:")
            for key, value in existing_config.items():
                if "token" in key.lower():
                    masked = f"{value[:8]}...***" if len(value) > 8 else "***"
                    typer.echo(f"   {key}: {masked}")
                else:
                    typer.echo(f"   {key}: {value}")
            typer.echo()

            if not typer.confirm("Overwrite existing configuration?"):
                typer.echo("Cancelled")
                raise typer.Exit(0)

        # Ask for API server URL
        typer.echo("Step 1: API Server Configuration")
        default_url = "http://localhost:8000"
        api_url = typer.prompt("Enter API server URL", default=default_url)
        api_url = api_url.rstrip("/")

        # Ask for role
        typer.echo("\nStep 2: Token Configuration")
        role = typer.prompt("Enter token role (admin/user)", default="admin")

        # Ask for expiry
        expiry = typer.prompt("Enter token expiry in days", default=365, type=int)

        # Generate configuration
        typer.echo("\n🔧 Generating configuration...")

        from apflow.cli.cli_config import (
            get_cli_config_file_path,
            save_cli_config_yaml,
        )

        config = load_cli_config()
        config["api_server_url"] = api_url

        token = generate_token(
            subject="apflow-cli",
            extra_claims={"roles": [role]},
            expiry_days=expiry,
        )
        config["admin_auth_token"] = token

        save_cli_config_yaml(config)

        typer.echo("\n✅ Configuration saved successfully!")
        typer.echo(f"   Server: {api_url}")
        typer.echo(f"   Token: {token[:20]}...***")
        typer.echo(f"   Role: {role}")
        typer.echo(f"   Expiry: {expiry} days")
        typer.echo(f"   Location: {get_cli_config_file_path()}")

        typer.echo("\n💡 Next steps:")
        typer.echo("   apflow config validate    # Validate configuration")
        typer.echo("   apflow tasks list         # Test CLI with API")

    except Exception as e:
        if "Cancelled" not in str(e):
            typer.echo(f"❌ Error: {str(e)}", err=True)
        raise typer.Exit(1)
