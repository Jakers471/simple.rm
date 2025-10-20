# How to Use Claude Flow SDK Agents - Practical Guide

## Quick Reference: Agent Categories Available

**Location:** `C:\Users\jakers\Desktop\simple risk manager\.claude\agents\`

---

## Agent Type Categories

### 1. Reasoning Agents (`/.claude/agents/reasoning/`)
- **goal-planner.md** - GOAP specialist (A* search, optimization)
- **sublinear-goal-planner.md** - Mathematical optimization (graph theory)

### 2. Goal Agents (`/.claude/agents/goal/`)
- **code-goal-planner.md** - SPARC methodology (Spec → Pseudocode → Arch → Refine → Complete)

### 3. Hive-Mind Agents (`/.claude/agents/hive-mind/`)
- **queen-coordinator.md** - Hierarchical swarm orchestration
- **collective-intelligence-coordinator.md** - Distributed consensus
- **scout-explorer.md** - Information gathering
- **worker-specialist.md** - Task execution
- **swarm-memory-manager.md** - State synchronization

### 4. Swarm Agents (`/.claude/agents/swarm/`)
- **mesh-coordinator.md** - Peer-to-peer coordination
- **hierarchical-coordinator.md** - Tree-based coordination
- **adaptive-coordinator.md** - Dynamic topology switching

### 5. Core Agents (`/.claude/agents/core/`)
- **coder.md** - Implementation
- **tester.md** - Test creation
- **reviewer.md** - Code review
- **planner.md** - Task decomposition
- **researcher.md** - Information gathering

### 6. Specialized Agents (`/.claude/agents/specialized/`)
- **backend-dev.md** - API/backend development
- **ml-developer.md** - Machine learning
- **system-architect.md** - Architecture design

---

## Spawning Agents: The Two Methods

### Method 1: Claude Code's Task Tool (PRIMARY - Actual Execution)

**This is what actually builds your code.**

```javascript
// Example: Spawn agents to build your risk manager

Task("Code Goal Planner", `
  Read project documentation:
  - /archive/OLD_PROJECT_DOCS/summary/project_overview.md
  - /archive/OLD_PROJECT_DOCS/architecture/system_architecture_v2.md
  - /archive/OLD_PROJECT_DOCS/rules/01_max_contracts.md
  - /archive/OLD_PROJECT_DOCS/rules/03_daily_realized_loss.md
  - /archive/OLD_PROJECT_DOCS/rules/09_session_block_outside.md

  Create SPARC implementation plan for Phase 1:
  - Break into milestones
  - Define success criteria
  - Create task breakdown
  - Map dependencies

  Output: Detailed execution plan for coder agents
`, "code-goal-planner")

// Spawn in parallel (SAME MESSAGE):
Task("Backend Developer", `
  Build core daemon components:
  - daemon.py (main service entry)
  - risk_engine.py (rule orchestrator)
  - event_router.py (route events to rules)

  Follow architecture at /archive/OLD_PROJECT_DOCS/architecture/
  Use Python, keep files under 200 lines each.
`, "backend-dev")

Task("API Integration Specialist", `
  Build TopstepX API integration:
  - signalr_listener.py (WebSocket listener)
  - rest_client.py (REST API wrapper)
  - auth.py (JWT authentication)

  Reference API docs at /archive/OLD_PROJECT_DOCS/api/topstepx_integration.md
  Handle reconnection logic and token refresh.
`, "backend-dev")

Task("Tester", `
  Write comprehensive tests for:
  - MaxContracts rule (RULE-001)
  - DailyRealizedLoss rule (RULE-003)
  - SessionBlockOutside rule (RULE-009)

  Use pytest, mock TopstepX API responses.
  Target 80% coverage.
`, "tester")
```

---

### Method 2: MCP Tools (OPTIONAL - Coordination Setup)

**This sets up coordination infrastructure but doesn't execute code.**

```javascript
// Initialize swarm topology (optional)
mcp__claude-flow__swarm_init({
  topology: "hierarchical",
  maxAgents: 8,
  strategy: "specialized"
})

// Define agent types (optional)
mcp__claude-flow__agent_spawn({
  type: "researcher",
  capabilities: ["api_analysis", "documentation_review"]
})

// Orchestrate high-level task (optional)
mcp__claude-flow__task_orchestrate({
  task: "Build Risk Manager Phase 1",
  strategy: "adaptive",
  priority: "high"
})
```

**Important:** MCP tools are coordination helpers. Use Task tool for actual work.

---

## Recommended Strategies for Your Project

### Strategy 1: Code-Goal-Planner (SPARC Methodology)

**Best for:** Systematic, test-driven development with clear milestones

**How it works:**
1. Code-goal-planner reads your docs
2. Creates SPARC phase plan:
   - **Specification:** Define rule contracts
   - **Pseudocode:** Design algorithms
   - **Architecture:** Structure components
   - **Refinement:** TDD implementation
   - **Completion:** Integration & deployment
3. Spawns coder agents per milestone
4. Tracks progress through phases

**Example Usage:**
```javascript
Task("Code Goal Planner", `
  Create SPARC plan for Risk Manager Phase 1.

  Read documentation:
  - Project overview: /archive/OLD_PROJECT_DOCS/summary/project_overview.md
  - Architecture: /archive/OLD_PROJECT_DOCS/architecture/system_architecture_v2.md
  - Rules: /archive/OLD_PROJECT_DOCS/rules/01_max_contracts.md
  - Rules: /archive/OLD_PROJECT_DOCS/rules/03_daily_realized_loss.md
  - Rules: /archive/OLD_PROJECT_DOCS/rules/09_session_block_outside.md
  - Modules: /archive/OLD_PROJECT_DOCS/modules/*.md

  Objectives:
  - Build working daemon with 3 rules
  - SignalR WebSocket integration
  - SQLite state persistence
  - Basic enforcement actions

  Create:
  1. SPARC milestone breakdown
  2. Success criteria per milestone
  3. Test strategy
  4. Task assignments for coder agents

  Focus on:
  - Python best practices
  - Modular design (files < 200 lines)
  - Test-first development
  - Clear component boundaries
`, "code-goal-planner")
```

**What you get:**
- Structured implementation plan
- Clear checkpoints
- TDD workflow integration
- Measurable progress

**Gaps it might find:**
- CLI command specifications
- Error handling details
- Deployment procedures

**How to address gaps:**
- Agent will ask clarifying questions
- You can provide answers
- Or let agent make reasonable assumptions

---

### Strategy 2: Sublinear-Goal-Planner (Optimization)

**Best for:** Complex dependency optimization, parallel task distribution

**How it works:**
1. Models your project as graph (nodes = tasks, edges = dependencies)
2. Uses A* search to find optimal execution path
3. Identifies critical path (bottlenecks)
4. Recommends parallel vs sequential execution
5. Optimizes for time, cost, resources

**Example Usage:**
```javascript
Task("Sublinear Goal Planner", `
  Optimize execution plan for Risk Manager Phase 1.

  Current State:
  - Empty /src directory
  - Complete specifications in /archive
  - 12 total rules (implementing 3 for MVP)
  - 4 core modules needed
  - TopstepX API integration required

  Goal State:
  - Working daemon process
  - 3 rules enforcing (MaxContracts, DailyLoss, SessionBlock)
  - SignalR listener operational
  - SQLite persistence functional
  - Basic CLI (trader view)
  - 80% test coverage

  Constraints:
  - Python technology stack
  - Files under 200 lines
  - Modular architecture (low coupling)
  - Test-first approach

  Optimize for:
  - Fastest path to working MVP
  - Maximum parallel execution
  - Minimal blocking dependencies

  Analyze:
  - Task dependency graph
  - Critical path (bottlenecks)
  - Parallel execution opportunities
  - Resource allocation (agent assignments)

  Output:
  - Optimal execution sequence
  - Parallel task groupings
  - Estimated timeline
  - Risk mitigation strategies
`, "sublinear-goal-planner")
```

**What you get:**
- Mathematical optimization of task order
- Parallel vs sequential identification
- Critical path analysis
- Resource allocation recommendations

**What it needs:**
- ✅ Current state (empty project)
- ✅ Goal state (working MVP)
- ✅ Available actions (your docs define what can be built)
- ✅ Constraints (your architecture docs)

**Your docs provide all of this!**

---

### Strategy 3: Queen-Coordinator (Swarm Orchestration)

**Best for:** Large-scale parallel development with centralized oversight

**How it works:**
1. Queen establishes command hierarchy
2. Delegates to specialized agents:
   - **Workers:** Implementation tasks
   - **Scouts:** Information gathering, API verification
   - **Collective Intelligence:** Consensus decisions
   - **Memory Manager:** State synchronization
3. Issues royal directives
4. Monitors progress
5. Reports status every 2 minutes

**Example Usage:**
```javascript
// Step 1: Initialize swarm
mcp__claude-flow__swarm_init({
  topology: "hierarchical",
  maxAgents: 10,
  strategy: "specialized"
})

// Step 2: Spawn Queen
Task("Queen Coordinator", `
  Establish hive command for Risk Manager build.

  Mission: Build Phase 1 (3 rules + core daemon)

  Read requirements:
  - /archive/OLD_PROJECT_DOCS/

  Royal Directives:

  1. Deploy Scouts:
     - Verify TopstepX API endpoints exist
     - Research Python SignalR libraries
     - Identify potential integration issues

  2. Assign Workers (parallel execution):
     - Worker 1: Core daemon (daemon.py, risk_engine.py)
     - Worker 2: API integration (signalr_listener.py, rest_client.py)
     - Worker 3: Rule 01 (max_contracts.py)
     - Worker 4: Rule 03 (daily_realized_loss.py)
     - Worker 5: Rule 09 (session_block_outside.py)
     - Worker 6: MOD-001 (enforcement/actions.py)
     - Worker 7: MOD-002 (state/lockout_manager.py)
     - Worker 8: SQLite persistence (state/persistence.py)

  3. Testing Regiment:
     - Tester 1: Unit tests (parallel with workers)
     - Tester 2: Integration tests (after components ready)

  4. Resource Allocation:
     - 50% compute: Workers (implementation)
     - 30% compute: Testers (test coverage)
     - 15% compute: Scouts (research/validation)
     - 5% compute: Memory (coordination)

  5. Governance:
     - Report progress every 5 minutes
     - Flag blockers immediately
     - Coordinate via memory sharing
     - Enforce quality standards

  Success Criteria:
  - All 3 rules functional
  - SignalR connection stable
  - State persists across restarts
  - 80% test coverage
  - No circular dependencies
`, "queen-coordinator")
```

**What you get:**
- Coordinated parallel execution
- Progress monitoring
- Resource management
- Quality oversight

**Trade-offs:**
- More complex setup
- Adds coordination overhead
- Best for large projects (probably overkill for Phase 1)

---

## Hybrid Approach (RECOMMENDED for You)

**Combines best of all strategies:**

```javascript
// PHASE 1: Planning & Optimization (5-10 min)
Task("Sublinear Goal Planner", `
  Read all docs in /archive/OLD_PROJECT_DOCS/
  Create optimized execution plan for Phase 1.
  Identify parallel execution opportunities.
  Map task dependencies.
  Output execution strategy.
`, "sublinear-goal-planner")

// Wait for result, then:

// PHASE 2: Validation (Optional, 5 min)
Task("Scout Explorer", `
  Scan documentation for gaps or ambiguities:
  - Missing CLI command specifications?
  - Unclear error handling?
  - Deployment procedure missing?

  Report findings with priority levels.
`, "scout-explorer")

// PHASE 3: Systematic Build (Main execution)
Task("Code Goal Planner", `
  Execute SPARC methodology using optimized plan from Phase 1.
  Address gaps from scout report.
  Create milestone-based implementation plan.
`, "code-goal-planner")

// Then spawn workers in parallel:
Task("Backend Dev 1", "Build core daemon", "backend-dev")
Task("Backend Dev 2", "Build API integration", "backend-dev")
Task("Coder 1", "Implement Rule 01", "coder")
Task("Coder 2", "Implement Rule 03", "coder")
Task("Coder 3", "Implement Rule 09", "coder")
Task("Tester 1", "Write unit tests", "tester")
Task("Tester 2", "Write integration tests", "tester")
Task("Reviewer", "Code quality review", "reviewer")
```

---

## What Each Agent Type Needs from Your Docs

### Code-Goal-Planner Needs:
- ✅ Feature descriptions (your 12 rules)
- ✅ Success criteria (breach conditions)
- ✅ Architecture (system_architecture_v2.md)
- ✅ Testing requirements (implied in rule specs)

### Sublinear-Goal-Planner Needs:
- ✅ Current state (empty project)
- ✅ Goal state (working MVP)
- ✅ Constraints (architecture, tech stack)
- ✅ Available actions (what can be built)

### Queen-Coordinator Needs:
- ✅ High-level objectives (Phase 1 scope)
- ✅ Component breakdown (your architecture)
- ✅ Resource requirements (your file structure)
- ✅ Success metrics (working daemon with 3 rules)

### Backend-Dev/Coder Agents Need:
- ✅ Implementation specs (your rule docs)
- ✅ API integration details (topstepx_integration.md)
- ✅ Code examples (Python snippets in your docs)
- ✅ File structure (system_architecture_v2.md)

### Tester Agents Need:
- ✅ Test criteria (rule breach conditions)
- ✅ Expected behaviors (enforcement actions)
- ✅ Edge cases (documented in your rules)
- ✅ Coverage goals (you can specify, or default 80%)

**YOU HAVE ALL OF THIS!**

---

## Handling Agent Questions During Execution

**What happens when agents find gaps:**

### Scenario 1: Missing CLI Commands
```
Agent: "I don't see specific CLI command syntax. Should I implement:
  A) risk-manager start/stop/status
  B) rm-daemon start/stop/status
  C) Something else?"

You respond: "Use option A, and add 'configure' command too."

Agent: "Got it, implementing..."
```

### Scenario 2: Error Recovery Logic
```
Agent: "SignalR connection loss handling isn't specified. Should I:
  A) Retry indefinitely with exponential backoff
  B) Retry 5 times then alert and pause
  C) Different approach?"

You respond: "Option B, max 5 retries, 30sec between attempts."

Agent: "Implementing retry logic with those parameters..."
```

### Scenario 3: Reasonable Assumptions
```
Agent: "No Windows Service deployment procedure found.
       I'll research best practices and implement using pywin32.
       Will document steps in README.md during implementation."

(Agent doesn't wait for your response, makes reasonable choice)
```

---

## Practical Example: Building Your Project

### If You Start Right Now:

**Step 1: You say to Claude:**
```
"Use SDK to build Phase 1 from my archive docs.

Approach:
1. Use sublinear-goal-planner to optimize execution
2. Use code-goal-planner for SPARC milestones
3. Spawn backend devs and coders in parallel
4. Concurrent test writing

Read all docs in /archive/OLD_PROJECT_DOCS/

Build:
- Core daemon with 3 rules
- SignalR integration
- SQLite persistence
- Basic enforcement

Target: Working MVP, 80% test coverage"
```

**Step 2: Claude spawns agents (single message):**
```javascript
Task("Sublinear Goal Planner", "Optimize execution plan", ...)
Task("Code Goal Planner", "Create SPARC milestones", ...)
Task("Backend Dev 1", "Build daemon core", ...)
Task("Backend Dev 2", "Build API integration", ...)
Task("Coder 1", "Implement MaxContracts rule", ...)
Task("Coder 2", "Implement DailyLoss rule", ...)
Task("Coder 3", "Implement SessionBlock rule", ...)
Task("Tester 1", "Write unit tests", ...)
Task("Tester 2", "Write integration tests", ...)
Task("Reviewer", "Quality review", ...)
```

**Step 3: Agents execute in parallel:**
- All read your archive docs
- Coordinate via memory
- Build their assigned components
- Ask questions if needed
- Self-review via hooks

**Step 4: You get back:**
- Complete /src directory structure
- All Phase 1 code implemented
- Comprehensive test suite
- Code review report
- Integration guide

**Time:** 1 message from you → working code back

---

## Common Patterns

### Pattern 1: Sequential (Safe but Slow)
```
1. Plan first
2. Wait for plan
3. Build from plan
4. Wait for build
5. Test
```

### Pattern 2: Parallel (Fast, SDK strength)
```
Single message spawns all agents:
├─ Planner (creates strategy)
├─ Builder 1 (starts work immediately)
├─ Builder 2 (starts work immediately)
├─ Builder 3 (starts work immediately)
├─ Tester 1 (writes tests as builders work)
└─ Reviewer (reviews as code completes)

All coordinate via memory
```

### Pattern 3: Hybrid (Balanced)
```
Message 1: Spawn planner
Wait for plan
Message 2: Spawn all builders + testers in parallel
```

---

## Tips for Success

### 1. Be Specific in Task Descriptions
**Bad:**
```javascript
Task("Build the project", "coder")
```

**Good:**
```javascript
Task("Backend Developer", `
  Build SignalR WebSocket listener (signalr_listener.py).

  Requirements:
  - Listen for GatewayUserTrade, GatewayUserPosition events
  - Parse JSON messages per schema in /archive/.../api/
  - Route events to risk_engine
  - Handle reconnection with exponential backoff
  - Keep under 150 lines

  Reference: /archive/OLD_PROJECT_DOCS/api/topstepx_integration.md
`, "backend-dev")
```

### 2. Leverage Your Docs
```javascript
// Always point agents to your docs
Task("...", `
  Read specification: /archive/OLD_PROJECT_DOCS/rules/03_daily_realized_loss.md
  ...
`, "...")
```

### 3. Specify Coordination
```javascript
Task("Coder 1", `
  Build max_contracts.py

  Dependencies:
  - Read base_rule.py interface
  - Use enforcement/actions.py (built by other agent)
  - Check memory for enforcement module status before integrating
`, "coder")
```

### 4. Define Success Criteria
```javascript
Task("...", `
  ...

  Success Criteria:
  - All tests pass
  - No circular imports
  - Follows architecture in /archive/.../architecture/
  - Files under 200 lines
`, "...")
```

---

## Summary

**To use SDK agents:**

1. **Have specifications ready** (you do: /archive docs)
2. **Choose agent strategy:**
   - Code-goal-planner (SPARC/TDD)
   - Sublinear-goal-planner (optimization)
   - Queen-coordinator (swarm)
   - Hybrid (recommended)
3. **Spawn via Task tool** (not just MCP)
4. **Provide clear instructions:**
   - What to build
   - Where to find specs
   - Success criteria
5. **Let agents coordinate** (via memory/hooks)
6. **Address questions** as they arise

**Your docs are SDK-ready. You can start building now.**
