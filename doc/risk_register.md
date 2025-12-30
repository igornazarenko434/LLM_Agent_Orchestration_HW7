# Risk Register
**Version:** 1.0.0
**Last Updated:** 2025-01-15
**Status:** Active Risk Tracking
**Source:** [PRD Section 13](../PRD_EvenOddLeague.md#13-risks--mitigation)

This document tracks all identified project risks, their mitigation strategies, and current status.

---

## 📊 Risk Summary Dashboard

### Overall Risk Profile

- **Total Risks:** 12
- **Critical (🔴):** 2
- **High (🟠):** 3
- **Medium (🟡):** 5
- **Low (🟢):** 2

### Risk Status Distribution

- **✅ Mitigated:** 8 (67%)
- **⏳ Active Monitoring:** 3 (25%)
- **✔️ Accepted:** 1 (8%)

### Overall Risk Level

**🟢 LOW** - All high/critical risks have documented mitigations and are actively managed.

---

## 🎯 Risk Matrix

### Severity Calculation

**Severity = Likelihood × Impact**

| Likelihood | Impact Low | Impact Medium | Impact High | Impact Critical |
|------------|-----------|---------------|-------------|----------------|
| **High** | 🟡 Medium | 🟠 High | 🔴 Critical | 🔴 Critical |
| **Medium** | 🟢 Low | 🟡 Medium | 🟠 High | 🔴 Critical |
| **Low** | 🟢 Low | 🟡 Medium | 🟠 High | 🔴 Critical |

---

## 📋 Active Risk Register

### R01: Player Timeout During Match
**Category:** Operational
**Likelihood:** High
**Impact:** Medium
**Severity:** 🟡 Medium
**Owner:** Referee Agent
**Status:** ✅ Mitigated

**Description:**
Player fails to respond within timeout window (5s for join, 30s for parity choice) due to network latency, processing delays, or agent failure.

**Mitigation Strategy:**
1. Implement retry policy with exponential backoff (2s → 4s → 8s)
2. Award technical loss after 3 retry attempts
3. Clear timeout configuration in system.json
4. Timeout enforcement implemented in referee agent

**Contingency Plan:**
- Referee reports timeout to League Manager
- Technical win awarded to opponent
- League continues with updated standings
- Detailed timeout logged for debugging

**Verification:**
```bash
# Test timeout enforcement
pytest tests/integration/test_timeout_enforcement.py -v

# Check timeout configuration
cat SHARED/config/system.json | jq '.timeouts'
```

**Evidence:**
- Implementation: [agents/referee_REF01/timeout_enforcement.py](../agents/referee_REF01/timeout_enforcement.py)
- Tests: [tests/integration/test_timeout_enforcement.py](../tests/integration/test_timeout_enforcement.py)
- Config: [SHARED/config/system.json](../SHARED/config/system.json)

---

### R02: Network Partition
**Category:** Infrastructure
**Likelihood:** Medium
**Impact:** High
**Severity:** 🟠 High
**Owner:** System Architecture
**Status:** ⏳ Active Monitoring

**Description:**
Network connectivity lost between agents due to network failures, routing issues, or infrastructure problems. Agents cannot communicate via HTTP.

**Mitigation Strategy:**
1. Retry logic with exponential backoff
2. Health check endpoints on all agents (/health)
3. Graceful degradation (agents log errors, don't crash)
4. Circuit breaker pattern to fail fast when service unavailable

**Contingency Plan:**
- Manual restart of affected agents
- League pauses until connectivity restored
- State persisted to disk (can resume from last checkpoint)
- Operators notified via log monitoring

**Verification:**
```bash
# Test health checks
curl -X GET http://localhost:8000/health  # League Manager
curl -X GET http://localhost:8001/health  # Referee
curl -X GET http://localhost:9001/health  # Player

# Test retry mechanism
pytest tests/unit/test_sdk/test_retry.py -v

# Test circuit breaker
pytest tests/unit/test_sdk/test_circuit_breaker.py -v
```

**Evidence:**
- Health checks: [agents/base/agent_base.py](../agents/base/agent_base.py) (line 100)
- Retry logic: [SHARED/league_sdk/retry.py](../SHARED/league_sdk/retry.py)
- Circuit breaker: [SHARED/league_sdk/retry.py](../SHARED/league_sdk/retry.py) (line 155)

---

### R03: File Corruption (Standings/Matches)
**Category:** Data Integrity
**Likelihood:** Low
**Impact:** High
**Severity:** 🟠 High
**Owner:** SDK (Repository Layer)
**Status:** ✅ Mitigated

**Description:**
Data files (standings.json, matches/*.json) become corrupted due to partial writes, concurrent access, or system crashes during write operations.

**Mitigation Strategy:**
1. Atomic writes using temp file + rename pattern (POSIX guarantee)
2. Regular backups (planned: automated archival)
3. JSON schema validation on read
4. Write-ahead logging for critical operations

**Contingency Plan:**
- Restore from latest backup
- Recalculate standings from match history
- Match transcripts provide audit trail
- Manual data recovery if needed

**Verification:**
```bash
# Test atomic write pattern
pytest tests/unit/test_sdk/test_repositories.py -v

# Verify atomic_write implementation
grep -A 20 "def atomic_write" SHARED/league_sdk/repositories.py

# Check data consistency
pytest tests/integration/test_standings_update.py -v
```

**Evidence:**
- Atomic writes: [SHARED/league_sdk/repositories.py](../SHARED/league_sdk/repositories.py) (line 38)
- Tests: [tests/unit/test_sdk/test_repositories.py](../tests/unit/test_sdk/test_repositories.py)
- Documentation: [doc/architecture/thread_safety.md](architecture/thread_safety.md) (Section 3.1)

---

### R04: Memory Leak in Long-Running Agent
**Category:** Performance
**Likelihood:** Medium
**Impact:** Medium
**Severity:** 🟡 Medium
**Owner:** Agent Developers
**Status:** ⏳ Active Monitoring

**Description:**
Agent processes accumulate memory over time due to unclosed resources, circular references, or retained object references, leading to degraded performance or crashes.

**Mitigation Strategy:**
1. Regular monitoring of agent memory usage
2. Automatic restart on memory threshold (planned)
3. Proper resource cleanup (context managers, finally blocks)
4. Periodic health checks

**Contingency Plan:**
- Graceful agent restart (preserve state to disk)
- In-progress matches reassigned to backup referee (planned)
- Memory profiling tools for diagnosis (memory_profiler)
- Process monitoring alerts

**Verification:**
```bash
# Monitor agent memory (requires agents running)
ps aux | grep "python.*agents" | awk '{print $6, $11}'

# Test resource cleanup
pytest tests/unit/ -v --cov=agents --cov-report=term

# Check for unclosed resources (planned)
# python -m pytest --find-leaked-resources
```

**Evidence:**
- Resource cleanup: Context managers in agent_base.py
- Graceful shutdown: [tests/e2e/test_graceful_shutdown.py](../tests/e2e/test_graceful_shutdown.py)
- Monitoring: Health endpoints on all agents

---

### R05: Concurrent Write Conflicts
**Category:** Concurrency
**Likelihood:** Medium
**Impact:** Low
**Severity:** 🟡 Medium
**Owner:** League Manager
**Status:** ✅ Mitigated

**Description:**
Multiple referees report match results simultaneously, leading to lost updates in standings.json due to read-modify-write race condition.

**Mitigation Strategy:**
1. Sequential queue processor for standings updates (SequentialQueueProcessor)
2. File versioning in standings.json (planned)
3. Last-writer-wins with log warning (current implementation)
4. Eventual consistency via recalculation from match history

**Contingency Plan:**
- Detect inconsistencies via standings validation
- Rebuild standings from match transcripts
- Log all concurrent writes for audit
- Future: Optimistic locking with version numbers

**Verification:**
```bash
# Test queue processor
pytest tests/unit/test_sdk/test_queue_processor.py -v

# Test concurrent updates
pytest tests/integration/test_concurrent_matches.py -v

# Check standings consistency
pytest tests/integration/test_standings_update.py -v
```

**Evidence:**
- Queue processor: [SHARED/league_sdk/queue_processor.py](../SHARED/league_sdk/queue_processor.py)
- Guide: [doc/guides/queue_processor_guide.md](guides/queue_processor_guide.md)
- Thread safety: [doc/architecture/thread_safety.md](architecture/thread_safety.md) (Section 4.1)

---

### R06: League Manager Crash
**Category:** Availability
**Likelihood:** Low
**Impact:** Critical
**Severity:** 🔴 Critical
**Owner:** System Architecture
**Status:** ✅ Mitigated

**Description:**
League Manager process crashes due to unhandled exceptions, resource exhaustion, or infrastructure failure. League cannot continue without central orchestrator.

**Mitigation Strategy:**
1. Health monitoring with automatic alerts
2. Automatic restart capability (systemd/supervisor)
3. State persistence to disk (registrations, standings, rounds)
4. Comprehensive error handling with logging

**Contingency Plan:**
- Restart League Manager from persisted state
- Resume from last completed round
- Re-register agents if needed (idempotent registration)
- Manual intervention for data recovery if state corrupted

**Verification:**
```bash
# Test graceful shutdown and restart
pytest tests/e2e/test_graceful_shutdown.py -v

# Verify state persistence
ls SHARED/data/leagues/*/standings.json
ls SHARED/data/leagues/*/rounds.json

# Test error handling
pytest tests/unit/test_league_manager/ -v
```

**Evidence:**
- State persistence: [agents/league_manager/server.py](../agents/league_manager/server.py)
- Graceful shutdown: [agents/base/agent_base.py](../agents/base/agent_base.py) (stop method)
- Error handling: Comprehensive try/except in all endpoints

---

### R07: Protocol Version Mismatch
**Category:** Compatibility
**Likelihood:** Low
**Impact:** High
**Severity:** 🟠 High
**Owner:** SDK & Protocol
**Status:** ✅ Mitigated

**Description:**
Agent uses incompatible protocol version, leading to message parsing failures, missing fields, or incorrect behavior.

**Mitigation Strategy:**
1. Strict version checking (protocol: "league.v2" required)
2. Reject incompatible messages with E011 (PROTOCOL_VERSION_MISMATCH)
3. Protocol version in all message envelopes
4. Pydantic validation enforces schema

**Contingency Plan:**
- Agent logs error and refuses to start
- Clear error message with expected vs. actual version
- Operator updates agent version
- Version documented in all code/configs

**Verification:**
```bash
# Test protocol version validation
pytest tests/protocol_compliance/test_protocol_version.py -v

# Check protocol version in messages
grep "league.v2" SHARED/league_sdk/protocol.py

# Verify error code E011
grep "E011" SHARED/league_sdk/protocol.py
grep "E011" doc/reference/error_codes_reference.md
```

**Evidence:**
- Protocol version: [SHARED/league_sdk/protocol.py](../SHARED/league_sdk/protocol.py) (MessageEnvelope)
- Error code: [doc/reference/error_codes_reference.md](reference/error_codes_reference.md) (E011)
- Validation tests: [tests/protocol_compliance/](../tests/protocol_compliance/)

---

### R08: Port Conflicts
**Category:** Configuration
**Likelihood:** Medium
**Impact:** High
**Severity:** 🟠 High
**Owner:** Deployment/Operations
**Status:** ✅ Mitigated

**Description:**
Agents cannot start because required ports (8000-8002, 8101-8104, 9001-9004) are already in use by other processes.

**Mitigation Strategy:**
1. Pre-flight port availability check in start scripts
2. Configurable port ranges in system.json
3. Clear error messages with port conflict details
4. Documentation of port assignments

**Contingency Plan:**
- Agents fail fast with actionable error message
- Operator identifies and resolves conflict
- Alternative: Configure different port ranges
- Scripts provide port status before start

**Verification:**
```bash
# Check port availability
netstat -an | grep -E "800[0-2]|810[1-4]|900[1-4]" || echo "Ports available"

# Verify port configuration
cat SHARED/config/system.json | jq '.agents[].port'

# Test start script port checking
./scripts/start_all_agents.sh --dry-run
```

**Evidence:**
- Port config: [SHARED/config/system.json](../SHARED/config/system.json)
- Start scripts: [scripts/start_all_agents.sh](../scripts/start_all_agents.sh)
- Error handling: Uvicorn startup exceptions caught and logged

---

### R09: Incomplete Match Transcript
**Category:** Data Quality
**Likelihood:** Medium
**Impact:** Low
**Severity:** 🟡 Medium
**Owner:** Referee Agent
**Status:** ✔️ Accepted

**Description:**
Match transcript missing events due to logging failures, exceptions during match, or referee crash mid-match.

**Mitigation Strategy:**
1. Transaction-like writes (append events atomically)
2. Consistency checks on match completion
3. Match status field (PENDING/IN_PROGRESS/COMPLETED/INCOMPLETE)
4. Detailed error logging

**Contingency Plan:**
- Mark match as INCOMPLETE in standings
- Manual review of partial transcript
- Re-run match if critical to league outcome
- Audit logs provide additional context

**Verification:**
```bash
# Check match transcripts
ls SHARED/data/matches/*.json | head -5

# Verify transcript structure
cat SHARED/data/matches/*.json | jq '.transcript | length' 2>/dev/null | head -1

# Test match completion
pytest tests/integration/test_match_flow.py -v
```

**Evidence:**
- Match repository: [SHARED/league_sdk/repositories.py](../SHARED/league_sdk/repositories.py)
- Transcript logging: Referee agent match conductor
- Risk acceptance: Low impact, costly to fully mitigate

---

### R10: Authentication Token Exposure
**Category:** Security
**Likelihood:** Low
**Impact:** Critical
**Severity:** 🔴 Critical
**Owner:** Security/SDK
**Status:** ✅ Mitigated

**Description:**
Authentication tokens exposed via logs, error messages, or insecure storage, allowing unauthorized access to agent endpoints.

**Mitigation Strategy:**
1. Generate cryptographically strong tokens (secrets.token_urlsafe)
2. Never log tokens (scrubbed from logs)
3. Secure storage (in-memory only, not written to disk)
4. Token validation on all protected endpoints

**Contingency Plan:**
- Revoke exposed token immediately
- Regenerate and redistribute new token
- Audit log access to identify breach scope
- Review and update token handling procedures

**Verification:**
```bash
# Check for hardcoded tokens in code
grep -r "token.*=" agents/ SHARED/ --include="*.py" | grep -v "auth_token" | grep -v "#"

# Verify token generation
grep "token_urlsafe\|uuid" SHARED/league_sdk/ -r

# Test token validation
pytest tests/protocol_compliance/test_auth_token_presence.py -v
```

**Evidence:**
- Token generation: [agents/league_manager/server.py](../agents/league_manager/server.py)
- No tokens in logs: Logging configuration scrubs sensitive fields
- Security scan: Evidence item #35 validates no hardcoded credentials

---

### R11: Test Coverage Gaps
**Category:** Quality
**Likelihood:** Medium
**Impact:** Medium
**Severity:** 🟡 Medium
**Owner:** Development Team
**Status:** ✅ Mitigated

**Description:**
Critical code paths not covered by tests, leading to undetected bugs that reach production.

**Mitigation Strategy:**
1. Mandatory 85% coverage gate (enforced)
2. Code review checklist includes test verification
3. 588 tests across 5 categories
4. CI/CD integration (planned)

**Contingency Plan:**
- Add tests before merging new features
- Block deployment if coverage drops below 85%
- Retroactive testing for discovered gaps
- Regular coverage audits

**Verification:**
```bash
# Measure current coverage
pytest tests/ --cov=agents --cov=SHARED/league_sdk --cov-report=term | grep "TOTAL"

# Run all 588 tests
pytest tests/ -v --tb=short

# Check coverage by module
pytest tests/ --cov=agents --cov=SHARED/league_sdk --cov-report=html
open htmlcov/index.html
```

**Evidence:**
- Current coverage: 85% (target met)
- Test count: 588 tests (161 SDK + 427 system)
- Coverage report: htmlcov/ directory
- Testing guide: [doc/testing_guide.md](testing_guide.md)

---

### R12: Scalability Bottleneck
**Category:** Performance
**Likelihood:** Medium
**Impact:** Medium
**Severity:** 🟡 Medium
**Owner:** Architecture
**Status:** ⏳ Active Monitoring

**Description:**
System cannot handle increased load (more players, more concurrent matches, higher request rates) due to architectural limitations.

**Mitigation Strategy:**
1. Load testing with 50+ concurrent matches
2. Horizontal scaling design (multiple referee agents)
3. Async I/O throughout (FastAPI + httpx)
4. Performance profiling and optimization

**Contingency Plan:**
- Add more referee agents (horizontal scaling)
- Implement queueing for match scheduling
- Optimize hot paths (standings updates, broadcasts)
- Database migration if file I/O becomes bottleneck

**Verification:**
```bash
# Load test (50 concurrent matches)
pytest tests/integration/test_concurrent_matches.py -v

# Performance profiling (planned)
# python -m cProfile -o profile.stats agents/league_manager/server.py

# Monitor response times
# Check logs for slow operations >1s
grep "duration" SHARED/logs/agents/*.log.jsonl | sort -t: -k4 -nr | head -10
```

**Evidence:**
- Load tests: [tests/integration/test_concurrent_matches.py](../tests/integration/test_concurrent_matches.py)
- Async design: [doc/architecture/thread_safety.md](architecture/thread_safety.md)
- Performance targets: <10s response time (99th percentile)

---

## 📈 Risk Trend Analysis

### Risks by Status Over Time

| Date | Mitigated | Active | Accepted | New | Closed |
|------|-----------|--------|----------|-----|--------|
| 2025-01-15 | 8 | 3 | 1 | 0 | 0 |

### Top 3 Risks Requiring Attention

1. **R02: Network Partition** (🟠 High) - Active monitoring, requires operational procedures
2. **R04: Memory Leak** (🟡 Medium) - Needs monitoring tools and restart automation
3. **R12: Scalability** (🟡 Medium) - Load testing and performance optimization ongoing

---

## 🔧 Risk Management Process

### Risk Identification
- Architecture reviews
- Code reviews
- Testing feedback
- Operational monitoring

### Risk Assessment
- Likelihood: High/Medium/Low
- Impact: Critical/High/Medium/Low
- Severity: Likelihood × Impact
- Priority: Critical > High > Medium > Low

### Risk Mitigation
- Technical controls (code, tests, monitoring)
- Process controls (reviews, checklists)
- Contingency planning
- Documentation

### Risk Monitoring
- Regular risk register reviews (monthly)
- Status updates in development meetings
- Incident post-mortems feed back to register
- Metrics tracking (test coverage, uptime, errors)

---

## 📚 Related Documentation

- **PRD Risk Baseline:** [PRD Section 13](../PRD_EvenOddLeague.md#13-risks--mitigation)
- **Thread Safety:** [doc/architecture/thread_safety.md](architecture/thread_safety.md)
- **Error Handling:** [doc/reference/error_handling_strategy.md](reference/error_handling_strategy.md)
- **Testing Guide:** [doc/testing_guide.md](testing_guide.md)

---

## 🔄 Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-01-15 | Initial risk register created from PRD Section 13 | Development Team |

---

**Last Review:** 2025-01-15
**Next Review:** Before M9.0 (Pre-Submission Checklist)
**Risk Owner:** Project Lead
**Maintained By:** Development Team
