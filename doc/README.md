# Documentation Index

**Version:** 2.0.0
**Last Updated:** 2025-01-15
**Status:** Production-Ready

This index organizes all documentation following best practices for production systems. Documentation is grouped by purpose to help you quickly find what you need.

---

## 📖 Table of Contents

1. [Getting Started](#-getting-started)
2. [How-To Guides](#-how-to-guides)
3. [Reference Documentation](#-reference-documentation)
4. [Architecture & Design](#-architecture--design)
5. [Research & Analysis](#-research--analysis)
6. [Planning & Implementation History](#-planning--implementation-history)
7. [Usability & Quality](#-usability--quality)
8. [Documentation Structure](#-documentation-structure)

---

## 🚀 Getting Started

**New to the project? Start here:**

- [../README.md](../README.md) - Project overview, quick start, and installation
- [developer_guide.md](developer_guide.md) - Complete developer onboarding guide
- [research_notes/QUICK_START_NOTEBOOK.md](research_notes/QUICK_START_NOTEBOOK.md) - Quick start for research notebook

---

## 📚 How-To Guides

**Practical guides for common tasks:**

### Core Guides (Start Here)

- [developer_guide.md](developer_guide.md) - **Developer Guide** - Development workflow and setup
  - Three installation methods with decision guide
  - Running the system and tests
  - Adding new agents and game types
  - Debugging and troubleshooting

- [configuration.md](configuration.md) - **Configuration Guide** - Complete system configuration (1,154 lines)
  - System, agent, league, and game configuration
  - Environment variable overrides
  - Configuration validation and troubleshooting

- [testing_guide.md](testing_guide.md) - **Testing Guide** - Complete testing documentation (3,208 lines)
  - 588 tests across 5 categories
  - Running tests and measuring coverage
  - Writing new tests
  - Test patterns and best practices

### Deployment & Operations

- [deployment_guide.md](deployment_guide.md) - **Deployment Guide** - Building packages and creating releases
  - Building SDK wheel and full system archive
  - Creating GitHub releases
  - Testing packages
  - Deployment best practices

- [guides/queue_processor_guide.md](guides/queue_processor_guide.md) - **Queue Processor Guide** - Thread-safe sequential processing
  - Eliminating race conditions in concurrent updates
  - Using SequentialQueueProcessor for standings updates
  - Complete League Manager examples
  - Testing concurrent operations

- [guides/HOW_QUALITY_WORKS.md](guides/HOW_QUALITY_WORKS.md) - Quality assurance workflow
  - Code quality tools (ruff, mypy, black, isort)
  - Running quality checks
  - CI/CD integration

---

## 📑 Reference Documentation

**Detailed technical reference (for lookup):**

### Protocol & API

- [reference/api_reference.md](reference/api_reference.md) - MCP tools, message formats, and examples
  - 18 message types (league.v2 protocol)
  - JSON-RPC 2.0 envelope format
  - Authentication and timeout specifications

### Error Handling

- [reference/error_codes_reference.md](reference/error_codes_reference.md) - E001–E018 error code catalog
- [reference/error_handling_strategy.md](reference/error_handling_strategy.md) - Retry and circuit breaker guidance
  - Exponential backoff strategy
  - Circuit breaker configuration
  - Retryable vs. terminal errors

### Data Management

- [reference/data_retention_policy.md](reference/data_retention_policy.md) - Retention policy and cleanup rules
  - Automated cleanup schedules
  - Archive strategy (gzip compression)
  - Data protection rules

### Quality Assurance

- [evidence_matrix.md](evidence_matrix.md) - **Evidence Matrix** - Verification tracking (35 items)
  - Verification commands for all requirements
  - Current status of all evidence items (35/35 verified)
  - Links to artifacts and test results
  - Score: 177/190 points (93% achievement)

- [risk_register.md](risk_register.md) - **Risk Register** - Risk tracking and mitigation (12 risks)
  - Risk severity and likelihood assessment
  - Mitigation strategies and ownership
  - Current status: 8 mitigated, 3 active, 1 accepted
  - Overall risk level: 🟢 LOW

---

## 🏗️ Architecture & Design

**Understanding the system design:**

### System Architecture

- [architecture.md](architecture.md) - **System Architecture** - C4 views, sequences, states, and data flow
  - Context, container, and component diagrams
  - Sequence diagrams (registration, match flow)
  - State machines and data flow

### Concurrency & Safety

- [architecture/thread_safety.md](architecture/thread_safety.md) - Concurrency model and safety rules
  - Thread-safe patterns
  - Async/await best practices
  - Lock-free data structures

### Architecture Decision Records (ADRs)

- [architecture/adr/README.md](architecture/adr/README.md) - **ADR Index** - 12 architecture decisions documented
  - [0001-use-fastapi-jsonrpc.md](architecture/adr/0001-use-fastapi-jsonrpc.md) - FastAPI + JSON-RPC over HTTP
  - [0002-async-httpx-client.md](architecture/adr/0002-async-httpx-client.md) - Async httpx for inter-agent calls
  - [0003-file-based-storage.md](architecture/adr/0003-file-based-storage.md) - File-based JSON storage
  - [0004-structured-jsonl-logging.md](architecture/adr/0004-structured-jsonl-logging.md) - Structured JSONL logging
  - [0005-retry-and-circuit-breaker.md](architecture/adr/0005-retry-and-circuit-breaker.md) - Retry + circuit breaker
  - [0006-method-alias-layer.md](architecture/adr/0006-method-alias-layer.md) - Method alias compatibility
  - [0007-cleanup-scheduler.md](architecture/adr/0007-cleanup-scheduler.md) - Scheduled cleanup
  - [0008-separate-referee-agents.md](architecture/adr/0008-separate-referee-agents.md) - Separate referee agents
  - [0009-shared-sdk-structure.md](architecture/adr/0009-shared-sdk-structure.md) - Shared SDK structure
  - [0010-round-robin-scheduling.md](architecture/adr/0010-round-robin-scheduling.md) - Round-robin scheduling
  - [0011-timeout-enforcement-referee.md](architecture/adr/0011-timeout-enforcement-referee.md) - Timeout enforcement
  - [0012-iso-8601-utc-timestamps.md](architecture/adr/0012-iso-8601-utc-timestamps.md) - ISO 8601 UTC timestamps

---

## 🔬 Research & Analysis

**Research methodology and experimental results:**

### Research Notebook (Mission M5.5)

- [research_notes/README.md](research_notes/README.md) - **Research Notebook Overview**
  - 14 cells, 3 LaTeX formulas, 7 plots
  - Statistical analysis with 95% confidence intervals
  - Actionable recommendations

- [research_notes/QUICK_START_NOTEBOOK.md](research_notes/QUICK_START_NOTEBOOK.md) - Quick start guide for notebook
- [research_notes/experiments.ipynb](research_notes/experiments.ipynb) - Interactive Jupyter notebook
- [research_notes/experiments.html](research_notes/experiments.html) - Pre-rendered HTML version (601 KB)

### Research Artifacts

- [research_notes/plot1_strategy_comparison.png](research_notes/plot1_strategy_comparison.png) - Strategy win rate comparison
- [research_notes/plot2_timeout_impact.png](research_notes/plot2_timeout_impact.png) - Timeout impact analysis
- [research_notes/plot3_4_retry_outcomes.png](research_notes/plot3_4_retry_outcomes.png) - Retry configuration outcomes

### Protocol Research

- [research_notes/mcp_protocol.md](research_notes/mcp_protocol.md) - MCP protocol research and notes

---

## 📋 Planning & Implementation History

**Project planning and development history:**

### Implementation Plans

- [plans/system_integration_verification_plan.md](plans/system_integration_verification_plan.md) - End-to-end verification flow
- [plans/M6.1_M6.2_IMPLEMENTATION_PLAN_v2.md](plans/M6.1_M6.2_IMPLEMENTATION_PLAN_v2.md) - CLI and operational scripts plan

### Mission Prompt Logs

Development prompts and planning documents for each mission:

- [prompt_log/mission_2_implementation_prompt.md](prompt_log/mission_2_implementation_prompt.md) - Mission 2 (Foundation)
- [prompt_log/config_layer_mission_3.0-3.3_prompt.md](prompt_log/config_layer_mission_3.0-3.3_prompt.md) - Mission 3.0-3.3 (Configuration)
- [prompt_log/testing_infrastructure_mission_4.0-4.1_prompt.md](prompt_log/testing_infrastructure_mission_4.0-4.1_prompt.md) - Mission 4.0-4.1 (Testing)
- [prompt_log/mission_4_0_4_1_implementation_prompt.md](prompt_log/mission_4_0_4_1_implementation_prompt.md) - Mission 4 implementation
- [prompt_log/missions_M6.1_M6.2_cli_and_operational_scripts_prompt.md](prompt_log/missions_M6.1_M6.2_cli_and_operational_scripts_prompt.md) - Mission 6.1-6.2 (CLI)
- [prompt_log/league_manager_missions_7.9-7.12_prompt.md](prompt_log/league_manager_missions_7.9-7.12_prompt.md) - Mission 7.9-7.12 (League Manager)
- [prompt_log/mission_7.13_and_7.13.5_deep_analysis_prompt.md](prompt_log/mission_7.13_and_7.13.5_deep_analysis_prompt.md) - Mission 7.13 (Deep Analysis)
- [prompt_log/comprehensive_verification_prompt.md](prompt_log/comprehensive_verification_prompt.md) - Comprehensive verification

---

## ✨ Usability & Quality

**Quality analysis and extensibility:**

- [usability_analysis.md](usability_analysis.md) - **M6.6 Usability Review**
  - UX analysis and recommendations
  - Operational considerations

- [usability_extensibility.md](usability_extensibility.md) - **ISO/IEC 25010 Quality Analysis** (1,400+ lines)
  - Complete ISO/IEC 25010 quality characteristics mapping
  - 5 extension points documented
  - Extensibility best practices

---

## 🎯 Domain Rules & Algorithms

**Game rules and scheduling algorithms:**

- [game_rules/even_odd.md](game_rules/even_odd.md) - Even/Odd game specification
  - Game rules and scoring
  - Win conditions
  - Protocol message flows

- [algorithms/round_robin.md](algorithms/round_robin.md) - Round-robin scheduling algorithm
  - Scheduling logic
  - Match pairing rules
  - Fairness guarantees

---

## 📊 Documentation Structure

This documentation follows the **Divio documentation system** and industry best practices:

1. **Getting Started** (Learning-oriented) → Quick onboarding
2. **How-To Guides** (Problem-oriented) → Solve specific problems
3. **Reference** (Information-oriented) → Technical specifications
4. **Architecture** (Understanding-oriented) → System design and decisions
5. **Research** (Analysis-oriented) → Experimental results
6. **History** (Context-oriented) → Development timeline

### Documentation Statistics

| Category | Files | Total Lines | Status |
|----------|-------|-------------|---------|
| **How-To Guides** | 5 | ~6,500 | ✅ Complete |
| **Reference** | 6 | ~3,500 | ✅ Complete |
| **Architecture** | 15 | ~3,000 | ✅ Complete |
| **Research** | 7 | ~1,500 + plots | ✅ Complete |
| **Planning** | 9 | ~1,500 | ✅ Complete |
| **Quality** | 2 | ~1,800 | ✅ Complete |
| **Domain** | 2 | ~800 | ✅ Complete |
| **TOTAL** | **46** | **~17,600** | **✅ Production-Ready** |

---

## 🔍 Quick Reference

**Find documentation by task:**

| I want to... | Read this |
|--------------|-----------|
| Get started with development | [developer_guide.md](developer_guide.md) |
| Configure the system | [configuration.md](configuration.md) |
| Run tests | [testing_guide.md](testing_guide.md) |
| Build packages and deploy | [deployment_guide.md](deployment_guide.md) |
| Understand the architecture | [architecture.md](architecture.md) |
| Look up error codes | [reference/error_codes_reference.md](reference/error_codes_reference.md) |
| Add a new agent | [developer_guide.md](developer_guide.md) § 8 |
| Add a new game type | [developer_guide.md](developer_guide.md) § 9 |
| Understand MCP protocol | [reference/api_reference.md](reference/api_reference.md) |
| Review research results | [research_notes/README.md](research_notes/README.md) |
| Understand design decisions | [architecture/adr/README.md](architecture/adr/README.md) |
| Check quality standards | [guides/HOW_QUALITY_WORKS.md](guides/HOW_QUALITY_WORKS.md) |
| Verify all requirements | [evidence_matrix.md](evidence_matrix.md) |
| Review project risks | [risk_register.md](risk_register.md) |
| Extend the system | [usability_extensibility.md](usability_extensibility.md) |

---

## 📝 Contributing to Documentation

When adding new documentation:

1. **Place it in the correct category folder**
2. **Update this README.md** with the new file reference
3. **Follow the documentation template** (see existing docs)
4. **Include version, date, and status headers**
5. **Add cross-references** to related documents
6. **Update the Quick Reference table** if applicable

For major changes, please review [../CONTRIBUTING.md](../CONTRIBUTING.md).

---

**Last Review:** 2025-01-15
**Maintained By:** Development Team
**Documentation Standard:** Divio System + Industry Best Practices
