---
doc_id: CONFIG-003
title: Admin Password Configuration Specification
version: 1.0
last_updated: 2025-10-21
created_by: Configuration Auditor Agent
---

# Admin Password Configuration Specification

**Purpose:** Specification for admin password storage and authentication

**File Location:** `config/admin_password.hash`

**Format:** Binary file (bcrypt hash)

---

## 🎯 Overview

The admin password controls access to the Admin CLI, which has full system privileges including:
- Configuration file editing
- Daemon service control
- Account authentication management
- Risk rule modification

**Security Level:** CRITICAL - This password protects all system administration functions.

---

## 📋 File Format

### **File Structure**

```
config/admin_password.hash
```

**Format:** Binary file containing bcrypt hash
**Size:** Typically 60 bytes
**Encoding:** UTF-8 encoded bcrypt hash string

**Example Content (not human-readable):**
```
$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5oDWEM7WQGhKy
```

---

## 🔐 Hash Algorithm Specification

### **Algorithm:** bcrypt

**Why bcrypt:**
- Designed for password hashing
- Adaptive (cost factor increases over time)
- Salt included automatically
- Resistant to rainbow table attacks
- Resistant to brute force (slow by design)

### **Cost Factor**

**Recommended:** 12 (default)
**Minimum:** 10
**Maximum:** 14 (for high-security environments)

**Cost Factor Meanings:**
- 10: ~100ms to hash (acceptable)
- 12: ~250ms to hash (recommended)
- 14: ~1000ms to hash (maximum security)

**Trade-off:** Higher cost = more security but slower login

---

## 📐 Password Requirements

### **Minimum Requirements**

| Requirement | Specification |
|-------------|---------------|
| **Min Length** | 8 characters |
| **Max Length** | 72 characters (bcrypt limit) |
| **Uppercase** | At least 1 (recommended) |
| **Lowercase** | At least 1 (recommended) |
| **Digits** | At least 1 (recommended) |
| **Special Chars** | At least 1 (recommended) |

### **Recommended Requirements**

For production environments:
- **Length:** 12+ characters
- **Complexity:** Mix of uppercase, lowercase, digits, special characters
- **No Dictionary Words:** Avoid common words or patterns
- **No Personal Info:** Avoid names, birthdays, etc.

### **Example Strong Passwords**

```
✅ R!sk#Mgr2025$Secure
✅ TradingB0t@Admin#99
✅ TopStep!Secure&Admin2025

❌ password123
❌ admin
❌ 12345678
```

---

## 🛠️ Initial Setup Procedure

### **Step 1: Set Admin Password (First Time)**

When Admin CLI runs for first time and `config/admin_password.hash` doesn't exist:

```python
import bcrypt
import getpass

def setup_initial_password():
    """Set up admin password on first run."""
    print("\n🔐 INITIAL ADMIN PASSWORD SETUP")
    print("=" * 50)
    print("\nNo admin password found. Let's create one.")
    print("\nPassword Requirements:")
    print("  - Minimum 8 characters")
    print("  - Recommended: 12+ characters")
    print("  - Mix of uppercase, lowercase, digits, symbols")
    print()

    while True:
        password = getpass.getpass("Enter new admin password: ")

        # Validate length
        if len(password) < 8:
            print("❌ Password too short. Minimum 8 characters.")
            continue

        if len(password) > 72:
            print("❌ Password too long. Maximum 72 characters.")
            continue

        # Confirm password
        confirm = getpass.getpass("Confirm admin password: ")

        if password != confirm:
            print("❌ Passwords don't match. Try again.")
            continue

        # Hash password
        cost_factor = 12  # Recommended cost
        salt = bcrypt.gensalt(rounds=cost_factor)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

        # Save to file
        with open('config/admin_password.hash', 'wb') as f:
            f.write(hashed)

        # Set restrictive permissions
        os.chmod('config/admin_password.hash', 0o600)

        print("✅ Admin password set successfully!")
        print("⚠️  Store this password securely - it cannot be recovered!")
        break
```

### **Step 2: File Permissions**

**Immediately after creation:**

**Linux/Mac:**
```bash
chmod 600 config/admin_password.hash
# Owner: read+write, Group: none, Others: none
```

**Windows (PowerShell):**
```powershell
$acl = Get-Acl "config\admin_password.hash"
$acl.SetAccessRuleProtection($true, $false)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    $env:USERNAME, "Read,Write", "Allow"
)
$acl.SetAccessRule($rule)
Set-Acl "config\admin_password.hash" $acl
```

---

## 🔑 Authentication Flow

### **Login Process**

```python
import bcrypt

def authenticate_admin(password: str) -> bool:
    """
    Authenticate admin password.

    Args:
        password: Plain text password entered by user

    Returns:
        True if password matches, False otherwise
    """
    try:
        # Read stored hash
        with open('config/admin_password.hash', 'rb') as f:
            stored_hash = f.read()

        # Check password
        password_bytes = password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, stored_hash)

    except FileNotFoundError:
        raise Exception("Admin password not configured. Run initial setup.")
    except Exception as e:
        raise Exception(f"Authentication error: {e}")
```

### **Login Attempt Limiting**

**Specification:**
- **Max Attempts:** 3 per session
- **Lockout Duration:** Exit program (no time-based lockout)
- **Rate Limiting:** None (offline attack vector minimal)

```python
def admin_login(max_attempts=3):
    """Prompt for admin password with attempt limiting."""
    for attempt in range(1, max_attempts + 1):
        password = getpass.getpass("\nEnter admin password: ")

        if authenticate_admin(password):
            print("✅ Authentication successful!")
            return True
        else:
            remaining = max_attempts - attempt
            if remaining > 0:
                print(f"❌ Incorrect password. {remaining} attempts remaining.")
            else:
                print("❌ Authentication failed. Exiting.")
                sys.exit(1)

    return False
```

---

## 🔄 Password Reset Procedure

### **Scenario 1: Password Forgotten**

**No recovery mechanism by design.** Admin must:

1. **Gain file system access** (requires Windows admin privileges)
2. **Delete hash file:**
   ```bash
   rm config/admin_password.hash
   ```
3. **Restart Admin CLI** (will prompt for new password)

### **Scenario 2: Planned Password Change**

Admin CLI should include "Change Admin Password" menu option:

```python
def change_admin_password():
    """Change admin password (requires current password)."""
    print("\n🔐 CHANGE ADMIN PASSWORD")
    print("=" * 50)

    # Verify current password
    current = getpass.getpass("Enter current password: ")
    if not authenticate_admin(current):
        print("❌ Current password incorrect.")
        return False

    # Get new password
    new_password = getpass.getpass("Enter new password: ")

    # Validate
    if len(new_password) < 8:
        print("❌ Password too short. Minimum 8 characters.")
        return False

    # Confirm
    confirm = getpass.getpass("Confirm new password: ")
    if new_password != confirm:
        print("❌ Passwords don't match.")
        return False

    # Hash and save
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(12))
    with open('config/admin_password.hash', 'wb') as f:
        f.write(hashed)

    print("✅ Password changed successfully!")
    return True
```

---

## 🔒 Security Best Practices

### **1. Physical Security**

- **Requirement:** System running Risk Manager must be physically secure
- **Reasoning:** File system access = password reset capability
- **Mitigation:** Use Windows user account with strong password

### **2. File Permissions**

- **Requirement:** Hash file readable only by daemon user
- **Linux/Mac:** `chmod 600 config/admin_password.hash`
- **Windows:** ACL limited to daemon user account

### **3. Password Strength**

- **Requirement:** Enforce minimum 8 characters (12+ recommended)
- **Recommendation:** Use password manager for strong random passwords
- **Warning:** No password complexity validation on input (user responsibility)

### **4. No Network Transmission**

- **Design:** Admin CLI is local only (no network authentication)
- **Benefit:** Password never transmitted over network
- **Limitation:** Must have local access to use Admin CLI

### **5. Rotation Policy**

**Recommended:**
- **Frequency:** Every 90 days
- **Trigger:** Whenever admin personnel changes
- **Procedure:** Use "Change Admin Password" in Admin CLI

---

## ⚠️ Security Warnings

### **Critical Warnings**

1. **No Password Recovery:**
   - Password cannot be recovered if forgotten
   - Must delete hash file and create new password
   - This is by design for security

2. **File System Access = Admin Access:**
   - Anyone who can delete `admin_password.hash` can reset password
   - Physical/filesystem security is critical

3. **No Account Lockout:**
   - No time-based lockout after failed attempts
   - Program exits after 3 failed attempts
   - Restart allows another 3 attempts
   - This is acceptable because attack requires local access

4. **Bcrypt 72-Character Limit:**
   - Bcrypt truncates passwords longer than 72 characters
   - Validation enforces this limit

---

## 🧪 Validation

### **File Validation**

```python
def validate_password_hash_file():
    """Validate admin password hash file."""

    # Check file exists
    if not os.path.exists('config/admin_password.hash'):
        raise ValidationError("Admin password file not found")

    # Check file size
    file_size = os.path.getsize('config/admin_password.hash')
    if file_size < 30 or file_size > 100:
        raise ValidationError("Invalid hash file size")

    # Check file is readable
    try:
        with open('config/admin_password.hash', 'rb') as f:
            hash_data = f.read()
    except PermissionError:
        raise ValidationError("Cannot read hash file - check permissions")

    # Check hash format (bcrypt starts with $2b$ or $2a$ or $2y$)
    hash_str = hash_data.decode('utf-8')
    if not (hash_str.startswith('$2b$') or
            hash_str.startswith('$2a$') or
            hash_str.startswith('$2y$')):
        raise ValidationError("Invalid bcrypt hash format")

    # Check hash length (bcrypt hashes are 60 characters)
    if len(hash_str.strip()) != 60:
        raise ValidationError("Invalid bcrypt hash length")

    return True
```

---

## 📖 Testing

### **Test 1: Initial Setup**

```python
# Scenario: No password file exists
# Expected: Prompt for new password, create hash file
assert not os.path.exists('config/admin_password.hash')
setup_initial_password()  # Interactive
assert os.path.exists('config/admin_password.hash')
```

### **Test 2: Valid Authentication**

```python
# Scenario: Correct password
# Expected: Returns True
result = authenticate_admin("correct_password")
assert result == True
```

### **Test 3: Invalid Authentication**

```python
# Scenario: Wrong password
# Expected: Returns False
result = authenticate_admin("wrong_password")
assert result == False
```

### **Test 4: Password Change**

```python
# Scenario: Change password
# Expected: Old password invalid, new password valid
old_pass = "OldPassword123"
new_pass = "NewPassword456"

assert authenticate_admin(old_pass) == True
change_admin_password()  # Interactive
assert authenticate_admin(old_pass) == False
assert authenticate_admin(new_pass) == True
```

---

## 📝 Summary

**Configuration File:** `config/admin_password.hash`

**Format:** Binary bcrypt hash (60 bytes)

**Algorithm:** bcrypt with cost factor 12

**Password Requirements:**
- Minimum 8 characters
- Maximum 72 characters
- Recommended: 12+ with mixed complexity

**Security Features:**
- Salted hashing (bcrypt)
- Adaptive cost factor
- File permissions (600)
- No network transmission
- 3-attempt limit per session

**Limitations:**
- No password recovery (by design)
- No account lockout (local access only)
- Physical access = reset capability

**Related Files:**
- `src/cli/admin_cli.py` - Admin CLI implementation
- `src/auth/admin_auth.py` - Authentication module
- `06-CLI-FRONTEND/ADMIN_CLI_SPEC.md` - Admin CLI specification

---

**Status:** Complete and ready for implementation
