# SDK Command Menu - Quick Reference

**Purpose**: Quick lookup for SDK commands. Copy-paste and customize.

---

## 🎯 Basic Pattern

```bash
npx claude-flow@alpha [command-type] [subcommand] "[your natural language prompt]"
```

**You use natural language** - just tell the agent what you want in plain English!

---

## 📋 Command Categories

### 1. Single Agent Commands

Run one specific agent for a task:

```bash
npx claude-flow@alpha sparc run [agent-name] "[your instructions in plain English]"
```

#### Planning Agents
```bash
# Strategic planning
npx claude-flow@alpha sparc run planner "your goal here"

# Architecture design
npx claude-flow@alpha sparc run architect "your design request here"

# Research
npx claude-flow@alpha sparc run researcher "what to research"

# Analysis
npx claude-flow@alpha sparc run analyst "what to analyze"

# Requirements
npx claude-flow@alpha sparc run specification "define requirements for X"
```

**Examples**:
```bash
# Have planner create a roadmap
npx claude-flow@alpha sparc run planner "Create a 3-phase implementation plan for a trading risk manager. Read archived docs in archive/OLD_PROJECT_DOCS for context."

# Have researcher investigate tech options
npx claude-flow@alpha sparc run researcher "Research Python async frameworks for real-time event processing. Compare FastAPI, Sanic, and Tornado."

# Have architect design system
npx claude-flow@alpha sparc run architect "Design a microservices architecture for risk management with event-driven communication."
```

---

### 2. Multi-Agent Commands

Coordinate multiple agents for complex tasks:

```bash
# Interactive wizard (easiest for complex tasks)
npx claude-flow@alpha hive-mind wizard

# Direct spawn with specific agents
npx claude-flow@alpha hive-mind spawn "[your goal]" --agents planner,architect,researcher

# Auto-select agents (SDK picks best agents)
npx claude-flow@alpha swarm "[your goal]"
```

**Examples**:
```bash
# Interactive planning session
npx claude-flow@alpha hive-mind wizard
# Then follow prompts and tell it your goal

# Specific agent team
npx claude-flow@alpha hive-mind spawn "Build complete system design for trading risk manager" --agents planner,architect,researcher,analyst

# Quick multi-agent task
npx claude-flow@alpha swarm "Analyze requirements and create implementation plan for risk monitoring system"
```

---

### 3. Memory Commands

Store and retrieve decisions/knowledge:

```bash
# Store knowledge
npx claude-flow@alpha memory store "[key]" "[value]" --namespace [category] --reasoningbank

# Query knowledge
npx claude-flow@alpha memory query "[search term]" --namespace [category] --reasoningbank

# List all stored knowledge
npx claude-flow@alpha memory list --namespace [category] --reasoningbank

# Check memory status
npx claude-flow@alpha memory status --reasoningbank
```

**Examples**:
```bash
# Store architecture decision
npx claude-flow@alpha memory store "arch_decision_001" "Use FastAPI with async/await for REST API" --namespace architecture --reasoningbank

# Store tech stack choice
npx claude-flow@alpha memory store "tech_stack" "Python 3.11, FastAPI, Redis, SQLite" --namespace decisions --reasoningbank

# Query past decisions
npx claude-flow@alpha memory query "FastAPI" --namespace architecture --reasoningbank

# List all architecture decisions
npx claude-flow@alpha memory list --namespace architecture --reasoningbank
```

---

### 4. Setup Commands

One-time setup:

```bash
# Initialize SDK in your project (run once)
npx claude-flow@alpha init --force

# Check SDK version
npx claude-flow@alpha --version

# Check health
npx claude-flow@alpha health

# List available modes
npx claude-flow@alpha sparc modes

# List available agents
npx claude-flow@alpha agents list
```

---

### 5. Session Management

Track work across sessions:

```bash
# Start session
npx claude-flow@alpha hooks pre-task --description "Planning phase for risk manager"

# End session (with metrics)
npx claude-flow@alpha hooks session-end --export-metrics true

# Restore previous session
npx claude-flow@alpha hooks session-restore --session-id "[id]"
```

---

## 🎨 Prompting Guide

### The Key: Use Natural Language!

**You don't need special syntax** - just tell the agent what you want like you're talking to a person.

#### ✅ Good Prompts

```bash
# Specific and clear
npx claude-flow@alpha sparc run planner "Create a 3-month implementation roadmap for a Python-based trading risk manager with 12 rules. Break it into sprints."

# Provides context
npx claude-flow@alpha sparc run architect "Design REST API architecture. The system needs to handle real-time events from trading platforms and enforce risk rules. Use async patterns."

# References available docs
npx claude-flow@alpha sparc run analyst "Read the archived project docs in archive/OLD_PROJECT_DOCS/. Analyze what's already specified and identify gaps."

# Clear output request
npx claude-flow@alpha sparc run researcher "Research WebSocket libraries for Python. Create a comparison table with pros/cons and recommendation."
```

#### ❌ Avoid Vague Prompts

```bash
# Too vague
npx claude-flow@alpha sparc run planner "make a plan"

# No context
npx claude-flow@alpha sparc run architect "design something"

# Unclear goal
npx claude-flow@alpha sparc run researcher "look stuff up"
```

### Prompt Template

Use this structure for best results:

```bash
npx claude-flow@alpha sparc run [agent] "
[WHAT you want done]
[WHY or CONTEXT]
[Any CONSTRAINTS or REQUIREMENTS]
[Where to find INFO if relevant]
[What FORMAT you want output in]
"
```

**Example**:
```bash
npx claude-flow@alpha sparc run planner "
Create an implementation plan for a trading risk manager MVP.
This will enforce trading rules and prevent violations in real-time.
Must support multiple broker connections.
Check archive/OLD_PROJECT_DOCS/ for existing rule specifications.
Output as phased plan with tasks and timelines.
"
```

---

## 🔥 Most Common Workflows

### Workflow 1: Start New Project Planning

```bash
# Step 1: Initialize
npx claude-flow@alpha init --force

# Step 2: High-level planning with multiple agents
npx claude-flow@alpha hive-mind wizard
# Tell it: "Plan a trading risk management system. Check archive/OLD_PROJECT_DOCS for existing specs."

# Step 3: Store key decisions
npx claude-flow@alpha memory store "project_scope" "Your scope here" --namespace planning --reasoningbank
```

### Workflow 2: Research & Decision Making

```bash
# Research options
npx claude-flow@alpha sparc run researcher "Research Python frameworks for REST APIs. Compare FastAPI, Flask, Django."

# Get architecture recommendation
npx claude-flow@alpha sparc run architect "Based on research, recommend framework for async real-time risk manager."

# Store decision
npx claude-flow@alpha memory store "framework_choice" "FastAPI chosen for async support" --namespace decisions --reasoningbank
```

### Workflow 3: Analyze Existing Work

```bash
# Have analyst review archived docs
npx claude-flow@alpha sparc run analyst "Review all docs in archive/OLD_PROJECT_DOCS/. Create gap analysis and improvement recommendations."

# Have planner create migration plan
npx claude-flow@alpha sparc run planner "Based on analyst report, create plan to complete the project."
```

### Workflow 4: Detailed Design

```bash
# Architecture design
npx claude-flow@alpha sparc run architect "Design microservices architecture for risk manager. Include API gateway, event bus, rule engine."

# API specification
npx claude-flow@alpha sparc run architect "Design REST API endpoints for risk rule management. Include OpenAPI spec."

# Store architecture
npx claude-flow@alpha memory store "api_design" "See output above" --namespace architecture --reasoningbank
```

---

## 📝 Quick Copy-Paste Commands

### Planning
```bash
npx claude-flow@alpha sparc run planner "Create implementation plan for [PROJECT]. Check archive/OLD_PROJECT_DOCS/ for context."
```

### Research
```bash
npx claude-flow@alpha sparc run researcher "Research [TOPIC]. Compare options and recommend best choice."
```

### Architecture
```bash
npx claude-flow@alpha sparc run architect "Design [COMPONENT] architecture. Requirements: [LIST]."
```

### Analysis
```bash
npx claude-flow@alpha sparc run analyst "Analyze [WHAT]. Identify gaps and improvements."
```

### Multi-Agent
```bash
npx claude-flow@alpha hive-mind wizard
```

---

## 🆘 Troubleshooting Commands

```bash
# Check status
npx claude-flow@alpha health

# Check memory
npx claude-flow@alpha memory status --reasoningbank

# Clear cache (if having issues)
npm cache clean --force

# Reinstall SDK
npx claude-flow@alpha init --force --reset
```

---

## 💡 Pro Tips

1. **Be specific in prompts** - More detail = Better results
2. **Reference archived docs** - Tell agents to check `archive/OLD_PROJECT_DOCS/`
3. **Use memory for decisions** - Store important choices for later sessions
4. **Start with hive-mind wizard** - Easiest for complex planning
5. **Natural language works** - No special syntax needed!

---

**Need more detail?** → Check `HOW_TO_USE_SDK/` folder

**Just want to start?** → Run:
```bash
npx claude-flow@alpha init --force
npx claude-flow@alpha hive-mind wizard
```
