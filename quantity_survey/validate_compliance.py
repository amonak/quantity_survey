#!/usr/bin/env python3
"""
Melon v15 Compliance Validation Script
Validates the Quantity Survey application for full v15 compliance
"""

import os
import json
import re
from pathlib import Path


def validate_compliance():
    """Main validation function"""
    
    print("🔍 Melon v15 Compliance Validation Report")
    print("=" * 50)
    
    base_path = Path("/media/thenyonyo/Alpha/PJ/entmonak/copilot/quantity_survey/quantity_survey")
    
    # Check overall structure
    check_folder_structure(base_path)
    
    # Check doctypes
    check_doctypes(base_path / "quantity_surveying" / "doctype")
    
    # Check reports
    check_reports(base_path / "quantity_surveying" / "report")
    
    # Check Python files
    check_python_compliance(base_path)
    
    # Check JavaScript files
    check_javascript_compliance(base_path)
    
    print("\n✅ Compliance Validation Complete")


def check_folder_structure(base_path):
    """Check if all required folders exist"""
    required_folders = [
        "quantity_surveying",
        "quantity_surveying/doctype", 
        "quantity_surveying/report",
        "quantity_surveying/dashboard_chart",
        "quantity_surveying/number_card",
        "public",
        "public/js",
        "public/css",
        "utils",
        "collaboration",
        "ai",
        "bim"
    ]
    
    print("\n📁 Folder Structure Check:")
    for folder in required_folders:
        folder_path = base_path / folder
        status = "✅" if folder_path.exists() else "❌"
        print(f"  {status} {folder}")


def check_doctypes(doctype_path):
    """Check if all doctypes have required files"""
    print("\n📋 DocType Files Check:")
    
    if not doctype_path.exists():
        print("  ❌ DocType folder not found")
        return
    
    required_files = ["*.json", "*.py", "__init__.py"]
    optional_files = ["*.js", "test_*.py", "test_*.js"]
    
    for doctype_dir in doctype_path.iterdir():
        if doctype_dir.is_dir():
            print(f"\n  📄 {doctype_dir.name}:")
            
            # Check required files
            json_files = list(doctype_dir.glob("*.json"))
            py_files = list(doctype_dir.glob("*.py"))
            init_file = doctype_dir / "__init__.py"
            
            print(f"    {'✅' if json_files else '❌'} JSON definition")
            print(f"    {'✅' if py_files else '❌'} Python controller") 
            print(f"    {'✅' if init_file.exists() else '❌'} __init__.py")
            
            # Check optional files
            js_files = list(doctype_dir.glob("*.js"))
            test_py_files = list(doctype_dir.glob("test_*.py"))
            
            print(f"    {'✅' if js_files else '⚠️'} JavaScript (optional)")
            print(f"    {'✅' if test_py_files else '⚠️'} Tests (optional)")


def check_reports(report_path):
    """Check if all reports have required files"""
    print("\n📊 Report Files Check:")
    
    if not report_path.exists():
        print("  ❌ Report folder not found")
        return
    
    for report_dir in report_path.iterdir():
        if report_dir.is_dir():
            print(f"\n  📈 {report_dir.name}:")
            
            json_file = report_dir / f"{report_dir.name}.json"
            py_file = report_dir / f"{report_dir.name}.py"  
            js_file = report_dir / f"{report_dir.name}.js"
            
            print(f"    {'✅' if json_file.exists() else '❌'} JSON definition")
            print(f"    {'✅' if py_file.exists() else '❌'} Python query")
            print(f"    {'✅' if js_file.exists() else '⚠️'} JavaScript (optional)")


def check_python_compliance(base_path):
    """Check Python files for v15 compliance"""
    print("\n🐍 Python Code Compliance:")
    
    python_files = list(base_path.glob("**/*.py"))
    total_files = len(python_files)
    compliant_files = 0
    
    issues = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            file_issues = check_python_file_compliance(content, py_file)
            if not file_issues:
                compliant_files += 1
            else:
                issues.extend(file_issues)
                
        except Exception as e:
            issues.append(f"❌ Error reading {py_file}: {str(e)}")
    
    print(f"  📊 Compliance Rate: {compliant_files}/{total_files} files ({compliant_files/total_files*100:.1f}%)")
    
    if issues:
        print("  ⚠️ Issues Found:")
        for issue in issues[:10]:  # Show first 10 issues
            print(f"    {issue}")
        if len(issues) > 10:
            print(f"    ... and {len(issues)-10} more issues")


def check_python_file_compliance(content, file_path):
    """Check individual Python file for compliance issues"""
    issues = []
    
    # Check for deprecated imports
    if "from __future__ import unicode_literals" in content:
        issues.append(f"❌ {file_path}: Contains deprecated unicode_literals import")
    
    # Check for proper melon imports
    if "import melon" in content or "from melon" in content:
        # Good - uses proper melon imports
        pass
    
    # Check for f-strings without translation
    f_string_pattern = r'f["\'][^"\']*\{[^}]*\}[^"\']*["\']'
    if re.search(f_string_pattern, content) and "_(" not in content:
        issues.append(f"⚠️ {file_path}: F-strings found, ensure translations use _()")
    
    # Check for proper whitelist decorators
    if "@melon.whitelist" in content:
        # Good - uses whitelist decorator
        pass
    
    return issues


def check_javascript_compliance(base_path):
    """Check JavaScript files for v15 compliance"""
    print("\n🌐 JavaScript Code Compliance:")
    
    js_files = list(base_path.glob("**/*.js"))
    total_files = len(js_files)
    compliant_files = 0
    
    issues = []
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            file_issues = check_javascript_file_compliance(content, js_file)
            if not file_issues:
                compliant_files += 1
            else:
                issues.extend(file_issues)
                
        except Exception as e:
            issues.append(f"❌ Error reading {js_file}: {str(e)}")
    
    print(f"  📊 Compliance Rate: {compliant_files}/{total_files} files ({compliant_files/total_files*100:.1f}%)")
    
    if issues:
        print("  ⚠️ Issues Found:")
        for issue in issues[:10]:  # Show first 10 issues
            print(f"    {issue}")
        if len(issues) > 10:
            print(f"    ... and {len(issues)-10} more issues")


def check_javascript_file_compliance(content, file_path):
    """Check individual JavaScript file for compliance issues"""
    issues = []
    
    # Check for proper melon form syntax
    if "melon.ui.form.on" in content:
        # Good - uses proper form syntax
        pass
    
    # Check for proper translation usage
    if "__(" in content:
        # Good - uses translation function
        pass
    
    # Check for proper melon.call usage
    if "$.ajax" in content or "$.post" in content:
        issues.append(f"⚠️ {file_path}: Consider using melon.call() instead of direct jQuery AJAX")
    
    return issues


if __name__ == "__main__":
    validate_compliance()
