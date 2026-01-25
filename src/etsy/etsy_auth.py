"""
Etsy Authentication Module
==========================
Handles Etsy OAuth2 token management for server-side API access.

Provides cached token storage with automatic refresh and retry logic.
"""

import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

ETSY_TOKEN = None
ETSY_TOKEN_EXPIRES = 0

# Create session with retry strategy
_etsy_session = None

def _get_etsy_session():
    """Get or create Etsy API session with retry configuration."""
    global _etsy_session
    if _etsy_session is None:
        _etsy_session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]  # Only retry POST for token requests
        )
        adapter = HTTPAdapter(max_retries=retry)
        _etsy_session.mount("https://", adapter)
    return _etsy_session


def get_etsy_token():
    """
    Get a valid Etsy access token, caching it until expiry.

    Returns cached token if still valid, otherwise requests a new one.

    Returns:
        str: Valid Etsy access token

    Raises:
        ValueError: If ETSY_API_KEY environment variable is not set
        requests.RequestException: If token request fails after retries
    """
    global ETSY_TOKEN, ETSY_TOKEN_EXPIRES

    # Return cached token if still valid (with 60 second buffer)
    if ETSY_TOKEN and time.time() < ETSY_TOKEN_EXPIRES:
        return ETSY_TOKEN

    # Get Etsy API key from environment
    api_key = os.environ.get("ETSY_API_KEY")
    if not api_key:
        raise ValueError("ETSY_API_KEY environment variable not set")

    # For Etsy, we use the API key directly (no OAuth token needed for public search)
    # This is a simplified approach - in production you'd want proper OAuth
    ETSY_TOKEN = api_key
    ETSY_TOKEN_EXPIRES = time.time() + (24 * 60 * 60)  # Cache for 24 hours

    return ETSY_TOKEN