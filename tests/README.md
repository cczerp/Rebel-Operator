# API Integration Tests

This directory contains tests for API integrations and OAuth credential validation.

## Running Tests

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
python tests/run_tests.py
```

### Run Specific Tests
```bash
pytest tests/test_api_integration.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## Test Coverage

### API Integration Tests
- Feed generation endpoints (`/api/generate-feed`)
- Feed sync scheduling (`/api/schedule-feed-sync`)
- Platform adapter functionality

### OAuth Validation
- Environment variable configuration
- Documentation completeness
- Credential storage validation

## Test Structure

```
tests/
├── conftest.py          # Test configuration
├── test_api_integration.py  # Main API tests
├── run_tests.py         # Test runner script
└── README.md           # This file
```

## Adding New Tests

1. Create new test files in `tests/` directory
2. Follow naming convention: `test_*.py`
3. Use Flask-Testing for API endpoint tests
4. Mock external dependencies appropriately

## OAuth Configuration Validation

The test suite validates that:
- Required OAuth environment variables are documented
- OAuth setup scripts exist
- Credential storage mechanisms are in place

For actual OAuth testing with real credentials, set the appropriate environment variables before running tests.