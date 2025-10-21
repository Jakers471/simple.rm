# 🎯 Risk Manager Project - Start Here

**Project Status:** Design & Specification Phase
**AI-First Development:** Building specs for AI agents to implement

---

## 🗺️ Project Organization

```
simple risk manager/
│
├── 📐 project-specs/              ← AI SPECIFICATIONS (YOUR MAIN FOCUS)
│   ├── AI_CONTEXT.md              ← 🔴 AI AGENTS: READ THIS FIRST!
│   ├── SPECS/                     ← Organized specifications
│   │   ├── 00-CORE-CONCEPT/       ✅ Architecture & overview
│   │   ├── 01-EXTERNAL-API/       ✅ TopstepX API docs
│   │   ├── 02-BACKEND-DAEMON/     ⏳ Daemon specs (TODO)
│   │   ├── 03-RISK-RULES/         ✅ All 12 risk rules
│   │   ├── 04-CORE-MODULES/       ✅ 4 core modules
│   │   ├── 05-INTERNAL-API/       🔴 CRITICAL - Decision needed
│   │   ├── 06-CLI-FRONTEND/       ⏳ UI specs (TODO)
│   │   ├── 07-DATA-MODELS/        ⏳ Data structures (TODO)
│   │   ├── 08-CONFIGURATION/      ⏳ Config specs (TODO)
│   │   └── 99-IMPLEMENTATION-GUIDES/ (Future)
│   ├── PROJECT_DOCS/              ← Original documentation
│   └── TEMPLATES/                 ← Code templates (future)
│
├── 📂 sdk/                        ← Claude Flow SDK (isolated)
│   ├── .claude/                   ← Agents & commands
│   ├── .claude-flow/              ← Metrics
│   ├── coordination/              ← Orchestration
│   ├── memory/                    ← Agent memory
│   └── node_modules/              ← SDK dependencies
│
├── 💼 YOUR RISK MANAGER PROJECT:
│   ├── src/                       ← Source code (empty - ready to build)
│   ├── config/                    ← Config files (empty)
│   ├── scripts/                   ← Utility scripts (empty)
│   ├── tests/                     ← Tests (empty)
│   │
│   ├── examples/                  ← CLI/GUI examples
│   │   ├── cli/trader/            ← Trader CLI examples
│   │   ├── cli/admin/             ← Admin CLI examples
│   │   ├── gui/                   ← GUI examples
│   │   └── web/                   ← Web examples
│   │
│   ├── risk-manager-docs/         ← Your documentation
│   ├── references/                ← Reference materials
│   ├── reports/                   ← Project reports
│   └── user.reference.md/         ← User references
│
└── 📦 Project Files:
    ├── package.json               ← NPM config
    └── .gitignore                 ← Git ignore rules
```

---

## 🚀 Quick Start Guide

### For AI Agents (Claude Code, etc.):
```
1. Read: project-specs/AI_CONTEXT.md
   ↳ Tells you project status, what's done, what's needed

2. Navigate to: project-specs/SPECS/
   ↳ See SPECS/README.md for navigation

3. Check for _TODO.md files:
   ↳ These show what needs design work

4. Ready to implement?
   ↳ Only if no _TODO.md in relevant folder
```

### For You (Project Owner):
```
1. Current Phase: Designing specs
2. Next Critical Decision: Internal API protocol
   ↳ See: project-specs/SPECS/05-INTERNAL-API/COMMUNICATION_PROTOCOL.md
   ↳ Choose: HTTP API, Named Pipes, or SQLite?

3. Continue working with agents to:
   ↳ Complete missing specs (02, 05, 06, 07, 08)
   ↳ Make design decisions
   ↳ Document everything for AI implementation
```

---

## 🎯 Current Status

### ✅ Complete Specs (Ready for AI Implementation):
- **Architecture** - Complete system design (ARCH-V2)
- **Risk Rules** - All 12 rules fully specified
- **Core Modules** - All 4 modules fully specified
- **External API** - TopstepX integration documented

### ⏳ Incomplete Specs (Need Design Work):
- **Backend Daemon** - How daemon works internally
- **Internal API** - 🔴 CRITICAL - How CLI talks to daemon
- **CLI Frontend** - User interface specifications
- **Data Models** - Exact data structures
- **Configuration** - Complete config file specs

### 🚫 Future Work (Don't Start Yet):
- Implementation guides
- Code templates
- Actual code implementation
- Testing

---

## 📋 Next Steps

**Immediate Priorities:**

1. **Make Critical Decision** (BLOCKING):
   - Read: `project-specs/SPECS/05-INTERNAL-API/COMMUNICATION_PROTOCOL.md`
   - Choose communication protocol
   - This unblocks CLI and daemon implementation

2. **Complete Data Models**:
   - Work with AI to define exact Python dataclasses
   - Define SQLite database schema
   - Document API response formats

3. **Define CLI Specifications**:
   - What screens does trader CLI have?
   - What screens does admin CLI have?
   - What UI library to use?

4. **Complete Config Specs**:
   - Full YAML specification
   - Validation rules
   - Example configs

**Then:** Start implementation with AI agents

---

## 🔑 Key Files for AI

**Start Here:**
- `project-specs/AI_CONTEXT.md` - AI agent entry point

**Architecture:**
- `project-specs/SPECS/00-CORE-CONCEPT/architecture/system_architecture_v2.md`

**Critical Missing Piece:**
- `project-specs/SPECS/05-INTERNAL-API/COMMUNICATION_PROTOCOL.md`

**All Specs Navigation:**
- `project-specs/SPECS/README.md`

---

## 💡 Philosophy

This is an **AI-first project**:
- Specs are written FOR AI agents to implement
- Precision over prose
- Complete specifications enable autonomous implementation
- Human makes decisions, AI executes

**Current Goal:** Get specs 100% complete so AI can build the system autonomously.

---

## 📞 Quick Reference

**To work on specs:**
```bash
cd project-specs/SPECS/
# Find _TODO.md files
# Work with AI to complete them
```

**To see what's already defined:**
```bash
cd project-specs/PROJECT_DOCS/
# Original documentation lives here
# Linked into SPECS/ for organization
```

**To view examples:**
```bash
cd examples/
# CLI and GUI examples for inspiration
```

---

**Last Updated:** 2025-01-21
**Current Phase:** Design & Specification
**Next Milestone:** Complete all SPECS/ sections, then begin implementation

🤖 **AI Agents:** Read `project-specs/AI_CONTEXT.md` first!
