# SDK Complete Command Reference

**ALL available SDK commands organized by category**

---

## 📋 Quick Navigation

1. [Core Commands](#-core-commands) - Setup, init, status
2. [Agent Commands](#-agent-commands) - Single agent execution
3. [Multi-Agent Commands](#-multi-agent-commands) - Swarm coordination
4. [SPARC Development](#-sparc-development) - Development methodology
5. [Memory System](#-memory-system) - Knowledge storage
6. [GitHub Integration](#-github-integration) - DevOps automation
7. [Hooks & Lifecycle](#-hooks--lifecycle) - Event management
8. [Advanced Features](#-advanced-features) - Performance, monitoring
9. [MCP Tools](#-mcp-tools) - Model Context Protocol

---

## 🚀 Core Commands

### Setup & Initialization
```bash
# Initialize SDK (first time)
npx claude-flow@alpha init
npx claude-flow@alpha init --force          # Force reinit
npx claude-flow@alpha init --monitoring     # Enable token tracking

# Check version
npx claude-flow@alpha --version

# System status
npx claude-flow@alpha status

# System health check
npx claude-flow@alpha health

# Get help
npx claude-flow@alpha --help
npx claude-flow@alpha <command> --help      # Help for specific command
```

### Start/Stop
```bash
# Start orchestration system
npx claude-flow@alpha start
npx claude-flow@alpha start --swarm         # Start with swarm intelligence
```

---

## 🤖 Agent Commands

### Single Agent Execution (SPARC Run)
```bash
# Run specific agent
npx claude-flow@alpha sparc run <agent-name> "<your prompt>"

# Planning agents
npx claude-flow@alpha sparc run planner "your planning task"
npx claude-flow@alpha sparc run architect "your architecture task"
npx claude-flow@alpha sparc run researcher "your research task"
npx claude-flow@alpha sparc run analyst "your analysis task"
npx claude-flow@alpha sparc run specification "your requirements task"

# Development agents
npx claude-flow@alpha sparc run coder "your coding task"
npx claude-flow@alpha sparc run reviewer "your review task"
npx claude-flow@alpha sparc run tester "your testing task"
npx claude-flow@alpha sparc run debugger "your debugging task"

# Specialized agents
npx claude-flow@alpha sparc run backend-dev "backend development task"
npx claude-flow@alpha sparc run mobile-dev "mobile development task"
npx claude-flow@alpha sparc run ml-developer "ML task"
npx claude-flow@alpha sparc run system-architect "system design task"
npx claude-flow@alpha sparc run devops "DevOps task"
npx claude-flow@alpha sparc run security-review "security audit task"
```

### Agent Management
```bash
# List all available agents
npx claude-flow@alpha agents list
npx claude-flow@alpha agent list

# Spawn agent
npx claude-flow@alpha agent spawn <agent-type> --name "CustomName"

# List active agents
npx claude-flow@alpha agent status

# Terminate agent
npx claude-flow@alpha agent terminate <agent-id>

# Agent metrics
npx claude-flow@alpha agent metrics
npx claude-flow@alpha agent metrics --agent-id <id>
```

### Agent Booster (Ultra-fast editing)
```bash
# Edit single file (352x faster, local WASM)
npx claude-flow@alpha agent booster edit <file>

# Batch edit multiple files
npx claude-flow@alpha agent booster batch <pattern>

# Run benchmark tests
npx claude-flow@alpha agent booster benchmark
```

---

## 🐝 Multi-Agent Commands

### Hive-Mind (Recommended for Complex Tasks)
```bash
# Interactive wizard (EASIEST!)
npx claude-flow@alpha hive-mind wizard

# Initialize Hive Mind system
npx claude-flow@alpha hive-mind init

# Spawn intelligent swarm with objective
npx claude-flow@alpha hive-mind spawn "<your goal>"
npx claude-flow@alpha hive-mind spawn "build API" --claude    # Opens Claude Code CLI

# Check swarm status
npx claude-flow@alpha hive-mind status

# Performance metrics
npx claude-flow@alpha hive-mind metrics

# Optimize memory usage
npx claude-flow@alpha hive-mind optimize-memory

# Pause/resume swarm
npx claude-flow@alpha hive-mind pause <swarm-id>
npx claude-flow@alpha hive-mind resume <swarm-id>

# List running swarms
npx claude-flow@alpha hive-mind ps
```

### Swarm Commands
```bash
# Quick multi-agent task
npx claude-flow@alpha swarm "<objective>"
npx claude-flow@alpha swarm "build REST API"
npx claude-flow@alpha swarm "task" --claude          # Opens Claude Code CLI

# Specify number of agents
npx claude-flow@alpha swarm "task" --agents 8

# Specify agent types
npx claude-flow@alpha swarm "task" --agents planner,coder,tester

# Swarm status
npx claude-flow@alpha swarm status
npx claude-flow@alpha swarm status --watch           # Real-time monitoring

# Swarm monitor
npx claude-flow@alpha swarm monitor
```

---

## 📐 SPARC Development

### SPARC Modes
```bash
# List available modes
npx claude-flow@alpha sparc modes

# Get mode info
npx claude-flow@alpha sparc info <mode>

# Run specific mode
npx claude-flow@alpha sparc run <mode> "<task>"

# Available modes:
# - orchestrator (multi-agent coordination)
# - coder (code generation)
# - architect (system design)
# - tdd (test-driven development)
# - researcher (research & analysis)
# - analyst (code/data analysis)
# - reviewer (code review)
# - tester (test creation)
# - debugger (debugging)
# - optimizer (performance optimization)
# - documenter (documentation)
# - devops (infrastructure)
# - integration (API integration)
```

### SPARC Workflows
```bash
# Test-Driven Development workflow
npx claude-flow@alpha sparc tdd "<feature description>"

# Batch processing (parallel execution)
npx claude-flow@alpha sparc batch <modes> "<task>"
# Example:
npx claude-flow@alpha sparc batch research,architecture,code "microservices platform"

# Full pipeline (all phases)
npx claude-flow@alpha sparc pipeline "<task>"
npx claude-flow@alpha sparc pipeline "e-commerce platform"

# Concurrent multi-task processing
npx claude-flow@alpha sparc concurrent <mode> "<tasks-file>"
```

---

## 💾 Memory System

### Memory Commands (ReasoningBank)
```bash
# Store knowledge
npx claude-flow@alpha memory store "<key>" "<value>"
npx claude-flow@alpha memory store "key" "value" --namespace <category>
npx claude-flow@alpha memory store "key" "value" --namespace arch --reasoningbank

# Query knowledge (semantic search)
npx claude-flow@alpha memory query "<search term>"
npx claude-flow@alpha memory query "term" --namespace <category>
npx claude-flow@alpha memory query "FastAPI" --namespace architecture --reasoningbank

# List all memories
npx claude-flow@alpha memory list
npx claude-flow@alpha memory list --namespace <category>
npx claude-flow@alpha memory list --namespace decisions --reasoningbank

# Memory status
npx claude-flow@alpha memory status
npx claude-flow@alpha memory status --reasoningbank

# Clear memory
npx claude-flow@alpha memory clear
npx claude-flow@alpha memory clear --namespace <category>

# Memory optimization
npx claude-flow@alpha memory optimize --threshold 0.8

# Garbage collection
npx claude-flow@alpha memory gc --threshold 0.9
```

### Agent Memory (ReasoningBank Integration)
```bash
# Initialize ReasoningBank
npx claude-flow@alpha agent memory init

# Memory status
npx claude-flow@alpha agent memory status

# List stored memories
npx claude-flow@alpha agent memory list
```

---

## 🐙 GitHub Integration

### GitHub Commands
```bash
# Initialize GitHub integration
npx claude-flow@alpha github init

# Pull request manager
npx claude-flow@alpha github pr-manager
npx claude-flow@alpha github pr-manager --auto-review
npx claude-flow@alpha github pr-manager "<review PR>"

# Issue tracker
npx claude-flow@alpha github issue-tracker
npx claude-flow@alpha github issue-tracker "<manage issues>"

# Release manager
npx claude-flow@alpha github release-manager
npx claude-flow@alpha github release-manager --version 2.1.0

# Code review swarm (multi-agent review)
npx claude-flow@alpha github code-review-swarm --pr 123

# Repository architect
npx claude-flow@alpha github repo-architect

# Workflow automation
npx claude-flow@alpha github workflow-automation

# Project board sync
npx claude-flow@alpha github project-board-sync
```

---

## 🔄 Hooks & Lifecycle

### Hook Commands
```bash
# Pre-task hook (start of session)
npx claude-flow@alpha hooks pre-task --description "task description"
npx claude-flow@alpha hooks pre-task --description "Planning phase" --git-integration

# Post-task hook (end of task)
npx claude-flow@alpha hooks post-task --task-id "task-id"
npx claude-flow@alpha hooks post-task --analyze-performance true

# Post-edit hook (after file changes)
npx claude-flow@alpha hooks post-edit --file "path/to/file"
npx claude-flow@alpha hooks post-edit --file "file" --memory-key "swarm/component"

# Session management
npx claude-flow@alpha hooks session-end --export-metrics true
npx claude-flow@alpha hooks session-restore --session-id "project-alpha"
npx claude-flow@alpha hooks session-restore --optimize-memory

# Pre-commit hook
npx claude-flow@alpha hooks pre-commit --validate

# Migrate hooks to new format
npx claude-flow@alpha migrate-hooks
```

---

## ⚡ Advanced Features

### Training & Learning
```bash
# Neural pattern learning
npx claude-flow@alpha training <command>
npx claude-flow@alpha training init
npx claude-flow@alpha training status
npx claude-flow@alpha training learn "<pattern>"
```

### Coordination
```bash
# Swarm coordination
npx claude-flow@alpha coordination <command>
npx claude-flow@alpha coordination init
npx claude-flow@alpha coordination status
npx claude-flow@alpha coordination optimize
```

### Analysis & Monitoring
```bash
# Performance analysis
npx claude-flow@alpha analysis <command>
npx claude-flow@alpha analysis performance
npx claude-flow@alpha analysis token-usage
npx claude-flow@alpha analysis metrics

# System monitoring
npx claude-flow@alpha monitoring <command>
npx claude-flow@alpha monitoring start
npx claude-flow@alpha monitoring status
npx claude-flow@alpha monitoring dashboard
```

### Automation
```bash
# Intelligent automation
npx claude-flow@alpha automation <command>
npx claude-flow@alpha automation init
npx claude-flow@alpha automation run "<workflow>"
npx claude-flow@alpha automation status
```

### Optimization
```bash
# Performance optimization
npx claude-flow@alpha optimization <command>
npx claude-flow@alpha optimization analyze
npx claude-flow@alpha optimization apply
npx claude-flow@alpha optimization topology --criteria performance

# Topology optimization
npx claude-flow@alpha optimization topology optimize --swarm-id <id>
```

### Verification & Quality
```bash
# Truth verification
npx claude-flow@alpha verify <subcommand>
npx claude-flow@alpha truth                    # View truth scores

# Pair programming with verification
npx claude-flow@alpha pair
npx claude-flow@alpha pair --start
```

### Proxy (Cost Savings)
```bash
# OpenRouter proxy (85-98% cost savings)
npx claude-flow@alpha proxy start
npx claude-flow@alpha proxy status
npx claude-flow@alpha proxy config
```

### Task Management
```bash
# Task operations
npx claude-flow@alpha task <action>
npx claude-flow@alpha task create "<task>"
npx claude-flow@alpha task list
npx claude-flow@alpha task status <task-id>
npx claude-flow@alpha task complete <task-id>
```

### Configuration
```bash
# System configuration
npx claude-flow@alpha config <action>
npx claude-flow@alpha config get <key>
npx claude-flow@alpha config set <key> <value>
npx claude-flow@alpha config list
```

### Batch Operations
```bash
# Batch processing
npx claude-flow@alpha batch <action>
npx claude-flow@alpha batch process "<tasks>"
npx claude-flow@alpha batch execute "<workflow>"
```

### Stream Chain
```bash
# Stream-JSON chaining for pipelines
npx claude-flow@alpha stream-chain <workflow>
```

### Checkpoints & Sessions
```bash
# Checkpoint management
npx claude-flow@alpha checkpoint create
npx claude-flow@alpha checkpoint restore <id>
npx claude-flow@alpha checkpoint list

# Session management
npx claude-flow@alpha session start
npx claude-flow@alpha session end
npx claude-flow@alpha session list
```

### Enterprise Features
```bash
# Enterprise commands
npx claude-flow@alpha enterprise <command>
# (Various enterprise-specific features)
```

---

## 🔧 MCP Tools

### MCP Server Management
```bash
# Start MCP server
npx claude-flow@alpha mcp start

# Check status
npx claude-flow@alpha mcp status

# Restart server
npx claude-flow@alpha mcp restart

# Stop server
npx claude-flow@alpha mcp stop
```

### MCP Tool Access

**Note**: MCP tools are called FROM WITHIN Claude Code, not as bash commands.

**Example MCP tools** (use within Claude Code):
```javascript
// Swarm initialization
mcp__claude-flow__swarm_init {
  topology: "hierarchical",
  maxAgents: 8
}

// Agent spawning
mcp__claude-flow__agent_spawn {
  type: "coder",
  name: "BackendDev"
}

// Task orchestration
mcp__claude-flow__task_orchestrate {
  task: "implement feature",
  strategy: "parallel"
}

// Memory operations
mcp__claude-flow__memory_usage {
  action: "store",
  key: "decision",
  value: "..."
}
```

**90+ MCP tools available** - see MCP_TOOLS.md in SDK docs for complete list.

---

## 📊 Command Categories Summary

| Category | Command Count | Primary Use |
|----------|---------------|-------------|
| **Core** | 5 | Setup, status, help |
| **Agents** | 15+ | Single agent execution |
| **Hive-Mind** | 8 | Multi-agent coordination |
| **Swarm** | 5 | Quick multi-agent tasks |
| **SPARC** | 10 | Development workflows |
| **Memory** | 12 | Knowledge storage |
| **GitHub** | 8 | DevOps integration |
| **Hooks** | 7 | Lifecycle management |
| **Advanced** | 20+ | Performance, monitoring, etc. |
| **MCP** | 90+ tools | Low-level coordination |

**Total**: 180+ commands/tools available!

---

## 🎯 Most Common Workflows

### 1. Quick Planning Session
```bash
npx claude-flow@alpha init --force
npx claude-flow@alpha hive-mind wizard
# Tell it your goal
```

### 2. Single Agent Task
```bash
npx claude-flow@alpha sparc run planner "create implementation plan"
```

### 3. Research & Analysis
```bash
npx claude-flow@alpha sparc run researcher "research Python frameworks"
npx claude-flow@alpha sparc run analyst "analyze codebase"
```

### 4. Full Development Pipeline
```bash
npx claude-flow@alpha sparc pipeline "build authentication system"
```

### 5. GitHub Workflow
```bash
npx claude-flow@alpha github pr-manager
npx claude-flow@alpha github code-review-swarm --pr 123
```

### 6. Memory Management
```bash
npx claude-flow@alpha memory store "key" "value" --namespace planning
npx claude-flow@alpha memory query "search" --namespace planning
```

---

## 💡 Tips

1. **Start simple**: Use `hive-mind wizard` for complex tasks
2. **Use memory**: Store important decisions for later reference
3. **Check help**: Run `<command> --help` for detailed options
4. **Batch operations**: Use `sparc batch` for parallel execution
5. **GitHub integration**: Automate PR reviews and releases
6. **Monitor performance**: Use `analysis` and `monitoring` commands
7. **Optimize**: Use `optimization` commands for better performance

---

**Need quick reference?** → See simplified `COMMAND_MENU.md`

**This is the COMPLETE list** - use what you need, ignore the rest!
