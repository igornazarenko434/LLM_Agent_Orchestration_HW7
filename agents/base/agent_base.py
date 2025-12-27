"""
Base agent implementation shared by League Manager, Referee, and Player agents.

Responsibilities:
- Initialize FastAPI application with health endpoint
- Load system configuration with env overrides
- Configure structured logging (JsonLogger + legacy logger for retry)
- Start/stop Uvicorn server with graceful shutdown
- Perform registration against the League Manager via JSON-RPC with retry
"""

from __future__ import annotations

import signal
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI

from league_sdk.config_loader import load_system_config
from league_sdk.config_models import SystemConfig
from league_sdk.logger import JsonLogger, setup_logger
from league_sdk.protocol import LeagueRegisterRequest, RefereeRegisterRequest
from league_sdk.retry import CircuitBreaker, call_with_retry

DEFAULT_SYSTEM_CONFIG_PATH = Path("SHARED/config/system.json")


class BaseAgent:
    """Reusable base class for all agents."""

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        league_id: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        system_config_path: Path | str = DEFAULT_SYSTEM_CONFIG_PATH,
        log_level: Optional[str] = None,
    ) -> None:
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.sender = f"{agent_type}:{agent_id}"
        self.league_id = league_id
        self.config: SystemConfig = load_system_config(system_config_path)
        self.host = host or self.config.network.host
        self.port = port or self._default_port_for_type(agent_type)
        self.log_level = (log_level or self.config.logging.get("level", "INFO")).upper()

        # Logging: JsonLogger for structured events, legacy logger for retry integration
        self.logger = JsonLogger(
            component=self.sender,
            agent_id=self.agent_id,
            league_id=self.league_id,
            min_level=self.log_level,
        )
        self.std_logger = setup_logger(
            component=self.sender,
            log_file=self.logger.log_file,
            level=self._log_level_int(self.log_level),
            max_bytes=self.config.logging.get("max_file_size_mb", 100) * 1024 * 1024,
            backup_count=self.config.logging.get("backup_count", 5),
        )

        self.circuit_breaker: Optional[CircuitBreaker] = None
        if getattr(self.config, "circuit_breaker", None):
            cb_cfg = self.config.circuit_breaker
            self.circuit_breaker = CircuitBreaker(
                failure_threshold=cb_cfg.get("failure_threshold", 5),
                reset_timeout=cb_cfg.get("reset_timeout_sec", 60),
            )

        self.app = self._create_app()
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[Thread] = None

        # Register graceful shutdown hooks
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, self._handle_shutdown)
            except ValueError:
                # In some environments (e.g., threads), signals cannot be set
                pass

    def _default_port_for_type(self, agent_type: str) -> int:
        """Return default port from config for the given agent type."""
        if agent_type == "league_manager":
            return self.config.network.league_manager_port
        if agent_type == "referee":
            return self.config.network.referee_port_start
        return self.config.network.player_port_start

    def _create_app(self) -> FastAPI:
        """Initialize FastAPI application with basic health endpoint."""
        app = FastAPI(title=f"{self.agent_type.capitalize()} Agent", version="1.0.0")

        @app.get("/health")
        async def health() -> Dict[str, str]:
            return {"status": "ok"}

        # Expose agent instance on app for handlers if needed
        app.state.agent = self
        return app

    @staticmethod
    def _log_level_int(level: str) -> int:
        """Convert level string to logging module integer."""
        import logging

        return getattr(logging, level.upper(), logging.INFO)

    @staticmethod
    def _utc_timestamp() -> str:
        """ISO 8601 UTC timestamp without microseconds."""
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _conversation_id() -> str:
        """Generate a unique conversation ID."""
        return f"conv-{uuid.uuid4()}"

    def start(self, run_in_thread: bool = True) -> None:
        """
        Start the Uvicorn server hosting this agent.

        Args:
            run_in_thread: If True, run the server in a background thread (default).
                           If False, run synchronously (useful for tests).
        """
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level=self.log_level.lower(),
            timeout_keep_alive=self.config.network.request_timeout_sec,
        )
        self._server = uvicorn.Server(config=config)

        if run_in_thread:
            self._thread = Thread(target=self._server.run, daemon=True)
            self._thread.start()
        else:
            self._server.run()

    def stop(self, wait: bool = True) -> None:
        """Gracefully stop the Uvicorn server."""
        if self._server:
            self._server.should_exit = True

        if wait and self._thread and self._thread.is_alive():
            self._thread.join(timeout=float(self.config.timeouts.generic_sec))

    def _handle_shutdown(self, signum, frame=None) -> None:
        """Handle OS shutdown signals."""
        try:
            sig_name = signal.Signals(signum).name
        except Exception:
            sig_name = str(signum)
        self.logger.info("Shutdown signal received", event_type="AGENT_SHUTDOWN", signal=sig_name)
        self.stop()

    async def register(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register this agent with the League Manager via JSON-RPC (async).

        THREAD SAFETY: Uses async call_with_retry for non-blocking HTTP request.

        Args:
            metadata: Agent-specific metadata (player_meta or referee_meta content).

        Returns:
            JSON-RPC response dictionary.
        """
        endpoint = f"http://{self.config.network.host}:{self.config.network.league_manager_port}/mcp"
        base_fields = {
            "sender": self.sender,
            "timestamp": self._utc_timestamp(),
            "conversation_id": self._conversation_id(),
            "league_id": self.league_id,
        }

        if self.agent_type == "referee":
            request = RefereeRegisterRequest(referee_meta=metadata, **base_fields)
        else:
            request = LeagueRegisterRequest(player_meta=metadata, **base_fields)

        payload = request.model_dump()
        self.logger.info(
            "Sending registration",
            event_type="AGENT_REGISTER",
            message_type=payload.get("message_type"),
            conversation_id=payload.get("conversation_id"),
            data={"endpoint": endpoint},
        )

        return await call_with_retry(
            endpoint=endpoint,
            method=payload["message_type"],
            params=payload,
            timeout=self.config.network.request_timeout_sec,
            logger=self.std_logger,
            circuit_breaker=self.circuit_breaker,
        )

    @classmethod
    def load_config(cls, path: Path | str = DEFAULT_SYSTEM_CONFIG_PATH) -> SystemConfig:
        """Load and validate system configuration."""
        return load_system_config(path)
