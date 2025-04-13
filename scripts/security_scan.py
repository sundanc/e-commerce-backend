#!/usr/bin/env python
"""
Security scanning script for e-commerce-backend

This script performs basic security checks on the codebase:
1. Checks for hardcoded secrets
2. Looks for unsafe dependencies 
3. Validates security configurations
"""
import os
import re
import sys
import argparse
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Define colors for output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Security scanner for e-commerce-backend")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency checks")
    parser.add_argument("--skip-secrets", action="store_true", help="Skip secret scanning")
    parser.add_argument("--skip-configs", action="store_true", help="Skip config validations")
    parser.add_argument("--json", type=str, help="Export results to JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    return parser.parse_args()

def print_header(title: str) -> None:
    """Print a formatted header"""
    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}{title}{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}")

def print_status(message: str, status: str, color: str) -> None:
    """Print a formatted status message"""
    print(f"  {message.ljust(60)} [{color}{status}{RESET}]")

def check_for_secrets(root_dir: Path, verbose: bool = False) -> List[Dict[str, Any]]:
    """Check for hardcoded secrets in the codebase using improved patterns"""
    issues = []
    
    # More comprehensive patterns with better coverage
    patterns = [
        # Classic assignment patterns (password="xyz")
        r'(?i)(password|secret|passwd|api_?key|token|auth|credential)["\'\s]*[:=]["\'\s]*([\'"][^\'"\$\{\}]+[\'"])',
        
        # Environment variable values
        r'(?i)os\.environ\[([\'"](PASSWORD|SECRET|API_?KEY|TOKEN)[\'"])\]\s*=\s*[\'"]([^\'"\$\{\}]+)[\'"]',
        
        # Config dict assignments
        r'(?i)(config|settings|options|cfg)\[[\'"](?:password|secret|api_?key|token)[\'"]]\s*=\s*[\'"]([^\'"\$\{\}]+)[\'"]',
        
        # Secrets in JSON-like structures
        r'(?i)[\'"](?:password|secret|api_?key|token)[\'"]\s*:\s*[\'"]([^\'"\$\{\}]+)[\'"]',
    ]
    
    # Files and directories to skip
    excluded_dirs = ['.git', '.venv', 'venv', 'env', '.pytest_cache', '__pycache__',
                     'alembic/versions', 'node_modules', 'dist', 'build']
    excluded_files = ['security_scan.py', 'test_data.py', '.env.example']
    
    skipped_files = []
    files_checked = 0
    
    for root, dirs, files in os.walk(root_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        for file in files:
            # Skip checking binary or non-relevant files
            if not file.endswith(('.py', '.js', '.ts', '.yml', '.yaml', '.sh', '.json', '.env', '.ini', '.conf', '.md')):
                continue
                
            if file in excluded_files:
                continue
                
            file_path = os.path.join(root, file)
            files_checked += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Also check .env files differently
                    if file.endswith('.env'):
                        env_lines = content.splitlines()
                        for i, line in enumerate(env_lines):
                            # Skip comments and empty lines
                            if line.strip().startswith('#') or not line.strip():
                                continue
                            
                            # Check if this looks like a real secret (not a placeholder)
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                
                                # Skip template/placeholder values
                                if (any(placeholder in value.lower() for placeholder in 
                                        ['example', 'placeholder', 'changeme', 'your']) or
                                    value.startswith(('$', '{', '%'))):
                                    continue
                                
                                if any(k.lower() in key.lower() for k in 
                                      ['password', 'secret', 'key', 'token', 'auth']):
                                    issues.append({
                                        'file': file_path,
                                        'line': i + 1,
                                        'match': line,
                                        'type': 'env_var'
                                    })

                    # Apply the regex patterns
                    for pattern in patterns:
                        for match in re.finditer(pattern, content, re.MULTILINE):
                            # Get the line number
                            line = content[:match.start()].count('\n') + 1
                            line_content = content.split('\n')[line-1]
                            
                            # Skip comments
                            if line_content.strip().startswith(('#', '//', '/*', '*')):
                                continue
                                
                            # Skip if appears to be a placeholder
                            match_text = match.group(0)
                            if (any(placeholder in match_text.lower() for placeholder in 
                                    ['example', 'placeholder', 'changeme', '<your', 'your-'])):
                                continue
                                
                            issues.append({
                                'file': file_path,
                                'line': line,
                                'match': match_text,
                                'type': 'hardcoded_secret'
                            })
            
            except UnicodeDecodeError:
                skipped_files.append(file_path)
                if verbose:
                    print_status(f"Skipped binary/unreadable file: {file_path}", "SKIPPED", YELLOW)
                continue
    
    if verbose:
        print_status(f"Files checked: {files_checked}", "INFO", GREEN)
        print_status(f"Files skipped due to encoding: {len(skipped_files)}", "INFO", YELLOW)
    
    return issues

def check_dependencies(verbose: bool = False) -> Tuple[bool, List[str], List[Dict[str, str]]]:
    """Check for vulnerable dependencies with better error handling"""
    issues = []
    messages = []
    
    # First check if pip is available
    try:
        pip_version = subprocess.run(
            ["pip", "--version"],
            capture_output=True, 
            text=True
        )
        if pip_version.returncode != 0:
            messages.append("Could not determine pip version")
            return False, messages, issues
            
    except FileNotFoundError:
        messages.append("pip command not found. Make sure it's installed and in your PATH")
        return False, messages, issues
    
    # Check if safety is installed
    safety_installed = False
    try:
        safety_check = subprocess.run(
            ["safety", "--version"],
            capture_output=True,
            text=True
        )
        safety_installed = safety_check.returncode == 0
    except FileNotFoundError:
        messages.append("Safety is not installed. Run 'pip install safety' to enable vulnerability scanning.")
        safety_installed = False
    
    # Get list of installed packages
    try:
        result = subprocess.run(
            ["pip", "list", "--format=freeze"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            messages.append(f"Error running pip list: {result.stderr}")
            return False, messages, issues
            
        requirements = result.stdout.strip()
        
        # Only run safety if installed
        if safety_installed:
            try:
                safety_result = subprocess.run(
                    ["safety", "check", "--stdin"], 
                    input=requirements,
                    capture_output=True, 
                    text=True
                )
                
                if safety_result.returncode != 0:
                    # Parse safety output
                    output_lines = safety_result.stdout.strip().split('\n')
                    
                    for line in output_lines:
                        if "| VULNERABLE" in line:
                            parts = line.split("|")
                            if len(parts) >= 3:
                                package = parts[0].strip()
                                vulnerability = parts[2].strip()
                                issues.append({
                                    "package": package,
                                    "vulnerability": vulnerability
                                })
                    
                    if issues:
                        messages.append(f"Found {len(issues)} vulnerable dependencies")
                    else:
                        messages.append("Vulnerability scan completed, output format unrecognized")
                else:
                    messages.append("No known vulnerabilities found")
                    return True, messages, issues
                    
            except Exception as e:
                messages.append(f"Error running safety check: {str(e)}")
                return False, messages, issues
        else:
            # Use pip-audit as a backup if available
            try:
                audit_result = subprocess.run(
                    ["pip-audit"], 
                    capture_output=True,
                    text=True
                )
                
                if "No known vulnerabilities found" in audit_result.stdout:
                    messages.append("No known vulnerabilities found (using pip-audit)")
                    return True, messages, issues
                else:
                    messages.append("Consider installing 'safety' or 'pip-audit' for better vulnerability scanning")
            except FileNotFoundError:
                pass
    
    except Exception as e:
        messages.append(f"Unexpected error checking dependencies: {str(e)}")
        return False, messages, issues
    
    return len(issues) == 0, messages, issues

def find_framework_files(root_dir: Path) -> List[Path]:
    """Find files likely to contain web framework configuration"""
    framework_files = []
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # Skip large files for performance
                if os.path.getsize(file_path) > 1_000_000:  # 1MB
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Look for imports of common web frameworks
                        if re.search(r'(from|import)\s+(fastapi|flask|starlette|django)', content):
                            # Look for app creation patterns
                            if re.search(r'(app\s*=|application\s*=|\s+app\s*=)', content):
                                framework_files.append(Path(file_path))
                                
                except (UnicodeDecodeError, PermissionError):
                    continue
    
    return framework_files

def check_security_configs(root_dir: Path, verbose: bool = False) -> List[Dict[str, str]]:
    """Check for proper security configurations with improved checks"""
    issues = []
    
    # Check for .env in .gitignore
    gitignore_path = root_dir / '.gitignore'
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
            # Use regex to handle more cases
            if not re.search(r'(^|\n)\s*\.env\b', content) and not re.search(r'(^|\n)\s*\*\.env', content):
                issues.append({
                    'type': 'configuration',
                    'message': '.env files should be added to .gitignore',
                    'file': str(gitignore_path),
                    'severity': 'high'
                })
                if verbose:
                    print_status(".env not found in .gitignore", "ISSUE", RED)
    else:
        issues.append({
            'type': 'configuration',
            'message': '.gitignore file not found. Create one and add .env to it.',
            'severity': 'medium'
        })
        if verbose:
            print_status(".gitignore file not found", "ISSUE", YELLOW)
    
    # Look for web framework files that might have CORS configuration
    framework_files = find_framework_files(root_dir)
    
    cors_checked = False
    for file_path in framework_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check CORS configuration
            if 'CORSMiddleware' in content or 'CORS' in content:
                cors_checked = True
                if ('allow_origins=["*"]' in content or "allow_origins=['*']" in content or 
                    'allow_origins=*' in content) and 'production' not in content:
                    issues.append({
                        'type': 'configuration',
                        'message': f'CORS wildcard origin (*) found without production check in {file_path.name}',
                        'file': str(file_path),
                        'severity': 'medium'
                    })
                    if verbose:
                        print_status(f"CORS allows all origins (*) in {file_path.name}", "ISSUE", YELLOW)
    
    if not cors_checked and verbose:
        print_status("Could not locate CORS configuration", "WARNING", YELLOW)
    
    # Check Docker user configuration with improved logic
    dockerfile_path = root_dir / 'Dockerfile'
    if dockerfile_path.exists():
        with open(dockerfile_path, 'r') as f:
            content = f.read()
            
            # Check for explicit root user
            if 'USER root' in content:
                issues.append({
                    'type': 'configuration',
                    'message': 'Dockerfile explicitly sets USER to root, which is a security risk',
                    'file': str(dockerfile_path),
                    'severity': 'high'
                })
                if verbose:
                    print_status("Dockerfile explicitly runs as root", "ISSUE", RED)
            
            # Check if no USER directive at all
            elif 'USER ' not in content:
                issues.append({
                    'type': 'configuration',
                    'message': 'Dockerfile does not specify a non-root USER, which is a security risk',
                    'file': str(dockerfile_path),
                    'severity': 'medium'
                })
                if verbose:
                    print_status("Dockerfile doesn't specify a non-root user", "ISSUE", YELLOW)
    
    # Security headers check
    for file_path in framework_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check for security headers in the file
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
                'Content-Security-Policy': True,  # Any value is good
                'X-XSS-Protection': ['1', '1; mode=block']
            }
            
            missing_headers = []
            for header, expected in security_headers.items():
                if header not in content:
                    missing_headers.append(header)
            
            if missing_headers and 'app' in content and ('response' in content or 'Response' in content):
                issues.append({
                    'type': 'configuration',
                    'message': f'Missing security headers in {file_path.name}: {", ".join(missing_headers)}',
                    'file': str(file_path),
                    'severity': 'low'
                })
                if verbose:
                    print_status(f"Missing security headers in {file_path.name}", "ISSUE", YELLOW)
    
    return issues

def main():
    """Main function to run security checks"""
    args = parse_args()
    verbose = args.verbose
    
    print_header("E-commerce Backend Security Scanner")
    print(f"Running security scan with: verbose={verbose}")
    
    # Get the repository root directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    all_issues = {
        "secrets": [],
        "dependencies": [],
        "configurations": []
    }
    
    # Check for hardcoded secrets
    if not args.skip_secrets:
        print_header("Checking for Hardcoded Secrets")
        secret_issues = check_for_secrets(repo_root, verbose)
        all_issues["secrets"] = secret_issues
        
        if secret_issues:
            print_status(f"Found {len(secret_issues)} potential hardcoded secrets", "ALERT", RED)
            for issue in secret_issues:
                print_status(
                    f"{issue['file']}:{issue['line']} - {issue['match'][:60]}{'...' if len(issue['match']) > 60 else ''}",
                    "SECRET", 
                    RED
                )
        else:
            print_status("No hardcoded secrets found", "PASSED", GREEN)
    
    # Check for vulnerable dependencies
    if not args.skip_deps:
        print_header("Checking for Vulnerable Dependencies")
        deps_safe, deps_messages, deps_issues = check_dependencies(verbose)
        all_issues["dependencies"] = deps_issues
        
        for msg in deps_messages:
            status = "PASSED" if deps_safe else "WARNING"
            color = GREEN if deps_safe else YELLOW
            print_status(msg, status, color)
            
        if deps_issues:
            for issue in deps_issues:
                print_status(
                    f"Vulnerable package: {issue.get('package', 'unknown')} - {issue.get('vulnerability', 'See details')}",
                    "VULN",
                    RED
                )
    
    # Check security configurations
    if not args.skip_configs:
        print_header("Checking Security Configurations")
        config_issues = check_security_configs(repo_root, verbose)
        all_issues["configurations"] = config_issues
        
        if config_issues:
            print_status(f"Found {len(config_issues)} security configuration issues", "WARNING", YELLOW)
            for issue in config_issues:
                print_status(
                    f"{issue.get('file', 'N/A')}: {issue['message']}",
                    issue['severity'].upper(), 
                    RED if issue['severity'] == 'high' else YELLOW
                )
        else:
            print_status("No security configuration issues found", "PASSED", GREEN)
    
    # Export to JSON if requested
    if args.json:
        try:
            with open(args.json, 'w') as f:
                json.dump(all_issues, f, indent=2)
            print_status(f"Results exported to {args.json}", "INFO", GREEN)
        except Exception as e:
            print_status(f"Failed to export results: {str(e)}", "ERROR", RED)
    
    # Summary
    print_header("Security Scan Summary")
    total_issues = len(all_issues["secrets"]) + len(all_issues["dependencies"]) + len(all_issues["configurations"])
    
    if total_issues > 0:
        print_status(f"Total issues found: {total_issues}", "WARNING", RED)
        print_status("Run this script regularly to identify security issues", "TIP", YELLOW)
        print_status("Use --verbose for more detailed output", "TIP", YELLOW)
        sys.exit(1)
    else:
        print_status("No security issues found!", "SUCCESS", GREEN)
        print_status("Keep up the good security practices", "TIP", GREEN)
        sys.exit(0)

if __name__ == "__main__":
    main()
