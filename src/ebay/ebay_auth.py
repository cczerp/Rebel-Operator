"""
eBay Authentication Module
==========================
Handles eBay OAuth2 token management for server-side API access.

Provides cached token storage with automatic refresh and retry logic.
"""

import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

EBAY_TOKEN = None
EBAY_TOKEN_EXPIRES = 0

# Create session with retry strategy
_ebay_session = None

def _get_ebay_session():
    """Get or create eBay API session with retry configuration."""
    global _ebay_session
    if _ebay_session is None:
        _ebay_session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]  # Only retry POST for token requests
        )
        adapter = HTTPAdapter(max_retries=retry)
        _ebay_session.mount("https://", adapter)
    return _ebay_session


def get_ebay_token():
    """
    Get a valid eBay access token, caching it until expiry.

    Returns cached token if still valid, otherwise requests a new one.

    Returns:
        str: Valid eBay access token

    Raises:
        ValueError: If EBAY_PROD_B64 environment variable is not set
        requests.RequestException: If token request fails after retries
    """
    global EBAY_TOKEN, EBAY_TOKEN_EXPIRES

    # Return cached token if still valid (with 60 second buffer)
    if EBAY_TOKEN and time.time() < EBAY_TOKEN_EXPIRES:
        return EBAY_TOKEN

    # Get base64 encoded app credentials from environment
    auth_b64 = os.environ.get("EBAY_PROD_B64")
    if not auth_b64:
        raise ValueError("EBAY_PROD_B64 environment variable not set")

    # Request new token using session with retries
    session = _get_ebay_session()
    resp = session.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers={
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        },
        timeout=10
    )

    resp.raise_for_status()
    data = resp.json()

    # Cache token with expiry (subtract 60 seconds for safety buffer)
    EBAY_TOKEN = data["access_token"]
    EBAY_TOKEN_EXPIRES = time.time() + data["expires_in"] - 60

    return EBAY_TOKEN