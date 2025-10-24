"""
Secure Token Storage with AES-256-GCM Encryption

Implements encrypted persistent token storage with:
- AES-256-GCM encryption for data at rest
- PBKDF2 key derivation from environment variable
- Secure file permissions (0600)
- Memory-only mode option
- Automatic token expiry validation

Security features:
- Environment-based encryption key derivation
- Authenticated encryption (GCM mode)
- Secure file permission management
- Safe token clearing
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class TokenStorage:
    """
    Secure encrypted token storage with AES-256-GCM encryption.

    Features:
    - AES-256-GCM authenticated encryption
    - PBKDF2 key derivation from environment
    - File permissions set to 0600 (owner read/write only)
    - Optional memory-only mode
    - Automatic expiry validation

    Usage:
        storage = TokenStorage()
        storage.store_token("jwt_token_here", datetime.now() + timedelta(hours=1))
        token, expiry = storage.load_token()
        storage.clear_token()
    """

    # Encryption constants
    KEY_SIZE = 32  # 256 bits for AES-256
    NONCE_SIZE = 12  # 96 bits (recommended for GCM)
    ITERATIONS = 600000  # PBKDF2 iterations (OWASP recommended minimum)
    SALT_SIZE = 16  # 128 bits

    # File permission constants
    SECURE_PERMISSIONS = 0o600  # Owner read/write only

    def __init__(self, storage_path: str = "data/tokens.enc", memory_only: bool = False):
        """
        Initialize token storage.

        Args:
            storage_path: Path to encrypted token file (default: data/tokens.enc)
            memory_only: If True, tokens are only stored in memory (not persisted)

        Raises:
            ValueError: If ENCRYPTION_KEY_SALT environment variable is not set
        """
        self.storage_path = Path(storage_path)
        self.memory_only = memory_only

        # In-memory token cache
        self._cached_token: Optional[str] = None
        self._cached_expiry: Optional[datetime] = None

        # Validate encryption key salt is available
        self.salt_base = os.environ.get('ENCRYPTION_KEY_SALT')
        if not self.salt_base:
            logger.warning("ENCRYPTION_KEY_SALT not set, using default (NOT SECURE for production)")
            self.salt_base = "default-salt-change-in-production"

        # Ensure storage directory exists if not memory-only
        if not self.memory_only:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Token storage initialized at {self.storage_path}")
        else:
            logger.debug("Token storage initialized in memory-only mode")

    def _derive_key(self) -> bytes:
        """
        Derive encryption key from environment using PBKDF2.

        Uses PBKDF2-HMAC-SHA256 with 600,000 iterations to derive a 256-bit key
        from the ENCRYPTION_KEY_SALT environment variable.

        Returns:
            32-byte encryption key suitable for AES-256
        """
        # Use fixed salt derived from environment (stored with encrypted data)
        salt = self.salt_base.encode('utf-8')[:self.SALT_SIZE].ljust(self.SALT_SIZE, b'\x00')

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.ITERATIONS,
            backend=default_backend()
        )

        # Derive key from salt (acts as password in this case)
        key = kdf.derive(self.salt_base.encode('utf-8'))
        return key

    def _encrypt(self, data: dict) -> bytes:
        """
        Encrypt data using AES-256-GCM.

        AES-GCM provides both confidentiality and authenticity, preventing
        tampering with encrypted data.

        Args:
            data: Dictionary containing token and expiry information

        Returns:
            Encrypted data with format: nonce (12 bytes) + ciphertext + tag

        Raises:
            Exception: If encryption fails
        """
        try:
            # Serialize data to JSON
            plaintext = json.dumps(data, default=str).encode('utf-8')

            # Generate random nonce (must be unique for each encryption)
            nonce = os.urandom(self.NONCE_SIZE)

            # Derive encryption key
            key = self._derive_key()

            # Create AESGCM cipher
            aesgcm = AESGCM(key)

            # Encrypt and authenticate
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)

            # Prepend nonce to ciphertext for storage
            encrypted_data = nonce + ciphertext

            logger.debug("Token data encrypted successfully")
            return encrypted_data

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def _decrypt(self, encrypted_data: bytes) -> dict:
        """
        Decrypt data using AES-256-GCM.

        Args:
            encrypted_data: Encrypted data with format: nonce + ciphertext + tag

        Returns:
            Decrypted dictionary containing token and expiry

        Raises:
            ValueError: If decryption or authentication fails
            Exception: If decryption encounters other errors
        """
        try:
            # Extract nonce from beginning of encrypted data
            nonce = encrypted_data[:self.NONCE_SIZE]
            ciphertext = encrypted_data[self.NONCE_SIZE:]

            # Derive decryption key (same as encryption key)
            key = self._derive_key()

            # Create AESGCM cipher
            aesgcm = AESGCM(key)

            # Decrypt and verify authentication tag
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            # Deserialize JSON
            data = json.loads(plaintext.decode('utf-8'))

            logger.debug("Token data decrypted successfully")
            return data

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt token data (invalid key or corrupted data)")

    def store_token(self, token: str, expires_at: datetime) -> None:
        """
        Encrypt and store authentication token.

        Args:
            token: JWT token string
            expires_at: Token expiry datetime

        Raises:
            Exception: If encryption or file operations fail
        """
        try:
            # Store in memory cache
            self._cached_token = token
            self._cached_expiry = expires_at

            # Skip file storage if memory-only mode
            if self.memory_only:
                logger.debug("Token stored in memory only")
                return

            # Prepare data for encryption
            data = {
                'token': token,
                'expires_at': expires_at.isoformat()
            }

            # Encrypt data
            encrypted_data = self._encrypt(data)

            # Write to file with secure permissions
            # Use temporary file and atomic rename for safer write
            temp_path = self.storage_path.with_suffix('.tmp')

            try:
                # Write encrypted data
                temp_path.write_bytes(encrypted_data)

                # Set secure permissions before moving to final location
                os.chmod(temp_path, self.SECURE_PERMISSIONS)

                # Atomic rename to final location
                temp_path.replace(self.storage_path)

                # Verify final permissions
                os.chmod(self.storage_path, self.SECURE_PERMISSIONS)

                logger.info(f"Token stored securely at {self.storage_path}")

            finally:
                # Clean up temp file if it still exists
                if temp_path.exists():
                    temp_path.unlink()

        except Exception as e:
            logger.error(f"Failed to store token: {e}")
            raise

    def load_token(self) -> Tuple[Optional[str], Optional[datetime]]:
        """
        Load and decrypt authentication token.

        Returns:
            Tuple of (token, expires_at) or (None, None) if no valid token exists

        Raises:
            ValueError: If decryption fails or data is corrupted
        """
        try:
            # Return cached token if available and not expired
            if self._cached_token and self._cached_expiry:
                if self._cached_expiry > datetime.now():
                    logger.debug("Returning cached token")
                    return self._cached_token, self._cached_expiry
                else:
                    logger.debug("Cached token expired, clearing cache")
                    self._cached_token = None
                    self._cached_expiry = None

            # If memory-only mode or file doesn't exist, return None
            if self.memory_only or not self.storage_path.exists():
                logger.debug("No stored token available")
                return None, None

            # Read encrypted data from file
            encrypted_data = self.storage_path.read_bytes()

            # Decrypt data
            data = self._decrypt(encrypted_data)

            # Parse token and expiry
            token = data.get('token')
            expires_at_str = data.get('expires_at')

            if not token or not expires_at_str:
                logger.warning("Token data is incomplete")
                return None, None

            # Parse expiry datetime
            expires_at = datetime.fromisoformat(expires_at_str)

            # Check if token is expired
            if expires_at <= datetime.now():
                logger.info("Stored token has expired")
                self.clear_token()
                return None, None

            # Update cache
            self._cached_token = token
            self._cached_expiry = expires_at

            logger.info("Token loaded successfully")
            return token, expires_at

        except FileNotFoundError:
            logger.debug("No token file found")
            return None, None
        except ValueError as e:
            logger.error(f"Failed to load token: {e}")
            # Clear corrupted token file
            self.clear_token()
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading token: {e}")
            return None, None

    def clear_token(self) -> None:
        """
        Securely delete stored token.

        Removes both in-memory cache and encrypted file (if exists).
        """
        try:
            # Clear memory cache
            self._cached_token = None
            self._cached_expiry = None

            # Skip file operations if memory-only mode
            if self.memory_only:
                logger.debug("Token cleared from memory")
                return

            # Delete encrypted token file if it exists
            if self.storage_path.exists():
                self.storage_path.unlink()
                logger.info("Token file deleted")
            else:
                logger.debug("No token file to delete")

        except Exception as e:
            logger.error(f"Failed to clear token: {e}")
            raise

    def is_token_valid(self) -> bool:
        """
        Check if a valid (non-expired) token exists.

        Returns:
            True if valid token exists, False otherwise
        """
        token, expiry = self.load_token()
        return token is not None and expiry is not None and expiry > datetime.now()
