#!/usr/bin/env python3
"""
Syntax and Grammar Checker for Codebase
=========================================
Checks all code files for syntax errors and common grammar/spelling mistakes.

Usage:
    python tools/check_syntax.py [directory]
    
    If no directory specified, checks current directory.
"""

import ast
import json
import re
import sys
from pathlib import Path

# Common grammar/spelling mistakes to check
GRAMMAR_ISSUES = {
    'recieve': 'receive',
    'seperate': 'separate',
    'occured': 'occurred',
    'occurence': 'occurrence',
    'existant': 'existent',
    'existance': 'existence',
    'sucess': 'success',
    'sucessful': 'successful',
    'definately': 'definitely',
    'neccessary': 'necessary',
    'accomodate': 'accommodate',
    'begining': 'beginning',
    'beleive': 'believe',
    'calender': 'calendar',
    'comming': 'coming',
    'concieve': 'conceive',
    'definate': 'definite',
    'developement': 'development',
    'enviroment': 'environment',
    'familar': 'familiar',
    'feild': 'field',
    'foreward': 'forward',
    'foward': 'forward',
    'freind': 'friend',
    'fufill': 'fulfill',
    'grammer': 'grammar',
    'harrass': 'harass',
    'heighth': 'height',
    'independant': 'independent',
    'judgement': 'judgment',
    'knowlege': 'knowledge',
    'lenght': 'length',
    'libary': 'library',
    'lisence': 'license',
    'mispell': 'misspell',
    'occured': 'occurred',
    'ommited': 'omitted',
    'posession': 'possession',
    'prefered': 'preferred',
    'prefering': 'preferring',
    'recomend': 'recommend',
    'recomendation': 'recommendation',
    'recomended': 'recommended',
    'recomending': 'recommending',
    'refered': 'referred',
    'refering': 'referring',
    'truely': 'truly',
    'untill': 'until',
    'usefull': 'useful',
}

errors = []
warnings = []

def check_python_syntax(filepath):
    """Check Python file for syntax errors."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        ast.parse(content)
        return None
    except SyntaxError as e:
        return f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def check_json_syntax(filepath):
    """Check JSON file for syntax errors."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            json.load(f)
        return None
    except json.JSONDecodeError as e:
        return f"JSON syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def check_grammar_in_text(text, filepath, line_num):
    """Check text for common grammar/spelling mistakes."""
    issues = []
    text_lower = text.lower()
    for mistake, correction in GRAMMAR_ISSUES.items():
        if mistake in text_lower:
            # Only check in comments/strings, not in code identifiers
            if re.search(r'\b' + re.escape(mistake) + r'\b', text_lower):
                issues.append((mistake, correction))
    return issues

def check_file(filepath):
    """Check a single file for issues."""
    path = Path(filepath)
    
    if path.suffix == '.py':
        syntax_error = check_python_syntax(filepath)
        if syntax_error:
            errors.append(f"{filepath}: {syntax_error}")
            return
        
        # Check grammar in comments and strings
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Check comments
                    if '#' in line:
                        comment = line[line.index('#'):]
                        issues = check_grammar_in_text(comment, filepath, line_num)
                        for mistake, correction in issues:
                            warnings.append(f"{filepath}:{line_num}: Possible spelling mistake: '{mistake}' should be '{correction}'")
                    
                    # Check string literals (simple check)
                    for match in re.finditer(r'["\']([^"\']+)["\']', line):
                        text = match.group(1)
                        if len(text) > 3:  # Only check longer strings
                            issues = check_grammar_in_text(text, filepath, line_num)
                            for mistake, correction in issues:
                                warnings.append(f"{filepath}:{line_num}: Possible spelling mistake in string: '{mistake}' should be '{correction}'")
        except Exception as e:
            errors.append(f"{filepath}: Error reading file: {str(e)}")
    
    elif path.suffix == '.json':
        syntax_error = check_json_syntax(filepath)
        if syntax_error:
            errors.append(f"{filepath}: {syntax_error}")
    
    elif path.suffix in ['.html', '.js', '.ts', '.tsx']:
        # Check HTML/JS for grammar in user-facing text
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Check in text content (between tags or in strings)
                issues = check_grammar_in_text(content, filepath, 0)
                for mistake, correction in issues:
                    # Only warn if it's likely user-facing text
                    if mistake in content.lower():
                        warnings.append(f"{filepath}: Possible spelling mistake: '{mistake}' should be '{correction}'")
        except Exception as e:
            errors.append(f"{filepath}: Error reading file: {str(e)}")

def main():
    """Main function to check all files."""
    exclude_dirs = {'venv', '__pycache__', '.git', 'node_modules', '.venv', 'tools'}
    exclude_files = {'check_syntax.py'}
    
    root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
    
    # Check Python files
    for py_file in root.rglob('*.py'):
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue
        if py_file.name in exclude_files:
            continue
        check_file(py_file)
    
    # Check JSON files
    for json_file in root.rglob('*.json'):
        if any(excluded in json_file.parts for excluded in exclude_dirs):
            continue
        check_file(json_file)
    
    # Check HTML files
    for html_file in root.rglob('*.html'):
        if any(excluded in html_file.parts for excluded in exclude_dirs):
            continue
        check_file(html_file)
    
    # Check JS/TS files
    for js_file in root.rglob('*.js'):
        if any(excluded in js_file.parts for excluded in exclude_dirs):
            continue
        check_file(js_file)
    
    for ts_file in root.rglob('*.ts'):
        if any(excluded in ts_file.parts for excluded in exclude_dirs):
            continue
        check_file(ts_file)
    
    for tsx_file in root.rglob('*.tsx'):
        if any(excluded in tsx_file.parts for excluded in exclude_dirs):
            continue
        check_file(tsx_file)
    
    # Print results
    if errors:
        print("=" * 80)
        print("SYNTAX ERRORS:")
        print("=" * 80)
        for error in errors:
            print(error)
        print()
    
    if warnings:
        print("=" * 80)
        print("GRAMMAR/SPELLING WARNINGS:")
        print("=" * 80)
        for warning in warnings:
            print(warning)
        print()
    
    if not errors and not warnings:
        print("[OK] No syntax or grammar errors found!")
    else:
        print(f"\nTotal: {len(errors)} errors, {len(warnings)} warnings")
        sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()

