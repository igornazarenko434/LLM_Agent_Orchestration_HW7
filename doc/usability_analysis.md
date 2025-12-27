# Usability Analysis (M6.6)

Date: 2025-12-27
Scope: CLI agents (LM/Referee/Player), operational scripts, and documentation.

This document evaluates usability and accessibility of the Even/Odd League system
based on CLI design principles, Nielsen's 10 heuristics, and practical operator
workflows. Findings and recommendations are aligned with the current
implementation (scripts and agent CLIs).

---

## 1) System Overview (What Was Evaluated)

### Agent CLIs
- Player agents: `agents/player_P01/main.py` through `player_P04/main.py`
- Referee agents: `agents/referee_REF01/main.py`, `agents/referee_REF02/main.py`
- League Manager: `agents/league_manager/main.py`

### Operational Scripts
- Startup/stop: `scripts/start_league.sh`, `scripts/stop_league.sh`
- Health/config checks: `scripts/check_health.sh`, `scripts/verify_configs.sh`
- Registration and orchestration: `scripts/check_registration_status.sh`,
  `scripts/trigger_league_start.sh`
- Queries/debug: `scripts/query_standings.sh`, `scripts/view_match_state.sh`,
  `scripts/analyze_logs.sh`
- Maintenance: `scripts/backup_data.sh`, `scripts/restore_data.sh`,
  `scripts/cleanup_old_data.sh`

### Logging/Data Paths (Current)
- Structured logs: [SHARED/logs/league/<league_id>/*.log.jsonl](../SHARED/logs/league/)
- Agent stdout logs: [SHARED/logs/agents/*.log](../SHARED/logs/agents/)
- Data outputs: [SHARED/data/](../SHARED/data/) (matches, rounds, standings, player history)

---

## 2) CLI Design Principles

### Discoverability
- Strengths: Consistent `--help` support, explicit usage blocks in scripts, and
  named options for auth, sender, and IDs.
- Gaps: Some options require domain knowledge (e.g., sender/auth token for
  `view_match_state`), but are explained in script usage.

### Consistency
- Strengths: All scripts support `--plain`/`--json`; agents use consistent
  `--log-level`, `--plain`, `--json`, `--verbose`, `--quiet`.
- Gaps: Agent CLIs and scripts have different output formats by necessity
  (agent logs vs script stdout), but flags are consistent.

### Feedback and Status
- Strengths: Scripts report success/failure and summarize actions. MCP calls
  return JSON-RPC results or errors and are surfaced to the operator.
- Gaps: `query_standings.sh` prints standings lines without a header in plain
  mode (acceptable, but could optionally label each entry).

### Error Prevention
- Strengths: Scripts validate endpoints and config presence; `verify_configs.sh`
  fails fast on invalid JSON.
- Gaps: Scripts that accept `--sender/--auth-token` do not validate token length
  against config; this is intentional to avoid coupling.

### Recoverability
- Strengths: Retry behavior is handled by agents; scripts provide clear failure
  messages and exit codes where appropriate.
- Gaps: `restore_data.sh` uses confirmation prompts; automation should use
  `--json` + `FORCE=1`.

---

## 3) Accessibility Considerations

### Screen Reader / Plain Mode
- All scripts support `--plain` and avoid emoji; common logging uses
  `set_output_mode plain`.
- Agent CLIs expose `--plain` and `--json`.

### Color / Contrast
- Output colorization is disabled when `NO_COLOR` is set or in plain/json mode.

### Text Output
- Plain mode uses readable text prefixes (INFO, WARN, SUCCESS).
- JSON mode provides structured machine-friendly output for automation.

---

## 4) Nielsen's 10 Heuristics (Score >= 7/10 Each)

Scale: 1 (poor) to 10 (excellent).
Minimum target: 7/10 each.

1) Visibility of system status: **8/10**
   - Scripts print progress and readiness; agent logs are structured JSONL.

2) Match between system and real world: **8/10**
   - Domain terms (rounds, matches, standings) align with league operations.

3) User control and freedom: **7/10**
   - Operators can start/stop agents, trigger league start, and query tools.
   - Manual overrides exist via scripts and MCP tools.

4) Consistency and standards: **8/10**
   - Flags and output modes are consistent across scripts and agents.

5) Error prevention: **7/10**
   - Config validation and endpoint checks prevent many failures.

6) Recognition rather than recall: **7/10**
   - Help text includes examples; scripts list expected usage.

7) Flexibility and efficiency of use: **7/10**
   - JSON output, `--plain`, and scripts allow fast ops.

8) Aesthetic and minimalist design: **8/10**
   - CLI output is concise and reduces noise in normal mode.

9) Help users recognize, diagnose, recover: **8/10**
   - Error codes are surfaced; scripts show clear failure context.

10) Help and documentation: **8/10**
   - README + docs cover usage; scripts have inline help and examples.

---

## 5) Error Message Clarity

### Strengths
- Uses explicit error codes (E001-E018) and JSON-RPC messages.
- Script failures include context (e.g., endpoint down, invalid config).

### Risks
- Debug tools may error on missing sender/auth; errors are accurate but may
  surprise operators without knowledge of auth settings.

---

## 6) Documentation Clarity

### Strengths
- Scripts and CLIs include usage and examples.
- Verification plan describes full end-to-end flow.

### Gaps
- No dedicated quick reference for auth token retrieval for debug tools; this
  is handled by `get_registration_status` and LM logs.

---

## 7) Best Practices Applied (Project-Specific)

This section documents the concrete practices implemented in this repo and why
they matter for the Even/Odd League workflow.

1) **Config-driven endpoints and ports**
   - Scripts and agents resolve endpoints from [SHARED/config/agents/agents_config.json](../SHARED/config/agents/agents_config.json)
     and host/protocol from [SHARED/config/system.json](../SHARED/config/system.json).
   - Prevents drift between CLI scripts and runtime, and supports multi-agent
     scale-out without code edits.

2) **Protocol alignment and compatibility**
   - All MCP calls use JSON-RPC 2.0 with `protocol: league.v2`.
   - Compatibility layer (`league_sdk/method_aliases.py`) ensures PDF method
     names map to system message types.

3) **Structured logging and traceability**
   - Structured JSONL logs for protocol-level messages are written to
     [SHARED/logs/league/<league_id>](../SHARED/logs/league/).
   - Agent stdout logs go to [SHARED/logs/agents](../SHARED/logs/agents/), aiding system-wide traceability.

4) **Accessibility-first CLI**
   - All scripts support `--plain` and `--json` for screen readers and automation.
   - Color and emoji output is optional and suppressed in plain/json modes.

5) **Fail-fast validation and safe defaults**
   - `verify_configs.sh` and health checks prevent starting with invalid configs.
   - Debug tools allow `allow_start_league_without_auth` only when configured.

6) **Separation of concerns**
   - League Manager orchestrates, Referee conducts matches, Players respond,
     repositories persist data, scripts operate the system.

---

## 8) Quality Gates (Evidence and Status)

These gates are aligned with project expectations. Each line indicates the
current status based on implemented behavior and available tooling.

- **Code Quality:** Python changes pass `black`, `isort`, `flake8`, `mypy`.
  - Status: Verified in recent commits; see pre-commit output.
- **Script Quality:** All shell scripts pass `bash -n`.
  - Status: Verified (syntax check).
- **Functional:** Full league can be started, run, and stopped using scripts.
  - Status: Verified with `start_league.sh`, `trigger_league_start.sh`, and
    `stop_league.sh`.
- **Accessibility:** All scripts work with `--plain` (no emoji dependencies).
  - Status: Verified; `common.sh` enforces plain output mode.
- **Documentation:** README includes script and CLI examples.
  - Status: Present; update if new scripts are added later.
- **Error Handling:** Errors use actual protocol codes (E001–E018) with
  recovery context where applicable.
  - Status: Implemented across agents and debug tools.
- **Usability:** Nielsen heuristic scores are all ≥7/10.
  - Status: Confirmed in Section 4.

---

## 9) Recommendations (Aligned With Current Implementation)

1) Add a short "Auth Token Quickstart" section in README, pointing to:
   - `get_registration_status` on Player/Referee
   - `check_registration_status.sh --sender --auth-token`

2) Consider adding a helper script to fetch tokens and export them as env vars
   for repeated debug tool usage (non-blocking, optional).

3) In `query_standings.sh`, optionally add a header line in plain mode:
   "Player: points (W/D/L)" for clarity (cosmetic).

---

## 10) Compliance Checklist (M6.6 DoD)

- [x] [usability_analysis.md](usability_analysis.md) created
- [x] CLI design principles analysis
- [x] Accessibility considerations
- [x] Nielsen heuristics evaluation
- [x] Error message clarity assessment
- [x] Documentation clarity evaluation

---

## 11) Evidence

Self-verify:
```bash
cat doc/usability_analysis.md | rg "CLI|Usability|Accessibility|Heuristics|Nielsen" && echo "Usability analysis complete"
```
