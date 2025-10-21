# 📋 TODO - Implementation Guides

**Status:** Future Work
**Priority:** LOW (Complete Specs First)
**For AI:** Step-by-step guides for implementing each component

---

## 🎯 What This Section Will Contain

**Purpose:** Bridge gap between specs → working code

These guides will be created AFTER all specs are complete and ready for implementation.

---

## 📋 Planned Implementation Guides

### 1. BACKEND_IMPLEMENTATION.md
**Purpose:** How to implement the backend daemon

**Will Cover:**
- Project setup (directory structure, dependencies)
- Implementing each layer (API, core, rules, state)
- Order of implementation (what to build first)
- Testing strategy for each component
- Integration points

**Implementation Order:**
1. State management (SQLite + in-memory)
2. API client (TopstepX REST + SignalR)
3. Core modules (MOD-001 through MOD-004)
4. Rules (start with 3 simple ones)
5. Daemon wrapper
6. Windows Service integration

---

### 2. CLI_IMPLEMENTATION.md
**Purpose:** How to implement the CLI tools

**Will Cover:**
- Shared UI component library
- Trader CLI implementation
- Admin CLI implementation
- Testing CLIs
- Connecting to daemon

**Implementation Order:**
1. UI component library (tables, timers, etc.)
2. Daemon client (internal API wrapper)
3. Trader CLI (read-only first)
4. Admin CLI (adds write operations)

---

### 3. TESTING_STRATEGY.md
**Purpose:** How to test the system

**Will Cover:**
- **Unit Tests:**
  - Test each rule independently
  - Test each module independently
  - Mock TopstepX API responses
  - Mock time/date for testing resets

- **Integration Tests:**
  - Full event pipeline (SignalR → Rule → Enforcement)
  - State persistence (write → restart → read)
  - CLI ↔ Daemon communication

- **Manual Testing:**
  - How to test with TopstepX demo account
  - How to simulate breach scenarios
  - How to verify lockouts work correctly

**Test Coverage Goals:**
- All rules: 100%
- All modules: 100%
- Core daemon logic: 90%+

---

### 4. DEPLOYMENT.md
**Purpose:** How to install and run in production

**Will Cover:**
- **Windows Service Installation:**
  - Running `install_service.py`
  - Service permissions
  - Auto-start configuration

- **Configuration Setup:**
  - Where to place config files
  - How to set up TopstepX API key
  - How to set admin password

- **Monitoring:**
  - Log file locations
  - What to monitor (daemon uptime, API connectivity)
  - Alert conditions

- **Backup & Recovery:**
  - Database backup schedule
  - How to restore state after crash
  - Config file backups

- **Troubleshooting:**
  - Common issues
  - How to debug
  - Log analysis

---

### 5. PHASE_1_QUICKSTART.md
**Purpose:** Fast path to a minimal working system

**Will Cover:**
- **Phase 1 Scope:**
  - 3 rules: MaxContracts, MaxContractsPerInstrument, SessionBlockOutside
  - Trader CLI (view-only)
  - No admin CLI yet
  - Manual config editing

- **Fast Implementation Path:**
  - Skip Windows Service (run daemon directly)
  - Skip admin CLI (edit YAML by hand)
  - Focus on core functionality

- **Goal:**
  - Get something working in 1-2 days
  - Validate architecture
  - Prove concept works
  - Then expand to full feature set

---

## 🚫 Do Not Create These Yet!

**Why Wait:**
1. Specs must be 100% complete first
2. Implementation guides reference completed specs
3. No point writing guides if specs change
4. Specs are priority - guides are helpers

---

## 🔗 Dependencies

**Requires ALL of these to be complete:**
- `../00-CORE-CONCEPT/` ✅ (complete)
- `../01-EXTERNAL-API/` ✅ (complete)
- `../02-BACKEND-DAEMON/` ⏳ (in progress)
- `../03-RISK-RULES/` ✅ (complete)
- `../04-CORE-MODULES/` ✅ (complete)
- `../05-INTERNAL-API/` ⏳ (waiting for decision)
- `../06-CLI-FRONTEND/` ⏳ (not started)
- `../07-DATA-MODELS/` ⏳ (not started)
- `../08-CONFIGURATION/` ⏳ (not started)

---

## 🚀 When to Create These

**Trigger:** When user says "specs are done, time to implement"

**Creation Order:**
1. PHASE_1_QUICKSTART.md (minimal viable product)
2. BACKEND_IMPLEMENTATION.md (core functionality)
3. CLI_IMPLEMENTATION.md (user interfaces)
4. TESTING_STRATEGY.md (validation)
5. DEPLOYMENT.md (production setup)

---

## 💡 For Now

**Current Focus:**
- Complete specs in sections 02, 05, 06, 07, 08
- Make design decisions (internal API protocol, etc.)
- Ensure all specs are AI-implementable

**This section stays as `_TODO.md` until implementation phase begins.**

---

**Status:** 🚫 DO NOT IMPLEMENT YET - FINISH SPECS FIRST
