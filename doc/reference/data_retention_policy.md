# Data Retention Policy

**Version:** 1.0.0
**Date:** 2025-12-20
**Protocol:** league.v2
**Status:** Active

---

## 1. Overview

This document defines the comprehensive data retention, archival, and cleanup policy for the Even/Odd League multi-agent system. The policy ensures:

1. **Compliance** with storage management best practices
2. **Performance** by preventing unbounded data growth
3. **Auditability** through historical archives
4. **Privacy** protection through controlled data lifecycle
5. **Observability** via logs without storage bloat

---

## 2. Data Classification & Retention Periods

### 2.1 Retention Schedule

| Data Type | Location | Retention Period | Justification | Storage Impact |
|-----------|----------|------------------|---------------|----------------|
| **Logs** | `SHARED/logs/**/*.log.jsonl` | **30 days** | Debugging recent issues, compliance | High growth rate |
| **Match Data** | `SHARED/data/matches/*.json` | **1 year** | Historical analysis, dispute resolution | Moderate growth |
| **Rounds History** | `SHARED/data/leagues/*/rounds.json` | **1 year** | League history, statistical analysis | Low growth |
| **Player History** | `SHARED/data/players/*/history.json` | **1 year** | Player statistics, performance tracking | Moderate growth |
| **Standings** | `SHARED/data/leagues/*/standings.json` | **Permanent** | Historical records, championship data | Minimal growth |
| **Configuration** | `SHARED/config/**/*.json` | **Permanent** | System configuration, never deleted | Static |
| **Test Data** | `SHARED/data/test/**/*` | **Immediate** | Cleanup after test runs | Test-only |

### 2.2 Data Growth Estimates

**Based on 4-player league scenario:**

| Data Type | Per Match | Per League | Monthly (4 leagues) | Annual |
|-----------|-----------|------------|---------------------|--------|
| Match JSON | 2-10 KB | 12-60 KB | 48-240 KB | ~576 KB - 2.8 MB |
| Player History | 1-3 KB/match | 4-12 KB | 16-48 KB | ~192 KB - 576 KB |
| Logs (per agent) | 1-5 MB/day | N/A | 120-600 MB | ~1.4 GB - 7.2 GB |
| **Total** | - | - | **~150-850 MB/month** | **~2-10 GB/year** |

**Conclusion:** Without retention policy, logs dominate storage (>80% of total). After 30-day log cleanup, annual storage is manageable (~500 MB - 1 GB).

---

## 3. Retention Policy Details

### 3.1 Logs (30-day retention)

**Scope:**
- `SHARED/logs/agents/*.log.jsonl` - Agent logs (players, referees)
- `SHARED/logs/league/*/*.log.jsonl` - League Manager logs
- `SHARED/logs/system/*.log.jsonl` - System orchestration logs
- Rotated log files: `*.log.jsonl.1`, `*.log.jsonl.2`, etc.

**Current Rotation Policy:**
- **Size-based rotation:** 100 MB per file (configured in `system.json`)
- **Backup count:** 5 rotated files retained
- **Handler:** `RotatingFileHandler` (Python logging)

**Retention Logic:**
- **Active log:** Never deleted (current `*.log.jsonl`)
- **Rotated logs:** Deleted if `file_mtime < (now - 30 days)`
- **Cleanup frequency:** Daily at 2:00 AM UTC

**Archive Strategy:**
```
Before deletion:
1. Compress rotated logs: gzip <file>.log.jsonl.X → <file>.log.jsonl.X.gz
2. Move to archive: SHARED/archive/logs/<year>/<month>/
3. Retention in archive: 6 months (configurable)
4. After 6 months in archive: Permanent deletion
```

**Example:**
```bash
# Day 0: Log created
SHARED/logs/agents/P01.log.jsonl (active)

# Day 15: Rotated (100 MB reached)
SHARED/logs/agents/P01.log.jsonl (new active)
SHARED/logs/agents/P01.log.jsonl.1 (rotated)

# Day 30: Cleanup job runs
- P01.log.jsonl.1 is 30 days old
- Archive: compress → SHARED/archive/logs/2025/12/P01.log.jsonl.1.gz
- Delete: P01.log.jsonl.1

# Day 210 (6 months later): Archive cleanup
- Delete: SHARED/archive/logs/2025/12/P01.log.jsonl.1.gz
```

**Special Cases:**
- **Error logs (ERROR level):** Consider longer retention (90 days) for critical incident investigation
- **Security logs (AUTH failures):** Retain 1 year for audit compliance

---

### 3.2 Match Data (1-year retention)

**Scope:**
- `SHARED/data/matches/<match_id>.json` - Individual match records

**Schema Fields Used for Cleanup:**
```json
{
  "match_id": "R1M1",
  "created_at": "2025-01-15T10:00:00Z",  // Used for age calculation
  "last_updated": "2025-01-15T10:05:00Z",
  "status": "COMPLETED",  // Only cleanup COMPLETED matches
  "league_id": "league_2025_even_odd"
}
```

**Retention Logic:**
```python
# Pseudo-code
for match in all_matches():
    if match.status == "COMPLETED" and (now - match.created_at) > 365 days:
        archive_match(match)
        delete_match(match)
```

**Archive Strategy:**
```
1. Group by league: SHARED/archive/matches/<league_id>/<year>/
2. Compress: tar.gz all matches from same league/year
3. Archive structure:
   SHARED/archive/matches/league_2025_even_odd/2025.tar.gz
   ├── R1M1.json
   ├── R1M2.json
   └── R2M1.json
```

**Exclusions:**
- **Championship matches:** Tag with `"championship": true`, retain permanently
- **Disputed matches:** Tag with `"disputed": true`, retain until resolved + 1 year

---

### 3.3 Rounds History (1-year retention)

**Scope:**
- `SHARED/data/leagues/<league_id>/rounds.json`

**Retention Logic:**
```json
{
  "rounds": [
    {
      "round_id": 1,
      "created_at": "2025-01-15T10:00:00Z",  // Age check
      "status": "COMPLETED"
    }
  ]
}
```

**Strategy:**
- **Prune old rounds:** Remove rounds >1 year from `rounds` array
- **Preserve metadata:** Keep league summary (total rounds, completion date)
- **Archive:** Save full rounds.json to `SHARED/archive/leagues/<league_id>/rounds_<year>.json.gz`

**Example:**
```json
// Before cleanup (2026-01-20)
{
  "rounds": [
    {"round_id": 1, "created_at": "2025-01-15T10:00:00Z", "status": "COMPLETED"},  // >1 year
    {"round_id": 2, "created_at": "2025-12-15T10:00:00Z", "status": "COMPLETED"}   // <1 year
  ]
}

// After cleanup
{
  "rounds": [
    {"round_id": 2, "created_at": "2025-12-15T10:00:00Z", "status": "COMPLETED"}
  ],
  "archived_rounds": 1,
  "oldest_archived": "2025-01-15T10:00:00Z"
}
```

---

### 3.4 Player History (1-year retention)

**Scope:**
- `SHARED/data/players/<player_id>/history.json`

**Schema:**
```json
{
  "player_id": "P01",
  "matches": [
    {
      "match_id": "R1M1",
      "timestamp": "2025-01-15T10:05:00Z",  // Age check
      "result": "WIN",
      "points": 3
    }
  ],
  "stats": {  // Preserved permanently
    "total_matches": 150,
    "wins": 90,
    "total_points": 270
  }
}
```

**Retention Logic:**
- **Prune old matches:** Remove matches >1 year from `matches` array
- **Preserve stats:** Aggregate statistics remain intact (total_matches, wins, etc.)
- **Archive:** Save full history to `SHARED/archive/players/<player_id>/history_<year>.json.gz`

**Example:**
```python
# Pseudo-code
def prune_player_history(player_id):
    history = load_history(player_id)
    cutoff = now() - 365 days

    old_matches = [m for m in history.matches if m.timestamp < cutoff]
    history.matches = [m for m in history.matches if m.timestamp >= cutoff]

    # Archive old matches
    archive_player_matches(player_id, old_matches)

    # Stats remain unchanged (already aggregated)
    save_history(player_id, history)
```

---

### 3.5 Standings (Permanent retention)

**Scope:**
- `SHARED/data/leagues/<league_id>/standings.json`

**Policy:** **NEVER DELETE**

**Justification:**
- Historical record of league champions
- Statistical analysis across seasons
- Minimal storage footprint (~1-5 KB per league)

**Backup Strategy:**
```
1. Monthly backups: SHARED/backups/standings/<year>/<month>/
2. Immutable archives: Once league completes, standings are read-only
3. Version control: Consider git tracking for standings files
```

---

## 4. Cleanup Procedures

### 4.1 Automated Cleanup (Recommended)

**Implementation:** Integrated into League Manager agent (M7.9-M7.13)

**Schedule:**
```python
# Daily cleanup at 2:00 AM UTC
CLEANUP_SCHEDULE = "0 2 * * *"  # Cron format

async def run_scheduled_cleanup():
    """Execute all cleanup tasks in sequence."""
    logger.info("Starting scheduled data retention cleanup")

    # Step 1: Clean logs (30 days)
    cleaned_logs = await cleanup_old_logs(retention_days=30)

    # Step 2: Archive and delete matches (1 year)
    archived_matches = await archive_old_matches(retention_days=365)

    # Step 3: Prune player history (1 year)
    pruned_players = await prune_player_histories(retention_days=365)

    # Step 4: Prune rounds history (1 year)
    pruned_rounds = await prune_league_rounds(retention_days=365)

    logger.info("Cleanup completed", data={
        "logs_deleted": cleaned_logs,
        "matches_archived": archived_matches,
        "players_pruned": pruned_players,
        "rounds_pruned": pruned_rounds
    })
```

**Location:** `agents/league_manager/cleanup_scheduler.py` (to be implemented in M7.9)

**Configuration:** `SHARED/config/system.json`
```json
{
  "data_retention": {
    "enabled": true,
    "logs_retention_days": 30,
    "match_data_retention_days": 365,
    "player_history_retention_days": 365,
    "rounds_retention_days": 365,
    "cleanup_schedule_cron": "0 2 * * *",
    "archive_enabled": true,
    "archive_path": "SHARED/archive/",
    "archive_compression": "gzip"
  }
}
```

---

### 4.2 Manual Cleanup (Fallback)

**Script:** `SHARED/scripts/cleanup_data.py`

**Usage:**
```bash
# Dry run (preview what would be deleted)
python SHARED/scripts/cleanup_data.py --dry-run

# Execute cleanup
python SHARED/scripts/cleanup_data.py --execute

# Cleanup specific data type
python SHARED/scripts/cleanup_data.py --execute --type logs
python SHARED/scripts/cleanup_data.py --execute --type matches

# Custom retention period
python SHARED/scripts/cleanup_data.py --execute --type logs --retention-days 60
```

**Output:**
```
Data Retention Cleanup Report
==============================
Date: 2025-12-20T14:30:00Z

[LOGS]
- Scanned: 47 rotated log files
- Deleted: 12 files (older than 30 days)
- Archived: 12 files → SHARED/archive/logs/2025/11/
- Freed: 245 MB

[MATCHES]
- Scanned: 156 match files
- Archived: 18 matches (older than 365 days)
- Archive: SHARED/archive/matches/league_2025_even_odd/2024.tar.gz
- Freed: 87 KB

[PLAYER HISTORY]
- Scanned: 24 player history files
- Pruned: 8 players (removed old matches)
- Archived: 142 match records
- Freed: 52 KB

Total space freed: 245.14 MB
```

---

### 4.3 Emergency Cleanup (Storage Full)

**Scenario:** Disk usage >90%, immediate action required

**Procedure:**
```bash
# Step 1: Check disk usage
df -h SHARED/

# Step 2: Identify largest files
du -sh SHARED/logs/* | sort -rh | head -10
du -sh SHARED/data/* | sort -rh | head -10

# Step 3: Emergency log cleanup (delete WITHOUT archive)
python SHARED/scripts/emergency_cleanup.py --type logs --retention-days 7

# Step 4: Compress old data
find SHARED/data/matches -name "*.json" -mtime +180 -exec gzip {} \;

# Step 5: Restart cleanup schedule
# (Ensure League Manager cleanup is running)
```

**Alert Threshold:** Configure monitoring to alert at 80% disk usage

---

## 5. Archive Strategy

### 5.1 Archive Structure

```
SHARED/archive/
├── logs/
│   ├── 2025/
│   │   ├── 11/
│   │   │   ├── P01.log.jsonl.1.gz
│   │   │   ├── P02.log.jsonl.2.gz
│   │   │   └── REF01.log.jsonl.1.gz
│   │   └── 12/
│   └── 2026/
├── matches/
│   ├── league_2025_even_odd/
│   │   ├── 2024.tar.gz
│   │   └── 2025.tar.gz
│   └── league_2026_winter/
├── players/
│   ├── P01/
│   │   ├── history_2024.json.gz
│   │   └── history_2025.json.gz
│   └── P02/
└── leagues/
    ├── league_2025_even_odd/
    │   └── rounds_2024.json.gz
    └── league_2026_winter/
```

### 5.2 Archive Retention

| Archive Type | Retention in Archive | Total Lifecycle | Reason |
|--------------|---------------------|-----------------|--------|
| Logs | 6 months | 30 days live + 6 months archive | Debugging historical issues |
| Matches | 5 years | 1 year live + 5 years archive | Dispute resolution, audits |
| Player History | 5 years | 1 year live + 5 years archive | Player performance analysis |
| Rounds | 5 years | 1 year live + 5 years archive | League historical analysis |

### 5.3 Archive Compression

**Format:** gzip (.gz) or tar+gzip (.tar.gz)

**Compression Ratios (estimated):**
- Logs (JSON): ~70-80% compression (100 MB → 20-30 MB)
- Match data: ~60-70% compression
- Player history: ~65-75% compression

**Performance:**
- Compression: Async background task (non-blocking)
- Decompression: On-demand (rare, for audit/dispute resolution)

---

## 6. Privacy & PII Considerations

### 6.1 Current Data Classification

**Personal Identifiable Information (PII) Assessment:**

| Data Field | PII? | Location | Handling |
|------------|------|----------|----------|
| `player_id` (P01, P02) | ❌ No | All data files | Pseudonymous identifier |
| `agent_id` (REF01, LM01) | ❌ No | All data files | System identifier |
| `display_name` | ⚠️ Maybe | Metadata (if added) | Could be real name |
| `contact_endpoint` | ❌ No | Configuration | Infrastructure URL |
| `auth_token` | ✅ Secret | In-memory only | Never logged |
| `conversation_id` | ❌ No | All messages | Session tracking |
| `timestamp` | ❌ No | All records | UTC timestamps |
| `game_choices` (even/odd) | ❌ No | Match data | Game mechanics |
| IP addresses | ❌ No | Not logged | Not captured |

**Current Status:** **No PII in current implementation** (all identifiers are pseudonymous)

### 6.2 Future PII Handling (If Added)

**If `display_name` or email is added to player metadata:**

1. **Anonymization Before Archive:**
   ```python
   def anonymize_match_data(match_data):
       """Replace display_name with player_id before archiving."""
       match_data["player_a_display"] = hash_pii(match_data["player_a_display"])
       match_data["player_b_display"] = hash_pii(match_data["player_b_display"])
       return match_data
   ```

2. **GDPR Compliance (Right to be Forgotten):**
   ```python
   async def purge_player_data(player_id):
       """Complete data purge for GDPR requests."""
       # Delete all player data (live + archive)
       delete_player_history(player_id)
       delete_player_matches(player_id)
       anonymize_logs(player_id)  # Replace player_id with "REDACTED"
   ```

3. **Consent Tracking:**
   - Add `data_consent` field to player registration
   - Log consent timestamp and version

**Recommendation:** If PII is introduced, update this policy to include GDPR/CCPA compliance sections.

---

## 7. Testing & Validation

### 7.1 Unit Tests

**Location:** `tests/unit/test_cleanup/`

**Test Coverage:**
```python
# test_log_cleanup.py
def test_cleanup_logs_older_than_retention():
    """Verify logs older than 30 days are deleted."""

def test_cleanup_preserves_recent_logs():
    """Verify logs within retention period are kept."""

def test_cleanup_archives_before_delete():
    """Verify logs are archived before deletion."""

# test_match_cleanup.py
def test_archive_completed_matches_older_than_1_year():
    """Verify old completed matches are archived."""

def test_preserve_in_progress_matches():
    """Verify active matches are never deleted."""

# test_player_history_cleanup.py
def test_prune_old_matches_preserve_stats():
    """Verify old matches removed but stats remain."""
```

### 7.2 Integration Tests

**Location:** `tests/integration/test_data_retention/`

```python
async def test_full_cleanup_cycle():
    """Test complete cleanup: logs → matches → history → rounds."""

async def test_cleanup_handles_missing_files():
    """Test graceful handling when files don't exist."""

async def test_cleanup_concurrent_access():
    """Test cleanup doesn't interfere with active operations."""
```

### 7.3 Manual Verification

**Checklist:**
```
□ Run cleanup script with --dry-run
□ Verify correct files identified for deletion
□ Check archive directory structure created
□ Verify compressed archives are readable
□ Check disk space freed matches expectation
□ Verify no active/recent data was deleted
□ Test decompression of archived files
□ Verify logs report accurate counts
```

---

## 8. Monitoring & Alerts

### 8.1 Metrics to Track

**Storage Metrics:**
```python
{
  "logs_total_size_mb": 450,
  "logs_files_count": 47,
  "matches_total_size_mb": 12,
  "matches_files_count": 156,
  "archive_total_size_mb": 1200,
  "disk_usage_percent": 45
}
```

**Cleanup Metrics:**
```python
{
  "last_cleanup_timestamp": "2025-12-20T02:00:00Z",
  "logs_deleted_count": 12,
  "logs_space_freed_mb": 245,
  "matches_archived_count": 18,
  "cleanup_duration_sec": 4.2,
  "cleanup_status": "SUCCESS"
}
```

### 8.2 Alerts

**Configure alerts for:**
- ⚠️ **Warning (80% disk usage):** Email notification to admin
- 🚨 **Critical (90% disk usage):** Emergency cleanup + page on-call
- ❌ **Error:** Cleanup job failed 3 times consecutively
- ⏰ **Info:** Cleanup job hasn't run in 48 hours (schedule issue)

**Alert Channels:**
- Logs: `SHARED/logs/system/cleanup.log.jsonl`
- Monitoring: Export to Prometheus/Grafana (if configured)
- Notifications: Email, Slack webhook (configurable)

---

## 9. Disaster Recovery

### 9.1 Backup Strategy

**Critical Data (Must Backup):**
1. **Standings:** `SHARED/data/leagues/*/standings.json` (permanent records)
2. **Current matches:** `SHARED/data/matches/*.json` (in-progress matches)
3. **Configuration:** `SHARED/config/**/*.json` (system state)

**Backup Schedule:**
```
Daily backup: SHARED/backups/<date>/
Weekly offsite: Cloud storage (S3, Google Cloud Storage)
```

**Retention:**
- Daily backups: 30 days
- Weekly backups: 1 year
- Annual backups: 7 years

### 9.2 Recovery Procedures

**Scenario: Accidental deletion of match data**

```bash
# Step 1: Check archive
ls SHARED/archive/matches/league_2025_even_odd/

# Step 2: Extract specific match
tar -xzf 2025.tar.gz R1M1.json

# Step 3: Restore to data directory
cp R1M1.json SHARED/data/matches/

# Step 4: Verify integrity
python SHARED/scripts/verify_data.py --file SHARED/data/matches/R1M1.json
```

**Scenario: Complete data loss**

```bash
# Restore from daily backup
rsync -av SHARED/backups/2025-12-19/ SHARED/data/

# Verify restoration
python SHARED/scripts/verify_data.py --all
```

---

## 10. Compliance & Audit

### 10.1 Audit Trail

**All cleanup operations are logged:**
```json
{
  "timestamp": "2025-12-20T02:00:15Z",
  "event_type": "DATA_RETENTION_CLEANUP",
  "component": "cleanup_scheduler",
  "level": "INFO",
  "message": "Deleted old log file",
  "data": {
    "file_path": "SHARED/logs/agents/P01.log.jsonl.3",
    "file_age_days": 45,
    "retention_policy_days": 30,
    "archived_to": "SHARED/archive/logs/2025/11/P01.log.jsonl.3.gz",
    "size_bytes": 104857600
  }
}
```

### 10.2 Compliance Verification

**Monthly Audit Checklist:**
```
□ Review cleanup logs for errors/anomalies
□ Verify disk usage trends (should be stable)
□ Check archive directory growth (should be linear)
□ Validate no production data in test directories
□ Confirm backups completed successfully
□ Test archive file integrity (sample decompression)
□ Review any manual cleanup interventions
```

**Annual Review:**
- Update retention periods based on usage patterns
- Review archive storage costs
- Assess if retention periods meet business needs

---

## 11. Configuration Reference

### 11.1 System Configuration

**File:** `SHARED/config/system.json`

```json
{
  "data_retention": {
    "enabled": true,
    "logs_retention_days": 30,
    "match_data_retention_days": 365,
    "player_history_retention_days": 365,
    "rounds_retention_days": 365,
    "standings_retention": "permanent",
    "cleanup_schedule_cron": "0 2 * * *",
    "archive_enabled": true,
    "archive_path": "SHARED/archive/",
    "archive_compression": "gzip",
    "archive_retention_days": {
      "logs": 180,
      "matches": 1825,
      "player_history": 1825,
      "rounds": 1825
    },
    "alerts": {
      "enabled": true,
      "disk_usage_warning_percent": 80,
      "disk_usage_critical_percent": 90,
      "cleanup_failure_threshold": 3
    }
  }
}
```

### 11.2 Environment Variables

**Override config via environment:**
```bash
export DATA_RETENTION_ENABLED=true
export DATA_RETENTION_LOGS_DAYS=60
export DATA_RETENTION_ARCHIVE_PATH=/mnt/archive
```

---

## 12. Implementation Roadmap

### 12.1 Phase 1: Foundation (M3.7) ✅
- [x] Create this documentation
- [x] Add configuration to `system.json`
- [x] Create cleanup utilities module
- [x] Add unit tests

### 12.2 Phase 2: Integration (M7.9 - League Manager)
- [ ] Implement cleanup scheduler in League Manager
- [ ] Add cleanup on League Manager startup
- [ ] Add periodic cleanup task (cron-based)
- [ ] Add cleanup API endpoint for manual triggers

### 12.3 Phase 3: Automation (M7.13 - League Orchestration)
- [ ] Integrate cleanup with league lifecycle
- [ ] Archive completed leagues automatically
- [ ] Add cleanup metrics to health checks

### 12.4 Phase 4: Observability (M8.x)
- [ ] Add cleanup dashboards
- [ ] Configure storage alerts
- [ ] Export metrics to monitoring system

---

## 13. References

**Related Documentation:**
- [../architecture/thread_safety.md](../architecture/thread_safety.md) - Thread-safe cleanup operations
- [error_handling_strategy.md](error_handling_strategy.md) - Error handling in cleanup tasks
- `SHARED/league_sdk/repositories.py` - Data access layer
- `SHARED/league_sdk/logger.py` - Logging infrastructure

**External Resources:**
- Python `logging.handlers.RotatingFileHandler` - Log rotation
- GDPR Compliance Guidelines
- Storage Best Practices

---

## 14. Summary

**Key Takeaways:**

1. ✅ **30-day log retention** prevents unbounded growth (saves ~70-80% storage)
2. ✅ **1-year data retention** balances auditability with storage efficiency
3. ✅ **Permanent standings** preserve historical championship records
4. ✅ **Automated cleanup** via League Manager (daily at 2 AM)
5. ✅ **Archive strategy** enables long-term retention at low cost
6. ✅ **No PII concerns** in current implementation
7. ✅ **Manual procedures** available as fallback
8. ✅ **Monitoring & alerts** ensure policy compliance

**Storage Impact:**
- Without retention: ~10+ GB/year (dominated by logs)
- With retention: ~500 MB - 1 GB/year (manageable)
- **Reduction: ~90% storage savings**

---

**Document Ownership:**
System Architecture Team

**Last Updated:** 2025-12-20
**Next Review:** 2026-03-20 (Quarterly)
