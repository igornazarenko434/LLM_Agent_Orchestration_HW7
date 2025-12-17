"""
Configuration file loading and validation.

This module provides functions to load and validate configuration files:
- load_system_config(): Load global system settings (with env overrides)
- load_league_config(): Load league-specific settings
- load_agents_config(): Load agent registry
"""

import json
import os
from pathlib import Path
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

try:
    from .config_models import AgentConfig, LeagueConfig, SystemConfig
except ImportError:
    from config_models import AgentConfig, LeagueConfig, SystemConfig

__all__ = ["load_system_config", "load_league_config", "load_agents_config", "load_json_file"]

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


def _get_env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, default))
    except ValueError:
        return default


def _get_env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, default))
    except ValueError:
        return default


def apply_env_overrides(system_config: dict) -> dict:
    """
    Apply environment variable overrides to system configuration.

    Environment variables are optional; if unset, JSON values remain.
    """
    cfg = dict(system_config)
    network = cfg.get("network", {})
    timeouts = cfg.get("timeouts", {})
    retry_policy = cfg.get("retry_policy", {})

    # Network/ports
    network["host"] = os.getenv("BASE_HOST", network.get("host"))
    network["league_manager_port"] = _get_env_int("LEAGUE_MANAGER_PORT", network.get("league_manager_port", 8000))
    network["referee_port_start"] = _get_env_int("REFEREE_PORT_START", network.get("referee_port_start", 8001))
    network["referee_port_end"] = _get_env_int("REFEREE_PORT_END", network.get("referee_port_end", 8002))
    network["player_port_start"] = _get_env_int("PLAYER_PORT_START", network.get("player_port_start", 8101))
    network["player_port_end"] = _get_env_int("PLAYER_PORT_END", network.get("player_port_end", 9100))
    cfg["network"] = network

    # Timeouts
    timeouts["registration_sec"] = _get_env_int("TIMEOUT_REGISTRATION", timeouts.get("registration_sec", 10))
    timeouts["game_join_ack_sec"] = _get_env_int("TIMEOUT_GAME_JOIN_ACK", timeouts.get("game_join_ack_sec", 5))
    timeouts["parity_choice_sec"] = _get_env_int("TIMEOUT_PARITY_CHOICE", timeouts.get("parity_choice_sec", 30))
    timeouts["game_over_sec"] = _get_env_int("TIMEOUT_GAME_OVER", timeouts.get("game_over_sec", 5))
    timeouts["match_result_sec"] = _get_env_int("TIMEOUT_MATCH_RESULT", timeouts.get("match_result_sec", 10))
    timeouts["league_query_sec"] = _get_env_int("TIMEOUT_LEAGUE_QUERY", timeouts.get("league_query_sec", 10))
    timeouts["generic_sec"] = _get_env_int("TIMEOUT_GENERIC", timeouts.get("generic_sec", 10))
    cfg["timeouts"] = timeouts

    # Retry policy
    retry_policy["max_retries"] = _get_env_int("RETRY_MAX_RETRIES", retry_policy.get("max_retries", 3))
    retry_policy["initial_delay_sec"] = _get_env_float(
        "RETRY_INITIAL_DELAY_SEC", retry_policy.get("initial_delay_sec", 2.0)
    )
    retry_policy["max_delay_sec"] = _get_env_float(
        "RETRY_MAX_DELAY_SEC", retry_policy.get("max_delay_sec", 10.0)
    )
    cfg["retry_policy"] = retry_policy

    # Logging level
    logging_cfg = cfg.get("logging", {})
    logging_cfg["level"] = os.getenv("LOG_LEVEL", logging_cfg.get("level", "INFO"))
    cfg["logging"] = logging_cfg

    # Network request timeout override (optional)
    network_request_timeout = _get_env_int("REQUEST_TIMEOUT_SEC", network.get("request_timeout_sec", 30))
    network["request_timeout_sec"] = network_request_timeout
    cfg["network"] = network

    # Optional league ID override
    league_id = os.getenv("LEAGUE_ID")
    if league_id:
        cfg["league_id"] = league_id

    return cfg


def load_system_config(file_path: str | Path) -> SystemConfig:
    """Load and validate system configuration with environment overrides."""
    data = load_json_file(file_path)
    data = apply_env_overrides(data)
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
