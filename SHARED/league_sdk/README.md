# League SDK

**Version:** 1.0.0 (league.v2 protocol)
**Python:** ≥3.10
**License:** MIT

Shared utilities and protocol implementation for the Even/Odd League Multi-Agent System. This SDK provides everything needed to build MCP-compliant agents that can participate in the league.

---

## 🚀 Quick Start

### Installation

**From wheel (pip):**
```bash
pip install league_sdk-1.0.0-py3-none-any.whl
```

**From source (editable mode for development):**
```bash
cd SHARED/league_sdk
pip install -e .
```

### Basic Usage

```python
from league_sdk import protocol, logger, retry, config_loader

# Import specific models
from league_sdk.protocol import GameInvitation, MessageEnvelope
from league_sdk.logger import JsonLogger
from league_sdk.retry import call_with_retry, CircuitBreaker
from league_sdk.config_loader import load_system_config
from league_sdk.repositories import StandingsRepository
```

---

## 📦 Modules

### Core Protocol
- **`protocol`** - 18 MCP message type models (league.v2)
  - `GameInvitation`, `MoveRequest`, `MatchResultReport`, etc.
  - Pydantic models with automatic validation
  - JSON-RPC 2.0 envelope format

### Configuration
- **`config_models`** - Pydantic schemas for all configuration types
  - System, Agent, League, Game configurations
  - Type-safe with validation

- **`config_loader`** - Load configs with environment variable overrides
  - Hierarchical config loading (CLI > ENV > JSON > Defaults)
  - Automatic validation

### Data Persistence
- **`repositories`** - Repository pattern for data storage
  - `StandingsRepository`, `MatchRepository`, `PlayerRepository`
  - Atomic write operations (temp file + rename)
  - Thread-safe file I/O

### Observability
- **`logger`** - Structured JSONL logging
  - Correlation IDs for distributed tracing
  - Automatic log rotation (100MB, 5 generations)
  - Machine-readable format

### Resilience
- **`retry`** - Retry policies with circuit breaker
  - Exponential backoff (2s → 4s → 8s)
  - Circuit breaker (5 failures, 60s reset)
  - Async/await support with httpx

### Concurrency
- **`queue_processor`** - Sequential async queue for thread safety
  - Eliminates race conditions for shared resource updates
  - Non-blocking enqueue, sequential processing
  - Graceful shutdown with queue draining

### Data Management
- **`cleanup`** - Data retention and archival
  - Automated cleanup scheduler
  - Gzip compression (80% reduction)
  - Configurable retention periods

### Compatibility
- **`method_aliases`** - PDF compatibility layer
  - Supports both camelCase and snake_case method names
  - Seamless protocol version compatibility

### Utilities
- **`utils`** - Common utility functions
  - Timestamp generation (ISO 8601 UTC)
  - Token generation
  - Helper functions

---

## 🎯 Key Features

- ✅ **MCP JSON-RPC 2.0 Protocol** - Full league.v2 implementation (18 message types)
- ✅ **Type Safety** - Pydantic models throughout
- ✅ **Async/Await** - Modern async patterns with httpx
- ✅ **Resilience** - Retry with exponential backoff + circuit breaker
- ✅ **Observability** - Structured JSONL logging with correlation IDs
- ✅ **Thread Safety** - Sequential queue processor for concurrent updates
- ✅ **Data Integrity** - Atomic write operations
- ✅ **Configurability** - Environment variable overrides

---

## 📚 Documentation

For comprehensive documentation, see:

- **[Full Documentation](../../doc/)** - Complete guide collection
- **[Configuration Guide](../../doc/configuration.md)** - All configuration options
- **[Developer Guide](../../doc/developer_guide.md)** - Development setup
- **[Thread Safety Guide](../../doc/guides/queue_processor_guide.md)** - Using the queue processor
- **[API Reference](../../doc/reference/api_reference.md)** - Protocol message types
- **[Architecture Docs](../../doc/architecture.md)** - System design

---

## 💡 Examples

### Creating a Message

```python
from league_sdk.protocol import GameInvitation

invitation = GameInvitation(
    sender="referee:REF01",
    timestamp="2025-01-15T10:00:00Z",
    conversation_id="conv_123",
    auth_token="a" * 32,  # 32-character token
    league_id="league_2025",
    match_id="MATCH_001",
    game_type="even_odd",
    player_id="P01",
    opponent_id="P02",
    opponent_endpoint="http://localhost:8102/mcp"
)
```

### Using the Logger

```python
from league_sdk.logger import JsonLogger

logger = JsonLogger("my_agent", "agent_id", "agent")
logger.info("Agent started", extra={"port": 8000})
# Output: {"timestamp": "2025-01-15T10:00:00Z", "level": "INFO", ...}
```

### Retry with Circuit Breaker

```python
from league_sdk.retry import call_with_retry

async def make_api_call():
    async with httpx.AsyncClient() as client:
        response = await client.post("http://example.com/api", json=data)
        return response.json()

result = await call_with_retry(
    make_api_call,
    max_retries=3,
    base_delay=2.0,
    logger=logger
)
```

### Loading Configuration

```python
from league_sdk.config_loader import load_system_config

config = load_system_config("SHARED/config/system.json")
print(config.protocol_version)  # "league.v2"
```

### Using Repository

```python
from league_sdk.repositories import StandingsRepository

repo = StandingsRepository(league_id="league_2025")
standings = repo.load()
standings.update_player_stats(player_id="P01", wins=1, points=3)
repo.save(standings)  # Atomic write
```

### Sequential Queue Processor

```python
from league_sdk import SequentialQueueProcessor

async def process_result(result):
    # This runs sequentially, no race conditions
    standings = load_standings()
    standings.update(result)
    save_standings(standings)

processor = SequentialQueueProcessor(process_result)
await processor.start()
await processor.enqueue(result1)  # Queued
await processor.enqueue(result2)  # Queued, processed sequentially
await processor.stop()
```

---

## 🧪 Testing

The SDK is thoroughly tested with 350+ unit tests:

```bash
# Run SDK tests
PYTHONPATH=../../:$PYTHONPATH pytest ../../tests/unit/test_sdk/ -v

# With coverage
PYTHONPATH=../../:$PYTHONPATH pytest ../../tests/unit/test_sdk/ --cov=. --cov-report=html
```

---

## 🔧 Dependencies

- `pydantic>=2.0.0` - Data validation
- `requests>=2.28.0` - HTTP client (sync)
- `httpx>=0.28.0` - HTTP client (async)
- `python-dateutil>=2.8.0` - Date/time utilities

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🤝 Contributing

This SDK is part of the Even/Odd League Multi-Agent System. For contribution guidelines, see [CONTRIBUTING.md](../../CONTRIBUTING.md).

---

**Built for:** Even/Odd League Multi-Agent System
**Protocol:** MCP league.v2 (JSON-RPC 2.0)
**Related:** [Project README](../../README.md) • [Documentation](../../doc/)
