"""
Configuration loading utilities for the Proxmox MCP server.

This module handles loading and validation of server configuration:
- JSON configuration file loading
- Environment variable handling
- Configuration validation using Pydantic models
- Error handling for invalid configurations

The module ensures that all required configuration is present
and valid before the server starts operation.
"""
import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .models import Config


def _load_env_auth() -> dict:
    """Load authentication from environment variables.

    Looks for:
    - PROXMOX_TOKEN_ID: Format "user@realm!token_name"
    - PROXMOX_TOKEN_SECRET: The token secret value

    Returns:
        dict with user, token_name, token_value if found, empty dict otherwise
    """
    token_id = os.getenv("PROXMOX_TOKEN_ID")
    token_secret = os.getenv("PROXMOX_TOKEN_SECRET")

    if not token_id or not token_secret:
        return {}

    # Parse token_id format: "user@realm!token_name"
    if "!" not in token_id:
        return {}

    user, token_name = token_id.rsplit("!", 1)
    return {
        "user": user,
        "token_name": token_name,
        "token_value": token_secret,
    }


def load_config(config_path: Optional[str] = None) -> Config:
    """Load and validate configuration from JSON file.

    Performs the following steps:
    1. Verifies config path is provided
    2. Loads JSON configuration file
    3. Validates required fields are present
    4. Converts to typed Config object using Pydantic
    
    Configuration must include:
    - Proxmox connection settings (host, port, etc.)
    - Authentication credentials (user, token)
    - Logging configuration
    
    Args:
        config_path: Path to the JSON configuration file
                    If not provided, raises ValueError

    Returns:
        Config object containing validated configuration:
        {
            "proxmox": {
                "host": "proxmox-host",
                "port": 8006,
                ...
            },
            "auth": {
                "user": "username",
                "token_name": "token-name",
                ...
            },
            "logging": {
                "level": "INFO",
                ...
            }
        }

    Raises:
        ValueError: If:
                 - Config path is not provided
                 - JSON is invalid
                 - Required fields are missing
                 - Field values are invalid
    """
    if not config_path:
        raise ValueError("PROXMOX_MCP_CONFIG environment variable must be set")

    # Load .env file from config directory or project root
    config_dir = Path(config_path).parent
    for env_path in [config_dir / ".env", Path.cwd() / ".env"]:
        if env_path.exists():
            load_dotenv(env_path)
            break

    try:
        with open(config_path) as f:
            config_data = json.load(f)
            if not config_data.get('proxmox', {}).get('host'):
                raise ValueError("Proxmox host cannot be empty")

            # Merge environment auth into config (env vars take precedence)
            env_auth = _load_env_auth()
            if env_auth:
                config_data.setdefault("auth", {})
                config_data["auth"] = {**config_data["auth"], **env_auth}

            return Config(**config_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load config: {e}")
