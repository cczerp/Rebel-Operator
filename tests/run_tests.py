#!/usr/bin/env python3
"""
Test Runner
===========
Run API integration tests and OAuth validation
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def run_tests():
    """Run the test suite"""
    print("Running API Integration Tests...")
    print("=" * 50)

    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("❌ pytest not installed. Install with: pip install pytest flask-testing")
        return False

    # Run tests
    result = pytest.main([
        'tests/',
        '-v',
        '--tb=short',
        '--disable-warnings'
    ])

    if result == 0:
        print("\n✅ All tests passed!")
        return True
    else:
        print(f"\n❌ Tests failed with exit code: {result}")
        return False

def validate_oauth_config():
    """Validate OAuth configuration"""
    print("\nValidating OAuth Configuration...")
    print("=" * 50)

    issues = []

    # Check required environment variables
    required_vars = [
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET',
        'EBAY_APP_ID',
        'EBAY_CERT_ID'
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        issues.append(f"Missing environment variables: {', '.join(missing_vars)}")
        print("⚠️  Some OAuth environment variables are not set")
        print("   This is normal for development/testing")
    else:
        print("✅ OAuth environment variables are configured")

    # Check OAuth setup documentation
    doc_files = ['GOOGLE_OAUTH_SETUP.md', 'CREDENTIALS_MANAGEMENT.md']
    for doc_file in doc_files:
        if os.path.exists(doc_file):
            print(f"✅ OAuth documentation found: {doc_file}")
        else:
            issues.append(f"Missing documentation: {doc_file}")

    # Check OAuth config script
    if os.path.exists('check-oauth-config.sh'):
        print("✅ OAuth configuration script found")
    else:
        issues.append("Missing OAuth config script: check-oauth-config.sh")

    if issues:
        print("\n⚠️  OAuth validation issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ OAuth configuration validation passed")
        return True

if __name__ == '__main__':
    print("API Integration Testing & OAuth Validation")
    print("=" * 50)

    # Validate OAuth config
    oauth_ok = validate_oauth_config()

    # Run tests
    tests_ok = run_tests()

    print("\n" + "=" * 50)
    if oauth_ok and tests_ok:
        print("🎉 All validations passed!")
        sys.exit(0)
    else:
        print("⚠️  Some validations failed. Check output above.")
        sys.exit(1)