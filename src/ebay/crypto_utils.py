"""
Token Encryption/Decryption Utilities
======================================
Provides secure encryption for storing OAuth tokens in the database.

Uses Fernet (symmetric encryption) from the cryptography library.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class TokenEncryption:
    """Handles encryption/decryption of OAuth tokens"""

    def __init__(self):
        """Initialize encryption with key from environment"""
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key)

    def _get_encryption_key(self) -> bytes:
        """
        Get or generate encryption key from environment.

        Returns:
            bytes: Fernet encryption key

        Raises:
            ValueError: If SECRET_KEY not set in environment
        """
        # Use Flask SECRET_KEY as base for encryption key
        # Check both common env var names
        secret_key = os.getenv('SECRET_KEY') or os.getenv('FLASK_SECRET_KEY')

        if not secret_key:
            raise ValueError(
                "SECRET_KEY environment variable is required for token encryption. "
                "Set it to a random string (min 32 characters): "
                "export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')"
            )

        # Derive a proper Fernet key from SECRET_KEY using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'rebel_operator_ebay_tokens',  # Static salt for consistency
            iterations=100000,
            backend=default_backend()
        )

        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        return key

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt (e.g., access token)

        Returns:
            str: Base64-encoded encrypted string
        """
        if not plaintext:
            return ''

        encrypted = self.fernet.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            ciphertext: The encrypted string from database

        Returns:
            str: Decrypted plaintext string

        Raises:
            Exception: If decryption fails (invalid key or corrupted data)
        """
        if not ciphertext:
            return ''

        decrypted = self.fernet.decrypt(ciphertext.encode())
        return decrypted.decode()

    def encrypt_token_pair(self, access_token: str, refresh_token: str) -> tuple:
        """
        Encrypt both access and refresh tokens.

        Args:
            access_token: eBay access token
            refresh_token: eBay refresh token

        Returns:
            tuple: (encrypted_access, encrypted_refresh)
        """
        return (
            self.encrypt(access_token),
            self.encrypt(refresh_token)
        )

    def decrypt_token_pair(self, encrypted_access: str, encrypted_refresh: str) -> tuple:
        """
        Decrypt both access and refresh tokens.

        Args:
            encrypted_access: Encrypted access token from DB
            encrypted_refresh: Encrypted refresh token from DB

        Returns:
            tuple: (access_token, refresh_token)
        """
        return (
            self.decrypt(encrypted_access),
            self.decrypt(encrypted_refresh)
        )


# Global instance for easy access
_token_crypto = None

def get_token_crypto() -> TokenEncryption:
    """Get singleton instance of TokenEncryption"""
    global _token_crypto
    if _token_crypto is None:
        _token_crypto = TokenEncryption()
    return _token_crypto


# Convenience functions
def encrypt_token(token: str) -> str:
    """Encrypt a single token"""
    return get_token_crypto().encrypt(token)


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a single token"""
    return get_token_crypto().decrypt(encrypted_token)
