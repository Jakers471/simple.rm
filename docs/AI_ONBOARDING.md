# AI Onboarding - How to Get Up to Speed

**For AI assistants picking up this project**

When user asks: **"where did we leave off?"** or **"what's the status?"**

Follow this protocol:

---

## 📖 REQUIRED READING ORDER

Read these files **IN THIS EXACT ORDER:**

### 1. START HERE (30 seconds)
```
/START_HERE.md
```
**What it tells you:**
- Current phase (1, 2, or 3)
- Overall completion percentage
- What exists vs what's missing
- Immediate next steps

### 2. Current Phase Plan (2 minutes)
```
/docs/PHASE_1_BUILD_PLAN.md  ← If phase 1
/docs/PHASE_2_BUILD_PLAN.md  ← If phase 2
/docs/PHASE_3_BUILD_PLAN.md  ← If phase 3
```
**What it tells you:**
- Detailed task breakdown
- What's ⏳ NOT STARTED vs ✅ COMPLETE
- Estimated time for each task
- Files to create
- Files to read for context

### 3. Actual Status (1 minute)
```
/docs/ACTUAL_STATUS_2025-10-23.md
```
**What it tells you:**
- Honest assessment of completion
- What library code exists
- What's missing (critical)
- Timeline estimates

### 4. Quick Source Code Scan (1 minute)
```bash
ls -la src/core/       # What modules exist
ls -la src/rules/      # What rules exist
ls -la src/api/        # What API code exists
ls -la src/cli/        # CLIs built yet?
ls -la data/           # Database exists?
ls -la config/         # Configs created?
```
**What it tells you:**
- Actual files that exist
- What's been built vs planned

---

## 🎯 QUICK STATUS CHECK (Run These Commands)

```bash
cd "/home/jakers/projects/simple-risk-manager/simple risk manager"

# Check virtual environment
which python
# Should show: .../venv/bin/python

# Run tests to see what works
source venv/bin/activate
python -m pytest tests/unit/test_enforcement_actions.py -v
# Should show: 8/8 tests passing

# Check database
ls -la data/state.db 2>/dev/null || echo "NO DATABASE YET"

# Check configs
ls -la config/*.yaml

# Check what needs building
ls -la src/core/daemon.py 2>/dev/null || echo "DAEMON NOT BUILT YET"
ls -la src/core/event_router.py 2>/dev/null || echo "EVENT ROUTER NOT BUILT YET"
```

---

## 📚 CONTEXT FILES (Read If Needed)

**Only read these if working on specific tasks:**

### For Building Daemon (Phase 1, Task 4)
```
project-specs/SPECS/02-BACKEND-DAEMON/DAEMON_ARCHITECTURE.md
project-specs/SPECS/02-BACKEND-DAEMON/EVENT_PIPELINE.md
src/api/signalr_manager.py  ← Already exists, use this!
src/core/enforcement_actions.py  ← See how to call it
```

### For Building Event Router (Phase 1, Task 3)
```
project-specs/SPECS/02-BACKEND-DAEMON/EVENT_PIPELINE.md  ← CRITICAL!
src/core/lockout_manager.py  ← How to check lockouts
src/rules/*.py  ← How rules expose check() method
```

### For Building Database (Phase 1, Task 1)
```
project-specs/SPECS/07-DATA-MODELS/DATABASE_SCHEMA.md  ← Schema definition
src/core/pnl_tracker.py  ← See how it uses DB
```

### For Building Configs (Phase 1, Task 2)
```
project-specs/SPECS/08-CONFIGURATION/RISK_CONFIG_YAML_SPEC.md
project-specs/SPECS/03-RISK-RULES/rules/*.md  ← All 12 rules
```

### For Building Admin CLI (Phase 2, Task 3)
```
project-specs/SPECS/06-CLI-FRONTEND/ADMIN_CLI_SPEC.md  ← CRITICAL!
src/service/installer.py  ← How to control service
```

### For Building Trader CLI (Phase 2, Task 4)
```
project-specs/SPECS/06-CLI-FRONTEND/TRADER_CLI_SPEC.md  ← CRITICAL!
src/core/daemon.py  ← WebSocket setup
```

---

## 🚦 DETERMINING CURRENT STATE

**After reading the required files, you should know:**

1. ✅ **What phase are we in?**
   - Phase 1: Building core daemon
   - Phase 2: Building Windows Service + CLIs
   - Phase 3: Production deployment

2. ✅ **What's the next task?**
   - Check current phase file for first ⏳ NOT STARTED task

3. ✅ **What exists already?**
   - Check `src/` directories
   - Check `data/` for database
   - Check `config/` for configs

4. ✅ **What tests pass?**
   ```bash
   python -m pytest tests/unit/ -v
   # Shows: What library code works
   ```

5. ✅ **Can we run anything?**
   ```bash
   python -m src.core.daemon 2>/dev/null || echo "NOT RUNNABLE YET"
   ```

---

## 💡 COMMON QUESTIONS & ANSWERS

**Q: "Where did we leave off?"**
A: Read `/START_HERE.md` → Current phase file. Look for first ⏳ NOT STARTED task.

**Q: "What's the current status?"**
A: ~25% complete. Library code exists, daemon doesn't. See `/docs/ACTUAL_STATUS_2025-10-23.md`

**Q: "What should I work on next?"**
A: Check current phase file. Start with first incomplete task.

**Q: "How much is left?"**
A: Phase 1: 32-42 hours, Phase 2: 25-34 hours, Phase 3: 11-16 hours
   Total: ~70-90 hours (2-3 weeks)

**Q: "Can it run yet?"**
A: No. Need to build daemon, event router, database first (Phase 1).

**Q: "What works already?"**
A: Core modules (9), Risk rules (12), API layer (9) - all library code with unit tests.

**Q: "What's missing?"**
A: Runnable daemon, event router, database, configs, CLIs, Windows Service.

---

## ⚠️ IMPORTANT NOTES

**DO:**
- ✅ Read START_HERE.md first
- ✅ Check current phase file for tasks
- ✅ Mark tasks ✅ COMPLETE as you finish
- ✅ Update phase file with actual time taken
- ✅ Run tests frequently
- ✅ Read specs before building

**DON'T:**
- ❌ Assume completion % without checking files
- ❌ Skip reading the phase plans
- ❌ Build without reading specs
- ❌ Forget to update task status
- ❌ Delete existing working code

---

## 🎯 MINIMAL ONBOARDING CHECKLIST

For an AI to get up to speed in < 5 minutes:

1. [ ] Read `/START_HERE.md` (30 sec)
2. [ ] Read current phase file (2 min)
3. [ ] Run quick status commands (1 min)
4. [ ] Check what files exist (1 min)
5. [ ] Identify next task (30 sec)

**Total: ~5 minutes to full context**

---

## 📁 FILE MAP

**Status Files (Read These First):**
```
START_HERE.md                          ← Overall status
docs/ACTUAL_STATUS_2025-10-23.md       ← Honest assessment
docs/PHASE_1_BUILD_PLAN.md             ← Current work
docs/PHASE_2_BUILD_PLAN.md             ← Next phase
docs/PHASE_3_BUILD_PLAN.md             ← Final phase
docs/AI_ONBOARDING.md                  ← You are here
```

**Source Code (What Exists):**
```
src/core/                              ← 9 modules (2,250 lines)
src/rules/                             ← 12 rules (2,407 lines)
src/api/                               ← API layer (3,671 lines)
tests/unit/                            ← Unit tests (143/144 passing)
```

**Specifications (How to Build):**
```
project-specs/SPECS/                   ← 100 spec files
  ├── 02-BACKEND-DAEMON/               ← Daemon specs
  ├── 03-RISK-RULES/                   ← Rule specs
  ├── 06-CLI-FRONTEND/                 ← CLI specs
  ├── 07-DATA-MODELS/                  ← Database specs
  └── 08-CONFIGURATION/                ← Config specs
```

---

## 🚀 STARTING WORK

**When ready to start building:**

1. Verify you know the current phase
2. Identify the next incomplete task
3. Read that task's "Files to Read" section
4. Read the relevant specs
5. Create the files listed in "Files to Create"
6. Run tests to verify
7. Mark task ✅ COMPLETE
8. Update phase file with time taken

---

**This document updated:** 2025-10-23
**Purpose:** Help any AI quickly understand project status
**Time to onboard:** ~5 minutes
