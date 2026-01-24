"""
eBay Token Manager
==================
Manages eBay OAuth tokens in the database with automatic refresh.
"""

import json
from datetime import datetime
from typing import Optional, Dict
from .crypto_utils import get_token_crypto
from .oauth_client import get_ebay_oauth_client


class eBayTokenManager:
    """Manages eBay OAuth tokens for users"""

    def __init__(self, db):
        """
        Initialize token manager.

        Args:
            db: Database instance
        """
        self.db = db
        self.crypto = get_token_crypto()

    def save_tokens(
        self,
        user_id: int,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        environment: str = 'sandbox',
        scopes: list = None,
        ebay_user_info: dict = None
    ) -> bool:
        """
        Save eBay OAuth tokens to database (encrypted).

        Args:
            user_id: User ID
            access_token: eBay access token
            refresh_token: eBay refresh token
            expires_in: Seconds until access token expires
            environment: 'sandbox' or 'production'
            scopes: List of granted scopes
            ebay_user_info: Optional eBay user info dict

        Returns:
            bool: True if successful
        """
        try:
            # Encrypt tokens
            encrypted_access = self.crypto.encrypt(access_token)
            encrypted_refresh = self.crypto.encrypt(refresh_token)

            # Calculate expiry time
            oauth_client = get_ebay_oauth_client(environment)
            expires_at = oauth_client.calculate_expiry_time(expires_in)

            # Prepare scopes JSON
            scopes_json = json.dumps(scopes) if scopes else None

            # Extract eBay user info
            ebay_user_id = None
            ebay_username = None
            if ebay_user_info:
                ebay_user_id = ebay_user_info.get('userId')
                ebay_username = ebay_user_info.get('username')

            cursor = self.db._get_cursor()

            # Check if tokens already exist for this user/environment
            cursor.execute("""
                SELECT id FROM ebay_tokens
                WHERE user_id = %s AND environment = %s
            """, (user_id, environment))

            existing = cursor.fetchone()

            if existing:
                # Update existing tokens
                cursor.execute("""
                    UPDATE ebay_tokens
                    SET access_token = %s,
                        refresh_token = %s,
                        expires_at = %s,
                        scopes = %s,
                        ebay_user_id = %s,
                        ebay_username = %s,
                        updated_at = NOW()
                    WHERE user_id = %s AND environment = %s
                """, (
                    encrypted_access,
                    encrypted_refresh,
                    expires_at,
                    scopes_json,
                    ebay_user_id,
                    ebay_username,
                    user_id,
                    environment
                ))
            else:
                # Insert new tokens
                cursor.execute("""
                    INSERT INTO ebay_tokens (
                        user_id, access_token, refresh_token, expires_at,
                        environment, scopes, ebay_user_id, ebay_username
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    encrypted_access,
                    encrypted_refresh,
                    expires_at,
                    environment,
                    scopes_json,
                    ebay_user_id,
                    ebay_username
                ))

            self.db.conn.commit()
            cursor.close()

            print(f"[SUCCESS] Saved eBay tokens for user {user_id} ({environment})")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to save eBay tokens: {e}")
            if self.db.conn:
                self.db.conn.rollback()
            return False

    def get_tokens(self, user_id: int, environment: str = 'sandbox') -> Optional[Dict]:
        """
        Get eBay OAuth tokens for user (decrypted, auto-refreshed if needed).

        Args:
            user_id: User ID
            environment: 'sandbox' or 'production'

        Returns:
            dict: Token data or None if not found
                - access_token: Decrypted access token
                - refresh_token: Decrypted refresh token
                - expires_at: Expiry datetime
                - ebay_user_id: eBay user ID
                - ebay_username: eBay username
        """
        try:
            cursor = self.db._get_cursor()

            cursor.execute("""
                SELECT *
                FROM ebay_tokens
                WHERE user_id = %s AND environment = %s
            """, (user_id, environment))

            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            # Convert to dict if using RealDictCursor
            if isinstance(row, dict):
                token_data = row
            else:
                # Convert tuple to dict
                columns = ['id', 'user_id', 'access_token', 'refresh_token', 'expires_at',
                          'token_type', 'environment', 'scopes', 'ebay_user_id', 'ebay_username',
                          'created_at', 'updated_at']
                token_data = dict(zip(columns, row))

            # Decrypt tokens
            access_token = self.crypto.decrypt(token_data['access_token'])
            refresh_token = self.crypto.decrypt(token_data['refresh_token'])

            # Check if access token is expired
            expires_at = token_data['expires_at']
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))

            if datetime.utcnow() >= expires_at:
                print(f"[INFO] Access token expired, refreshing...")
                refreshed = self.refresh_tokens(user_id, refresh_token, environment)
                if refreshed:
                    # Get updated tokens
                    return self.get_tokens(user_id, environment)
                else:
                    print(f"[ERROR] Failed to refresh tokens")
                    return None

            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_at': expires_at,
                'ebay_user_id': token_data.get('ebay_user_id'),
                'ebay_username': token_data.get('ebay_username'),
                'scopes': json.loads(token_data['scopes']) if token_data.get('scopes') else None
            }

        except Exception as e:
            print(f"[ERROR] Failed to get eBay tokens: {e}")
            return None

    def refresh_tokens(
        self,
        user_id: int,
        refresh_token: str,
        environment: str = 'sandbox'
    ) -> bool:
        """
        Refresh expired access token.

        Args:
            user_id: User ID
            refresh_token: Current refresh token (decrypted)
            environment: 'sandbox' or 'production'

        Returns:
            bool: True if successful
        """
        try:
            oauth_client = get_ebay_oauth_client(environment)

            # Call eBay API to refresh token
            token_response = oauth_client.refresh_access_token(refresh_token)

            # Save new tokens
            return self.save_tokens(
                user_id=user_id,
                access_token=token_response['access_token'],
                refresh_token=refresh_token,  # Refresh token stays the same
                expires_in=token_response['expires_in'],
                environment=environment
            )

        except Exception as e:
            print(f"[ERROR] Failed to refresh eBay tokens: {e}")
            return False

    def has_valid_tokens(self, user_id: int, environment: str = 'sandbox') -> bool:
        """
        Check if user has valid eBay tokens.

        Args:
            user_id: User ID
            environment: 'sandbox' or 'production'

        Returns:
            bool: True if user has valid tokens
        """
        tokens = self.get_tokens(user_id, environment)
        return tokens is not None

    def delete_tokens(self, user_id: int, environment: str = 'sandbox') -> bool:
        """
        Delete eBay tokens for user (disconnect).

        Args:
            user_id: User ID
            environment: 'sandbox' or 'production'

        Returns:
            bool: True if successful
        """
        try:
            cursor = self.db._get_cursor()

            cursor.execute("""
                DELETE FROM ebay_tokens
                WHERE user_id = %s AND environment = %s
            """, (user_id, environment))

            self.db.conn.commit()
            cursor.close()

            print(f"[SUCCESS] Deleted eBay tokens for user {user_id} ({environment})")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to delete eBay tokens: {e}")
            if self.db.conn:
                self.db.conn.rollback()
            return False

    def get_ebay_user_info(self, user_id: int, environment: str = 'sandbox') -> Optional[Dict]:
        """
        Get eBay user information.

        Args:
            user_id: User ID
            environment: 'sandbox' or 'production'

        Returns:
            dict: eBay user info or None
        """
        try:
            cursor = self.db._get_cursor()

            cursor.execute("""
                SELECT ebay_user_id, ebay_username
                FROM ebay_tokens
                WHERE user_id = %s AND environment = %s
            """, (user_id, environment))

            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            if isinstance(row, dict):
                return {
                    'ebay_user_id': row['ebay_user_id'],
                    'ebay_username': row['ebay_username']
                }
            else:
                return {
                    'ebay_user_id': row[0],
                    'ebay_username': row[1]
                }

        except Exception as e:
            print(f"[ERROR] Failed to get eBay user info: {e}")
            return None
