# CLI Visual Examples - Risk Manager Setup

This document showcases the professional CLI interface designs for the Risk Manager system.

---

## Design Principles

- **Minimalist**: Clean, uncluttered interface
- **Professional**: Business-appropriate color scheme
- **Keyboard-driven**: Efficient navigation
- **Clear hierarchy**: Numbered menus, consistent spacing
- **Helpful feedback**: Validation messages, progress indicators

---

## Color Palette

```
PRIMARY TEXT:     White
ACCENT:           Cyan (selections, highlights)
SUCCESS:          Green (✓ marks, confirmations)
ERROR:            Red (warnings, errors)
DISABLED:         Gray (inactive options)
BORDERS:          White (dimmed)
```

---

## 1. Splash Screen / Welcome

```
╔════════════════════════════════════════════════════════╗
║                                                        ║
║           ██████╗ ██╗███████╗██╗  ██╗                ║
║           ██╔══██╗██║██╔════╝██║ ██╔╝                ║
║           ██████╔╝██║███████╗█████╔╝                 ║
║           ██╔══██╗██║╚════██║██╔═██╗                 ║
║           ██║  ██║██║███████║██║  ██╗                ║
║           ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝                ║
║                                                        ║
║              MANAGER - Setup Wizard                    ║
║                    v1.0.0                              ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Welcome to the Risk Manager initial setup.           ║
║                                                        ║
║  This wizard will guide you through:                  ║
║    • TopstepX API authentication                      ║
║    • Trading account selection                        ║
║    • Risk rule configuration                          ║
║    • Service installation & testing                   ║
║                                                        ║
║  Estimated time: 5-10 minutes                         ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Press ENTER to begin setup                           ║
║  Press Q to quit                                      ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

---

## 2. Main Admin Menu

```
╔════════════════════════════════════════════════════════╗
║          RISK MANAGER - ADMIN CONTROL PANEL           ║
║                      v1.0.0                            ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  SETUP & CONFIGURATION                                ║
║  ─────────────────────                                ║
║  1. Initial Setup Wizard                              ║
║  2. Configure Authentication                          ║
║  3. Select Monitored Account                          ║
║  4. Configure Risk Rules                              ║
║                                                        ║
║  SERVICE MANAGEMENT                                   ║
║  ─────────────────────                                ║
║  5. Service Control (Start/Stop/Restart)              ║
║  6. Test Connection                                   ║
║  7. View Logs                                         ║
║                                                        ║
║  SYSTEM                                               ║
║  ─────────────────────                                ║
║  8. Change Admin Password                             ║
║  9. Exit                                              ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  Service Status: ● RUNNING  | Uptime: 3h 24m          ║
║  Account: Main Trading (1234) | Rules: 8 enabled      ║
╠════════════════════════════════════════════════════════╣
║  Enter choice [1-9]: _                                ║
╚════════════════════════════════════════════════════════╝
```

---

## 3. Authentication Setup (Step 1)

```
╔════════════════════════════════════════════════════════╗
║        SETUP WIZARD - Step 1 of 4                     ║
║        Authentication Configuration                    ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Enter your TopstepX credentials                      ║
║                                                        ║
║  Username:                                            ║
║  > john_trader_                                       ║
║                                                        ║
║  API Key:                                             ║
║  > ••••••••••••••••••••••••••••••                     ║
║                                                        ║
║  [ Show API Key ]  (Press S)                          ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  ℹ  Get your API key from TopstepX Dashboard          ║
║     Settings → API Access → Generate Key              ║
╠════════════════════════════════════════════════════════╣
║  Press ENTER to validate | B to go back               ║
╚════════════════════════════════════════════════════════╝
```

### Authentication Success

```
╔════════════════════════════════════════════════════════╗
║        SETUP WIZARD - Step 1 of 4                     ║
║        Authentication Configuration                    ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Validating credentials...                            ║
║                                                        ║
║  ✓ Connected to TopstepX API                          ║
║  ✓ Authentication successful                          ║
║  ✓ JWT token obtained                                 ║
║  ✓ Token valid for 24 hours                           ║
║                                                        ║
║  Credentials saved to: config/accounts.yaml           ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  Press ENTER to continue to Step 2                    ║
╚════════════════════════════════════════════════════════╝
```

---

## 4. Account Selection (Step 2)

```
╔════════════════════════════════════════════════════════╗
║        SETUP WIZARD - Step 2 of 4                     ║
║        Account Selection                              ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Fetching your TopstepX accounts... ✓                 ║
║                                                        ║
║  ┌──────┬──────────────────────┬──────────┬─────────┐ ║
║  │  #   │ Account Name         │  Balance │ Status  │ ║
║  ├──────┼──────────────────────┼──────────┼─────────┤ ║
║  │  1   │ Main Trading Account │ $10,250  │ Active  │ ║
║  │  2   │ Practice Account     │  $5,000  │ Active  │ ║
║  │  3   │ Demo Account         │  $2,500  │ Paused  │ ║
║  └──────┴──────────────────────┴──────────┴─────────┘ ║
║                                                        ║
║  Select account to monitor [1-3]: 1_                  ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  Selected: Main Trading Account (ID: 1234)            ║
║                                                        ║
║  This account will be monitored for risk violations.  ║
║  You can change this later in the admin panel.        ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  Confirm selection? [Y/n]: _                          ║
╚════════════════════════════════════════════════════════╝
```

---

## 5. Risk Rules Configuration (Step 3)

### Category Selection

```
╔════════════════════════════════════════════════════════╗
║        SETUP WIZARD - Step 3 of 4                     ║
║        Risk Rules Configuration                       ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Choose configuration mode:                           ║
║                                                        ║
║  1. Quick Setup (Recommended defaults)                ║
║     • Max 5 contracts globally                        ║
║     • $500 daily loss limit                           ║
║     • Basic session controls                          ║
║                                                        ║
║  2. Custom Setup (Configure each rule)                ║
║     • Full control over all 12 rules                  ║
║     • Set specific limits and actions                 ║
║                                                        ║
║  3. Import Configuration (Load from file)             ║
║     • Use existing risk_config.yaml                   ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  Enter choice [1-3]: _                                ║
╚════════════════════════════════════════════════════════╝
```

### Custom Configuration - Position Limits

```
╔════════════════════════════════════════════════════════╗
║        RISK RULES - Position Limits                   ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  ┌─ Max Contracts (Global) ────────────────────────┐  ║
║  │                                                  │  ║
║  │  Status:        [✓] Enabled                      │  ║
║  │  Limit:         5 contracts                      │  ║
║  │  Count Type:    Net position                     │  ║
║  │  Action:        Close all positions              │  ║
║  │                                                  │  ║
║  │  Press E to edit                                 │  ║
║  └──────────────────────────────────────────────────┘  ║
║                                                        ║
║  ┌─ Max Contracts Per Instrument ──────────────────┐  ║
║  │                                                  │  ║
║  │  Status:        [✓] Enabled                      │  ║
║  │  Limits:                                         │  ║
║  │    MNQ: 2 contracts                              │  ║
║  │    ES:  1 contract                               │  ║
║  │    NQ:  1 contract                               │  ║
║  │  Action:        Reduce to limit                  │  ║
║  │                                                  │  ║
║  │  Press E to edit                                 │  ║
║  └──────────────────────────────────────────────────┘  ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  N = Next category | B = Back | H = Help              ║
╚════════════════════════════════════════════════════════╝
```

### Editing a Rule

```
╔════════════════════════════════════════════════════════╗
║        EDIT RULE - Max Contracts (Global)             ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Enable this rule? [Y/n]: Y                           ║
║                                                        ║
║  Maximum contracts allowed:                           ║
║  Current: 5                                           ║
║  New: 3_                                              ║
║                                                        ║
║  Count type:                                          ║
║  1. Net position (Long - Short)                       ║
║  2. Gross position (|Long| + |Short|)                 ║
║  Choice [1-2]: 1                                      ║
║                                                        ║
║  Enforcement action:                                  ║
║  1. Close all positions immediately                   ║
║  2. Reduce to limit (partial close)                   ║
║  Choice [1-2]: 1                                      ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  Preview:                                             ║
║  When net position exceeds 3 contracts,               ║
║  all positions will be closed immediately.            ║
║                                                        ║
║  Save changes? [Y/n]: _                               ║
╚════════════════════════════════════════════════════════╝
```

---

## 6. Loss Limits Configuration

```
╔════════════════════════════════════════════════════════╗
║        RISK RULES - Loss Limits                       ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  ┌─ Daily Realized Loss Limit ──────────────────────┐ ║
║  │                                                   │ ║
║  │  Status:        [✓] Enabled                       │ ║
║  │  Limit:         -$500                             │ ║
║  │  Reset Time:    17:00 (5:00 PM)                   │ ║
║  │  Timezone:      America/New_York                  │ ║
║  │  Action:        Close all + Lockout until reset   │ ║
║  │                                                   │ ║
║  │  Current P&L:   -$245.50  (51% of limit used)    │ ║
║  │  Reset in:      4h 23m                            │ ║
║  │                                                   │ ║
║  │  Press E to edit                                  │ ║
║  └───────────────────────────────────────────────────┘ ║
║                                                        ║
║  ┌─ Daily Unrealized Loss Limit ────────────────────┐ ║
║  │                                                   │ ║
║  │  Status:        [✓] Enabled                       │ ║
║  │  Limit:         -$750                             │ ║
║  │  Action:        Close all positions (no lockout)  │ ║
║  │                                                   │ ║
║  │  Current:       -$120.00  (16% of limit)          │ ║
║  │                                                   │ ║
║  │  Press E to edit                                  │ ║
║  └───────────────────────────────────────────────────┘ ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  N = Next | B = Back | D = Disable rule               ║
╚════════════════════════════════════════════════════════╝
```

---

## 7. Service Installation & Testing (Step 4)

```
╔════════════════════════════════════════════════════════╗
║        SETUP WIZARD - Step 4 of 4                     ║
║        Service Installation                           ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Installing Windows Service...                        ║
║                                                        ║
║  ✓ Created service: RiskManagerService                ║
║  ✓ Set startup type: Automatic                        ║
║  ✓ Configured service account                         ║
║  ✓ Starting service...                                ║
║                                                        ║
║  Service started successfully!                        ║
║                                                        ║
║  Running connection tests...                          ║
║                                                        ║
║  ✓ TopstepX API: Connected (45ms)                     ║
║  ✓ SignalR WebSocket: Connected (32ms)                ║
║  ✓ Database: Initialized                              ║
║  ✓ Account access: Verified                           ║
║  ✓ Event subscription: Active                         ║
║                                                        ║
║  All tests passed! ✓                                  ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  Setup complete! Risk Manager is now running.         ║
║                                                        ║
║  To view live status, run:                            ║
║    python -m src.cli.trader.main                      ║
║                                                        ║
║  Press ENTER to exit                                  ║
╚════════════════════════════════════════════════════════╝
```

---

## 8. Service Control Panel

```
╔════════════════════════════════════════════════════════╗
║              SERVICE CONTROL PANEL                     ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  SERVICE STATUS                                       ║
║  ──────────────                                       ║
║  State:         ● RUNNING                             ║
║  PID:           12345                                 ║
║  Uptime:        3h 24m 15s                            ║
║  Started:       2025-01-20 14:30:00                   ║
║  CPU Usage:     2.3%                                  ║
║  Memory:        45.2 MB                               ║
║                                                        ║
║  CONNECTION STATUS                                    ║
║  ──────────────                                       ║
║  TopstepX API:      ✓ Connected (latency: 45ms)      ║
║  SignalR Stream:    ✓ Connected (latency: 32ms)      ║
║  Database:          ✓ OK (state.db)                   ║
║  Account Access:    ✓ Verified (account 1234)        ║
║                                                        ║
║  MONITORING STATUS                                    ║
║  ──────────────                                       ║
║  Account:           Main Trading (1234)               ║
║  Enabled Rules:     8 of 12                           ║
║  Active Lockouts:   0                                 ║
║  Events Today:      142 processed                     ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  1. Start Service                                     ║
║  2. Stop Service                                      ║
║  3. Restart Service                                   ║
║  4. View Live Logs (tail -f)                          ║
║  5. Test Connection                                   ║
║  6. Back to Main Menu                                 ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  Enter choice [1-6]: _                                ║
╚════════════════════════════════════════════════════════╝
```

---

## 9. Live Logs Viewer

```
╔════════════════════════════════════════════════════════╗
║              LIVE LOGS - Press Q to exit              ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  [14:45:12] INFO  Event received: GatewayUserPosition ║
║  [14:45:12] DEBUG Position updated: MNQ +2 @ 21000.5  ║
║  [14:45:13] INFO  Rule check: MaxContractsPerInstr    ║
║  [14:45:13] INFO  ✓ Within limit (2/2 allowed)        ║
║  [14:45:15] INFO  Event received: GatewayUserTrade    ║
║  [14:45:15] DEBUG Trade: MNQ SELL 1 @ 21001.0         ║
║  [14:45:15] INFO  P&L updated: -$45.50 (realized)     ║
║  [14:45:15] INFO  Rule check: DailyRealizedLoss       ║
║  [14:45:15] INFO  ✓ Within limit (-$45.50 / -$500)    ║
║  [14:45:20] INFO  SignalR heartbeat: OK               ║
║  [14:45:25] INFO  Event received: GatewayUserOrder    ║
║  [14:45:25] DEBUG Order status: FILLED (order #789)   ║
║  [14:45:30] INFO  SignalR heartbeat: OK               ║
║  [14:45:35] INFO  Event received: GatewayUserPosition ║
║  [14:45:35] DEBUG Position updated: MNQ +1 @ 21000.5  ║
║  [14:45:35] INFO  Rule check: MaxContracts            ║
║  [14:45:35] INFO  ✓ Within limit (1/5 allowed)        ║
║  [14:45:40] INFO  SignalR heartbeat: OK               ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  Filter: [ALL] | Level: [INFO] | Auto-scroll: [ON]    ║
╚════════════════════════════════════════════════════════╝
```

---

## 10. Connection Test Screen

```
╔════════════════════════════════════════════════════════╗
║              CONNECTION TEST                           ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  AUTHENTICATION TEST                                  ║
║  ───────────────────                                  ║
║  Testing TopstepX credentials...                      ║
║  ✓ Username valid                                     ║
║  ✓ API key accepted                                   ║
║  ✓ JWT token obtained                                 ║
║  ✓ Token expires: 2025-01-21 14:30:00                 ║
║                                                        ║
║  REST API TEST                                        ║
║  ──────────────                                       ║
║  Testing API endpoint connectivity...                 ║
║  ✓ GET /api/Health: 200 OK (45ms)                     ║
║  ✓ POST /api/Account/search: 200 OK (62ms)            ║
║  ✓ POST /api/Position/searchOpen: 200 OK (53ms)       ║
║  ✓ Average latency: 53ms                              ║
║                                                        ║
║  SIGNALR WEBSOCKET TEST                               ║
║  ───────────────────                                  ║
║  Connecting to SignalR hub...                         ║
║  ✓ WebSocket connection established (32ms)            ║
║  ✓ Subscribed to account events                       ║
║  ✓ Received test event: GatewayUserAccount            ║
║  ✓ Event latency: 28ms                                ║
║                                                        ║
║  ACCOUNT ACCESS TEST                                  ║
║  ────────────────────                                 ║
║  Testing account 1234 permissions...                  ║
║  ✓ Can query positions                                ║
║  ✓ Can query orders                                   ║
║  ✓ Can close positions (permission verified)          ║
║  ✓ Can cancel orders (permission verified)            ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  All tests passed! ✓                                  ║
║  Risk Manager is ready to enforce rules.              ║
║                                                        ║
║  Press ENTER to return                                ║
╚════════════════════════════════════════════════════════╝
```

---

## 11. Error Handling Examples

### Authentication Failed

```
╔════════════════════════════════════════════════════════╗
║        AUTHENTICATION ERROR                            ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  ✗ Authentication failed                              ║
║                                                        ║
║  Error: Invalid API key                               ║
║                                                        ║
║  Possible causes:                                     ║
║  • API key was typed incorrectly                      ║
║  • API key has been revoked                           ║
║  • API key has expired                                ║
║                                                        ║
║  Solutions:                                           ║
║  1. Double-check your API key (copy/paste)            ║
║  2. Generate a new API key from TopstepX              ║
║  3. Contact TopstepX support if issue persists        ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  R = Retry | B = Back to menu | H = Help              ║
╚════════════════════════════════════════════════════════╝
```

### Connection Lost

```
╔════════════════════════════════════════════════════════╗
║        CONNECTION WARNING                              ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  ⚠ SignalR connection lost                            ║
║                                                        ║
║  Attempting to reconnect...                           ║
║                                                        ║
║  Attempt 1/10: Failed (timeout)                       ║
║  Attempt 2/10: Failed (timeout)                       ║
║  Attempt 3/10: Success! ✓                             ║
║                                                        ║
║  Connection restored.                                 ║
║  Risk enforcement is active again.                    ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  Press ENTER to continue                              ║
╚════════════════════════════════════════════════════════╝
```

### Invalid Configuration

```
╔════════════════════════════════════════════════════════╗
║        VALIDATION ERROR                                ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  ✗ Invalid configuration value                        ║
║                                                        ║
║  Field:  Daily Loss Limit                             ║
║  Value:  500                                          ║
║  Error:  Loss limit must be negative (e.g., -500)     ║
║                                                        ║
║  Please enter a negative value representing           ║
║  the maximum loss allowed per day.                    ║
║                                                        ║
║  Example: -500 means "stop trading at $500 loss"      ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  Press ENTER to correct the value                     ║
╚════════════════════════════════════════════════════════╝
```

---

## 12. Confirmation Prompts

### Dangerous Action Confirmation

```
╔════════════════════════════════════════════════════════╗
║        CONFIRM ACTION                                  ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  ⚠ You are about to disable:                          ║
║                                                        ║
║    "Daily Realized Loss Limit"                        ║
║                                                        ║
║  This rule protects you from losing more than         ║
║  $500 per day.                                        ║
║                                                        ║
║  Disabling this rule will remove this protection.     ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Are you sure? Type "DISABLE" to confirm:             ║
║  > _                                                  ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

---

## 13. Progress Indicators

### Loading with Progress Bar

```
╔════════════════════════════════════════════════════════╗
║        LOADING CONFIGURATION                           ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Initializing Risk Manager...                         ║
║                                                        ║
║  ✓ Loading accounts.yaml                              ║
║  ✓ Loading risk_config.yaml                           ║
║  ✓ Loading holidays.yaml                              ║
║  ▶ Connecting to TopstepX API...                      ║
║                                                        ║
║  ████████████████░░░░░░░░  67% complete               ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

---

## Implementation Notes

### Box Drawing Characters Used
```
╔ ╗ ╚ ╝ ║ ═ ╠ ╣ ╦ ╩ ╬    # Double-line boxes (headers)
┌ ┐ └ ┘ │ ─ ├ ┤ ┬ ┴ ┼    # Single-line boxes (content)
```

### Icons Used
```
✓  Success / Enabled
✗  Error / Failed
●  Status indicator (running)
○  Status indicator (stopped)
⚠  Warning
ℹ  Information
▶  In progress / Loading
```

### Keyboard Shortcuts
```
ENTER  - Confirm / Continue
Q      - Quit / Back to previous menu
B      - Back
H      - Help
E      - Edit
D      - Disable
S      - Show (e.g., show masked password)
N      - Next
R      - Retry
```

---

## Backend Function Calls Summary

### For Each Screen:

**Main Menu**: No backend calls (static display)
**Authentication**: `auth.py::authenticate(username, api_key)`
**Account Selection**: `rest_client.py::get_accounts(token)`
**Rule Config**: `config/loader.py::load_risk_config()`, `validator.py::validate_rule_settings()`
**Service Control**: `service/installer.py::get_service_status()`, `::start_service()`, etc.
**Test Connection**: `auth.py::test_connection()`, `signalr_listener.py::test_signalr()`
**Logs Viewer**: `utils/logging.py::tail_log(file, lines)`

---

This visual design provides a professional, minimalist CLI interface that's both functional and pleasant to use.
