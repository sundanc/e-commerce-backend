#!/usr/bin/env python
"""
Comprehensive security audit tool for the e-commerce backend

This script performs deeper security checks:
1. JWT configuration vulnerabilities
2. SQL Injection risks
3. CSRF vulnerabilities
4. Weak password hashing
5. Insecure redirects
6. Unsafe deserialization
7. Missing access controls
"""
import os
import re
import sys
import ast
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

# ANSI colors for output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Comprehensive security audit for e-commerce backend")
    parser.add_argument("--detailed", "-d", action="store_true", help="Show detailed findings")
    parser.add_argument("--output", "-o", type=str, help="Write results to file")
    return parser.parse_args()

def print_header(title: str) -> None:
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}{title}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}")

def print_finding(title: str, message: str, severity: str, file: str = None, line: int = None) -> None:
    """Print a security finding with proper formatting"""
    severity_color = {
        "critical": RED,
        "high": RED,
        "medium": YELLOW,
        "low": GREEN,
        "info": BLUE
    }.get(severity.lower(), BLUE)
    
    location = f"{file}:{line}" if file and line else file if file else "N/A"
    
    print(f"\n{BOLD}{severity_color}[{severity.upper()}]{RESET} {BOLD}{title}{RESET}")
    print(f"  {severity_color}Location:{RESET} {location}")
    print(f"  {severity_color}Description:{RESET} {message}")

def check_jwt_config() -> List[Dict[str, Any]]:
    """Check for JWT configuration vulnerabilities"""
    issues = []
    jwt_files = []
    
    # Find files related to JWT 
    for root, _, files in os.walk("app"):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'jwt' in content.lower() or 'token' in content.lower():
                        jwt_files.append((file_path, content))
            except Exception:
                continue
    
    # Check for common JWT security issues
    for file_path, content in jwt_files:
        # Check for missing algorithm verification
        if 'decode(' in content and 'algorithms=' not in content:
            issues.append({
                "title": "JWT Missing Algorithm Verification",
                "description": "JWT decoding without specifying algorithms parameter. "
                              "This could allow algorithm switching attacks.",
                "file": file_path,
                "line": content.split('\n').index(next(line for line in content.split('\n') if 'decode(' in line)) + 1,
                "severity": "high"
            })
        
        # Check for weak algorithms (HS256 is acceptable but not ideal for high-security)
        if "HS256" in content and "ALGORITHM" in content:
            issues.append({
                "title": "Consider Stronger JWT Algorithm",
                "description": "Using HS256 for JWT. Consider RS256 or ES256 for better security in production.",
                "file": file_path,
                "severity": "low"
            })
        
        # Check for short expiration times
        expiration_match = re.search(r'ACCESS_TOKEN_EXPIRE_MINUTES\s*=\s*(\d+)', content)
        if expiration_match:
            expiration = int(expiration_match.group(1))
            if expiration > 60:
                issues.append({
                    "title": "Long JWT Expiration Time",
                    "description": f"JWT tokens expire after {expiration} minutes. "
                                  "Consider reducing to 15-60 minutes for sensitive operations.",
                    "file": file_path,
                    "severity": "medium" if expiration > 180 else "low"
                })
    
    return issues

def check_sql_injection() -> List[Dict[str, Any]]:
    """Check for potential SQL injection vulnerabilities"""
    issues = []
    
    for root, _, files in os.walk("app"):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check for raw SQL execution
                    raw_sql_lines = []
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'execute(' in line or 'text(' in line or '.sql(' in line:
                            if any(var in line for var in ['%s', '?', 'format(', 'f"', "f'"]):
                                raw_sql_lines.append((i+1, line))
                    
                    if raw_sql_lines:
                        for line_num, line_content in raw_sql_lines:
                            issues.append({
                                "title": "Potential SQL Injection",
                                "description": "Raw SQL execution with string formatting or variables. "
                                              "Ensure proper parameterization.",
                                "file": file_path,
                                "line": line_num,
                                "severity": "high",
                                "code": line_content.strip()
                            })
            except Exception:
                continue
    
    return issues

def check_csrf_protection() -> List[Dict[str, Any]]:
    """Check for CSRF vulnerabilities"""
    issues = []
    has_csrf_protection = False
    
    # Check main app file and middleware for CSRF protection
    main_py = Path("app/main.py")
    if main_py.exists():
        with open(main_py, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'csrf' in content.lower():
                has_csrf_protection = True
    
    # Check if forms are used in the application
    forms_used = False
    for root, _, files in os.walk("app"):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'form' in content.lower() and 'post' in content.lower():
                        forms_used = True
                        break
            except Exception:
                continue
    
    # Only flag CSRF if forms are used but no protection is enabled
    if forms_used and not has_csrf_protection:
        issues.append({
            "title": "Missing CSRF Protection",
            "description": "The application appears to use forms but has no CSRF protection middleware. "
                          "Consider adding CSRF protection if handling form submissions.",
            "file": "app/main.py",
            "severity": "medium"
        })
    
    return issues

def check_password_hashing() -> List[Dict[str, Any]]:
    """Check for weak password hashing"""
    issues = []
    
    security_files = []
    for root, _, files in os.walk("app"):
        for file in files:
            if not file.endswith('.py'):
                continue
            
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'password' in content.lower() and ('hash' in content.lower() or 'crypt' in content.lower()):
                        security_files.append((file_path, content))
            except Exception:
                continue
    
    for file_path, content in security_files:
        # Check for weak hashing algorithms (MD5, SHA1)
        if re.search(r'(md5|sha1)\(', content, re.IGNORECASE):
            issues.append({
                "title": "Weak Password Hashing Algorithm",
                "description": "Using MD5 or SHA1 for password hashing. These algorithms are not secure for passwords.",
                "file": file_path, 
                "severity": "critical"
            })
        
        # Check for proper bcrypt usage
        if 'bcrypt' in content and 'rounds' not in content and 'work_factor' not in content:
            # If using passlib CryptContext, check for default values
            if 'CryptContext' in content:
                # Try to find if the rounds/work_factor is set
                if not re.search(r'schemes=\[\"bcrypt\"\].*deprecated=\"auto\"', content):
                    issues.append({
                        "title": "Check Bcrypt Configuration",
                        "description": "Using bcrypt but couldn't verify rounds parameter. Ensure cost factor is appropriate (10+).",
                        "file": file_path,
                        "severity": "low" 
                    })
    
    return issues

def check_insecure_redirects() -> List[Dict[str, Any]]:
    """Check for insecure redirects"""
    issues = []
    
    for root, _, files in os.walk("app"):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines):
                        # Check for redirects using user input
                        if 'redirect' in line.lower() and any(param in line for param in ['request.', 'params.', 'query_params', 'body_params']):
                            issues.append({
                                "title": "Potential Insecure Redirect",
                                "description": "Redirect using user-supplied data could lead to open redirect vulnerabilities.",
                                "file": file_path,
                                "line": i+1,
                                "severity": "medium",
                                "code": line.strip()
                            })
            except Exception:
                continue
    
    return issues

def check_access_controls() -> List[Dict[str, Any]]:
    """Check for missing or weak access controls"""
    issues = []
    
    # Find all API route files
    route_files = []
    for root, _, files in os.walk("app/api/routes"):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            route_files.append(file_path)
    
    # Check each route file for endpoints missing access controls
    for file_path in route_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                has_get_current_user = 'get_current_user' in content
                endpoints = []
                
                # Extract endpoints
                for i, line in enumerate(lines):
                    if '@router.' in line:
                        endpoint_type = re.search(r'@router\.(get|post|put|delete|patch)', line)
                        if endpoint_type:
                            endpoint = {
                                'type': endpoint_type.group(1),
                                'line': i+1,
                                'has_auth': False
                            }
                            
                            # Look at function definition for this endpoint
                            for j in range(i+1, min(i+20, len(lines))):
                                if 'def ' in lines[j]:
                                    # Check if this endpoint has auth dependency
                                    if 'current_user' in lines[j] or 'Depends(get_current_user)' in lines[j]:
                                        endpoint['has_auth'] = True
                                    endpoints.append(endpoint)
                                    break
                
                # Flag endpoints that might be missing auth
                for endpoint in endpoints:
                    if not endpoint['has_auth'] and endpoint['type'] in ['post', 'put', 'delete', 'patch']:
                        issues.append({
                            "title": "Potential Missing Access Control",
                            "description": f"Endpoint using {endpoint['type'].upper()} does not appear to have user authentication checks.",
                            "file": file_path,
                            "line": endpoint['line'],
                            "severity": "high"
                        })
        except Exception:
            continue
    
    return issues

def check_rate_limiting() -> List[Dict[str, Any]]:
    """Check for rate limiting on sensitive endpoints"""
    issues = []
    
    # Check if rate limiting is implemented
    has_rate_limiting = False
    rate_limit_endpoints = set()
    
    # Check for rate limiting middleware or decorators
    for root, _, files in os.walk("app"):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'rate_limit' in content.lower() or 'ratelimit' in content.lower() or 'throttle' in content.lower():
                        has_rate_limiting = True
                        
                        # Extract endpoints with rate limiting
                        for line in content.split('\n'):
                            if '@' in line and 'limit' in line.lower():
                                next_lines = content.split('\n')[content.split('\n').index(line)+1:content.split('\n').index(line)+5]
                                for next_line in next_lines:
                                    if 'def ' in next_line:
                                        func_match = re.search(r'def\s+(\w+)', next_line)
                                        if func_match:
                                            rate_limit_endpoints.add(func_match.group(1))
                                        break
            except Exception:
                continue
    
    # Check auth endpoints for rate limiting
    auth_file = Path("app/api/routes/auth.py")
    if auth_file.exists() and has_rate_limiting:
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
            auth_functions = ['login', 'register', 'reset_password']
            
            for func in auth_functions:
                func_pattern = r'def\s+' + func
                if re.search(func_pattern, content) and not any(func in endpoint for endpoint in rate_limit_endpoints):
                    issues.append({
                        "title": "Missing Rate Limiting on Auth Endpoint",
                        "description": f"The {func} endpoint does not appear to have rate limiting. "
                                      "This could allow brute force attacks.",
                        "file": str(auth_file),
                        "severity": "medium"
                    })
    
    # Check if rate limiting is missing entirely
    if not has_rate_limiting:
        issues.append({
            "title": "No Rate Limiting Detected",
            "description": "The application does not appear to implement rate limiting. "
                          "Consider adding rate limiting to protect sensitive endpoints.",
            "severity": "medium"
        })
    
    return issues

def check_session_management() -> List[Dict[str, Any]]:
    """Check for session management issues"""
    issues = []
    
    jwt_settings_found = False
    
    # Check for JWT expiration times
    config_file = Path("app/core/config.py")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
            jwt_settings_found = True
            
            # Check if JWT rotation is implemented
            refresh_token = 'refresh_token' in content.lower()
            if not refresh_token:
                issues.append({
                    "title": "No JWT Refresh Mechanism",
                    "description": "No JWT refresh token mechanism detected. Long-lived access tokens "
                                  "are less secure than using short-lived access tokens with refresh tokens.",
                    "file": str(config_file),
                    "severity": "low"
                })
    
    # Check for session database logging/tracking
    session_tracking = False
    for root, _, files in os.walk("app/models"):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if ('session' in content.lower() or 'token' in content.lower()) and 'class' in content:
                        session_tracking = True
                        break
            except Exception:
                continue
    
    if jwt_settings_found and not session_tracking:
        issues.append({
            "title": "No Session Tracking",
            "description": "JWT authentication is used but no session/token tracking detected. "
                          "Consider tracking active tokens to enable forced logout and token revocation.",
            "severity": "medium"
        })
    
    return issues

def check_exception_handling() -> List[Dict[str, Any]]:
    """Check for exception handling issues"""
    issues = []
    
    # Look for exception handling in main app file
    main_py = Path("app/main.py")
    has_global_exception_handler = False
    
    if main_py.exists():
        with open(main_py, 'r', encoding='utf-8') as f:
            content = f.read()
            has_global_exception_handler = 'exception_handler' in content or '@app.exception_handler' in content
    
    if not has_global_exception_handler:
        issues.append({
            "title": "Missing Global Exception Handler",
            "description": "No global exception handler found. This could leak sensitive error information "
                          "to users if exceptions are not properly caught.",
            "file": "app/main.py",
            "severity": "medium"
        })
    
    # Check for try-except blocks that might suppress errors
    for root, _, files in os.walk("app"):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    in_try_block = False
                    try_line = 0
                    
                    for i, line in enumerate(lines):
                        line = line.strip()
                        
                        if line.startswith('try:'):
                            in_try_block = True
                            try_line = i+1
                        elif line.startswith('except') and in_try_block:
                            # Check for bare except
                            if line == 'except:' or 'except Exception:' in line:
                                # Look for logging in the except block
                                has_logging = False
                                j = i + 1
                                indent = len(lines[i]) - len(lines[i].lstrip())
                                
                                while j < len(lines) and (j == i + 1 or len(lines[j]) - len(lines[j].lstrip()) > indent):
                                    if 'log' in lines[j].lower() or 'print' in lines[j].lower():
                                        has_logging = True
                                        break
                                    j += 1
                                
                                if not has_logging:
                                    issues.append({
                                        "title": "Broad Exception Handling Without Logging",
                                        "description": "Catching broad exceptions without logging can hide errors and security issues.",
                                        "file": file_path,
                                        "line": i+1,
                                        "severity": "low"
                                    })
                            
                            in_try_block = False
            except Exception:
                continue
    
    return issues

def check_env_variable_usage() -> List[Dict[str, Any]]:
    """Check for hard-coded configuration that should be in environment variables"""
    issues = []
    
    env_variables_found = set()
    env_example = Path(".env.example")
    
    # Get expected environment variables
    expected_env_vars = set()
    if env_example.exists():
        with open(env_example, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    var_name = line.split('=')[0].strip()
                    expected_env_vars.add(var_name)
    
    # Find actual environment variable usage
    for root, _, files in os.walk("app"):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Find os.environ usage
                    env_vars = re.findall(r'os\.environ\.get\([\'"]([^\'"]+)[\'"]', content)
                    env_vars.extend(re.findall(r'os\.environ\[[\'"]([^\'"]+)[\'"]', content))
                    
                    # Find settings usage (common pattern)
                    settings_vars = re.findall(r'settings\.([A-Z_]+)', content)
                    
                    env_variables_found.update(env_vars)
                    env_variables_found.update(settings_vars)
            except Exception:
                continue
    
    # Check for hard-coded values that should be environment variables
    common_config_names = ['secret', 'api_key', 'password', 'token', 'connection', 'url']
    
    for root, _, files in os.walk("app"):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            if 'test' in file_path.lower():
                continue  # Skip test files
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines):
                        for config_name in common_config_names:
                            pattern = r'[\'"]([^\'"\s]+)[\'"]'
                            if config_name in line.lower() and '=' in line and re.search(pattern, line):
                                value_match = re.search(pattern, line)
                                value = value_match.group(1)
                                
                                # Skip if it's likely a placeholder or example
                                if (any(x in value.lower() for x in ['example', 'placeholder', 'your']) or 
                                    len(value) < 8 or  # Too short to be a real secret
                                    '{' in value):  # Template variable
                                    continue
                                
                                issues.append({
                                    "title": "Potential Hard-coded Configuration",
                                    "description": f"Found potentially hard-coded {config_name} that should be in environment variables.",
                                    "file": file_path,
                                    "line": i+1,
                                    "severity": "medium",
                                })
            except Exception:
                continue
    
    # Check for expected env vars that are not found in code
    missing_vars = expected_env_vars - env_variables_found
    if missing_vars:
        issues.append({
            "title": "Unused Environment Variables",
            "description": f"Environment variables defined in .env.example but not used in code: {', '.join(missing_vars)}",
            "file": ".env.example",
            "severity": "low"
        })
    
    return issues

def main():
    """Main function to run security audit"""
    args = parse_args()
    print_header("E-commerce Backend Security Audit")
    
    all_issues = []
    audit_functions = [
        ("JWT Configuration", check_jwt_config),
        ("SQL Injection Risks", check_sql_injection),
        ("CSRF Vulnerabilities", check_csrf_protection),
        ("Password Hashing", check_password_hashing),
        ("Insecure Redirects", check_insecure_redirects),
        ("Access Controls", check_access_controls),
        ("Rate Limiting", check_rate_limiting),
        ("Session Management", check_session_management),
        ("Exception Handling", check_exception_handling),
        ("Environment Variables", check_env_variable_usage)
    ]
    
    for name, func in audit_functions:
        print(f"Checking {name}...")
        issues = func()
        if issues:
            print(f"  Found {len(issues)} issues")
            all_issues.extend(issues)
        else:
            print(f"  {GREEN}No issues found{RESET}")
    
    # Sort issues by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "info").lower(), 99))
    
    # Print findings
    print_header("Security Findings")
    
    if not all_issues:
        print(f"{GREEN}No security issues found. Great job!{RESET}")
    else:
        for issue in all_issues:
            print_finding(
                issue["title"],
                issue["description"],
                issue["severity"],
                issue.get("file"),
                issue.get("line")
            )
    
    # Summary
    critical = sum(1 for i in all_issues if i.get("severity") == "critical")
    high = sum(1 for i in all_issues if i.get("severity") == "high")
    medium = sum(1 for i in all_issues if i.get("severity") == "medium")
    low = sum(1 for i in all_issues if i.get("severity") == "low")
    
    print_header("Security Audit Summary")
    print(f"  {RED}Critical:{RESET} {critical}")
    print(f"  {RED}High:{RESET} {high}")
    print(f"  {YELLOW}Medium:{RESET} {medium}")
    print(f"  {GREEN}Low:{RESET} {low}")
    print(f"  {BLUE}Total Issues:{RESET} {len(all_issues)}")
    
    if args.output:
        try:
            with open(args.output, 'w') as f:
                for issue in all_issues:
                    f.write(f"{issue['severity'].upper()}: {issue['title']}\n")
                    f.write(f"File: {issue.get('file', 'N/A')}")
                    if issue.get('line'):
                        f.write(f":{issue['line']}")
                    f.write(f"\n{issue['description']}\n\n")
            print(f"\nResults written to {args.output}")
        except Exception as e:
            print(f"Error writing to output file: {e}")
    
    # Return exit code based on findings
    if critical > 0:
        sys.exit(3)  # Critical issues
    elif high > 0:
        sys.exit(2)  # High issues
    elif medium > 0:
        sys.exit(1)  # Medium issues
    else:
        sys.exit(0)  # No significant issues

if __name__ == "__main__":
    main()
