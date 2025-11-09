"""
Encryption Utilities
Provides secure encryption/decryption for sensitive data like access tokens
"""

import os
import logging
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger('encryption')


class EncryptionError(Exception):
    """Raised when encryption/decryption fails"""
    pass


class SecureTokenStorage:
    """Securely store and retrieve access tokens with encryption"""

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize secure token storage

        Args:
            encryption_key: Base64-encoded Fernet key. If None, loads from environment.

        Raises:
            EncryptionError: If no encryption key provided and ENCRYPTION_KEY not set
        """
        self.encryption_key = encryption_key or os.getenv('ENCRYPTION_KEY')

        if not self.encryption_key:
            logger.error("No encryption key provided!")
            logger.error("Generate one with:")
            logger.error("  python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
            logger.error("Then add to config/secrets.env:")
            logger.error("  ENCRYPTION_KEY=<generated_key>")
            raise EncryptionError("ENCRYPTION_KEY not set. Cannot encrypt tokens.")

        try:
            self.fernet = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)
        except Exception as e:
            raise EncryptionError(f"Invalid encryption key: {e}")

    def encrypt_token(self, token: str) -> bytes:
        """
        Encrypt an access token

        Args:
            token: Plain text token to encrypt

        Returns:
            Encrypted token bytes

        Raises:
            EncryptionError: If encryption fails
        """
        if not token:
            raise EncryptionError("Cannot encrypt empty token")

        try:
            encrypted = self.fernet.encrypt(token.encode())
            logger.debug("Token encrypted successfully")
            return encrypted
        except Exception as e:
            logger.error(f"Token encryption failed: {e}")
            raise EncryptionError(f"Encryption failed: {e}")

    def decrypt_token(self, encrypted_token: bytes) -> str:
        """
        Decrypt an access token

        Args:
            encrypted_token: Encrypted token bytes

        Returns:
            Decrypted plain text token

        Raises:
            EncryptionError: If decryption fails (invalid key or corrupted data)
        """
        if not encrypted_token:
            raise EncryptionError("Cannot decrypt empty token")

        try:
            decrypted = self.fernet.decrypt(encrypted_token).decode()
            logger.debug("Token decrypted successfully")
            return decrypted
        except InvalidToken:
            logger.error("Token decryption failed: Invalid token or wrong encryption key")
            raise EncryptionError("Invalid token or wrong encryption key")
        except Exception as e:
            logger.error(f"Token decryption failed: {e}")
            raise EncryptionError(f"Decryption failed: {e}")

    def save_token(self, token: str, file_path: Path) -> bool:
        """
        Encrypt and save token to file

        Args:
            token: Plain text token
            file_path: Path to save encrypted token

        Returns:
            True if successful, False otherwise
        """
        try:
            encrypted = self.encrypt_token(token)

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save encrypted token
            with open(file_path, 'wb') as f:
                f.write(encrypted)

            # Secure file permissions (read/write for owner only)
            os.chmod(file_path, 0o600)

            logger.info(f"Token saved securely to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save token: {e}")
            return False

    def load_token(self, file_path: Path) -> Optional[str]:
        """
        Load and decrypt token from file

        Args:
            file_path: Path to encrypted token file

        Returns:
            Decrypted token, or None if file doesn't exist or decryption fails
        """
        if not file_path.exists():
            logger.warning(f"Token file not found: {file_path}")
            return None

        try:
            with open(file_path, 'rb') as f:
                encrypted = f.read()

            token = self.decrypt_token(encrypted)
            logger.info(f"Token loaded from {file_path}")
            return token

        except EncryptionError as e:
            logger.error(f"Failed to load token: {e}")
            logger.error("You may need to re-authenticate to generate a new token")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading token: {e}")
            return None

    def delete_token(self, file_path: Path) -> bool:
        """
        Securely delete token file

        Args:
            file_path: Path to token file

        Returns:
            True if deleted, False otherwise
        """
        if not file_path.exists():
            logger.warning(f"Token file not found: {file_path}")
            return False

        try:
            # Overwrite file with random data before deletion (secure deletion)
            file_size = file_path.stat().st_size
            with open(file_path, 'wb') as f:
                f.write(os.urandom(file_size))

            # Delete file
            file_path.unlink()

            logger.info(f"Token file securely deleted: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete token file: {e}")
            return False


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key

    Returns:
        Base64-encoded encryption key
    """
    key = Fernet.generate_key().decode()
    print(f"Generated encryption key:\n{key}")
    print("\nAdd this to config/secrets.env:")
    print(f"ENCRYPTION_KEY={key}")
    return key


if __name__ == '__main__':
    # Generate encryption key for testing
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'generate-key':
        generate_encryption_key()
    else:
        print("Usage:")
        print("  python encryption.py generate-key  # Generate new encryption key")
