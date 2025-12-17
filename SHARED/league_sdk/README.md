# League SDK

Shared utilities for Even/Odd League Multi-Agent System.

## Installation

```bash
pip install -e .
```

## Modules

- `protocol`: Message models and validation
- `config_loader`: Configuration file loading
- `config_models`: Configuration data models
- `repositories`: Data persistence layer
- `logger`: Structured JSON logging
- `retry`: Retry policies with exponential backoff
- `utils`: Utility functions

## Usage

```python
from league_sdk import protocol, config_loader, repositories, logger, retry, utils
```

## Version

1.0.0 (league.v2 protocol)
