# Swarm Coordination Flow Diagrams

**Project:** Simple Risk Manager v2.2
**Date:** 2025-10-22
**Purpose:** Visual representation of agent coordination patterns

---

## Table of Contents
1. [Event-Driven Coordination Flow](#event-driven-coordination-flow)
2. [Hierarchical Coordination Example](#hierarchical-coordination-example)
3. [Adaptive Strategy Phase Transitions](#adaptive-strategy-phase-transitions)
4. [Parallel Workstream Coordination](#parallel-workstream-coordination)
5. [Integration Handoff Patterns](#integration-handoff-patterns)

---

## Event-Driven Coordination Flow

### How Agents Coordinate During Implementation

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. TASK ASSIGNMENT                                              │
│                                                                 │
│    Chief Architect                                              │
│         │                                                       │
│         ├─► Backend Lead: "Implement MOD-001 (Enforcement)"     │
│         ├─► Rules Lead: "Wait for MOD-001, then RULE-001"       │
│         └─► Testing Lead: "Prepare test fixtures"              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. PARALLEL EXECUTION                                           │
│                                                                 │
│    Backend Lead                 Rules Lead         Testing Lead │
│         │                            │                   │      │
│         ▼                            ▼                   ▼      │
│    [Modules Specialist]         [WAITING]         [Unit Tester] │
│     Implements MOD-001           (blocked)         Creates mocks │
│         │                            │                   │      │
│         │                            │                   │      │
└─────────┼────────────────────────────┼───────────────────┼──────┘
          │                            │                   │
          │ (Stores interface          │                   │
          │  in memory)                │                   │
          ▼                            │                   │
┌─────────────────────────────────────────────────────────────────┐
│ 3. COORDINATION EVENT                                           │
│                                                                 │
│    Backend Lead → Memory: "MOD-001 complete, interface ready"   │
│    Backend Lead → Rules Lead: "Notify: MOD-001 unblocked"       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. UNBLOCKING & CONTINUATION                                   │
│                                                                 │
│    Rules Lead                                                   │
│         │                                                       │
│         ├─► Reads MOD-001 interface from memory                 │
│         ├─► Assigns task: "Implement RULE-001"                  │
│         └─► [Loss Rules Specialist] starts work                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. INTEGRATION VERIFICATION                                     │
│                                                                 │
│    Testing Lead                                                 │
│         │                                                       │
│         ├─► Reads MOD-001 interface from memory                 │
│         ├─► Reads RULE-001 implementation                       │
│         ├─► [Integration Tester] validates end-to-end           │
│         └─► Reports: ✅ MOD-001 + RULE-001 integrated           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Memory-Based Coordination Protocol

```
┌──────────────────────────────────────────────────────────┐
│ SHARED MEMORY (claude-flow memory store)                │
│                                                          │
│  swarm/                                                  │
│    ├─ interfaces/                                        │
│    │   ├─ MOD-001.json     ← Backend Lead writes         │
│    │   ├─ MOD-002.json     ← Backend Lead writes         │
│    │   └─ WebSocket.json   ← Frontend Lead writes        │
│    │                                                      │
│    ├─ status/                                            │
│    │   ├─ MOD-001: "complete"  ← Backend Lead updates    │
│    │   ├─ RULE-001: "in_progress" ← Rules Lead updates   │
│    │   └─ daemon.py: "blocked" ← Daemon Spec reads       │
│    │                                                      │
│    ├─ decisions/                                         │
│    │   ├─ threading-model.md ← Chief Architect decides   │
│    │   ├─ database-schema.md ← Backend Lead decides      │
│    │   └─ ui-framework.md   ← Frontend Lead decides      │
│    │                                                      │
│    └─ blockers/                                          │
│        ├─ RULE-003: "needs PNL tracker" ← Rules Lead     │
│        ├─ trader-cli: "needs WebSocket" ← Frontend Lead  │
│        └─ integration-test: "needs all rules" ← Tester   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Hierarchical Coordination Example

### Complete Flow: From Task Assignment to Delivery

```
DAY 6: Implementing PNL Tracking Infrastructure

┌───────────────────────────────────────────────────────────────────┐
│ MORNING: Chief Architect Plans                                   │
└───────────────────────────────────────────────────────────────────┘

Chief Architect:
  │
  ├─► Reads specs: MOD-005, MOD-006, MOD-007
  ├─► Defines interfaces for all 3 modules
  ├─► Stores decisions in memory:
  │       swarm/decisions/pnl-architecture.md
  │
  └─► Broadcasts plan to leads:
      "Backend Lead: Coordinate PNL infrastructure (MOD-005, 006, 007)"
      "Rules Lead: Prepare to implement loss rules once PNL ready"

        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ Backend Lead receives task, breaks into parallel subtasks        │
└───────────────────────────────────────────────────────────────────┘

Backend Lead:
  │
  ├─► Reads swarm/decisions/pnl-architecture.md
  ├─► Identifies dependencies:
  │       MOD-007 (Contract Cache) ← no dependencies
  │       MOD-006 (Quote Tracker) ← depends on MOD-007
  │       MOD-005 (PNL Tracker) ← depends on MOD-006 + MOD-007
  │
  └─► Assigns tasks in dependency order:

      ┌────────────────────────────────────────────────┐
      │ PARALLEL: 2 specialists start simultaneously  │
      └────────────────────────────────────────────────┘

      Backend Lead → API Specialist:
         "Implement MOD-007 (Contract Cache)"
         "Priority: HIGH (blocks MOD-006)"

      Backend Lead → Modules Specialist:
         "Wait for MOD-007, then implement MOD-006 (Quote Tracker)"
         "Prepare code structure while waiting"

        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ API Specialist works on MOD-007                                  │
└───────────────────────────────────────────────────────────────────┘

API Specialist (10:00 AM):
  │
  ├─► Hooks: pre-task --description "Implement MOD-007"
  ├─► Implements contract_cache.py (~80 lines)
  │     - Cache contract metadata (tick size, tick value)
  │     - SQLite persistence
  ├─► Hooks: post-edit --file "src/api/contract_cache.py"
  │           --memory-key "swarm/modules/MOD-007/complete"
  │
  └─► Reports to Backend Lead (11:30 AM):
      "✅ MOD-007 complete - interface in memory"

        │
        ▼ (Notification triggers unblocking)
┌───────────────────────────────────────────────────────────────────┐
│ Modules Specialist unblocked, starts MOD-006                     │
└───────────────────────────────────────────────────────────────────┘

Modules Specialist (11:30 AM):
  │
  ├─► Hooks: session-restore (reads MOD-007 interface from memory)
  ├─► Implements quote_tracker.py (~100 lines)
  │     - Connects Market Hub
  │     - Uses MOD-007 for contract lookups
  ├─► Hooks: post-edit --file "src/api/quote_tracker.py"
  │
  └─► Reports to Backend Lead (1:00 PM):
      "✅ MOD-006 complete - ready for MOD-005"

        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ AFTERNOON: State Specialist implements MOD-005                   │
└───────────────────────────────────────────────────────────────────┘

Backend Lead → State Specialist (1:00 PM):
   "Implement MOD-005 (PNL Tracker)"
   "Dependencies ready: MOD-006 + MOD-007"

State Specialist (1:00 PM - 4:00 PM):
  │
  ├─► Implements pnl_tracker.py (~130 lines)
  │     - Realized P&L from trades
  │     - Unrealized P&L from positions + quotes
  │     - Uses MOD-006 for current prices
  │     - Uses MOD-007 for tick calculations
  │
  ├─► Integration testing:
  │     - Simulates trade events
  │     - Simulates quote updates
  │     - Verifies P&L calculations
  │
  └─► Reports to Backend Lead (4:00 PM):
      "✅ MOD-005 complete and tested"

        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ Backend Lead consolidates, reports to Chief Architect            │
└───────────────────────────────────────────────────────────────────┘

Backend Lead (4:00 PM):
  │
  ├─► Verifies all 3 modules integrated:
  │     - Tests MOD-007 standalone
  │     - Tests MOD-006 with MOD-007
  │     - Tests MOD-005 with MOD-006 + MOD-007
  │
  ├─► Updates memory:
  │     swarm/status/pnl-infrastructure: "complete"
  │     swarm/interfaces/MOD-005.json
  │     swarm/interfaces/MOD-006.json
  │     swarm/interfaces/MOD-007.json
  │
  └─► Reports to Chief Architect:
      "✅ PNL infrastructure complete (MOD-005, 006, 007)"
      "Ready for: RULE-003, 004, 005, 007"

        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ Chief Architect notifies Rules Lead                              │
└───────────────────────────────────────────────────────────────────┘

Chief Architect → Rules Lead (4:00 PM):
   "PNL infrastructure ready"
   "Proceed with loss limit rules (RULE-003, 004, 005, 007)"

        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ DAY 7: Rules Lead coordinates 4 parallel rule implementations    │
└───────────────────────────────────────────────────────────────────┘

Rules Lead (Day 7, 9:00 AM):
  │
  ├─► Reads PNL interfaces from memory
  ├─► Assigns 4 specialists in parallel:
  │
  │   Loss Rules Specialist 1: "Implement RULE-003 (Daily Realized Loss)"
  │   Loss Rules Specialist 2: "Implement RULE-004 (Daily Unrealized Loss)"
  │   Loss Rules Specialist 3: "Implement RULE-005 (Max Unrealized Profit)"
  │   Loss Rules Specialist 4: "Implement RULE-007 (Cooldown After Loss)"
  │
  └─► All 4 specialists work in parallel (no dependencies!)

        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ END OF DAY 7: All 4 rules complete                               │
└───────────────────────────────────────────────────────────────────┘

Result:
  ✅ 3 modules implemented in 1 day (MOD-005, 006, 007)
  ✅ 4 rules implemented in 1 day (RULE-003, 004, 005, 007)
  ✅ 7 components total in 2 days
  ✅ 10x parallelization achieved (7 components / 2 days = 3.5x)
```

### Decision Escalation Flow

```
┌───────────────────────────────────────────────────────────────────┐
│ SCENARIO: WebSocket protocol disagreement                        │
└───────────────────────────────────────────────────────────────────┘

WebSocket Developer:
   "Should we use JSON or MessagePack for WebSocket messages?"
        │
        ├─► Asks Frontend Lead (direct manager)
        │
        ▼
Frontend Lead:
   "Hmm, this affects backend too. Need to check with Backend Lead."
        │
        ├─► Asks Backend Lead (peer coordination)
        │
        ▼
Backend Lead:
   "MessagePack would be faster, but JSON is easier to debug."
   "This is a system-wide decision. Escalating to Chief Architect."
        │
        ├─► Escalates to Chief Architect
        │
        ▼
Chief Architect:
   Considers:
     - Debugging needs (Phase 4 testing)
     - Performance requirements (< 10ms latency)
     - CLI complexity (parsing messages)
     - Future extensibility (web interface?)
        │
        ├─► DECISION: Use JSON
        │     Rationale: "Easier debugging outweighs 2-3ms perf gain"
        │
        ├─► Stores decision:
        │     swarm/decisions/websocket-protocol.md
        │
        └─► Broadcasts to both leads:
            "Use JSON for WebSocket messages (logged reasoning in memory)"

        ▼
WebSocket Developer:
   Reads decision from memory
   Implements JSON protocol
   ✅ No further blocking
```

---

## Adaptive Strategy Phase Transitions

### Visualization of Topology Changes

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: MVP (Days 1-5)                                         │
│ Topology: STAR (Centralized)                                   │
│ Team Size: 4 agents                                            │
│                                                                 │
│                     ┌──────────┐                                │
│                     │Architect │ ◄─── All decisions            │
│                     │(Hub)     │                                │
│                     └────┬─────┘                                │
│                          │                                      │
│          ┌───────────────┼───────────────┐                      │
│          │               │               │                      │
│          ▼               ▼               ▼                      │
│     ┌────────┐     ┌─────────┐     ┌────────┐                  │
│     │Backend │     │  Rules  │     │ Tester │                  │
│     │  Dev   │     │   Dev   │     │        │                  │
│     └────────┘     └─────────┘     └────────┘                  │
│                                                                 │
│ Communication Pattern:                                         │
│   - All agents report to Architect                             │
│   - No peer-to-peer communication                              │
│   - Architect reviews all work                                 │
│                                                                 │
│ Parallelization: 3x (3 agents working simultaneously)          │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ TRANSITION (Day 6)
                           │ - Expand team to 10 agents
                           │ - Add workstream leads
                           │ - Switch to hierarchical
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: Full Rules (Days 6-11)                                │
│ Topology: HIERARCHICAL (Tree)                                  │
│ Team Size: 10 agents                                           │
│                                                                 │
│                   ┌──────────────┐                              │
│                   │Chief Architect│ ◄─── System decisions       │
│                   └──────┬────────┘                             │
│                          │                                      │
│          ┌───────────────┼───────────────┐                      │
│          │               │               │                      │
│          ▼               ▼               ▼                      │
│     ┌────────┐     ┌─────────┐     ┌────────┐                  │
│     │Backend │     │  Rules  │     │Testing │                  │
│     │  Lead  │     │  Lead   │     │  Lead  │                  │
│     └────┬───┘     └────┬────┘     └────┬───┘                  │
│          │              │               │                       │
│    ┌─────┼─────┐   ┌────┼────┐      ┌───┼───┐                  │
│    ▼     ▼     ▼   ▼    ▼    ▼      ▼   ▼   ▼                  │
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐   ┌──┐ ┌──┐ ┌──┐               │
│  │AP│ │MD│ │ST│ │LR│ │FR│ │MR│   │UT│ │IT│ │PT│               │
│  │I │ │LS│ │AT│ │UL│ │EQ│ │GMT│   │  │ │  │ │  │               │
│  └──┘ └──┘ └──┘ └──┘ └──┘ └──┘   └──┘ └──┘ └──┘               │
│                                                                 │
│ Communication Pattern:                                         │
│   - Specialists report to Leads                                │
│   - Leads coordinate with Chief Architect                      │
│   - Limited peer-to-peer (via memory)                          │
│                                                                 │
│ Parallelization: 10x (9 specialists working in parallel)       │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ TRANSITION (Day 12)
                           │ - Flatten hierarchy
                           │ - Enable peer collaboration
                           │ - Switch to mesh
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: Real-Time & Admin (Days 12-15)                        │
│ Topology: MESH (Peer-to-Peer)                                  │
│ Team Size: 8 agents                                            │
│                                                                 │
│         ┌──────────┐                                            │
│         │WebSocket │◄─────────────┐                             │
│         │   Dev    │              │                             │
│         └────┬─────┘              │                             │
│              │                    │                             │
│         ┌────┼────────────────────┼─────┐                       │
│         │    │                    │     │                       │
│         ▼    ▼                    ▼     ▼                       │
│     ┌──────┐ ┌──────┐        ┌──────┐ ┌──────┐                 │
│     │Daemon│─│Admin │────────│Trader│─│Service│                │
│     │ Dev  │ │ CLI  │        │ CLI  │ │ Dev   │                │
│     └───┬──┘ └──┬───┘        └──┬───┘ └──┬────┘                │
│         │       │               │       │                       │
│         └───────┼───────────────┼───────┼────────┐              │
│                 │               │       │        │              │
│                 ▼               ▼       ▼        ▼              │
│             ┌──────┐        ┌──────┐ ┌──────┐ ┌──────┐         │
│             │Integ.│────────│Unit  │─│Perf  │─│Polish│         │
│             │Tester│        │Tester│ │Tester│ │Agent │         │
│             └──────┘        └──────┘ └──────┘ └──────┘         │
│                                                                 │
│ Communication Pattern:                                         │
│   - All agents communicate directly                            │
│   - No hierarchy (all peers)                                   │
│   - Consensus decisions for conflicts                          │
│                                                                 │
│ Parallelization: 7x (high communication overhead)              │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ TRANSITION (Day 16)
                           │ - Add testing coordination layer
                           │ - Keep mesh for bug fixes
                           │ - Switch to hybrid
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: Production Hardening (Days 16-22)                     │
│ Topology: HYBRID (Testing Lead + Mesh)                         │
│ Team Size: 8 agents                                            │
│                                                                 │
│                  ┌──────────────┐                               │
│                  │ Testing Lead │ ◄─── Coverage coordination    │
│                  └──────┬───────┘                               │
│                         │                                       │
│            ┌────────────┼────────────┐                          │
│            │            │            │                          │
│            ▼            ▼            ▼                          │
│       ┌────────┐   ┌────────┐   ┌────────┐                     │
│       │  Unit  │   │ Integ. │   │  Perf  │                     │
│       │ Tester │   │ Tester │   │ Tester │                     │
│       └────────┘   └────────┘   └────────┘                     │
│                                                                 │
│       ┌──────────────────────────────────────┐                 │
│       │  MESH: All other agents peer-to-peer │                 │
│       │  (Bug fixes, polish, optimization)   │                 │
│       └──────────────────────────────────────┘                 │
│                                                                 │
│            ┌──────┐  ┌──────┐  ┌──────┐                        │
│            │Daemon│◄─┤Rules │◄─┤CLIs  │                        │
│            │Fix   │  │Fix   │  │Polish│                        │
│            └───┬──┘  └──┬───┘  └──┬───┘                        │
│                │        │         │                             │
│                └────────┼─────────┘                             │
│                         │                                       │
│                         ▼                                       │
│                    [Integration]                                │
│                                                                 │
│ Communication Pattern:                                         │
│   - Testing Lead coordinates test strategy                     │
│   - All other agents mesh for bug fixes                        │
│   - Frequent integration testing                               │
│                                                                 │
│ Parallelization: 6x (testing coordination + peer fixes)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Parallel Workstream Coordination

### Phase 2: Maximum Parallelization Example

```
DAY 6-11: All workstreams running simultaneously

┌──────────────────────────────────────────────────────────────────┐
│ BACKEND WORKSTREAM (Days 6-11)                                  │
│ Lead: Backend Lead                                              │
└──────────────────────────────────────────────────────────────────┘

Timeline:
Day 6:  MOD-007 (Contract Cache) ────────► Complete
Day 6:  MOD-006 (Quote Tracker) ──────────► Complete
Day 6:  MOD-005 (PNL Tracker) ────────────► Complete
Day 7:  [WAITING for rules to catch up]
Day 8:  MOD-003 (Timer Manager) ──────────► Complete
Day 8:  MOD-004 (Reset Scheduler) ────────► Complete
Day 9:  MOD-008 (Trade Counter) ──────────► Complete
Day 10-11: [Support rules implementation]

Agents: 3 specialists (API, Modules, State)

┌──────────────────────────────────────────────────────────────────┐
│ RULES WORKSTREAM (Days 6-11)                                    │
│ Lead: Rules Lead                                                │
└──────────────────────────────────────────────────────────────────┘

Timeline:
Day 6:  [BLOCKED - waiting for PNL infrastructure]
Day 7:  RULE-003 (Realized Loss) ─────────► Complete
Day 7:  RULE-004 (Unrealized Loss) ───────► Complete
Day 7:  RULE-005 (Profit Target) ─────────► Complete
Day 7:  RULE-007 (Cooldown) ──────────────► Complete
Day 8:  [BLOCKED - waiting for Timer Manager]
Day 9:  RULE-006 (Frequency) ─────────────► Complete
Day 9:  RULE-008 (Stop-Loss Grace) ───────► Complete
Day 10: RULE-010 (Auth Loss) ─────────────► Complete
Day 10: RULE-011 (Symbol Blocks) ─────────► Complete
Day 11: RULE-012 (Trade Management) ──────► Complete

Agents: 3 specialists (Loss Rules, Frequency, Management)

┌──────────────────────────────────────────────────────────────────┐
│ TESTING WORKSTREAM (Days 6-11)                                  │
│ Lead: Testing Lead                                              │
└──────────────────────────────────────────────────────────────────┘

Timeline:
Day 6-11: Unit tests for each module/rule as completed
Day 6-11: Integration test fixtures preparation
Day 6-11: Mock TopstepX API setup

Agents: 2 testers (Unit, Integration)

┌──────────────────────────────────────────────────────────────────┐
│ COORDINATION MECHANISM                                          │
└──────────────────────────────────────────────────────────────────┘

Shared Memory Updates (hourly):
  swarm/status/
    MOD-005: "complete" ────► Unblocks RULE-003, 004, 005, 007
    MOD-003: "complete" ────► Unblocks RULE-006, 008
    RULE-001: "complete" ───► Triggers unit test
    ...

Blocker Notifications:
  Rules Lead → Backend Lead: "Need MOD-005 to proceed"
  Backend Lead → Rules Lead: "MOD-005 ready, proceed"

Daily Sync (15 minutes):
  Chief Architect + All Leads
    - Review progress
    - Identify blockers
    - Adjust priorities
    - Coordinate handoffs

Result:
  ✅ 6 modules implemented in 3 days (MOD-003 through MOD-008)
  ✅ 9 rules implemented in 5 days (RULE-003 through RULE-012)
  ✅ 15 components total in 6 days = 2.5 components/day
  ✅ ~10x parallelization (vs. 1 agent doing all sequentially)
```

### Dependency Graph Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│ Module & Rule Dependencies (shows parallel opportunities)      │
└─────────────────────────────────────────────────────────────────┘

NO DEPENDENCIES (Can start immediately):
  ┌──────────┐
  │ MOD-001  │ Enforcement Actions
  └──────────┘
  ┌──────────┐
  │ MOD-002  │ Lockout Manager
  └──────────┘
  ┌──────────┐
  │ MOD-007  │ Contract Cache
  └──────────┘
  ┌──────────┐
  │ MOD-009  │ State Manager
  └──────────┘
  ┌──────────┐
  │ RULE-001 │ Max Contracts (depends on MOD-001, 009)
  └──────────┘
  ┌──────────┐
  │ RULE-002 │ Max Contracts Per Instrument (depends on MOD-001, 009)
  └──────────┘
  ┌──────────┐
  │ RULE-009 │ Session Block (depends on MOD-001, 002)
  └──────────┘
  ┌──────────┐
  │ RULE-011 │ Symbol Blocks (depends on MOD-001, 002)
  └──────────┘

DEPENDS ON MOD-007:
  ┌──────────┐
  │ MOD-006  │ Quote Tracker
  └──────────┘

DEPENDS ON MOD-006 + MOD-007:
  ┌──────────┐
  │ MOD-005  │ PNL Tracker
  └──────────┘

DEPENDS ON MOD-005:
  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ RULE-003 │  │ RULE-004 │  │ RULE-005 │  │ RULE-007 │
  └──────────┘  └──────────┘  └──────────┘  └──────────┘
   Daily Loss   Unrealized    Profit Max   Cooldown

DEPENDS ON MOD-008:
  ┌──────────┐  ┌──────────┐
  │ RULE-006 │  │ RULE-008 │
  └──────────┘  └──────────┘
   Frequency    Stop-Loss

DEPENDS ON ALL MODULES:
  ┌──────────┐  ┌──────────┐
  │ RULE-010 │  │ RULE-012 │
  └──────────┘  └──────────┘
   Auth Loss    Trade Mgmt

CRITICAL PATH (longest dependency chain):
  MOD-007 (Day 6) → MOD-006 (Day 6) → MOD-005 (Day 6) → RULE-003/004/005/007 (Day 7)
  ▲
  4 steps, 2 days
```

---

## Integration Handoff Patterns

### Backend → Frontend Handoff (Phase 2 → Phase 3)

```
┌─────────────────────────────────────────────────────────────────┐
│ DAY 11: Backend workstream completing                          │
└─────────────────────────────────────────────────────────────────┘

Backend Lead:
  │
  ├─► Finalizes daemon.py
  ├─► Implements WebSocket server stub (localhost:8765)
  ├─► Documents WebSocket protocol:
  │     swarm/interfaces/websocket-protocol.md
  │     {
  │       "type": "GatewayUserTrade",
  │       "account_id": 123,
  │       "data": { ... }
  │     }
  │
  └─► Notifies Frontend Lead:
      "WebSocket server ready on port 8765"
      "Protocol spec in memory: swarm/interfaces/websocket-protocol.md"

        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ DAY 12: Frontend workstream starting                           │
└─────────────────────────────────────────────────────────────────┘

Frontend Lead:
  │
  ├─► Reads websocket-protocol.md from memory
  ├─► Assigns tasks:
  │
  │   WebSocket Client Developer:
  │      "Implement websocket_client.py per protocol spec"
  │      "Test connection to localhost:8765"
  │
  │   Trader CLI Developer:
  │      "Integrate WebSocket client into dashboard"
  │      "Update UI on event reception"
  │
  └─► Both developers work in parallel

        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Integration Testing (continuous)                               │
└─────────────────────────────────────────────────────────────────┘

Integration Tester:
  │
  ├─► Runs daemon (backend)
  ├─► Connects Trader CLI (frontend)
  ├─► Simulates trade events
  ├─► Verifies WebSocket broadcast
  ├─► Reports issues to both leads:
  │     "✅ Position updates working"
  │     "❌ Quote events not received - missing subscription?"
  │
  └─► Backend & Frontend collaborate to fix:
      Backend Dev: "Added quote subscription to daemon startup"
      Frontend Dev: "Added quote handler in websocket_client.py"
      Integration Tester: "✅ Fixed - quotes now flowing"
```

### Rules → Testing Handoff Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│ CONTINUOUS: Rules complete incrementally                        │
└─────────────────────────────────────────────────────────────────┘

Day 7, 11:30 AM:
  Rules Lead → Testing Lead:
    "✅ RULE-003 (Daily Realized Loss) complete"
    "Implementation: swarm/rules/RULE-003/complete"

Day 7, 11:35 AM:
  Testing Lead assigns:
    Unit Tester: "Write tests for RULE-003"
    Integration Tester: "Add RULE-003 to end-to-end suite"

Day 7, 3:00 PM:
  Unit Tester → Rules Lead:
    "Found edge case: What if P&L exactly equals limit (-$500)?"

Day 7, 3:05 PM:
  Rules Lead → Loss Rules Specialist:
    "Clarify: Use <= not < for breach detection"

Day 7, 3:10 PM:
  Loss Rules Specialist:
    "✅ Fixed - using <= now"
    Updated: swarm/rules/RULE-003/v1.1

Day 7, 3:15 PM:
  Unit Tester:
    "✅ All tests passing"
    Coverage: 100% for RULE-003

[REPEAT for each rule as it completes]

Day 11, 5:00 PM:
  Testing Lead → Chief Architect:
    "✅ All 12 rules: 100% unit test coverage"
    "✅ Integration suite: 45 scenarios passing"
```

---

## Summary: Key Coordination Patterns

### 1. Memory-Based Handoffs
Agents store interfaces, status, and decisions in shared memory for async coordination.

### 2. Hierarchical Escalation
Issues escalate up the tree until resolved at the appropriate level.

### 3. Dependency-Based Scheduling
Tasks blocked on dependencies wait for completion signals via memory updates.

### 4. Continuous Integration
Testing agents validate each component as it's completed, providing rapid feedback.

### 5. Phase-Based Topology Switching
Coordination structure adapts to project phase (centralized → hierarchical → mesh → hybrid).

---

**Document Version:** 1.0
**Date:** 2025-10-22
**Status:** Complete
