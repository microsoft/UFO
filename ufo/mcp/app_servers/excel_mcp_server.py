#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Excel MCP Server
Provides MCP interface for Microsoft Excel automation via UFO framework.
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
    Main entry point for the Excel MCP server.
    """
    parser = argparse.ArgumentParser(description="Excel MCP Server")
    parser.add_argument("--port", type=int, default=8003, help="Port to run the server on")
    parser.add_argument("--host", default="localhost", help="Host to bind the server to")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("UFO Excel MCP Server")
    print("Microsoft Excel automation via Model Context Protocol")
    print(f"Running on {args.host}:{args.port}")
    print("=" * 50)
    
    # Create and run the Excel MCP server
    server = create_mcp_server(
        app_namespace="excel",
        server_name="ufo-excel",
        port=args.port  # Use parsed port instead of hardcoded value
    )
    
    server.run()


if __name__ == "__main__":
    main()
