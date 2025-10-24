#!/usr/bin/env python3
"""
Create Admin Password Hash
Generates a secure password hash for Admin CLI authentication.

Usage:
    python scripts/create_admin_password.py
    python scripts/create_admin_password.py --password "YourPassword123"
"""

import argparse
import bcrypt
import getpass
import sys
from pathlib import Path


def create_password_hash(password: str) -> str:
    """
    Create bcrypt hash of password.

    Args:
        password: Plain text password

    Returns:
        Bcrypt hash string
    """
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

    return password_hash.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify password against hash.

    Args:
        password: Plain text password
        password_hash: Bcrypt hash

    Returns:
        True if password matches hash
    """
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create admin password hash for Simple Risk Manager'
    )
    parser.add_argument(
        '--password',
        type=str,
        help='Admin password (will prompt if not provided)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output file path (default: config/admin_password.hash)'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify existing password hash'
    )

    args = parser.parse_args()

    # Determine output path
    project_root = Path(__file__).parent.parent
    output_path = args.output or (project_root / 'config' / 'admin_password.hash')

    if args.verify:
        # Verify mode
        if not output_path.exists():
            print(f"❌ Password hash file not found: {output_path}")
            sys.exit(1)

        # Read existing hash
        with open(output_path, 'r') as f:
            stored_hash = f.read().strip()

        # Get password to verify
        password = getpass.getpass("Enter password to verify: ")

        if verify_password(password, stored_hash):
            print("✅ Password verified successfully!")
            sys.exit(0)
        else:
            print("❌ Password does not match!")
            sys.exit(1)

    # Create mode
    if args.password:
        password = args.password
    else:
        # Prompt for password (secure)
        password = getpass.getpass("Enter admin password: ")
        password_confirm = getpass.getpass("Confirm admin password: ")

        if password != password_confirm:
            print("❌ Passwords do not match!")
            sys.exit(1)

    # Validate password strength
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long!")
        sys.exit(1)

    # Create hash
    print("Creating password hash...")
    password_hash = create_password_hash(password)

    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(password_hash)

    # Set restrictive permissions (Unix only)
    try:
        output_path.chmod(0o600)  # Owner read/write only
    except Exception:
        pass  # Windows doesn't support chmod

    print(f"✅ Password hash saved to: {output_path}")
    print(f"📝 Hash: {password_hash}")

    # Verify
    if verify_password(password, password_hash):
        print("✅ Password hash verified successfully!")
    else:
        print("⚠️  Warning: Password verification failed!")

    print("\n⚠️  IMPORTANT: Keep this password secure!")
    print("⚠️  The admin password grants full access to the risk manager.")


if __name__ == '__main__':
    main()
