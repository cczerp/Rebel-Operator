"""
Flask Session Storage for Supabase Auth
Based on: https://supabase.com/blog/oauth2-login-python-flask-apps
"""

from gotrue import SyncSupportedStorage
from flask import session


class FlaskSessionStorage(SyncSupportedStorage):
    """
    Custom storage adapter for Supabase Auth to use Flask sessions.

    This tells the Supabase authentication library (gotrue) how to
    retrieve, store and remove sessions (JWT tokens) in Flask's session.
    
    CRITICAL: Must mark session as modified when storing items so Flask-Session
    persists them to Redis. Without this, OAuth state/code_verifier won't persist
    between requests, causing bad_oauth_state errors.
    """

    def __init__(self):
        self.storage = session

    def get_item(self, key: str) -> str | None:
        """Retrieve item from Flask session"""
        if key in self.storage:
            return self.storage[key]
        return None

    def set_item(self, key: str, value: str) -> None:
        """
        Store item in Flask session.
        
        CRITICAL: Mark session as modified so Flask-Session saves to Redis.
        This is required for OAuth PKCE flow - code_verifier must persist
        between OAuth initiation and callback.
        """
        self.storage[key] = value
        # CRITICAL: Mark session as modified so Flask-Session persists to Redis
        # Without this, the code_verifier won't be available on callback
        self.storage.modified = True

    def remove_item(self, key: str) -> None:
        """Remove item from Flask session"""
        if key in self.storage:
            self.storage.pop(key, None)
            # Mark as modified when removing items too
            self.storage.modified = True
