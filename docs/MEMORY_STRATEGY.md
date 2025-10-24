# Memory Management Strategy for Risk Manager Project

## Architecture (Based on claude-flow SDK patterns)

### Tier 1: Orchestrator (Claude Code / You)
**Lifespan:** Per-session (reset after 10 agents or 1 hour)
**Memory Access:** Only reads `active-work` and `coordination` namespaces
**Responsibilities:**
- Spawn worker agents with explicit memory keys
- Summarize worker results every hour
- Archive old data
- Respawn fresh to prevent context bloat

### Tier 2: Memory Manager (Background Agent)
**Lifespan:** Continuous (runs every 60 seconds)
**Memory Access:** All namespaces
**Responsibilities:**
- Maintain memory index (`coordination:memory-index`)
- Clean up stale data (TTL expired)
- Archive completed work
- Optimize cache performance

### Tier 3: Worker Agents (Temporary)
**Lifespan:** Single task only
**Memory Access:** Only keys specified by orchestrator
**Responsibilities:**
- Read assignment from specific key
- Execute task
- Write results to `coordination` namespace
- Die immediately after completion

---

## Namespace Organization

```
active-work/          → Current session ONLY (cleaned daily)
  ├── session-summary      Latest compressed state
  ├── current-bugs         Open issues
  └── next-steps           Action items

coordination/         → Agent-to-agent communication (cleaned hourly)
  ├── memory-index         Catalog of all memory
  ├── worker-1-status      Temp worker state
  └── hierarchical-status  Orchestrator state

project-knowledge/    → Long-term reference (never deleted)
  ├── codebase-structure   Architecture docs
  ├── risk-rules-overview  Rule patterns
  └── testing-guide        Test conventions

archive-YYYY-MM-DD/   → Historical data (read-only)
  ├── bugs-fixed           Completed work
  └── decisions            Historical decisions
```

---

## Memory Compression Pattern

### Every Hour (or after 10 agents complete):

```python
# Orchestrator compresses knowledge
summary = {
    "session_date": "2025-10-24",
    "agents_used": 10,
    "tasks_completed": [
        "Fixed StorageMode import error",
        "Enabled SQLite persistence",
        "Updated MCP configuration"
    ],
    "key_learnings": "MCP memory requires curation. Use namespaces for organization.",
    "active_bugs": [],  # Compressed from 10 agent reports
    "next_steps": ["Verify SQLite persistence", "Implement cleanup strategy"],
    "details_archived_in": "archive-2025-10-24"
}

memory_usage(store, "session-summary", summary, "active-work")

# Move full details to archive
for key in completed_worker_keys:
    data = memory_usage(retrieve, key, "coordination")
    memory_usage(store, key, data, "archive-2025-10-24")
    memory_usage(delete, key, "coordination")
```

---

## Worker Agent Template

```python
# When spawning worker, provide explicit memory guidance
Task("Fix bug", f"""
Fix the bug in {file}.

MEMORY GUIDANCE:
- Your assignment: Read "coordination:task-{id}"
- Project structure: Read "project-knowledge:codebase-structure"
- IGNORE: All "archive-*" namespaces

WHEN DONE:
1. Write summary: "coordination:worker-{id}-result"
2. Do NOT read other workers' data
3. Agent will die after this task completes
""", "general-purpose")
```

---

## Memory Index Pattern

```python
# Memory Manager maintains this index
memory_index = {
    "active_session": {
        "current_focus": "Enabling SQLite persistence",
        "key": "active-work:session-summary"
    },
    "project_docs": {
        "architecture": "project-knowledge:codebase-structure",
        "risk_rules": "project-knowledge:risk-rules-overview"
    },
    "recent_work": [
        {"date": "2025-10-24", "summary": "SQLite setup", "archive": "archive-2025-10-24"},
        {"date": "2025-10-23", "summary": "Test fixes", "archive": "archive-2025-10-23"}
    ],
    "last_updated": "2025-10-24T06:45:00Z"
}

memory_usage(store, "memory-index", memory_index, "coordination")
```

---

## Cleanup Strategy

### Hourly (Memory Manager Agent):
- Delete TTL-expired keys from `coordination`
- Archive completed work from `active-work`
- Update memory index

### Daily (End of day):
- Compress `active-work` into final summary
- Move all to `archive-{date}`
- Reset `active-work` to empty

### Weekly (Manual or scheduled):
- Review old archives
- Delete archives older than 30 days
- Compress old archives into quarterly summaries

---

## Reset Pattern for Orchestrator

```python
# Orchestrator lifecycle management

def should_reset_orchestrator():
    """Reset if context getting full or many agents spawned"""
    return (
        agents_spawned >= 10 or
        hours_elapsed >= 1 or
        context_usage >= 150000  # 75% of 200k
    )

if should_reset_orchestrator():
    # 1. Compress current session
    compress_session_knowledge()

    # 2. Store handoff data
    memory_usage(store, "orchestrator-handoff", {
        "previous_session": summary,
        "continue_from": next_steps,
        "context_size": current_context
    }, "coordination")

    # 3. Kill current orchestrator (clear context)
    # 4. New orchestrator spawns:
    handoff = memory_usage(retrieve, "orchestrator-handoff", "coordination")
    # Continues with fresh 200k context ✅
```

---

## Benefits

1. **No context bloat:** Orchestrator resets regularly
2. **Fast retrieval:** Agents use index, not full search
3. **Relevant data only:** Workers get explicit keys
4. **Automatic cleanup:** Memory Manager handles curation
5. **Historical reference:** Archives preserve knowledge without bloating active memory

## Tools

- Memory Manager agent: `swarm-memory-manager` (SDK built-in)
- Hierarchical coordination: `hierarchical-coordinator` (SDK built-in)
- Or implement custom cleanup via cron/scheduled tasks
