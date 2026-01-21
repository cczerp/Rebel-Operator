#!/usr/bin/env python3
"""
Platform Connection Test Suite
===============================
Tests actual API connections and credential validity for all integrated platforms.

Usage:
    python scripts/test_platform_connections.py                    # Test all platforms
    python scripts/test_platform_connections.py ebay               # Test specific platform
    python scripts/test_platform_connections.py --user-id 1        # Test for specific user
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


class PlatformConnectionTester:
    """Tests platform API connections and credential validity"""

    def __init__(self, user_id: Optional[int] = None):
        self.user_id = user_id
        self.results = {}

    def print_header(self, title: str):
        """Print formatted section header"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}{title:^60}{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

    def print_success(self, message: str):
        """Print success message"""
        print(f"{GREEN}✅ {message}{RESET}")

    def print_error(self, message: str):
        """Print error message"""
        print(f"{RED}❌ {message}{RESET}")

    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{YELLOW}⚠️  {message}{RESET}")

    def print_info(self, message: str):
        """Print info message"""
        print(f"   {message}")

    # -------------------------------------------------------------------------
    # API-BASED PLATFORMS (Can test actual connections)
    # -------------------------------------------------------------------------

    def test_ebay_connection(self, credentials: Dict) -> Tuple[bool, str]:
        """Test eBay API connection with OAuth tokens"""
        try:
            client_id = credentials.get('client_id')
            client_secret = credentials.get('client_secret')
            refresh_token = credentials.get('refresh_token')

            if not all([client_id, client_secret, refresh_token]):
                return False, "Missing required credentials (client_id, client_secret, or refresh_token)"

            # Step 1: Refresh access token
            self.print_info("Step 1: Refreshing OAuth access token...")
            auth_response = requests.post(
                "https://api.ebay.com/identity/v1/oauth2/token",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                auth=(client_id, client_secret),
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                },
                timeout=10
            )

            if auth_response.status_code != 200:
                return False, f"OAuth token refresh failed: {auth_response.text}"

            access_token = auth_response.json().get('access_token')
            self.print_success("Access token refreshed")

            # Step 2: Test API connectivity
            self.print_info("Step 2: Testing API connectivity...")
            api_response = requests.get(
                "https://api.ebay.com/sell/account/v1/fulfillment_policy",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )

            if api_response.status_code in [200, 204]:
                self.print_success("API connectivity verified")
                return True, "eBay API connection successful"
            else:
                return False, f"API test failed: HTTP {api_response.status_code}"

        except requests.exceptions.Timeout:
            return False, "Connection timeout - eBay API not responding"
        except requests.exceptions.ConnectionError:
            return False, "Network error - Cannot reach eBay API"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def test_etsy_connection(self, credentials: Dict) -> Tuple[bool, str]:
        """Test Etsy API connection"""
        try:
            api_key = credentials.get('api_key')
            shop_id = credentials.get('shop_id')

            if not api_key:
                return False, "Missing API key"

            # Test Etsy API v3
            response = requests.get(
                f"https://openapi.etsy.com/v3/application/shops/{shop_id}",
                headers={
                    "x-api-key": api_key
                },
                timeout=10
            )

            if response.status_code == 200:
                shop_data = response.json()
                shop_name = shop_data.get('shop_name', 'Unknown')
                self.print_success(f"Connected to shop: {shop_name}")
                return True, "Etsy API connection successful"
            else:
                return False, f"API test failed: HTTP {response.status_code}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def test_shopify_connection(self, credentials: Dict) -> Tuple[bool, str]:
        """Test Shopify API connection"""
        try:
            store_url = credentials.get('store_url')
            access_token = credentials.get('access_token')

            if not all([store_url, access_token]):
                return False, "Missing store URL or access token"

            # Ensure URL format
            if not store_url.startswith('https://'):
                store_url = f"https://{store_url}"
            if not store_url.endswith('.myshopify.com'):
                store_url = f"{store_url}.myshopify.com"

            # Test Shopify Admin API
            response = requests.get(
                f"{store_url}/admin/api/2024-01/shop.json",
                headers={
                    "X-Shopify-Access-Token": access_token
                },
                timeout=10
            )

            if response.status_code == 200:
                shop_data = response.json().get('shop', {})
                shop_name = shop_data.get('name', 'Unknown')
                self.print_success(f"Connected to store: {shop_name}")
                return True, "Shopify API connection successful"
            else:
                return False, f"API test failed: HTTP {response.status_code}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def test_tcgplayer_connection(self, credentials: Dict) -> Tuple[bool, str]:
        """Test TCGplayer API connection"""
        try:
            api_key = credentials.get('api_key')

            if not api_key:
                return False, "Missing API key"

            # Test TCGplayer API
            response = requests.get(
                "https://api.tcgplayer.com/catalog/categories",
                headers={
                    "Authorization": f"Bearer {api_key}"
                },
                timeout=10
            )

            if response.status_code == 200:
                categories = response.json()
                self.print_success(f"API access verified ({len(categories)} categories)")
                return True, "TCGplayer API connection successful"
            else:
                return False, f"API test failed: HTTP {response.status_code}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def test_woocommerce_connection(self, credentials: Dict) -> Tuple[bool, str]:
        """Test WooCommerce API connection"""
        try:
            store_url = credentials.get('store_url')
            consumer_key = credentials.get('consumer_key')
            consumer_secret = credentials.get('consumer_secret')

            if not all([store_url, consumer_key, consumer_secret]):
                return False, "Missing store URL, consumer key, or consumer secret"

            # Test WooCommerce REST API
            response = requests.get(
                f"{store_url}/wp-json/wc/v3/system_status",
                auth=(consumer_key, consumer_secret),
                timeout=10
            )

            if response.status_code == 200:
                system_data = response.json()
                env_data = system_data.get('environment', {})
                wp_version = env_data.get('wp_version', 'Unknown')
                wc_version = env_data.get('wc_version', 'Unknown')
                self.print_success(f"WP {wp_version}, WC {wc_version}")
                return True, "WooCommerce API connection successful"
            else:
                return False, f"API test failed: HTTP {response.status_code}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    # -------------------------------------------------------------------------
    # CSV-ONLY PLATFORMS (Validate format only)
    # -------------------------------------------------------------------------

    def test_poshmark_credentials(self, credentials: Dict) -> Tuple[bool, str]:
        """Validate Poshmark credentials format (no API)"""
        username = credentials.get('username')
        password = credentials.get('password')

        if not username or not password:
            return False, "Missing username or password"

        self.print_warning("Poshmark has no public API - manual validation required")
        self.print_info("Credentials format validated")
        return True, "Credentials stored (manual login required)"

    def test_mercari_credentials(self, credentials: Dict) -> Tuple[bool, str]:
        """Validate Mercari credentials format (no API)"""
        username = credentials.get('username')
        password = credentials.get('password')

        if not username or not password:
            return False, "Missing username or password"

        self.print_warning("Mercari has no public API - manual validation required")
        self.print_info("Credentials format validated")
        return True, "Credentials stored (manual login required)"

    def test_grailed_credentials(self, credentials: Dict) -> Tuple[bool, str]:
        """Validate Grailed credentials format (no API)"""
        username = credentials.get('username')
        password = credentials.get('password')

        if not username or not password:
            return False, "Missing username or password"

        self.print_warning("Grailed has no public API - manual validation required")
        self.print_info("Credentials format validated")
        return True, "Credentials stored (manual login required)"

    def test_depop_credentials(self, credentials: Dict) -> Tuple[bool, str]:
        """Validate Depop credentials format (limited API)"""
        username = credentials.get('username')
        password = credentials.get('password')

        if not username or not password:
            return False, "Missing username or password"

        self.print_warning("Depop API requires approval - manual validation required")
        self.print_info("Credentials format validated")
        return True, "Credentials stored (API approval pending)"

    # -------------------------------------------------------------------------
    # Test Orchestration
    # -------------------------------------------------------------------------

    PLATFORM_TESTERS = {
        # API Platforms (actual connection tests)
        'ebay': test_ebay_connection,
        'etsy': test_etsy_connection,
        'shopify': test_shopify_connection,
        'tcgplayer': test_tcgplayer_connection,
        'woocommerce': test_woocommerce_connection,

        # CSV Platforms (format validation only)
        'poshmark': test_poshmark_credentials,
        'mercari': test_mercari_credentials,
        'grailed': test_grailed_credentials,
        'depop': test_depop_credentials,
    }

    def test_platform(self, platform: str, credentials: Dict) -> Tuple[bool, str]:
        """Test a specific platform"""
        tester = self.PLATFORM_TESTERS.get(platform.lower())

        if not tester:
            return False, f"No test available for platform: {platform}"

        return tester(self, credentials)

    def load_credentials_from_db(self, platform: Optional[str] = None) -> Dict:
        """Load credentials from database"""
        try:
            from src.database.db import get_connection

            conn = get_connection()
            cursor = conn.cursor()

            if platform:
                query = """
                    SELECT platform, username, password, credentials_json
                    FROM marketplace_credentials
                    WHERE platform = %s
                """
                params = (platform,)
                if self.user_id:
                    query += " AND user_id = %s"
                    params = (platform, self.user_id)

                cursor.execute(query, params)
            else:
                query = """
                    SELECT platform, username, password, credentials_json
                    FROM marketplace_credentials
                """
                if self.user_id:
                    query += " WHERE user_id = %s"
                    cursor.execute(query, (self.user_id,))
                else:
                    cursor.execute(query)

            results = {}
            for row in cursor.fetchall():
                platform_name = row[0]
                creds = {
                    'username': row[1],
                    'password': row[2],
                }

                # Parse JSON credentials if present
                if row[3]:
                    try:
                        json_creds = json.loads(row[3])
                        creds.update(json_creds)
                    except:
                        pass

                results[platform_name] = creds

            cursor.close()
            conn.close()

            return results

        except Exception as e:
            self.print_error(f"Database error: {e}")
            return {}

    def run_tests(self, platforms: Optional[List[str]] = None):
        """Run connection tests for specified platforms"""
        self.print_header("Platform Connection Test Suite")

        # Load credentials
        all_credentials = self.load_credentials_from_db()

        if not all_credentials:
            self.print_error("No credentials found in database")
            self.print_info("Add credentials in Settings → Platform Integrations")
            return

        # Filter to requested platforms if specified
        if platforms:
            test_platforms = {p: all_credentials[p] for p in platforms if p in all_credentials}
        else:
            test_platforms = all_credentials

        if not test_platforms:
            self.print_error("No matching platforms found")
            return

        # Run tests
        total = len(test_platforms)
        passed = 0
        failed = 0

        for platform, credentials in test_platforms.items():
            print(f"\n{BOLD}Testing {platform.upper()}...{RESET}")
            print("─" * 60)

            success, message = self.test_platform(platform, credentials)

            if success:
                self.print_success(message)
                passed += 1
                self.results[platform] = "PASS"
            else:
                self.print_error(message)
                failed += 1
                self.results[platform] = "FAIL"

        # Summary
        self.print_header("Test Summary")
        print(f"Total Platforms: {total}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")

        # Detailed results
        print(f"\n{BOLD}Results by Platform:{RESET}")
        for platform, result in self.results.items():
            status_icon = "✅" if result == "PASS" else "❌"
            print(f"  {status_icon} {platform.capitalize()}: {result}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test platform API connections")
    parser.add_argument('platforms', nargs='*', help="Specific platforms to test")
    parser.add_argument('--user-id', type=int, help="Test for specific user ID")
    args = parser.parse_args()

    tester = PlatformConnectionTester(user_id=args.user_id)
    tester.run_tests(args.platforms if args.platforms else None)


if __name__ == "__main__":
    main()
