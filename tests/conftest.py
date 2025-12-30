"""
Test Configuration
==================
Configuration for running API integration tests
"""

import os

# Test database configuration
TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL', 'sqlite:///test_resell_rebel.db')

# Test OAuth credentials (use dummy values for testing)
TEST_OAUTH_CONFIG = {
    'GOOGLE_CLIENT_ID': 'test_google_client_id',
    'GOOGLE_CLIENT_SECRET': 'test_google_client_secret',
    'EBAY_APP_ID': 'test_ebay_app_id',
    'EBAY_CERT_ID': 'test_ebay_cert_id',
    'MERCARI_CLIENT_ID': 'test_mercari_client_id',
    'MERCARI_CLIENT_SECRET': 'test_mercari_client_secret'
}

# Test user configuration
TEST_USER = {
    'id': 1,
    'email': 'test@example.com',
    'username': 'testuser'
}