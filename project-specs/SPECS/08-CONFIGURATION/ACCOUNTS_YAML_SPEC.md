---
doc_id: CONFIG-001
title: accounts.yaml Specification
version: 1.0
last_updated: 2025-10-21
---

# accounts.yaml Configuration Specification

**Purpose:** Complete specification for the accounts configuration file

**File Location:** `config/accounts.yaml`

**Format:** YAML

---

## 🎯 Overview

The `accounts.yaml` file defines which TopstepX trading accounts the Risk Manager should monitor. Each account requires authentication credentials and optional metadata.

**Key Features:**
- Multiple accounts supported
- Per-account enable/disable
- Optional nicknames for UI display
- Secure API key storage (not committed to git)

---

## 📋 Complete Schema

```yaml
# accounts.yaml - Trading account configurations

accounts:
  - account_id: 123456              # Required: TopstepX account ID
    username: "trader@example.com"  # Required: TopstepX username (email)
    api_key: "sk_live_abc123..."    # Required: TopstepX API key
    enabled: true                    # Optional: Enable/disable monitoring (default: true)
    nickname: "John's Main Account" # Optional: Display name for UI

  - account_id: 789012
    username: "trader2@example.com"
    api_key: "sk_live_def456..."
    enabled: false                   # Disabled - won't be monitored
    nickname: "Test Account"

  - account_id: 345678
    username: "trader3@example.com"
    api_key: "sk_live_ghi789..."
    # enabled defaults to true
    # nickname is optional
```

---

## 🔑 Field Specifications

### **accounts** (array, required)

Top-level array containing account configurations.

**Minimum:** 1 account
**Maximum:** Unlimited (but daemon monitors all simultaneously)

---

### **account_id** (integer, required)

The unique TopstepX account ID.

**Format:** Positive integer
**Example:** `123456`

**How to Find:**
1. Log in to TopstepX platform
2. Navigate to Account Settings
3. Copy the Account ID displayed

**Validation:**
- Must be positive integer
- Must be unique across all accounts in file

---

### **username** (string, required)

The TopstepX account username (email address).

**Format:** Valid email address
**Example:** `"trader@example.com"`

**Validation:**
- Must be valid email format
- Used for authentication via TopstepX API

**Security Note:** This is visible in logs, but API key is never logged.

---

### **api_key** (string, required)

The TopstepX API key for authentication.

**Format:** String starting with `sk_live_` or `sk_test_`
**Example:** `"sk_live_abc123def456ghi789..."`

**How to Get:**
1. Log in to TopstepX platform
2. Navigate to API Settings
3. Generate new API key
4. Copy immediately (shown only once)

**Security:**
- ⚠️ **NEVER commit this file to git with real API keys**
- Use `.gitignore` to exclude `config/accounts.yaml`
- Store production keys in secure password manager
- Rotate keys periodically

**Validation:**
- Must be non-empty string
- Must start with `sk_live_` (production) or `sk_test_` (testing)

---

### **enabled** (boolean, optional)

Whether to monitor this account.

**Default:** `true`
**Example:** `true` or `false`

**Use Cases:**
- `true`: Actively monitor and enforce rules
- `false`: Ignore account (useful for temporary disable)

**Behavior When `false`:**
- Daemon skips authentication for this account
- No events are processed
- Account not shown in Trader CLI
- Account still visible in Admin CLI (as "disabled")

---

### **nickname** (string, optional)

Human-readable display name for the account.

**Default:** `null` (uses username instead)
**Example:** `"John's Main Account"`

**Use Cases:**
- Distinguish multiple accounts in Trader CLI
- More readable than email addresses
- Helpful when monitoring multiple traders

**Display:**
- Trader CLI: Shows nickname if set, otherwise username
- Admin CLI: Shows both nickname and username

---

## 📖 Complete Example

```yaml
# accounts.yaml
# Trading accounts to monitor

accounts:
  # Production account - actively trading
  - account_id: 123456
    username: "john.trader@example.com"
    api_key: "sk_live_EXAMPLE_KEY_NOT_REAL_DO_NOT_USE_1234"
    enabled: true
    nickname: "John's Main Account"

  # Demo account - for testing
  - account_id: 789012
    username: "demo@example.com"
    api_key: "sk_test_EXAMPLE_KEY_NOT_REAL_DO_NOT_USE_5678"
    enabled: true
    nickname: "Demo Account"

  # Backup account - currently disabled
  - account_id: 345678
    username: "backup@example.com"
    api_key: "sk_live_EXAMPLE_KEY_NOT_REAL_DO_NOT_USE_9012"
    enabled: false
    nickname: "Backup Account (Disabled)"

  # Minimal configuration (uses defaults)
  - account_id: 567890
    username: "minimal@example.com"
    api_key: "sk_live_EXAMPLE_KEY_NOT_REAL_DO_NOT_USE_3456"
```

---

## ✅ Validation Rules

### **File-Level Validation**

1. **File must exist:** `config/accounts.yaml` must be present
2. **Valid YAML:** Must parse without syntax errors
3. **Top-level key:** Must have `accounts` key
4. **At least one account:** `accounts` array must not be empty

### **Account-Level Validation**

Each account must pass:

| Rule | Validation |
|------|------------|
| **account_id required** | Must be present and non-null |
| **account_id unique** | No duplicate account_ids in file |
| **account_id positive** | Must be > 0 |
| **username required** | Must be present and non-empty |
| **username format** | Must be valid email format |
| **api_key required** | Must be present and non-empty |
| **api_key format** | Must start with `sk_live_` or `sk_test_` |
| **enabled type** | If present, must be boolean |
| **nickname type** | If present, must be string |

### **Validation Errors**

If validation fails, daemon should:
1. Log detailed error message
2. Specify which account failed (by account_id if available)
3. Refuse to start daemon
4. Display validation error in Admin CLI

**Example Error:**
```
ERROR: Invalid accounts.yaml
  - Account 123456: Missing required field 'api_key'
  - Account 789012: Invalid account_id (must be positive integer)
  - Account 345678: Duplicate account_id (already exists)

Daemon cannot start with invalid configuration.
```

---

## 🔒 Security Best Practices

### **1. Never Commit API Keys**

Add to `.gitignore`:
```gitignore
# Never commit API keys
config/accounts.yaml
config/admin_password.hash
```

### **2. Use Environment Variables (Alternative)**

For production deployments, support environment variables:
```yaml
accounts:
  - account_id: 123456
    username: "trader@example.com"
    api_key: "${TOPSTEPX_API_KEY}"  # Read from environment
```

**Implementation:**
```python
import os

# Expand environment variables
if api_key.startswith('${') and api_key.endswith('}'):
    env_var = api_key[2:-1]
    api_key = os.environ.get(env_var)
    if not api_key:
        raise ValueError(f"Environment variable {env_var} not set")
```

### **3. Encrypt at Rest (Advanced)**

For highly sensitive environments:
```bash
# Encrypt file
gpg --encrypt --recipient your@email.com accounts.yaml

# Daemon decrypts on startup
gpg --decrypt accounts.yaml.gpg > /tmp/accounts.yaml
```

### **4. File Permissions**

Set restrictive permissions:
```bash
# Linux/Mac
chmod 600 config/accounts.yaml  # Owner read/write only

# Windows (via PowerShell)
icacls config\accounts.yaml /inheritance:r /grant:r "%USERNAME%:R"
```

---

## 🛠️ Configuration Loader Implementation

**Location:** `src/config/loader.py`

**Pseudocode:**
```python
import yaml

def load_accounts_config(file_path='config/accounts.yaml'):
    """
    Load and validate accounts configuration.

    Returns:
        List[AccountConfig]: Validated account configurations

    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If validation fails
    """
    # Read file
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)

    # Validate top-level structure
    if 'accounts' not in config:
        raise ValidationError("Missing 'accounts' key")

    if not isinstance(config['accounts'], list):
        raise ValidationError("'accounts' must be an array")

    if len(config['accounts']) == 0:
        raise ValidationError("Must have at least one account")

    # Validate each account
    accounts = []
    seen_ids = set()

    for i, account_data in enumerate(config['accounts']):
        # Validate required fields
        if 'account_id' not in account_data:
            raise ValidationError(f"Account {i}: Missing 'account_id'")

        account_id = account_data['account_id']

        # Check for duplicates
        if account_id in seen_ids:
            raise ValidationError(f"Duplicate account_id: {account_id}")
        seen_ids.add(account_id)

        # Validate account_id
        if not isinstance(account_id, int) or account_id <= 0:
            raise ValidationError(f"Account {account_id}: Invalid account_id")

        # Validate username
        if 'username' not in account_data:
            raise ValidationError(f"Account {account_id}: Missing 'username'")

        # Validate api_key
        if 'api_key' not in account_data:
            raise ValidationError(f"Account {account_id}: Missing 'api_key'")

        api_key = account_data['api_key']
        if not (api_key.startswith('sk_live_') or api_key.startswith('sk_test_')):
            raise ValidationError(f"Account {account_id}: Invalid api_key format")

        # Create AccountConfig object
        account = AccountConfig(
            account_id=account_id,
            username=account_data['username'],
            api_key=account_data['api_key'],
            enabled=account_data.get('enabled', True),
            nickname=account_data.get('nickname')
        )

        accounts.append(account)

    return accounts
```

---

## 🧪 Testing

### **Test 1: Valid Configuration**
```yaml
accounts:
  - account_id: 123
    username: "test@example.com"
    api_key: "sk_test_validkey"
    enabled: true
```

**Expected:** Loads successfully

---

### **Test 2: Missing Required Field**
```yaml
accounts:
  - account_id: 123
    username: "test@example.com"
    # Missing api_key
```

**Expected:** ValidationError: "Missing 'api_key'"

---

### **Test 3: Invalid account_id**
```yaml
accounts:
  - account_id: -1  # Negative
    username: "test@example.com"
    api_key: "sk_test_key"
```

**Expected:** ValidationError: "Invalid account_id"

---

### **Test 4: Duplicate account_id**
```yaml
accounts:
  - account_id: 123
    username: "test1@example.com"
    api_key: "sk_test_key1"
  - account_id: 123  # Duplicate!
    username: "test2@example.com"
    api_key: "sk_test_key2"
```

**Expected:** ValidationError: "Duplicate account_id: 123"

---

## 📝 Summary

**Configuration File:** `config/accounts.yaml`

**Required Fields per Account:**
- `account_id` (integer)
- `username` (string, email)
- `api_key` (string, starts with `sk_`)

**Optional Fields per Account:**
- `enabled` (boolean, default: true)
- `nickname` (string, default: null)

**Security:**
- Never commit file to git
- Use restrictive file permissions
- Consider environment variables or encryption

**Validation:**
- Daemon validates on startup
- Refuses to start if invalid
- Shows detailed error messages

---

**Related Files:**
- `src/config/loader.py` - Configuration loader implementation
- `src/data_models/account_config.py` - AccountConfig dataclass
- `07-DATA-MODELS/STATE_OBJECTS.md` - AccountConfig specification

---

**Status:** Complete and ready for implementation
