# 🤖 Swarm Implementation Strategy - TDD Risk Rules

**Date:** 2025-10-22
**Objective:** Implement all 12 risk rules using parallel agent swarms following TDD

---

## 🎯 **Strategy Overview**

### **Approach: Test-Driven Development (TDD)**
1. **Tests are already written** (78 test scenarios across 12 rules)
2. **Specifications are complete** (in `project-specs/SPECS/03-RISK-RULES/`)
3. **All dependencies ready** (9 core modules, 100% passing tests)
4. **Pattern:** Read tests → Implement to pass tests → Verify

### **Swarm Topology: Mesh**
- **Why:** Allows parallel independent work on different rules
- **Coordination:** Via hooks and shared memory
- **Agents:** 4-6 coder agents per phase

### **Phases: 3 Waves**
- **Phase 1:** Simple rules (4 rules, 2-3 hours)
- **Phase 2:** Medium complexity (4 rules, 3-4 hours)
- **Phase 3:** Complex rules (4 rules, 4-5 hours)

---

## 📋 **Phase 1: Simple Rules (Priority)**

### **Rules to Implement:**
1. **RULE-001: MaxContracts** ⭐ SIMPLEST
2. **RULE-002: MaxContractsPerInstrument**
3. **RULE-011: SymbolBlocks**
4. **RULE-006: TradeFrequencyLimit**

### **Why These First:**
- Minimal dependencies (1-2 modules each)
- Clear logic (simple comparisons)
- Fast to implement (1-2 hours each)
- Build confidence in TDD workflow

### **Dependencies:**
- RULE-001: MOD-009 (State Manager) ✅
- RULE-002: MOD-009 ✅
- RULE-011: MOD-009 ✅
- RULE-006: MOD-008 (Trade Counter) ✅

**All dependencies satisfied!**

---

## 🎨 **Phase 2: Medium Complexity**

### **Rules to Implement:**
5. **RULE-003: DailyRealizedLoss**
6. **RULE-004: DailyUnrealizedLoss**
7. **RULE-005: MaxUnrealizedProfit**
8. **RULE-007: CooldownAfterLoss**

### **Why These Second:**
- Moderate dependencies (2-3 modules each)
- P&L calculations involved
- Timer/cooldown logic
- Build on Phase 1 learnings

### **Dependencies:**
- RULE-003: MOD-005 (P&L Tracker) ✅, MOD-001 (Enforcement) ✅
- RULE-004: MOD-005 ✅, MOD-006 (Quote Tracker) ✅, MOD-007 (Contract Cache) ✅
- RULE-005: MOD-005 ✅, MOD-006 ✅, MOD-007 ✅
- RULE-007: MOD-003 (Timer Manager) ✅, MOD-005 ✅

**All dependencies satisfied!**

---

## 🔥 **Phase 3: Complex Rules**

### **Rules to Implement:**
9. **RULE-008: NoStopLossGrace**
10. **RULE-009: SessionBlockOutside**
11. **RULE-010: AuthLossGuard**
12. **RULE-012: TradeManagement**

### **Why These Last:**
- Complex business logic
- Multiple enforcement modes
- Time-based logic
- Integration with multiple modules

### **Dependencies:**
- RULE-008: MOD-003 ✅, MOD-009 ✅
- RULE-009: MOD-004 (Reset Scheduler) ✅
- RULE-010: MOD-005 ✅, MOD-002 (Lockout Manager) ✅
- RULE-012: MOD-009 ✅, MOD-001 ✅

**All dependencies satisfied!**

---

## 🤖 **Agent Instructions (TDD Template)**

### **Each Agent Receives:**

1. **Rule Assignment:** RULE-XXX with spec path
2. **Test Path:** Location of test file with scenarios
3. **Dependencies:** Which modules to import and use
4. **Output Path:** Where to create the rule file
5. **TDD Workflow:** Step-by-step instructions

### **TDD Workflow for Each Agent:**

```markdown
## Agent Task: Implement RULE-XXX

### 1. Read the Specification
**File:** `project-specs/SPECS/03-RISK-RULES/rules/XX_rule_name.md`
- Understand: What triggers the rule
- Understand: What action to take
- Understand: Configuration parameters

### 2. Read ALL Test Scenarios
**File:** `tests/unit/rules/test_rule_name.py`
- Read EVERY test function (Given/When/Then format)
- Each test defines EXACT behavior expected
- Note the mocked dependencies and assertions

### 3. Run Tests (See Them Fail)
```bash
cd "/home/jakers/projects/simple-risk-manager/simple risk manager"
pytest tests/unit/rules/test_rule_name.py -v
```
- Tests will fail (no implementation yet)
- This is EXPECTED in TDD

### 4. Create Rule File
**File:** `src/rules/rule_name.py`
- Use template from `HOW_TO_ADD_NEW_RULES.md`
- Import required modules (already implemented)

### 5. Implement ONE Test at a Time
- Start with simplest test (usually "test_rule_disabled")
- Implement MINIMUM code to pass that ONE test
- Run tests: `pytest tests/unit/rules/test_rule_name.py::TestRuleName::test_rule_disabled -v`
- Move to next test

### 6. Iterate Until ALL Tests Pass
- Implement each test scenario one by one
- Run full test suite after each addition
- Refactor while keeping tests green

### 7. Final Verification
```bash
# All tests for this rule
pytest tests/unit/rules/test_rule_name.py -v

# With coverage (aim for 90%+)
pytest tests/unit/rules/test_rule_name.py --cov=src/rules/rule_name --cov-report=term-missing
```

### 8. Report Completion
- Total tests: X/X passing
- Coverage: XX%
- File created: `src/rules/rule_name.py` (XX lines)
- Ready for integration
```

---

## 📊 **Agent Coordination Strategy**

### **Pre-Task (Coordination Setup):**
Each agent runs:
```bash
npx claude-flow@alpha hooks pre-task --description "Implement RULE-XXX"
npx claude-flow@alpha hooks session-restore --session-id "swarm-risk-rules-phase1"
```

### **During Task (Memory Sharing):**
```bash
# Store progress
npx claude-flow@alpha hooks post-edit --file "src/rules/rule_name.py" --memory-key "swarm/rules/RULE-XXX/status"

# Store completion
npx claude-flow@alpha hooks notify --message "RULE-XXX: 6/6 tests passing"
```

### **Post-Task (Report Results):**
```bash
npx claude-flow@alpha hooks post-task --task-id "RULE-XXX"
npx claude-flow@alpha hooks session-end --export-metrics true
```

---

## 🎯 **Success Criteria (Per Rule)**

### **Must Have:**
- ✅ Rule file created in `src/rules/`
- ✅ All test scenarios passing (6-8 tests per rule)
- ✅ Code coverage ≥ 90%
- ✅ No pylint/flake8 errors
- ✅ Proper type hints
- ✅ Docstrings for all methods

### **Quality Checks:**
- ✅ Follows template from `HOW_TO_ADD_NEW_RULES.md`
- ✅ Uses existing modules (no reimplementation)
- ✅ Returns `None` for non-relevant events (fast path)
- ✅ Descriptive breach reasons
- ✅ Proper error handling

---

## 📁 **File Organization**

```
src/rules/
├── __init__.py                    # Module exports
├── max_contracts.py               # RULE-001 (Phase 1)
├── max_contracts_per_instrument.py# RULE-002 (Phase 1)
├── symbol_blocks.py               # RULE-011 (Phase 1)
├── trade_frequency_limit.py       # RULE-006 (Phase 1)
├── daily_realized_loss.py         # RULE-003 (Phase 2)
├── daily_unrealized_loss.py       # RULE-004 (Phase 2)
├── max_unrealized_profit.py       # RULE-005 (Phase 2)
├── cooldown_after_loss.py         # RULE-007 (Phase 2)
├── no_stop_loss_grace.py          # RULE-008 (Phase 3)
├── session_block_outside.py       # RULE-009 (Phase 3)
├── auth_loss_guard.py             # RULE-010 (Phase 3)
└── trade_management.py            # RULE-012 (Phase 3)
```

---

## 🚀 **Phase 1 Execution Plan**

### **Swarm Configuration:**
- **Topology:** Mesh (parallel execution)
- **Max Agents:** 4 (one per rule)
- **Coordination:** Via hooks + shared memory
- **Session ID:** `swarm-risk-rules-phase1`

### **Agent Assignments:**

**Agent 1: "RULE-001 Implementer"**
- Task: Implement MaxContracts
- Spec: `project-specs/SPECS/03-RISK-RULES/rules/01_max_contracts.md`
- Tests: `tests/unit/rules/test_max_contracts.py` (6 tests)
- Output: `src/rules/max_contracts.py`
- Dependencies: MOD-009 (State Manager)

**Agent 2: "RULE-002 Implementer"**
- Task: Implement MaxContractsPerInstrument
- Spec: `project-specs/SPECS/03-RISK-RULES/rules/02_max_contracts_per_instrument.md`
- Tests: `tests/unit/rules/test_max_contracts_per_instrument.py` (6 tests)
- Output: `src/rules/max_contracts_per_instrument.py`
- Dependencies: MOD-009

**Agent 3: "RULE-011 Implementer"**
- Task: Implement SymbolBlocks
- Spec: `project-specs/SPECS/03-RISK-RULES/rules/11_symbol_blocks.md`
- Tests: `tests/unit/rules/test_symbol_blocks.py` (6 tests)
- Output: `src/rules/symbol_blocks.py`
- Dependencies: MOD-009

**Agent 4: "RULE-006 Implementer"**
- Task: Implement TradeFrequencyLimit
- Spec: `project-specs/SPECS/03-RISK-RULES/rules/06_trade_frequency_limit.md`
- Tests: `tests/unit/rules/test_trade_frequency_limit.py` (8 tests)
- Output: `src/rules/trade_frequency_limit.py`
- Dependencies: MOD-008 (Trade Counter)

### **Time Estimate:**
- Agent setup: 5 minutes
- Implementation: 1-2 hours per rule (parallel)
- Verification: 15 minutes
- **Total:** ~2-3 hours for Phase 1

---

## 📊 **Success Metrics (Phase 1)**

### **Target:**
- 4 rules implemented
- 26 tests passing (6+6+6+8)
- 4 files created (~100-150 lines each)
- Coverage ≥ 90% per file

### **Deliverables:**
1. `src/rules/max_contracts.py`
2. `src/rules/max_contracts_per_instrument.py`
3. `src/rules/symbol_blocks.py`
4. `src/rules/trade_frequency_limit.py`
5. Updated `src/rules/__init__.py` (exports)
6. Phase 1 completion report

---

## 🔄 **Iteration Strategy**

### **If Agent Encounters Issues:**
1. **Review test failures** - Tests define correct behavior
2. **Check dependencies** - Ensure modules imported correctly
3. **Review spec** - Clarify business logic
4. **Check existing implementations** - See core modules for patterns
5. **Ask for clarification** - If ambiguous

### **Quality Assurance:**
- Run tests after EVERY change
- Use watch mode for instant feedback
- Don't move to next test until current passes
- Refactor only when tests are green

---

## 💡 **Key TDD Principles**

### **Red → Green → Refactor:**
1. **Red:** Write/run test, see it fail
2. **Green:** Write minimum code to pass
3. **Refactor:** Clean up while keeping tests green

### **YAGNI (You Aren't Gonna Need It):**
- Only implement what tests require
- Don't add "future" features
- Keep it simple

### **Single Responsibility:**
- Each rule does ONE thing
- Extract helpers for clarity
- Keep `check()` method clean

---

## 📚 **Reference Documents**

### **For Agents:**
1. **TDD Guide:** `project-specs/SPECS/03-RISK-RULES/HOW_TO_ADD_NEW_RULES.md`
2. **Architecture:** `project-specs/SPECS/00-CORE-CONCEPT/system_architecture_v2.md`
3. **Module Specs:** `project-specs/SPECS/04-CORE-MODULES/modules/`
4. **Test Examples:** `tests/unit/test_state_manager.py` (reference for patterns)

### **Available for Reference:**
- All 9 core modules (working implementations)
- REST API client (working implementation)
- Test fixtures (139 ready-to-use fixtures)

---

## 🎯 **Ready to Execute**

**Phase 1 is ready to launch!**

All prerequisites met:
- ✅ Specifications complete
- ✅ Tests written
- ✅ Dependencies implemented
- ✅ Templates available
- ✅ TDD guide ready
- ✅ Swarm strategy defined

**Next:** Spawn Phase 1 swarm (4 agents, mesh topology)

---

**Document Version:** 1.0
**Created:** 2025-10-22
**Status:** Ready for execution
