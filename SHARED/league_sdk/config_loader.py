"""
Configuration file loading and validation.

This module provides functions to load and validate configuration files:
- load_system_config(): Load global system settings
- load_league_config(): Load league-specific settings
- load_agents_config(): Load agent registry
"""

import json
from pathlib import Path
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

try:
    from .config_models import AgentConfig, LeagueConfig, SystemConfig
except ImportError:
    from config_models import AgentConfig, LeagueConfig, SystemConfig

__all__ = ["load_system_config", "load_league_config", "load_agents_config"]

T = TypeVar("T", bound=BaseModel)


def load_json_file(file_path: str | Path) -> dict:
    """
    Load and parse JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data as dictionary

    Raises:
        FileNotFoundError: If file does not exist
        JSONDecodeError: If file is not valid JSON
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with open(path, "r") as f:
        return json.load(f)


def validate_config(data: dict, model: Type[T]) -> T:
    """
    Validate configuration data against Pydantic model.

    Args:
        data: Configuration dictionary
        model: Pydantic model class

    Returns:
        Validated model instance

    Raises:
        ValidationError: If data does not match schema
    """
    return model(**data)


def load_system_config(file_path: str | Path) -> SystemConfig:
    """Load and validate system configuration."""
    data = load_json_file(file_path)
    return validate_config(data, SystemConfig)


def load_league_config(file_path: str | Path) -> LeagueConfig:
    """Load and validate league configuration."""
    data = load_json_file(file_path)
    return validate_config(data, LeagueConfig)


def load_agents_config(file_path: str | Path) -> dict:
    """Load and validate agents configuration."""
    data = load_json_file(file_path)
    # Return as dict for now, will be enhanced in M3
    return data
