# How SDK Commands Actually Work

## What Happens Step-by-Step

### 1. You Run A Command
```bash
npx claude-flow@alpha sparc run planner "your long prompt here"
```

### 2. SDK Does Its Thing
- Loads the `planner` agent (from `.claude/agents/planner.md`)
- Reads your prompt
- Executes the agent (calls Claude API)
- Agent thinks through the problem
- Agent generates output

### 3. Output Is Returned
The agent's response is printed to your terminal (stdout) and/or:
- Saved to files (if specified)
- Stored in memory system (`.swarm/memory.db`)
- Can be piped to other commands

### 4. You Use The Output
- Read the plan the agent created
- Copy it to a file
- Use it as input for the next agent
- Store important decisions in memory

## Example Flow

```bash
# Step 1: Planning
npx claude-flow@alpha sparc run planner "Create implementation plan. Check archive/OLD_PROJECT_DOCS/"

# Agent returns:
# 📋 IMPLEMENTATION PLAN
#
# Phase 1: MVP
# - Task 1: Setup Python project structure
# - Task 2: Implement RULE-001 (max contracts)
# ...
# [You see this output in terminal]

# Step 2: Save output to file (manually or redirect)
npx claude-flow@alpha sparc run planner "..." > docs/implementation_plan.md

# Step 3: Store key decisions in memory
npx claude-flow@alpha memory store "phase1_tasks" "Setup, RULE-001, RULE-002" --namespace planning

# Step 4: Use planner output for next agent
npx claude-flow@alpha sparc run architect "Design architecture for tasks in docs/implementation_plan.md"
```

## Interactive Mode (Easier!)

Instead of chaining commands, use the wizard:

```bash
npx claude-flow@alpha hive-mind wizard
```

**What happens:**
1. Wizard asks: "What's your goal?"
2. You type/paste your long explanation
3. Wizard asks follow-up questions
4. Wizard coordinates multiple agents automatically
5. Wizard shows you results as they complete
6. Results saved to files

## Key Differences from Claude Code

| Claude Code (me) | SDK claude-flow |
|------------------|-----------------|
| Interactive chat | One-shot commands |
| Back and forth conversation | Single prompt → single output |
| I read files for you | You tell agent which files to read |
| Ongoing context | Each command is independent |
| You talk to me | You run bash commands |

## When To Use Which

**Use Claude Code (me) for:**
- Exploring codebase
- Interactive debugging
- Asking questions
- Iterative changes

**Use SDK agents for:**
- Large planning tasks
- Multi-agent coordination
- Batch processing
- Autonomous execution

## They Work Together!

**Typical workflow:**
1. Use SDK to create plans: `npx claude-flow@alpha hive-mind wizard`
2. SDK agents create docs in `docs/` folder
3. Ask me (Claude Code) to read those docs and implement
4. I do the actual coding based on agent plans
5. Use SDK again for review: `npx claude-flow@alpha sparc run reviewer "Review my code"`

## Where Output Goes

**Terminal (stdout):**
- Default output location
- You see agent's response immediately
- Can redirect: `command > file.md`

**Memory System:**
- `.swarm/memory.db` - SQLite database
- Store with: `memory store "key" "value"`
- Query with: `memory query "search term"`

**Files:**
- Agents can write to files if you ask
- Example: "Create plan and save to docs/plan.md"
- Or redirect: `sparc run planner "..." > docs/plan.md`

**Agent State:**
- `.claude-flow/` folder contains agent state
- Session checkpoints
- Configuration

## Quick Reference

```bash
# Ask agent to create file directly
npx claude-flow@alpha sparc run planner "Create plan, save output to docs/phase1_plan.md"

# Or redirect output yourself
npx claude-flow@alpha sparc run planner "Create plan" > docs/phase1_plan.md

# Interactive (easiest for beginners)
npx claude-flow@alpha hive-mind wizard

# Store result in memory for later
npx claude-flow@alpha memory store "plan_v1" "$(npx claude-flow@alpha sparc run planner '...')"

# Multi-agent coordination
npx claude-flow@alpha swarm "Plan, design, and create initial code structure"
```

## Example: Full Planning Session

```bash
# Start interactive wizard
npx claude-flow@alpha hive-mind wizard

# When prompted "What's your goal?", paste this:
"""
Create a comprehensive implementation plan for trading risk manager.

Background:
- Fresh start on previously planned project
- All specs in archive/OLD_PROJECT_DOCS/
- 12 risk rules (RULE-001 to 012)
- 4 modules (MOD-001 to 004)
- Architecture already designed (ARCH-V2)

Goal:
Phase 1 MVP with 3 core rules, then expand to full system.

What I need:
1. Review archived specs
2. Create 3-phase implementation plan
3. Break down into weekly tasks
4. Identify dependencies
5. Risk assessment
6. Testing strategy

Save all outputs to docs/ folder.
"""

# Wizard will:
# - Spawn planner agent
# - Spawn researcher agent (to review archive)
# - Spawn architect agent (for dependencies)
# - Coordinate between them
# - Show you results
# - Save to docs/
```

## TL;DR

**SDK is NOT a chatbot. It's a command runner.**

1. Run command with prompt → Agent executes → Output returned
2. Use `hive-mind wizard` for interactive mode (easiest)
3. Long prompts: Use multi-line strings or files
4. Output goes to terminal (redirect to files if needed)
5. SDK and Claude Code work together (SDK plans, I implement)
