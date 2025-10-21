# Claude-Flow Setup Guide for Windows

## Installation Issues Encountered

Unfortunately, we encountered Windows-specific installation issues with claude-flow:

### Problems:
1. **Windows Path Length Limits**: Nested node_modules exceed Windows max path length (260 chars)
2. **Native Module Compilation**: Requires Visual Studio Build Tools for `better-sqlite3`
3. **NPX Cache Issues**: Resource locking in npm cache directory

### Required to Fix (if you want claude-flow):
```bash
# Install Visual Studio Build Tools
# Download from: https://visualstudio.microsoft.com/downloads/
# Select "Desktop development with C++" workload

# Then try again:
npm install -g claude-flow@alpha --force
```

---

## What Claude-Flow Would Provide

If installed, claude-flow offers:

### 1. **Multi-Agent Coordination**
```bash
# Spawn multiple AI agents to work on different tasks
claude-flow hive-mind spawn "Build authentication system" --claude
```

### 2. **Persistent Memory (ReasoningBank)**
```bash
# Store design decisions across sessions
claude-flow memory store "api_design" "REST API with JWT auth" --namespace backend
claude-flow memory query "authentication" --namespace backend
```

### 3. **SPARC Methodology (TDD)**
```bash
# Automated test-driven development workflow
claude-flow sparc tdd "User registration feature"
```

### 4. **MCP Tools Integration**
- 100+ tools for swarm orchestration
- GitHub integration
- Performance tracking
- Neural pattern learning

---

## Alternative Approaches (What You CAN Do Now)

### ✅ Option 1: Use Claude Code's Built-in Features

**Claude Code already has powerful agent coordination via the Task tool:**

```javascript
// You can spawn multiple agents in a single message
Task("Backend Developer", "Build REST API endpoints", "backend-dev")
Task("Database Designer", "Create schema for user data", "code-analyzer")
Task("Tester", "Write comprehensive tests", "tester")
Task("Security Reviewer", "Audit authentication logic", "reviewer")
```

**Memory via your own documentation:**
```bash
# Create structured docs instead of using ReasoningBank
mkdir -p docs/architecture docs/decisions docs/api

# Store decisions in markdown files
# Claude Code can read these across sessions
```

### ✅ Option 2: Manual Project Organization

**Create a structured workflow without claude-flow:**

#### Step 1: Plan Your Work
```bash
# Create a planning document
mkdir -p docs/plans
```

**docs/plans/sprint_current.md:**
```markdown
# Current Sprint Plan

## Feature: Risk Manager Core

### Tasks:
1. [ ] Design risk rule engine
2. [ ] Implement order validation
3. [ ] Add position tracking
4. [ ] Create alert system
5. [ ] Write comprehensive tests

### Agents Needed:
- System Architect (design)
- Backend Developer (implementation)
- Test Engineer (tests)
- DevOps (deployment)
```

#### Step 2: Use TodoWrite for Tracking
```javascript
// Claude Code's TodoWrite tool tracks progress
TodoWrite { todos: [
  {content: "Design risk rule engine", status: "in_progress"},
  {content: "Implement order validation", status: "pending"},
  {content: "Add position tracking", status: "pending"},
  ...
]}
```

#### Step 3: Session Memory via Docs
```bash
# Create decision log
mkdir -p docs/decisions
```

**docs/decisions/001-architecture.md:**
```markdown
# ADR 001: Risk Manager Architecture

## Decision
Use event-driven architecture with Redis pub/sub

## Rationale
- Real-time risk monitoring required
- Need to integrate with multiple trading platforms
- Scalability for future growth

## Consequences
- Need Redis deployment
- Event schema must be versioned
- Testing requires mock event bus
```

### ✅ Option 3: Simple MCP Integration (Without claude-flow)

**You can still use MCP servers without claude-flow:**

```bash
# Add useful MCP servers to Claude Code
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem /path/to/project
claude mcp add git npx @modelcontextprotocol/server-git
```

This gives Claude Code access to:
- File system operations
- Git repository management
- Other MCP tools

---

## Recommended Workflow for Your Risk Manager

### Phase 1: Planning & Design

**1. Create Project Structure**
```bash
mkdir -p {docs/architecture,docs/api,docs/decisions,tests,src}
```

**2. Write Specifications**
```markdown
# docs/architecture/risk-engine.md

## Overview
Real-time risk monitoring system for trading operations

## Components
1. Order Validator - Pre-trade risk checks
2. Position Monitor - Real-time position tracking
3. Alert Manager - Risk threshold notifications
4. Rule Engine - Configurable risk rules

## Data Flow
[Create diagram or description]
```

**3. Use Claude Code Task Tool for Research**
```javascript
// Single message with multiple research agents
Task("Research Agent", "Analyze risk management patterns in trading", "researcher")
Task("Architecture Agent", "Design scalable event-driven system", "system-architect")
```

### Phase 2: Implementation

**1. Break Down Features**
```javascript
TodoWrite { todos: [
  {content: "Setup Python project structure", status: "pending"},
  {content: "Implement Order validator", status: "pending"},
  {content: "Create Position tracker", status: "pending"},
  {content: "Build Alert manager", status: "pending"},
  {content: "Write unit tests (90% coverage)", status: "pending"},
  {content: "Integration tests", status: "pending"},
  {content: "API documentation", status: "pending"}
]}
```

**2. Use Task Tool for Parallel Development**
```javascript
// Spawn agents for different components
Task("Backend Dev", "Implement order validator with risk rules", "backend-dev")
Task("Test Engineer", "Create test suite for validator", "tester")
Task("API Designer", "Document REST endpoints", "api-docs")
```

**3. Document as You Go**
```bash
# Keep docs updated
docs/api/endpoints.md       # API documentation
docs/architecture/*.md      # Architecture decisions
docs/integration/adapters.md  # Integration guides
```

### Phase 3: Testing & Deployment

**1. Comprehensive Testing**
```javascript
Task("Test Agent", "Write unit tests for all modules", "tester")
Task("Integration Tester", "Create end-to-end test scenarios", "tester")
Task("Performance Analyst", "Load testing and benchmarking", "perf-analyzer")
```

**2. Documentation Review**
```javascript
Task("Reviewer", "Review all documentation for completeness", "reviewer")
Task("API Docs Writer", "Finalize API documentation", "api-docs")
```

---

## Session-to-Session Continuity

### Without claude-flow's ReasoningBank, use:

**1. Session Summary Files**
```bash
# Create session logs
mkdir -p docs/sessions
```

**docs/sessions/2025-10-19.md:**
```markdown
# Development Session: 2025-10-19

## What We Did
- Designed risk engine architecture
- Implemented order validator core logic
- Created unit tests for validator

## Decisions Made
- Using Redis for event bus
- JWT for API authentication
- PostgreSQL for state persistence

## Next Session
- Implement position tracker
- Add WebSocket support for real-time alerts
- Deploy to staging environment

## Context for Claude
Key files modified:
- src/core/order_validator.py
- tests/test_validator.py
- docs/api/orders.md
```

**2. Context Files for Claude**
```bash
# Create .claude/README.md with project context
```

**.claude/PROJECT_CONTEXT.md:**
```markdown
# Risk Manager Project Context

## Current Focus
Building real-time trading risk management system

## Key Technologies
- Python 3.11
- Redis (event bus)
- PostgreSQL (state)
- FastAPI (REST API)

## Architecture
Event-driven with pluggable adapters for trading platforms

## Important Files
- src/core/risk_engine.py - Main orchestrator
- src/adapters/ - Trading platform integrations
- src/rules/ - Risk rule implementations

## Development Principles
- Test-driven development (TDD)
- 90%+ code coverage required
- API-first design
```

---

## Pro Tips for Claude Code Without Claude-Flow

### 1. **Batch Operations**
Always spawn multiple agents in single messages:
```javascript
// ✅ Good - parallel execution
[Single Message]:
  Task("Agent 1", "...", "type1")
  Task("Agent 2", "...", "type2")
  Task("Agent 3", "...", "type3")
  TodoWrite { todos: [...all todos...] }
  Write "file1.py"
  Write "file2.py"

// ❌ Bad - sequential
Message 1: Task("Agent 1")
Message 2: Task("Agent 2")
Message 3: TodoWrite
```

### 2. **Maintain Context Files**
```bash
# Update these before each session
docs/sessions/latest.md
docs/architecture/current_state.md
README.md  # Keep updated with latest info
```

### 3. **Use Git Effectively**
```bash
# Commit often with descriptive messages
git commit -m "feat: implement order validator with position limits"

# Claude Code can review git history for context
git log --oneline --graph
```

### 4. **Structured Documentation**
```
docs/
  ├── architecture/      # System design
  ├── api/              # API documentation
  ├── decisions/        # Architecture Decision Records (ADR)
  ├── integration/      # Integration guides
  ├── plans/           # Sprint/feature plans
  └── sessions/        # Session logs
```

---

## If You Still Want Claude-Flow

### Installation Steps (Windows):

**1. Install Visual Studio Build Tools**
- Download: https://visualstudio.microsoft.com/downloads/
- Run installer
- Select "Desktop development with C++" workload
- Install (requires ~7GB)

**2. Install claude-flow**
```bash
npm install -g claude-flow@alpha --force
```

**3. Initialize in Your Project**
```bash
cd "C:\Users\jakers\Desktop\simple risk manager"
claude-flow init --force
```

**4. Add MCP Server**
```bash
claude mcp add claude-flow npx claude-flow@alpha mcp start
```

---

## Summary

**You DON'T NEED claude-flow to be productive!**

Claude Code's built-in features are powerful:
- ✅ Task tool for multi-agent coordination
- ✅ TodoWrite for progress tracking
- ✅ File operations for documentation
- ✅ Git integration for version control
- ✅ MCP support for extensibility

**Key Success Factors:**
1. **Good documentation** (replaces ReasoningBank memory)
2. **Structured todos** (tracks progress)
3. **Session logs** (maintains continuity)
4. **Parallel agent spawning** (Task tool efficiency)

Start building your risk manager now using Claude Code's built-in capabilities!
