#!/usr/bin/env python3
"""
Python Syntax Validator
=======================
Validates Python syntax for all .py files in the codebase using AST parsing.

Usage:
    python tools/validate_python.py [directory]
    
    If no directory specified, checks current directory.
"""

import ast
import sys
from pathlib import Path

def validate_python_file(filepath):
    """Validate a single Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        ast.parse(content)
        return None
    except SyntaxError as e:
        return {
            'file': str(filepath),
            'line': e.lineno,
            'offset': e.offset,
            'message': e.msg,
            'text': e.text
        }
    except Exception as e:
        return {
            'file': str(filepath),
            'line': None,
            'offset': None,
            'message': f"Error reading file: {str(e)}",
            'text': None
        }

def main():
    """Main function."""
    exclude_dirs = {'venv', '__pycache__', '.git', 'node_modules', '.venv', 'tools'}
    
    root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
    
    errors = []
    files_checked = 0
    
    for py_file in root.rglob('*.py'):
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue
        files_checked += 1
        error = validate_python_file(py_file)
        if error:
            errors.append(error)
    
    if errors:
        print(f"Found {len(errors)} syntax error(s) in {files_checked} Python file(s):\n")
        for error in errors:
            print(f"File: {error['file']}")
            if error['line']:
                print(f"  Line {error['line']}, Column {error['offset']}: {error['message']}")
                if error['text']:
                    print(f"  {error['text'].strip()}")
            else:
                print(f"  {error['message']}")
            print()
        sys.exit(1)
    else:
        print(f"[OK] All {files_checked} Python files have valid syntax!")
        sys.exit(0)

if __name__ == '__main__':
    main()

