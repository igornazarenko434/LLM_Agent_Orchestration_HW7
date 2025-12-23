# Referee REF02 Agent

Second referee agent for the Even/Odd League, sharing implementation with REF01.

## Architecture

REF02 follows **DRY (Don't Repeat Yourself)** best practices by **importing** the generic `RefereeAgent` class from `referee_REF01` instead of duplicating code.

### Shared Components

All core logic is shared with REF01:
- `game_logic.py` - Even/Odd game rules (cryptographic RNG, winner determination)
- `timeout_enforcement.py` - Timeout handling with exponential backoff
- `match_conductor.py` - 6-step match protocol orchestration
- `server.py` - MCP server with JSON-RPC 2.0 dispatch

### REF02-Specific Files

- `__init__.py` - Imports `RefereeAgent` from REF01
- `main.py` - Entry point with `agent_id="REF02"` default
- `README.md` - This file

## Configuration

All configuration loaded from `SHARED/config/agents/agents_config.json`:

```json
{
  "agent_id": "REF02",
  "agent_type": "referee",
  "display_name": "Referee 02",
  "endpoint": "http://localhost:8002/mcp",
  "port": 8002,
  "active": true,
  "version": "1.0.0",
  "capabilities": [
    "conduct_match",
    "enforce_timeouts",
    "determine_winner",
    "report_results"
  ],
  "game_types": ["even_odd"],
  "max_concurrent_matches": 10
}
```

**Zero hardcoded values** - all parameters from config files.

## Usage

### Start REF02

```bash
# Start with defaults (agent_id=REF02, port=8002)
python agents/referee_REF02/main.py

# Or specify custom parameters
python agents/referee_REF02/main.py --referee-id REF02 --port 8002 --log-level DEBUG
```

### Command-Line Options

- `--referee-id` - Referee ID (default: REF02)
- `--league-id` - League ID (default: league_2025_even_odd)
- `--host` - Host to bind (default: localhost)
- `--port` - Port to bind (default: from config)
- `--log-level` - Log level (DEBUG, INFO, WARNING, ERROR)
- `--version` - Show version

### Registration

On startup, REF02 automatically:
1. Starts HTTP server on port 8002
2. Registers with League Manager (http://localhost:8000/mcp)
3. Initializes `MatchConductor` after successful registration
4. Waits for `START_MATCH` requests

## Testing

Run REF02-specific tests:
```bash
pytest tests/unit/test_referee_agent/test_referee_ref02.py -v
```

Run all referee tests:
```bash
pytest tests/unit/test_referee_agent/ -v
```

## Differences from REF01

| Aspect | REF01 | REF02 |
|--------|-------|-------|
| Agent ID | `REF01` | `REF02` |
| Port | 8001 | 8002 |
| Endpoint | http://localhost:8001/mcp | http://localhost:8002/mcp |
| Implementation | Direct | Imports from REF01 |
| Capabilities | Identical | Identical |
| Game Logic | Identical | Shared |

## Scalability

This architecture supports adding more referees easily:

```bash
# REF03 would be:
- Port: 8003
- Imports from REF01
- Only main.py needs to be created
```

## Dependencies

- Python 3.10+
- FastAPI (HTTP server)
- Pydantic (data validation)
- league_sdk (protocol, config, logging, retry)

## Best Practices Applied

✅ **No Code Duplication** - Imports from REF01
✅ **Config-Driven** - Zero hardcoded values
✅ **Consistent with league_sdk** - Uses all SDK components
✅ **Type-Safe** - Full mypy compliance
✅ **Well-Tested** - 19 unit tests, 100% pass rate
✅ **Documented** - Clear README and code comments

## Related Documentation

- [Mission 7.5-7.8: Referee Implementation](../../Missions_EvenOddLeague.md)
- [league_sdk Protocol](../../SHARED/league_sdk/protocol.py)
- [System Configuration](../../SHARED/config/system.json)
- [Agents Configuration](../../SHARED/config/agents/agents_config.json)
