# SDK Features for This Project + Business Strategy

## Part 1: What SDK Features You Actually Need

### ✅ ESSENTIAL - Use These for Your Risk Manager

#### 1. Core Development Agents
**File:** `/.claude/agents/core/`

**coder.md** - Implementation specialist
- **Why you need it:** Writes your Python code (daemon, rules, API integration)
- **Use for:** Building all 12 risk rules, enforcement modules, CLI
- **Priority:** CRITICAL

**tester.md** - Test creation
- **Why you need it:** Creates pytest test suites
- **Use for:** Unit tests for rules, integration tests for SignalR flow
- **Priority:** CRITICAL (80% coverage target)

**reviewer.md** - Code quality
- **Why you need it:** Reviews code for bugs, performance issues, security
- **Use for:** Ensuring production-ready quality before deployment
- **Priority:** HIGH

**planner.md** - Task decomposition
- **Why you need it:** Breaks Phase 1/2/3 into manageable tasks
- **Use for:** Organizing 12 rules + modules into build order
- **Priority:** HIGH

---

#### 2. Goal Planning Agents
**File:** `/.claude/agents/goal/code-goal-planner.md`

**code-goal-planner** - SPARC methodology specialist
- **Why you need it:** Systematic TDD development with milestones
- **Use for:** Breaking each rule into Spec → Pseudocode → Arch → Refine → Complete
- **Priority:** HIGH
- **Benefit:** Clear checkpoints, measurable progress, test-first approach

**Example for your project:**
```yaml
Rule 03 (DailyRealizedLoss) SPARC Plan:
  Specification:
    - Define rule contract (inputs, outputs, breach condition)
    - Success criteria: Locks out at -$500, clears at 17:00 ET

  Pseudocode:
    - Algorithm: Track cumulative P&L from GatewayUserTrade events
    - Logic: if daily_pnl <= -500 → trigger enforcement

  Architecture:
    - daily_realized_loss.py (rule implementation)
    - Uses: enforcement/actions.py, state/lockout_manager.py
    - Persists: SQLite daily_pnl table

  Refinement (TDD):
    - Test 1: Normal trading (no breach)
    - Test 2: Breach at -$500 (lockout triggers)
    - Test 3: Lockout clears at reset time
    - Test 4: Multi-day persistence

  Completion:
    - Integration with daemon
    - End-to-end SignalR → Rule → Enforcement test
    - Documentation
```

---

#### 3. Specialized Development Agents
**File:** `/.claude/agents/specialized/`

**backend-dev.md** - API/backend specialist
- **Why you need it:** Expert in REST APIs, WebSockets, authentication
- **Use for:** TopstepX SignalR integration, JWT auth, REST client
- **Priority:** CRITICAL
- **Better than generic coder:** Knows async patterns, connection pooling, error handling

**system-architect.md** - Architecture design
- **Why you need it:** Ensures modular, maintainable design
- **Use for:** Validating your module boundaries, dependency management
- **Priority:** MEDIUM (you already have architecture, but good for validation)

---

#### 4. Basic Coordination (Optional but Helpful)
**File:** `/.claude/agents/swarm/hierarchical-coordinator.md`

**hierarchical-coordinator** - Simple swarm organization
- **Why you might use it:** Coordinates 5-8 agents building Phase 1 in parallel
- **Use for:** Managing workers building different modules simultaneously
- **Priority:** LOW (Claude Code Task tool handles this well enough)
- **When to use:** If building all 12 rules at once (Phase 2+)

---

### ❌ NOT NEEDED - Skip These for Your Project

#### 1. Byzantine Fault Tolerance Agents
**Files:**
- `byzantine-coordinator.md`
- `raft-manager.md`
- `gossip-coordinator.md`
- `crdt-synchronizer.md`
- `quorum-manager.md`

**What they do:** Handle malicious actors in distributed systems (crypto, blockchain)

**Why you don't need them:**
- Your risk manager is a **solo Windows Service** (not distributed)
- No multiple nodes to coordinate
- No consensus needed (single source of truth)
- No Byzantine generals problem

**When you WOULD need them:**
- Building a trading platform with multiple servers
- Decentralized exchange
- Multi-region deployment with conflict resolution
- Cryptocurrency wallet

**Your situation:** Single daemon on one machine → **Skip entirely**

---

#### 2. Consensus Protocols
**Files:**
- `consensus/*` (all consensus agents)
- `security-manager.md` (for distributed security)
- `performance-benchmarker.md` (for distributed performance)

**Why skip:**
- No distributed consensus needed
- Single SQLite database (not distributed)
- No multi-node coordination

---

#### 3. Hive Mind Coordination (Overkill for Phase 1)
**Files:**
- `queen-coordinator.md`
- `collective-intelligence-coordinator.md`
- `swarm-memory-manager.md`

**What they do:** Complex hierarchical swarm coordination with "queen" commanding "workers"

**When useful:**
- Very large projects (50+ files)
- Complex multi-phase builds
- Need centralized oversight

**For your Phase 1 (3 rules, ~20 files):**
- **Overkill** - Basic parallel spawning is enough
- Adds complexity without benefit
- Better for Phase 3 when building all 12 rules

**Use instead:** Simple parallel Task spawning

---

#### 4. Advanced Neural/ML Features
**Files:**
- `neural/*` (neural network agents)
- `ml-developer.md`

**Why skip:**
- Your risk manager is rule-based (not ML-based)
- No need for neural networks
- Simple if/then logic works perfectly

**Future consideration:**
- Could add ML for pattern recognition ("trader is tilting")
- Predictive lockouts based on behavior
- But **NOT needed for MVP or even v1.0**

---

#### 5. Flow-Nexus Cloud Features
**Files:**
- `flow-nexus/*` (cloud deployment, sandboxes, payments)

**Why skip for now:**
- You're building local Windows Service first
- No cloud deployment until Phase 4+
- Payment system comes much later

**When to revisit:**
- Phase 4: SaaS version (cloud deployment)
- Phase 5: Payment integration
- See Part 2 below

---

### 🎯 RECOMMENDED SDK Feature Set for Your Project

**Phase 1 (MVP - 3 Rules):**
```
Essential:
- code-goal-planner (SPARC milestones)
- backend-dev (API integration)
- coder × 3 (build 3 rules in parallel)
- tester × 2 (unit + integration tests)
- reviewer (quality check)

Optional:
- planner (task breakdown)
- system-architect (validate design)
```

**Phase 2 (All 12 Rules):**
```
Essential:
- All Phase 1 agents
- coder × 9 (build remaining 9 rules)
- hierarchical-coordinator (manage 9 parallel builds)

Optional:
- sublinear-goal-planner (optimize dependency graph)
```

**Phase 3 (Production Hardening):**
```
Essential:
- production-validator (ensure deployment-ready)
- security-manager (basic security scan, NOT distributed)
- performance-benchmarker (basic performance, NOT distributed)

Optional:
- cicd-engineer (GitHub Actions setup)
```

---

## Part 2: Future Business Strategy

### The Problem Your Project Solves

**Why Traders Need This:**

1. **Emotion-Driven Mistakes**
   - Trader gets tilted after loss → revenge trades → blows account
   - Your system: Hard lockout prevents emotional trading

2. **TopstepX Account Violations**
   - Daily loss limit: $500 (if exceeded, account reset)
   - Max contracts: Varies by account size
   - Trading hours: Specific windows only
   - **Your system:** Prevents violations BEFORE they happen

3. **Lack of Discipline**
   - "I'll stop at $300 loss" → actually stops at $800
   - Your system: Enforces discipline automatically

4. **Manual Monitoring is Impossible**
   - Trader can't watch P&L while trading
   - Your system: Monitors 24/7, acts in milliseconds

**The Value Proposition:**
```
Without Risk Manager:
- 70% of funded traders fail within 3 months
- Average reason: Daily loss limit violation
- Cost: $150-$500 per account reset

With Risk Manager:
- Automated enforcement (no willpower needed)
- Cannot violate daily loss limit
- Cannot trade outside allowed hours
- Cannot exceed contract limits
- Preservation of $150-$500 account fee
```

---

### Current System Strengths

**What makes it valuable:**

1. **Unfalsifiable Enforcement**
   - Runs as Windows Service (trader can't kill it)
   - Admin password required to stop/modify
   - Closes positions within milliseconds of breach
   - No "I'll just disable it this once"

2. **Real-Time Integration**
   - SignalR WebSocket (sub-second event processing)
   - Reactive enforcement (can't block broker, but closes immediately)
   - State persistence (survives crashes/reboots)

3. **Comprehensive Rules**
   - 12 different risk scenarios covered
   - Trade-by-trade enforcement
   - Hard lockouts (until reset)
   - Timer-based cooldowns

4. **Trader-Friendly**
   - View-only CLI (see status without temptation to disable)
   - Countdown timers for lockouts
   - Enforcement log (understand what happened)

---

### Current System Drawbacks

**Limitations to address:**

1. **Windows-Only**
   - **Problem:** Mac/Linux traders excluded
   - **Impact:** Limits market size
   - **Solution (Phase 4):** Cross-platform daemon or cloud-hosted version

2. **Solo Trader Only**
   - **Problem:** One instance per machine
   - **Impact:** Can't manage multiple accounts elegantly
   - **Solution (Phase 3):** Multi-account support

3. **Manual Installation**
   - **Problem:** Requires technical knowledge to install
   - **Impact:** Non-technical traders can't use it
   - **Solution (Phase 4):** One-click installer, or SaaS version

4. **No Remote Monitoring**
   - **Problem:** Can't check status from phone/away from PC
   - **Impact:** Reduced peace of mind
   - **Solution (Phase 5):** Web dashboard + mobile app

5. **Local-Only Data**
   - **Problem:** No analytics, no performance tracking over time
   - **Impact:** Can't prove ROI to users
   - **Solution (Phase 5):** Cloud sync, analytics dashboard

6. **API Dependency**
   - **Problem:** If TopstepX API changes, software breaks
   - **Impact:** Support burden
   - **Solution (Phase 3):** Robust error handling, API version detection

7. **No Machine Learning**
   - **Problem:** Reactive, not predictive
   - **Impact:** Doesn't prevent tilt BEFORE it happens
   - **Solution (Phase 6):** ML-based pattern recognition

---

### Features to Add for Subscription Appeal

**Phase 3 (Desktop Premium - $29/month):**
```
Core (Already Built):
- 12 risk rules
- Windows Service
- Dual CLI

Add:
- Multi-account support (manage 3-5 TopstepX accounts)
- Trade analytics dashboard (local web UI)
- Performance reports (daily/weekly/monthly)
- Email/SMS alerts (lockout notifications)
- Automatic daily reports
- Backup/restore settings
- Custom rule configurations per account
```

**Phase 4 (Cloud Lite - $49/month):**
```
Migrate to Cloud (SaaS):
- No installation needed
- Works on any device (Windows/Mac/Linux)
- Web dashboard (access from anywhere)
- Mobile app (iOS/Android for monitoring)
- Cloud-hosted daemon (runs 24/7)
- Automatic updates
- Priority support

Technical:
- Use Flow-Nexus for cloud deployment
- flow-nexus__sandbox_create (isolated daemon per user)
- flow-nexus__workflow_create (event-driven enforcement)
- flow-nexus__user_register (authentication)
```

**Phase 5 (Cloud Pro - $99/month):**
```
Premium Features:
- Unlimited accounts
- Advanced analytics
  - Tilt detection patterns
  - Optimal trading hours
  - Best performing instruments
  - Risk-adjusted returns
- White-label for prop firms
  - Customizable branding
  - Bulk account management
  - Admin portal for prop firm managers
- API access (for custom integrations)
- Historical data export
- Slack/Discord webhooks
```

**Phase 6 (Cloud Elite - $199/month):**
```
AI-Powered Features:
- Predictive lockouts
  - ML model detects tilt BEFORE it happens
  - "You've lost $150, and your trade frequency just spiked 3x"
  - "Based on patterns, recommend stopping for the day"
- Smart position sizing
  - "You tend to over-leverage in the afternoon"
  - Suggests contract limits based on time of day
- Personalized coaching
  - Weekly AI-generated performance reviews
  - Recommendations for rule adjustments
- Auto-optimization
  - System learns your patterns
  - Suggests rule changes ("tighten loss limit after 3 consecutive losses")

Technical:
- Use flow-nexus__neural_train (pattern recognition)
- flow-nexus__neural_predict (tilt detection)
- Store training data in cloud
```

---

### Revenue Model Strategy

**Tiered Pricing:**

| Tier | Price | Target Customer | Key Features |
|------|-------|----------------|--------------|
| **Desktop Free** | $0 | New users, trial | 1 account, 3 basic rules, local only |
| **Desktop Premium** | $29/mo | Serious solo traders | 5 accounts, 12 rules, local analytics |
| **Cloud Lite** | $49/mo | Mobile traders | Web access, anywhere, auto-updates |
| **Cloud Pro** | $99/mo | Full-time traders | Unlimited accounts, advanced analytics |
| **Cloud Elite** | $199/mo | Professional traders | AI features, predictive lockouts |
| **Enterprise** | Custom | Prop firms | White-label, bulk management, API |

**Target Customers:**
- Funded TopstepX traders (50,000+ globally)
- Other prop firm traders (Apex, FTMO, etc.) - Phase 7
- Retail traders with broker APIs - Phase 8

**Market Size:**
```
TopstepX Funded Traders: ~50,000
- Conservative conversion: 5% = 2,500 customers
- Average tier: $49/month
- Monthly Revenue: $122,500
- Annual Revenue: $1,470,000

Expansion to other prop firms (3x market):
- Total addressable: 150,000 traders
- 5% conversion: 7,500 customers
- Average tier: $49/month
- Annual Revenue: $4,410,000
```

---

### Deployment Roadmap (SDK Features Needed)

**Phase 4: Cloud Deployment**
```
SDK Features to Use:
- flow-nexus__sandbox_create
  - Purpose: Isolated daemon per user
  - Why: Security, resource isolation
  - Each user gets their own E2B sandbox running Python daemon

- flow-nexus__user_register / user_login
  - Purpose: Authentication
  - Why: Multi-tenant SaaS

- flow-nexus__workflow_create
  - Purpose: Event-driven enforcement
  - Why: Cloud-native architecture

- flow-nexus__storage_upload
  - Purpose: User configuration storage
  - Why: Persist settings in cloud

- flow-nexus__realtime_subscribe
  - Purpose: Live dashboard updates
  - Why: Web UI sees real-time enforcement events

Build Process:
1. Use backend-dev agent to refactor for cloud
2. Use flow-nexus agents to deploy infrastructure
3. Use cicd-engineer for automated deployment
```

**Phase 5: Payment System**
```
SDK Features to Use:
- flow-nexus__user_upgrade
  - Purpose: Tier management
  - Why: Handle subscription upgrades/downgrades

- flow-nexus__check_balance
  - Purpose: Credit system (optional)
  - Why: Pay-per-use model alternative

- Integrate Stripe (external):
  - Subscription billing
  - Payment processing
  - Invoice generation

Build Process:
1. Use backend-dev to build payment webhooks
2. Use flow-nexus__payments tools for integration
3. Use tester for payment flow testing
```

**Phase 6: ML Features**
```
SDK Features to Use:
- flow-nexus__neural_train
  - Purpose: Train tilt detection models
  - Why: Predictive lockouts

- flow-nexus__neural_predict
  - Purpose: Real-time predictions
  - Why: "You're about to tilt" warnings

- flow-nexus__neural_list_templates
  - Purpose: Pre-built models
  - Why: Time-series analysis, anomaly detection

Data Collection:
- Every trade event (GatewayUserTrade)
- Trade frequency, P&L patterns, time of day
- Win/loss streaks, volatility

Models to Train:
1. Tilt Detection: Binary classifier (tilting vs not)
2. Optimal Position Size: Regression (based on time/performance)
3. Trade Frequency Anomaly: Anomaly detection (unusual patterns)

Build Process:
1. Use ml-developer agent for model design
2. Use flow-nexus__neural_train for distributed training
3. Use flow-nexus__sandbox for isolated model testing
```

---

### Why This Project is Worth Building

**For You (Developer):**
- Solves real problem (trader account blowups)
- Recurring revenue model ($49/mo × customers)
- Scalable (cloud SaaS)
- Low competition (niche market)
- High retention (traders depend on it)

**For Traders (Customers):**
- Saves account fees ($150-$500 per violation)
- Removes emotional trading
- Enforces discipline automatically
- Peace of mind (can't screw up)
- ROI: $49/month vs $500 account reset = 10x value

**Success Metrics:**
```
Customer Acquisition Cost: $50 (Google Ads)
Lifetime Value (LTV): $49/mo × 18 months = $882
LTV/CAC Ratio: 17.6x (excellent)

Churn Prevention:
- Free tier: 60% churn (no commitment)
- Paid tier: 20% churn (invested, dependent)
- Annual plan: 10% churn (locked in)

Target: 1,000 paid customers = $49,000/month = $588,000/year
```

---

### Competitive Advantages

**Why traders would pay for YOUR solution:**

1. **TopstepX-Specific Integration**
   - Competitors: Generic risk management (manual setup)
   - You: Plug-and-play for TopstepX

2. **Unfalsifiable Enforcement**
   - Competitors: Browser extensions (easy to disable)
   - You: Windows Service (admin password required)

3. **Millisecond Enforcement**
   - Competitors: Minute-level polling
   - You: SignalR WebSocket (real-time)

4. **Comprehensive Rules**
   - Competitors: 2-3 basic rules
   - You: 12 rules covering all scenarios

5. **Future: AI-Powered Predictive**
   - Competitors: Reactive only
   - You (Phase 6): Predicts tilt before it happens

---

### Marketing Strategy

**Target Channels:**
- TopstepX Discord/Facebook groups
- Trading subreddit (r/Daytrading, r/FuturesTrading)
- YouTube ads (trading channels)
- Trading influencer partnerships
- Prop firm partnerships (white-label)

**Messaging:**
- "Stop Blowing Your TopstepX Account"
- "Automated Discipline for Funded Traders"
- "Your Trading Guardian Angel"
- "$49/month vs $500 Account Reset"

**Free Trial Strategy:**
- 14-day trial (Desktop Premium)
- Require credit card (reduces tire-kickers)
- Email drip campaign during trial
- Show value: "We prevented 3 rule violations this week"

---

## Summary

### SDK Features You Need:
✅ **Use These:**
- code-goal-planner (SPARC milestones)
- backend-dev (API integration)
- coder (rule implementation)
- tester (test coverage)
- reviewer (quality)
- system-architect (validation)

❌ **Skip These:**
- Byzantine/consensus agents (not distributed)
- Hive mind (overkill for Phase 1-2)
- Neural/ML (not needed until Phase 6)
- Flow-Nexus cloud (Phase 4+)

### Business Phases:
- **Phase 1-3:** Local Windows Service (MVP → All Rules → Polish)
- **Phase 4:** Cloud SaaS (Flow-Nexus deployment)
- **Phase 5:** Payment system (Stripe integration)
- **Phase 6:** AI features (Neural network tilt detection)

### Revenue Potential:
- 1,000 customers × $49/month = $588,000/year
- Scalable to $4M+ with prop firm expansion

**Your project has real commercial potential. Build the MVP first, validate with customers, then scale to cloud.**
