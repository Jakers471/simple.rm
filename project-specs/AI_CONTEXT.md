# 🤖 AI Context - Risk Manager Project

**Last Updated:** 2025-01-21
**Current Phase:** Design & Specification
**Build Status:** Pre-implementation - gathering requirements

---

## 📍 Where We Are Right Now

### ✅ What's Complete
1. **System Architecture** - SPECS/00-CORE-CONCEPT/system_architecture_v2.md (ARCH-V2)
   - Complete directory structure defined
   - Layer architecture documented
   - 12 risk rules identified
   - 4 core modules specified

2. **External API Documentation** - SPECS/01-EXTERNAL-API/projectx_gateway_api/
   - TopstepX Gateway API endpoints documented
   - Authentication flow defined
   - SignalR events documented

3. **Risk Rules Specifications** - SPECS/03-RISK-RULES/
   - 12 rule specifications written
   - Each rule has enforcement logic defined
   - Configuration formats specified

4. **Core Module Specifications** - SPECS/04-CORE-MODULES/
   - MOD-001: Enforcement Actions
   - MOD-002: Lockout Manager
   - MOD-003: Timer Manager
   - MOD-004: Reset Scheduler

### 🚧 What Needs Specs Written (PLACEHOLDER FILES READY)

**Next agent's job:** Fill placeholder files with complete specifications

1. **02-BACKEND-DAEMON/** (3 placeholder files)
   - DAEMON_ARCHITECTURE.md
   - EVENT_PIPELINE.md
   - STATE_MANAGEMENT.md

2. **05-INTERNAL-API/** (4 files - 1 complete, 3 placeholders)
   - ✅ COMMUNICATION_PROTOCOL.md (decision framework ready)
   - 📝 DAEMON_ENDPOINTS.md (placeholder)
   - 📝 CLI_TO_DAEMON_CONTRACTS.md (placeholder)
   - 📝 REAL_TIME_UPDATES.md (placeholder)

3. **06-CLI-FRONTEND/** (3 placeholder files)
   - ADMIN_CLI_SPEC.md
   - TRADER_CLI_SPEC.md
   - UI_COMPONENTS.md

4. **07-DATA-MODELS/** (4 placeholder files)
   - STATE_OBJECTS.md
   - DATABASE_SCHEMA.md
   - EVENT_PAYLOADS.md
   - API_RESPONSE_FORMATS.md

5. **08-CONFIGURATION/** (3 placeholder files)
   - ACCOUNTS_YAML_SPEC.md
   - RISK_CONFIG_YAML_SPEC.md
   - CONFIG_VALIDATION.md

### ⏳ What's Next (Future Work)
1. Implementation guides (99-IMPLEMENTATION-GUIDES/)
2. Code templates (TEMPLATES/)
3. Testing strategy
4. Deployment procedures

---

## 🎯 Current Goal

**PRIMARY OBJECTIVE:** Fill all placeholder files with complete, detailed specifications.

**STRUCTURE COMPLETE:** File/folder organization is done. Now fill the placeholders.

**NEXT AGENT READS:** `DOCUMENTATION_STRUCTURE_GUIDE.md` for instructions

---

## 🗺️ How to Navigate This Project (For AI Agents)

### If you're asked to implement a risk rule:
1. Read: `SPECS/00-CORE-CONCEPT/system_architecture_v2.md` (understand architecture)
2. Read: `SPECS/03-RISK-RULES/RULE-XXX_*.md` (specific rule requirements)
3. Read: `SPECS/04-CORE-MODULES/MOD-001_enforcement_actions.md` (how to enforce)
4. Read: `SPECS/01-EXTERNAL-API/projectx_gateway_api/` (how to interact with broker)

### If you're asked to build the daemon:
1. Read: `SPECS/00-CORE-CONCEPT/system_architecture_v2.md` (full architecture)
2. Read: `SPECS/02-BACKEND-DAEMON/` (daemon-specific specs - IN PROGRESS)
3. Read: `SPECS/05-INTERNAL-API/` (how to expose state to CLIs - IN PROGRESS)
4. Read: `SPECS/07-DATA-MODELS/` (data structures - IN PROGRESS)

### If you're asked to build the CLI:
1. Read: `SPECS/06-CLI-FRONTEND/` (UI requirements - IN PROGRESS)
2. Read: `SPECS/05-INTERNAL-API/` (how to talk to daemon - IN PROGRESS)
3. Read: `SPECS/07-DATA-MODELS/` (what data looks like - IN PROGRESS)

### If you're asked to help design/document:
1. Read `DOCUMENTATION_STRUCTURE_GUIDE.md` for full instructions
2. Find placeholder files (marked with 📝 Placeholder)
3. Interview user about the topic
4. Fill placeholder with complete specification
5. Update this AI_CONTEXT.md when completing files

---

## 🧭 Project Structure Quick Reference

```
project-specs/
├── AI_CONTEXT.md                    ← YOU ARE HERE (read this first!)
│
├── SPECS/
│   ├── 00-CORE-CONCEPT/            ← System overview & architecture
│   ├── 01-EXTERNAL-API/            ← TopstepX API integration
│   ├── 02-BACKEND-DAEMON/          ← Daemon implementation specs
│   ├── 03-RISK-RULES/              ← Individual rule specifications
│   ├── 04-CORE-MODULES/            ← Shared module specifications
│   ├── 05-INTERNAL-API/            ← CLI ↔ Daemon communication (CRITICAL!)
│   ├── 06-CLI-FRONTEND/            ← User interface specifications
│   ├── 07-DATA-MODELS/             ← Data structures & schemas
│   ├── 08-CONFIGURATION/           ← Config file specifications
│   └── 99-IMPLEMENTATION-GUIDES/   ← How to build each component
│
└── TEMPLATES/                       ← Code templates for implementation
```

---

## 🔑 Key Architectural Concepts

### The System Has 3 Main Parts:

1. **Backend Daemon** (`src/core/`, `src/api/`, `src/enforcement/`, `src/rules/`, `src/state/`)
   - Runs as Windows Service
   - Listens to TopstepX SignalR events
   - Checks rules on every event
   - Enforces violations via REST API
   - Manages state in SQLite

2. **Internal API** (TO BE DESIGNED - see SPECS/05-INTERNAL-API/)
   - Daemon exposes state to CLI tools
   - CLIs query current status
   - CLIs receive real-time updates
   - **DECISION NEEDED:** Communication method

3. **CLI Frontends** (`src/cli/admin/`, `src/cli/trader/`)
   - Admin CLI: password-protected, can modify config
   - Trader CLI: view-only, shows status & timers
   - Both connect to daemon via internal API

### Data Flow:
```
TopstepX (Broker)
    ↓ SignalR events
Backend Daemon (risk engine)
    ↓ state changes
Internal API
    ↓ queries/updates
CLI Frontends (admin/trader)
```

---

## 💡 Design Principles (Why We Made These Choices)

1. **Event-Driven Architecture:** No polling, react to TopstepX events
2. **Modular Rules:** Each rule = one file, easy to add/remove
3. **Centralized Enforcement:** All rules use MOD-001 (no duplication)
4. **State Persistence:** SQLite ensures recovery from crashes
5. **No Blocking:** Can't prevent orders, but close within milliseconds
6. **File Size Limit:** No file over 200 lines (maintainability)

---

## 📋 Open Questions (Need User Input)

### Critical Decisions Needed:
1. **Internal API Communication Method**
   - HTTP REST API on localhost?
   - Named Pipes (Windows IPC)?
   - Direct SQLite reads?
   - WebSocket for real-time?

2. **CLI Update Mechanism**
   - Poll every second?
   - Server-sent events?
   - WebSocket stream?
   - Database watch?

3. **Admin CLI Authentication**
   - Password hash in file?
   - Windows authentication?
   - API key?

### Design Clarifications Needed:
- Exact SQLite schema (tables, columns, indexes)
- Exact state object structures (Python dataclasses)
- CLI screen layouts (what info on each screen?)
- Configuration validation rules (what makes config invalid?)

---

## 🎓 Context for AI Agents

**This is not a typical software project.** This is an AI-assisted design and build process where:
- The user (project owner) is collaborating with AI agents to design AND build
- Specifications are primarily for AI consumption, not human developers
- Documentation needs to be precise enough for AI to generate working code
- Open questions in specs are intentional - waiting for user decisions

**When you see a `_TODO.md` file:** That section needs design work. Ask the user questions to help make decisions, then document the answers.

**When you see detailed specs:** Those are ready for implementation. You can generate code from them.

---

## 🚀 How to Help

### If user asks you to continue design work:
1. Identify which SPECS folder has `_TODO.md`
2. Read related existing specs for context
3. Ask clarifying questions
4. Document decisions in new spec files
5. Update this AI_CONTEXT.md

### If user asks you to implement something:
1. Check if specs are complete (no `_TODO.md` in that area)
2. If incomplete: flag missing specs, help complete them first
3. If complete: read all related specs, then generate code
4. Follow architecture exactly as specified

### If user asks for your opinion:
1. Reference the design principles above
2. Suggest options that align with existing architecture
3. Explain tradeoffs clearly
4. Let user make final decision

---

## 📞 Common Questions Answered

**Q: Where do I start reading?**
A: `SPECS/00-CORE-CONCEPT/system_architecture_v2.md` - the master architecture doc

**Q: Can I change the architecture?**
A: Only with user approval. Suggest changes but don't implement without confirmation.

**Q: What if I find incomplete specs?**
A: Note what's missing, ask user for guidance, help document the decisions.

**Q: Should I generate code now?**
A: Only if the relevant specs are complete. Check for `_TODO.md` files first.

**Q: How detailed should specs be?**
A: Detailed enough that AI can generate working code without ambiguity.

---

## 🔄 Update Log

- **2025-01-21:** File/folder structure complete
  - Existing docs moved into SPECS/
  - Placeholder files created for missing specs
  - DOCUMENTATION_STRUCTURE_GUIDE.md created for next agent
  - Ready for next agent to fill placeholders

---

**Remember:** This file is your north star. When in doubt, read this first, then dive into specific SPECS folders.
