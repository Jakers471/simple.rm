# Project Structure - What's What

**Last Updated**: 2025-10-19

---

## 📂 Your Actual Project (Risk Manager)

These are YOUR docs for the risk manager you're building:

```
docs/
├── architecture/
│   ├── system_architecture_v1.md    ← Your original architecture
│   └── system_architecture_v2.md    ← Your current architecture (ARCH-V2)
├── rules/
│   ├── 01_max_contracts.md          ← RULE-001
│   ├── 02_max_contracts_per_instrument.md  ← RULE-002
│   ├── ...                          ← RULE-003 to RULE-012
│   └── 12_trade_management.md
├── modules/
│   ├── enforcement_actions.md       ← MOD-001
│   ├── lockout_manager.md           ← MOD-002
│   ├── timer_manager.md             ← MOD-003
│   └── reset_scheduler.md           ← MOD-004
├── api/
│   └── topstepx_integration.md      ← API integration docs
└── summary/
    └── project_overview.md

projectx_gateway_api/                ← TopstepX API reference docs
```

**These define WHAT you're building** (your specs, rules, architecture)

---

## 🆘 SDK Help Docs (For You To Read)

These are MY explanations to help YOU understand how to use the SDK:

```
HOW_TO_USE_SDK/
├── START_HERE.md                    ← Read this first!
├── SDK_README.md                    ← Quick overview
├── SDK_HOW_IT_ACTUALLY_WORKS.md     ← Detailed explanation
├── SDK_VISUAL_EXPLANATION.md        ← Visual diagrams
└── SDK_QUICK_START.md               ← Command reference
```

**These are NOT for agents** - they're for YOU to understand the SDK.

**Agents don't need these** - they have their own instructions in the SDK.

---

## 📚 SDK Reference (Read-Only)

The actual SDK codebase with all agent definitions:

```
references/claude-flow/              ← Full SDK source (read-only)
├── .claude/
│   └── agents/                      ← Agent instruction files (78 agents)
│       ├── core/planner.md
│       ├── core/coder.md
│       └── [78 total .md files]
├── docs/                            ← SDK documentation
└── src/                             ← SDK source code
```

**This is reference only** - you don't edit these files.

---

## 🗄️ Archive (Old Stuff)

```
archive/
└── agents/                          ← Your old custom agents (archived)
    ├── planner_agent.md
    ├── deep_spec.md
    └── integration-alignment-auditor.md
```

**Archived** - not using these anymore (replaced by SDK agents).

---

## 📁 Empty Folders (Can Probably Delete)

These were created but are empty:

```
src/         ← Empty (no code yet)
tests/       ← Empty (no tests yet)
scripts/     ← Empty (no scripts yet)
config/      ← Empty (no config yet)
reports/     ← Has some old reports (not sure what these are)
```

**You can delete these empty folders if you want** - they'll be created later when you start coding.

---

## 🎯 What To Focus On

### Your Project Docs (Keep & Use)
- ✅ `docs/architecture/` - Your architecture
- ✅ `docs/rules/` - Your 12 risk rules
- ✅ `docs/modules/` - Your 4 modules
- ✅ `docs/api/` - Your API integration
- ✅ `projectx_gateway_api/` - API reference

### SDK Help (Read Once, Then Ignore)
- 📖 `HOW_TO_USE_SDK/START_HERE.md` - Read this to understand SDK
- 📖 Other SDK docs - Only if you need more detail

### SDK Reference (Leave Alone)
- 📚 `references/claude-flow/` - Read-only reference, don't touch

### Archive (Ignore)
- 🗄️ `archive/` - Old stuff, not using anymore

---

## 🤔 Still Confused About Folders?

**Simple version**:

| Folder | What It Is | Do You Touch It? |
|--------|-----------|------------------|
| `docs/` | YOUR project specs | ✅ Yes - this is your project |
| `HOW_TO_USE_SDK/` | MY help docs for you | 📖 Read once |
| `references/claude-flow/` | SDK source code | ❌ No - read-only reference |
| `archive/` | Old custom agents | ❌ No - archived |
| `src/`, `tests/`, etc. | Empty folders | ⚠️ Delete or ignore until coding |

---

## 🎯 What Should You Do Now?

1. **Read**: `HOW_TO_USE_SDK/START_HERE.md` (2 minutes)
2. **Run**: `npx claude-flow@alpha init --force` (30 seconds)
3. **Use**: Let SDK agents do your planning:
   ```bash
   npx claude-flow@alpha sparc run planner "create implementation plan"
   ```

**That's it!** The agents read YOUR docs (in `docs/`) and do the planning/work.

---

## 🧹 Want To Clean Up?

If you want to simplify:

```bash
# Delete empty folders
rm -rf src tests scripts config

# Keep:
# - docs/ (your project)
# - HOW_TO_USE_SDK/ (read these)
# - references/ (SDK reference)
# - projectx_gateway_api/ (API docs)
```

**But it's not necessary** - empty folders don't hurt anything.
