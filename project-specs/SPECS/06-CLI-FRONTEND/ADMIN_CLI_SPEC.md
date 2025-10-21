---
doc_id: CLI-ADMIN-001
version: 1.0
last_updated: 2025-10-21
dependencies: [DAEMON-001, FRONTEND-BACKEND-001, CONFIG-001, CONFIG-002]
---

# Admin CLI Specification

**Purpose:** Complete specification for admin CLI - setup wizard and configuration tool with beautiful UI

**File Coverage:** `src/cli/admin/admin_main.py`, `src/cli/admin/ui_components.py`, `src/cli/admin/service_control.py`

---

## 🎯 Overview

### **What is the Admin CLI?**
A setup wizard and configuration tool for administrators to:
- Authenticate with TopstepX API
- Manage trader accounts
- Configure risk rules
- Control Windows Service (install, start, stop, restart)
- Test connections
- View daemon status

### **Key Features:**
- **Beautiful ANSI UI** with centered menus, colors, and animations
- **Number-based selection** (type 1, 2, 3 - no external dependencies)
- **Password authentication** (admin-only access)
- **Windows Service control** (requires admin privileges)
- **YAML configuration editing** (accounts.yaml, risk_config.yaml)
- **Connection testing** (TopstepX API, SignalR, database)

### **Access Level:**
- ✅ **REQUIRES** admin password authentication
- ✅ **REQUIRES** Windows admin privileges (for service control)
- ✅ **CAN** modify all configuration files
- ✅ **CAN** install/start/stop/restart daemon service
- ✅ **CAN** authenticate trader accounts
- ❌ **NO real-time dashboard** (use Trader CLI for that)

---

## 🎨 UI Design Philosophy

### **Design Principles:**
1. **Centered Layout** - All content centered in terminal
2. **Color-Coded Sections** - Each menu has a semantic color
3. **Beautiful Borders** - Unicode box drawing (╔═══╗)
4. **Loading Animations** - Spinner animations for operations
5. **No Dependencies** - Pure Python 3, no pip install needed

### **Color Scheme:**
```python
class Colors:
    """ANSI color codes for beautiful terminal UI"""
    RESET = '\033[0m'

    # Text colors
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BRIGHT_WHITE = '\033[1;97m'

    # Semantic colors
    BLUE = '\033[94m'           # Authentication
    CYAN = '\033[96m'           # Account management
    YELLOW = '\033[93m'         # Rules/warnings
    GREEN = '\033[92m'          # Service/success
    MAGENTA = '\033[95m'        # Testing
    RED = '\033[91m'            # Danger/errors

    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
```

### **Box Drawing Characters:**
```python
# Unicode box drawing
TOP_LEFT = "╔"
TOP_RIGHT = "╗"
BOTTOM_LEFT = "╚"
BOTTOM_RIGHT = "╝"
HORIZONTAL = "═"
VERTICAL = "║"
T_DOWN = "╦"
T_UP = "╩"
T_RIGHT = "╠"
T_LEFT = "╣"
```

---

## 🔐 Login Screen

### **Layout:**
```
                    ██████╗ ██╗███████╗██╗  ██╗
                    ██╔══██╗██║██╔════╝██║ ██╔╝
                    ██████╔╝██║███████╗█████╔╝
                    ██╔══██╗██║╚════██║██╔═██╗
                    ██║  ██║██║███████║██║  ██╗
                    ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝

              Risk Manager - Admin Configuration v1.0.0


              ╔══════════════════════════════════════════════════════╗
              ║ 🔐 Admin Authentication Required                    ║
              ╠══════════════════════════════════════════════════════╣
              ║ Enter admin password to continue                    ║
              ║                                                      ║
              ║ ⚠️  This tool requires admin privileges             ║
              ║                                                      ║
              ╚══════════════════════════════════════════════════════╝

              Password (hidden): ********
```

### **Authentication Flow:**
1. **Prompt for password** (input hidden with `getpass` module)
2. **Hash password** using bcrypt
3. **Compare with stored hash** in `config/admin_password.hash`
4. **3 attempts allowed** - then exit
5. **On success:** Show main menu

### **Password Storage:**
```python
# config/admin_password.hash
# Contains bcrypt hash of admin password
# Generated during initial setup

import bcrypt

# Set password (one-time setup)
password = "admin123"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Save to file
with open('config/admin_password.hash', 'wb') as f:
    f.write(hashed)

# Verify password (on login)
with open('config/admin_password.hash', 'rb') as f:
    stored_hash = f.read()

if bcrypt.checkpw(entered_password.encode(), stored_hash):
    print("✓ Access granted")
else:
    print("✗ Access denied")
```

### **Windows Admin Privilege Check:**
```python
import ctypes

def is_admin():
    """Check if running with Windows admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    print("❌ This tool requires Windows admin privileges")
    print("   Right-click and 'Run as Administrator'")
    sys.exit(1)
```

---

## 📋 Main Menu

### **Layout:**
```
                    ██████╗ ██╗███████╗██╗  ██╗
                    ██╔══██╗██║██╔════╝██║ ██╔╝
                    ██████╔╝██║███████╗█████╔╝
                    ██╔══██╗██║╚════██║██╔═██╗
                    ██║  ██║██║███████║██║  ██╗
                    ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝

              Risk Manager - Admin Configuration v1.0.0


              ╔══════════════════════════════════════════════════════╗
              ║ Quick Actions                                        ║
              ╠══════════════════════════════════════════════════════╣
              ║                                                      ║
              ║ 1. 🔐 Configure Authentication                      ║
              ║ 2. 👤 Manage Accounts                               ║
              ║ 3. ⚙️  Configure Risk Rules                          ║
              ║ 4. 🚀 Service Control                               ║
              ║ 5. 🔍 Test Connection                               ║
              ║ 6. 📊 View Daemon Status                            ║
              ║                                                      ║
              ║ 0. Exit                                              ║
              ║                                                      ║
              ╚══════════════════════════════════════════════════════╝

              Enter choice [0-6]: _
```

### **Menu Options:**

1. **Configure Authentication** (Blue 🔐)
   - Enter TopstepX username and API key
   - Validate credentials
   - Obtain JWT token
   - Save to `config/accounts.yaml`

2. **Manage Accounts** (Cyan 👤)
   - Add new trader account
   - Edit existing account
   - Remove account
   - View all accounts

3. **Configure Risk Rules** (Yellow ⚙️)
   - Edit rule limits
   - Enable/disable rules
   - Set enforcement actions
   - Configure reset times

4. **Service Control** (Green 🚀)
   - Install Windows Service (one-time)
   - Start service
   - Stop service
   - Restart service
   - Uninstall service
   - View service status

5. **Test Connection** (Magenta 🔍)
   - Test TopstepX API connection
   - Test SignalR WebSocket
   - Test account authentication
   - Test database access

6. **View Daemon Status** (Cyan 📊)
   - Service status (running/stopped)
   - Uptime
   - CPU/memory usage
   - Connection status
   - Recent logs

---

## 🔐 Screen 1: Configure Authentication

### **Layout:**
```
              ╔══════════════════════════════════════════════════════╗
              ║ 🔐 Authentication Configuration                     ║
              ╠══════════════════════════════════════════════════════╣
              ║ Enter your TopstepX API credentials                 ║
              ║                                                      ║
              ╚══════════════════════════════════════════════════════╝

              Username: trader1@example.com
              API Key (hidden): ********************************


              ⠋ Validating credentials...

              ✓ Validating credentials - Complete!

              ✓ Authentication successful!
              ℹ JWT token obtained (valid 24h)

              Press ENTER to continue...
```

### **Process:**
1. **Prompt for username** (email or username)
2. **Prompt for API key** (masked input)
3. **Show loading animation** ("Validating credentials...")
4. **Call TopstepX auth API:**
   ```python
   import requests

   response = requests.post(
       "https://api.topstepx.com/auth/validate",
       json={
           "username": username,
           "apiKey": api_key
       }
   )

   if response.status_code == 200:
       jwt_token = response.json()['token']
       print("✓ Authentication successful!")
       print("ℹ JWT token obtained (valid 24h)")
   else:
       print("✗ Authentication failed")
   ```
5. **Save to accounts.yaml:**
   ```yaml
   accounts:
     - account_id: 123
       username: "trader1@example.com"
       api_key: "abc123..."
       jwt_token: "eyJ..."  # Optional - can be stored
   ```
6. **Show success message**
7. **Return to main menu**

---

## 👤 Screen 2: Manage Accounts

### **Layout:**
```
              ╔══════════════════════════════════════════════════════╗
              ║ 👤 Account Management                               ║
              ╠══════════════════════════════════════════════════════╣
              ║                                                      ║
              ║ 1. Main Trading Account                             ║
              ║    ID: 1234 | trader1@example.com | ✅ Active       ║
              ║                                                      ║
              ║ 2. Practice Account                                 ║
              ║    ID: 1235 | trader2@example.com | ✅ Active       ║
              ║                                                      ║
              ║ 3. Demo Account                                     ║
              ║    ID: 1236 | demo@example.com | ⏸️  Paused          ║
              ║                                                      ║
              ╚══════════════════════════════════════════════════════╝

              ╔══════════════════════════════════════════════════════╗
              ║ Actions                                              ║
              ╠══════════════════════════════════════════════════════╣
              ║ A. Add New Account                                   ║
              ║ E. Edit Account                                      ║
              ║ D. Delete Account                                    ║
              ║ 0. Back to Main Menu                                 ║
              ╚══════════════════════════════════════════════════════╝

              Select action: _
```

### **Actions:**

**A. Add New Account:**
1. Prompt for account details:
   - Account ID (integer)
   - Username/email
   - API key
2. Validate credentials (call auth API)
3. Add to `config/accounts.yaml`
4. Show success message

**E. Edit Account:**
1. Prompt for account number (1-3)
2. Show current details
3. Prompt for field to edit (username, API key)
4. Update `config/accounts.yaml`
5. Show success message

**D. Delete Account:**
1. Prompt for account number (1-3)
2. Show confirmation dialog:
   ```
   ⚠️  Are you sure you want to delete account 1234?
   This action cannot be undone.

   Type 'DELETE' to confirm: _
   ```
3. Remove from `config/accounts.yaml`
4. Show success message

---

## ⚙️ Screen 3: Configure Risk Rules

### **Layout:**
```
              ╔══════════════════════════════════════════════════════╗
              ║ ⚙️  Risk Rules Configuration                         ║
              ╠══════════════════════════════════════════════════════╣
              ║                                                      ║
              ║ ✅ 1. Max Contracts (Global)                        ║
              ║    Limit: 10 | Action: Close all positions          ║
              ║                                                      ║
              ║ ✅ 2. Max Contracts Per Instrument                  ║
              ║    MNQ: 5, ES: 3 | Action: Reduce to limit          ║
              ║                                                      ║
              ║ ✅ 3. Daily Realized Loss Limit                     ║
              ║    Limit: -$2000 | Reset: 17:00 ET                  ║
              ║                                                      ║
              ║ ✅ 4. Daily Unrealized Loss Limit                   ║
              ║    Limit: -$1500 | Action: Close all + lockout      ║
              ║                                                      ║
              ║ ❌ 5. Session Block (Outside Hours)                 ║
              ║    Hours: 9:30-16:00 ET | Disabled                  ║
              ║                                                      ║
              ║ ... (7 more rules)                                   ║
              ║                                                      ║
              ╚══════════════════════════════════════════════════════╝

              ╔══════════════════════════════════════════════════════╗
              ║ Actions                                              ║
              ╠══════════════════════════════════════════════════════╣
              ║ E. Edit Rule (type E then rule number)               ║
              ║ T. Toggle Enable/Disable                             ║
              ║ R. Reset All to Defaults                             ║
              ║ 0. Back to Main Menu                                 ║
              ╚══════════════════════════════════════════════════════╝

              Select action: _
```

### **Edit Rule Flow:**
1. **Select rule** (type "E" then rule number)
2. **Show rule editor:**
   ```
   ╔══════════════════════════════════════════════════════╗
   ║ Edit Rule: Daily Realized Loss Limit                ║
   ╠══════════════════════════════════════════════════════╣
   ║ Current Settings:                                    ║
   ║   Enabled: Yes                                       ║
   ║   Limit: -$2000                                      ║
   ║   Reset Time: 17:00 ET                               ║
   ║   Reset Timezone: America/New_York                   ║
   ║   Action: Close all + lockout (until reset)          ║
   ║                                                      ║
   ╚══════════════════════════════════════════════════════╝

   Field to edit [limit/reset_time/action/cancel]: limit
   New limit (current: -$2000): -$3000

   ⠋ Saving configuration...

   ✓ Rule updated successfully!
   ℹ Changes will apply on next daemon restart

   Press ENTER to continue...
   ```
3. **Update `config/risk_config.yaml`**
4. **Show success message**

### **Toggle Enable/Disable:**
1. Prompt for rule number
2. Toggle `enabled: true/false` in YAML
3. Show success message

### **Reset All to Defaults:**
1. Show confirmation dialog
2. Restore default `risk_config.yaml` from template
3. Show success message

---

## 🚀 Screen 4: Service Control

### **Layout:**
```
              ╔══════════════════════════════════════════════════════╗
              ║ 🚀 Service Status                                    ║
              ╠══════════════════════════════════════════════════════╣
              ║ ● RUNNING                                            ║
              ║ PID: 12345 | Uptime: 3h 24m | CPU: 2.3% | Mem: 45MB ║
              ║                                                      ║
              ║ Connections:                                         ║
              ║ ✅ TopstepX API - Connected (45ms)                  ║
              ║ ✅ SignalR WebSocket - Connected (32ms)             ║
              ║ ✅ WebSocket Server - Listening (ws://localhost:8765)║
              ║ ✅ Database - OK (state.db, 245KB)                  ║
              ║                                                      ║
              ╚══════════════════════════════════════════════════════╝

              ╔══════════════════════════════════════════════════════╗
              ║ Actions                                              ║
              ╠══════════════════════════════════════════════════════╣
              ║ 1. ▶️  Start Service                                 ║
              ║ 2. ⏹️  Stop Service                                  ║
              ║ 3. 🔄 Restart Service                                ║
              ║ 4. 📋 View Logs                                      ║
              ║ 5. 🔧 Install Service (one-time setup)               ║
              ║ 6. ❌ Uninstall Service                              ║
              ║ 0. Back to Main Menu                                 ║
              ╚══════════════════════════════════════════════════════╝

              Select action [0-6]: _
```

### **Service Actions:**

**1. Start Service:**
```python
import win32serviceutil

def start_service():
    print("⠋ Starting Risk Manager service...")

    try:
        win32serviceutil.StartService("RiskManagerDaemon")
        time.sleep(2)  # Wait for service to start

        # Check status
        status = get_service_status()
        if status == "RUNNING":
            print("✓ Service started successfully!")
        else:
            print(f"⚠️  Service status: {status}")
    except Exception as e:
        print(f"✗ Failed to start service: {e}")
```

**2. Stop Service:**
```python
def stop_service():
    print("⠋ Stopping Risk Manager service...")

    try:
        win32serviceutil.StopService("RiskManagerDaemon")
        time.sleep(2)  # Wait for graceful shutdown

        status = get_service_status()
        if status == "STOPPED":
            print("✓ Service stopped successfully!")
        else:
            print(f"⚠️  Service status: {status}")
    except Exception as e:
        print(f"✗ Failed to stop service: {e}")
```

**3. Restart Service:**
```python
def restart_service():
    print("⠋ Restarting Risk Manager service...")

    stop_service()
    time.sleep(2)
    start_service()
```

**4. View Logs:**
```
╔══════════════════════════════════════════════════════════════╗
║ 📋 Live Service Logs (Last 20 lines)                        ║
╠══════════════════════════════════════════════════════════════╣
║ [14:45:12] INFO  Event received: GatewayUserPosition        ║
║ [14:45:12] DEBUG Position updated: MNQ +2 @ 21000.5         ║
║ [14:45:13] INFO  Rule check: MaxContractsPerInstr           ║
║ [14:45:13] INFO  ✓ Within limit (2/5 allowed)               ║
║ [14:45:15] INFO  Event received: GatewayUserTrade           ║
║ [14:45:15] DEBUG Trade: MNQ SELL 1 @ 21001.0                ║
║ [14:45:15] INFO  P&L updated: -$45.50 (realized)            ║
║ [14:45:15] INFO  ✓ Within limit (-$45.50 / -$2000)          ║
║ [14:45:20] INFO  SignalR heartbeat: OK                      ║
║ [14:45:25] INFO  WebSocket broadcast: 3 clients connected   ║
║ ... (10 more lines)                                          ║
╚══════════════════════════════════════════════════════════════╝

Press ENTER to continue...
```

**5. Install Service (One-Time Setup):**
```python
def install_service():
    print("⠋ Installing Risk Manager Windows Service...")

    # Check admin privileges
    if not is_admin():
        print("✗ Admin privileges required")
        return

    try:
        subprocess.run(
            [sys.executable, "src/service/windows_service.py", "install"],
            check=True
        )

        # Configure auto-start
        win32serviceutil.ChangeServiceConfig(
            None,
            "RiskManagerDaemon",
            startType=win32service.SERVICE_AUTO_START
        )

        print("✓ Service installed successfully!")
        print("ℹ Service will auto-start on boot")
    except Exception as e:
        print(f"✗ Failed to install service: {e}")
```

**6. Uninstall Service:**
```python
def uninstall_service():
    # Show confirmation
    confirm = input("⚠️  Type 'UNINSTALL' to confirm: ")

    if confirm != "UNINSTALL":
        print("ℹ Cancelled")
        return

    print("⠋ Uninstalling Risk Manager Windows Service...")

    # Stop service first
    try:
        win32serviceutil.StopService("RiskManagerDaemon")
        time.sleep(2)
    except:
        pass

    # Uninstall
    try:
        subprocess.run(
            [sys.executable, "src/service/windows_service.py", "remove"],
            check=True
        )

        print("✓ Service uninstalled successfully!")
    except Exception as e:
        print(f"✗ Failed to uninstall service: {e}")
```

---

## 🔍 Screen 5: Test Connection

### **Layout:**
```
              ╔══════════════════════════════════════════════════════╗
              ║ 🔍 Connection Test                                   ║
              ╠══════════════════════════════════════════════════════╣
              ║ Running diagnostic tests...                          ║
              ║                                                      ║
              ╚══════════════════════════════════════════════════════╝

              ⠋ Testing TopstepX API...
              ✓ Testing TopstepX API - Complete!

              ⠋ Testing SignalR WebSocket...
              ✓ Testing SignalR WebSocket - Complete!

              ⠋ Testing Account Authentication...
              ✓ Testing Account Authentication - Complete!

              ⠋ Testing Database Access...
              ✓ Testing Database Access - Complete!

              ⠋ Testing WebSocket Server...
              ✓ Testing WebSocket Server - Complete!


              ╔══════════════════════════════════════════════════════╗
              ║ Test Results                                         ║
              ╠══════════════════════════════════════════════════════╣
              ║ ✅ TopstepX API - OK (response time: 145ms)         ║
              ║ ✅ SignalR User Hub - Connected                     ║
              ║ ✅ SignalR Market Hub - Connected                   ║
              ║ ✅ Account 1234 - Authenticated                     ║
              ║ ✅ Account 1235 - Authenticated                     ║
              ║ ✅ Database - OK (state.db, 245KB)                  ║
              ║ ✅ WebSocket Server - Listening on localhost:8765   ║
              ║                                                      ║
              ║ All tests passed! ✓                                  ║
              ║                                                      ║
              ╚══════════════════════════════════════════════════════╝

              Press ENTER to continue...
```

### **Test Implementation:**
```python
import requests
import sqlite3
import websocket

def test_topstepx_api():
    """Test TopstepX API connection"""
    try:
        response = requests.get(
            "https://api.topstepx.com/health",
            timeout=5
        )
        if response.status_code == 200:
            return True, f"OK (response time: {response.elapsed.total_seconds() * 1000:.0f}ms)"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_signalr():
    """Test SignalR connection"""
    try:
        # Attempt to connect to SignalR hubs
        # (implementation depends on signalr-client library)
        return True, "Connected"
    except Exception as e:
        return False, str(e)

def test_account_auth(account_id, username, api_key):
    """Test account authentication"""
    try:
        response = requests.post(
            "https://api.topstepx.com/auth/validate",
            json={"username": username, "apiKey": api_key},
            timeout=5
        )
        if response.status_code == 200:
            return True, "Authenticated"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_database():
    """Test database access"""
    try:
        db = sqlite3.connect('data/state.db')
        cursor = db.execute("SELECT COUNT(*) FROM sqlite_master")
        count = cursor.fetchone()[0]

        # Get file size
        import os
        size_kb = os.path.getsize('data/state.db') / 1024

        db.close()
        return True, f"OK (state.db, {size_kb:.0f}KB)"
    except Exception as e:
        return False, str(e)

def test_websocket_server():
    """Test WebSocket server"""
    try:
        ws = websocket.create_connection("ws://localhost:8765", timeout=2)
        ws.close()
        return True, "Listening on localhost:8765"
    except Exception as e:
        return False, str(e)
```

---

## 📊 Screen 6: View Daemon Status

### **Layout:**
```
              ╔══════════════════════════════════════════════════════╗
              ║ 📊 Daemon Status                                     ║
              ╠══════════════════════════════════════════════════════╣
              ║                                                      ║
              ║ Service: ● RUNNING                                   ║
              ║ PID: 12345                                           ║
              ║ Uptime: 3h 24m 15s                                   ║
              ║ CPU: 2.3% | Memory: 45.2 MB                          ║
              ║                                                      ║
              ╚══════════════════════════════════════════════════════╝

              ╔══════════════════════════════════════════════════════╗
              ║ Connections                                          ║
              ╠══════════════════════════════════════════════════════╣
              ║ ✅ TopstepX API - Connected (45ms)                  ║
              ║ ✅ SignalR User Hub - Connected (32ms)              ║
              ║ ✅ SignalR Market Hub - Connected (28ms)            ║
              ║ ✅ WebSocket Server - 3 clients connected           ║
              ║ ✅ Database - OK (state.db)                         ║
              ║                                                      ║
              ╚══════════════════════════════════════════════════════╝

              ╔══════════════════════════════════════════════════════╗
              ║ Monitored Accounts                                   ║
              ╠══════════════════════════════════════════════════════╣
              ║ Account 1234 - trader1@example.com                  ║
              ║   Status: ✅ Active                                  ║
              ║   P&L Today: +$1,250.00                              ║
              ║   Positions: 3 open                                  ║
              ║   Lockouts: None                                     ║
              ║                                                      ║
              ║ Account 1235 - trader2@example.com                  ║
              ║   Status: 🔴 Locked (Daily loss limit)              ║
              ║   P&L Today: -$2,100.00                              ║
              ║   Positions: 0 open (all closed by enforcement)      ║
              ║   Lockouts: Active until 17:00 ET                    ║
              ║                                                      ║
              ╚══════════════════════════════════════════════════════╝

              ╔══════════════════════════════════════════════════════╗
              ║ Recent Events (Last 10)                              ║
              ╠══════════════════════════════════════════════════════╣
              ║ [14:45:25] Account 1234 - Trade executed (MNQ)      ║
              ║ [14:45:20] WebSocket broadcast sent (3 clients)      ║
              ║ [14:45:15] Account 1235 - ENFORCEMENT: Lockout set  ║
              ║ [14:45:15] Account 1235 - ENFORCEMENT: Close all    ║
              ║ [14:45:13] Account 1234 - Rule check: OK            ║
              ║ ... (5 more events)                                  ║
              ║                                                      ║
              ╚══════════════════════════════════════════════════════╝

              Press ENTER to continue...
```

### **Data Sources:**
- **Service Status:** Win32 service API
- **Connections:** Read from daemon logs or query daemon
- **Accounts:** Read from `data/state.db` (daily_pnl, lockouts, positions)
- **Recent Events:** Read from `logs/daemon.log` (last 10 lines)

---

## 🚀 Main Implementation

### **src/cli/admin/admin_main.py** (~500 lines)

```python
"""
Main Admin CLI entry point.
Beautiful menu-driven interface for configuration and service control.
"""

import os
import sys
import time
import getpass
import bcrypt
import ctypes
from typing import Optional

# Import UI components
from ui_components import *
from service_control import *

class AdminCLI:
    """Main Admin CLI application"""

    def __init__(self):
        self.authenticated = False

    def check_admin_privileges(self):
        """Check if running with Windows admin privileges"""
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            is_admin = False

        if not is_admin:
            clear_screen()
            print_centered(f"{Colors.RED}❌ This tool requires Windows admin privileges{Colors.RESET}")
            print_centered("   Right-click and 'Run as Administrator'")
            print()
            sys.exit(1)

    def authenticate(self):
        """Admin password authentication"""
        clear_screen()
        show_header()

        print_box(
            "🔐 Admin Authentication Required",
            "Enter admin password to continue\n\n⚠️  This tool requires admin privileges",
            Colors.BLUE,
            60
        )
        print()

        # Load stored password hash
        try:
            with open('config/admin_password.hash', 'rb') as f:
                stored_hash = f.read()
        except FileNotFoundError:
            print_centered(f"{Colors.RED}✗ Admin password not set{Colors.RESET}")
            print_centered("   Run setup wizard first")
            sys.exit(1)

        # Allow 3 attempts
        attempts = 3

        for attempt in range(attempts):
            password = getpass.getpass(
                center_text(f"{Colors.CYAN}Password (hidden): {Colors.RESET}")
            )

            if bcrypt.checkpw(password.encode(), stored_hash):
                print()
                print_centered(f"{Colors.GREEN}✓ Access granted{Colors.RESET}")
                time.sleep(1)
                self.authenticated = True
                return
            else:
                remaining = attempts - attempt - 1
                if remaining > 0:
                    print()
                    print_centered(f"{Colors.RED}✗ Incorrect password{Colors.RESET}")
                    print_centered(f"   {remaining} attempts remaining")
                    print()

        # All attempts failed
        print()
        print_centered(f"{Colors.RED}✗ Access denied - too many failed attempts{Colors.RESET}")
        time.sleep(2)
        sys.exit(1)

    def show_main_menu(self):
        """Show main menu and get user choice"""
        clear_screen()
        show_header()

        menu_items = f"""
{Colors.BLUE}{Colors.BOLD}1.{Colors.RESET} {Colors.BLUE}🔐 Configure Authentication{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}2.{Colors.RESET} {Colors.CYAN}👤 Manage Accounts{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}3.{Colors.RESET} {Colors.YELLOW}⚙️  Configure Risk Rules{Colors.RESET}
{Colors.GREEN}{Colors.BOLD}4.{Colors.RESET} {Colors.GREEN}🚀 Service Control{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}5.{Colors.RESET} {Colors.MAGENTA}🔍 Test Connection{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}6.{Colors.RESET} {Colors.CYAN}📊 View Daemon Status{Colors.RESET}

{Colors.RED}{Colors.BOLD}0.{Colors.RESET} {Colors.RED}Exit{Colors.RESET}
"""

        print_box("Quick Actions", menu_items.strip(), Colors.CYAN, 60)
        print()

        choice = get_input("Enter choice [0-6]:")
        return choice

    def run(self):
        """Main application loop"""
        # Check admin privileges
        self.check_admin_privileges()

        # Authenticate
        self.authenticate()

        # Main menu loop
        while True:
            choice = self.show_main_menu()

            if choice == '0':
                clear_screen()
                print_centered(f"{Colors.GREEN}Thank you for using Risk Manager!{Colors.RESET}")
                print()
                sys.exit(0)
            elif choice == '1':
                show_authentication()
            elif choice == '2':
                show_account_management()
            elif choice == '3':
                show_risk_rules()
            elif choice == '4':
                show_service_control()
            elif choice == '5':
                show_connection_test()
            elif choice == '6':
                show_daemon_status()
            else:
                print_centered(f"{Colors.RED}Invalid choice. Please try again.{Colors.RESET}")
                time.sleep(1)

# Entry point
if __name__ == "__main__":
    try:
        app = AdminCLI()
        app.run()
    except KeyboardInterrupt:
        clear_screen()
        print_centered(f"{Colors.YELLOW}Setup cancelled by user{Colors.RESET}")
        print()
        sys.exit(0)
```

---

## 📝 Summary

**Key Points:**

1. **Beautiful ANSI UI** with centered menus, colors, animations
2. **Number-based navigation** (type 1-6, no mouse needed)
3. **Password authentication** (bcrypt hash verification)
4. **Windows admin privileges required** (for service control)
5. **YAML configuration editing** (accounts.yaml, risk_config.yaml)
6. **Windows Service control** (install, start, stop, restart, uninstall)
7. **Connection testing** (TopstepX API, SignalR, database, WebSocket)
8. **Daemon status monitoring** (uptime, connections, accounts, logs)
9. **No real-time dashboard** (that's Trader CLI's job)

**Files to Implement:**
- `src/cli/admin/ui_components.py` (~300 lines) - Colors, boxes, animations, centering
- `src/cli/admin/service_control.py` (~200 lines) - Windows Service management
- `src/cli/admin/admin_main.py` (~500 lines) - Main menu and screens

**Total: ~1000 lines** (UI components + service control + main app)

**Dependencies:**
- `bcrypt` library (for password hashing)
- `pywin32` library (for Windows Service control)
- `pyyaml` library (for YAML editing)
- Built-in: `getpass`, `os`, `sys`, `time`, `ctypes`

**UI Pattern:**
Based on `examples/cli/admin/cli-clickable.py` - beautiful, centered, colorful menus with no external UI dependencies (just ANSI codes).

---

**Next Step:** All frontend/backend specs complete! Ready for implementation.
