# ADR-0001: Use FastAPI + JSON-RPC over HTTP

Status: Accepted
Date: 2025-12-27

## Context
Agents must expose MCP endpoints and exchange structured messages reliably. Options
included raw HTTP handlers, WebSockets, and gRPC.

## Decision
Use FastAPI servers with JSON-RPC 2.0 over HTTP for all agents.

## Alternatives
- WebSockets: persistent connections, higher complexity.
- gRPC: protobuf tooling overhead, not required for scope.

## Consequences
- Simple request/response model, easy to test with curl.
- Stateless interactions simplify agent lifecycle.
- Slightly higher latency than persistent sockets, acceptable for scale.
