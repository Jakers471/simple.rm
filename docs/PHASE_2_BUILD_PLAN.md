# Phase 2: Make It Production (Service + CLIs)

**Status:** NOT STARTED
**Goal:** Windows Service with admin control and trader dashboard
**Estimated Time:** 3-5 days (25-34 hours)
**Started:** TBD
**Target Completion:** TBD

**Prerequisites:** Phase 1 must be COMPLETE (daemon works in console mode)

---

## 🎯 OBJECTIVE

Transform console daemon into production Windows Service with:
- Auto-start on boot
- Admin-only service control
- Admin CLI for configuration
- Trader CLI for real-time monitoring
- Professional user experience

**Deliverable:** Production-ready Windows Service + 2 CLIs

---

## 📋 TASKS BREAKDOWN

### Task 1: Windows Service Wrapper (~6-8 hours)

**Status:** ⏳ NOT STARTED

**Goal:** Daemon runs as Windows Service

**Steps:**

1. **Create service wrapper** (2-3 hours)
   - Read: `project-specs/SPECS/02-BACKEND-DAEMON/DAEMON_ARCHITECTURE.md` (Windows Service section)
   - Create: `src/service/windows_service.py`
   - Use: `win32serviceutil`, `win32service`, `win32event`
   - Class: `RiskManagerService(win32serviceutil.ServiceFramework)`
   - Methods:
     - `SvcDoRun()` - Start daemon
     - `SvcStop()` - Stop daemon gracefully
     - Logging to Windows Event Log

2. **Implement service lifecycle** (1-2 hours)
   - Service start: Initialize and run daemon
   - Service stop: Graceful shutdown
   - Service pause/resume (optional)
   - Service status reporting

3. **Add auto-recovery** (1 hour)
   - Configure service recovery options
   - Auto-restart on failure
   - Delay between retries
   - Alert admin on repeated failures

4. **Windows Event Log integration** (1 hour)
   - Log to Windows Event Log (not just files)
   - Log: Service start/stop
   - Log: Critical errors
   - Log: Enforcement actions

5. **Test service** (1-2 hours)
   - Create: `tests/integration/test_windows_service.py`
   - Test: Install/start/stop/uninstall
   - Test: Auto-start on boot
   - Test: Recovery after crash
   - Test: Event log entries

**Files to Create:**
- `src/service/windows_service.py` (150-200 lines)
- `tests/integration/test_windows_service.py`

**Files to Read:**
- `project-specs/SPECS/02-BACKEND-DAEMON/DAEMON_ARCHITECTURE.md`
- `src/core/daemon.py` (from Phase 1)

**Dependencies:**
- Phase 1 complete (daemon works)
- Windows environment (WSL won't work)
- Admin privileges

**Success Criteria:**
- ✅ Service installs successfully
- ✅ Service starts daemon
- ✅ Service stops gracefully
- ✅ Auto-starts on boot
- ✅ Recovers from crashes
- ✅ Logs to Event Log

---

### Task 2: Service Installer (~3-4 hours)

**Status:** ⏳ NOT STARTED

**Goal:** Easy install/uninstall commands

**Steps:**

1. **Create installer script** (1-2 hours)
   - Create: `src/service/installer.py`
   - Commands:
     - `install` - Install service
     - `uninstall` - Remove service
     - `start` - Start service
     - `stop` - Stop service
     - `restart` - Restart service
     - `status` - Check service status
   - Require admin privileges

2. **Add validation** (30 min)
   - Check: Config files exist
   - Check: Database initialized
   - Check: API credentials present
   - Fail early with clear errors

3. **Create setup script** (30 min)
   - Create: `install.bat` (Windows batch file)
   - Check admin privileges
   - Run database initialization
   - Install service
   - Start service
   - Print success message

4. **Test installer** (1-2 hours)
   - Test: Fresh installation
   - Test: Uninstall completely removes service
   - Test: Upgrade (uninstall + reinstall)
   - Test: Error handling (missing files, etc.)

**Files to Create:**
- `src/service/installer.py` (100-150 lines)
- `install.bat` (Windows)
- `uninstall.bat` (Windows)
- `tests/integration/test_installer.py`

**Files to Read:**
- `src/service/windows_service.py` (from Task 1)
- `scripts/init_database.py` (from Phase 1)

**Success Criteria:**
- ✅ Install works on fresh system
- ✅ Uninstall removes everything
- ✅ Validation catches errors
- ✅ Clear error messages
- ✅ Documentation for users

---

### Task 3: Admin CLI (~8-10 hours)

**Status:** ⏳ NOT STARTED

**Goal:** Admin interface for service control and configuration

**Steps:**

1. **Create CLI framework** (2 hours)
   - Read: `project-specs/SPECS/06-CLI-FRONTEND/ADMIN_CLI_SPEC.md`
   - Create: `src/cli/admin/admin_main.py`
   - Beautiful ANSI UI (colors, boxes, centered)
   - Number-based menu selection
   - Password authentication

2. **Implement authentication** (1 hour)
   - Prompt for admin password
   - Verify against `config/admin_password.hash`
   - 3 attempts before exit
   - Option to reset password

3. **Implement main menu** (1 hour)
   - Service Control
   - Account Management
   - Rule Configuration
   - Connection Testing
   - View Logs
   - Exit

4. **Service control submenu** (1-2 hours)
   - Status (running/stopped)
   - Start
   - Stop
   - Restart
   - View recent logs

5. **Account management submenu** (2-3 hours)
   - List accounts
   - Add account
   - Edit account (API keys)
   - Enable/disable account
   - Test API connection
   - Authenticate with TopstepX

6. **Rule configuration submenu** (1-2 hours)
   - List all 12 rules
   - Show enabled/disabled status
   - Edit rule parameters
   - Validate changes
   - Reload config (restart service)

7. **Connection testing** (1 hour)
   - Test database connection
   - Test TopstepX REST API
   - Test TopstepX SignalR
   - Show detailed error messages

8. **Test admin CLI** (1 hour)
   - Test: Authentication works
   - Test: All menu options work
   - Test: Config changes persist
   - Test: Service control works

**Files to Create:**
- `src/cli/admin/admin_main.py` (200-300 lines)
- `src/cli/admin/ui_components.py` (100-150 lines)
- `src/cli/admin/service_control.py` (100-150 lines)
- `tests/integration/test_admin_cli.py`

**Files to Read:**
- `project-specs/SPECS/06-CLI-FRONTEND/ADMIN_CLI_SPEC.md` (critical!)
- `config/risk_config.yaml` (to know what to edit)
- `src/service/installer.py` (to know how to control service)

**Success Criteria:**
- ✅ Beautiful UI with colors/boxes
- ✅ Password authentication works
- ✅ Service control works
- ✅ Config editing works
- ✅ Changes persist
- ✅ Clear error messages

---

### Task 4: Trader CLI (~4-6 hours)

**Status:** ⏳ NOT STARTED

**Goal:** Real-time dashboard for traders

**Steps:**

1. **Create CLI framework** (1 hour)
   - Read: `project-specs/SPECS/06-CLI-FRONTEND/TRADER_CLI_SPEC.md`
   - Create: `src/cli/trader/trader_main.py`
   - Beautiful ANSI UI
   - Tab-based interface
   - No authentication (read-only)

2. **Implement WebSocket client** (1-2 hours)
   - Create: `src/cli/trader/realtime_client.py`
   - Connect to daemon's WebSocket (port 8765)
   - Receive real-time events
   - Update UI on event

3. **Implement dashboard views** (2-3 hours)
   - Overview tab:
     - Account status
     - Current P&L
     - Lockout status
     - Connection health
   - P&L tab:
     - Daily realized P&L
     - Daily unrealized P&L
     - Recent trades
   - Positions tab:
     - Current positions
     - Average price
     - Unrealized P&L
   - Rules tab:
     - All 12 rules
     - Enabled/disabled
     - Current status vs limits
   - Logs tab:
     - Recent enforcement actions
     - Lockout history

4. **Add real-time updates** (1 hour)
   - Update dashboard when events arrive
   - Flash changed values
   - Audio alert on lockout (optional)

5. **Test trader CLI** (30 min)
   - Test: Dashboard displays correctly
   - Test: Real-time updates work
   - Test: Tab switching works
   - Test: Reconnect on disconnect

**Files to Create:**
- `src/cli/trader/trader_main.py` (150-200 lines)
- `src/cli/trader/realtime_client.py` (100-150 lines)
- `src/cli/trader/ui_components.py` (100-150 lines)
- `tests/integration/test_trader_cli.py`

**Files to Read:**
- `project-specs/SPECS/06-CLI-FRONTEND/TRADER_CLI_SPEC.md` (critical!)
- `src/core/daemon.py` (to see WebSocket setup)
- `data/state.db` (to read current state)

**Success Criteria:**
- ✅ Beautiful real-time dashboard
- ✅ WebSocket updates work
- ✅ All tabs display correctly
- ✅ No authentication needed
- ✅ Reconnects automatically

---

### Task 5: Testing & Documentation (~4-6 hours)

**Status:** ⏳ NOT STARTED

**Goal:** Comprehensive testing and user documentation

**Steps:**

1. **End-to-end testing** (2-3 hours)
   - Test: Fresh install on clean Windows VM
   - Test: Service auto-starts on boot
   - Test: Admin CLI controls service
   - Test: Trader CLI shows real-time data
   - Test: Multi-account monitoring
   - Test: All 12 rules enforced
   - Test: Crash recovery

2. **Write user documentation** (2-3 hours)
   - Create: `docs/INSTALLATION_GUIDE.md`
     - System requirements
     - Installation steps
     - Initial configuration
     - Troubleshooting
   - Create: `docs/ADMIN_GUIDE.md`
     - How to use Admin CLI
     - Service management
     - Account setup
     - Rule configuration
   - Create: `docs/TRADER_GUIDE.md`
     - How to use Trader CLI
     - Dashboard explanation
     - What lockouts mean
     - FAQ

**Files to Create:**
- `tests/e2e/test_full_production.py`
- `docs/INSTALLATION_GUIDE.md`
- `docs/ADMIN_GUIDE.md`
- `docs/TRADER_GUIDE.md`

**Success Criteria:**
- ✅ All E2E tests pass
- ✅ Installation works on fresh system
- ✅ Documentation clear and complete
- ✅ No manual intervention needed

---

## 📊 PHASE 2 COMPLETION CHECKLIST

- [ ] Task 1: Windows Service Wrapper (6-8 hours)
- [ ] Task 2: Service Installer (3-4 hours)
- [ ] Task 3: Admin CLI (8-10 hours)
- [ ] Task 4: Trader CLI (4-6 hours)
- [ ] Task 5: Testing & Documentation (4-6 hours)

**Total Time:** 25-34 hours (3-5 days)

---

## ✅ PHASE 2 COMPLETE WHEN:

- ✅ Windows Service installed and running
- ✅ Auto-starts on boot
- ✅ Admin CLI fully functional
- ✅ Trader CLI displays real-time data
- ✅ All 12 rules tested in production
- ✅ Multi-account monitoring verified
- ✅ Documentation complete
- ✅ E2E tests pass

---

## 🚦 HOW TO USE WHEN COMPLETE

**Installation:**
```batch
REM As Administrator
cd "C:\simple-risk-manager"
install.bat

REM Should see:
REM [1/4] Initializing database...
REM [2/4] Installing Windows Service...
REM [3/4] Starting Risk Manager Service...
REM [4/4] Installation complete!
```

**Admin CLI:**
```batch
python -m src.cli.admin.admin_main

REM Enter admin password:
REM ****
REM
REM ╔════════════════════════════════════════╗
REM ║     RISK MANAGER - ADMIN CONSOLE      ║
REM ╠════════════════════════════════════════╣
REM ║ 1. Service Control                     ║
REM ║ 2. Account Management                  ║
REM ║ 3. Rule Configuration                  ║
REM ║ 4. Connection Testing                  ║
REM ║ 5. View Logs                           ║
REM ║ 6. Exit                                ║
REM ╚════════════════════════════════════════╝
```

**Trader CLI:**
```batch
python -m src.cli.trader.trader_main

REM ╔════════════════════════════════════════╗
REM ║    RISK MANAGER - TRADER DASHBOARD    ║
REM ╠════════════════════════════════════════╣
REM ║ Account: 12345                         ║
REM ║ Status: ACTIVE                         ║
REM ║ Daily P&L: +$250.00                    ║
REM ║ Lockout: None                          ║
REM ╚════════════════════════════════════════╝
```

---

## 📁 FILES CREATED IN PHASE 2

**Windows Service:**
- `src/service/windows_service.py`
- `src/service/installer.py`
- `install.bat`
- `uninstall.bat`

**Admin CLI:**
- `src/cli/admin/admin_main.py`
- `src/cli/admin/ui_components.py`
- `src/cli/admin/service_control.py`

**Trader CLI:**
- `src/cli/trader/trader_main.py`
- `src/cli/trader/realtime_client.py`
- `src/cli/trader/ui_components.py`

**Documentation:**
- `docs/INSTALLATION_GUIDE.md`
- `docs/ADMIN_GUIDE.md`
- `docs/TRADER_GUIDE.md`

**Tests:**
- `tests/integration/test_windows_service.py`
- `tests/integration/test_installer.py`
- `tests/integration/test_admin_cli.py`
- `tests/integration/test_trader_cli.py`
- `tests/e2e/test_full_production.py`

---

**Phase 2 Status:** NOT STARTED
**Last Updated:** 2025-10-23
**Prerequisites:** Phase 1 COMPLETE
