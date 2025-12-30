# Development Tools

This directory contains utility scripts for code quality checking, syntax validation, and codebase maintenance.

## Available Tools

### `check_syntax.py`
Comprehensive syntax and grammar checker for all code files.

**Usage:**
```bash
python tools/check_syntax.py [directory]
```

**Features:**
- Checks Python, JSON, HTML, JavaScript, and TypeScript files
- Validates syntax (AST parsing for Python, JSON validation)
- Checks for common spelling/grammar mistakes in comments and strings
- Excludes venv, node_modules, and other common directories

**Example:**
```bash
python tools/check_syntax.py
python tools/check_syntax.py src/
```

---

### `find_js_errors.py`
Finds JavaScript syntax errors in HTML template files by checking for unbalanced braces, parentheses, and brackets.

**Usage:**
```bash
python tools/find_js_errors.py [file_or_directory]
```

**Features:**
- Extracts JavaScript from `<script>` tags in HTML files
- Checks for balanced braces `{}`, parentheses `()`, and brackets `[]`
- Reports exact location and differences
- Defaults to checking `templates/` directory

**Example:**
```bash
python tools/find_js_errors.py
python tools/find_js_errors.py templates/create.html
```

---

### `validate_python.py`
Fast Python syntax validator using AST parsing.

**Usage:**
```bash
python tools/validate_python.py [directory]
```

**Features:**
- Validates all `.py` files using Python's AST parser
- Reports syntax errors with line numbers and details
- Faster than running full linters
- Excludes common directories automatically

**Example:**
```bash
python tools/validate_python.py
python tools/validate_python.py src/
```

---

### `check_imports.py`
Analyzes imports in Python files to find potentially unused imports.

**Usage:**
```bash
python tools/check_imports.py [file_or_directory]
```

**Features:**
- Parses Python AST to find all imports
- Tracks which imported names are actually used
- Reports potentially unused imports
- Filters out common false positives (self, cls, exceptions, etc.)

**Example:**
```bash
python tools/check_imports.py
python tools/check_imports.py src/database/
```

---

## Running All Checks

You can run multiple tools in sequence:

```bash
# Quick syntax check
python tools/validate_python.py

# Comprehensive check
python tools/check_syntax.py

# JavaScript-specific
python tools/find_js_errors.py templates/

# Import analysis
python tools/check_imports.py src/
```

---

## Adding New Tools

When creating new utility scripts:

1. Add them to the `tools/` directory
2. Include a shebang line: `#!/usr/bin/env python3`
3. Add docstring with usage instructions
4. Update this README.md with documentation
5. Make them executable (optional): `chmod +x tools/script_name.py`

---

## Notes

- All tools exclude common directories: `venv`, `__pycache__`, `.git`, `node_modules`, `.venv`
- Tools handle encoding errors gracefully
- Exit codes: 0 = success, 1 = errors found
- Tools are designed to be run from the project root directory

