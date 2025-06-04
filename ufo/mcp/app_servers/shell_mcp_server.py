#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Shell MCP Server
Provides MCP interface for shell command execution via UFO framework.
"""

import argparse
import os
import sys

# Add UFO2 to the path
ufo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ufo_root not in sys.path:
    sys.path.insert(0, ufo_root)

from ufo.mcp.base_mcp_server import create_mcp_server


def main():
    """
    Main entry point for the Shell MCP server.
    """
    parser = argparse.ArgumentParser(description="Shell MCP Server")
    parser.add_argument("--port", type=int, default=8005, help="Port to run the server on")
    parser.add_argument("--host", default="localhost", help="Host to bind the server to")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("UFO Shell MCP Server")
    print("Shell command execution via Model Context Protocol")
    print(f"Running on {args.host}:{args.port}")
    print("=" * 50)
    
    # Create and run the Shell MCP server
    server = create_mcp_server(
        app_namespace="shell",
        server_name="ufo-shell",
        port=args.port  # Use parsed port instead of hardcoded value
    )
    
    server.run()


if __name__ == "__main__":
    main()
