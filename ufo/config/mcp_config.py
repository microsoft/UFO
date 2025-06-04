"""
MCP Configuration Manager
This module handles loading and managing MCP (Model Context Protocol) configurations for UFO2.
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""
    name: str
    description: str
    endpoint: str
    instructions_path: str
    timeout: int = 30
    retry_count: int = 3
    health_check_endpoint: str = "/health"
    tools_endpoint: str = "/tools"
    execute_endpoint: str = "/execute_tool"
    enabled: bool = True

@dataclass
class MCPGlobalConfig:
    """Global MCP configuration settings."""
    connection_timeout: int = 10
    read_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    log_requests: bool = True
    log_responses: bool = True
    log_level: str = "INFO"
    fallback_to_ui: bool = True
    ignore_connection_errors: bool = False
    connection_pool_size: int = 10
    keep_alive: bool = True
    verify_ssl: bool = True
    allowed_hosts: List[str] = None

class MCPConfigManager:
    """Manager for MCP configuration loading and validation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the MCP configuration manager.
        
        Args:
            config_path: Path to the MCP servers configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.servers: Dict[str, MCPServerConfig] = {}
        self.global_config: Optional[MCPGlobalConfig] = None
        self.app_mapping: Dict[str, str] = {}
        
        if config_path:
            self.load_configuration(config_path)
    
    def load_configuration(self, config_path: str) -> bool:
        """
        Load MCP configuration from YAML file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            True if configuration was loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(config_path):
                self.logger.warning(f"MCP configuration file not found: {config_path}")
                return False
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Load server configurations
            mcp_servers = config_data.get("mcp_servers", {})
            for namespace, server_config in mcp_servers.items():
                self.servers[namespace] = MCPServerConfig(
                    name=server_config.get("name", f"{namespace.title()} MCP Server"),
                    description=server_config.get("description", f"MCP server for {namespace}"),
                    endpoint=server_config["endpoint"],
                    instructions_path=server_config["instructions_path"],
                    timeout=server_config.get("timeout", 30),
                    retry_count=server_config.get("retry_count", 3),
                    health_check_endpoint=server_config.get("health_check_endpoint", "/health"),
                    tools_endpoint=server_config.get("tools_endpoint", "/tools"),
                    execute_endpoint=server_config.get("execute_endpoint", "/execute_tool"),
                    enabled=server_config.get("enabled", True)
                )
            
            # Load global configuration
            global_config_data = config_data.get("global_config", {})
            self.global_config = MCPGlobalConfig(
                connection_timeout=global_config_data.get("connection_timeout", 10),
                read_timeout=global_config_data.get("read_timeout", 30),
                max_retries=global_config_data.get("max_retries", 3),
                retry_delay=global_config_data.get("retry_delay", 1.0),
                log_requests=global_config_data.get("log_requests", True),
                log_responses=global_config_data.get("log_responses", True),
                log_level=global_config_data.get("log_level", "INFO"),
                fallback_to_ui=global_config_data.get("fallback_to_ui", True),
                ignore_connection_errors=global_config_data.get("ignore_connection_errors", False),
                connection_pool_size=global_config_data.get("connection_pool_size", 10),
                keep_alive=global_config_data.get("keep_alive", True),
                verify_ssl=global_config_data.get("verify_ssl", True),
                allowed_hosts=global_config_data.get("allowed_hosts", ["localhost", "127.0.0.1"])
            )
            
            # Load application mapping
            self.app_mapping = config_data.get("app_mapping", {})
            
            self.logger.info(f"Successfully loaded MCP configuration from {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load MCP configuration: {e}")
            return False
    
    def get_server_config(self, namespace: str) -> Optional[MCPServerConfig]:
        """
        Get configuration for a specific MCP server.
        
        Args:
            namespace: Server namespace (e.g., 'powerpoint', 'word')
            
        Returns:
            Server configuration or None if not found
        """
        return self.servers.get(namespace)
    
    def get_server_for_app(self, app_name: str) -> Optional[MCPServerConfig]:
        """
        Get MCP server configuration for a specific application.
        
        Args:
            app_name: Application name (e.g., 'POWERPNT.EXE')
            
        Returns:
            Server configuration or None if not found
        """
        namespace = self.app_mapping.get(app_name)
        if namespace:
            return self.get_server_config(namespace)
        return None
    
    def get_enabled_servers(self) -> Dict[str, MCPServerConfig]:
        """
        Get all enabled MCP servers.
        
        Returns:
            Dictionary of enabled server configurations
        """
        return {name: config for name, config in self.servers.items() if config.enabled}
    
    def get_server_endpoints(self) -> Dict[str, str]:
        """
        Get all server endpoints.
        
        Returns:
            Dictionary mapping server names to endpoints
        """
        return {name: config.endpoint for name, config in self.servers.items() if config.enabled}
    
    def validate_configuration(self) -> List[str]:
        """
        Validate the MCP configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for required fields
        for namespace, config in self.servers.items():
            if not config.endpoint:
                errors.append(f"Server '{namespace}' missing endpoint")
            
            if not config.instructions_path:
                errors.append(f"Server '{namespace}' missing instructions_path")
            
            # Check if instructions file exists
            if config.instructions_path and not os.path.exists(config.instructions_path):
                errors.append(f"Instructions file not found for '{namespace}': {config.instructions_path}")
        
        # Check for duplicate endpoints
        endpoints = [config.endpoint for config in self.servers.values()]
        if len(endpoints) != len(set(endpoints)):
            errors.append("Duplicate endpoints found in server configuration")
        
        return errors
    
    def create_default_config(self, output_path: str) -> bool:
        """
        Create a default MCP configuration file.
        
        Args:
            output_path: Path where to save the default configuration
            
        Returns:
            True if file was created successfully, False otherwise
        """
        try:
            default_config = {
                "mcp_servers": {
                    "powerpoint": {
                        "name": "PowerPoint MCP Server",
                        "description": "MCP server for Microsoft PowerPoint automation and control",
                        "endpoint": "http://localhost:8001",
                        "instructions_path": "ufo/config/mcp_instructions/powerpoint.yaml",
                        "timeout": 30,
                        "retry_count": 3,
                        "enabled": True
                    },
                    "word": {
                        "name": "Word MCP Server",
                        "description": "MCP server for Microsoft Word automation and document manipulation",
                        "endpoint": "http://localhost:8002",
                        "instructions_path": "ufo/config/mcp_instructions/word.yaml",
                        "timeout": 30,
                        "retry_count": 3,
                        "enabled": True
                    },
                    "excel": {
                        "name": "Excel MCP Server",
                        "description": "MCP server for Microsoft Excel automation and spreadsheet manipulation",
                        "endpoint": "http://localhost:8003",
                        "instructions_path": "ufo/config/mcp_instructions/excel.yaml",
                        "timeout": 30,
                        "retry_count": 3,
                        "enabled": True
                    },
                    "web": {
                        "name": "Web MCP Server",
                        "description": "MCP server for web browser automation and web page interaction",
                        "endpoint": "http://localhost:8004",
                        "instructions_path": "ufo/config/mcp_instructions/web.yaml",
                        "timeout": 30,
                        "retry_count": 3,
                        "enabled": True
                    },
                    "shell": {
                        "name": "Shell MCP Server",
                        "description": "MCP server for shell command execution and system operations",
                        "endpoint": "http://localhost:8005",
                        "instructions_path": "ufo/config/mcp_instructions/shell.yaml",
                        "timeout": 30,
                        "retry_count": 3,
                        "enabled": True
                    }
                },
                "global_config": {
                    "connection_timeout": 10,
                    "read_timeout": 30,
                    "max_retries": 3,
                    "retry_delay": 1.0,
                    "log_requests": True,
                    "log_responses": True,
                    "log_level": "INFO",
                    "fallback_to_ui": True,
                    "ignore_connection_errors": False,
                    "allowed_hosts": ["localhost", "127.0.0.1"]
                },
                "app_mapping": {
                    "POWERPNT.EXE": "powerpoint",
                    "WINWORD.EXE": "word",
                    "EXCEL.EXE": "excel",
                    "powerpoint": "powerpoint",
                    "word": "word",
                    "excel": "excel",
                    "msedge.exe": "web",
                    "chrome.exe": "web",
                    "firefox.exe": "web",
                    "cmd.exe": "shell",
                    "powershell.exe": "shell",
                    "pwsh.exe": "shell"
                }
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Created default MCP configuration at {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create default configuration: {e}")
            return False

# Global instance for easy access
_config_manager = None

def get_mcp_config_manager(config_path: Optional[str] = None) -> MCPConfigManager:
    """
    Get the global MCP configuration manager instance.
    
    Args:
        config_path: Path to configuration file (only used on first call)
        
    Returns:
        MCPConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = MCPConfigManager(config_path)
    return _config_manager

def load_mcp_config(config_path: str) -> bool:
    """
    Load MCP configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        True if configuration was loaded successfully
    """
    manager = get_mcp_config_manager()
    return manager.load_configuration(config_path)
