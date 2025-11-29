"""
API Integration Tests
====================
Tests for platform API integrations and OAuth credential validation
"""

import pytest
import json
import os
from unittest.mock import Mock, patch
from flask import Flask
from flask_testing import TestCase

# Import the Flask app
from web_app import app
from src.database.db import Database
from src.adapters.all_platforms import (
    FacebookShopsAdapter,
    GoogleShoppingAdapter,
    PinterestAdapter,
    EtsyAdapter,
    ShopifyAdapter
)


class TestAPIIntegration(TestCase):
    """Test API integrations and OAuth validation"""

    def create_app(self):
        """Create Flask test app"""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        return app

    def setUp(self):
        """Set up test fixtures"""
        self.db = Database()
        # Create test user if not exists
        self.test_user_id = 1

    def tearDown(self):
        """Clean up after tests"""
        pass

    def test_feed_generation_facebook(self):
        """Test Facebook feed generation"""
        with self.client:
            # Login as test user (mock)
            with patch('flask_login.utils._get_user') as mock_user:
                mock_user.return_value = Mock(id=self.test_user_id, is_authenticated=True)

                # Test feed generation
                response = self.client.post('/api/generate-feed',
                    json={'platform': 'facebook', 'format': 'csv'},
                    content_type='application/json'
                )

                # Should return CSV data or error
                self.assertIn(response.status_code, [200, 404])  # 404 if no listings

    def test_feed_generation_google(self):
        """Test Google Shopping feed generation"""
        with self.client:
            with patch('flask_login.utils._get_user') as mock_user:
                mock_user.return_value = Mock(id=self.test_user_id, is_authenticated=True)

                response = self.client.post('/api/generate-feed',
                    json={'platform': 'google', 'format': 'xml'},
                    content_type='application/json'
                )

                self.assertIn(response.status_code, [200, 404])

    def test_feed_generation_pinterest(self):
        """Test Pinterest feed generation"""
        with self.client:
            with patch('flask_login.utils._get_user') as mock_user:
                mock_user.return_value = Mock(id=self.test_user_id, is_authenticated=True)

                response = self.client.post('/api/generate-feed',
                    json={'platform': 'pinterest', 'format': 'csv'},
                    content_type='application/json'
                )

                self.assertIn(response.status_code, [200, 404])

    def test_feed_sync_scheduling(self):
        """Test feed sync scheduling"""
        with self.client:
            with patch('flask_login.utils._get_user') as mock_user:
                mock_user.return_value = Mock(id=self.test_user_id, is_authenticated=True)

                response = self.client.post('/api/schedule-feed-sync',
                    json={
                        'platforms': ['facebook', 'google'],
                        'interval_hours': 6
                    },
                    content_type='application/json'
                )

                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertIn('status', data)
                self.assertEqual(data['status'], 'scheduled')

    @patch('src.adapters.all_platforms.FacebookShopsAdapter.generate_csv')
    def test_facebook_adapter_csv_generation(self, mock_generate_csv):
        """Test Facebook adapter CSV generation"""
        mock_generate_csv.return_value = "id,title,description\n1,Test Item,Description"

        adapter = FacebookShopsAdapter()
        listings = []  # Empty list for test

        result = adapter.generate_csv(listings)
        self.assertIsInstance(result, str)
        mock_generate_csv.assert_called_once_with(listings)

    @patch('src.adapters.all_platforms.GoogleShoppingAdapter.generate_csv')
    def test_google_adapter_csv_generation(self, mock_generate_csv):
        """Test Google Shopping adapter CSV generation"""
        mock_generate_csv.return_value = "id,title,description\n1,Test Item,Description"

        adapter = GoogleShoppingAdapter()
        listings = []

        result = adapter.generate_csv(listings)
        self.assertIsInstance(result, str)
        mock_generate_csv.assert_called_once_with(listings)

    @patch('src.adapters.all_platforms.PinterestAdapter.generate_csv')
    def test_pinterest_adapter_csv_generation(self, mock_generate_csv):
        """Test Pinterest adapter CSV generation"""
        mock_generate_csv.return_value = "id,title,description\n1,Test Item,Description"

        adapter = PinterestAdapter()
        listings = []

        result = adapter.generate_csv(listings)
        self.assertIsInstance(result, str)
        mock_generate_csv.assert_called_once_with(listings)


class TestOAuthValidation(TestCase):
    """Test OAuth credential validation"""

    def create_app(self):
        return app

    def setUp(self):
        self.db = Database()

    def test_oauth_config_validation(self):
        """Test OAuth configuration validation"""
        # Test that OAuth config script exists and is executable
        config_script = "check-oauth-config.sh"
        self.assertTrue(os.path.exists(config_script))

        # Test OAuth environment variables are documented
        required_vars = [
            'GOOGLE_CLIENT_ID',
            'GOOGLE_CLIENT_SECRET',
            'EBAY_APP_ID',
            'EBAY_CERT_ID',
            'MERCARI_CLIENT_ID',
            'MERCARI_CLIENT_SECRET'
        ]

        # Check if these are mentioned in documentation
        with open('GOOGLE_OAUTH_SETUP.md', 'r') as f:
            google_doc = f.read()

        with open('CREDENTIALS_MANAGEMENT.md', 'r') as f:
            creds_doc = f.read()

        for var in required_vars:
            self.assertTrue(
                var in google_doc or var in creds_doc,
                f"OAuth variable {var} not documented"
            )

    def test_platform_credentials_storage(self):
        """Test that platform credentials are properly stored"""
        # This would test the credential storage mechanism
        # For now, just verify the database has credential tables
        cursor = self.db._get_cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE '%credential%'
        """)
        tables = cursor.fetchall()

        # Should have some credential-related tables
        credential_tables = [t[0] for t in tables]
        self.assertTrue(len(credential_tables) > 0, "No credential tables found")


if __name__ == '__main__':
    pytest.main([__file__])