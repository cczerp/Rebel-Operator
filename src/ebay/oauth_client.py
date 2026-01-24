"""
eBay OAuth 2.0 Client
=====================
Handles eBay OAuth authentication flow for Inventory API access.

Supports both sandbox and production environments.
"""

import os
import requests
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from urllib.parse import urlencode


class eBayOAuthClient:
    """Handles eBay OAuth 2.0 authorization flow"""

    # OAuth endpoints
    SANDBOX_AUTH_URL = "https://auth.sandbox.ebay.com/oauth2/authorize"
    PRODUCTION_AUTH_URL = "https://auth.ebay.com/oauth2/authorize"

    SANDBOX_TOKEN_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
    PRODUCTION_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"

    # Required scopes for Inventory API
    REQUIRED_SCOPES = [
        "https://api.ebay.com/oauth/api_scope",
        "https://api.ebay.com/oauth/api_scope/sell.inventory",
        "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly"
    ]

    def __init__(self, environment: str = 'sandbox'):
        """
        Initialize eBay OAuth client.

        Args:
            environment: 'sandbox' or 'production'

        Raises:
            ValueError: If environment is invalid or credentials missing
        """
        if environment not in ['sandbox', 'production']:
            raise ValueError("environment must be 'sandbox' or 'production'")

        self.environment = environment

        # Load credentials from environment variables
        if environment == 'sandbox':
            self.app_id = os.getenv('EBAY_SANDBOX_APP_ID')
            self.cert_id = os.getenv('EBAY_SANDBOX_CERT_ID')
            self.ru_name = os.getenv('EBAY_SANDBOX_RUNAME')
            self.auth_url = self.SANDBOX_AUTH_URL
            self.token_url = self.SANDBOX_TOKEN_URL
        else:  # production
            self.app_id = os.getenv('EBAY_PROD_APP_ID')
            self.cert_id = os.getenv('EBAY_PROD_CERT_ID')
            self.ru_name = os.getenv('EBAY_PROD_RUNAME')
            self.auth_url = self.PRODUCTION_AUTH_URL
            self.token_url = self.PRODUCTION_TOKEN_URL

        self.redirect_uri = os.getenv('EBAY_REDIRECT_URI', 'https://www.rebeloperator.com/ebay/callback')

        # Validate credentials
        if not self.app_id:
            raise ValueError(f"Missing EBAY_{environment.upper()}_APP_ID environment variable")
        if not self.cert_id:
            raise ValueError(f"Missing EBAY_{environment.upper()}_CERT_ID environment variable")
        if not self.ru_name:
            raise ValueError(f"Missing EBAY_{environment.upper()}_RUNAME environment variable")

    def get_authorization_url(self, state: str = None) -> str:
        """
        Generate eBay authorization URL for user consent.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            str: Full authorization URL to redirect user to
        """
        params = {
            'client_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.REQUIRED_SCOPES)
        }

        if state:
            params['state'] = state

        # For sandbox, we need to add the RuName
        if self.environment == 'sandbox':
            params['runame'] = self.ru_name

        return f"{self.auth_url}?{urlencode(params)}"

    def exchange_code_for_tokens(self, authorization_code: str) -> Dict:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            authorization_code: The code from OAuth callback

        Returns:
            dict: Token response containing:
                - access_token: OAuth access token
                - refresh_token: OAuth refresh token
                - expires_in: Seconds until access token expires
                - token_type: Usually 'Bearer'

        Raises:
            Exception: If token exchange fails
        """
        # Create Basic Auth header (app_id:cert_id)
        credentials = f"{self.app_id}:{self.cert_id}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {encoded_credentials}'
        }

        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri
        }

        try:
            response = requests.post(
                self.token_url,
                headers=headers,
                data=data,
                timeout=30
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"eBay token exchange error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise Exception(f"Failed to exchange authorization code: {str(e)}")

    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh an expired access token using refresh token.

        Args:
            refresh_token: The refresh token from previous authorization

        Returns:
            dict: Token response containing new access_token and expires_in

        Raises:
            Exception: If token refresh fails
        """
        # Create Basic Auth header
        credentials = f"{self.app_id}:{self.cert_id}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {encoded_credentials}'
        }

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'scope': ' '.join(self.REQUIRED_SCOPES)
        }

        try:
            response = requests.post(
                self.token_url,
                headers=headers,
                data=data,
                timeout=30
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"eBay token refresh error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise Exception(f"Failed to refresh access token: {str(e)}")

    def get_user_info(self, access_token: str) -> Dict:
        """
        Get eBay user information using access token.

        Args:
            access_token: Valid OAuth access token

        Returns:
            dict: User information from eBay

        Raises:
            Exception: If API call fails
        """
        # Use eBay Account API to get user info
        if self.environment == 'sandbox':
            api_url = "https://apiz.sandbox.ebay.com/commerce/identity/v1/user/"
        else:
            api_url = "https://apiz.ebay.com/commerce/identity/v1/user/"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"eBay user info error: {e}")
            # Not critical if this fails, return minimal info
            return {'username': 'Unknown'}

    def calculate_expiry_time(self, expires_in_seconds: int) -> datetime:
        """
        Calculate token expiry timestamp.

        Args:
            expires_in_seconds: Seconds until token expires (from eBay response)

        Returns:
            datetime: Expiry timestamp (UTC)
        """
        # Subtract 5 minutes as buffer to refresh before actual expiry
        buffer_seconds = 300
        return datetime.utcnow() + timedelta(seconds=expires_in_seconds - buffer_seconds)


def get_ebay_oauth_client(environment: str = None) -> eBayOAuthClient:
    """
    Get eBay OAuth client for specified environment.

    Args:
        environment: 'sandbox' or 'production'. If None, uses EBAY_ENV env var.

    Returns:
        eBayOAuthClient: Configured OAuth client
    """
    if environment is None:
        environment = os.getenv('EBAY_ENV', 'sandbox')

    return eBayOAuthClient(environment=environment)
