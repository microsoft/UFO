#!/usr/bin/env python3
"""
Final MCP Configuration Verification
This script provides a comprehensive test of the MCP configuration system.
"""

import os
import sys
import yaml
from pathlib import Path

def print_status(message, status="info"):
    """Print a status message with color coding."""
    colors = {
        "success": "\033[92m✓",  # Green
        "error": "\033[91m✗",    # Red
        "warning": "\033[93m⚠",  # Yellow
        "info": "\033[94mℹ"      # Blue
    }
    reset = "\033[0m"
    
    color_code = colors.get(status, "\033[94mℹ")
    print(f"{color_code} {message}{reset}")

def verify_file_exists(file_path, description):
    """Verify that a file exists and return True if it does."""
    if os.path.exists(file_path):
        print_status(f"{description}: {file_path}", "success")
        return True
    else:
        print_status(f"{description} NOT FOUND: {file_path}", "error")
        return False

def verify_yaml_file(file_path, description):
    """Verify that a YAML file exists and is valid."""
    if not verify_file_exists(file_path, f"{description} (file check)"):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        print_status(f"{description} (YAML valid)", "success")
        return True
    except yaml.YAMLError as e:
        print_status(f"{description} (YAML invalid): {e}", "error")
        return False
    except Exception as e:
        print_status(f"{description} (read error): {e}", "error")
        return False

def main():
    """Main verification function."""
    print("=" * 60)
    print("MCP Configuration System Verification")
    print("=" * 60)
    
    # Get the base directory
    base_dir = Path(__file__).parent
    config_dir = base_dir / "ufo" / "config"
    instructions_dir = config_dir / "mcp_instructions"
    
    results = []
    
    # 1. Verify main configuration files
    print("\n1. Main Configuration Files:")
    print("-" * 30)
    
    servers_config = config_dir / "mcp_servers.yaml"
    launcher_config = config_dir / "mcp_launcher.yaml"
    config_manager = config_dir / "mcp_config.py"
    
    results.append(verify_yaml_file(servers_config, "MCP Servers Config"))
    results.append(verify_yaml_file(launcher_config, "MCP Launcher Config"))
    results.append(verify_file_exists(config_manager, "MCP Config Manager"))
    
    # 2. Verify instruction files
    print("\n2. MCP Instruction Files:")
    print("-" * 30)
    
    instruction_files = [
        "powerpoint.yaml",
        "word.yaml", 
        "excel.yaml",
        "web.yaml",
        "shell.yaml"
    ]
    
    for filename in instruction_files:
        file_path = instructions_dir / filename
        app_name = filename.replace('.yaml', '').capitalize()
        results.append(verify_yaml_file(file_path, f"{app_name} Instructions"))
    
    # 3. Verify launcher script
    print("\n3. Launcher Scripts:")
    print("-" * 30)
    
    ps_launcher = base_dir / "launch_mcp_servers.ps1"
    results.append(verify_file_exists(ps_launcher, "PowerShell Launcher"))
    
    # 4. Test configuration loading
    print("\n4. Configuration Loading Test:")
    print("-" * 30)
    
    try:
        # Test servers config structure
        with open(servers_config, 'r') as f:
            servers_data = yaml.safe_load(f)
        
        if 'mcp_servers' in servers_data:
            server_count = len(servers_data['mcp_servers'])
            print_status(f"Found {server_count} MCP servers configured", "success")
            
            for name, config in servers_data['mcp_servers'].items():
                enabled = config.get('enabled', True)
                endpoint = config.get('endpoint', 'N/A')
                status = "enabled" if enabled else "disabled"
                print_status(f"  {name}: {endpoint} ({status})", "info")
                
        else:
            print_status("No 'mcp_servers' section found in servers config", "error")
            results.append(False)
    
    except Exception as e:
        print_status(f"Error loading servers config: {e}", "error")
        results.append(False)
    
    # 5. Test launcher config structure
    try:
        with open(launcher_config, 'r') as f:
            launcher_data = yaml.safe_load(f)
        
        if 'startup_config' in launcher_data:
            startup_order = launcher_data['startup_config'].get('startup_order', [])
            print_status(f"Startup order defined for {len(startup_order)} servers", "success")
            results.append(True)
        else:
            print_status("No 'startup_config' section found in launcher config", "error")
            results.append(False)
    
    except Exception as e:
        print_status(f"Error loading launcher config: {e}", "error")
        results.append(False)
    
    # 6. Final summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print_status(f"Passed: {passed_tests}", "success")
    
    if failed_tests > 0:
        print_status(f"Failed: {failed_tests}", "error")
        print_status("Some components need attention", "warning")
    else:
        print_status("All tests passed!", "success")
        print_status("MCP Configuration System is ready!", "success")
    
    return failed_tests == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
