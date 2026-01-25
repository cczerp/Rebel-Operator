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
import base64

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


def _get_ebay_b64_credentials():
    """
    Get base64-encoded eBay credentials for API authentication.

    Tries multiple sources in order:
    1. EBAY_PROD_B64 (uppercase)
    2. EBAY_PROD_b64 (lowercase - common user error)
    3. Auto-generate from EBAY_PROD_APP_ID and EBAY_PROD_CERT_ID

    Returns:
        str: Base64-encoded credentials string

    Raises:
        ValueError: If no credentials can be obtained
    """
    # Try uppercase first (documented standard)
    auth_b64 = os.environ.get("EBAY_PROD_B64")

    # Try lowercase (common user error)
    if not auth_b64:
        auth_b64 = os.environ.get("EBAY_PROD_b64")
        if auth_b64:
            print("[eBay Auth] Note: Using EBAY_PROD_b64 (lowercase). Consider renaming to EBAY_PROD_B64.")

    # Auto-generate from APP_ID and CERT_ID if B64 not provided
    if not auth_b64:
        app_id = os.environ.get("EBAY_PROD_APP_ID")
        cert_id = os.environ.get("EBAY_PROD_CERT_ID")

        if app_id and cert_id:
            credentials = f"{app_id}:{cert_id}"
            auth_b64 = base64.b64encode(credentials.encode()).decode()
            print("[eBay Auth] Auto-generated B64 credentials from EBAY_PROD_APP_ID and EBAY_PROD_CERT_ID")
        else:
            raise ValueError(
                "eBay credentials not found. Set either:\n"
                "  - EBAY_PROD_B64 (base64 of APP_ID:CERT_ID), or\n"
                "  - Both EBAY_PROD_APP_ID and EBAY_PROD_CERT_ID"
            )

    return auth_b64


def get_ebay_token():
    """
    Get a valid eBay access token, caching it until expiry.

    Returns cached token if still valid, otherwise requests a new one.

    Returns:
        str: Valid eBay access token

    Raises:
        ValueError: If eBay credentials are not configured
        requests.RequestException: If token request fails after retries
    """
    global EBAY_TOKEN, EBAY_TOKEN_EXPIRES

    # Return cached token if still valid (with 60 second buffer)
    if EBAY_TOKEN and time.time() < EBAY_TOKEN_EXPIRES:
        return EBAY_TOKEN

    # Get base64 encoded app credentials
    auth_b64 = _get_ebay_b64_credentials()

    # Request new token using session with retries
    session = _get_ebay_session()

    print("[eBay Auth] Requesting new access token...")

    try:
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

        if resp.status_code != 200:
            print(f"[eBay Auth] Token request failed with status {resp.status_code}")
            print(f"[eBay Auth] Response: {resp.text[:500]}")
            resp.raise_for_status()

        data = resp.json()

        # Cache token with expiry (subtract 60 seconds for safety buffer)
        EBAY_TOKEN = data["access_token"]
        EBAY_TOKEN_EXPIRES = time.time() + data["expires_in"] - 60

        print(f"[eBay Auth] Token obtained successfully, expires in {data['expires_in']} seconds")

        return EBAY_TOKEN

    except requests.RequestException as e:
        print(f"[eBay Auth] Token request error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[eBay Auth] Response body: {e.response.text[:500]}")
        raise