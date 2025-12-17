# 📋 Kickoff Agent v3.1 - Templates Library

**Version**: 3.1.0 - Updated with new submission guidelines (60% Academic / 40% Technical split)
**Purpose**: Complete template collection for PRD, Missions, Progress Tracker, and .claude files
**Usage**: Reference these templates when generating deliverables (used by kickoff_agent_core_v3.1.md)

**NEW v3.1 Requirements**:
- Package Organization (Chapter 15): __init__.py in all packages, proper directory structure
- Parallel Processing (Chapter 16): Multiprocessing vs multithreading, thread safety
- Modular Design & Building Blocks (Chapter 17): SRP, Separation of Concerns, reusability
- Updated grading: 60% Academic Criteria + 40% Technical Criteria

---

## 📖 TABLE OF CONTENTS

- **Section 1**: PRD Template (Enhanced with Evidence Matrix)
- **Section 2**: Missions Templates - 5 Project Types
  - 2.1: Full-Stack Web Application
  - 2.2: CLI-Only Application
  - 2.3: Backend REST API
  - 2.4: Data Pipeline / ETL
  - 2.5: Machine Learning Model
- **Section 3**: Progress Tracker Template
- **Section 4**: .claude File Template

---

# SECTION 1: PRD TEMPLATE

## 📋 PRD Template (Enhanced with Evidence Matrix)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  📋 PRD TEMPLATE - FOLLOW THIS STRUCTURE EXACTLY                             ║
║                                                                               ║
║  When generating PRD_[ProjectName].md, include ALL sections below:           ║
║  - This is your complete blueprint for the PRD file                          ║
║  - Do NOT skip or abbreviate any section                                     ║
║  - Target: Complete all 17 sections with comprehensive detail               ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### Required PRD Sections

Generate Markdown with these sections (use tables whenever possible):

1. **Overview** (Name, Tagline, Project Type, Background, Problem, Alignment, Success)
2. **Stakeholders & Personas** (two tables: 5 stakeholder groups, 2+ personas)
3. **KPIs & Requirements** (KPI table with verification commands, Functional Reqs, Non-Functional Reqs covering ISO-25010, 6+ User Stories)
4. **Scope & Constraints** (Dependencies, Assumptions, Constraints, In/Out of Scope)
5. **Installation & Verification Plan** (Installation Matrix with 10+ steps, each with verification command, include `pip install -e .` verification)
6. **Delivery Plan** (Timeline with ≥4 milestones, Deliverables, Risks ≥3, Open Questions)
7. **Data & Integrations** (Data sources, External APIs, Extensibility hooks)
8. **Configuration & Security** (strategy, env vars ≥5, security controls, token budget)
8.5. **Quality Standards & Code Quality (CRITICAL - Professor's top deduction area)** (Linting configuration: pylint/.pylintrc with standards, CI/CD pipeline: .github/workflows/test.yml running tests+linting+coverage, Style guide: CONTRIBUTING.md with code standards+naming conventions+commit format+PR process, Pre-commit hooks: .pre-commit-config.yaml with black+pylint+mypy+trailing whitespace, Code formatter: black configuration in pyproject.toml, Type checking: mypy configuration with strict mode)
9. **Testing & QA** (strategy, coverage targets ≥70% minimum / ≥85% for 90+, CI/CD, edge cases ≥5)
10. **Research & Analysis** (experiments with ≥3 parameters, sensitivity analysis, notebooks ≥8 cells, LaTeX formulas ≥2, visualizations ≥4 plot types)
11. **UX & Accessibility** (Usability analysis: Nielsen's 10 for Web UI / CLI usability principles / API usability / Pipeline observability, accessibility plan, screenshots ≥8 minimum / ≥20 for 90+)
12. **Architecture Decisions** (ADRs ≥5 minimum / ≥7 for 90+, option comparison tables, recommendations, escalation triggers)
13. **Architecture & Modular Design (NEW v3.1)** (Building block structure with Input/Output/Setup data, Component diagrams showing SRP, Separation of Concerns between layers, Parallel processing strategy: multiprocessing vs multithreading decisions, Thread safety mechanisms if using multithreading)
14. **Scenario, Quality, & Resource Plans** (best/worst/realistic cases, staffing/cost allocations, quality gates 1-5)
15. **Documentation & Prompt Engineering** (README outline 15+ sections, prompt log structure organized by category, docstring standards ≥70%)
16. **Package Organization (NEW v3.1)** (Package structure with __init__.py locations, Directory organization: src/, tests/, docs/, config/, Relative import strategy, pyproject.toml / setup.py configuration)
17. **Evidence & Verification Matrix** (table with ≥20 entries minimum / ≥30 for 90+, include package organization, parallel processing, and modular design verification items)
18. **AI Handoff Summary** (machine-readable structured output)

Use `_TBD_` for unknown details and highlight any assumptions.

### Decision Matrix Format Example

```markdown
| Decision | Option | Pros | Cons | Risk | Recommendation |
|----------|--------|------|------|------|----------------|
| API Framework | FastAPI | Async, auto-docs, modern | Learning curve | Low | ✅ |
| API Framework | Django REST | Mature, rapid auth | Heavy for small projects | Medium |  |
| API Framework | Flask | Simple, flexible | Manual docs, no async | Medium |  |
```

### KPI Table Format Example

```markdown
| KPI ID | Metric | Target | Verification Command | Expected Output | Artifact Path | Owner |
|--------|--------|--------|---------------------|-----------------|---------------|-------|
| KPI-001 | Test Coverage | ≥85% | `pytest --cov=app` | TOTAL ... 85% | htmlcov/index.html | Dev Team |
| KPI-002 | API Response Time | <2s (p95) | `pytest tests/test_performance.py` | p95: 1.8s PASSED | test results | Backend Dev |
```

### Evidence Matrix Format Example

```markdown
| Evidence ID | Claim | Verification Command | Expected Output | Artifact Path | Status |
|-------------|-------|---------------------|-----------------|---------------|--------|
| EV-001 | Package is pip-installable | `pip install . && python -m project_name --version` | Version: 0.1.0 | pyproject.toml | ✅ |
| EV-002 | Test coverage ≥85% | `pytest --cov=app --cov-report=html` | TOTAL ... 87% | htmlcov/ | ✅ |
| EV-003 | No hardcoded secrets | `grep -r "api_key\|password" app/ --exclude-dir=venv` | (empty output) | Source code | ✅ |
```

### Installation Matrix Format Example (10+ Steps Required)

```markdown
| Step | Action | Verification Command | Expected Output | Troubleshooting |
|------|--------|---------------------|-----------------|-----------------|
| 1 | Check Python version | `python --version` | Python 3.11+ | Install Python 3.11 |
| 2 | Clone repository | `git clone [repo]` | Cloning into... done | Check git installed |
| 3 | Create virtual env | `python -m venv venv` | (no output) | Check write permissions |
| 4 | Activate venv | `source venv/bin/activate` | (venv) prefix in prompt | On Windows use venv\Scripts\activate |
| 5 | Install package | `pip install -e .` | Successfully installed | Check pyproject.toml exists |
| 6 | Verify installation | `python -m project_name --version` | Version: 0.1.0 | Check __main__.py |
| 7 | Configure environment | `cp .env.example .env` | (no output) | Fill in API keys if needed |
| 8 | Run tests | `pytest tests/` | X passed | Fix any failures |
| 9 | Check config loads | `python -c "from app.config import settings; print(settings)"` | Settings(...) | Check config.py |
| 10 | Run application | `python -m project_name` | Application started | Check logs/ for errors |
```

### Usability Analysis (Project-Type-Dependent)

**FOR WEB UI PROJECTS**: Nielsen's 10 Usability Heuristics Table

```markdown
| Heuristic | Application to This Project | Implementation | Evidence |
|-----------|----------------------------|----------------|----------|
| 1. Visibility of system status | Show progress bars during data processing | Progress indicators in UI | screenshots/progress_bar.png |
| 2. Match between system and real world | Use familiar terminology (not technical jargon) | User-friendly labels | documentation/terminology.md |
| 3. User control and freedom | Provide "Cancel" for long operations | Cancel buttons + undo | screenshots/cancel_operation.png |
| 4. Consistency and standards | Consistent color scheme and button placement | Style guide followed | assets/style_guide.md |
| 5. Error prevention | Input validation before submission | Client-side validation | screenshots/validation_errors.png |
| 6. Recognition rather than recall | Auto-complete for common inputs | Dropdown suggestions | screenshots/autocomplete.png |
| 7. Flexibility and efficiency | Keyboard shortcuts for power users | Shortcut documentation | README.md#keyboard-shortcuts |
| 8. Aesthetic and minimalist design | Clean UI with no unnecessary elements | Wireframes reviewed | documentation/wireframes/ |
| 9. Help users recognize, diagnose, and recover from errors | Clear error messages with solutions | Error handling guide | documentation/error_messages.md |
| 10. Help and documentation | Comprehensive README and help section | README.md + in-app help | Comprehensive README |
```

**FOR CLI PROJECTS**: CLI Usability Principles

```markdown
| Principle | Application to This Project | Implementation | Evidence |
|-----------|----------------------------|----------------|----------|
| Clear help text | Comprehensive `--help` with examples | argparse/Click with detailed help | `python -m app --help` output |
| Intuitive commands | Verb-noun pattern (e.g., `process route`) | Command structure design | CLI documentation |
| Helpful error messages | Specific errors with suggested actions | Custom error handlers | screenshots/errors.png |
| Consistent flags | Standard flags (-v, --verbose, -h, --help) | Flag naming convention | Command reference |
| Progress indicators | Show progress for long operations | tqdm or rich progress bars | screenshots/progress.png |
```

**FOR API PROJECTS**: API Usability Principles

```markdown
| Principle | Application to This Project | Implementation | Evidence |
|-----------|----------------------------|----------------|----------|
| Consistent endpoints | RESTful naming conventions | API design standards | OpenAPI spec |
| Clear documentation | Swagger/OpenAPI with examples | FastAPI auto-docs | /docs endpoint |
| Helpful error responses | Structured error JSON with codes | Error middleware | API error guide |
| Versioning strategy | URL versioning (/api/v1/) | Version routing | API structure |
| Rate limiting transparency | Clear rate limit headers | Rate limit middleware | Response headers |
```

### ISO/IEC 25010 Quality Characteristics (Required NFRs)

Ensure Non-Functional Requirements cover ALL 8 characteristics:

```markdown
| Characteristic | NFR | Target | Verification | KPI |
|----------------|-----|--------|--------------|-----|
| Functional Suitability | Feature completeness | All 8 FRs implemented | Manual checklist | 100% FR coverage |
| Performance Efficiency | Response time | API <2s (p95) | pytest performance tests | KPI-002 |
| Compatibility | Cross-platform | Works on Win/Mac/Linux | Test on 3 OS | Manual validation |
| Usability | Learnability | New user productive in <15min | User testing | Time-to-first-success |
| Reliability | Fault tolerance | Graceful degradation on API failure | Chaos testing | Uptime % |
| Security | Confidentiality | No secrets in code | Secret scanner | grep results |
| Maintainability | Modularity | Files <150 LOC | LOC counter | % files <150 LOC |
| Portability | Installability | pip install succeeds | Installation test | Success rate |
```

---

# SECTION 2: MISSIONS TEMPLATES (5 Project Types)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  🎯 MISSIONS TEMPLATES - SELECT BASED ON PROJECT TYPE                       ║
║                                                                               ║
║  Choose the mission template that matches your project type from interview  ║
║  Section A. Each template has 30+ missions customized for that project type.║
║                                                                               ║
║  Available Templates:                                                        ║
║  • 2.1: Full-Stack Web Application (UI + Backend)                           ║
║  • 2.2: CLI-Only Application (Terminal tool)                                ║
║  • 2.3: Backend REST API (No frontend)                                      ║
║  • 2.4: Data Pipeline / ETL (Data processing)                               ║
║  • 2.5: Machine Learning Model (Training/Inference)                         ║
║                                                                               ║
║  Target: 20-60 missions (adaptive based on project complexity)              ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## General Mission Table Structure

**Column Headers** (for all templates):
- **Mission ID**: Unique identifier (M0, M1, M2.0, GATE 1, etc.)
- **Title**: Brief descriptive name
- **Objective**: What this mission accomplishes
- **Rubric Focus**: Which rubric category this contributes to (20pts max)
- **Definition of Done**: Checklist with ≥3 verifiable items
- **Self-Verification Command**: Exact command to verify completion
- **Expected Evidence**: What artifacts prove completion
- **Time Estimate**: Realistic hours estimate
- **Status**: Pending / In Progress / Complete
- **Dependencies**: Mission IDs that must complete first (format: "M2.0, M3.1" or "None (kickoff)")
- **Blocks**: Mission IDs waiting for this one (format: "M7.2, M7.9" or "None (final)")

---

## 2.1: FULL-STACK WEB APPLICATION MISSIONS

*Use this template for projects with both UI and backend components*

| ID | Title | Objective | Rubric Focus | Definition of Done | Self-Verify Command | Evidence | Time | Status | Dependencies | Blocks |
|----|-------|-----------|--------------|--------------------|--------------------|----------|------|--------|--------------|--------|
| **M0** | Intake & Kickoff | Confirm project scope | N/A | ✅ Kickoff Agent interview complete<br>✅ PRD, Missions, Progress Tracker, .claude generated<br>✅ All `_TBD_` items resolved | N/A | PRD_project.md, Missions_project.md, PROGRESS_TRACKER.md, .claude | 2-3h | Pending | None (kickoff) | M1 |
| **M1** | PRD Finalization | Complete comprehensive PRD | Project Docs (20pts) | ✅ All 17 sections complete<br>✅ Comprehensive KPIs with verification commands<br>✅ Evidence matrix filled (≥30 entries)<br>✅ Usability analysis (project-appropriate)<br>✅ `.claude` updated (Section 5: Mission Progress) | `grep -c "^## " documentation/PRD.md` → ≥17 | PRD.md | 4-6h | Pending | M0 | GATE 1, M2.0-M2.2 |
| **GATE 1** | 🚪 PRD Quality Gate | Verify PRD meets standards | N/A | ✅ Self-assessment ≥18/20 in "Project Documentation"<br>✅ Evidence matrix complete<br>✅ All verification commands testable | Manual review against rubric | Self-assessment score | 30min | Pending | M1 | M3, M4.1 |
| **M2.0** | Package Setup (NEW v3.1) | Create installable Python package with proper organization | Structure (12pts) | ✅ pyproject.toml or setup.py exists with complete metadata (name, version, dependencies, entry points)<br>✅ src/project_name structure<br>✅ __init__.py in EVERY package and subpackage directory (Chapter 15)<br>✅ __main__.py for CLI entry<br>✅ Relative imports used within packages<br>✅ `pip install -e .` works (editable install)<br>✅ No circular dependencies<br>✅ `.claude` updated | `pip install -e . && python -m project_name --version && find src -type d -exec test -f {}/__init__.py \;` → Success | pyproject.toml, src/, all __init__.py files | 2-3h | Pending | GATE 1 | M2.1, M4.1, M7.1+ |
| **M2.1** | Repo Structure | Create modular folders | Structure (15pts) | ✅ 7+ directories (src, tests, docs, data, config, scripts, notebooks)<br>✅ .gitignore (≥15 patterns)<br>✅ README skeleton with basic sections<br>✅ requirements.txt<br>✅ `.claude` updated | `ls -d */ \| wc -l` → ≥7 | Clean directory tree | 1h | Pending | M2.0 | M2.2, M3 |
| **M2.2** | Architecture Doc (NEW v3.1) | Draft C4 diagrams + ADRs + Building Blocks | Architecture & Design (6pts) | ✅ 4 C4 levels (Context, Container, Component, Deployment)<br>✅ ≥7 ADRs with alternatives and trade-offs<br>✅ API/data contracts documented<br>✅ Building block structure documented (Input/Output/Setup data for major components - Chapter 17)<br>✅ SRP applied: Each component has single responsibility documented<br>✅ Separation of Concerns: Business logic, data access, presentation layers defined<br>✅ Parallel processing strategy: CPU-bound vs I/O-bound operations identified (Chapter 16)<br>✅ `.claude` updated | `grep -c "mermaid" docs/Architecture.md` → ≥4 | Architecture.md with building blocks section | 4-5h | Pending | M2.1 | M5, M6, GATE 2 |
| **M3** | Config & Security | Set up .env, scan for secrets | Config (10pts) | ✅ .env.example (≥5 vars with comments)<br>✅ .gitignore complete<br>✅ No hardcoded secrets<br>✅ Config module (src/project/config.py)<br>✅ `.claude` updated | `grep -r "api_key" src/ \| grep -v getenv` → empty | .env.example, config.py | 2h | Pending | GATE 1, M2.1 | M3.1 |
| **M3.1** | YAML Config | Create centralized config | Config (10pts) | ✅ config/settings.yaml (≥20 lines)<br>✅ All params in YAML<br>✅ Config loader module<br>✅ `.claude` updated | `wc -l config/settings.yaml` → ≥20 | settings.yaml | 1-2h | Pending | M3 | M3.2, M7.x |
| **M3.2** | Logging Setup | Implement comprehensive logging | Config (10pts) | ✅ Python logging configured<br>✅ logs/ directory<br>✅ Format: `TIMESTAMP \| LEVEL \| MODULE \| EVENT \| MESSAGE`<br>✅ Transaction ID tracking<br>✅ Events: Scheduler, Orchestrator, Agent, Search, Fetch, Error, Retry<br>✅ Thread-safe logging.getLogger()<br>✅ `.claude` updated | `ls logs/*.log && grep "Orchestrator" logs/*.log` → matches | logs/, logging_config.py | 1-2h | Pending | M3.1 | M3.3, GATE 2, M7.x |
| **M3.3** | Quality Standards Setup (CRITICAL) | Configure linting, CI/CD, style guide, pre-commit hooks | Structure (12pts) + Config (10pts) | ✅ **Linting configured**: .pylintrc or .flake8 file with project standards, `pylint src/` runs successfully<br>✅ **CI/CD pipeline**: .github/workflows/test.yml (or .gitlab-ci.yml) that runs tests, linting, coverage checks<br>✅ **Style guide**: CONTRIBUTING.md or STYLE_GUIDE.md with code standards, naming conventions, commit message format, PR process<br>✅ **Pre-commit hooks**: .pre-commit-config.yaml with hooks for black, pylint, mypy, trailing whitespace; `pre-commit install && pre-commit run --all-files` passes<br>✅ **Code formatter**: black configured (pyproject.toml [tool.black] section), all code formatted<br>✅ **Type checking**: mypy configured (mypy.ini or pyproject.toml [tool.mypy]), basic type hints added<br>✅ CI/CD pipeline runs successfully on test commit<br>✅ `.claude` updated | `ls .pylintrc .github/workflows/test.yml CONTRIBUTING.md .pre-commit-config.yaml && pylint src/ --exit-zero && black --check src/ && mypy src/ --install-types --non-interactive` → files exist, checks pass | .pylintrc, .github/workflows/test.yml, CONTRIBUTING.md, .pre-commit-config.yaml | 3-4h | Pending | M3.2, M2.1 | GATE 2, M4.1 |
| **GATE 2** | 🚪 Architecture Gate | Verify setup works | N/A | ✅ Dependencies install<br>✅ Config loads<br>✅ Entry points exist<br>✅ Quality checks pass (linting, formatting, CI/CD) | `pip install -r requirements.txt && pylint src/ --exit-zero && pytest --version` → Success | install_log.txt, CI/CD pass | 30min | Pending | M2.2, M3.2, M3.3 | M4.1, M5 |
| **M4.1** | Test Framework | Set up pytest | Testing (15pts) | ✅ tests/ structure<br>✅ conftest.py with fixtures<br>✅ pytest.ini<br>✅ Sample test passes<br>✅ `.claude` updated | `pytest tests/test_sample.py` → 1 passed | tests/, pytest.ini | 1h | Pending | GATE 2, M2.0 | M4.2 |
| **M4.2** | Unit Tests | Write ≥20 unit tests | Testing (15pts) | ✅ ≥20 test functions<br>✅ All tests pass<br>✅ Coverage ≥70% (≥85% for 90+)<br>✅ ≥5 edge case tests<br>✅ `.claude` updated | `pytest --cov=src` → TOTAL ≥70% | tests/test_*.py (≥10 files) | 4-5h | Pending | M4.1 | GATE 3 |
| **GATE 3** | 🚪 Testing Gate | Verify test suite | N/A | ✅ All tests pass<br>✅ Coverage meets target<br>✅ Report generated | `pytest` → 0 failures | htmlcov/ | 15min | Pending | M4.2 | M7.1+ |
| **M5** | Research Setup | Create experiment plan | Research (15pts) | ✅ Parameter sensitivity doc (≥3 params)<br>✅ Jupyter notebook (≥8 cells)<br>✅ Data collection scripts<br>✅ `.claude` updated | `ls docs/Parameter_Sensitivity.md` → exists | notebooks/ | 2-3h | Pending | GATE 2 | M8.1 |
| **M6** | UX/Extensibility Docs | Write guides | UI/UX (10pts) | ✅ Usability analysis (project-appropriate)<br>✅ Extensibility guide complete<br>✅ ≥3 extension points documented<br>✅ `.claude` updated | `grep -c "## Extension Point" docs/Extensibility_Guide.md` → ≥3 | Extensibility_Guide.md | 2-3h | Pending | M2.2 | M6.1, M6.2 |
| **M6.1** | Extensibility Implementation (CRITICAL for HW2 feedback) | Implement plugin/extension system | Architecture (6pts) + Structure (12pts) | ✅ **Plugin architecture implemented** (not just documented)<br>✅ Plugin base class or interface defined (e.g., `PluginInterface` with `register()`, `execute()` methods)<br>✅ Plugin discovery mechanism (scan plugins/ directory or use entry points in pyproject.toml)<br>✅ ≥2 example plugins implemented (e.g., CustomFormatter, CustomValidator)<br>✅ Plugin loading and execution works: `python -m project_name --plugin custom_plugin`<br>✅ Plugins documented in docs/Extensibility_Guide.md with code examples<br>✅ Tests for plugin system: tests/test_plugins.py (plugin loading, execution, error handling)<br>✅ `.claude` updated | `ls src/plugins/__init__.py && python -c "from src.plugins import load_plugins; print(load_plugins())" && pytest tests/test_plugins.py -v` → plugin system works, tests pass | src/plugins/, tests/test_plugins.py, docs/Extensibility_Guide.md | 3-4h | Pending | M6, M2.2 | M6.2, M7.1 |
| **M6.2** | JSON Schema Definition | Define data contracts | Structure (15pts) | ✅ ≥3 JSON schema files in docs/contracts/<br>✅ Valid JSON Schema Draft-07<br>✅ Include: $schema, type, properties, required<br>✅ Documented in Architecture.md<br>✅ Tests validate against schemas<br>✅ `.claude` updated | `ls docs/contracts/*.json \| wc -l && jq empty docs/contracts/*.json` → ≥3, valid | contracts/*.json | 1h | Pending | M6, M6.1 | M7.1-M7.8 |
| **M7.1** | Core Feature Implementation | Business logic | Structure (15pts) | ✅ Service layer complete<br>✅ API routes implemented<br>✅ All FR tests pass<br>✅ Test file tests/test_core.py (≥3 tests)<br>✅ `.claude` updated | `pytest tests/test_fr_*.py` → All pass | src/services/, tests/test_core.py | 6-8h | Pending | M2.0, M3.1, M6.1, GATE 3 | M7.2, M7.9 |
| **M7.2** | UI Implementation | Frontend screens | UI/UX (10pts) | ✅ UI components complete<br>✅ All user stories have UI<br>✅ Manual testing checklist<br>✅ Test file tests/test_ui.py (≥3 tests)<br>✅ `.claude` updated | `ls ui/*.py && pytest tests/test_ui.py -v` → pass | ui/, tests/test_ui.py | 4-6h | Pending | M7.1, M6.1 | M7.5 |
| **M7.3** | Error Handling | Exception handling | Testing (15pts) | ✅ All error scenarios tested<br>✅ Try/except in controllers<br>✅ Graceful degradation<br>✅ Error logging with TID + context<br>✅ Test file tests/test_errors.py (exception injection)<br>✅ `.claude` updated | `grep -r "test_error" tests/ \| wc -l` → ≥5 | tests/test_errors.py | 3-4h | Pending | M7.1, M7.2 | M7.4 |
| **M7.4** | Integration Testing | End-to-end flows | Testing (15pts) | ✅ API + UI + DB integration tests<br>✅ All user story flows tested<br>✅ Tests pass<br>✅ `.claude` updated | `pytest tests/test_integration*.py` → All pass | tests/test_integration*.py | 2-3h | Pending | M7.3 | GATE 4 |
| **M7.5** | Screenshot Capture | Document UI states | UI/UX (10pts) | ✅ ≥20 screenshots<br>✅ All UI states covered<br>✅ High res (1920x1080+)<br>✅ `.claude` updated | `find docs -name "screenshot_*.png" \| wc -l` → ≥20 | docs/screenshots/ | 2h | Pending | M7.2 | M8.3 |
| **M7.6** | Demo Script | 5-min walkthrough | README (15pts) | ✅ Step-by-step script<br>✅ Demo data prepared<br>✅ Video (optional)<br>✅ `.claude` updated | Manual rehearsal → <5min | Demo_Script.md | 1h | Pending | M7.4 | M9.1 |
| **M7.7a** | File-Based Interfaces | JSON contracts | Structure (15pts) | ✅ FileInterface module<br>✅ JSON files in data/ and output/<br>✅ Contracts documented<br>✅ Test file tests/test_file_interface.py (JSON validation, edge cases)<br>✅ `.claude` updated | `ls data/*.json && pytest tests/test_file_interface.py -v` → valid, pass | file_interface.py, tests/ | 2-3h | Pending | M6.1 | M7.1+ |
| **M7.7b** | LLM Abstraction | LLM client abstraction | Structure (15pts) | ✅ LLMClient abstract class<br>✅ Implementations (Ollama, OpenAI, Mock)<br>✅ Factory pattern, config-driven<br>✅ Timeout, retry (3×: 1s/2s/4s), error propagation<br>✅ Test file tests/test_llm.py (timeout, retry, fallback)<br>✅ `.claude` updated | `pytest tests/test_llm.py -v` → pass | tools/llm_client.py, tests/ | 3-4h | Pending | M3.1 | M7.1+ |
| **M7.7c** | Search+Fetch Tools | Tool separation | Structure (15pts) | ✅ SearchTool module<br>✅ FetchTool module<br>✅ Agents use tools<br>✅ Logging queries/URLs<br>✅ Test file tests/test_search_fetch.py (timeout handling)<br>✅ `.claude` updated | `pytest tests/test_search_fetch.py -v && ls src/tools/search.py` → pass, exists | tools/search.py, fetch.py | 2-3h | Pending | M3.2 | M7.1+ |
| **M7.7d** | Parallel Processing (NEW v3.1) | Multiprocessing vs Multithreading | Architecture (6pts) | ✅ Correct choice: ProcessPoolExecutor for CPU-bound tasks OR ThreadPoolExecutor for I/O-bound tasks (Chapter 16)<br>✅ Thread safety: queue.Queue for thread-safe data sharing (not regular lists/dicts)<br>✅ Context managers (with statements) for locks if needed<br>✅ Communication via Queue between threads/processes<br>✅ Exception handling on future.result()<br>✅ Logging with Thread/Process IDs + TIDs<br>✅ Test file tests/test_parallel.py (thread safety, exception propagation)<br>✅ Architecture.md documents parallelization strategy<br>✅ `.claude` updated | `grep -E "ThreadPoolExecutor\|ProcessPoolExecutor" src/ -r && pytest tests/test_parallel.py -v` → found, pass | orchestration/parallel.py, tests/test_parallel.py | 4-5h | Pending | M2.2, M3.2, M7.1 | M7.4 |
| **GATE 4** | 🚪 Feature Gate | Verify features | N/A | ✅ All user stories tested<br>✅ Preflight passes<br>✅ Screenshots ≥20 | `python scripts/preflight.py` → All pass | preflight_output.log | 30min | Pending | M7.4, M7.5, M7.6 | M8.1 |
| **M8.1** | Research Analysis | Run experiments | Research (15pts) | ✅ All experiments run<br>✅ Data collected (CSV)<br>✅ Notebook analysis + plots<br>✅ `.claude` updated | `ls notebooks/data/*.csv` → ≥1 | notebooks/*.ipynb | 3-4h | Pending | M5, GATE 4 | M8.2 |
| **M8.2** | Visualization | Publication plots | Research (15pts) | ✅ ≥4 plot types (bar, line, scatter, heatmap)<br>✅ Labeled, high res (≥300 DPI)<br>✅ `.claude` updated | `find notebooks -name "*.png" \| wc -l` → ≥4 | plots/*.png | 2h | Pending | M8.1 | M8.3 |
| **M8.3** | README Polish | Complete sections | README (15pts) | ✅ All 15 sections complete<br>✅ Comprehensive documentation<br>✅ Screenshots embedded<br>✅ `.claude` updated | `grep -c "^## " README.md` → ≥15 | README.md | 2-3h | Pending | M7.5, M8.2 | M8.4 |
| **M8.4** | Documentation Review | Cross-check docs | All | ✅ All paths valid<br>✅ All commands tested<br>✅ No broken links<br>✅ `.claude` updated | `python scripts/validate_docs.py` → 0 errors | All docs/*.md | 1-2h | Pending | M8.3 | M9.1 |
| **M9.1** | Pre-Submission Checks | Run preflight | All | ✅ 33 checklist items pass<br>✅ Self-eval ≥90/100<br>✅ Evidence matrix complete<br>✅ `.claude` updated | `python scripts/preflight.py` → All pass | preflight_log.txt | 1h | Pending | M8.4, M7.6 | M9.2 |
| **M9.2** | Self-Evaluation + Checklist | Evaluation report | All | ✅ PROJECT_EVALUATION_REPORT.md created<br>✅ Self-score ≥90/100<br>✅ All rubric categories scored<br>✅ docs/submission_checklist.md created<br>✅ Map ALL guideline items (sections 1-12) to evidence<br>✅ Format: `- [ ] Item → Evidence: path`<br>✅ Verification: `grep -c "✅" docs/submission_checklist.md` ≥50<br>✅ `.claude` updated | `ls PROJECT_EVALUATION_REPORT.md docs/submission_checklist.md` → both exist | REPORT.md, checklist.md | 2-3h | Pending | M9.1 | M9.3 |
| **M9.3** | Final Verification | Clean up | All | ✅ Git history (≥15 commits)<br>✅ No large files (>1MB)<br>✅ Spell-check markdown<br>✅ `.claude` updated | `git log --oneline \| wc -l` → ≥15 | git log | 1h | Pending | M9.2 | GATE 5 |
| **GATE 5** | 🚪 Submission Gate | Final quality check | N/A | ✅ Self-score ≥90/100<br>✅ All evidence verified<br>✅ Ready for grader | Manual checklist review | REPORT.md | 30min | Pending | M9.3 | M10 |
| **M10** | Submission | Package and submit | N/A | ✅ All files in repo<br>✅ README accurate<br>✅ Grader install <15min<br>✅ `.claude` final update | Test in clean environment | Submission bundle | 30min | Pending | GATE 5 | None (final) |

**TOTAL MISSIONS: 37** (M0, M1, M2.0-M2.2, M3-M3.3, M4.1-M4.2, M5, M6-M6.2, M7.1-M7.7d, M8.1-M8.4, M9.1-M9.3, M10, + 5 Gates)

**NEW in v3.1 based on professor feedback:**
- **M3.3**: Quality Standards Setup (linting, CI/CD, style guide, pre-commit hooks) - CRITICAL addition based on consistent deductions in HW1, HW2, HW3
- **M6.1**: Extensibility Implementation (actual plugin system, not just docs) - addresses HW2 feedback about documented but not implemented plugin architecture

---

## 2.2: CLI-ONLY APPLICATION MISSIONS

*Use this template for terminal-based tools without GUI (like HW4 Route Enrichment)*

**Key Differences from Full-Stack:**
- **REMOVED**: M7.2 (UI Implementation), M7.5 (Screenshot Capture)
- **ADDED**: M7.9 (CLI Help & Documentation)
- **MODIFIED**: Focus on CLI interface quality, help text, error messages

| ID | Title | Objective | Rubric Focus | Definition of Done | Self-Verify Command | Evidence | Time | Status | Dependencies | Blocks |
|----|-------|-----------|--------------|--------------------|--------------------|----------|------|--------|--------------|--------|
| **M0-M6.2** | *(Same as Full-Stack template - Planning, Architecture, Config, Quality Standards, Testing, Research, Extensibility, Schemas)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |
| **M7.1** | Core Business Logic | Implement main functionality | Structure (15pts) | ✅ Service layer complete<br>✅ All FR tests pass<br>✅ Test file tests/test_core.py (≥3 tests + edge cases)<br>✅ `.claude` updated | `pytest tests/test_core.py -v` → All pass | src/services/, tests/test_core.py | 6-8h | Pending | M2.0, M3.1, M6.2, GATE 3 | M7.3, M7.9 |
| **M7.3** | Orchestrator/Controller | Coordinate components | Structure (15pts) | ✅ Orchestrator implemented<br>✅ Worker coordination logic<br>✅ Exception handling, graceful degradation<br>✅ Test file tests/test_orchestrator.py (worker exceptions)<br>✅ `.claude` updated | `pytest tests/test_orchestrator.py -v` → pass | orchestration/orchestrator.py, tests/ | 4-6h | Pending | M7.1, M3.2 | M7.4, M7.7d |
| **M7.4** | Integration Testing | End-to-end flows | Testing (15pts) | ✅ Full pipeline tests (input → processing → output)<br>✅ All user story flows tested<br>✅ Tests pass<br>✅ `.claude` updated | `pytest tests/test_integration*.py` → All pass | tests/test_integration*.py | 2-3h | Pending | M7.3, M7.7a-d | M7.6, GATE 4 |
| **M7.6** | Demo Script | CLI walkthrough | README (15pts) | ✅ Step-by-step CLI commands<br>✅ Sample input data<br>✅ Expected output shown<br>✅ `.claude` updated | Manual run → matches expected output | Demo_Script.md | 1h | Pending | M7.4, M7.9 | M9.1 |
| **M7.7a-d** | *(Same as Full-Stack: File Interfaces, LLM Abstraction, Search+Fetch, Concurrency)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |
| **M7.9** | CLI Interface & Help | Command-line UX | UI/UX (10pts) + README (15pts) | ✅ Comprehensive `--help` output<br>✅ Argparse or Click with subcommands<br>✅ User-friendly error messages<br>✅ Examples in help text<br>✅ Exit codes documented (0=success, 1=error, 2=invalid args)<br>✅ Test file tests/test_cli.py (argument parsing, help output)<br>✅ `.claude` updated | `python -m project_name --help \| wc -l` → ≥20 lines | __main__.py, tests/test_cli.py | 2-3h | Pending | M7.1 | M7.4, M7.6 |
| **M8.1-M8.4** | *(Same as Full-Stack: Research Analysis, Visualization, README Polish, Doc Review)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |
| **M8.3** | README Polish (CLI-specific) | Complete sections | README (15pts) | ✅ All 15 sections<br>✅ ≥200 lines<br>✅ **CLI usage examples with input/output**<br>✅ **Terminal screenshots using `screenshot_terminal.sh` or similar** (≥8 images)<br>✅ `.claude` updated | `wc -l README.md && find docs -name "terminal_*.png" \| wc -l` → ≥200, ≥8 | README.md, terminal screenshots | 2-3h | Pending | M7.9, M8.2 | M8.4 |
| **M9.1-M10** | *(Same as Full-Stack: Pre-Submission, Evaluation, Final Verification, Submission)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |

**TOTAL MISSIONS: 35** (Removed M7.2, M7.5; Added M7.9, M3.3 Quality Standards, M6.1 Extensibility; same core structure as Full-Stack with CLI-specific adaptations)

**NOTE on Screenshots for CLI**: While UI screenshots are removed, you MUST provide terminal screenshots showing:
- Help output (`--help`)
- Example runs with sample data
- Error handling (invalid input → clear error message)
- Success output
Target ≥8 terminal screenshots embedded in README for 90+ score.

---

## 2.3: BACKEND REST API MISSIONS

*Use this template for API-only projects (no frontend UI)*

**Key Differences from Full-Stack:**
- **REMOVED**: M7.2 (UI Implementation), M7.5 (Screenshot Capture)
- **ADDED**: M7.8 (API Documentation & Swagger), M7.10 (API Load Testing)
- **MODIFIED**: M7.1 focuses on API endpoints, authentication, request validation
- **INCLUDES**: M3.3 (Quality Standards), M6.1 (Extensibility Implementation) - same as Full-Stack

| ID | Title | Objective | Rubric Focus | Definition of Done | Self-Verify Command | Evidence | Time | Status | Dependencies | Blocks |
|----|-------|-----------|--------------|--------------------|--------------------|----------|------|--------|--------------|--------|
| **M0-M6.2** | *(Same as Full-Stack - Planning, Architecture, Config, Quality Standards, Testing, Research, Extensibility, Schemas)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |
| **M7.1** | API Endpoints - Core Resources | Implement REST routes | Structure (15pts) | ✅ CRUD endpoints for main resources<br>✅ Request validation (Pydantic models)<br>✅ Response schemas documented<br>✅ Test file tests/test_api_endpoints.py (≥3 tests per endpoint)<br>✅ `.claude` updated | `pytest tests/test_api_endpoints.py -v` → All pass | api/routes/, tests/test_api_endpoints.py | 6-8h | Pending | M2.0, M3.1, M6.1, GATE 3 | M7.3, M7.8 |
| **M7.3** | Authentication & Authorization | API security | Security (10pts) + Structure (15pts) | ✅ JWT or API key authentication<br>✅ Role-based access control (RBAC)<br>✅ Protected endpoints require auth<br>✅ Test file tests/test_auth.py (valid/invalid tokens, permissions)<br>✅ `.claude` updated | `pytest tests/test_auth.py -v` → pass | api/auth/, tests/test_auth.py | 4-5h | Pending | M7.1 | M7.4 |
| **M7.4** | Integration Testing | API end-to-end | Testing (15pts) | ✅ Full request/response cycle tests<br>✅ Database integration<br>✅ Authentication flow tests<br>✅ `.claude` updated | `pytest tests/test_integration_api.py` → All pass | tests/test_integration_api.py | 2-3h | Pending | M7.3, M7.7a-d | M7.8, GATE 4 |
| **M7.6** | Demo Script & Postman Collection | API walkthrough | README (15pts) | ✅ Postman collection exported<br>✅ cURL examples in script<br>✅ Sample requests/responses documented<br>✅ `.claude` updated | `ls postman_collection.json && cat Demo_Script.md` → exists, examples present | postman_collection.json, Demo_Script.md | 1-2h | Pending | M7.4, M7.8 | M9.1 |
| **M7.7a-d** | *(Same as Full-Stack: File Interfaces, LLM Abstraction, Search+Fetch, Concurrency)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |
| **M7.8** | API Documentation & Swagger | OpenAPI spec | README (15pts) + Structure (15pts) | ✅ Swagger UI accessible (FastAPI auto-docs or Flask-RESTX)<br>✅ All endpoints documented<br>✅ Request/response examples<br>✅ Authentication requirements noted<br>✅ **Screenshots of Swagger UI** (≥8 images for different endpoints)<br>✅ `.claude` updated | `curl http://localhost:8000/docs \| grep "Swagger"` → found | docs/api_screenshots/, openapi.json | 2-3h | Pending | M7.1, M7.3 | M7.6, M8.3 |
| **M7.10** | API Load Testing | Performance validation | Performance (subset of Testing 15pts) | ✅ Load test with ApacheBench or Locust<br>✅ Test ≥100 concurrent requests<br>✅ p95 latency <2s verified<br>✅ Results documented<br>✅ `.claude` updated | `ab -n 1000 -c 100 http://localhost:8000/api/resource \| grep "requests per second"` → results logged | docs/load_test_results.md | 1-2h | Pending | M7.4 | M8.3 |
| **M8.1-M8.2** | *(Same as Full-Stack: Research Analysis, Visualization)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |
| **M8.3** | README Polish (API-specific) | Complete sections | README (15pts) | ✅ All 15 sections<br>✅ ≥200 lines<br>✅ **API endpoint documentation** (table of routes, methods, descriptions)<br>✅ **Swagger UI screenshots embedded** (≥8 images)<br>✅ Authentication setup guide<br>✅ `.claude` updated | `wc -l README.md && grep -c "## Endpoints" README.md` → ≥200, ≥1 | README.md | 2-3h | Pending | M7.8, M7.10, M8.2 | M8.4 |
| **M8.4-M10** | *(Same as Full-Stack: Doc Review, Pre-Submission, Evaluation, Final Verification, Submission)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |

**TOTAL MISSIONS: 37** (Removed M7.2, M7.5; Added M7.8, M7.10, M3.3 Quality Standards, M6.1 Extensibility; same core structure)

**NOTE on Screenshots for API**: Since no frontend UI, provide:
- Swagger UI screenshots (different endpoints, request/response examples) - ≥8 images
- Postman collection screenshots (optional but helpful)
- Terminal screenshots of cURL commands and responses - ≥3 images
Target ≥8 total screenshots (Swagger + terminal) for 90+ score.

---

## 2.4: DATA PIPELINE / ETL MISSIONS

*Use this template for data processing pipelines (ingestion → transformation → loading)*

**Key Differences from Full-Stack:**
- **REMOVED**: M7.2 (UI), M7.5 (Screenshots)
- **REPLACED M7.1-M7.6** with: M7.1 (Ingestion), M7.2 (Transformation), M7.3 (Loading), M7.4 (Validation), M7.5 (Orchestration), M7.6 (Monitoring)
- **FOCUS**: Data quality, schema enforcement, error handling, idempotency
- **INCLUDES**: M3.3 (Quality Standards), M6.1 (Extensibility Implementation) - same as Full-Stack

| ID | Title | Objective | Rubric Focus | Definition of Done | Self-Verify Command | Evidence | Time | Status | Dependencies | Blocks |
|----|-------|-----------|--------------|--------------------|--------------------|----------|------|--------|--------------|--------|
| **M0-M6.2** | *(Same as Full-Stack - Planning, Architecture, Config, Quality Standards, Testing, Research, Extensibility, Schemas)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |
| **M7.1** | Data Ingestion | Extract from sources | Structure (15pts) | ✅ Connectors for data sources (API, DB, files)<br>✅ Incremental load logic (only new/changed data)<br>✅ Raw data saved to data/raw/<br>✅ Test file tests/test_ingestion.py (mocked sources, edge cases)<br>✅ `.claude` updated | `pytest tests/test_ingestion.py -v && ls data/raw/*.json` → pass, ≥1 file | src/ingestion/, tests/test_ingestion.py | 5-7h | Pending | M2.0, M3.1, M6.1, GATE 3 | M7.2 |
| **M7.2** | Data Transformation | Apply ETL logic | Structure (15pts) | ✅ Transformation functions (clean, enrich, aggregate)<br>✅ Schema validation against JSON schemas (M6.1)<br>✅ Transformed data in data/processed/<br>✅ Test file tests/test_transformation.py (data quality checks)<br>✅ `.claude` updated | `pytest tests/test_transformation.py -v && ls data/processed/*.json` → pass, ≥1 | src/transformation/, tests/test_transformation.py | 5-7h | Pending | M7.1, M6.1 | M7.3 |
| **M7.3** | Data Loading | Load to target | Structure (15pts) | ✅ Loaders for targets (DB, data warehouse, files)<br>✅ Idempotency (re-run safe, no duplicates)<br>✅ Transaction management<br>✅ Test file tests/test_loading.py (rollback on failure)<br>✅ `.claude` updated | `pytest tests/test_loading.py -v` → pass | src/loading/, tests/test_loading.py | 4-6h | Pending | M7.2 | M7.4 |
| **M7.4** | Data Validation & Quality | Schema enforcement | Testing (15pts) | ✅ Pre-load validation against schemas<br>✅ Data quality rules (nulls, ranges, formats)<br>✅ Rejection handling (bad records logged)<br>✅ Test file tests/test_validation.py (invalid data scenarios)<br>✅ `.claude` updated | `pytest tests/test_validation.py -v && ls data/rejected/*.json` → pass, rejected records exist | src/validation/, tests/test_validation.py | 3-4h | Pending | M7.3, M6.1 | M7.5 |
| **M7.5** | Pipeline Orchestration | Workflow automation | Structure (15pts) | ✅ Pipeline orchestrator (Airflow DAG / Prefect flow / custom scheduler)<br>✅ Task dependencies defined<br>✅ Retry logic with exponential backoff<br>✅ Test file tests/test_pipeline.py (full pipeline run)<br>✅ `.claude` updated | `python -m src.pipeline && pytest tests/test_pipeline.py -v` → pipeline runs, tests pass | src/pipeline/, tests/test_pipeline.py | 4-5h | Pending | M7.4, M7.7d | M7.6 |
| **M7.6** | Monitoring & Alerts | Observability | Config (10pts) + Testing (15pts) | ✅ Logging for each pipeline stage (ingestion/transform/load)<br>✅ Metrics collected (rows processed, errors, runtime)<br>✅ Alerting on failures (email/Slack/log)<br>✅ Dashboard or logs analysis script<br>✅ `.claude` updated | `grep "Pipeline completed" logs/*.log && cat docs/monitoring_dashboard.md` → pipeline logs exist, dashboard documented | logs/, docs/monitoring_dashboard.md | 2-3h | Pending | M7.5, M3.2 | GATE 4 |
| **M7.7a** | *(Same as Full-Stack: File-Based Interfaces)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |
| **M7.7b** | *(Optional for pipelines - remove if no LLM component)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |
| **M7.7c** | *(Same as Full-Stack: Search+Fetch - if pipeline sources require web scraping)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |
| **M7.7d** | *(Same as Full-Stack: Concurrency - parallel processing of data batches)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |
| **M7.8** | Integration Testing | End-to-end pipeline | Testing (15pts) | ✅ Full pipeline test (ingest → transform → load → validate)<br>✅ Data quality verified in target<br>✅ Performance test (1000+ records)<br>✅ `.claude` updated | `pytest tests/test_integration_pipeline.py -v` → pass | tests/test_integration_pipeline.py | 2-3h | Pending | M7.6, M7.7a-d | GATE 4 |
| **GATE 4** | 🚪 Feature Gate | Verify pipeline works | N/A | ✅ Full pipeline runs successfully<br>✅ Data quality checks pass<br>✅ Monitoring active | `python -m src.pipeline --mode=test` → Success | pipeline_output.log | 30min | Pending | M7.8 | M8.1 |
| **M8.1** | Research Analysis (Pipeline-specific) | Pipeline optimization experiments | Research (15pts) | ✅ Experiments: batch size, parallelism, transformation strategies<br>✅ Data collected (runtime, throughput, error rates)<br>✅ Notebook analysis<br>✅ `.claude` updated | `ls notebooks/pipeline_optimization.ipynb` → exists | notebooks/*.ipynb | 3-4h | Pending | M5, GATE 4 | M8.2 |
| **M8.2** | Visualization (Pipeline metrics) | Performance plots | Research (15pts) | ✅ Plots: throughput over time, error rate trends, data quality metrics<br>✅ ≥4 plot types<br>✅ `.claude` updated | `find notebooks -name "*.png" \| wc -l` → ≥4 | plots/*.png | 2h | Pending | M8.1 | M8.3 |
| **M8.3** | README Polish (Pipeline-specific) | Complete sections | README (15pts) | ✅ All 15 sections<br>✅ ≥200 lines<br>✅ **Pipeline architecture diagram** (data flow)<br>✅ **Sample data screenshots or terminal outputs** (≥8 images)<br>✅ Configuration guide (sources, targets, schedules)<br>✅ `.claude` updated | `wc -l README.md && find docs -name "pipeline_*.png" \| wc -l` → ≥200, ≥8 | README.md, diagrams | 2-3h | Pending | M7.6, M8.2 | M8.4 |
| **M8.4-M10** | *(Same as Full-Stack: Doc Review, Pre-Submission, Evaluation, Final Verification, Submission)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |

**TOTAL MISSIONS: 36** (Removed M7.2 UI, M7.5 Screenshots; Replaced M7.1-M7.6 with ETL missions; added M7.8 Integration, M3.3 Quality Standards, M6.1 Extensibility; same core structure)

**NOTE on Screenshots for Pipeline**: Provide diagrams and terminal outputs:
- Pipeline architecture diagram (data flow: sources → stages → targets)
- Sample raw data vs transformed data (before/after)
- Monitoring dashboard or logs
- Terminal screenshots of pipeline runs (success, error handling)
Target ≥8 diagrams + terminal screenshots for 90+ score.

---

## 2.5: MACHINE LEARNING MODEL MISSIONS

*Use this template for ML training/inference projects*

**Key Differences from Full-Stack:**
- **REMOVED**: M7.2 (UI), M7.5 (Screenshots)
- **REPLACED M7.1-M7.6** with: M7.1 (Data Prep), M7.2 (Training), M7.3 (Evaluation), M7.4 (Hyperparameter Tuning), M7.5 (Model Serving), M7.6 (Monitoring)
- **FOCUS**: Model performance, reproducibility, experiment tracking, deployment
- **INCLUDES**: M3.3 (Quality Standards), M6.1 (Extensibility Implementation) - same as Full-Stack

| ID | Title | Objective | Rubric Focus | Definition of Done | Self-Verify Command | Evidence | Time | Status | Dependencies | Blocks |
|----|-------|-----------|--------------|--------------------|--------------------|----------|------|--------|--------------|--------|
| **M0-M6.2** | *(Same as Full-Stack - Planning, Architecture, Config, Quality Standards, Testing, Research, Extensibility, Schemas)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |
| **M7.1** | Data Preparation & Feature Engineering | Prepare training data | Structure (15pts) | ✅ Data loading and cleaning<br>✅ Train/val/test split (70/15/15 or 80/10/10)<br>✅ Feature engineering pipeline<br>✅ Data saved to data/processed/<br>✅ Test file tests/test_data_prep.py (split correctness, no data leakage)<br>✅ `.claude` updated | `pytest tests/test_data_prep.py -v && ls data/processed/` → pass, splits exist | src/data/, tests/test_data_prep.py | 5-7h | Pending | M2.0, M3.1, M6.1, GATE 3 | M7.2 |
| **M7.2** | Model Training | Train baseline + advanced models | Structure (15pts) + Research (15pts) | ✅ Baseline model trained (e.g., Logistic Regression, Random Forest)<br>✅ Advanced model trained (e.g., XGBoost, Neural Net)<br>✅ Training logs with loss/accuracy curves<br>✅ Models saved to models/<br>✅ Test file tests/test_training.py (model convergence, overfitting checks)<br>✅ `.claude` updated | `pytest tests/test_training.py -v && ls models/*.pkl` → pass, ≥2 models | src/training/, models/, tests/test_training.py | 6-8h | Pending | M7.1 | M7.3 |
| **M7.3** | Model Evaluation | Assess performance | Research (15pts) + Testing (15pts) | ✅ Evaluation metrics (accuracy, precision, recall, F1, AUC)<br>✅ Confusion matrix generated<br>✅ Model comparison table<br>✅ Test file tests/test_evaluation.py (metric calculations correct)<br>✅ `.claude` updated | `pytest tests/test_evaluation.py -v && cat results/evaluation_results.json` → pass, results exist | src/evaluation/, results/, tests/test_evaluation.py | 3-4h | Pending | M7.2 | M7.4, M8.1 |
| **M7.4** | Hyperparameter Tuning | Optimize model | Research (15pts) | ✅ Grid search or Bayesian optimization<br>✅ Cross-validation (k-fold, k≥5)<br>✅ Best params documented<br>✅ Tuning results logged (all trials)<br>✅ Test file tests/test_tuning.py (param search correctness)<br>✅ `.claude` updated | `pytest tests/test_tuning.py -v && cat results/tuning_results.json` → pass, best params found | src/tuning/, results/, tests/test_tuning.py | 4-6h | Pending | M7.3 | M7.5 |
| **M7.5** | Model Serving / Inference API | Deploy model | Structure (15pts) | ✅ Inference API (FastAPI or Flask endpoint)<br>✅ Model loading from models/<br>✅ Request validation (input schema)<br>✅ Response format (prediction + confidence)<br>✅ Test file tests/test_serving.py (API endpoint tests)<br>✅ `.claude` updated | `pytest tests/test_serving.py -v && curl -X POST http://localhost:8000/predict -d '{"features": [...]}'` → pass, prediction returned | src/serving/, tests/test_serving.py | 4-5h | Pending | M7.4 | M7.6 |
| **M7.6** | Model Monitoring & Drift Detection | Observability | Config (10pts) + Testing (15pts) | ✅ Prediction logging (inputs, outputs, timestamps)<br>✅ Drift detection (input distribution shift)<br>✅ Performance monitoring (accuracy over time)<br>✅ Alerting on degradation<br>✅ `.claude` updated | `grep "Drift detected" logs/*.log && cat docs/monitoring_guide.md` → logs exist, guide documented | logs/, docs/monitoring_guide.md | 2-3h | Pending | M7.5, M3.2 | M7.8 |
| **M7.7a-d** | *(Optional for ML - focus on M7.7b if using LLMs, M7.7d for concurrent training)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |
| **M7.8** | Integration Testing | End-to-end ML pipeline | Testing (15pts) | ✅ Full pipeline test (data prep → train → eval → serve)<br>✅ Model performance validated<br>✅ API integration tested<br>✅ `.claude` updated | `pytest tests/test_integration_ml.py -v` → pass | tests/test_integration_ml.py | 2-3h | Pending | M7.6, M7.7a-d | GATE 4 |
| **GATE 4** | 🚪 Feature Gate | Verify ML system works | N/A | ✅ Model achieves target metrics (e.g., accuracy ≥85%)<br>✅ API serves predictions<br>✅ Monitoring active | `python -m src.evaluate && python -m src.serve --test` → Success | evaluation_results.json, API logs | 30min | Pending | M7.8 | M8.1 |
| **M8.1** | Research Analysis (ML Experiments) | Sensitivity analysis & ablation studies | Research (15pts) | ✅ Experiments: feature importance, model comparison, hyperparameter sensitivity<br>✅ Ablation studies (remove features, see impact)<br>✅ Notebook with LaTeX formulas (≥2: loss function, evaluation metrics)<br>✅ Statistical significance tests<br>✅ `.claude` updated | `ls notebooks/ml_experiments.ipynb && grep "LaTeX" notebooks/*.ipynb` → exists, ≥2 formulas | notebooks/*.ipynb | 4-5h | Pending | M5, GATE 4 | M8.2 |
| **M8.2** | Visualization (ML Metrics) | Performance plots | Research (15pts) | ✅ Plots: training curves, confusion matrix, ROC curve, feature importance<br>✅ ≥4 plot types<br>✅ High res, publication quality<br>✅ `.claude` updated | `find notebooks -name "*.png" \| wc -l` → ≥4 | plots/*.png | 2-3h | Pending | M8.1 | M8.3 |
| **M8.3** | README Polish (ML-specific) | Complete sections | README (15pts) | ✅ All 15 sections<br>✅ ≥200 lines<br>✅ **Model architecture diagram**<br>✅ **Training results table** (model comparison)<br>✅ **Screenshots or plots** (training curves, confusion matrix, etc. - ≥8 images)<br>✅ **API usage examples** (prediction requests)<br>✅ `.claude` updated | `wc -l README.md && find docs -name "*.png" \| wc -l` → ≥200, ≥8 | README.md, plots | 2-3h | Pending | M7.6, M8.2 | M8.4 |
| **M8.4-M10** | *(Same as Full-Stack: Doc Review, Pre-Submission, Evaluation, Final Verification, Submission)* | ... | ... | ... | ... | ... | ... | Pending | ... | ... |

**TOTAL MISSIONS: 36** (Removed M7.2 UI, M7.5 Screenshots; Replaced M7.1-M7.6 with ML lifecycle missions; added M7.8 Integration, M3.3 Quality Standards, M6.1 Extensibility; same core structure)

**NOTE on Screenshots for ML**: Provide plots and diagrams:
- Model architecture diagram
- Training/validation loss curves
- Confusion matrix heatmap
- ROC curve (if classification)
- Feature importance plot
- Hyperparameter tuning results (grid search heatmap)
- Sample predictions (input → output examples)
- Monitoring dashboard or drift detection plots
Target ≥8 plots + diagrams for 90+ score.

---

## 2.6: HYBRID PROJECT COMPOSITION EXAMPLES (NEW)

*Use this section when project combines multiple architectures (see Principle 10.1 in core agent file)*

### Example 1: Full-Stack + ML Model (42 missions)

**User Selection**: Web UI + ML Model
**Primary**: Web UI (Full-Stack is more complex)

**Composition Strategy**:
1. Base: Template 2.1 (Full-Stack) → Keep all 35 missions as-is
2. Import from Template 2.5 (ML):
   - M7.1 (Data Prep) → M7.20a
   - M7.2 (Training) → M7.20b
   - M7.3 (Evaluation) → M7.20c
   - M7.4 (Tuning) → M7.20d
   - M7.5 (Serving) → M7.20e
   - M7.6 (Monitoring) → M7.20f
3. Add Integration: M7.21 (UI-ML Integration)

**Key Modified Missions**:

| ID | Title | Changes from Base |
|----|-------|-------------------|
| M7.1 | Core Feature Implementation | Add dependency on M7.20e (ML Serving) for prediction data |
| M7.8 | API Documentation | Add ML inference endpoint: POST /api/predict |
| M7.5 | Screenshot Capture | Include ML prediction results in UI screenshots |

**New Missions Added**:

| ID | Title | Objective | Rubric Focus | Definition of Done | Self-Verify Command | Evidence | Time | Status | Dependencies | Blocks |
|----|-------|-----------|--------------|--------------------|--------------------|----------|------|--------|--------------|--------|
| **M7.20a** | ML Data Preparation | Prepare training dataset | Research (15pts) | ✅ Dataset cleaned<br>✅ Train/val/test split (70/15/15)<br>✅ Features engineered<br>✅ Saved to data/processed/ | ls data/processed/train.csv | Processed data | 5-7h | Pending | M2.0, M3.1, GATE 3 | M7.20b |
| **M7.20b** | ML Model Training | Train baseline + advanced models | Research (15pts) | ✅ Baseline trained<br>✅ Advanced model trained<br>✅ Training logs saved<br>✅ Models in models/ | ls models/*.pkl \| wc -l → ≥2 | Trained models | 6-8h | Pending | M7.20a | M7.20c |
| **M7.20c** | ML Model Evaluation | Assess performance | Research (15pts) | ✅ Metrics calculated (acc, F1, AUC)<br>✅ Confusion matrix<br>✅ Model comparison table | cat results/eval.json | Evaluation report | 3-4h | Pending | M7.20b | M7.20d |
| **M7.20d** | Hyperparameter Tuning | Optimize model | Research (15pts) | ✅ Grid/Bayesian search<br>✅ Cross-validation<br>✅ Best params saved | cat results/tuning.json | Tuning results | 4-6h | Pending | M7.20c | M7.20e |
| **M7.20e** | ML Model Serving | Deploy inference API | Structure (15pts) | ✅ API endpoint functional<br>✅ Model loads from models/<br>✅ Prediction <2s | curl -X POST /api/predict | API response | 4-5h | Pending | M7.20d, M7.1 | M7.20f, M7.8, M7.21 |
| **M7.20f** | ML Monitoring | Track model performance | Config (10pts) | ✅ Prediction logging<br>✅ Drift detection<br>✅ Accuracy tracking | grep "Drift" logs/*.log | Monitoring logs | 2-3h | Pending | M7.20e | M7.21 |
| **M7.21** | UI-ML Integration Testing | End-to-end ML flow | Testing (15pts) | ✅ UI triggers prediction<br>✅ API calls ML model<br>✅ Results display correctly<br>✅ Error handling tested | pytest tests/test_ui_ml_integration.py | Integration test | 3-4h | Pending | M7.2, M7.20e, M7.20f | GATE 4 |

**TOTAL: 42 missions** (35 base + 6 ML + 1 integration)

---

### Example 2: CLI + Pipeline + API (42 missions)

**User Selection**: CLI + Data Pipeline + REST API
**Primary**: CLI (main user interface)

**Composition Strategy**:
1. Base: Template 2.2 (CLI) → Keep all 33 missions
2. Import from Template 2.4 (Pipeline):
   - M7.1 (Ingestion) → M7.20a
   - M7.2 (Transformation) → M7.20b
   - M7.3 (Loading) → M7.20c
   - M7.4 (Validation) → M7.20d
   - M7.5 (Orchestration) → M7.20e
   - M7.6 (Monitoring) → M7.20f
3. Import from Template 2.3 (API):
   - M7.8 (Swagger) → M7.30a
   - M7.10 (Load Testing) → M7.30b
4. Add Integration: M7.31 (CLI-Pipeline-API Integration)

**New Missions Added**:

| ID | Title | Objective | Rubric Focus | Definition of Done | Dependencies | Blocks |
|----|-------|-----------|--------------|--------------------|--------------| -------|
| **M7.20a-f** | Pipeline Stages (6 missions) | ETL implementation | Structure (15pts) | All 6 ETL stages functional | M2.0, M3.1, GATE 3 | M7.30a, M7.31 |
| **M7.30a** | API Monitoring Endpoints | Swagger for pipeline status | README (15pts) | ✅ GET /status, /metrics<br>✅ Swagger UI accessible | M7.20e | M7.30b |
| **M7.30b** | API Load Testing | Performance validation | Testing (15pts) | ✅ 100 concurrent requests<br>✅ p95 <2s | M7.30a | M7.31 |
| **M7.31** | CLI-Pipeline-API Integration | Full system test | Testing (15pts) | ✅ CLI triggers pipeline<br>✅ API reports status<br>✅ All modes work | M7.9, M7.20e, M7.30a | GATE 4 |

**Updated Missions**:
- M7.9 (CLI Help) → Add commands: `--run-pipeline`, `--status`, `--monitor`
- M7.4 (Integration Testing) → Include pipeline + API components

**TOTAL: 42 missions** (33 CLI + 6 Pipeline + 2 API + 1 integration)

---

### Example 3: API + ML (Training Pipeline + Inference) (42 missions)

**User Selection**: REST API + ML Model
**Primary**: API (serves ML predictions)

**Composition Strategy**:
1. Base: Template 2.3 (Backend API) → Keep all 35 missions
2. Import from Template 2.5 (ML):
   - M7.1 (Data Prep) → M7.20a
   - M7.2 (Training) → M7.20b
   - M7.3 (Evaluation) → M7.20c
   - M7.4 (Tuning) → M7.20d
   - M7.5 (Serving) → M7.20e
   - M7.6 (Monitoring) → M7.20f
3. Add Integration: M7.21 (ML API Integration)

**Key Missions**:
- M7.1 (API Endpoints) → includes POST /predict endpoint
- M7.20a (Data Prep) → training data pipeline
- M7.20b (Training) → model training offline
- M7.20e (Serving) → load trained model, serve via API
- M7.8 (Swagger) → documents POST /predict, GET /model_info endpoints
- M7.21 (Integration) → test train → deploy → inference flow

**TOTAL: 42 missions** (35 API + 6 ML + 1 integration)

---

### Composition Decision Tree

```
Is project HYBRID?
├─ NO → Use single template (2.1-2.5)
└─ YES → Composition workflow:
    ├─ Step 1: Identify primary component
    │   ├─ Web UI present? → Base = 2.1 (Full-Stack)
    │   ├─ API primary? → Base = 2.3 (API)
    │   ├─ CLI primary? → Base = 2.2 (CLI)
    │   ├─ Pipeline primary? → Base = 2.4 (Pipeline)
    │   └─ ML primary? → Base = 2.5 (ML)
    │
    ├─ Step 2: Import secondary components
    │   ├─ Need Web UI? → Import M7.2, M7.5 from 2.1
    │   ├─ Need API? → Import M7.8, M7.10 from 2.3
    │   ├─ Need CLI? → Import M7.9 from 2.2
    │   ├─ Need Pipeline? → Import M7.1-M7.6 from 2.4
    │   └─ Need ML? → Import M7.1-M7.6 from 2.5
    │
    ├─ Step 3: Renumber conflicts (M7.20a+, M7.30a+, M7.40a+ to avoid collisions)
    ├─ Step 4: Add cross-dependencies
    ├─ Step 5: Add integration mission(s)
    └─ Step 6: Validate (35-50 missions, all components present)
```

**Validation**: When generating hybrid missions, ensure:
- [ ] Base template matches primary component
- [ ] All checked architecture types have missions
- [ ] Mission IDs renumbered correctly (no duplicates)
- [ ] Cross-dependencies make sense
- [ ] Integration missions test multi-component flows
- [ ] Mission count within 35-50 range
- [ ] All 5 Gates present

---

# SECTION 3: PROGRESS TRACKER TEMPLATE

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  📊 PROGRESS TRACKER TEMPLATE                                                ║
║                                                                               ║
║  When generating PROGRESS_TRACKER.md, include ALL sections:                  ║
║  - Project header with target grade                                          ║
║  - Overall Progress metrics                                                  ║
║  - Rubric Category Progress table (7 categories)                             ║
║  - Mission Status by phase with checkboxes                                   ║
║  - Issues & Blockers table                                                   ║
║  - Time Tracking table                                                       ║
║  - Next Actions priority list                                                ║
║  - Status legend (✅🟢🟡🔴⚪)                                                  ║
║                                                                               ║
║  Target: 200+ lines with detailed tracking structure                         ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## Progress Tracker Format

```markdown
# 📋 PROJECT PROGRESS TRACKER

**Project**: [Project Name from PRD]
**Target Grade**: [70-79 / 80-89 / 90-100]
**Started**: [YYYY-MM-DD]
**Last Updated**: [YYYY-MM-DD]

---

## 🎯 Overall Progress

**Missions**: X / Y Complete (Z%)
**Estimated Time Remaining**: ~X hours
**Projected Completion**: [YYYY-MM-DD]

---

## 📊 Rubric Category Progress

| Category | Target | Current | Status | Notes |
|----------|--------|---------|--------|-------|
| Project Documentation | 19-20 / 20 | X / 20 | [✅/🟢/🟡/🔴/⚪] | [Progress notes] |
| README & Code Docs | 14-15 / 15 | X / 15 | [✅/🟢/🟡/🔴/⚪] | [Progress notes] |
| Structure & Code Quality | 14-15 / 15 | X / 15 | [✅/🟢/🟡/🔴/⚪] | [Progress notes] |
| Configuration & Security | 10 / 10 | X / 10 | [✅/🟢/🟡/🔴/⚪] | [Progress notes] |
| Testing & QA | 14-15 / 15 | X / 15 | [✅/🟢/🟡/🔴/⚪] | [Progress notes] |
| Research & Analysis | 13-15 / 15 | X / 15 | [✅/🟢/🟡/🔴/⚪] | [Progress notes] |
| UI/UX & Extensibility | 9-10 / 10 | X / 10 | [✅/🟢/🟡/🔴/⚪] | [Progress notes] |
| **TOTAL** | **90-100** | **X / 100** | **[✅/🟢/🟡/🔴/⚪]** | **[Overall status]** |

**Status Legend**:
- ✅ Complete (≥90% of target)
- 🟢 On Track (70-89% of target)
- 🟡 In Progress (40-69% of target)
- 🔴 Behind (<40% of target)
- ⚪ Not Started (0%)

---

## 📝 Mission Status

### Phase 0: Kickoff
- [ ] M0: Intake & Kickoff - [Status] (Xh actual/estimated)

### Phase 1: Planning & Architecture (Target: 18-20/20 Project Docs)
- [ ] M1: PRD Finalization - [Status] (Xh actual/estimated)
- [ ] GATE 1: PRD Quality Gate - [Status]
- [ ] M2.0: Package Setup - [Status] (Xh actual/estimated)
- [ ] M2.1: Repo Structure - [Status] (Xh actual/estimated)
- [ ] M2.2: Architecture Doc - [Status] (Xh actual/estimated)
  - [ ] C4 diagrams: X/4 done
  - [ ] ADRs: X/7 done
  - [ ] API contracts: X% documented

### Phase 2: Foundation (Target: 10/10 Config & Security)
- [ ] M3: Config & Security - [Status] (Xh actual/estimated)
- [ ] M3.1: YAML Config - [Status] (Xh actual/estimated)
- [ ] M3.2: Logging Setup - [Status] (Xh actual/estimated)
- [ ] GATE 2: Architecture Gate - [Status]

### Phase 3: Testing Framework (Target: 14-15/15 Testing)
- [ ] M4.1: Test Framework - [Status] (Xh actual/estimated)
- [ ] M4.2: Unit Tests - [Status] (Xh actual/estimated)
  - [ ] Test count: X/20 done
  - [ ] Coverage: X% (target: ≥70% or ≥85%)
  - [ ] Edge cases: X/5 done
- [ ] GATE 3: Testing Gate - [Status]

### Phase 4: Research Setup (Target: 13-15/15 Research)
- [ ] M5: Research Setup - [Status] (Xh actual/estimated)
- [ ] M6: UX/Extensibility Docs - [Status] (Xh actual/estimated)
- [ ] M6.1: JSON Schema Definition - [Status] (Xh actual/estimated)

### Phase 5: Implementation (Target: 14-15/15 Structure, 9-10/10 UI/UX)
*[List all M7.x missions based on project type template used]*
- [ ] M7.1: [Title] - [Status] (Xh actual/estimated)
- [ ] M7.2: [Title] - [Status] (Xh actual/estimated)
- [ ] ...
- [ ] GATE 4: Feature Gate - [Status]

### Phase 6: Analysis & Documentation (Target: 13-15/15 Research, 14-15/15 README)
- [ ] M8.1: Research Analysis - [Status] (Xh actual/estimated)
- [ ] M8.2: Visualization - [Status] (Xh actual/estimated)
- [ ] M8.3: README Polish - [Status] (Xh actual/estimated)
- [ ] M8.4: Documentation Review - [Status] (Xh actual/estimated)

### Phase 7: Submission (Target: 90-100/100 Overall)
- [ ] M9.1: Pre-Submission Checks - [Status] (Xh actual/estimated)
- [ ] M9.2: Self-Evaluation - [Status] (Xh actual/estimated)
- [ ] M9.3: Final Verification - [Status] (Xh actual/estimated)
- [ ] GATE 5: Submission Gate - [Status]
- [ ] M10: Submission - [Status] (Xh actual/estimated)

---

## 🚧 Current Focus

**Active Missions**: [List missions currently in progress]
**Next Up**: [Next mission(s) to start]
**Blockers**: [Any blocking issues]
**Risks**: [Any identified risks]

---

## ⚠️ Issues & Blockers

| Issue | Severity | Impact | Resolution Plan | Status |
|-------|----------|--------|-----------------|--------|
| [Issue description] | [High/Medium/Low] | [Impact on score/timeline] | [How to resolve] | [🔴/🟡/🟢/✅] |

---

## 📈 Time Tracking

| Phase | Estimated | Actual | Remaining | Status |
|-------|-----------|--------|-----------|--------|
| Phase 1: Planning | X-Yh | Xh | Xh | [✅/🟢/🟡/🔴/⚪] |
| Phase 2: Foundation | X-Yh | Xh | Xh | [✅/🟢/🟡/🔴/⚪] |
| Phase 3: Testing | X-Yh | Xh | Xh | [✅/🟢/🟡/🔴/⚪] |
| Phase 4: Research | X-Yh | Xh | Xh | [✅/🟢/🟡/🔴/⚪] |
| Phase 5: Implementation | X-Yh | Xh | Xh | [✅/🟢/🟡/🔴/⚪] |
| Phase 6: Documentation | X-Yh | Xh | Xh | [✅/🟢/🟡/🔴/⚪] |
| Phase 7: Submission | X-Yh | Xh | Xh | [✅/🟢/🟡/🔴/⚪] |
| **TOTAL** | **X-Yh** | **Xh** | **Xh** | **[✅/🟢/🟡/🔴/⚪]** **X% Complete** |

---

## ✅ Completed Milestones

- [x] [YYYY-MM-DD]: [Milestone description]

---

## 📅 Upcoming Milestones

- [ ] [YYYY-MM-DD]: [Milestone description]

---

## 🎯 Next Actions (Priority Order)

1. **[HIGH/MEDIUM/LOW]**: [Action item] - [time estimate]
2. **[HIGH/MEDIUM/LOW]**: [Action item] - [time estimate]
3. ...

---

**Last Updated**: [YYYY-MM-DD] by [Name/LLM]
**Next Review**: [YYYY-MM-DD]
```

**Update Frequency**: Daily (or after each mission completion)

**LLM Update Instructions**:
"After completing a mission, update PROGRESS_TRACKER.md:
1. Change mission status from [ ] to [x]
2. Update 'Missions Complete' count in Overall Progress
3. Update rubric category scores based on mission completion
4. Add any issues/blockers encountered
5. Update 'Last Updated' timestamp"

---

# SECTION 4: .CLAUDE FILE TEMPLATE

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  📁 .CLAUDE FILE TEMPLATE - LIVING PROJECT KNOWLEDGE BASE                    ║
║                                                                               ║
║  This file provides continuity across LLM sessions and serves as the        ║
║  single source of truth for project state, decisions, and progress.         ║
║                                                                               ║
║  Updated: After EVERY mission completion                                     ║
║  Purpose: LLM context restoration, grader handoff, team collaboration        ║
║  Target: 500+ lines with complete project memory                            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## .claude File Format

**Location**: Project root directory: `.claude`

```markdown
# .claude - Project Knowledge Base

**Last Updated**: YYYY-MM-DD HH:MM (after Mission MX.Y)
**Project**: [Project Name from PRD]
**Version**: 0.1.0
**Status**: [Planning / In Progress / Testing / Complete]

---

## 1. Project Overview

**One-Line Vision**: [One sentence describing what this project does]

**Problem Statement**:
[2-3 sentences explaining the problem this project solves]

**Target Users**:
- [Persona 1]: [Primary goal]
- [Persona 2]: [Primary goal]

**Success Criteria**:
- [KPI 1]: [Target and current status]
- [KPI 2]: [Target and current status]
- [KPI 3]: [Target and current status]

**Target Grade**: [70-79 / 80-89 / 90-100]
**Current Self-Assessment**: [X / 100] (as of [date])

---

## 2. Architecture & Tech Stack

**Tech Stack**:
- **Language**: Python 3.11+
- **Framework**: [FastAPI / Flask / Django / None]
- **LLM**: [Ollama / OpenAI / Claude / None]
- **UI**: [Streamlit / Gradio / React / None (CLI-only)]
- **Database**: [None / SQLite / PostgreSQL / ChromaDB]
- **Deployment**: [Local / Docker / Cloud]

**Package Structure**:
```
project_name/
  src/project_name/
    __init__.py
    __main__.py
    config/
    [other modules based on project type]
  config/
    settings.yaml
  logs/
  data/
  tests/
  pyproject.toml
```

**Key Architectural Decisions** (see PRD ADRs for full details):
- [ADR-001]: [Decision summary and rationale]
- [ADR-002]: [Decision summary and rationale]
- [ADR-003]: [Decision summary and rationale]
[... list all ADRs]

---

## 3. Configuration & Environment

**Environment Variables** (see `.env.example`):
- `ENV_VAR_1`: [Description] (required/optional)
- `ENV_VAR_2`: [Description] (required/optional)
[... list all env vars]

**YAML Configuration** (`config/settings.yaml` key parameters):
- `param_1`: [value] ([description])
- `param_2`: [value] ([description])
[... list key config params]

**How to Configure**:
1. Copy `.env.example` to `.env`
2. Fill in API keys (if needed)
3. Adjust `config/settings.yaml` for your use case
4. Run `python -m project_name --check-config` to validate

---

## 4. Installation & Usage

**Prerequisites**:
- Python 3.11+
- [List other dependencies: Ollama, Docker, etc.]

**Installation**:
```bash
# Clone repo
git clone [repo-url]
cd project_name

# Create venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .

# Verify installation
python -m project_name --version
```

**Usage**:
```bash
# [Primary usage command]
python -m project_name [args]

# [Alternative usage examples]
python -m project_name --help
python -m project_name --config config/custom_settings.yaml

# Run tests
pytest tests/

# Run with logging
python -m project_name --log-level DEBUG
```

---

## 5. Mission Progress & Status

**Current Mission**: [MX.Y - Title] ([Status: Pending/In Progress/Complete])
**Completed Missions**: [M1, M2, M3, ...]
**Blocked Missions**: [None / MX (reason)]

**Latest Updates** (newest first):

### [YYYY-MM-DD] - Mission MX.Y: [Title] [✅/🟡/🔴]

**What was done**:
- [Accomplishment 1]
- [Accomplishment 2]
- [Accomplishment 3]

**What changed from PRD**:
- [Deviation 1: reason]
- [Deviation 2: reason]
- [None - followed PRD exactly]

**Verification**:
```bash
[verification command from mission DoD]  # [✅/❌] [output summary]
[verification command 2]                 # [✅/❌] [output summary]
```

**Files Added/Modified**:
- NEW: [file path]
- MODIFIED: [file path] (changed: [what changed])
- DELETED: [file path] (reason: [why])

**Issues Encountered**:
- [Issue 1]: [How resolved]
- [Issue 2]: [Still open - mitigation plan]
- [None]

**Next Steps**: [Next mission to start / dependencies to resolve]

---

*[Repeat Section 5 format for each completed mission]*

---

## 6. Key Dependencies & Integration Points

**External Dependencies**:
- [Dependency 1]: For [purpose] (status: [configured/pending/issue])
- [Dependency 2]: For [purpose] (status: [configured/pending/issue])

**Internal Module Dependencies**:
```
[main module] → [sub-module 1] → [sub-module 2]
                              ↓
                           [sub-module 3]
```

**File-Based Interfaces** (JSON contracts - if applicable):
- `[path/to/contract1.json]`: [Producer] → [Consumer] ([purpose])
- `[path/to/contract2.json]`: [Producer] → [Consumer] ([purpose])

**Testing Mocks** (if applicable):
- `tests/mocks/[mock1].json`: Mock [external service] responses
- `tests/mocks/[mock2].json`: Mock [data source] outputs

---

## 7. Known Issues & Deviations from PRD

**Deviations from Original Plan**:
| Item | PRD Version | Actual Implementation | Reason | Impact |
|------|-------------|----------------------|--------|--------|
| [Item 1] | [Original plan] | [What was done instead] | [Why changed] | [Impact on score/functionality] |
| [Item 2] | [Original plan] | [What was done instead] | [Why changed] | [Impact] |
*[If no deviations: "None - all implementations match PRD"]*

**Known Issues**:
| Issue | Severity | Impact | Workaround | Fix Plan |
|-------|----------|--------|------------|----------|
| [Issue 1] | [High/Medium/Low] | [Description] | [Temporary workaround] | [When/how to fix] |
*[If no issues: "None - all functionality working as expected"]*

**Technical Debt**:
| Debt Item | Why Incurred | Refactor Plan | Priority |
|-----------|--------------|---------------|----------|
| [Debt 1] | [Reason taken on] | [How to refactor] | [High/Med/Low] |
*[If none: "None - code follows best practices"]*

---

## 8. Grading Checklist (Self-Assessment)

*Updated after each mission completion*

### Project Documentation (20pts)
- [✅/❌] PRD complete (1500+ lines for 90+)
- [✅/❌] 12+ KPIs with verification commands
- [✅/❌] Evidence Matrix (30+ entries for 90+)
- [✅/❌] 7+ ADRs with alternatives
- [✅/❌] Architecture docs (4 C4 levels)
**Current Score**: X / 20

### README & Code Docs (15pts)
- [✅/❌] README 200+ lines with 15 sections
- [✅/❌] Installation guide (10+ steps)
- [✅/❌] Docstrings ≥70% coverage
- [✅/❌] Examples and troubleshooting
**Current Score**: X / 15

### Structure & Code Quality (15pts)
- [✅/❌] Modular repo (7+ directories)
- [✅/❌] ≥90% files <150 LOC
- [✅/❌] DRY, SRP principles followed
- [✅/❌] Type hints used
**Current Score**: X / 15

### Configuration & Security (10pts)
- [✅/❌] .env.example complete
- [✅/❌] No hardcoded secrets
- [✅/❌] YAML config (20+ params)
- [✅/❌] Comprehensive .gitignore
**Current Score**: X / 10

### Testing & QA (15pts)
- [✅/❌] Coverage ≥70% (≥85% for 90+)
- [✅/❌] 20+ unit tests
- [✅/❌] 5+ edge case tests
- [✅/❌] Integration tests
**Current Score**: X / 15

### Research & Analysis (15pts)
- [✅/❌] Jupyter notebook (8+ cells)
- [✅/❌] 4+ plot types
- [✅/❌] 2+ LaTeX formulas (for 90+)
- [✅/❌] Statistical analysis
**Current Score**: X / 15

### UI/UX & Extensibility (10pts)
- [✅/❌] Nielsen's 10 heuristics table
- [✅/❌] 20+ screenshots (8+ minimum)
- [✅/❌] Extensibility guide (500+ lines)
- [✅/❌] 3+ extension points documented
**Current Score**: X / 10

**TOTAL SELF-ASSESSMENT**: **X / 100** ([Tier: 70-79 / 80-89 / 90-100])

---

## 9. Quick Reference Commands

**Development**:
```bash
# Install dependencies
pip install -e .

# Run application
python -m project_name

# Run tests
pytest tests/ -v

# Check coverage
pytest --cov=src --cov-report=html
```

**Verification (from PRD Evidence Matrix)**:
```bash
# [Evidence ID 1]
[verification command]  # Expected: [output]

# [Evidence ID 2]
[verification command]  # Expected: [output]

[... list key verification commands]
```

**Debugging**:
```bash
# View logs
tail -f logs/[latest].log

# Check config
python -c "from [project].config import settings; print(settings)"

# Test specific component
pytest tests/test_[component].py -v
```

---

## 10. LLM Prompt Context (For Next Session)

**Resume Instructions**:
"You are continuing work on [Project Name]. Current status:
- Last completed mission: [MX.Y - Title]
- Next mission to start: [MX.Z - Title]
- Current self-assessment: [X / 100]
- Blockers: [list or 'None']

**Key context**:
1. Tech stack: [summarize]
2. Architecture: [summarize key decisions]
3. Recent changes: [summarize last 2-3 missions]
4. Open issues: [list or 'None']

**Action needed**:
[What the next LLM session should focus on]

**Files to reference**:
- PRD: `documentation/PRD_[project].md`
- Missions: `Missions_[project].md`
- Progress: `PROGRESS_TRACKER.md`
- This file: `.claude`"

**Critical Reminders**:
- [Reminder 1: e.g., "Always update `.claude` after each mission"]
- [Reminder 2: e.g., "Run pytest before marking mission complete"]
- [Reminder 3: e.g., "Target grade is 90+ - maintain high quality standards"]

---

**End of .claude File**
```

**Update Frequency**: After EVERY mission completion

**Update Protocol**:
1. Update "Last Updated" timestamp and mission number
2. Add new Section 5 entry for completed mission
3. Update Section 8 checklist (mark completed items)
4. Update Section 10 with new resume instructions
5. Commit .claude file to git with message: "Update .claude after MX.Y completion"

---

# END OF TEMPLATES FILE

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║  ✅ TEMPLATES LIBRARY COMPLETE                                               ║
║                                                                               ║
║  This file contains ALL templates needed for deliverable generation:        ║
║  • Section 1: PRD Template (complete structure)                             ║
║  • Section 2: Missions Templates (5 project types)                          ║
║    - 2.1: Full-Stack Web Application (35 missions)                          ║
║    - 2.2: CLI-Only Application (33 missions)                                ║
║    - 2.3: Backend REST API (35 missions)                                    ║
║    - 2.4: Data Pipeline / ETL (34 missions)                                 ║
║    - 2.5: Machine Learning Model (34 missions)                              ║
║  • Section 3: Progress Tracker Template (comprehensive structure)           ║
║  • Section 4: .claude File Template (10 sections, living documentation)     ║
║                                                                               ║
║  Usage: Reference these templates when generating deliverables              ║
║  (see kickoff_agent_core_v3.0.md Section 5 for generation instructions)     ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```
