#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Base MCP Server
Provides the common functionality for all UFO MCP servers.
"""

import os
import sys
import yaml
from typing import Dict, Any
from fastmcp import FastMCP

# Add UFO2 to the path
ufo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ufo_root not in sys.path:
    sys.path.insert(0, ufo_root)

from ufo.automator.app_apis.factory import MCPReceiverFactory
from ufo.utils import print_with_color

class BaseMCPServer:
    """
    Base class for all UFO MCP servers.
    """
    def __init__(self, app_namespace: str, server_name: str = None, port: int = None):
        """
        Initialize the base MCP server with enhanced diagnostics.
        :param app_namespace: The application namespace (word, excel, powerpoint, web, shell)
        :param server_name: Optional custom server name
        :param port: Optional port number for HTTP mode
        """
        self.app_namespace = app_namespace
        self.server_name = server_name or f"ufo-{app_namespace}"
        self.port = port
        
        # Initialize FastMCP
        self.mcp = FastMCP(self.server_name)
        
        # Load instructions and create receiver
        self.instructions = self._load_instructions()
        self.receiver = self._create_receiver()
        
        # Register diagnostic tools first
        self._register_diagnostic_tools()
        
        # Register application tools
        self._register_tools()
        
        # Print diagnostic information
        self._print_startup_diagnostics()
      
    def _load_instructions(self) -> Dict[str, Any]:
        """
        Load instructions from YAML file.
        :return: Instructions dictionary
        """
        try:
            instructions_path = os.path.join(
                os.path.dirname(__file__),
                "..", "config", "mcp_instructions", f"{self.app_namespace}.yaml"
            )
            if os.path.exists(instructions_path):
                with open(instructions_path, 'r') as f:
                    instructions = yaml.safe_load(f)
                print_with_color(f"Loaded instructions for {self.app_namespace}", "green")
                return instructions
            else:
                print_with_color(f"Instructions file not found: {instructions_path}", "yellow")
                return {"tools": []}
        except Exception as e:
            print_with_color(f"Error loading instructions: {e}", "red")
            return {"tools": []}
    def _create_receiver(self):
        """
        Create the application receiver using the factory.
        :return: The receiver instance
        """
        try:
            factory = MCPReceiverFactory()
            
            # Map app namespace to app_root_name and process_name for COM applications
            app_root_name = None
            process_name = None
            
            if self.app_namespace.lower() == "word":
                app_root_name = "WINWORD.EXE"
                process_name = "WINWORD.EXE"
            elif self.app_namespace.lower() == "excel":
                app_root_name = "EXCEL.EXE"
                process_name = "EXCEL.EXE"
            elif self.app_namespace.lower() == "powerpoint":
                app_root_name = "POWERPNT.EXE"
                process_name = "POWERPNT.EXE"
            elif self.app_namespace.lower() == "web":
                app_root_name = "msedge.exe"  # Default to Edge, could be configurable
            # For shell, no app_root_name or process_name needed
            
            receiver = factory.create_receiver(self.app_namespace, app_root_name, process_name)
            if receiver:
                print_with_color(f"Created {self.app_namespace} receiver", "green")
                return receiver
            else:
                print_with_color(f"Failed to create {self.app_namespace} receiver", "red")
                return None
        except Exception as e:
            print_with_color(f"Error creating receiver: {e}", "red")
            return None
    
    def _register_tools(self):
        """
        Register MCP tools based on the loaded instructions.
        """
        if not self.instructions or "tools" not in self.instructions:
            print_with_color(f"No tools found in instructions for {self.app_namespace}", "yellow")
            return
        
        for tool_def in self.instructions["tools"]:
            tool_name = tool_def.get("name")
            if tool_name:
                self._register_tool(tool_def)
    def _register_tool(self, tool_def: Dict[str, Any]):
        """
        Register a single MCP tool with proper parameter handling.
        :param tool_def: Tool definition from instructions
        """
        tool_name = tool_def["name"]
        description = tool_def.get("description", f"Execute {tool_name}")
        parameters = tool_def.get("parameters", [])
        
        print_with_color(f"Attempting to register {tool_name} with {len(parameters)} parameters", "cyan")
        
        # Try modern parameter registration first, fallback to simple registration
        try:
            self._register_tool_with_parameters(tool_name, description, parameters)
            print_with_color(f"✓ Successfully registered {tool_name} with parameters", "green")
        except Exception as e:
            print_with_color(f"✗ Parameter registration failed for {tool_name}: {e}", "red")
            print_with_color(f"  Falling back to simple registration for {tool_name}", "yellow")
            self._register_simple_tool(tool_name, description)    
    def _register_tool_with_parameters(self, tool_name: str, description: str, parameters: list):
        """Register tool with proper FastMCP parameter handling."""
        print_with_color(f"  🔧 _register_tool_with_parameters called for {tool_name}", "blue")
        
        try:
            from typing import Optional, Union, Any
            import inspect
            
            # If no parameters, create simple function
            if not parameters:
                print_with_color(f"  📝 {tool_name} has no parameters, creating simple function", "blue")
                def tool_function() -> Dict[str, Any]:
                    """Dynamic tool function with no parameters."""
                    return self._execute_tool(tool_name, {})
                
                tool_function.__name__ = tool_name
                tool_function.__doc__ = description
                self.mcp.tool()(tool_function)
                print_with_color(f"Registered tool: {tool_name} with no parameters", "green")
                return

            print_with_color(f"  📋 Processing {len(parameters)} parameters for {tool_name}: {[p.get('name') for p in parameters]}", "blue")

            # Create parameter objects for function signature
            sig_params = []
            param_names = []
            
            for i, param in enumerate(parameters):
                param_name = param.get("name")
                param_type = param.get("type", "string")
                param_required = param.get("required", False)
                param_default = param.get("default")
                
                print_with_color(f"    - Parameter {i+1}: {param_name} (type: {param_type}, required: {param_required}, default: {param_default})", "cyan")
                
                if not param_name:
                    raise ValueError(f"Parameter {i} missing name")
                
                param_names.append(param_name)
                
                # Map YAML types to Python types
                type_mapping = {
                    "string": str,
                    "integer": int,
                    "number": float,
                    "boolean": bool,
                    "array": list,
                    "object": dict
                }
                
                python_type = type_mapping.get(param_type, str)
                print_with_color(f"      → Mapped to Python type: {python_type.__name__}", "cyan")
                
                # Create inspect.Parameter for the signature
                if param_required and param_default is None:
                    # Required parameter
                    sig_param = inspect.Parameter(
                        param_name,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=python_type
                    )
                    print_with_color(f"      → Created required parameter: {param_name}", "cyan")
                else:
                    # Optional parameter with default
                    default_val = param_default if param_default is not None else None
                    sig_param = inspect.Parameter(
                        param_name,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        default=default_val,
                        annotation=Optional[python_type]
                    )
                    print_with_color(f"      → Created optional parameter: {param_name} = {default_val}", "cyan")
                
                sig_params.append(sig_param)
            
            print_with_color(f"  🏗️ Building dynamic function for {tool_name}", "blue")
            
            # Create the function body dynamically
            def create_dynamic_function():
                # Create a closure that captures the parameters
                def tool_function(*args, **kwargs) -> Dict[str, Any]:
                    """Dynamic tool function with proper parameters."""
                    try:
                        # Build the arguments dictionary from both positional and keyword args
                        processed_args = {}
                        
                        # Handle positional arguments
                        for i, arg_value in enumerate(args):
                            if i < len(param_names):
                                processed_args[param_names[i]] = arg_value
                        
                        # Handle keyword arguments
                        for param_name in param_names:
                            if param_name in kwargs:
                                processed_args[param_name] = kwargs[param_name]
                        
                        # Validate required parameters
                        for param in parameters:
                            param_name = param.get("name")
                            param_required = param.get("required", False)
                            param_default = param.get("default")
                            
                            if param_required and param_default is None:
                                if param_name not in processed_args:
                                    return {
                                        "success": False,
                                        "error": f"Missing required parameter: {param_name}",
                                        "tool_name": tool_name
                                    }
                            elif param_name not in processed_args and param_default is not None:
                                processed_args[param_name] = param_default
                        
                        return self._execute_tool(tool_name, processed_args)
                        
                    except Exception as e:
                        return {
                            "success": False,
                            "error": f"Parameter processing error: {str(e)}",
                            "tool_name": tool_name
                        }
                  # Set function metadata
                tool_function.__name__ = tool_name
                tool_function.__doc__ = description
                
                # Create and set the dynamic signature
                signature = inspect.Signature(sig_params)
                tool_function.__signature__ = signature
                
                # Create __annotations__ for Pydantic type validation
                annotations = {}
                for param in sig_params:
                    annotations[param.name] = param.annotation
                # Add return type annotation
                annotations['return'] = Dict[str, Any]
                tool_function.__annotations__ = annotations
                
                print_with_color(f"    🏷️ Set annotations: {annotations}", "cyan")
                
                return tool_function
            print_with_color(f"  ⚙️ Creating and registering dynamic function", "blue")
            
            # Create and register the function
            try:
                dynamic_function = create_dynamic_function()
                print_with_color(f"  ✅ Dynamic function created successfully", "blue")
            except Exception as e:
                print_with_color(f"  ❌ Dynamic function creation failed: {e}", "red")
                raise Exception(f"Dynamic function creation failed: {e}")
            
            try:
                self.mcp.tool()(dynamic_function)
                print_with_color(f"  ✅ Function registered with FastMCP successfully", "blue")
            except Exception as e:
                print_with_color(f"  ❌ FastMCP registration failed: {e}", "red")
                raise Exception(f"FastMCP registration failed: {e}")
            
            print_with_color(f"Registered tool: {tool_name} with {len(parameters)} parameters: {param_names}", "green")
            
        except Exception as e:
            import traceback
            print_with_color(f"  💥 Full error traceback:", "red")
            print_with_color(f"  {traceback.format_exc()}", "red")
            raise Exception(f"Parameter registration failed: {e}")

    def _register_simple_tool(self, tool_name: str, description: str):
        """Fallback simple tool registration."""
        def simple_tool_function(request: str = "{}") -> Dict[str, Any]:
            """Simple tool function fallback."""
            try:
                if isinstance(request, str):
                    import json
                    tool_args = json.loads(request) if request.strip() else {}
                else:
                    tool_args = request if isinstance(request, dict) else {}
            except json.JSONDecodeError:
                tool_args = {"raw_input": request}
            
            return self._execute_tool(tool_name, tool_args)
        
        simple_tool_function.__name__ = tool_name
        simple_tool_function.__doc__ = description
        
        try:
            self.mcp.tool()(simple_tool_function)
            print_with_color(f"Registered simple tool: {tool_name}", "yellow")
        except Exception as e:
            print_with_color(f"Failed to register simple tool {tool_name}: {e}", "red")
    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool using the receiver with enhanced error handling.
        :param tool_name: Name of the tool to execute
        :param tool_args: Arguments for the tool
        :return: Tool execution result
        """
        if not self.receiver:
            return {
                "success": False,
                "error": f"No receiver available for {self.app_namespace}",
                "tool_name": tool_name,
                "namespace": self.app_namespace
            }
        
        try:
            print_with_color(f"Executing {tool_name} with args: {tool_args}", "cyan")
            
            # Ensure receiver has the required method
            if not hasattr(self.receiver, 'execute_tool'):
                # Try alternative method names
                if hasattr(self.receiver, 'execute'):
                    result = self.receiver.execute(tool_name, tool_args)
                elif hasattr(self.receiver, 'run_tool'):
                    result = self.receiver.run_tool(tool_name, tool_args)
                else:
                    return {
                        "success": False,
                        "error": f"Receiver does not have execute_tool method",
                        "tool_name": tool_name,
                        "available_methods": [m for m in dir(self.receiver) if not m.startswith('_')]
                    }
            else:
                result = self.receiver.execute_tool(tool_name, tool_args)
            
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                result = {
                    "success": True,
                    "result": result,
                    "tool_name": tool_name
                }
            
            print_with_color(f"Tool {tool_name} executed successfully: {result.get('success', 'unknown')}", "green")
            return result
            
        except AttributeError as e:
            error_msg = f"Method not found: {str(e)}"
            print_with_color(f"AttributeError executing {tool_name}: {error_msg}", "red")
            return {
                "success": False,
                "error": error_msg,
                "tool_name": tool_name,
                "receiver_type": type(self.receiver).__name__
            }
        except Exception as e:
            error_msg = f"Error executing tool: {str(e)}"
            print_with_color(f"Error executing {tool_name}: {error_msg}", "red")
            return {
                "success": False,
                "error": error_msg,
                "tool_name": tool_name,
                "namespace": self.app_namespace,
                "exception_type": type(e).__name__
            }
    def run(self):
        """
        Start the MCP server with proper transport configuration.
        """
        print_with_color(f"Starting {self.app_namespace} MCP server: {self.server_name}", "blue")
        
        if self.instructions:
            print_with_color(f"Loaded {len(self.instructions.get('tools', []))} tools", "green")
        
        try:
            if self.port:
                # Configure for SSE transport
                print_with_color(f"Running SSE server on port {self.port}", "blue")
                
                try:
                    # Try FastMCP's SSE transport
                    self.mcp.run(transport="sse", port=self.port)
                except Exception as sse_error:
                    print_with_color(f"SSE transport failed: {sse_error}", "yellow")
            else:
                # Run via stdio (standard MCP protocol)
                self.mcp.run()
        except KeyboardInterrupt:
            print_with_color(f"\nShutting down {self.app_namespace} MCP server", "yellow")
        except Exception as e:
            print_with_color(f"Error running server: {e}", "red")
            raise
    
    @property
    def app(self):
        """
        Get the FastMCP app instance.
        :return: FastMCP app
        """
        return self.mcp
    
    def get_tools(self):
        """
        Get list of registered tools.
        :return: List of tool names
        """
        # Try different ways to access FastMCP tools
        if hasattr(self.mcp, '_tools'):
            return list(self.mcp._tools.keys())
        elif hasattr(self.mcp, 'tools'):
            return list(self.mcp.tools.keys())
        elif hasattr(self.mcp, '_handlers'):
            # Look for tool handlers
            tools = []
            for handler_type, handlers in self.mcp._handlers.items():
                if 'tool' in handler_type.lower():
                    tools.extend(handlers.keys())
            return tools
        else:
            # Fall back to instruction-based tool list
            if self.instructions and "tools" in self.instructions:
                return [tool.get("name") for tool in self.instructions["tools"] if tool.get("name")]
            return []

    def _register_diagnostic_tools(self):
        """Register diagnostic tools for debugging MCP issues."""
        
        def diagnose_server() -> Dict[str, Any]:
            """Diagnostic tool to check server status."""
            return {
                "success": True,
                "server_name": self.server_name,
                "app_namespace": self.app_namespace,
                "receiver_available": self.receiver is not None,
                "receiver_type": type(self.receiver).__name__ if self.receiver else None,
                "instructions_loaded": bool(self.instructions),
                "tools_count": len(self.instructions.get('tools', [])),
                "registered_tools": self.get_tools()
            }
        
        def test_receiver() -> Dict[str, Any]:
            """Test receiver functionality."""
            if not self.receiver:
                return {"success": False, "error": "No receiver available"}
            
            return {
                "success": True,
                "receiver_methods": [m for m in dir(self.receiver) if not m.startswith('_')],
                "has_execute_tool": hasattr(self.receiver, 'execute_tool'),
                "receiver_class": self.receiver.__class__.__name__
            }
        
        # Register diagnostic tools
        self.mcp.tool()(diagnose_server)
        self.mcp.tool()(test_receiver)
        print_with_color("Registered diagnostic tools: diagnose_server, test_receiver", "blue")

    def _print_startup_diagnostics(self):
        """Print diagnostic information at startup."""
        print_with_color(f"=== {self.app_namespace.upper()} MCP Server Diagnostics ===", "blue")
        print_with_color(f"Server Name: {self.server_name}", "white")
        print_with_color(f"Port: {self.port if self.port else 'stdio'}", "white")
        print_with_color(f"Instructions Loaded: {'✓' if self.instructions else '✗'}", "green" if self.instructions else "red")
        print_with_color(f"Receiver Created: {'✓' if self.receiver else '✗'}", "green" if self.receiver else "red")
        
        if self.receiver:
            print_with_color(f"Receiver Type: {type(self.receiver).__name__}", "white")
            print_with_color(f"Has execute_tool: {'✓' if hasattr(self.receiver, 'execute_tool') else '✗'}", 
                             "green" if hasattr(self.receiver, 'execute_tool') else "yellow")
        
        tools = self.get_tools()
        print_with_color(f"Registered Tools: {len(tools)}", "white")
        for tool in tools:
            print_with_color(f"  - {tool}", "cyan")
        
        print_with_color("=" * 50, "blue")
        
def create_mcp_server(app_namespace: str, server_name: str = None, port: int = None) -> BaseMCPServer:
    """
    Factory function to create an MCP server for a specific application.
    :param app_namespace: The application namespace
    :param server_name: Optional custom server name
    :param port: Optional port number
    :return: MCP server instance
    """
    return BaseMCPServer(app_namespace, server_name, port)


if __name__ == "__main__":
    # This is a base class, specific servers should be run individually
    print("This is the base MCP server class.")
    print("Run specific application servers like word_mcp_server.py, excel_mcp_server.py, etc.")
