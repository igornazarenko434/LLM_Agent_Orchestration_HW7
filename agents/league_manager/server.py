"""
League Manager MCP server (Missions 7.9-7.12).

Implements:
- M7.9: Registration handlers (referee, player)
- M7.9.5: Data retention initialization
- M7.10: Round-robin scheduler
- M7.11: Standings calculator
- M7.12: Match result handler
"""

from __future__ import annotations

import asyncio
import hashlib
import itertools
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agents.base import BaseAgent
from fastapi import Request
from fastapi.responses import JSONResponse

from league_sdk.cleanup import archive_old_matches, get_retention_config, run_full_cleanup
from league_sdk.config_loader import load_agents_config, load_league_config, load_system_config
from league_sdk.logger import log_error, log_message_received, log_message_sent
from league_sdk.method_aliases import translate_pdf_method_to_message_type
from league_sdk.protocol import (
    ErrorCode,
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    LeagueCompleted,
    LeagueQuery,
    LeagueQueryResponse,
    LeagueRegisterResponse,
    LeagueStandingsUpdate,
    MatchResultReport,
    RefereeRegisterResponse,
    RoundAnnouncement,
    RoundCompleted,
)
from league_sdk.queue_processor import SequentialQueueProcessor
from league_sdk.repositories import RoundsRepository, StandingsRepository
from league_sdk.retry import call_with_retry

AGENTS_CONFIG_PATH = "SHARED/config/agents/agents_config.json"
SYSTEM_CONFIG_PATH = "SHARED/config/system.json"


class LeagueManager(BaseAgent):
    """
    League Manager MCP server with registration, scheduling, and orchestration.

    Thread Safety (CRITICAL):
    - All endpoints async (non-blocking)
    - Concurrent registrations handled safely (in-memory dict)
    - No file I/O during registration (fast response)
    - Standings updates serialized via SequentialQueueProcessor
    """

    def __init__(
        self,
        agent_id: str = "LM01",
        league_id: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ) -> None:
        super().__init__(
            agent_id=agent_id,
            agent_type="league_manager",
            league_id=league_id or "league_2025_even_odd",
            host=host,
            port=port,
        )

        # Load configs (no hardcoding!)
        self.agents_config = load_agents_config(AGENTS_CONFIG_PATH)
        self.system_config = load_system_config(SYSTEM_CONFIG_PATH)
        self.league_config = load_league_config(
            f"SHARED/config/leagues/{league_id or 'league_2025_even_odd'}.json"
        )

        # Get league manager metadata from config
        self.lm_config = self.agents_config.get("league_manager", {})
        if not port:
            configured_port = self.lm_config.get("port")
            if configured_port is None:
                self.std_logger.warning(
                    "League Manager port not configured in agents_config.json, using default 8000. "
                    "Add 'league_manager.port' to config for explicit control."
                )
                self.port = 8000
            else:
                self.port = configured_port

        # In-memory registration storage (thread-safe with async)
        self.registered_referees: Dict[str, Dict[str, Any]] = {}
        self.registered_players: Dict[str, Dict[str, Any]] = {}

        # Counter for generating sequential IDs
        self.referee_counter = 0
        self.player_counter = 0

        # League orchestration state
        self.league_state: str = "INIT"
        self.current_round_id: Optional[int] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_stop: Optional[asyncio.Event] = None

        # Initialize repositories (M7.10, M7.11)
        self.rounds_repo = RoundsRepository(league_id=self.league_id)
        self.standings_repo = StandingsRepository(league_id=self.league_id)

        # Queue processor for thread-safe standings updates (M7.11)
        self.standings_processor = SequentialQueueProcessor(
            process_func=self._process_match_result,
            max_queue_size=self.system_config.network.max_connections,
            logger=self.std_logger,
        )

        # Initialize data retention subsystem (M7.9.5)
        self._init_data_retention()

        self._register_mcp_route()
        self._log_registry_snapshot("startup")

    def _log_registry_snapshot(self, context: str) -> None:
        """Log league state and current registry contents for verification."""
        self.std_logger.info(
            "Registry snapshot",
            extra={
                "event_type": "REGISTRY_SNAPSHOT",
                "context": context,
                "league_state": self.league_state,
                "registered_referees": list(self.registered_referees.keys()),
                "registered_players": list(self.registered_players.keys()),
            },
        )

    def _log_league_state_change(self, context: str, previous: str, current: str) -> None:
        """Log league_state transitions explicitly for verification."""
        self.std_logger.info(
            "League state changed",
            extra={
                "event_type": "LEAGUE_STATE_CHANGED",
                "context": context,
                "from_state": previous,
                "to_state": current,
                "registered_referees": list(self.registered_referees.keys()),
                "registered_players": list(self.registered_players.keys()),
            },
        )

    async def start(self, run_in_thread: bool = True) -> None:  # type: ignore[override]
        """Start agent and queue processor."""
        # Start queue processor first
        await self.standings_processor.start()

        # Run cleanup on startup and schedule periodic cleanup (M7.13.5)
        await self._run_startup_cleanup()
        self._start_cleanup_scheduler()

        # Start base server
        super().start(run_in_thread=run_in_thread)

    def stop(self, wait: bool = True) -> None:
        """Stop agent and queue processor."""
        # Stop base server first
        super().stop(wait=wait)

        # Stop queue processor (run in new loop if needed, but stop is async)
        # Since stop() is synchronous in BaseAgent, we need to handle async stop here
        # Ideally, BaseAgent.stop should be async or we run this in existing loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(
                    self.standings_processor.stop(
                        timeout=float(self.system_config.timeouts.generic_sec)
                    )
                )
            else:
                loop.run_until_complete(
                    self.standings_processor.stop(
                        timeout=float(self.system_config.timeouts.generic_sec)
                    )
                )
        except Exception:
            # Fallback if loop issues
            pass

        # Stop cleanup scheduler
        self._stop_cleanup_scheduler()

    def _get_config_with_warning(
        self, config_dict: Dict[str, Any], key: str, default: Any, config_name: str
    ) -> Any:
        """
        Get config value with warning if missing (P2.1 best practice).

        Args:
            config_dict: Configuration dictionary to query
            key: Configuration key to retrieve
            default: Default value if key is missing
            config_name: Human-readable config name for warning message

        Returns:
            Configuration value or default
        """
        if hasattr(config_dict, "get"):
            value = config_dict.get(key)
        else:
            value = getattr(config_dict, key, None)
        if value is None:
            self.std_logger.warning(
                f"Config key '{key}' not found in {config_name}, using default: {default}. "
                f"Add '{key}' to config for explicit control."
            )
            return default
        return value

    def _init_data_retention(self) -> None:
        """
        Initialize data retention subsystem (M7.9.5).

        Creates archive directories and logs retention policy configuration.
        Called during League Manager startup to ensure retention infrastructure is ready.

        Thread Safety: Sync method called during __init__ (single-threaded startup).
        """
        # Load retention configuration from system.json
        self.retention_config = get_retention_config()

        # Check if retention is enabled
        if not self.retention_config.get("enabled", True):
            self.std_logger.warning(
                "Data retention is DISABLED in system configuration",
                extra={
                    "event_type": "RETENTION_DISABLED",
                    "agent_id": self.agent_id,
                },
            )
            return

        # Create archive directories (if not exist)
        archive_path_str = self._get_config_with_warning(
            self.retention_config, "archive_path", "SHARED/archive", "system.json data_retention"
        )
        archive_path = Path(archive_path_str)
        archive_subdirs = ["logs", "matches", "players", "leagues"]

        created_dirs = []
        for subdir in archive_subdirs:
            dir_path = archive_path / subdir
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(dir_path))

        # Validate and load retention config values with warnings
        logs_retention_days = self._get_config_with_warning(
            self.retention_config, "logs_retention_days", 30, "system.json data_retention"
        )
        match_data_retention_days = self._get_config_with_warning(
            self.retention_config, "match_data_retention_days", 365, "system.json data_retention"
        )
        player_history_retention_days = self._get_config_with_warning(
            self.retention_config, "player_history_retention_days", 365, "system.json data_retention"
        )
        rounds_retention_days = self._get_config_with_warning(
            self.retention_config, "rounds_retention_days", 365, "system.json data_retention"
        )
        standings_retention = self._get_config_with_warning(
            self.retention_config, "standings_retention", "permanent", "system.json data_retention"
        )
        archive_enabled = self._get_config_with_warning(
            self.retention_config, "archive_enabled", True, "system.json data_retention"
        )
        archive_compression = self._get_config_with_warning(
            self.retention_config, "archive_compression", "gzip", "system.json data_retention"
        )
        cleanup_schedule = self._get_config_with_warning(
            self.retention_config, "cleanup_schedule_cron", "0 2 * * *", "system.json data_retention"
        )

        # Log retention policy initialization
        self.std_logger.info(
            "Data retention initialized successfully",
            extra={
                "event_type": "RETENTION_INITIALIZED",
                "agent_id": self.agent_id,
                "retention_enabled": True,
                "logs_retention_days": logs_retention_days,
                "match_data_retention_days": match_data_retention_days,
                "player_history_retention_days": player_history_retention_days,
                "rounds_retention_days": rounds_retention_days,
                "standings_retention": standings_retention,
                "archive_enabled": archive_enabled,
                "archive_path": str(archive_path),
                "archive_compression": archive_compression,
                "cleanup_schedule": cleanup_schedule,
                "directories_created": created_dirs if created_dirs else "all_exist",
            },
        )

    async def _run_startup_cleanup(self) -> None:
        """Run cleanup once on startup if retention is enabled."""
        if not self.retention_config.get("enabled", True):
            return

        self.std_logger.info("Running startup data retention cleanup...")
        try:
            results = await run_full_cleanup(logger=self.std_logger)
            total_mb = sum(r.bytes_freed / (1024**2) for r in results.values())
            total_files = sum(r.files_deleted for r in results.values())
            self.std_logger.info(
                f"Startup cleanup completed: freed {total_mb:.2f} MB, deleted {total_files} files"
            )
        except Exception as exc:
            self.std_logger.error(f"Startup cleanup failed: {exc}", exc_info=True)

    def _start_cleanup_scheduler(self) -> None:
        """Start periodic cleanup scheduler task."""
        if not self.retention_config.get("enabled", True):
            return
        if self._cleanup_task and not self._cleanup_task.done():
            return
        self._cleanup_stop = asyncio.Event()
        self._cleanup_task = asyncio.create_task(self._cleanup_scheduler())

    def _stop_cleanup_scheduler(self) -> None:
        """Stop periodic cleanup scheduler task."""
        if not self._cleanup_stop:
            return
        self._cleanup_stop.set()
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

    async def _cleanup_scheduler(self) -> None:
        """Run cleanup on a daily schedule (default: 02:00 UTC)."""
        while self._cleanup_stop and not self._cleanup_stop.is_set():
            delay = self._seconds_until_next_cleanup()
            try:
                await asyncio.wait_for(self._cleanup_stop.wait(), timeout=delay)
            except asyncio.TimeoutError:
                # Scheduled cleanup time reached
                self.std_logger.info("Starting scheduled data retention cleanup...")
                try:
                    results = await run_full_cleanup(logger=self.std_logger)
                    total_mb = sum(r.bytes_freed / (1024**2) for r in results.values())
                    total_files = sum(r.files_deleted for r in results.values())
                    self.std_logger.info(
                        f"Scheduled cleanup completed: freed {total_mb:.2f} MB, "
                        f"deleted {total_files} files"
                    )
                except Exception as exc:
                    self.std_logger.error(f"Cleanup scheduler failed: {exc}", exc_info=True)

    def _seconds_until_next_cleanup(self) -> float:
        """Compute seconds until next scheduled cleanup."""
        cron = self.retention_config.get("cleanup_schedule_cron", "0 2 * * *")
        hour, minute = self._parse_daily_cron(cron)

        now = datetime.now(timezone.utc)
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run = next_run + timedelta(days=1)
        return (next_run - now).total_seconds()

    def _parse_daily_cron(self, cron: str) -> tuple[int, int]:
        """Parse cron string for daily schedule (minute hour * * *)."""
        try:
            parts = cron.split()
            if len(parts) != 5:
                raise ValueError("Invalid cron format")
            minute = int(parts[0])
            hour = int(parts[1])
            if not (0 <= minute <= 59 and 0 <= hour <= 23):
                raise ValueError("Invalid cron values")
            return hour, minute
        except Exception:
            self.std_logger.warning(f"Invalid cleanup cron '{cron}', defaulting to 02:00 UTC")
            return 2, 0

    async def _on_league_completed_cleanup(self) -> None:
        """
        Run specialized cleanup when league completes (M7.13.5).

        Archives all matches from the completed league immediately,
        regardless of age, for permanent storage.
        """
        if not self.retention_config.get("enabled", True):
            return

        self.std_logger.info(f"League {self.league_id} completed, running final cleanup...")

        try:
            # Archive all matches from this league immediately (retention_days=0)
            result = await archive_old_matches(
                retention_days=0, logger=self.std_logger  # Archive all, regardless of age
            )

            mb_freed = result.bytes_freed / (1024**2)
            self.std_logger.info(
                f"League {self.league_id} data archived: "
                f"freed {mb_freed:.2f} MB, archived {result.files_deleted} match files"
            )

        except Exception as exc:
            self.std_logger.error(f"Failed to archive league {self.league_id}: {exc}", exc_info=True)

    def _register_mcp_route(self) -> None:
        """
        Attach /mcp JSON-RPC endpoint.

        Thread Safety: async endpoint, handles concurrent requests safely.
        """

        @self.app.post("/mcp")
        async def mcp(request: Request):
            body = await request.json()
            rpc_request = self._parse_rpc(body)
            if isinstance(rpc_request, JSONResponse):
                return rpc_request

            # PDF COMPATIBILITY LAYER: Translate PDF-style method names to message types
            original_method = rpc_request.method
            rpc_request.method = translate_pdf_method_to_message_type(rpc_request.method)

            # Log translation if PDF-style method was used
            if original_method != rpc_request.method:
                self.std_logger.debug(
                    f"Translated PDF method '{original_method}' → '{rpc_request.method}'",
                    extra={
                        "pdf_method": original_method,
                        "message_type": rpc_request.method,
                        "compatibility_layer": True,
                    },
                )

            # Route to handler based on method
            if rpc_request.method == "REFEREE_REGISTER_REQUEST":
                return await self._handle_referee_registration(rpc_request)
            elif rpc_request.method == "LEAGUE_REGISTER_REQUEST":
                return await self._handle_player_registration(rpc_request)
            elif rpc_request.method == "MATCH_RESULT_REPORT":
                return await self._handle_match_result_report(rpc_request)
            elif rpc_request.method == "LEAGUE_QUERY":
                return await self._handle_league_query(rpc_request)
            elif rpc_request.method == "get_standings":
                return await self._handle_get_standings(rpc_request)
            elif rpc_request.method == "get_league_status":
                return await self._handle_get_league_status(rpc_request)
            elif rpc_request.method == "start_league":
                return await self._handle_start_league(rpc_request)
            else:
                return self._error_response(
                    rpc_request.id,
                    code=-32601,
                    message="Method not found",
                    error_code=ErrorCode.INVALID_ENDPOINT,
                    status=404,
                    payload=rpc_request.model_dump(),
                )

    async def _handle_referee_registration(self, rpc_request: JSONRPCRequest) -> JSONResponse:
        """
        Handle REFEREE_REGISTER_REQUEST (M7.9).

        Thread Safety: Async handler, safe concurrent registration.

        Expected params:
        {
            "sender": "referee:REF01",
            "timestamp": "2025-01-15T12:00:00Z",
            "conversation_id": "reg-REF01",
            "referee_meta": {
                "display_name": "Referee 01",
                "version": "1.0.0",
                "game_types": ["even_odd"],
                "contact_endpoint": "http://localhost:8001/mcp",
                "max_concurrent_matches": 10
            }
        }
        """
        try:
            params = rpc_request.params
            log_message_received(self.std_logger, rpc_request.model_dump())

            # Validate required fields
            required_fields = ["sender", "timestamp", "conversation_id", "referee_meta"]
            for field in required_fields:
                if field not in params:
                    return self._error_response(
                        rpc_request.id,
                        code=-32602,
                        message=f"Missing required parameter: {field}",
                        error_code=ErrorCode.INVALID_MESSAGE_FORMAT,
                        status=400,
                        payload=params,
                    )

            referee_meta = params["referee_meta"]
            contact_endpoint = referee_meta.get("contact_endpoint")

            # Check for duplicate registration (E017)
            if self._is_duplicate_referee(contact_endpoint):
                return self._error_response(
                    rpc_request.id,
                    code=-32000,
                    message="Referee already registered",
                    error_code=ErrorCode.DUPLICATE_REGISTRATION,
                    status=409,
                    payload=params,
                    extra_data={"contact_endpoint": contact_endpoint},
                )

            # Generate referee ID and auth token
            referee_id = self._referee_id_from_sender(params.get("sender"))
            if referee_id and referee_id in self.registered_referees:
                return self._error_response(
                    rpc_request.id,
                    code=-32000,
                    message="Referee already registered",
                    error_code=ErrorCode.DUPLICATE_REGISTRATION,
                    status=409,
                    payload=params,
                    extra_data={"referee_id": referee_id},
                )
            if not referee_id:
                referee_id = self._generate_referee_id()
            auth_token = self._generate_auth_token()

            # Store registration (in-memory, thread-safe)
            self.registered_referees[referee_id] = {
                "referee_id": referee_id,
                "auth_token": auth_token,
                "sender": params.get("sender"),
                "contact_endpoint": contact_endpoint,
                "display_name": referee_meta.get("display_name", referee_id),
                "version": referee_meta.get("version", "1.0.0"),
                "game_types": referee_meta.get("game_types", []),
                "max_concurrent_matches": referee_meta.get("max_concurrent_matches", 10),
                "registered_at": self._timestamp(),
                "status": "ACTIVE",
            }
            self._log_registry_snapshot("referee_registered")

            # Build success response
            response_data = RefereeRegisterResponse(
                sender=f"league_manager:{self.agent_id}",
                timestamp=self._timestamp(),
                conversation_id=params["conversation_id"],
                status="ACCEPTED",
                referee_id=referee_id,
                auth_token=auth_token,
                league_id=self.league_id,
            )

            rpc_response = JSONRPCResponse(id=rpc_request.id, result=response_data.model_dump())

            log_message_sent(self.std_logger, response_data.model_dump())

            self.std_logger.info(
                f"Referee registered: {referee_id}",
                extra={
                    "referee_id": referee_id,
                    "contact_endpoint": contact_endpoint,
                    "display_name": referee_meta.get("display_name"),
                },
            )

            return JSONResponse(status_code=200, content=rpc_response.model_dump())

        except Exception as exc:
            return self._error_response(
                rpc_request.id,
                code=-32000,
                message="Server error",
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                status=500,
                payload=rpc_request.model_dump(),
                extra_data={"error": str(exc)},
            )

    async def _handle_player_registration(self, rpc_request: JSONRPCRequest) -> JSONResponse:
        """
        Handle LEAGUE_REGISTER_REQUEST (M7.9).

        Thread Safety: Async handler, safe concurrent registration.

        Expected params:
        {
            "sender": "player:P01",
            "timestamp": "2025-01-15T12:00:00Z",
            "conversation_id": "reg-P01",
            "player_meta": {
                "display_name": "Player 01",
                "version": "1.0.0",
                "game_types": ["even_odd"],
                "strategy": "random"
            }
        }
        """
        try:
            params = rpc_request.params
            log_message_received(self.std_logger, rpc_request.model_dump())

            # Validate required fields
            required_fields = ["sender", "timestamp", "conversation_id", "player_meta"]
            for field in required_fields:
                if field not in params:
                    return self._error_response(
                        rpc_request.id,
                        code=-32602,
                        message=f"Missing required parameter: {field}",
                        error_code=ErrorCode.INVALID_MESSAGE_FORMAT,
                        status=400,
                        payload=params,
                    )

            player_meta = params["player_meta"]
            sender = params["sender"]

            # Check for duplicate registration (E017)
            if self._is_duplicate_player(sender):
                return self._error_response(
                    rpc_request.id,
                    code=-32000,
                    message="Player already registered",
                    error_code=ErrorCode.DUPLICATE_REGISTRATION,
                    status=409,
                    payload=params,
                    extra_data={"sender": sender},
                )

            # Generate player ID and auth token
            player_id = self._player_id_from_sender(params.get("sender"))
            if player_id and player_id in self.registered_players:
                return self._error_response(
                    rpc_request.id,
                    code=-32000,
                    message="Player already registered",
                    error_code=ErrorCode.DUPLICATE_REGISTRATION,
                    status=409,
                    payload=params,
                    extra_data={"player_id": player_id},
                )
            if not player_id:
                player_id = self._generate_player_id()
            auth_token = self._generate_auth_token()

            # Store registration (in-memory, thread-safe)
            self.registered_players[player_id] = {
                "player_id": player_id,
                "auth_token": auth_token,
                "sender": sender,
                "contact_endpoint": player_meta.get("contact_endpoint"),
                "display_name": player_meta.get("display_name", player_id),
                "version": player_meta.get("version", "1.0.0"),
                "game_types": player_meta.get("game_types", []),
                "strategy": player_meta.get("strategy", "unknown"),
                "registered_at": self._timestamp(),
                "status": "ACTIVE",
            }
            self._log_registry_snapshot("player_registered")

            # Build success response
            response_data = LeagueRegisterResponse(
                sender=f"league_manager:{self.agent_id}",
                timestamp=self._timestamp(),
                conversation_id=params["conversation_id"],
                status="ACCEPTED",
                player_id=player_id,
                auth_token=auth_token,
                league_id=self.league_id,
            )

            rpc_response = JSONRPCResponse(id=rpc_request.id, result=response_data.model_dump())

            log_message_sent(self.std_logger, response_data.model_dump())

            self.std_logger.info(
                f"Player registered: {player_id}",
                extra={
                    "player_id": player_id,
                    "sender": sender,
                    "display_name": player_meta.get("display_name"),
                    "contact_endpoint": player_meta.get("contact_endpoint"),
                },
            )

            return JSONResponse(status_code=200, content=rpc_response.model_dump())

        except Exception as exc:
            return self._error_response(
                rpc_request.id,
                code=-32000,
                message="Server error",
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                status=500,
                payload=rpc_request.model_dump(),
                extra_data={"error": str(exc)},
            )

    def _generate_referee_id(self) -> str:
        """Generate sequential referee ID (REF01, REF02, ...)."""
        self.referee_counter += 1
        return f"REF{self.referee_counter:02d}"

    def _generate_player_id(self) -> str:
        """Generate sequential player ID (P01, P02, ...)."""
        self.player_counter += 1
        return f"P{self.player_counter:02d}"

    def _referee_id_from_sender(self, sender: Optional[str]) -> Optional[str]:
        """Extract referee ID from sender if formatted as referee:REFxx."""
        if not sender or not sender.startswith("referee:"):
            return None
        candidate = sender.split("referee:", 1)[1]
        return candidate or None

    def _player_id_from_sender(self, sender: Optional[str]) -> Optional[str]:
        """Extract player ID from sender if formatted as player:Pxx."""
        if not sender or not sender.startswith("player:"):
            return None
        candidate = sender.split("player:", 1)[1]
        return candidate or None

    def _generate_auth_token(self) -> str:
        """
        Generate cryptographically random auth token (M7.9).

        Returns 32-character hexadecimal token (128 bits of entropy).
        """
        return secrets.token_hex(16)  # 16 bytes = 32 hex chars

    def _is_duplicate_referee(self, contact_endpoint: str) -> bool:
        """Check if referee with this endpoint already registered."""
        for ref in self.registered_referees.values():
            if ref.get("contact_endpoint") == contact_endpoint:
                return True
        return False

    def _get_referee_by_sender(self, sender: str) -> Optional[Dict[str, Any]]:
        """Lookup registered referee by sender value."""
        for ref in self.registered_referees.values():
            if ref.get("sender") == sender:
                return ref
        return None

    def _is_duplicate_player(self, sender: str) -> bool:
        """Check if player with this sender already registered."""
        for player in self.registered_players.values():
            if player.get("sender") == sender:
                return True
        return False

    def _allowed_query_senders(self) -> set[str]:
        senders: set[str] = set()
        # Filter out None values explicitly for type safety
        player_senders = (p.get("sender") for p in self.registered_players.values())
        senders.update(s for s in player_senders if s is not None)
        referee_senders = (r.get("sender") for r in self.registered_referees.values())
        senders.update(s for s in referee_senders if s is not None)
        return senders

    def _auth_token_matches_sender(self, sender: str, auth_token: str) -> bool:
        for player in self.registered_players.values():
            if player.get("sender") == sender:
                return player.get("auth_token") == auth_token
        for ref in self.registered_referees.values():
            if ref.get("sender") == sender:
                return ref.get("auth_token") == auth_token
        return False

    def _validate_debug_tool_request(self, rpc_request: JSONRPCRequest) -> Optional[JSONResponse]:
        params = rpc_request.params
        protocol = params.get("protocol")
        if protocol and protocol != self.system_config.protocol_version:
            return self._error_response(
                rpc_request.id,
                code=-32602,
                message="Protocol mismatch",
                error_code=ErrorCode.PROTOCOL_VERSION_MISMATCH,
                status=400,
                payload=rpc_request.model_dump(),
                extra_data={"supported_protocols": [self.system_config.protocol_version]},
            )
        sender = params.get("sender")
        if not sender:
            return self._error_response(
                rpc_request.id,
                code=-32602,
                message="Missing sender",
                error_code=ErrorCode.INVALID_MESSAGE_FORMAT,
                status=400,
                payload=rpc_request.model_dump(),
            )
        if sender not in self._allowed_query_senders():
            return self._error_response(
                rpc_request.id,
                code=-32602,
                message="Sender not registered",
                error_code=ErrorCode.AGENT_NOT_REGISTERED,
                status=403,
                payload=rpc_request.model_dump(),
                extra_data={"sender": sender},
            )
        if self.system_config.security.require_auth:
            auth_token = params.get("auth_token")
            if not auth_token:
                return self._error_response(
                    rpc_request.id,
                    code=-32000,
                    message="Missing auth token",
                    error_code=ErrorCode.AUTHENTICATION_FAILED,
                    status=401,
                    payload=rpc_request.model_dump(),
                )
            if not self._auth_token_matches_sender(sender, auth_token):
                return self._error_response(
                    rpc_request.id,
                    code=-32000,
                    message="Invalid auth token",
                    error_code=ErrorCode.AUTH_TOKEN_INVALID,
                    status=401,
                    payload=rpc_request.model_dump(),
                    extra_data={"sender": sender},
                )
        return None

    def _timestamp(self) -> str:
        """Generate ISO 8601 UTC timestamp."""
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _parse_rpc(self, body: Dict[str, Any]) -> JSONRPCRequest | JSONResponse:
        """Parse JSON-RPC request from body."""
        try:
            return JSONRPCRequest(**body)
        except Exception as exc:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request",
                        "data": {"error": str(exc)},
                    },
                    "id": body.get("id"),
                },
            )

    def _error_response(
        self,
        request_id: Any,
        code: int,
        message: str,
        error_code: ErrorCode | str,
        status: int,
        payload: Dict[str, Any],
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> JSONResponse:
        """Build JSON-RPC error response."""
        # ErrorCode is a class of string constants, so use the value directly
        code_val = error_code if isinstance(error_code, str) else str(error_code)
        error_data = {"error_code": code_val, "payload": payload}
        if extra_data:
            error_data.update(extra_data)

        error = JSONRPCError(code=code, message=message, data=error_data)
        self._log_error(error, payload)

        return JSONResponse(
            status_code=status,
            content={
                "jsonrpc": "2.0",
                "error": error.model_dump(),
                "id": request_id,
            },
        )

    def _log_error(self, error: JSONRPCError, payload: Dict[str, Any]) -> None:
        """Helper to log structured errors."""
        details = error.data if isinstance(error.data, dict) else {"details": error.data}
        details.update(
            {
                "message": error.message,
                "jsonrpc_code": error.code,
                "method": payload.get("method"),
            }
        )
        log_error(
            self.std_logger,
            details.get("error_code", ErrorCode.INTERNAL_SERVER_ERROR),
            details,
        )

    # ========================================================================
    # M7.10: ROUND-ROBIN SCHEDULER
    # ========================================================================

    def create_schedule(
        self,
        player_ids: Optional[List[str]] = None,
        referee_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate round-robin tournament schedule using Circle Method algorithm (M7.10).

        Creates n*(n-1)/2 matches for n players, distributed across balanced rounds
        with even referee assignment. Persists schedule to rounds.json.

        Args:
            player_ids: List of registered player IDs (default: use registered_players)
            referee_ids: List of referee IDs (default: use registered_referees)

        Returns:
            Dictionary with schedule metadata:
            {
                "total_matches": int,
                "total_rounds": int,
                "players_count": int,
                "referees_count": int,
                "schedule": List[Dict] - rounds with matches
            }

        Raises:
            ValueError: If validation fails (duplicate players, insufficient participants)

        Thread Safety:
            - Sync method (called during league initialization)
            - Uses RoundsRepository for atomic file writes
            - Deterministic scheduling with league_id-based seed

        Algorithm:
            Circle Method from doc/algorithms/round_robin.md
            - Fix one player at position 0
            - Rotate remaining players for each round
            - Pair players symmetrically
            - Handle odd player count with bye

        Compliance (M7.10):
            - Validates no duplicate player IDs (E002)
            - Includes league_id and game_type in each match
            - Logs per-match assignments for traceability
            - Warns if match count exceeds referee capacity
        """
        # Use registered players if not provided
        if player_ids is None:
            player_ids = list(self.registered_players.keys())

        if referee_ids is None:
            referee_ids = list(self.registered_referees.keys())

        # Validate no duplicate player IDs (E002)
        if len(player_ids) != len(set(player_ids)):
            duplicates = [pid for pid in set(player_ids) if player_ids.count(pid) > 1]
            self.std_logger.error(
                f"Duplicate player IDs detected: {duplicates}",
                extra={
                    "event_type": "SCHEDULE_ERROR",
                    "error_code": ErrorCode.INVALID_MESSAGE_FORMAT,
                    "duplicates": duplicates,
                },
            )
            raise ValueError(
                f"Duplicate player IDs not allowed: {duplicates}. "
                f"Error code: {ErrorCode.INVALID_MESSAGE_FORMAT} (E002)"
            )

        # Validate minimum participants (from league config)
        min_players = getattr(self.league_config.participants, "min_players", 2)
        if len(player_ids) < min_players:
            self.std_logger.error(
                f"Insufficient players for scheduling: {len(player_ids)} < {min_players}",
                extra={
                    "event_type": "SCHEDULE_ERROR",
                    "error_code": ErrorCode.INVALID_MESSAGE_FORMAT,
                    "players_count": len(player_ids),
                    "min_required": min_players,
                },
            )
            raise ValueError(
                f"At least {min_players} players required for scheduling. "
                f"Error code: {ErrorCode.INVALID_MESSAGE_FORMAT} (E002)"
            )

        if len(referee_ids) == 0:
            self.std_logger.error(
                "No referees available for scheduling",
                extra={
                    "event_type": "SCHEDULE_ERROR",
                    "error_code": ErrorCode.INVALID_MESSAGE_FORMAT,
                },
            )
            raise ValueError(
                f"At least 1 referee required for scheduling. "
                f"Error code: {ErrorCode.INVALID_MESSAGE_FORMAT} (E002)"
            )

        # Deterministic shuffle for fairness (reproducible with league_id seed)
        player_ids_sorted = self._shuffle_players_deterministic(player_ids)

        # Generate round-robin rounds using Circle Method
        rounds = self._generate_round_robin_rounds(player_ids_sorted)

        # Get game_type from league config
        game_type = self.league_config.game_type

        # Assign referees to matches using round-robin distribution
        schedule = self._assign_referees_to_rounds(rounds, referee_ids, game_type)

        # Check referee capacity and warn if needed
        max_matches_per_round = max(len(round_data["matches"]) for round_data in schedule)
        total_referee_capacity = sum(
            self.registered_referees.get(ref_id, {}).get("max_concurrent_matches", 10)
            for ref_id in referee_ids
        )
        if max_matches_per_round > total_referee_capacity:
            self.std_logger.warning(
                f"Round has {max_matches_per_round} matches but total referee "
                f"capacity is {total_referee_capacity}. "
                "Matches may need to be staggered during execution.",
                extra={
                    "event_type": "CAPACITY_WARNING",
                    "max_matches_per_round": max_matches_per_round,
                    "total_referee_capacity": total_referee_capacity,
                    "referees_count": len(referee_ids),
                },
            )

        # Generate match IDs and persist to rounds.json
        total_matches = self._persist_schedule(schedule)

        # Log scheduling completion
        self.std_logger.info(
            f"Schedule generated successfully: {total_matches} matches across {len(schedule)} rounds",
            extra={
                "event_type": "SCHEDULE_CREATED",
                "total_matches": total_matches,
                "total_rounds": len(schedule),
                "players_count": len(player_ids),
                "referees_count": len(referee_ids),
                "league_id": self.league_id,
                "game_type": game_type,
            },
        )

        return {
            "total_matches": total_matches,
            "total_rounds": len(schedule),
            "players_count": len(player_ids),
            "referees_count": len(referee_ids),
            "schedule": schedule,
        }

    def _shuffle_players_deterministic(self, player_ids: List[str]) -> List[str]:
        """
        Shuffle players deterministically using league_id as seed.

        Ensures fairness while maintaining reproducibility for testing.
        Per doc/algorithms/round_robin.md: Use hash(league_id) as seed.

        Args:
            player_ids: List of player IDs

        Returns:
            Shuffled list of player IDs
        """
        import random

        # Create deterministic seed from league_id
        # Type guard: self.league_id should never be None at this point (set in __init__)
        assert self.league_id is not None, "league_id must be set"
        seed = int(hashlib.md5(self.league_id.encode()).hexdigest(), 16) % (2**32)

        # Shuffle with seed for reproducibility
        shuffled = player_ids.copy()
        random.Random(seed).shuffle(shuffled)

        return shuffled

    def _generate_round_robin_rounds(self, player_ids: List[str]) -> List[List[Tuple[str, str]]]:
        """
        Generate round-robin rounds using Circle Method algorithm.

        Implements algorithm from doc/algorithms/round_robin.md:
        - Fix player at position 0
        - Rotate remaining players clockwise each round
        - Pair players symmetrically
        - Handle odd count with bye (no match generated)

        Args:
            player_ids: List of player IDs (already shuffled)

        Returns:
            List of rounds, each round is list of (player_a, player_b) tuples
        """
        n = len(player_ids)
        # Allow None in the list for bye handling
        players: List[Optional[str]] = list(player_ids)

        # Handle odd number of players: add bye
        if n % 2 == 1:
            players.append(None)  # None represents bye
            n += 1

        rounds = []
        # Create rotation indices: keep 0 fixed, rotate 1 to n-1
        rotation_indices = list(range(n))

        # Total rounds for single round-robin: n-1
        for round_num in range(n - 1):
            current_round = []

            # Pair players symmetrically
            for i in range(n // 2):
                p1_idx = rotation_indices[i]
                p2_idx = rotation_indices[n - 1 - i]

                p1 = players[p1_idx]
                p2 = players[p2_idx]

                # Skip if either player is bye
                if p1 is not None and p2 is not None:
                    current_round.append((p1, p2))

            rounds.append(current_round)

            # Rotate indices: keep [0] fixed, insert last at position [1]
            # [0, 1, 2, 3] -> [0, 3, 1, 2] -> [0, 2, 3, 1]
            rotation_indices = [rotation_indices[0]] + [rotation_indices[-1]] + rotation_indices[1:-1]

        return rounds

    def _assign_referees_to_rounds(
        self, rounds: List[List[Tuple[str, str]]], referee_ids: List[str], game_type: str
    ) -> List[Dict[str, Any]]:
        """
        Assign referees to matches using round-robin distribution.

        Uses modulo assignment for even load balancing across referees.
        Per doc/algorithms/round_robin.md: referee = referees[idx % num_referees]

        Args:
            rounds: List of rounds with (player_a, player_b) tuples
            referee_ids: List of available referee IDs
            game_type: Game type from league config (e.g., "even_odd")

        Returns:
            List of round dictionaries with match metadata

        Compliance:
            - Each match includes league_id, round_id, match_id, game_type
            - Logs per-match assignments for traceability (M7.10)
        """
        schedule = []
        match_counter = 0  # Global match counter for modulo assignment

        for round_idx, round_matches in enumerate(rounds):
            round_id = round_idx + 1
            round_data: dict[str, Any] = {
                "round_id": round_id,
                "matches": [],
                "status": "PENDING",
            }

            for match in round_matches:
                player_a, player_b = match

                # Assign referee using round-robin (modulo)
                referee_id = referee_ids[match_counter % len(referee_ids)]

                match_id = f"R{round_id}M{len(round_data['matches']) + 1}"

                # Build match data with all required fields
                match_data = {
                    "match_id": match_id,
                    "league_id": self.league_id,
                    "round_id": round_id,
                    "game_type": game_type,
                    "player_a_id": player_a,
                    "player_b_id": player_b,
                    "referee_id": referee_id,
                    "status": "PENDING",
                }

                # Log per-match assignment for traceability (M7.10 compliance)
                self.std_logger.info(
                    f"Match assigned: {match_id}",
                    extra={
                        "event_type": "MATCH_ASSIGNED",
                        "match_id": match_id,
                        "round_id": round_id,
                        "league_id": self.league_id,
                        "player_a_id": player_a,
                        "player_b_id": player_b,
                        "referee_id": referee_id,
                    },
                )

                round_data["matches"].append(match_data)
                match_counter += 1

            schedule.append(round_data)

        return schedule

    def _persist_schedule(self, schedule: List[Dict[str, Any]]) -> int:
        """
        Persist schedule to rounds.json using RoundsRepository.

        Args:
            schedule: List of round dictionaries

        Returns:
            Total number of matches scheduled
        """
        total_matches = 0

        for round_data in schedule:
            round_id = round_data["round_id"]
            matches = round_data["matches"]

            # Add round to repository (atomic write)
            self.rounds_repo.add_round(round_id=round_id, matches=matches)

            total_matches += len(matches)

        return total_matches

    async def _handle_match_result_report(self, rpc_request: JSONRPCRequest) -> JSONResponse:
        """
        Handle MATCH_RESULT_REPORT from referee (M7.12).

        Thread Safety:
        - Validates sender and token
        - Enqueues processing to SequentialQueueProcessor (no race condition)
        - Returns immediate acknowledgement
        """
        try:
            params = rpc_request.params
            log_message_received(self.std_logger, rpc_request.model_dump())

            # Validate sender is a registered referee
            sender = params.get("sender", "")
            if not sender.startswith("referee:"):
                return self._error_response(
                    rpc_request.id,
                    code=-32602,
                    message="Invalid sender format",
                    error_code=ErrorCode.INVALID_MESSAGE_FORMAT,
                    status=400,
                    payload=params,
                )

            referee = self._get_referee_by_sender(sender)
            if not referee:
                return self._error_response(
                    rpc_request.id,
                    code=-32000,
                    message="Referee not registered",
                    error_code=ErrorCode.AGENT_NOT_REGISTERED,
                    status=403,
                    payload=params,
                )

            # Validate auth token if sender is known
            # (In production, would lookup ref by ID and check token)
            if self.system_config.security.require_auth:
                auth_token = params.get("auth_token")
                if not auth_token:
                    return self._error_response(
                        rpc_request.id,
                        code=-32000,
                        message="Missing auth token",
                        error_code=ErrorCode.AUTHENTICATION_FAILED,
                        status=401,
                        payload=params,
                    )
                if auth_token != referee.get("auth_token"):
                    return self._error_response(
                        rpc_request.id,
                        code=-32000,
                        message="Invalid auth token",
                        error_code=ErrorCode.AUTH_TOKEN_INVALID,
                        status=401,
                        payload=params,
                    )

            # Enqueue result for processing (M7.11)
            await self.standings_processor.enqueue(params)

            # Return success immediately
            return JSONResponse(
                status_code=200,
                content=JSONRPCResponse(
                    id=rpc_request.id,
                    result={
                        "message_type": "MATCH_RESULT_REPORT_ACK",
                        "conversation_id": params.get("conversation_id"),
                        "status": "ACCEPTED",
                        "message": "Result queued for processing",
                    },
                ).model_dump(),
            )

        except Exception as exc:
            return self._error_response(
                rpc_request.id,
                code=-32000,
                message="Server error",
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                status=500,
                payload=rpc_request.model_dump(),
                extra_data={"error": str(exc)},
            )

    async def _handle_league_query(self, rpc_request: JSONRPCRequest) -> JSONResponse:
        """Handle LEAGUE_QUERY requests (GET_STANDINGS only)."""
        try:
            params = rpc_request.params
            log_message_received(self.std_logger, params)

            try:
                query = LeagueQuery(**params)
            except Exception as exc:
                return self._error_response(
                    rpc_request.id,
                    code=-32602,
                    message="Invalid params",
                    error_code=ErrorCode.INVALID_MESSAGE_FORMAT,
                    status=400,
                    payload=rpc_request.model_dump(),
                    extra_data={"details": str(exc)},
                )

            sender = query.sender
            if sender not in self._allowed_query_senders():
                return self._error_response(
                    rpc_request.id,
                    code=-32602,
                    message="Sender not registered",
                    error_code=ErrorCode.AGENT_NOT_REGISTERED,
                    status=403,
                    payload=rpc_request.model_dump(),
                    extra_data={"sender": sender},
                )

            if self.system_config.security.require_auth:
                if not query.auth_token:
                    return self._error_response(
                        rpc_request.id,
                        code=-32000,
                        message="Missing auth token",
                        error_code=ErrorCode.AUTHENTICATION_FAILED,
                        status=401,
                        payload=rpc_request.model_dump(),
                    )
                if not self._auth_token_matches_sender(sender, query.auth_token):
                    return self._error_response(
                        rpc_request.id,
                        code=-32000,
                        message="Invalid auth token",
                        error_code=ErrorCode.AUTH_TOKEN_INVALID,
                        status=401,
                        payload=rpc_request.model_dump(),
                        extra_data={"sender": sender},
                    )

            if query.league_id != self.league_id:
                return self._error_response(
                    rpc_request.id,
                    code=-32000,
                    message="League not found",
                    error_code=ErrorCode.LEAGUE_NOT_FOUND,
                    status=404,
                    payload=rpc_request.model_dump(),
                    extra_data={"league_id": query.league_id},
                )

            if query.query_type != "GET_STANDINGS":
                return self._error_response(
                    rpc_request.id,
                    code=-32602,
                    message="Unsupported query type",
                    error_code=ErrorCode.INVALID_MESSAGE_FORMAT,
                    status=400,
                    payload=rpc_request.model_dump(),
                    extra_data={"query_type": query.query_type},
                )

            standings = self.standings_repo.load().get("standings", [])
            response = LeagueQueryResponse(
                sender=f"league_manager:{self.agent_id}",
                timestamp=self._timestamp(),
                conversation_id=query.conversation_id,
                query_type=query.query_type,
                success=True,
                data={"standings": standings},
            )
            rpc_response = JSONRPCResponse(id=rpc_request.id, result=response.model_dump())
            log_message_sent(self.std_logger, response.model_dump())
            return JSONResponse(status_code=200, content=rpc_response.model_dump())

        except Exception as exc:
            return self._error_response(
                rpc_request.id,
                code=-32000,
                message="Server error",
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                status=500,
                payload=rpc_request.model_dump(),
                extra_data={"error": str(exc)},
            )

    async def _handle_get_standings(self, rpc_request: JSONRPCRequest) -> JSONResponse:
        """Handle debug get_standings tool."""
        try:
            params = rpc_request.params
            log_message_received(self.std_logger, params)

            allow_unauth = getattr(
                self.system_config.security, "allow_start_league_without_auth", False
            )
            if not allow_unauth or params.get("sender"):
                validation_error = self._validate_debug_tool_request(rpc_request)
                if validation_error:
                    return validation_error

            standings = self.standings_repo.load().get("standings", [])
            rpc_response = JSONRPCResponse(
                id=rpc_request.id,
                result={
                    "message_type": "get_standings",
                    "conversation_id": params.get("conversation_id"),
                    "standings": standings,
                },
            )
            log_message_sent(self.std_logger, rpc_response.result)
            return JSONResponse(status_code=200, content=rpc_response.model_dump())
        except Exception as exc:
            return self._error_response(
                rpc_request.id,
                code=-32000,
                message="Server error",
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                status=500,
                payload=rpc_request.model_dump(),
                extra_data={"error": str(exc)},
            )

    async def _handle_get_league_status(self, rpc_request: JSONRPCRequest) -> JSONResponse:
        """Handle debug get_league_status tool."""
        try:
            params = rpc_request.params
            log_message_received(self.std_logger, params)

            allow_unauth = getattr(
                self.system_config.security, "allow_start_league_without_auth", False
            )
            if not allow_unauth or params.get("sender"):
                validation_error = self._validate_debug_tool_request(rpc_request)
                if validation_error:
                    return validation_error

            rpc_response = JSONRPCResponse(
                id=rpc_request.id,
                result={
                    "message_type": "get_league_status",
                    "conversation_id": params.get("conversation_id"),
                    "league_id": self.league_id,
                    "status": self.league_state,
                    "current_round_id": self.current_round_id,
                    "registered_players": list(self.registered_players.keys()),
                    "registered_referees": list(self.registered_referees.keys()),
                },
            )
            log_message_sent(self.std_logger, rpc_response.result)
            return JSONResponse(status_code=200, content=rpc_response.model_dump())
        except Exception as exc:
            return self._error_response(
                rpc_request.id,
                code=-32000,
                message="Server error",
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                status=500,
                payload=rpc_request.model_dump(),
                extra_data={"error": str(exc)},
            )

    async def _handle_start_league(self, rpc_request: JSONRPCRequest) -> JSONResponse:
        """Handle start_league tool to trigger league orchestration."""
        try:
            params = rpc_request.params
            log_message_received(self.std_logger, params)

            league_id = params.get("league_id")
            if league_id and league_id != self.league_id:
                return self._error_response(
                    rpc_request.id,
                    code=-32000,
                    message="League not found",
                    error_code=ErrorCode.LEAGUE_NOT_FOUND,
                    status=404,
                    payload=rpc_request.model_dump(),
                    extra_data={"league_id": league_id},
                )

            # Allow starting league without auth if configured
            allow_unauth = getattr(
                self.system_config.security, "allow_start_league_without_auth", False
            )
            if not allow_unauth or params.get("sender"):
                validation_error = self._validate_debug_tool_request(rpc_request)
                if validation_error:
                    return validation_error

            schedule_info = await self.start_league()
            result = {
                "message_type": "start_league",
                "conversation_id": params.get("conversation_id"),
                **schedule_info,
            }
            rpc_response = JSONRPCResponse(id=rpc_request.id, result=result)
            log_message_sent(self.std_logger, rpc_response.result)
            return JSONResponse(status_code=200, content=rpc_response.model_dump())
        except ValueError as exc:
            return self._error_response(
                rpc_request.id,
                code=-32000,
                message=str(exc),
                error_code=ErrorCode.INVALID_GAME_STATE,
                status=400,
                payload=rpc_request.model_dump(),
                extra_data={"error": str(exc)},
            )
        except Exception as exc:
            return self._error_response(
                rpc_request.id,
                code=-32000,
                message="Server error",
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                status=500,
                payload=rpc_request.model_dump(),
                extra_data={"error": str(exc)},
            )

    def _match_exists_in_schedule(self, match_id: str, round_id: int) -> bool:
        """
        Validate that match_id exists in the league schedule.

        Args:
            match_id: Match identifier to validate
            round_id: Round number where match should exist

        Returns:
            True if match exists, False otherwise
        """
        try:
            round_data = self.rounds_repo.get_round(round_id)
            if not round_data:
                return False

            matches = round_data.get("matches", [])
            for match in matches:
                if match.get("match_id") == match_id:
                    return True

            return False
        except Exception:
            # If we can't validate, assume match doesn't exist (fail-safe)
            return False

    async def _process_match_result(self, report_data: Dict[str, Any]) -> None:
        """
        Process match result sequentially (M7.11).

        Thread Safety:
        - Called by SequentialQueueProcessor
        - Only one execution at a time
        - Safe to update shared StandingsRepository
        """
        try:
            # Parse report
            report = MatchResultReport(**report_data)
            match_id = report.match_id
            round_id = report.round_id

            # E007 MATCH_NOT_FOUND - Validate match exists in schedule
            if not self._match_exists_in_schedule(match_id, round_id):
                log_error(
                    self.std_logger,
                    ErrorCode.MATCH_NOT_FOUND,
                    {
                        "match_id": match_id,
                        "round_id": round_id,
                        "referee_id": report.sender,
                        "reason": "Match ID not found in league schedule",
                    },
                )
                # Don't process invalid match results
                return

            result = report.result
            player_ids = self.update_standings(result)

            self.std_logger.info(
                f"Standings updated for match {report.match_id}",
                extra={
                    "event_type": "STANDINGS_UPDATE",
                    "match_id": report.match_id,
                    "winner": result.get("winner"),
                    "players": player_ids,
                },
            )

            # Broadcast new standings
            await self._broadcast_standings_update(report.round_id)

            # Check round completion
            await self._update_round_and_check_completion(report.round_id, report.match_id)

        except Exception as exc:
            self.std_logger.error(f"Error processing match result: {exc}", exc_info=True)

    async def _update_round_and_check_completion(self, round_id: int, match_id: str) -> None:
        """
        Update match status in round and check for completion.

        Thread Safety:
        - Sequential execution via queue processor
        """
        try:
            round_data = self.rounds_repo.get_round(round_id)
            if not round_data:
                return

            matches = round_data.get("matches", [])
            all_complete = True
            updated = False

            # Update status for the specific match
            for match in matches:
                if match.get("match_id") == match_id:
                    if match.get("status") != "COMPLETED":
                        match["status"] = "COMPLETED"
                        updated = True

                if match.get("status") != "COMPLETED":
                    all_complete = False

            # Persist updates to round file
            if updated:
                self.rounds_repo.add_round(round_id, matches)  # Overwrites existing round data

            # If round completed, update status and broadcast
            if all_complete and round_data.get("status") != "COMPLETED":
                self.rounds_repo.update_round_status(round_id, "COMPLETED")
                self.std_logger.info(f"Round {round_id} completed")

                rounds_data = self.rounds_repo.load().get("rounds", [])
                next_round_id = self._next_round_id(round_id, rounds_data)
                summary = self._round_summary(matches)

                # Broadcast ROUND_COMPLETED
                await self._broadcast_round_completed(round_id, len(matches), next_round_id, summary)

                # Trigger next round if available, otherwise finalize league
                if next_round_id:
                    await self.manage_round(next_round_id)
                else:
                    await self.detect_league_completion()

        except Exception as exc:
            self.std_logger.error(f"Error updating round status: {exc}", exc_info=True)

    async def _broadcast_round_completed(
        self,
        round_id: int,
        matches_completed: int,
        next_round_id: Optional[int],
        summary: Dict[str, Any],
    ) -> None:
        """Broadcast ROUND_COMPLETED message."""
        try:
            message = RoundCompleted(
                sender=f"league_manager:{self.agent_id}",
                timestamp=self._timestamp(),
                conversation_id=f"round-{round_id}-comp",
                league_id=self.league_id,
                round_id=round_id,
                matches_completed=matches_completed,
                next_round_id=next_round_id,
                summary=summary,
            )
            await self._broadcast_to_players(message.model_dump(), "ROUND_COMPLETED")
        except Exception as exc:
            self.std_logger.error(f"Failed to broadcast round completion: {exc}", exc_info=True)

    async def _broadcast_standings_update(self, round_id: int) -> None:
        """Broadcast updated standings to all registered players."""
        try:
            standings_data = self.standings_repo.load()
            update = LeagueStandingsUpdate(
                sender=f"league_manager:{self.agent_id}",
                timestamp=self._timestamp(),
                conversation_id=f"standings-{self._timestamp()}",
                league_id=self.league_id,
                round_id=round_id,
                standings=standings_data.get("standings", []),
            )
            await self._broadcast_to_players(update.model_dump(), "LEAGUE_STANDINGS_UPDATE")
        except Exception as exc:
            self.std_logger.error(f"Broadcast standings failed: {exc}", exc_info=True)

    async def _broadcast_to_players(self, payload: Dict[str, Any], message_type: str) -> None:
        """
        Helper to broadcast message to all registered players.

        Uses endpoints from agents_config for reliability.
        Logs per-recipient failures with E006 PLAYER_NOT_AVAILABLE.
        """
        tasks = []
        task_player_map = []  # Track which task belongs to which player

        # Use agents_config as source of truth for endpoints
        known_players = {p["agent_id"]: p["endpoint"] for p in self.agents_config.get("players", [])}

        # Broadcast to all registered players (from memory or config)
        # Using registered_players keys ensures we only send to those who actually registered
        target_ids = list(self.registered_players.keys())

        for player_id in target_ids:
            endpoint = known_players.get(player_id)
            if not endpoint:
                # Try to get from registration data if dynamic
                endpoint = self.registered_players[player_id].get("contact_endpoint")

            if endpoint:
                player_token = self.registered_players.get(player_id, {}).get("auth_token")
                per_recipient_payload = dict(payload)
                if player_token:
                    per_recipient_payload["auth_token"] = player_token
                log_message_sent(self.std_logger, per_recipient_payload)
                task = call_with_retry(
                    endpoint=endpoint,
                    method=message_type,
                    params=per_recipient_payload,
                    timeout=self.system_config.network.request_timeout_sec,
                    logger=self.std_logger,
                )
                tasks.append(task)
                task_player_map.append((player_id, endpoint))
            else:
                self.std_logger.warning(f"No endpoint found for player {player_id}, skipping broadcast")

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log per-recipient failures
            success_count = 0
            for (player_id, endpoint), result in zip(task_player_map, results):
                if isinstance(result, Exception):
                    log_error(
                        self.std_logger,
                        ErrorCode.PLAYER_NOT_AVAILABLE,
                        {
                            "player_id": player_id,
                            "endpoint": endpoint,
                            "message_type": message_type,
                            "error": str(result),
                            "reason": "Failed to broadcast message to player",
                        },
                    )
                else:
                    success_count += 1

            self.std_logger.info(
                f"Broadcasted {message_type} to {success_count}/{len(tasks)} players successfully"
            )

    def update_standings(self, result: Dict[str, Any]) -> List[str]:
        """
        Update standings after a match result (M7.11).

        Args:
            result: Result dict with winner and score payload

        Returns:
            List of player IDs updated
        """
        winner_id = result.get("winner")

        scoring = self.league_config.scoring
        win_points = self._get_config_with_warning(
            scoring, "points_for_win", 3, "league config scoring"
        )
        draw_points = self._get_config_with_warning(
            scoring, "points_for_draw", 1, "league config scoring"
        )
        loss_points = self._get_config_with_warning(
            scoring, "points_for_loss", 0, "league config scoring"
        )

        scores = result.get("score", {})
        player_ids = list(scores.keys())

        for player_id in player_ids:
            outcome = "LOSS"
            points = loss_points

            if winner_id == "DRAW":
                outcome = "DRAW"
                points = draw_points
            elif winner_id == player_id:
                outcome = "WIN"
                points = win_points

            self.standings_repo.update_player(
                player_id=player_id,
                result=outcome,
                points=points,
            )

        return player_ids

    async def start_league(self) -> Dict[str, Any]:
        """
        Trigger league start after sufficient registrations (M7.13).

        Uses protocol error codes:
        - E004 AGENT_NOT_REGISTERED: Insufficient players/referees
        """
        min_players = getattr(self.league_config.participants, "min_players", 2)

        # Use E004 AGENT_NOT_REGISTERED per protocol for insufficient agents
        if len(self.registered_players) < min_players:
            error_msg = (
                f"At least {min_players} players required to start league "
                f"(currently: {len(self.registered_players)})"
            )
            log_error(
                self.std_logger,
                ErrorCode.AGENT_NOT_REGISTERED,
                {
                    "message": error_msg,
                    "min_players": min_players,
                    "registered_players": len(self.registered_players),
                    "player_ids": list(self.registered_players.keys()),
                },
            )
            raise ValueError(error_msg)

        if len(self.registered_referees) == 0:
            error_msg = "At least 1 referee required to start league"
            log_error(
                self.std_logger,
                ErrorCode.AGENT_NOT_REGISTERED,
                {"message": error_msg, "min_referees": 1, "registered_referees": 0},
            )
            raise ValueError(error_msg)

        self.std_logger.info(
            "Starting league",
            extra={
                "league_id": self.league_id,
                "players_count": len(self.registered_players),
                "referees_count": len(self.registered_referees),
                "min_players_required": min_players,
            },
        )

        schedule_info = self.create_schedule()
        previous_state = self.league_state
        self.league_state = "ACTIVE"
        self._log_league_state_change("start_league", previous_state, self.league_state)
        self.current_round_id = 1

        await self.manage_round(1)

        self.std_logger.info(
            "League started successfully",
            extra={
                "league_id": self.league_id,
                "total_rounds": schedule_info.get("total_rounds"),
                "current_round": self.current_round_id,
            },
        )

        return schedule_info

    async def broadcast_round_announcement(self, round_id: int) -> None:
        """
        Broadcast ROUND_ANNOUNCEMENT to all players.

        Uses protocol error codes:
        - E009 ROUND_NOT_ACTIVE: Round not found or inactive
        """
        round_data = self.rounds_repo.get_round(round_id)
        if not round_data:
            error_msg = f"Round {round_id} not found"
            log_error(
                self.std_logger,
                ErrorCode.ROUND_NOT_ACTIVE,
                {"message": error_msg, "round_id": round_id, "league_id": self.league_id},
            )
            raise ValueError(error_msg)

        matches_payload = []
        for match in round_data.get("matches", []):
            referee_id = match.get("referee_id")
            referee_endpoint = self._referee_endpoint(referee_id)
            matches_payload.append(
                {
                    "match_id": match.get("match_id"),
                    "game_type": match.get("game_type"),
                    "player_A_id": match.get("player_a_id"),
                    "player_B_id": match.get("player_b_id"),
                    "referee_endpoint": referee_endpoint,
                }
            )

        announcement = RoundAnnouncement(
            sender=f"league_manager:{self.agent_id}",
            timestamp=self._timestamp(),
            conversation_id=f"round-{round_id}-announce",
            league_id=self.league_id,
            round_id=round_id,
            matches=matches_payload,
        )
        await self._broadcast_to_players(announcement.model_dump(), "ROUND_ANNOUNCEMENT")

    async def manage_round(self, round_id: int) -> None:
        """Manage round lifecycle: announce and start matches."""
        round_data = self.rounds_repo.get_round(round_id)
        if not round_data:
            raise ValueError(f"Round {round_id} not found")

        self.current_round_id = round_id
        self.rounds_repo.update_round_status(round_id, "IN_PROGRESS")

        await self.broadcast_round_announcement(round_id)

        tasks = []
        for match in round_data.get("matches", []):
            referee_id = match.get("referee_id")
            endpoint = self._referee_endpoint(referee_id)
            if not endpoint:
                self.std_logger.warning(
                    f"No referee endpoint for {referee_id}, skipping match {match.get('match_id')}"
                )
                continue
            auth_token = None
            if referee_id:
                auth_token = self.registered_referees.get(referee_id, {}).get("auth_token")
            params = {
                "sender": f"league_manager:{self.agent_id}",
                "protocol": self.system_config.protocol_version,
                "message_type": "START_MATCH",
                "match_id": match.get("match_id"),
                "round_id": round_id,
                "player_a_id": match.get("player_a_id"),
                "player_b_id": match.get("player_b_id"),
                "conversation_id": self._conversation_id(),
            }
            if auth_token:
                params["auth_token"] = auth_token
            log_message_sent(
                self.std_logger,
                {
                    "message_type": "START_MATCH",
                    "conversation_id": params.get("conversation_id"),
                    "sender": params.get("sender"),
                },
            )
            tasks.append(
                call_with_retry(
                    endpoint=endpoint,
                    method="START_MATCH",
                    params=params,
                    timeout=self.system_config.timeouts.generic_sec,
                    logger=self.std_logger,
                )
            )

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def detect_league_completion(self) -> None:
        """Check for league completion and broadcast LEAGUE_COMPLETED."""
        rounds = self.rounds_repo.load().get("rounds", [])
        if not rounds:
            return
        if any(r.get("status") != "COMPLETED" for r in rounds):
            return

        total_rounds = len(rounds)
        total_matches = sum(len(r.get("matches", [])) for r in rounds)
        champion, final_standings = self.identify_champion()

        await self.broadcast_league_completed(total_rounds, total_matches, champion, final_standings)

        previous_state = self.league_state
        self.league_state = "COMPLETED"
        self._log_league_state_change("league_completed", previous_state, self.league_state)
        # Run specialized cleanup to archive completed league data immediately
        await self._on_league_completed_cleanup()

    def identify_champion(self) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Identify champion and build final standings with ranks."""
        standings = self.standings_repo.load().get("standings", [])
        final_standings = []
        for idx, entry in enumerate(standings, start=1):
            final_entry = dict(entry)
            final_entry["rank"] = idx
            final_standings.append(final_entry)

        champion = final_standings[0] if final_standings else {}
        return champion, final_standings

    async def broadcast_league_completed(
        self,
        total_rounds: int,
        total_matches: int,
        champion: Dict[str, Any],
        final_standings: List[Dict[str, Any]],
    ) -> None:
        """Broadcast LEAGUE_COMPLETED to all players."""
        message = LeagueCompleted(
            sender=f"league_manager:{self.agent_id}",
            timestamp=self._timestamp(),
            conversation_id="league-complete",
            league_id=self.league_id,
            total_rounds=total_rounds,
            total_matches=total_matches,
            champion={
                "player_id": champion.get("player_id"),
                "display_name": champion.get("display_name", champion.get("player_id")),
                "points": champion.get("points", 0),
            },
            final_standings=final_standings,
        )
        await self._broadcast_to_players(message.model_dump(), "LEAGUE_COMPLETED")

    def _referee_endpoint(self, referee_id: Optional[str]) -> Optional[str]:
        if not referee_id:
            return None
        ref = self.registered_referees.get(referee_id, {})
        if ref.get("contact_endpoint"):
            return ref.get("contact_endpoint")
        for ref_cfg in self.agents_config.get("referees", []):
            if ref_cfg.get("agent_id") == referee_id:
                return ref_cfg.get("endpoint")
        return None

    def _next_round_id(self, current_round_id: int, rounds: List[Dict[str, Any]]) -> Optional[int]:
        # Filter out None values and ensure type safety
        round_ids: List[int] = []
        for r in rounds:
            rid = r.get("round_id")
            if rid is not None and isinstance(rid, int):
                round_ids.append(rid)
        ids = sorted(round_ids)
        for rid in ids:
            if rid > current_round_id:
                return rid
        return None

    def _round_summary(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Basic round summary placeholder."""
        return {
            "total_matches": len(matches),
            "wins": 0,
            "draws": 0,
            "technical_losses": 0,
        }
