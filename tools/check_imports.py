#!/usr/bin/env python3
"""
Import Checker
==============
Checks for missing or unused imports in Python files.

Usage:
    python tools/check_imports.py [file_or_directory]
"""

import ast
import sys
from pathlib import Path
from collections import defaultdict

def analyze_imports(filepath):
    """Analyze imports in a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        imports = []
        imported_names = set()
        used_names = set()
        
        class ImportVisitor(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    imports.append(alias.name)
                    imported_names.add(alias.asname if alias.asname else alias.name)
            
            def visit_ImportFrom(self, node):
                module = node.module or ''
                for alias in node.names:
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    imports.append(full_name)
                    imported_names.add(alias.asname if alias.asname else alias.name)
            
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)
        
        visitor = ImportVisitor()
        visitor.visit(tree)
        
        return {
            'file': str(filepath),
            'imports': imports,
            'imported_names': imported_names,
            'used_names': used_names,
            'potentially_unused': imported_names - used_names
        }
    except Exception as e:
        return {'file': str(filepath), 'error': str(e)}

def main():
    """Main function."""
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    else:
        target = Path('.')
    
    exclude_dirs = {'venv', '__pycache__', '.git', 'node_modules', '.venv', 'tools'}
    
    if target.is_file():
        files = [target]
    else:
        files = [f for f in target.rglob('*.py') 
                if not any(excluded in f.parts for excluded in exclude_dirs)]
    
    results = []
    for py_file in files:
        result = analyze_imports(py_file)
        results.append(result)
    
    print(f"Analyzed {len(results)} Python file(s):\n")
    
    for result in results:
        if 'error' in result:
            print(f"{result['file']}: Error - {result['error']}")
            continue
        
        unused = result['potentially_unused']
        # Filter out common false positives (like decorators, exceptions, etc.)
        common_false_positives = {'self', 'cls', 'kwargs', 'args', 'Exception', 'BaseException'}
        unused = unused - common_false_positives
        
        if unused:
            print(f"{result['file']}:")
            print(f"  Potentially unused imports: {', '.join(sorted(unused))}")
            print()

if __name__ == '__main__':
    main()

