"""
Zerodha Kite Connect Authentication
Handles OAuth2 login flow and secure token management
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from kiteconnect import KiteConnect
from ..utils.encryption import SecureTokenStorage, EncryptionError


class ZerodhaAuth:
    """Handles authentication with Zerodha Kite Connect API"""

    def __init__(self, api_key: str, api_secret: str, redirect_url: str = None):
        """
        Initialize Zerodha authentication

        Args:
            api_key: Kite Connect API key
            api_secret: Kite Connect API secret
            redirect_url: OAuth redirect URL
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_url = redirect_url or "http://localhost:8080/callback"

        self.kite = KiteConnect(api_key=self.api_key)
        self.access_token = None
        self.logger = logging.getLogger('auth')

        # Initialize secure token storage
        try:
            self.token_storage = SecureTokenStorage()
            self.use_encryption = True
            self.logger.info("Secure token storage enabled")
        except EncryptionError as e:
            self.logger.warning(f"Encryption not available: {e}")
            self.logger.warning("Tokens will be stored in PLAIN TEXT (INSECURE)")
            self.token_storage = None
            self.use_encryption = False

    def get_login_url(self) -> str:
        """
        Get Kite Connect login URL

        Returns:
            Login URL for manual authentication
        """
        login_url = self.kite.login_url()
        self.logger.info(f"Login URL generated: {login_url}")
        return login_url

    def generate_session(self, request_token: str) -> Dict[str, Any]:
        """
        Generate access token from request token

        Args:
            request_token: Request token from OAuth callback

        Returns:
            Session data with access token
        """
        try:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)

            # Save token to file for future use
            self._save_access_token(self.access_token)

            self.logger.info("Access token generated successfully")
            return data

        except Exception as e:
            self.logger.error(f"Failed to generate session: {e}")
            raise

    def set_access_token(self, access_token: str):
        """
        Set access token directly (for reuse)

        Args:
            access_token: Previously generated access token
        """
        self.access_token = access_token
        self.kite.set_access_token(access_token)
        self.logger.info("Access token set successfully")

    def load_access_token(self) -> bool:
        """
        Load access token securely from file

        Returns:
            True if token loaded successfully, False otherwise
        """
        token_file = Path("config/.access_token")

        if not token_file.exists():
            self.logger.debug("Token file not found")
            return False

        try:
            if self.use_encryption and self.token_storage:
                # Load encrypted token
                token = self.token_storage.load_token(token_file)
                if token:
                    self.set_access_token(token)
                    self.logger.info("Access token loaded and decrypted successfully")
                    return True
                else:
                    self.logger.error("Failed to decrypt token")
                    return False
            else:
                # Fallback: read plain text
                with open(token_file, 'r') as f:
                    token = f.read().strip()

                if token:
                    self.set_access_token(token)
                    self.logger.info("Access token loaded from file (plain text)")
                    return True
        except Exception as e:
            self.logger.error(f"Failed to load access token: {e}")

        return False

    def _save_access_token(self, token: str):
        """Save access token securely to file"""
        token_file = Path("config/.access_token")

        try:
            if self.use_encryption and self.token_storage:
                # Save encrypted token
                success = self.token_storage.save_token(token, token_file)
                if success:
                    self.logger.info("Access token saved securely (encrypted)")
                else:
                    self.logger.error("Failed to save encrypted token")
            else:
                # Fallback: plain text (INSECURE)
                token_file.parent.mkdir(parents=True, exist_ok=True)
                with open(token_file, 'w') as f:
                    f.write(token)
                os.chmod(token_file, 0o600)  # At least restrict permissions
                self.logger.warning("Access token saved in PLAIN TEXT (insecure)")
                self.logger.warning("Set ENCRYPTION_KEY in secrets.env for secure storage")
        except Exception as e:
            self.logger.error(f"Failed to save access token: {e}")

    def verify_token(self) -> bool:
        """
        Verify if access token is valid

        Returns:
            True if token is valid, False otherwise
        """
        try:
            profile = self.kite.profile()
            self.logger.info(f"Token verified. User: {profile['user_name']}")
            return True
        except Exception as e:
            self.logger.error(f"Token verification failed: {e}")
            return False

    def get_kite_instance(self) -> KiteConnect:
        """
        Get authenticated KiteConnect instance

        Returns:
            KiteConnect instance
        """
        if not self.access_token:
            raise ValueError("Not authenticated. Please login first.")

        return self.kite

    def interactive_login(self) -> KiteConnect:
        """
        Interactive login flow for development

        Returns:
            Authenticated KiteConnect instance
        """
        # Try to load existing token
        if self.load_access_token():
            if self.verify_token():
                self.logger.info("Using existing access token")
                return self.kite

        # Generate new token
        print("\n" + "="*60)
        print("ZERODHA KITE CONNECT AUTHENTICATION")
        print("="*60)
        print(f"\n1. Open this URL in your browser:")
        print(f"\n   {self.get_login_url()}\n")
        print("2. Login with your Zerodha credentials")
        print("3. After login, you'll be redirected to a URL")
        print("4. Copy the 'request_token' parameter from that URL")
        print("\n" + "="*60 + "\n")

        request_token = input("Enter request token: ").strip()

        if not request_token:
            raise ValueError("Request token is required")

        # Generate session
        self.generate_session(request_token)

        print("\n✅ Authentication successful!")
        print("="*60 + "\n")

        return self.kite


def authenticate(api_key: str, api_secret: str, access_token: str = None) -> KiteConnect:
    """
    Helper function for quick authentication

    Args:
        api_key: Kite Connect API key
        api_secret: Kite Connect API secret
        access_token: Optional access token (for reuse)

    Returns:
        Authenticated KiteConnect instance
    """
    auth = ZerodhaAuth(api_key, api_secret)

    # Use existing token if provided
    if access_token:
        auth.set_access_token(access_token)
        if auth.verify_token():
            return auth.get_kite_instance()

    # Try interactive login
    return auth.interactive_login()
