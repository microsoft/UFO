#!/usr/bin/env python3
"""
Simple MCP Integration Test
"""

import sys
import os

# Add the UFO2 root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_mcp_config_files():
    """Test that MCP configuration files are valid"""
    print("Testing MCP Configuration Files")
    print("=" * 40)
    
    import yaml
    
    # Test mcp_servers.yaml
    servers_path = os.path.join(current_dir, "ufo", "config", "mcp_servers.yaml")
    try:
        with open(servers_path, 'r') as f:
            servers_config = yaml.safe_load(f)
        print(f"✓ mcp_servers.yaml: Valid YAML")
        print(f"  Servers: {list(servers_config['mcp_servers'].keys())}")
    except Exception as e:
        print(f"✗ mcp_servers.yaml: Error - {e}")
    
    # Test mcp_launcher.yaml
    launcher_path = os.path.join(current_dir, "ufo", "config", "mcp_launcher.yaml")
    try:
        with open(launcher_path, 'r') as f:
            launcher_config = yaml.safe_load(f)
        print(f"✓ mcp_launcher.yaml: Valid YAML")
        print(f"  Sections: {list(launcher_config.keys())}")
    except Exception as e:
        print(f"✗ mcp_launcher.yaml: Error - {e}")

def test_mcp_config_manager():
    """Test the MCP configuration manager"""
    print("\nTesting MCP Configuration Manager")
    print("=" * 40)
    
    try:
        from ufo.config.mcp_config import MCPConfigManager, MCPServerConfig
        print("✓ MCPConfigManager imported successfully")
        
        config_manager = MCPConfigManager()
        print("✓ MCPConfigManager instantiated")
        
        # Test loading servers configuration
        servers_config = config_manager.load_servers_config()
        if servers_config:
            print(f"✓ Servers config loaded: {len(servers_config.mcp_servers)} servers")
            for name, server in servers_config.mcp_servers.items():
                print(f"  - {name}: {server.endpoint} ({'enabled' if server.enabled else 'disabled'})")
        else:
            print("✗ Failed to load servers configuration")
        
    except Exception as e:
        print(f"✗ Error testing MCP Config Manager: {e}")

def test_computer_mcp_integration():
    """Test MCP integration with Computer class"""
    print("\nTesting Computer MCP Integration")
    print("=" * 40)
    
    try:
        from ufo.cs.computer import Computer
        print("✓ Computer class imported successfully")
        
        computer = Computer("TestComputer")
        print("✓ Computer instance created")
        
        # Check MCP servers
        if hasattr(computer, 'mcp_servers') and computer.mcp_servers:
            print(f"✓ MCP servers initialized: {list(computer.mcp_servers.keys())}")
            for namespace, server_info in computer.mcp_servers.items():
                endpoint = server_info.get('endpoint', 'N/A')
                status = server_info.get('status', 'N/A')
                print(f"  - {namespace}: {endpoint} ({status})")
        else:
            print("✗ No MCP servers initialized")
        
        # Check MCP instructions
        if hasattr(computer, 'mcp_instructions') and computer.mcp_instructions:
            print(f"✓ MCP instructions loaded: {list(computer.mcp_instructions.keys())}")
        else:
            print("✗ No MCP instructions loaded")
            
    except Exception as e:
        print(f"✗ Error testing Computer MCP integration: {e}")

if __name__ == "__main__":
    test_mcp_config_files()
    test_mcp_config_manager()
    test_computer_mcp_integration()
    
    print("\nTest Complete!")
