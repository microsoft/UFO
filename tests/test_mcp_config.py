#!/usr/bin/env python3
"""
Test script for MCP configuration system
"""

import os
import sys
import yaml
from pathlib import Path

# Add the UFO directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ufo'))

def test_mcp_config_loading():
    """Test loading of MCP configuration files"""
    print("Testing MCP Configuration System")
    print("=" * 50)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(base_dir, "ufo", "config")
    
    # Test 1: Check if MCP servers config exists
    servers_config_path = os.path.join(config_dir, "mcp_servers.yaml")
    print(f"1. Checking MCP servers config: {servers_config_path}")
    
    if os.path.exists(servers_config_path):
        print("   ✓ MCP servers config file exists")
        try:
            with open(servers_config_path, 'r') as f:
                servers_config = yaml.safe_load(f)
            print("   ✓ MCP servers config is valid YAML")
            
            # Check structure
            if 'mcp_servers' in servers_config:
                print(f"   ✓ Found {len(servers_config['mcp_servers'])} MCP servers configured")
                for namespace, config in servers_config['mcp_servers'].items():
                    status = "enabled" if config.get('enabled', True) else "disabled"
                    print(f"     - {namespace}: {config['endpoint']} ({status})")
            else:
                print("   ✗ No 'mcp_servers' section found")
                
        except Exception as e:
            print(f"   ✗ Error loading MCP servers config: {e}")
    else:
        print("   ✗ MCP servers config file not found")
    
    # Test 2: Check MCP launcher config
    launcher_config_path = os.path.join(config_dir, "mcp_launcher.yaml")
    print(f"\n2. Checking MCP launcher config: {launcher_config_path}")
    
    if os.path.exists(launcher_config_path):
        print("   ✓ MCP launcher config file exists")
        try:
            with open(launcher_config_path, 'r') as f:
                launcher_config = yaml.safe_load(f)
            print("   ✓ MCP launcher config is valid YAML")
            
            if 'launcher' in launcher_config:
                startup_config = launcher_config['launcher'].get('startup', {})
                print(f"   ✓ Startup timeout: {startup_config.get('timeout_seconds', 'default')}s")
                print(f"   ✓ Health check interval: {startup_config.get('health_check_interval_seconds', 'default')}s")
            
        except Exception as e:
            print(f"   ✗ Error loading MCP launcher config: {e}")
    else:
        print("   ✗ MCP launcher config file not found")
    
    # Test 3: Check instruction files
    instructions_dir = os.path.join(config_dir, "mcp_instructions")
    print(f"\n3. Checking MCP instruction files: {instructions_dir}")
    
    if os.path.exists(instructions_dir):
        print("   ✓ MCP instructions directory exists")
        instruction_files = [f for f in os.listdir(instructions_dir) if f.endswith('.yaml')]
        print(f"   ✓ Found {len(instruction_files)} instruction files:")
        
        for file in instruction_files:
            file_path = os.path.join(instructions_dir, file)
            try:
                with open(file_path, 'r') as f:
                    instructions = yaml.safe_load(f)
                print(f"     - {file}: ✓ valid")
            except Exception as e:
                print(f"     - {file}: ✗ error ({e})")
    else:
        print("   ✗ MCP instructions directory not found")
    
    # Test 4: Check PowerShell launcher script
    launcher_script_path = os.path.join(base_dir, "launch_mcp_servers.ps1")
    print(f"\n4. Checking PowerShell launcher script: {launcher_script_path}")
    
    if os.path.exists(launcher_script_path):
        print("   ✓ PowerShell launcher script exists")
        with open(launcher_script_path, 'r') as f:
            content = f.read()
            if 'Start-MCPServers' in content:
                print("   ✓ Start-MCPServers function found")
            if 'Stop-MCPServers' in content:
                print("   ✓ Stop-MCPServers function found")
            if 'Test-MCPServerHealth' in content:
                print("   ✓ Test-MCPServerHealth function found")
    else:
        print("   ✗ PowerShell launcher script not found")

def test_mcp_config_manager():
    """Test the MCP configuration manager"""
    print("\n\nTesting MCP Configuration Manager")
    print("=" * 50)
    
    try:
        # Import the config manager
        from ufo.config.mcp_config import MCPConfigManager
        
        print("1. Creating MCP Configuration Manager...")
        config_manager = MCPConfigManager()
        print("   ✓ MCPConfigManager imported and initialized successfully")
        
        print("\n2. Loading MCP server configurations...")
        servers_config = config_manager.load_servers_config()
        
        if servers_config:
            print("   ✓ Servers configuration loaded successfully")
            print(f"   ✓ Found {len(servers_config.mcp_servers)} configured servers")
            
            # Test individual server configurations
            for namespace, server in servers_config.mcp_servers.items():
                print(f"     - {namespace}: {server.endpoint} ({'enabled' if server.enabled else 'disabled'})")
        else:
            print("   ✗ Failed to load servers configuration")
        
        print("\n3. Loading MCP launcher configuration...")
        launcher_config = config_manager.load_launcher_config()
        
        if launcher_config:
            print("   ✓ Launcher configuration loaded successfully")
            print(f"   ✓ Startup timeout: {launcher_config.launcher.startup.timeout_seconds}s")
            print(f"   ✓ Health check interval: {launcher_config.launcher.startup.health_check_interval_seconds}s")
        else:
            print("   ✗ Failed to load launcher configuration")
            
    except ImportError as e:
        print(f"   ✗ Failed to import MCPConfigManager: {e}")
        print("   Note: This might be expected if the module path is not correctly set up")
    except Exception as e:
        print(f"   ✗ Error testing MCP Configuration Manager: {e}")

def test_computer_integration():
    """Test MCP integration with Computer class"""
    print("\n\nTesting Computer Class MCP Integration")
    print("=" * 50)
    
    try:
        # Import the Computer class
        from ufo.cs.computer import Computer
        
        print("1. Creating Computer instance...")
        computer = Computer("TestComputer")
        print("   ✓ Computer instance created successfully")
        
        print("\n2. Checking MCP servers initialization...")
        if hasattr(computer, 'mcp_servers') and computer.mcp_servers:
            print(f"   ✓ MCP servers initialized: {list(computer.mcp_servers.keys())}")
            
            for namespace, server_info in computer.mcp_servers.items():
                print(f"     - {namespace}: {server_info.get('endpoint', 'N/A')} ({server_info.get('status', 'N/A')})")
        else:
            print("   ✗ No MCP servers found or initialization failed")
        
        print("\n3. Checking MCP instructions cache...")
        if hasattr(computer, 'mcp_instructions') and computer.mcp_instructions:
            print(f"   ✓ MCP instructions loaded: {list(computer.mcp_instructions.keys())}")
        else:
            print("   ✗ No MCP instructions found in cache")
            
    except ImportError as e:
        print(f"   ✗ Failed to import Computer class: {e}")
    except Exception as e:
        print(f"   ✗ Error testing Computer MCP integration: {e}")

if __name__ == "__main__":
    test_mcp_config_loading()
    test_mcp_config_manager()
    test_computer_integration()
    
    print("\n\nTesting Complete!")
    print("=" * 50)
