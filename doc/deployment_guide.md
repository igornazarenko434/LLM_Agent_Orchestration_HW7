# Deployment & Release Guide

**Document Version:** 1.0.0
**Date:** 2025-01-15
**Status:** Production-Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Package Types](#package-types)
3. [Building the SDK Wheel](#building-the-sdk-wheel)
4. [Building the Full System Archive](#building-the-full-system-archive)
5. [Creating GitHub Releases](#creating-github-releases)
6. [Testing the Packages](#testing-the-packages)
7. [Installation Methods for End Users](#installation-methods-for-end-users)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Even/Odd League system is distributed in **two formats** to serve different use cases:

| Package | Size | Contains | Use Case |
|---------|------|----------|----------|
| **SDK Wheel** | ~50 KB | SDK library only (9 Python files) | Developers building custom agents |
| **Full System Archive** | ~2 MB | Complete project (agents, tests, docs, scripts) | Running/evaluating the system |

This follows **modern Python packaging best practices**:
- **Library** (league_sdk) → Wheel for pip installation
- **Application** (Even/Odd League) → Archive for deployment

---

## Package Types

### Package 1: SDK Wheel (`league_sdk-1.0.0-py3-none-any.whl`)

**Purpose**: Library for building custom agents
**Size**: ~50 KB
**Format**: Python Wheel (.whl)

**Contains**:
```
league_sdk/
├── __init__.py
├── protocol.py (891 lines) - 18 message types
├── config_models.py (458 lines) - Pydantic schemas
├── config_loader.py (156 lines) - Config loading
├── repositories.py (485 lines) - Data persistence
├── logger.py (403 lines) - JSONL logging
├── retry.py (514 lines) - Retry + circuit breaker
├── queue_processor.py (59 lines) - Sequential queue
├── cleanup.py (258 lines) - Data retention
├── method_aliases.py (106 lines) - PDF compatibility
└── utils.py (33 lines) - Utilities
```

**Dependencies** (from pyproject.toml):
- pydantic>=2.0.0
- requests>=2.28.0
- httpx>=0.28.0
- python-dateutil>=2.8.0

**Does NOT include**:
- ❌ Agents (no player/referee/league manager)
- ❌ Tests
- ❌ Scripts
- ❌ Configuration files
- ❌ Documentation

**Who should use this**: Developers who want to build their own custom agents using our SDK

---

### Package 2: Full System Archive (`even-odd-league-v1.0.0.tar.gz`)

**Purpose**: Complete deployable system
**Size**: ~2 MB (without caches)
**Format**: Gzipped tarball (.tar.gz)

**Contains**:
```
even-odd-league-v1.0.0/
├── SHARED/
│   ├── league_sdk/ (SDK source)
│   ├── config/ (JSON configs)
│   └── scripts/ (utility scripts)
├── agents/
│   ├── league_manager/
│   ├── referee_REF01/
│   ├── referee_REF02/
│   ├── player_P01/
│   ├── player_P02/
│   ├── player_P03/
│   └── player_P04/
├── tests/ (588 tests)
├── doc/ (all documentation)
├── scripts/ (12 operational scripts)
├── README.md
├── requirements.txt
├── pyproject.toml
├── PRD_EvenOddLeague.md
├── Missions_EvenOddLeague.md
└── .env.example
```

**Who should use this**: Professors, evaluators, deployers who want to run the complete system

---

## Building the SDK Wheel

### Option 1: Automated Build (Recommended)

Use the automated build script that handles everything:

```bash
# Build both SDK wheel and full system archive
./scripts/build_release_packages.sh

# Or build only SDK wheel
./scripts/build_release_packages.sh --skip-archive

# Dry run to see what would be built
./scripts/build_release_packages.sh --dry-run
```

The script automatically:
- ✅ Checks if build tool is installed (installs if needed)
- ✅ Builds the SDK wheel
- ✅ Verifies the output
- ✅ Reports file size and location

**Output**: `SHARED/league_sdk/dist/league_sdk-1.0.0-py3-none-any.whl`

---

### Option 2: Manual Build

If you prefer to build manually:

```bash
# Install build tool if needed
pip install build

# Navigate to SDK directory
cd SHARED/league_sdk

# Build wheel and source distribution
python3 -m build

# Output:
# dist/league_sdk-1.0.0-py3-none-any.whl  ← Upload this to GitHub Releases
# dist/league_sdk-1.0.0.tar.gz
```

### Verify Build

```bash
# Check file was created
ls -lh dist/league_sdk-1.0.0-py3-none-any.whl

# Expected: ~50KB file

# Test installation in clean environment
python3 -m venv /tmp/test-sdk
source /tmp/test-sdk/bin/activate
pip install dist/league_sdk-1.0.0-py3-none-any.whl
python3 -c "from league_sdk import protocol, logger, retry; print('✅ SDK works')"
deactivate
rm -rf /tmp/test-sdk
```

---

## Building the Full System Archive

### Option 1: Automated Build (Recommended)

Use the automated build script for clean, consistent archives:

```bash
# Build both SDK wheel and full system archive
./scripts/build_release_packages.sh

# Or build only full system archive
./scripts/build_release_packages.sh --skip-sdk

# Dry run to see what would be included/excluded
./scripts/build_release_packages.sh --dry-run
```

The script automatically:
- ✅ Excludes all cache files (.mypy_cache, .ruff_cache, __pycache__, .DS_Store)
- ✅ Excludes virtual environments (venv, .venv)
- ✅ Excludes runtime data (SHARED/data, SHARED/logs)
- ✅ Includes only production files
- ✅ Verifies no cache pollution
- ✅ Reports file size and count

**Output**: `even-odd-league-v1.0.0.tar.gz` (~2MB, 500-600 files)

---

### Option 2: Manual Build

If you prefer to build manually (not recommended - easy to forget exclusions):

```bash
# From project root
cd /Users/igornazarenko/PycharmProjects/LLM_Agent_Orchestration_HW7

# Build archive with proper exclusions
tar -czf even-odd-league-v1.0.0.tar.gz \
  --exclude='venv' \
  --exclude='.venv' \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache' \
  --exclude='htmlcov' \
  --exclude='.coverage' \
  --exclude='.mypy_cache' \
  --exclude='.ruff_cache' \
  --exclude='.DS_Store' \
  --exclude='dist' \
  --exclude='build' \
  --exclude='*.egg-info' \
  --exclude='SHARED/data' \
  --exclude='SHARED/logs' \
  --exclude='SHARED/archive' \
  --exclude='.idea' \
  --exclude='.quality_check_venv' \
  --exclude='backups' \
  SHARED/ agents/ tests/ doc/ scripts/ \
  README.md requirements.txt pyproject.toml \
  PRD_EvenOddLeague.md Missions_EvenOddLeague.md \
  CONTRIBUTING.md .env.example \
  .gitignore .flake8 .pre-commit-config.yaml \
  mypy.ini verify_installation.py
```

### Verify Archive

```bash
# Check file size (should be ~2MB, not >3MB)
ls -lh even-odd-league-v1.0.0.tar.gz

# Count files (should be ~500-600, not 778)
tar -tzf even-odd-league-v1.0.0.tar.gz | wc -l

# Check for unwanted cache files (should be empty)
tar -tzf even-odd-league-v1.0.0.tar.gz | grep -E '\.mypy_cache|\.ruff_cache|__pycache__|\.DS_Store' || echo "✅ No cache files"

# List first 50 files
tar -tzf even-odd-league-v1.0.0.tar.gz | head -50
```

---

## Creating GitHub Releases

### Option 1: GitHub Web Interface (Recommended)

1. **Navigate to Releases**:
   ```
   https://github.com/YOUR-USERNAME/LLM_Agent_Orchestration_HW7/releases/new
   ```

2. **Fill Release Information**:
   - **Tag**: `v1.0.0`
   - **Title**: `Even/Odd League v1.0.0 - Production Release`
   - **Description**: See [Release Description Template](#release-description-template) below

3. **Upload Release Assets**:
   - Drag and drop `SHARED/league_sdk/dist/league_sdk-1.0.0-py3-none-any.whl`
   - Drag and drop `even-odd-league-v1.0.0.tar.gz`

4. **Publish Release**

### Option 2: GitHub CLI

```bash
# Install GitHub CLI if needed: https://cli.github.com/

# Create release and upload both files
gh release create v1.0.0 \
  --title "Even/Odd League v1.0.0 - Production Release" \
  --notes-file doc/deployment_guide.md \
  SHARED/league_sdk/dist/league_sdk-1.0.0-py3-none-any.whl \
  even-odd-league-v1.0.0.tar.gz
```

### Release Description Template

```markdown
# Even/Odd League v1.0.0 🎮

Production-ready multi-agent system demonstrating advanced distributed computing patterns with MCP protocol.

## 🎯 What's Included

- ✅ **588 tests** with 85% code coverage
- ✅ **7 autonomous agents** (League Manager + 2 Referees + 4 Players)
- ✅ **MCP JSON-RPC 2.0 protocol** (league.v2 with 18 message types)
- ✅ **Comprehensive documentation** (15,100+ lines across guides)
- ✅ **12 automation scripts** for deployment and monitoring
- ✅ **PEP 517/518/621 compliant** packaging

## 📦 Installation

### Choose Your Installation Method

| I want to... | Download This | Steps |
|--------------|---------------|-------|
| **Run the complete Even/Odd League system** | [even-odd-league-v1.0.0.tar.gz](even-odd-league-v1.0.0.tar.gz) | Extract → Install deps → Run |
| **Build my own agents with the SDK** | [league_sdk-1.0.0-py3-none-any.whl](league_sdk-1.0.0-py3-none-any.whl) | pip install |
| **Contribute or modify code** | Clone the repository | git clone |

---

### Option 1: Run Complete System (Recommended for Professors)

Download the full system archive:

\`\`\`bash
# Download
wget https://github.com/YOUR-ORG/LLM_Agent_Orchestration_HW7/releases/download/v1.0.0/even-odd-league-v1.0.0.tar.gz

# Extract
tar -xzf even-odd-league-v1.0.0.tar.gz
cd even-odd-league-v1.0.0

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e SHARED/league_sdk

# Verify installation
python3 -c "from league_sdk import protocol; print('✅ SDK installed')"

# Start the system
./scripts/start_league.sh

# Check system health
./scripts/check_health.sh

# Start a league round
./scripts/trigger_league_start.sh

# View standings
./scripts/query_standings.sh
\`\`\`

**Expected output**: All 7 agents running on ports 8000-8104

---

### Option 2: SDK Library Only (For Custom Development)

Download the SDK wheel:

\`\`\`bash
# Install SDK
pip install https://github.com/YOUR-ORG/LLM_Agent_Orchestration_HW7/releases/download/v1.0.0/league_sdk-1.0.0-py3-none-any.whl

# Verify
python3 -c "from league_sdk import protocol, logger, retry; print('✅ SDK installed')"

# Build your own agents
python3 your_agent.py
\`\`\`

**Note**: This installs ONLY the SDK library. To run the Even/Odd League system, use Option 1 or 3.

---

### Option 3: Development from Source

Clone the repository for full development access:

\`\`\`bash
git clone https://github.com/YOUR-ORG/LLM_Agent_Orchestration_HW7.git
cd LLM_Agent_Orchestration_HW7

# Setup
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e SHARED/league_sdk

# Run tests
PYTHONPATH=SHARED:\$PYTHONPATH pytest

# Start system
./scripts/start_league.sh
\`\`\`

---

## 📚 Documentation

- **[README.md](README.md)** - Project overview and quick start
- **[Developer Guide](doc/developer_guide.md)** - Complete development setup
- **[Configuration Guide](doc/configuration.md)** - All configuration options
- **[Testing Guide](doc/testing_guide.md)** - Running and writing tests (3,208 lines)
- **[Architecture Docs](doc/architecture.md)** - System architecture and design

---

## 🔧 System Requirements

- Python 3.10+ (tested on 3.10, 3.11, 3.12, 3.13, 3.14)
- 512 MB RAM minimum (4GB recommended)
- Ports 8000-8104 available
- ~500MB disk space (including venv)

---

## 📊 Technical Highlights

- **Async/await architecture** with FastAPI and httpx
- **Retry logic** with exponential backoff (2s → 4s → 8s) and circuit breaker
- **Structured logging** in JSONL format with correlation IDs
- **Pydantic validation** for all message types and configs
- **Data retention** with automated cleanup and gzip archival (80% reduction)
- **Health checks** and graceful shutdown
- **85% test coverage** across unit, integration, E2E, and protocol tests

---

## 🏆 Best Practices Demonstrated

- ✅ PEP 517/518/621 compliant packaging
- ✅ Modern async Python patterns (httpx, FastAPI)
- ✅ JSON-RPC 2.0 protocol implementation
- ✅ Comprehensive test pyramid (588 tests)
- ✅ ISO/IEC 25010 quality characteristics
- ✅ Configuration-driven architecture
- ✅ Structured logging and observability
- ✅ Graceful error handling and retries

---

## 📝 Release Notes

### Features
- Multi-agent league system with 7 autonomous agents
- Even/Odd parity game with round-robin scheduling
- MCP JSON-RPC 2.0 protocol (league.v2, 18 message types)
- Automated match orchestration and scoring
- Real-time standings calculation
- Data persistence with atomic writes and archival

### Infrastructure
- 12 automation scripts for deployment and monitoring
- Comprehensive test suite (588 tests, 85% coverage)
- 15,100+ lines of documentation
- Production-ready configuration system

### Quality
- All 588 tests passing ✅
- Type hints throughout
- Linting with black, flake8, mypy, pylint, isort
- Protocol compliance validation

---

## 💬 Support

- **Documentation**: See `doc/` directory in the archive
- **Issues**: GitHub Issues
- **Architecture**: See `doc/architecture.md`

---

## 📄 License

MIT License - See LICENSE file for details

---

**Built with**: Python 3.10+ • FastAPI • Pydantic • Pytest
**Demonstrates**: MCP Protocol • Multi-Agent Systems • Async Architecture • Production Best Practices
```

---

## Testing the Packages

### Test 1: SDK Wheel Installation

```bash
# Create clean test environment
mkdir -p /tmp/test-sdk-install
cd /tmp/test-sdk-install
python3 -m venv venv
source venv/bin/activate

# Install SDK wheel
pip install /path/to/league_sdk-1.0.0-py3-none-any.whl

# Test imports
python3 << 'EOF'
from league_sdk import protocol, logger, retry, config_loader
from league_sdk.protocol import GameInvitation, MessageEnvelope
from league_sdk.logger import JsonLogger
from league_sdk.retry import call_with_retry, CircuitBreaker
from league_sdk.config_loader import load_system_config
from league_sdk.repositories import StandingsRepository
from league_sdk.cleanup import CleanupScheduler
print("✅ All SDK imports successful")
EOF

# Verify package metadata
pip show league-sdk

# Expected output:
# Name: league-sdk
# Version: 1.0.0
# Summary: Shared SDK for Even/Odd League Multi-Agent System
# Location: /tmp/test-sdk-install/venv/lib/python3.X/site-packages

# Cleanup
deactivate
cd /tmp
rm -rf /tmp/test-sdk-install

echo "✅ SDK wheel test passed"
```

### Test 2: Full System Archive Installation

```bash
# Create clean test environment
mkdir -p /tmp/test-full-system
cd /tmp/test-full-system

# Extract archive
tar -xzf /path/to/even-odd-league-v1.0.0.tar.gz

# Verify extraction
ls -la
# Expected: SHARED/, agents/, tests/, doc/, scripts/, README.md

# Setup
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e SHARED/league_sdk

# Run quick tests
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/unit/test_sdk/test_protocol_models.py -v

# Expected: All tests pass

# Try starting one agent
PYTHONPATH=SHARED:$PYTHONPATH timeout 5 python3 agents/player_P01/main.py &
sleep 2

# Check health
curl http://localhost:8101/health

# Expected: {"status":"ok"}

# Kill agent
pkill -f "agents/player_P01/main.py"

# Cleanup
deactivate
cd /tmp
rm -rf /tmp/test-full-system

echo "✅ Full system archive test passed"
```

---

## Installation Methods for End Users

### Summary Table

| Method | Use Case | Time | Git Needed | Tests Included | Scripts Included |
|--------|----------|------|------------|----------------|------------------|
| **Git Clone** | Development, contribution | 5 min | Yes | Yes | Yes |
| **Full Archive** | Quick deployment, evaluation | 3 min | No | Yes | Yes |
| **SDK Wheel** | Library use only | 1 min | No | No | No |

### Detailed Steps for Each Method

See [README.md Installation Section](../README.md#-installation) for complete step-by-step instructions.

---

## Troubleshooting

### Issue: SDK wheel build fails

**Error**: `ModuleNotFoundError: No module named 'build'`

**Solution**:
```bash
pip install build
cd SHARED/league_sdk
python3 -m build
```

---

### Issue: Archive too large (>3MB)

**Cause**: Cache files included

**Solution**: Rebuild with proper exclusions (see [Building the Full System Archive](#building-the-full-system-archive))

---

### Issue: SDK import fails after wheel installation

**Error**: `ModuleNotFoundError: No module named 'league_sdk'`

**Solution**:
```bash
# Verify installation
pip show league-sdk

# Reinstall if needed
pip install --force-reinstall league_sdk-1.0.0-py3-none-any.whl
```

---

### Issue: Full system tests fail after extraction

**Error**: `ModuleNotFoundError: No module named 'league_sdk'`

**Solution**:
```bash
# Make sure SDK is installed in editable mode
pip install -e SHARED/league_sdk

# Run tests with PYTHONPATH
PYTHONPATH=SHARED:$PYTHONPATH pytest
```

---

## Best Practices Checklist

Before creating a release:

- [ ] SDK wheel builds successfully (`python3 -m build`)
- [ ] SDK wheel is ~50KB (not >100KB)
- [ ] SDK wheel installs in clean environment
- [ ] SDK imports work after installation
- [ ] Full archive is ~2MB (not >3MB)
- [ ] Full archive contains no cache files
- [ ] Full archive extracts cleanly
- [ ] Tests pass after archive extraction
- [ ] Scripts work after archive extraction
- [ ] Both packages uploaded to GitHub Releases
- [ ] Release description includes clear installation instructions
- [ ] README.md updated with release download links

---

**Last Updated**: 2025-01-15
**Maintained By**: Development Team
**Related Documents**: [README.md](../README.md), [developer_guide.md](developer_guide.md), [configuration.md](configuration.md)
