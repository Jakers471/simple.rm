# AI-Driven Interview-to-Implementation Workflow

## Overview
This workflow uses the claude-flow SDK to bridge the gap between user ideas and implemented code through AI-powered requirements gathering, consensus-based architecture, and automated implementation.

---

## **Phase 1: Requirements Discovery (Interview)**

### **Agent:** `specification` (SPARC Specification Agent)
### **Goal:** Interview user and create comprehensive project specification

### **Workflow:**

```yaml
Step 1 - Spawn Specification Agent:
  Agent: specification
  Task: |
    Interview the user to gather complete project requirements.

    Ask about:
    - What problem are you solving?
    - Who are the users?
    - What are the must-have features?
    - What are the nice-to-have features?
    - What are the constraints? (budget, timeline, tech stack)
    - What are the security requirements?
    - What are the performance requirements?
    - What are the compliance requirements?

    Create structured specification document with:
    - Functional requirements (FR-001, FR-002, etc.)
    - Non-functional requirements (NFR-001, NFR-002, etc.)
    - Constraints (technical, business, regulatory)
    - Use cases
    - Acceptance criteria
    - Success metrics

Step 2 - Store Specification in Memory:
  memory_usage:
    action: store
    key: "project-specification"
    namespace: "project-knowledge"
    value: |
      {
        "project_name": "...",
        "description": "...",
        "functional_requirements": [
          {"id": "FR-001", "description": "...", "priority": "high"},
          {"id": "FR-002", "description": "...", "priority": "medium"}
        ],
        "non_functional_requirements": [
          {"id": "NFR-001", "category": "security", "requirement": "..."},
          {"id": "NFR-002", "category": "performance", "requirement": "..."}
        ],
        "constraints": {
          "technical": ["Node.js 18+", "PostgreSQL"],
          "business": ["Launch Q2 2024", "Budget $50k"],
          "regulatory": ["GDPR", "SOC2"]
        },
        "project_principles": {
          "security_level": "high|medium|low",
          "performance_priority": "high|medium|low",
          "code_quality_standards": "strict|moderate|flexible"
        }
      }
```

---

## **Phase 2: Architecture Analysis (Multi-Agent Consensus)**

### **Agent:** `architecture` x10 (10 parallel architecture analysts)
### **Goal:** Each agent analyzes spec and proposes architecture independently

### **Workflow:**

```yaml
Step 1 - Spawn 10 Architecture Agents in Parallel:

  # Agent 1-10 all execute simultaneously
  For each agent (1-10):
    Agent: architecture
    Task: |
      Read the project specification from memory:
      memory_usage(retrieve, "project-specification", "project-knowledge")

      Analyze requirements and propose architecture:
      1. Database design (tables, relationships, indexes)
      2. API structure (REST/GraphQL, endpoints, authentication)
      3. Service architecture (microservices vs monolith)
      4. Technology stack (frameworks, libraries)
      5. Security measures (encryption, auth, validation)
      6. Testing strategy (unit, integration, e2e)
      7. Deployment strategy (Docker, K8s, serverless)

      Store your analysis:
      memory_usage(store, "architecture-proposal-${agent_id}", {
        "agent_id": "${agent_id}",
        "proposed_stack": {...},
        "database_schema": {...},
        "api_design": {...},
        "security_approach": {...},
        "rationale": "Why this approach is optimal",
        "tradeoffs": "What we're optimizing for",
        "estimated_complexity": "low|medium|high"
      }, "coordination")

Step 2 - Consensus Building (Byzantine-style):

  Agent: collective-intelligence-coordinator
  Task: |
    Read all 10 architecture proposals from memory:
    proposals = []
    for i in range(1, 11):
      proposal = memory_usage(retrieve, f"architecture-proposal-{i}", "coordination")
      proposals.append(proposal)

    Analyze proposals for consensus:
    - Compare technology stack choices
    - Identify common patterns (7+ agents agree = consensus)
    - Flag disagreements
    - Weight by rationale quality

    Build consensus architecture (67% threshold):
    consensus = {
      "database": "PostgreSQL" (8/10 agents agree),
      "api_framework": "FastAPI" (9/10 agents agree),
      "authentication": "OAuth2 + JWT" (7/10 agents agree),
      "deployment": "Docker + AWS ECS" (6/10 agents - below threshold!)
    }

    For items below 67% threshold:
    - Flag for user decision
    - Present top 2-3 options with pros/cons

    Store consensus:
    memory_usage(store, "architecture-consensus", consensus, "project-knowledge")
```

---

## **Phase 3: Detailed Design**

### **Agent:** Specialized design agents
### **Goal:** Create detailed technical specifications from consensus architecture

```yaml
Step 1 - Spawn Specialized Design Agents:

  Database Agent:
    Task: |
      Read consensus architecture
      Create detailed database schema:
      - Tables with columns, types, constraints
      - Indexes for performance
      - Migration scripts
      Store: memory_usage(store, "database-design", {...}, "project-knowledge")

  API Agent:
    Task: |
      Read consensus architecture
      Create OpenAPI specification:
      - All endpoints with request/response schemas
      - Authentication flows
      - Error responses
      Store: memory_usage(store, "api-specification", {...}, "project-knowledge")

  Security Agent:
    Task: |
      Read project specification (security_level from principles)
      Design security measures:
      - If security_level == "high": Full encryption, MFA, audit logs
      - If security_level == "medium": Standard auth, basic logging
      - If security_level == "low": Simple auth only
      Store: memory_usage(store, "security-design", {...}, "project-knowledge")

Step 2 - Store Complete Design:

  Coordinator combines all designs:
  memory_usage(store, "complete-technical-design", {
    "database": {...},
    "api": {...},
    "security": {...},
    "frontend": {...}
  }, "project-knowledge")
```

---

## **Phase 4: Test Planning**

### **Agent:** `tester` + Test design swarm
### **Goal:** Determine what needs testing and create test specifications

```yaml
Step 1 - Test Analysis:

  Agent: tester
  Task: |
    Read complete technical design

    Identify testable components:
    - Each API endpoint needs: unit + integration tests
    - Each database operation needs: integration tests
    - Each security feature needs: security tests
    - Each user flow needs: e2e tests

    Create test plan:
    {
      "unit_tests": [
        {"component": "UserService", "scenarios": [...], "priority": "high"},
        {"component": "AuthService", "scenarios": [...], "priority": "critical"}
      ],
      "integration_tests": [...],
      "e2e_tests": [...],
      "performance_tests": [...],
      "security_tests": [...]
    }

    Store: memory_usage(store, "test-plan", test_plan, "project-knowledge")

Step 2 - Generate Test Specifications:

  For each component:
    Agent: tester
    Task: |
      Read test plan for component ${component}
      Write detailed test specifications:

      describe('UserService', () => {
        it('should create user with valid data', () => {
          // Given: valid user data
          // When: createUser called
          // Then: user created in database
        });

        it('should reject duplicate email', () => {
          // Test duplicate handling
        });
      });

      Store: memory_usage(store, "test-spec-${component}", {...}, "coordination")
```

---

## **Phase 5: TDD Implementation**

### **Agent:** `coder` agents implementing tests first
### **Goal:** Write tests then implement features

```yaml
Step 1 - Test Implementation:

  For each component in parallel:
    Agent: coder (TDD mode)
    Task: |
      Read test specification: memory_usage(retrieve, "test-spec-${component}")
      Read technical design: memory_usage(retrieve, "complete-technical-design")

      Write tests FIRST:
      1. Create test file
      2. Write all test cases (they should fail)
      3. Run tests to verify they fail

      Store: "Tests written for ${component}, all failing as expected"

Step 2 - Feature Implementation:

  For each component:
    Agent: coder
    Task: |
      Read tests: tests/${component}.test.ts
      Read technical design

      Implement minimum code to make tests pass:
      1. Write implementation
      2. Run tests
      3. Refactor if needed
      4. Ensure all tests green

      Store: memory_usage(store, "implementation-${component}", {
        "status": "complete",
        "tests_passing": true,
        "coverage": "95%"
      }, "coordination")
```

---

## **Phase 6: Integration & Validation**

### **Agent:** `integration-validator` + `quality-enforcer`
### **Goal:** Ensure all pieces work together

```yaml
Step 1 - Integration Testing:

  Agent: integration-validator
  Task: |
    Read all component implementations

    Run full integration test suite:
    - API tests against real database
    - End-to-end user flows
    - Performance benchmarks
    - Security scans

    Store results: memory_usage(store, "integration-results", {...}, "coordination")

Step 2 - Quality Gates:

  Agent: quality-enforcer
  Task: |
    Check all quality requirements from original spec:

    ✓ All tests passing (from test-plan)
    ✓ Code coverage > 90% (from project principles)
    ✓ Performance meets NFR-001 requirements
    ✓ Security scan passes (based on security_level)
    ✓ Documentation complete

    If all pass → Ready for deployment
    If any fail → Create fix tasks
```

---

## **Single Source of Truth: Project Principles File**

### **File:** `.claude/project-principles.yaml`

```yaml
# Project-Specific Configuration
# All agents MUST read this before starting work

project:
  name: "simple-risk-manager"
  type: "trading_risk_management"
  criticality: "high"  # high|medium|low

principles:
  security:
    level: "critical"  # critical|high|medium|low
    requirements:
      - "All financial data encrypted at rest and in transit"
      - "Multi-factor authentication for admin access"
      - "Audit logging for all risk rule changes"
      - "Zero-trust architecture"
    compliance:
      - "SOC2 Type II"
      - "PCI-DSS for payment data"

  performance:
    priority: "critical"
    requirements:
      - "Risk rule evaluation < 10ms (p99)"
      - "Order blocking < 50ms end-to-end"
      - "Handle 10,000 orders/second"
      - "99.99% uptime requirement"

  code_quality:
    standards: "strict"
    requirements:
      - "100% test coverage for risk rules"
      - "Type safety enforced (mypy strict mode)"
      - "Code review required for all changes"
      - "Automated security scanning"

  testing:
    strategy: "test-driven"
    coverage_target: 95
    requirements:
      - "Unit tests for all risk rules"
      - "Integration tests for API/SignalR"
      - "E2E tests for complete trading flows"
      - "Performance tests for latency requirements"

  architecture:
    style: "microservices"  # monolith|microservices|serverless
    database: "postgresql"
    api_framework: "fastapi"
    deployment: "docker"

  development:
    methodology: "SPARC + TDD"
    version_control: "git"
    ci_cd: "github_actions"
    code_review: "required"

agent_instructions:
  all_agents_must:
    - "Read this file before starting any task"
    - "Follow security level requirements strictly"
    - "Adhere to performance constraints"
    - "Write tests first (TDD)"
    - "Store all decisions in memory for other agents"

  when_security_level_critical:
    - "Implement defense in depth"
    - "Assume breach mentality"
    - "Encrypt everything"
    - "Log all access"

  when_performance_priority_critical:
    - "Optimize hot paths first"
    - "Use caching aggressively"
    - "Profile before optimizing"
    - "Load test everything"
```

---

## **How Agents Use This:**

```yaml
# Every agent starts with:
Agent Task Template:
  1. Read project principles:
     principles = read_file('.claude/project-principles.yaml')

  2. Read project specification:
     spec = memory_usage(retrieve, "project-specification", "project-knowledge")

  3. Read relevant technical design:
     design = memory_usage(retrieve, "complete-technical-design", "project-knowledge")

  4. Execute task following principles:
     if principles.security.level == "critical":
       # Apply critical security measures

     if principles.performance.priority == "critical":
       # Optimize for performance

  5. Store results in memory:
     memory_usage(store, "my-task-result", {...}, namespace)
```

---

## **Example: Full Workflow Execution**

```bash
# Step 1: User initiates requirements gathering
claude-flow sparc run specification "I want to build a trading risk manager"

# Specification agent interviews user, stores in memory:
# - project-specification → project-knowledge namespace
# - project-principles.yaml → created in .claude/

# Step 2: Architecture consensus
claude-flow swarm init mesh --maxAgents=10
# 10 architecture agents read spec, propose solutions
# Consensus coordinator reads all proposals
# Stores: architecture-consensus → project-knowledge

# Step 3: Detailed design
claude-flow agent spawn database-architect
claude-flow agent spawn api-architect
# Each reads consensus, creates detailed design
# Stores: complete-technical-design → project-knowledge

# Step 4: Test planning
claude-flow sparc run tdd "Create test plan from technical design"
# Tester reads design, creates test plan
# Stores: test-plan → project-knowledge

# Step 5: TDD Implementation
claude-flow swarm init hierarchical
# Queen coordinator spawns coder agents
# Each reads test-spec, writes tests, then implementation
# Stores: implementation-status → coordination

# Step 6: Validation
claude-flow agent spawn integration-validator
claude-flow agent spawn quality-enforcer
# Reads all implementations, runs validation
# Stores: validation-results → coordination
```

---

## **Memory Storage Pattern:**

```yaml
Namespaces:
  project-knowledge/        # Long-term project data
    ├── project-specification     # From interview
    ├── architecture-consensus    # From 10 agents
    ├── complete-technical-design # Detailed design
    ├── test-plan                 # What to test
    └── api-specification         # OpenAPI spec

  coordination/             # Agent-to-agent communication
    ├── architecture-proposal-1   # Agent 1's proposal
    ├── architecture-proposal-2   # Agent 2's proposal
    ├── ...
    ├── implementation-UserService
    └── validation-results

  active-work/              # Current session
    └── current-phase             # What we're working on
```

---

## **Benefits:**

1. **Single Source of Truth:** `.claude/project-principles.yaml` + memory
2. **Consistent Behavior:** All agents read same principles
3. **Project-Specific:** Security/performance/quality tuned per project
4. **Consensus-Based:** 10 agents vote, not one agent's opinion
5. **Full Traceability:** Every decision stored in memory
6. **Automated:** User interviews once, AI handles rest
7. **Testable:** TDD from the start
8. **Scalable:** Add more agents for more perspectives

---

## **To Implement This Today:**

```bash
# 1. Create project principles file
cat > .claude/project-principles.yaml << 'EOF'
[Your project-specific principles]
EOF

# 2. Run specification phase
npx claude-flow@alpha sparc run specification "Your project idea"

# 3. Run architecture consensus
npx claude-flow@alpha swarm init mesh --maxAgents=10
# Then spawn 10 architecture agents

# 4. Continue through phases...
```

**Want me to set this up for your risk manager project RIGHT NOW?**
