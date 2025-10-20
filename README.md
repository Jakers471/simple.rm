# Trading Risk Manager - Fresh Start

**Status**: Planning Phase (Using SDK Agents)
**Last Updated**: 2025-10-19

---

## 📁 Project Structure

```
your-project/
├── COMMAND_MENU.md              ← 📋 SDK commands (START HERE!)
├── PROJECT_STRUCTURE.md         ← 📂 What each folder is
├── HOW_TO_USE_SDK/              ← 📖 SDK help docs
│   └── START_HERE.md            ← Quick SDK overview
├── docs/                        ← 📝 Fresh start (empty)
├── archive/OLD_PROJECT_DOCS/    ← 📦 Previous planning work
│   ├── architecture/
│   ├── rules/
│   └── modules/
└── references/claude-flow/      ← 🔧 SDK source (read-only)
```

---

## ⚡ Quick Start (3 Commands)

```bash
# 1. Initialize SDK (one time)
npx claude-flow@alpha init --force

# 2. Start interactive planning
npx claude-flow@alpha hive-mind wizard
# Tell it: "Plan trading risk manager. Check archive/OLD_PROJECT_DOCS/ for existing specs."

# 3. Review output, iterate!
```

---

## 🎯 What To Do

### 1. Read The Command Menu (2 minutes)
Open: **`COMMAND_MENU.md`** ← All SDK commands with examples

### 2. Initialize SDK (30 seconds)
```bash
npx claude-flow@alpha init --force
```

### 3. Let Agents Plan Your Project
```bash
npx claude-flow@alpha hive-mind wizard
```

Tell agents what you want in plain English. They'll handle the rest!

---

## 📦 About The Archived Docs

Your previous planning work is in `archive/OLD_PROJECT_DOCS/`:
- Architecture (ARCH-V2)
- 12 Risk Rules (RULE-001 to RULE-012)
- 4 Modules (MOD-001 to MOD-004)
- API integration specs

**Agents can reference these!** Just tell them:
```bash
"Check archive/OLD_PROJECT_DOCS/ for existing specifications"
```

---

## 🤔 How Prompting Works

**You use natural language** - no special syntax!

✅ **Good prompt**:
```bash
npx claude-flow@alpha sparc run planner "Create 3-phase implementation plan for trading risk manager. Check archive/OLD_PROJECT_DOCS/ for existing rule specs. Output with tasks and timelines."
```

❌ **Bad prompt**:
```bash
npx claude-flow@alpha sparc run planner "make plan"
```

**More specific = Better results**

---

## 📚 Documentation

- **COMMAND_MENU.md** - Quick command reference (use this most!)
- **PROJECT_STRUCTURE.md** - What each folder contains
- **HOW_TO_USE_SDK/** - Detailed SDK help (optional reading)

---

## 💡 Key Points

1. **SDK has 78 prebuilt agents** - planner, architect, researcher, coder, etc.
2. **You run commands** - `npx claude-flow@alpha sparc run [agent] "goal"`
3. **Agents do the work** - They plan, research, design, code
4. **Use natural language** - Just tell them what you want
5. **Fresh start** - Old docs are archived but available for reference

---

## 🚀 Recommended First Steps

### Option 1: Interactive (Easiest)
```bash
npx claude-flow@alpha hive-mind wizard
```

### Option 2: Specific Agent
```bash
# Have planner analyze old docs and create fresh plan
npx claude-flow@alpha sparc run planner "Review archive/OLD_PROJECT_DOCS/ and create updated implementation plan incorporating those specs"
```

### Option 3: Research & Plan
```bash
# Research best practices
npx claude-flow@alpha sparc run researcher "Research trading risk management patterns and Python frameworks for real-time systems"

# Then plan based on research
npx claude-flow@alpha sparc run planner "Based on research, create implementation plan for risk manager"
```

---

**TL;DR**: Read `COMMAND_MENU.md`, run `npx claude-flow@alpha hive-mind wizard`, tell it your goal!
