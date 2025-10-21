# Trading Risk Manager - Fresh Start with SDK

**Last Updated**: 2025-10-19
**Status**: Planning Phase

---

## ⚡ Quick Start (3 Steps)

```bash
# 1. Initialize SDK (30 seconds)
npx claude-flow@alpha init --force

# 2. Start planning (interactive - easiest!)
npx claude-flow@alpha hive-mind wizard

# 3. Tell it your goal!
# Example: "Plan trading risk manager. Check archive/OLD_PROJECT_DOCS/ for existing specs."
```

**That's it!** Agents take over from there.

---

## 📋 Command Reference

**COMMAND_MENU.md** ← **Complete list of 180+ SDK commands**
- All agents, workflows, features documented
- Organized by category
- Copy-paste examples

**COMMAND_MENU_SIMPLE.md** ← Simplified version (most common commands only)

---

## 📂 Project Structure

```
your-project/
├── COMMAND_MENU.md              ← 📋 Complete SDK commands (180+)
├── COMMAND_MENU_SIMPLE.md       ← 📋 Simplified commands (common ones)
├── PROJECT_STRUCTURE.md         ← 📂 What each folder is
├── START_HERE.md                ← 🚀 This file
│
├── HOW_TO_USE_SDK/              ← 📖 SDK help docs
│   ├── README.md                ← Navigation
│   ├── START_HERE.md            ← Quick overview
│   └── [detailed docs]          ← Optional reading
│
├── docs/                        ← 📝 Fresh start (empty)
├── archive/OLD_PROJECT_DOCS/    ← 📦 Previous work (reference)
│   ├── architecture/
│   ├── rules/ (RULE-001 to 012)
│   └── modules/ (MOD-001 to 004)
│
└── references/claude-flow/      ← 🔧 SDK source (don't touch)
```

---

## 💡 Key Points

1. **SDK has 180+ commands** - Check COMMAND_MENU.md
2. **All commands listed** - Complete reference now available
3. **Use natural language** - No special syntax for prompts
4. **Archived docs available** - Tell agents to check `archive/OLD_PROJECT_DOCS/`
5. **Fresh start** - New `docs/` folder for planning output

---

## 🎯 What To Do

### Option 1: Interactive (Recommended)
```bash
npx claude-flow@alpha hive-mind wizard
```
Follow prompts, tell it your goal.

### Option 2: Specific Agent
```bash
npx claude-flow@alpha sparc run planner "Create implementation plan for trading risk manager. Reference archive/OLD_PROJECT_DOCS/ for existing specs."
```

### Option 3: Research First
```bash
npx claude-flow@alpha sparc run researcher "Research Python frameworks for real-time event processing"
```

---

## ❓ Common Questions

**Q: Do I have all SDK commands now?**
A: YES! COMMAND_MENU.md has the complete list (180+ commands).

**Q: What about prompts - do I need special syntax?**
A: NO! Just use natural language. Be specific about what you want.

**Q: Can agents use my old project docs?**
A: YES! Tell them: "Check archive/OLD_PROJECT_DOCS/ for context"

**Q: Which commands should I start with?**
A: `hive-mind wizard` (easiest) or `sparc run planner "your goal"`

---

## 📖 More Info

- **COMMAND_MENU.md** - All 180+ SDK commands
- **PROJECT_STRUCTURE.md** - What each folder is
- **HOW_TO_USE_SDK/** - Detailed SDK help (optional)

---

**TL;DR**:
1. Read `COMMAND_MENU.md` for all commands
2. Run `npx claude-flow@alpha hive-mind wizard`
3. Tell it your goal
4. Agents do the work!
