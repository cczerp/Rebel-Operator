#!/usr/bin/env python3
"""
JavaScript Syntax Error Finder
===============================
Finds JavaScript syntax errors in HTML template files by checking for
unbalanced braces, parentheses, and brackets.

Usage:
    python tools/find_js_errors.py [file_or_directory]
    
    If no path specified, checks templates/ directory.
"""

import re
import sys
from pathlib import Path

def count_braces(js_code):
    """Count opening and closing braces."""
    open_braces = js_code.count('{')
    close_braces = js_code.count('}')
    return open_braces, close_braces

def count_parentheses(js_code):
    """Count opening and closing parentheses."""
    open_parens = js_code.count('(')
    close_parens = js_code.count(')')
    return open_parens, close_parens

def count_brackets(js_code):
    """Count opening and closing brackets."""
    open_brackets = js_code.count('[')
    close_brackets = js_code.count(']')
    return open_brackets, close_brackets

def find_scripts_in_file(filepath):
    """Extract all script blocks from an HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        return scripts, content
    except Exception as e:
        return [], f"Error reading file: {e}"

def check_file(filepath):
    """Check a single file for JavaScript syntax issues."""
    scripts, content = find_scripts_in_file(filepath)
    
    if not scripts:
        return None
    
    issues = []
    for i, script in enumerate(scripts):
        open_braces, close_braces = count_braces(script)
        open_parens, close_parens = count_parentheses(script)
        open_brackets, close_brackets = count_brackets(script)
        
        brace_diff = open_braces - close_braces
        paren_diff = open_parens - close_parens
        bracket_diff = open_brackets - close_brackets
        
        if brace_diff != 0 or paren_diff != 0 or bracket_diff != 0:
            # Find the line number where this script block starts
            script_start = content.find(f'<script')
            lines_before = content[:script_start].count('\n') + 1
            
            issue = {
                'file': str(filepath),
                'script_num': i + 1,
                'braces': (open_braces, close_braces, brace_diff),
                'parens': (open_parens, close_parens, paren_diff),
                'brackets': (open_brackets, close_brackets, bracket_diff),
                'start_line': lines_before,
                'script_preview': script[:200].replace('\n', ' ')
            }
            issues.append(issue)
    
    return issues if issues else None

def main():
    """Main execution."""
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    else:
        target = Path('templates')
    
    if not target.exists():
        print(f"Error: {target} does not exist")
        sys.exit(1)
    
    # Find HTML files
    if target.is_file():
        html_files = [target]
    else:
        html_files = list(target.rglob('*.html'))
    
    all_issues = []
    for html_file in html_files:
        issues = check_file(html_file)
        if issues:
            all_issues.extend(issues)
    
    if all_issues:
        print("JavaScript Syntax Issues Found:\n")
        print("=" * 80)
        for issue in all_issues:
            print(f"\nFile: {issue['file']}")
            print(f"Script block #{issue['script_num']}")
            print(f"Line ~{issue['start_line']}")
            
            brace_open, brace_close, brace_diff = issue['braces']
            paren_open, paren_close, paren_diff = issue['parens']
            bracket_open, bracket_close, bracket_diff = issue['brackets']
            
            if brace_diff != 0:
                print(f"Braces: {brace_open} open, {brace_close} close (diff: {brace_diff} {'missing closing' if brace_diff > 0 else 'extra closing'})")
            if paren_diff != 0:
                print(f"Parentheses: {paren_open} open, {paren_close} close (diff: {paren_diff} {'missing closing' if paren_diff > 0 else 'extra closing'})")
            if bracket_diff != 0:
                print(f"Brackets: {bracket_open} open, {bracket_close} close (diff: {bracket_diff} {'missing closing' if bracket_diff > 0 else 'extra closing'})")
            
            print(f"Preview: {issue['script_preview']}...")
            print("-" * 80)
        
        sys.exit(1)
    else:
        print("No JavaScript syntax issues found in template files.")
        sys.exit(0)

if __name__ == '__main__':
    main()

