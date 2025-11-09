"""
Unit Tests for Token Encryption
Tests the secure token storage functionality
"""

import pytest
import os
from pathlib import Path
from cryptography.fernet import Fernet
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.encryption import SecureTokenStorage, EncryptionError


class TestSecureTokenStorage:
    """Test cases for SecureTokenStorage class"""

    @pytest.fixture
    def encryption_key(self):
        """Generate a test encryption key"""
        return Fernet.generate_key().decode()

    @pytest.fixture
    def storage(self, encryption_key):
        """Create a SecureTokenStorage instance"""
        return SecureTokenStorage(encryption_key=encryption_key)

    @pytest.fixture
    def temp_token_file(self, tmp_path):
        """Create a temporary token file path"""
        return tmp_path / ".test_token"

    def test_encryption_key_required(self):
        """Test that encryption key is required"""
        # Remove ENCRYPTION_KEY from environment
        old_key = os.environ.get('ENCRYPTION_KEY')
        if 'ENCRYPTION_KEY' in os.environ:
            del os.environ['ENCRYPTION_KEY']

        try:
            with pytest.raises(EncryptionError, match="ENCRYPTION_KEY not set"):
                SecureTokenStorage()
        finally:
            # Restore original key
            if old_key:
                os.environ['ENCRYPTION_KEY'] = old_key

    def test_encrypt_token_success(self, storage):
        """Test successful token encryption"""
        token = "test_access_token_12345"
        encrypted = storage.encrypt_token(token)

        assert isinstance(encrypted, bytes)
        assert encrypted != token.encode()  # Should be different from plaintext
        assert len(encrypted) > len(token)  # Encrypted data is longer

    def test_encrypt_empty_token_fails(self, storage):
        """Test that encrypting empty token raises error"""
        with pytest.raises(EncryptionError, match="Cannot encrypt empty token"):
            storage.encrypt_token("")

    def test_decrypt_token_success(self, storage):
        """Test successful token decryption"""
        original_token = "test_access_token_12345"
        encrypted = storage.encrypt_token(original_token)
        decrypted = storage.decrypt_token(encrypted)

        assert decrypted == original_token

    def test_decrypt_invalid_token_fails(self, storage):
        """Test that decrypting invalid token raises error"""
        invalid_token = b"not_a_valid_encrypted_token"

        with pytest.raises(EncryptionError, match="Invalid token or wrong encryption key"):
            storage.decrypt_token(invalid_token)

    def test_decrypt_empty_token_fails(self, storage):
        """Test that decrypting empty token raises error"""
        with pytest.raises(EncryptionError, match="Cannot decrypt empty token"):
            storage.decrypt_token(b"")

    def test_decrypt_with_wrong_key_fails(self, encryption_key):
        """Test that decrypting with wrong key fails"""
        storage1 = SecureTokenStorage(encryption_key=encryption_key)
        token = "test_token"
        encrypted = storage1.encrypt_token(token)

        # Create storage with different key
        wrong_key = Fernet.generate_key().decode()
        storage2 = SecureTokenStorage(encryption_key=wrong_key)

        with pytest.raises(EncryptionError, match="Invalid token or wrong encryption key"):
            storage2.decrypt_token(encrypted)

    def test_save_token_success(self, storage, temp_token_file):
        """Test successful token save"""
        token = "test_access_token"
        result = storage.save_token(token, temp_token_file)

        assert result is True
        assert temp_token_file.exists()
        assert temp_token_file.stat().st_size > 0

    def test_load_token_success(self, storage, temp_token_file):
        """Test successful token load"""
        original_token = "test_access_token_12345"
        storage.save_token(original_token, temp_token_file)

        loaded_token = storage.load_token(temp_token_file)

        assert loaded_token == original_token

    def test_load_nonexistent_token_returns_none(self, storage, tmp_path):
        """Test loading non-existent token file returns None"""
        nonexistent_file = tmp_path / "nonexistent_token"
        result = storage.load_token(nonexistent_file)

        assert result is None

    def test_file_permissions_are_secure(self, storage, temp_token_file):
        """Test that saved token file has secure permissions (Unix-like systems)"""
        if os.name == 'posix':  # Only test on Unix-like systems
            token = "test_token"
            storage.save_token(token, temp_token_file)

            # Get file permissions
            stat_info = temp_token_file.stat()
            permissions = oct(stat_info.st_mode)[-3:]

            # Should be 600 (rw-------)
            assert permissions == '600', f"Expected 600, got {permissions}"

    def test_delete_token_success(self, storage, temp_token_file):
        """Test successful token deletion"""
        token = "test_token"
        storage.save_token(token, temp_token_file)

        assert temp_token_file.exists()

        result = storage.delete_token(temp_token_file)

        assert result is True
        assert not temp_token_file.exists()

    def test_delete_nonexistent_token_fails(self, storage, tmp_path):
        """Test deleting non-existent token returns False"""
        nonexistent_file = tmp_path / "nonexistent_token"
        result = storage.delete_token(nonexistent_file)

        assert result is False

    def test_round_trip_encryption(self, storage):
        """Test complete encrypt-decrypt round trip"""
        test_tokens = [
            "simple_token",
            "token_with_special_chars!@#$%",
            "long_token_" * 100,  # Long token
            "token.with.dots",
            "token-with-dashes",
        ]

        for original_token in test_tokens:
            encrypted = storage.encrypt_token(original_token)
            decrypted = storage.decrypt_token(encrypted)
            assert decrypted == original_token, f"Round trip failed for: {original_token}"

    def test_same_token_different_ciphertext(self, storage):
        """Test that encrypting same token produces different ciphertext (IV randomization)"""
        token = "test_token"
        encrypted1 = storage.encrypt_token(token)
        encrypted2 = storage.encrypt_token(token)

        # Ciphertexts should be different due to IV randomization
        # But both should decrypt to same plaintext
        assert encrypted1 != encrypted2
        assert storage.decrypt_token(encrypted1) == token
        assert storage.decrypt_token(encrypted2) == token


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
