# 📐 Documentation Structure Guide

**For:** Next AI Agent (Spec Writer)
**Purpose:** Explains how documentation is organized and what needs to be filled in

---

## 🗂️ File Organization Pattern

```
SPECS/
├── 00-CORE-CONCEPT/          ✅ COMPLETE
├── 01-EXTERNAL-API/          ✅ COMPLETE
├── 02-BACKEND-DAEMON/        📝 Has placeholders → Fill these
├── 03-RISK-RULES/            ✅ COMPLETE
├── 04-CORE-MODULES/          ✅ COMPLETE
├── 05-INTERNAL-API/          📝 Has COMMUNICATION_PROTOCOL + placeholders
├── 06-CLI-FRONTEND/          📝 Has placeholders → Fill these
├── 07-DATA-MODELS/           📝 Has placeholders → Fill these
├── 08-CONFIGURATION/         📝 Has placeholders → Fill these
└── 99-IMPLEMENTATION-GUIDES/ 🔮 Future (during coding phase)
```

---

## 📝 What "Placeholder" Means

Each **placeholder file** looks like this:

```markdown
# FILENAME.md

**Status:** 📝 Placeholder - Needs Spec
**Purpose:** [What this spec is for]

---

## To Be Documented:

- Topic 1
- Topic 2
- Topic 3

---

**Next Agent:** Fill this with [description]
```

**Your Job:** Replace the entire file with the actual detailed specification

---

## 🎯 What Needs to Be Filled

### **02-BACKEND-DAEMON/** (3 files)
- `DAEMON_ARCHITECTURE.md` - How daemon works internally
- `EVENT_PIPELINE.md` - Event flow from TopstepX → Enforcement
- `STATE_MANAGEMENT.md` - Memory + SQLite persistence

### **05-INTERNAL-API/** (4 files)
- `COMMUNICATION_PROTOCOL.md` - ⚠️ USER DECISION NEEDED FIRST
- `DAEMON_ENDPOINTS.md` - What daemon exposes
- `CLI_TO_DAEMON_CONTRACTS.md` - Request/response formats
- `REAL_TIME_UPDATES.md` - How CLI gets live updates

### **06-CLI-FRONTEND/** (3 files)
- `ADMIN_CLI_SPEC.md` - Admin interface complete spec
- `TRADER_CLI_SPEC.md` - Trader interface complete spec
- `UI_COMPONENTS.md` - Reusable UI elements

### **07-DATA-MODELS/** (4 files)
- `STATE_OBJECTS.md` - Python dataclasses
- `DATABASE_SCHEMA.md` - SQLite schema
- `EVENT_PAYLOADS.md` - TopstepX event formats
- `API_RESPONSE_FORMATS.md` - Internal API responses

### **08-CONFIGURATION/** (3 files)
- `ACCOUNTS_YAML_SPEC.md` - accounts.yaml complete spec
- `RISK_CONFIG_YAML_SPEC.md` - risk_config.yaml complete spec
- `CONFIG_VALIDATION.md` - Validation rules

---

## 📋 Spec Format Template

Each completed spec should follow this structure:

```markdown
---
doc_id: [SECTION]-[NUMBER]
title: [Spec Title]
version: 1.0
status: COMPLETE | DRAFT | REVIEW_NEEDED
last_updated: YYYY-MM-DD
dependencies: [Other doc_ids this depends on]
---

# [Spec Title]

## Overview
[Brief description of what this spec covers]

## [Section 1]
[Detailed specification content]

## [Section 2]
[More detailed content]

## Examples
[Code/config/JSON examples]

## Validation
[How to know if implementation is correct]

## Dependencies
[What this relies on]
```

---

## 🔑 Key Principles

### 1. **AI-Implementable**
- Detailed enough that an AI can generate working code
- No ambiguity - be precise
- Include examples (code snippets, JSON, YAML)

### 2. **Self-Contained**
- Each spec should be understandable on its own
- Reference other specs via doc_id when needed
- Don't duplicate - reference instead

### 3. **Complete**
- Cover ALL aspects of the topic
- Don't leave gaps for "later"
- If something is unknown, mark it as "DECISION_NEEDED"

### 4. **Structured**
- Use consistent formatting
- Use headers, lists, code blocks
- Make it scannable

---

## 🎓 How to Fill Specs

### **Step 1: Interview User**
- Ask questions about the topic
- Clarify ambiguities
- Get decisions on open questions
- Understand their vision

### **Step 2: Research Existing Docs**
- Read related completed specs
- Check architecture docs (00-CORE-CONCEPT/)
- Look at rule/module examples (03, 04)
- Understand the full context

### **Step 3: Write Complete Spec**
- Replace placeholder file entirely
- Follow spec format template
- Include all sections
- Add examples
- Be thorough

### **Step 4: Cross-Reference**
- Update `AI_CONTEXT.md` if section is complete
- Add doc_id to related specs' dependency lists
- Ensure consistency across specs

---

## 🚫 What NOT to Do

- ❌ Don't leave placeholder text
- ❌ Don't write partial specs ("to be added later")
- ❌ Don't assume - ask user if unclear
- ❌ Don't duplicate specs from other files
- ❌ Don't write implementation code yet

---

## ✅ Completion Checklist

For each placeholder file you fill:

- [ ] Interviewed user about the topic
- [ ] Read all related existing specs
- [ ] Wrote complete specification
- [ ] Included code/config/JSON examples
- [ ] Added doc_id header
- [ ] Listed dependencies
- [ ] Verified no ambiguities
- [ ] Cross-referenced in other specs if needed

---

## 📊 Progress Tracking

**Current Status:**
- ✅ Complete: 00, 01, 03, 04
- 📝 Needs Specs: 02, 05, 06, 07, 08
- 🔮 Future: 99, TEMPLATES

**Priority Order:**
1. 05-INTERNAL-API (critical - blocks CLI work)
2. 07-DATA-MODELS (foundational)
3. 02-BACKEND-DAEMON (core system)
4. 06-CLI-FRONTEND (user-facing)
5. 08-CONFIGURATION (supporting)

---

## 🔄 Workflow

```
1. User + You → Discuss topic, make decisions
2. You → Fill placeholder with complete spec
3. Update AI_CONTEXT.md → Mark progress
4. Move to next placeholder
5. Repeat until all placeholders filled
```

**End Goal:** Every file in SPECS/ is either ✅ complete or 🔮 marked for future

---

**Remember:** This is the foundation for AI to build the entire system. Make it bulletproof.
