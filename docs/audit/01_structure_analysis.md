# Structural Analysis Report - Simple Risk Manager
**Generated:** 2025-10-22
**Analyst:** Structure Analyst Agent
**Scope:** Complete codebase excluding sdk/, node_modules/, __pycache__, .git, venv, .mypy_cache

---

## Executive Summary

### Overview Statistics
- **Total Files:** 608
- **Python Files:** 97
- **Markdown Files:** 340
- **Total Source Lines (Python):** 4,553
- **Directory Count:** 93 major directories
- **Largest File:** rest_client.py (382 lines)

### Key Findings
1. **Multiple organizational paradigms co-existing** - test-specs/ and tests/ directories serve overlapping purposes
2. **Scattered documentation** - 9+ markdown files in root, plus docs/, reports/, and embedded READMEs
3. **Duplicate directory purposes** - Multiple "logs", "docs", and configuration directories
4. **Inconsistent file organization** - Mix of empty and heavily populated directories
5. **Large generated artifact directories** - htmlcov (548K), test-results (2.0M), reports (596K)

---

## Complete File Inventory

### Source Code Structure (`/src`)

#### API Layer (`src/api/`)
| File | Lines | Size | Purpose |
|------|-------|------|---------|
| `rest_client.py` | 382 | 15K | Main REST API client implementation |
| `exceptions.py` | 53 | 915 | API exception definitions |
| `__init__.py` | 12 | 365 | Package exports |

**Status:** Clean, well-organized API layer with appropriate separation.

#### Core Modules (`src/core/`)
| File | Lines | Size | Purpose |
|------|-------|------|---------|
| `contract_cache.py` | 325 | 11K | Contract data caching |
| `pnl_tracker.py` | 321 | 11K | P&L tracking logic |
| `enforcement_actions.py` | 254 | 8.3K | Rule violation enforcement |
| `lockout_manager.py` | 253 | 8.3K | Account lockout management |
| `reset_scheduler.py` | 229 | 6.7K | Daily reset scheduling |
| `trade_counter.py` | 217 | 7.1K | Trade frequency tracking |
| `state_manager.py` | 209 | 9.4K | Application state management |
| `quote_tracker.py` | 184 | 6.1K | Real-time quote tracking |
| `timer_manager.py` | 180 | 6.1K | Timer-based operations |
| `__init__.py` | 10 | 238 | Package exports |

**Status:** Well-structured core modules with reasonable file sizes (all <400 lines).

#### Risk Rules (`src/rules/`)
| File | Lines | Size | Purpose |
|------|-------|------|---------|
| `symbol_blocks.py` | 208 | 7.0K | Symbol blocking rules |
| `max_contracts_per_instrument.py` | 194 | 7.7K | Per-instrument position limits |
| `trade_frequency_limit.py` | 174 | 6.1K | Trading frequency constraints |
| `max_contracts.py` | 147 | 4.9K | Total position limits |
| `__init__.py` | 0 | 0 | **Empty file** |

**Issues:**
- Empty `__init__.py` (no exports defined)
- Only 4 rules implemented despite 12 rules documented in specs

#### Utilities (`src/utils/`)
| File | Lines | Size | Purpose |
|------|-------|------|---------|
| `symbol_utils.py` | 37 | 934 | Symbol manipulation utilities |
| `__init__.py` | 0 | 0 | **Empty file** |

**Status:** Minimal utilities, empty init file.

#### Logging System (`src/risk_manager/logging/`)
| File | Lines | Size | Purpose |
|------|-------|------|---------|
| `performance.py` | 353 | 11K | Performance metrics logging |
| `config.py` | 318 | 8.9K | Logging configuration |
| `formatters.py` | 241 | 7.6K | Custom log formatters |
| `context.py` | 218 | 5.8K | Contextual logging |
| `__init__.py` | 31 | 903 | Package exports |
| `README.md` | N/A | 8.7K | Documentation |

**Status:** Well-implemented logging subsystem with documentation.

---

### Test Structure

#### Test Directories Overview
```
tests/                    # Actual test implementations (51 files)
├── unit/                 # Unit tests (14 test files)
│   ├── core/            # Core module tests
│   └── rules/           # Rule tests
├── integration/          # Integration tests (8 test files)
│   ├── api/             # API integration
│   ├── database/        # Database integration (empty)
│   ├── signalr/         # SignalR integration
│   └── workflows/       # Workflow integration (empty)
├── e2e/                 # End-to-end tests (6 test files)
├── fixtures/            # Test data fixtures (9 files)
├── swarm/               # Swarm testing (appears unused)
└── logs/                # Test execution logs

test-specs/              # Test specifications (9 markdown files)
├── unit/
│   ├── core/
│   └── rules/
├── integration/
│   ├── api/
│   ├── database/
│   └── signalr/
└── e2e/
```

#### Test Files Inventory

**Unit Tests (`tests/unit/`)**
| Category | File | Lines | Size |
|----------|------|-------|------|
| Rules | `test_daily_realized_loss.py` | N/A | 12K |
| Rules | `test_daily_unrealized_loss.py` | N/A | 12K |
| Rules | `test_trade_frequency_limit.py` | N/A | 13K |
| Rules | `test_max_unrealized_profit.py` | N/A | 9.3K |
| Rules | `test_trade_management.py` | N/A | 9.9K |
| Rules | `test_max_contracts_per_instrument.py` | N/A | 8.9K |
| Rules | `test_auth_loss_guard.py` | N/A | 8.6K |
| Rules | `test_symbol_blocks.py` | N/A | 8.3K |
| Rules | `test_session_block_outside_hours.py` | N/A | 8.4K |
| Rules | `test_max_contracts.py` | N/A | 7.8K |
| Rules | `test_no_stop_loss_grace.py` | N/A | 6.8K |
| Rules | `test_cooldown_after_loss.py` | N/A | 6.3K |
| Core | `test_enforcement_actions.py` | N/A | 9.6K |
| Core | `test_lockout_manager.py` | N/A | 9.4K |
| Core | `test_state_manager.py` | N/A | 7.5K |
| Core | `test_pnl_tracker.py` | N/A | 7.1K |

**Integration Tests (`tests/integration/`)**
| Category | File | Lines | Size |
|----------|------|-------|------|
| SignalR | `test_reconnection.py` | N/A | 19K |
| SignalR | `test_event_subscription.py` | N/A | 17K |
| SignalR | `test_event_parsing.py` | N/A | 16K |
| SignalR | `test_connection.py` | N/A | 14K |
| API | `test_error_handling.py` | N/A | 11K |
| API | `test_position_management.py` | N/A | 7.5K |
| API | `test_order_management.py` | N/A | 5.9K |
| API | `test_authentication.py` | N/A | 3.8K |

**E2E Tests (`tests/e2e/`)**
| File | Lines | Size |
|------|-------|------|
| `test_rule_violations.py` | N/A | 21K |
| `test_complete_trading_flow.py` | N/A | 17K |
| `test_signalr_triggers.py` | N/A | 15K |
| `test_network_recovery.py` | N/A | 13K |
| `test_performance.py` | N/A | 12K |
| `test_daily_reset.py` | N/A | 8.0K |

**Test Fixtures (`tests/fixtures/`)**
| File | Purpose | Size |
|------|---------|------|
| `signalr_events.py` | SignalR event mocks | 11K |
| `configs.py` | Configuration fixtures | 9.2K |
| `api_responses.py` | API response mocks | 9.5K |
| `positions.py` | Position data fixtures | 7.2K |
| `contracts.py` | Contract data fixtures | 6.4K |
| `trades.py` | Trade data fixtures | 5.6K |
| `orders.py` | Order data fixtures | 5.0K |
| `lockouts.py` | Lockout fixtures | 4.5K |
| `quotes.py` | Quote data fixtures | 3.5K |
| `accounts.py` | Account fixtures | 3.4K |

**Issue: Parallel Test Structures**
- `tests/` contains actual implementations
- `test-specs/` contains markdown specifications
- Both mirror the same directory structure (unit/core, unit/rules, integration/api, etc.)
- This creates maintenance overhead and potential drift

---

### Documentation Landscape

#### Root Level Documentation (9 files)
| File | Size | Purpose | Status |
|------|------|---------|--------|
| `CLAUDE.md` | 13K | Development environment config | **Should be .claude/README.md** |
| `PHASE_2_COMPLETE_SUMMARY.md` | 16K | Project milestone report | **Should be in docs/** |
| `integration_alignment_audit_report.md` | 20K | Audit report | **Should be in docs/audit/** |
| `LOGGING_IMPLEMENTATION.md` | 12K | Logging guide | **Should be in docs/** |
| `LOGGING_QUICK_START.md` | 6.3K | Logging guide | **Should be in docs/** |
| `LOGGING_CHEAT_SHEET.md` | 5.1K | Logging reference | **Should be in docs/** |
| `WHERE_WE_ARE.md` | 5.3K | Status document | **Should be in docs/** |
| `API_CLIENT_COMPLETE.md` | 1.8K | API client notes | **Should be in docs/** |
| `user.reference.md/` | Directory | User reference (weird structure) | **Should be docs/user-guide/** |

#### Organized Documentation (`docs/`)
| File | Purpose |
|------|---------|
| `SWARM_IMPLEMENTATION_SUMMARY.md` | Swarm coordination summary |
| `TESTING_LOGGING_GUIDE.md` | Testing and logging guide |
| `PHASE_1_SWARM_COMPLETE.md` | Phase 1 completion report |
| `TEST_RESULTS_GUIDE.md` | Test results interpretation |
| `ACTUAL_STATUS_REVIEW.md` | Project status review |
| `ERRORS_AND_WARNINGS_CONSOLIDATED.md` | Error catalog |
| `SWARM_COORDINATION_SUMMARY.md` | Swarm coordination details |
| `PROJECT_STATUS_CURRENT.md` | Current project status |
| `ERROR_HANDLING_SPECS_COMPLETE.md` | Error handling specs |
| `FINAL_STATUS_REPORT.md` | Final status report |
| `SWARM_IMPLEMENTATION_STRATEGY.md` | Implementation strategy |
| `SWARM_STRATEGY_ANALYSIS.md` | Strategy analysis |
| `SWARM_DEPLOYMENT_REPORT.md` | Deployment report |
| `COORDINATION_FLOW_DIAGRAMS.md` | Flow diagrams |

**Total: 14 markdown files in docs/**

#### Specification Documentation (`project-specs/`)
```
project-specs/
├── SPECS/                          # Main specifications
│   ├── 00-CORE-CONCEPT/           # 4 files (architecture, status, version)
│   ├── 01-EXTERNAL-API/           # 35+ files (API specs)
│   ├── 02-BACKEND-DAEMON/         # 3 files (daemon architecture)
│   ├── 03-RISK-RULES/             # 13 files (12 rules + guide)
│   ├── 04-CORE-MODULES/           # Module specs
│   ├── 05-INTERNAL-API/           # 2 files (endpoints, architecture)
│   ├── 06-CLI-FRONTEND/           # CLI specifications
│   ├── 07-DATA-MODELS/            # 8 files (schema, state objects)
│   ├── 08-CONFIGURATION/          # 4 files (config specs)
│   └── 99-IMPLEMENTATION-GUIDES/  # Implementation guides
├── spec_agents/                    # Agent coordination specs
│   ├── daemon_specialist.md
│   ├── integration-alignment-auditor.md
│   ├── planner_agent_kickoff.md
│   ├── deep_spec.md
│   ├── planner_agent.md
│   ├── cli-setup-specialist.md
│   └── promts.md/                 # Prompts directory
└── COMPLETE_SPECIFICATION.md       # Master spec (27K)
```

**Total: 100+ specification files**

#### Report Documentation (`reports/`)
```
reports/
├── 2025-10-22-spec-governance/    # Governance audit
│   ├── 00-manifest/               # 3 files (TOML, JSON, MD)
│   ├── 01-registry/               # 5 registry files
│   ├── 02-analysis/               # 4 analysis reports
│   ├── 03-dependencies/           # 2 dependency maps
│   ├── 04-testing/                # 3 testing readiness files
│   ├── 05-verification/           # 2 verification reports
│   ├── 06-handoff/                # 1 checklist
│   └── EXECUTIVE_SUMMARY.md
├── IMPLEMENTATION_ROADMAP.md
├── api-quick-reference.md
├── api-integration-analysis.md
├── COMPLETENESS_REPORT.md
├── api-call-matrix.md
└── DATA_MODEL_ANALYSIS.md
```

**Total: 25 report files**

#### Archive Documentation (`archive/project-specs/PROJECT_DOCS/`)
- Contains old/archived specifications
- Mirrors some current specs (duplication risk)
- Size: 400K

---

### Configuration Structure

#### Multiple Configuration Locations

**1. Root-Level Config Files**
```
.gitignore               # Git exclusions
.mcp.json                # MCP server config
.mcp.json.backup         # Backup MCP config
.wslconfig               # WSL configuration (empty)
package.json             # NPM packages
package-lock.json        # NPM lock (220K)
requirements-test.txt    # Python test dependencies
requirements-logging.txt # Python logging dependencies
```

**2. Config Directory (`config/`)**
```
config/
└── logging.yaml         # Logging configuration
```
**Issue:** Only 1 file, yet has dedicated directory

**3. Hidden Config Directories**
```
.claude/
├── settings.json        # Claude Code settings
├── settings.local.json  # Local overrides
├── statusline-command.sh
├── checkpoints/         # (empty)
├── commands/            # 16 command subdirectories
│   ├── agents/
│   ├── analysis/
│   ├── automation/
│   ├── coordination/
│   ├── github/
│   ├── hive-mind/
│   ├── hooks/
│   ├── memory/
│   ├── metrics/
│   ├── monitoring/
│   ├── optimization/
│   ├── swarm/
│   ├── training/
│   └── workflows/
└── helpers/

.claude-flow/
└── metrics/
    ├── performance.json
    ├── system-metrics.json
    ├── task-metrics.json
    └── agent-metrics.json

.hive-mind/
├── config.json
├── hive.db             # SQLite database (127K)
├── README.md
├── backups/
├── config/
│   ├── queens.json
│   └── workers.json
├── exports/
├── logs/
├── memory/
├── sessions/
└── templates/

.swarm/
├── module-dependency-analysis.json
└── config-audit-report.json
```

**Issues:**
- 4 separate hidden configuration systems (.claude, .claude-flow, .hive-mind, .swarm)
- Overlapping purposes (metrics, memory, sessions)
- No clear hierarchy or delegation

---

### Log File Structure

#### Multiple Log Directories

**1. Root Logs (`logs/`)**
```
logs/
└── tests/
    ├── test_run_20251022_043459.log (2151 lines)
    ├── test_run_20251022_043020.log (2151 lines)
    ├── test_run_20251022_050537.log (1921 lines)
    ├── test_run_20251022_045853.log (1921 lines)
    └── ... (multiple test runs)
```
**Purpose:** Test execution logs

**2. Test Logs (`tests/logs/`)**
```
tests/logs/
├── test_execution.log   # 9013 lines
├── coverage/            # Coverage reports
└── reports/             # Test reports
```
**Issue:** Duplicate log locations for tests

**3. Test Results (`test-results/`)**
```
test-results/            # 2.0M total
├── coverage/
│   ├── coverage.json
│   └── html/            # HTML coverage reports
├── history/             # Test history
├── logs/                # More logs
└── reports/
    └── report.html      # 2195 lines
```
**Issue:** Third test-related log location

**4. Hidden Logs**
```
.hive-mind/logs/         # Hive-mind logs
.claude-flow/metrics/    # Metrics (logs)
```

**5. Swarm Logs**
```
tests/swarm/             # Swarm test logs
└── .claude-flow/metrics/
```

**Summary:** 5 different log storage locations with overlapping purposes

---

### Script Files Structure

#### Root-Level Scripts (7 files)
| Script | Size | Purpose |
|--------|------|---------|
| `claude-swarm.sh` | 2.9K | Swarm orchestration script |
| `ruv-swarm-wrapper` | 1.2K | RUV swarm wrapper (no extension) |
| `ruv-swarm-wrapper.bat` | 1.1K | Windows batch version |
| `ruv-swarm-wrapper.ps1` | 1.5K | PowerShell version |
| `enable_wsl_interop.sh` | 646 | WSL interop setup |
| `run_tests.sh` | 242 | Test execution |
| `view_test_results.sh` | 133 | View test results |
| `open_reports.sh` | 2.1K | Open reports in browser |

**Issues:**
- No `scripts/` directory organization
- Multiple platform-specific versions (bat, ps1, sh) for same functionality
- Mix of test, deployment, and utility scripts

#### Scripts Directory (`scripts/`)
```
scripts/
└── test-management/     # Organized test scripts
```
**Issue:** Scripts exist in both root and `scripts/` directory

---

### Examples Structure

```
examples/
├── daemon_example.py           # Daemon usage example
├── logging_examples.py         # Logging examples
├── README.md                   # Examples documentation
├── cli-visual-examples.md      # CLI visual guide
├── trader-layouts-overview.md  # Layout overview
├── cli/
│   ├── admin/
│   │   ├── tui-dark-mode.py
│   │   └── cli-clickable.py
│   └── trader/
│       ├── trader-cli-smooth.py
│       ├── trader-compact.py
│       ├── cli-interactive-demo.py
│       ├── trader-heatmap.py
│       ├── trader-cli.py
│       ├── trader-minimal.py
│       ├── trader-splitscreen.py
│       └── trader-orderflow.py
└── swarm/
    ├── performance-benchmark.js
    └── basic-usage.js
```

**Status:** Well-organized with proper subdirectories

---

### Memory & Coordination Directories

#### Memory System (`memory/`)
```
memory/
├── agents/
│   └── README.md
├── sessions/
│   └── README.md
└── claude-flow@alpha-data.json
```
**Size:** 24K
**Status:** Minimal usage, mostly empty

#### Coordination System (`coordination/`)
```
coordination/
├── memory_bank/         # Empty
├── orchestration/       # Empty
└── subtasks/            # Empty
```
**Size:** 16K
**Status:** Directory structure created but unused

#### References (`references/`)
```
references/              # Empty
```
**Size:** 4.0K
**Status:** Created but unused

---

## Directory Tree Visualization

```
simple-risk-manager/
│
├── [SOURCE CODE] ─────────────────────────────────
│   └── src/
│       ├── api/              # API client (3 files, 450 lines)
│       ├── core/             # Core modules (10 files, 2400 lines)
│       ├── rules/            # Risk rules (5 files, 723 lines)
│       ├── utils/            # Utilities (2 files, 37 lines)
│       └── risk_manager/     # Logging system (6 files, 1161 lines)
│
├── [TESTING] ─────────────────────────────────────
│   ├── tests/                # Test implementations (51 files)
│   │   ├── unit/            # 14 unit test files
│   │   ├── integration/     # 8 integration test files
│   │   ├── e2e/             # 6 end-to-end test files
│   │   ├── fixtures/        # 9 fixture files
│   │   ├── swarm/           # Swarm tests (appears unused)
│   │   └── logs/            # Test logs
│   ├── test-specs/          # Test specifications (9 markdown)
│   └── test-results/        # Test output (2.0M)
│
├── [DOCUMENTATION] ───────────────────────────────
│   ├── docs/                # Organized docs (14 files)
│   ├── project-specs/       # Specifications (100+ files)
│   │   └── SPECS/           # Categorized specs
│   ├── reports/             # Generated reports (25 files)
│   ├── archive/             # Old specs (400K)
│   └── [9 ROOT MD FILES]    # Should be relocated
│
├── [CONFIGURATION] ───────────────────────────────
│   ├── .claude/             # Claude Code config
│   ├── .claude-flow/        # Flow metrics
│   ├── .hive-mind/          # Hive-mind system (127K DB)
│   ├── .swarm/              # Swarm analysis
│   ├── config/              # Single YAML file
│   ├── .mcp.json            # MCP server config
│   └── package.json         # NPM dependencies
│
├── [LOGS & RESULTS] ──────────────────────────────
│   ├── logs/                # Test logs
│   ├── test-results/        # Test results (2.0M)
│   └── htmlcov/             # Coverage HTML (548K)
│
├── [EXAMPLES & SCRIPTS] ──────────────────────────
│   ├── examples/            # Code examples (well-organized)
│   ├── scripts/             # Organized scripts
│   └── [7 ROOT SCRIPTS]     # Should be relocated
│
├── [COORDINATION] ────────────────────────────────
│   ├── memory/              # Memory system (minimal use)
│   ├── coordination/        # Empty structure
│   └── references/          # Empty
│
└── [BUILD ARTIFACTS] ─────────────────────────────
    ├── venv/                # Python virtual environment
    ├── node_modules/        # NPM packages
    ├── __pycache__/         # Python bytecode
    └── .mypy_cache/         # MyPy cache
```

---

## Structural Issues Found

### 1. File Placement Issues

#### Root Directory Clutter (Severity: HIGH)
**Problem:** 9 markdown files in root that should be in `docs/`

**Files Needing Relocation:**
```
ROOT → docs/
├── PHASE_2_COMPLETE_SUMMARY.md → docs/milestones/
├── integration_alignment_audit_report.md → docs/audit/
├── LOGGING_IMPLEMENTATION.md → docs/guides/
├── LOGGING_QUICK_START.md → docs/guides/
├── LOGGING_CHEAT_SHEET.md → docs/reference/
├── WHERE_WE_ARE.md → docs/status/
├── API_CLIENT_COMPLETE.md → docs/api/
└── user.reference.md/ (directory!) → docs/user-guide/
```

**Impact:** Makes root directory hard to navigate, unclear project organization

#### Root Script Clutter (Severity: MEDIUM)
**Problem:** 7 scripts in root should be in `scripts/`

**Recommended Organization:**
```
scripts/
├── development/
│   ├── claude-swarm.sh
│   ├── ruv-swarm-wrapper
│   └── enable_wsl_interop.sh
├── testing/
│   ├── run_tests.sh
│   └── view_test_results.sh
├── reporting/
│   └── open_reports.sh
└── platform/
    ├── windows/
    │   └── ruv-swarm-wrapper.bat
    └── powershell/
        └── ruv-swarm-wrapper.ps1
```

### 2. Duplicate Directory Structures (Severity: HIGH)

#### Test Duplication
**Problem:** `tests/` and `test-specs/` mirror each other

```
Parallel Structure:
tests/unit/core/          ←→  test-specs/unit/core/
tests/unit/rules/         ←→  test-specs/unit/rules/
tests/integration/api/    ←→  test-specs/integration/api/
tests/integration/signalr/←→  test-specs/integration/signalr/
tests/e2e/                ←→  test-specs/e2e/
```

**Recommendation:** Merge specs into test files as docstrings or move to `docs/testing/`

#### Log Duplication
**Problem:** 5 separate log directories

```
Duplicate Log Locations:
1. logs/tests/              # Test run logs
2. tests/logs/              # Test execution logs
3. test-results/logs/       # Test result logs
4. test-results/coverage/   # Coverage reports
5. .hive-mind/logs/         # System logs
```

**Recommendation:** Consolidate to single `logs/` with subdirectories:
```
logs/
├── tests/          # All test logs
├── coverage/       # Coverage reports
├── system/         # System logs
└── swarm/          # Swarm coordination logs
```

### 3. Empty or Underutilized Directories (Severity: MEDIUM)

**Empty Directories:**
```
coordination/memory_bank/    # Created but unused
coordination/orchestration/  # Created but unused
coordination/subtasks/       # Created but unused
references/                  # Created but unused
tests/integration/database/  # Placeholder
tests/integration/workflows/ # Placeholder
config/                      # Only 1 file (logging.yaml)
```

**Recommendation:**
- Remove unused directories
- Consider consolidating single-file directories
- Document purpose before creating directory structures

### 4. Configuration Fragmentation (Severity: HIGH)

**Multiple Config Systems:**
```
Configuration Locations:
1. .claude/              # Claude Code settings
2. .claude-flow/         # Flow metrics (config-like)
3. .hive-mind/           # Hive-mind config + DB
4. .swarm/               # Swarm analysis
5. config/               # Application config (1 file)
6. .mcp.json            # MCP server config
7. package.json         # NPM dependencies
8. requirements-*.txt   # Python dependencies
```

**Issues:**
- No clear hierarchy
- Overlapping purposes (metrics, memory, sessions)
- Hard to understand overall configuration
- Difficult to backup/restore configuration state

**Recommendation:** Create configuration map document showing:
- What each config directory controls
- Interdependencies
- Which configs should be version-controlled vs gitignored

### 5. Naming Convention Inconsistencies (Severity: MEDIUM)

#### File Naming Patterns
| Pattern | Examples | Count |
|---------|----------|-------|
| `snake_case.py` | Most Python files | 90% |
| `kebab-case.md` | Most markdown files | 70% |
| `SCREAMING_SNAKE.md` | Some docs | 20% |
| `PascalCase.md` | Some docs | 10% |
| No extension | `claude-flow`, `wsl`, `john_trader_` | 3 |

**Recommendation:** Standardize on:
- Python files: `snake_case.py`
- Markdown files: `kebab-case.md` (not SCREAMING)
- Scripts: `kebab-case.sh`
- Config files: `kebab-case.json/yaml`

#### Weird Files Found
```
john_trader_             # 0 bytes, no extension
wsl                      # 0 bytes, no extension
user.reference.md/       # Directory named like file
```

**Recommendation:** Delete orphaned files, fix user.reference.md structure

### 6. Test Structure Issues (Severity: MEDIUM)

#### Missing Test Implementations
**Found in specs but not implemented:**

```
test-specs/ declares tests for all 12 rules:
01-12: All rule tests documented

tests/unit/rules/ only has 12 test files:
✓ 01_max_contracts
✓ 02_max_contracts_per_instrument
✓ 03_daily_realized_loss
✓ 04_daily_unrealized_loss
✓ 05_max_unrealized_profit
✓ 06_trade_frequency_limit
✓ 07_cooldown_after_loss
✓ 08_no_stop_loss_grace
✓ 09_session_block_outside_hours
✓ 10_auth_loss_guard
✓ 11_symbol_blocks
✓ 12_trade_management
```

**But source only has 4 rule implementations:**
```
src/rules/
✓ max_contracts.py
✓ max_contracts_per_instrument.py
✓ symbol_blocks.py
✓ trade_frequency_limit.py
✗ Missing 8 rule implementations!
```

**Gap:** Tests and specs exist for unimplemented rules

### 7. Documentation Fragmentation (Severity: HIGH)

**340 Markdown files across:**
- Root (9 files)
- docs/ (14 files)
- project-specs/ (100+ files)
- reports/ (25 files)
- test-specs/ (9 files)
- archive/ (unknown count)
- Embedded READMEs (4+ files)

**Issues:**
- No single entry point
- Overlapping documentation
- Unclear what's current vs archived
- Hard to maintain consistency

**Recommendation:** Create documentation hierarchy:
```
docs/
├── README.md              # Main entry point
├── architecture/          # System architecture
├── api/                   # API documentation
├── guides/                # User/developer guides
├── reference/             # Reference materials
├── audit/                 # Audit reports
├── milestones/            # Project milestones
└── specs/                 # Link to project-specs/
```

---

## File Size Analysis

### Large Files (>500 lines)
| File | Lines | Category | Recommendation |
|------|-------|----------|----------------|
| N/A | N/A | N/A | All Python files <500 lines ✓ |

**Status:** Good! All source files are reasonably sized.

### Tiny Files (<10 lines)
| File | Lines | Purpose | Recommendation |
|------|-------|---------|----------------|
| `src/rules/__init__.py` | 0 | Package init | Add exports |
| `src/utils/__init__.py` | 0 | Package init | Add exports |
| `run_tests.sh` | 4 | Test runner | OK for script |

**Issue:** Empty `__init__.py` files prevent proper imports

### Orphaned Files
```
john_trader_      # 0 bytes, unknown purpose
wsl               # 0 bytes, WSL-related?
.wslconfig        # 0 bytes, WSL config (empty)
```

**Recommendation:** Delete or document purpose

---

## Dependencies and Build Artifacts

### Large Artifact Directories
| Directory | Size | Purpose | .gitignored? |
|-----------|------|---------|--------------|
| `test-results/` | 2.0M | Test output | ✓ |
| `htmlcov/` | 548K | Coverage HTML | ✓ |
| `reports/` | 596K | Generated reports | ? |
| `archive/` | 400K | Old specs | Partial |
| `package-lock.json` | 220K | NPM lock | No |
| `.hive-mind/hive.db` | 127K | SQLite DB | ? |

**Recommendations:**
- Ensure all build artifacts are gitignored
- Consider archiving old reports
- Review if `reports/` should be in git or gitignored

### Python Package Structure
```
src/
├── api/           # ✓ Has __init__.py with exports
├── core/          # ✓ Has __init__.py with exports
├── rules/         # ✗ Empty __init__.py
├── utils/         # ✗ Empty __init__.py
└── risk_manager/
    └── logging/   # ✓ Has __init__.py with exports
```

**Issue:** Incomplete package structure

---

## Directory Organization Patterns

### Well-Organized Areas ✓
1. **src/core/** - Clean module organization, consistent file sizes
2. **src/api/** - Proper separation of concerns
3. **src/risk_manager/logging/** - Good subsystem organization
4. **examples/** - Proper subdirectories for different example types
5. **tests/fixtures/** - Centralized test data
6. **project-specs/SPECS/** - Numbered categorization system

### Poorly-Organized Areas ✗
1. **Root directory** - Too many files (9 markdown + 7 scripts)
2. **Log directories** - 5 separate locations
3. **Config directories** - 4+ systems with overlap
4. **Documentation** - Fragmented across 6+ locations
5. **Test structure** - Duplicate test-specs/tests directories
6. **Coordination** - Empty directory structure

---

## Recommendations Summary

### Priority 1: Critical (Do Immediately)

1. **Fix Empty Init Files**
   ```bash
   # Add proper exports to:
   src/rules/__init__.py
   src/utils/__init__.py
   ```

2. **Relocate Root Documentation**
   ```bash
   mkdir -p docs/{guides,reference,audit,milestones,status,api}
   mv *.md docs/  # Then reorganize into subdirectories
   ```

3. **Consolidate Log Directories**
   ```bash
   # Create unified log structure
   logs/
   ├── tests/
   ├── coverage/
   ├── system/
   └── swarm/
   ```

4. **Clean Up Orphaned Files**
   ```bash
   rm john_trader_ wsl .wslconfig
   ```

### Priority 2: High (Do This Week)

5. **Reorganize Scripts**
   ```bash
   scripts/
   ├── development/
   ├── testing/
   ├── reporting/
   └── platform/{windows,powershell}/
   ```

6. **Resolve Test-Specs Duplication**
   - Option A: Merge specs into test docstrings
   - Option B: Move to docs/testing/specifications/
   - Option C: Keep but document relationship clearly

7. **Create Configuration Map**
   - Document each config directory's purpose
   - Show interdependencies
   - Define backup/restore strategy

8. **Standardize Naming Conventions**
   - Rename SCREAMING_CASE.md to kebab-case.md
   - Fix user.reference.md/ directory structure

### Priority 3: Medium (Do This Sprint)

9. **Clean Up Empty Directories**
   ```bash
   # Remove or document:
   coordination/{memory_bank,orchestration,subtasks}/
   references/
   tests/integration/{database,workflows}/
   ```

10. **Audit Archive Directory**
    - Identify truly archived content
    - Remove duplicates
    - Consider compression

11. **Create Documentation Index**
    - Single README.md as entry point
    - Clear hierarchy
    - Links to all doc locations

12. **Review Generated Reports**
    - Determine if reports/ should be gitignored
    - Archive old reports
    - Set retention policy

### Priority 4: Low (Nice to Have)

13. **Optimize Directory Depths**
    - Some specs are 4-5 levels deep
    - Consider flattening where appropriate

14. **Create File Organization Guide**
    - Document where new files should go
    - Provide templates
    - Onboarding documentation

15. **Implement File Size Monitoring**
    - Alert when files exceed 500 lines
    - Encourage modular design

---

## Conclusion

The simple-risk-manager codebase has **good modular design** in its source code but suffers from **organizational inconsistency** in its supporting files. The main issues are:

1. **Root directory clutter** (9 MD files + 7 scripts)
2. **Duplicate directory purposes** (logs, docs, test-specs)
3. **Configuration fragmentation** (4+ config systems)
4. **Documentation scattered** across 6+ locations
5. **Empty directory structures** (coordination, references)

The **source code itself is well-organized** with appropriate file sizes and clean module structure. The **test suite is comprehensive** with good fixture organization.

**Immediate action needed:**
- Fix empty `__init__.py` files (breaks imports)
- Relocate root-level documentation files
- Consolidate log directories
- Delete orphaned files

**Strategic improvements:**
- Unify test specifications with implementations
- Create clear configuration hierarchy
- Establish documentation index
- Define file organization standards

---

## Appendix: Complete File Tree

```
.
├── API_CLIENT_COMPLETE.md
├── CLAUDE.md
├── LOGGING_CHEAT_SHEET.md
├── LOGGING_FILES_SUMMARY.txt
├── LOGGING_FILE_PATHS.txt
├── LOGGING_IMPLEMENTATION.md
├── LOGGING_QUICK_START.md
├── PHASE_2_COMPLETE_SUMMARY.md
├── WHERE_WE_ARE.md
├── claude-flow
├── claude-swarm.sh
├── config/
│   └── logging.yaml
├── coordination/
│   ├── memory_bank/
│   ├── orchestration/
│   └── subtasks/
├── docs/
│   └── [14 markdown files]
├── enable_wsl_interop.sh
├── examples/
│   ├── cli/
│   │   ├── admin/ [2 py files]
│   │   └── trader/ [9 py files]
│   ├── swarm/ [2 js files]
│   └── [3 md/py files]
├── integration_alignment_audit_report.md
├── john_trader_
├── logs/
│   └── tests/ [multiple .log files]
├── memory/
│   ├── agents/
│   ├── sessions/
│   └── claude-flow@alpha-data.json
├── open_reports.sh
├── package.json
├── package-lock.json
├── project-specs/
│   ├── SPECS/
│   │   ├── 00-CORE-CONCEPT/ [4 files]
│   │   ├── 01-EXTERNAL-API/ [35+ files in subdirs]
│   │   ├── 02-BACKEND-DAEMON/ [3 files]
│   │   ├── 03-RISK-RULES/ [13 files]
│   │   ├── 04-CORE-MODULES/
│   │   ├── 05-INTERNAL-API/ [2 files]
│   │   ├── 06-CLI-FRONTEND/
│   │   ├── 07-DATA-MODELS/ [8 files in subdirs]
│   │   ├── 08-CONFIGURATION/ [4 files]
│   │   └── 99-IMPLEMENTATION-GUIDES/
│   └── spec_agents/ [7 files]
├── references/
├── reports/
│   ├── 2025-10-22-spec-governance/ [25 files in subdirs]
│   └── [6 md files]
├── requirements-logging.txt
├── requirements-test.txt
├── run_tests.sh
├── ruv-swarm-wrapper
├── ruv-swarm-wrapper.bat
├── ruv-swarm-wrapper.ps1
├── scripts/
│   └── test-management/
├── src/
│   ├── api/ [3 py files]
│   ├── core/ [10 py files]
│   ├── risk_manager/
│   │   └── logging/ [5 py files + README]
│   ├── rules/ [5 py files]
│   └── utils/ [2 py files]
├── test-results/
│   ├── coverage/
│   ├── history/
│   ├── logs/
│   └── reports/
├── test-specs/
│   ├── e2e/ [1 md file]
│   ├── fixtures/
│   ├── integration/ [3 md files in subdirs]
│   ├── unit/ [4 md files in subdirs]
│   └── [2 md files]
├── tests/
│   ├── conftest.py
│   ├── e2e/ [6 py files]
│   ├── fixtures/ [10 py files]
│   ├── integration/
│   │   ├── api/ [5 py files]
│   │   └── signalr/ [4 py files]
│   ├── logs/
│   ├── swarm/
│   ├── unit/
│   │   ├── core/ [9 py files]
│   │   └── rules/ [12 py files]
│   └── [4 py files]
├── user.reference.md/
│   └── README.md
├── view_test_results.sh
└── wsl

Hidden Directories:
├── .claude/
│   ├── settings.json
│   ├── settings.local.json
│   ├── statusline-command.sh
│   ├── checkpoints/
│   ├── commands/ [16 subdirs]
│   └── helpers/
├── .claude-flow/
│   └── metrics/ [4 json files]
├── .hive-mind/
│   ├── config.json
│   ├── hive.db
│   ├── README.md
│   ├── backups/
│   ├── config/ [2 json files]
│   ├── exports/
│   ├── logs/
│   ├── memory/
│   ├── sessions/
│   └── templates/
└── .swarm/ [2 json files]

Excluded from analysis:
├── .git/
├── .mypy_cache/
├── __pycache__/
├── node_modules/
├── sdk/
└── venv/
```

---

**End of Structural Analysis Report**

Generated by Structure Analyst Agent
Date: 2025-10-22
Analysis Scope: 608 files, 93 directories
Source Lines Analyzed: 4,553 (Python only)
