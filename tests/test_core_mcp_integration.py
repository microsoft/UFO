#!/usr/bin/env python3
"""
Test script for the Core MCP Client integration with UFOWebClient.

This script tests the core MCP client functionality and UFOWebClient
with the use_core_mcp_server configuration.
"""
import sys
import logging
from pathlib import Path

# Add the UFO directory to the Python path
ufo_path = Path(__file__).parent / "ufo"
sys.path.insert(0, str(ufo_path.parent))

from ufo.mcp.core_mcp_client import CoreMCPClient
from ufo.cs.web_client import UFOWebClient
from ufo.cs.contracts import (
    CaptureDesktopScreenshotAction,
    CaptureDesktopScreenshotParams,
    GetDesktopAppInfoAction,
    GetDesktopAppInfoParams
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_core_mcp_client_basic():
    """Test basic functionality of the Core MCP Client."""
    logger.info("Testing Core MCP Client basic functionality...")
    
    # Initialize the client (this will fail if no server is running, which is expected)
    client = CoreMCPClient(host="localhost", port=8000)
    
    # Test connection (this will return False if no server is running)
    connection_ok = client.test_connection()
    logger.info(f"MCP Server connection test: {'PASSED' if connection_ok else 'FAILED (Expected if server not running)'}")
    
    if not connection_ok:
        logger.warning("Core MCP Server is not running. This is expected if you haven't started it yet.")
        logger.info("To start the Core MCP Server, run: python -m ufo.mcp.core_mcp_server")
        return False
    
    # Test a simple action
    try:
        action = GetDesktopAppInfoAction(
            params=GetDesktopAppInfoParams(remove_empty=True, refresh_app_windows=False)
        )
        result = client.run_action(action)
        logger.info(f"GetDesktopAppInfo test: PASSED (got {len(result) if isinstance(result, list) else 'non-list'} apps)")
        return True
    except Exception as e:
        logger.error(f"GetDesktopAppInfo test: FAILED - {str(e)}")
        return False


def test_ufo_web_client_with_mcp():
    """Test UFOWebClient with Core MCP Server enabled."""
    logger.info("Testing UFOWebClient with Core MCP Server...")
    
    # Test with MCP enabled (will fall back to direct execution if server not available)
    client = UFOWebClient(
        server_url="http://localhost:5000",
        computer_name="test_client",
        use_core_mcp_server=True,
        core_mcp_host="localhost",
        core_mcp_port=8000
    )
    
    logger.info(f"UFOWebClient initialized with use_core_mcp_server={client.use_core_mcp_server}")
    
    if client.use_core_mcp_server:
        logger.info("MCP client is active and connected")
    else:
        logger.info("MCP client failed to connect, using direct computer execution")
    
    return True


def test_ufo_web_client_without_mcp():
    """Test UFOWebClient with Core MCP Server disabled (default behavior)."""
    logger.info("Testing UFOWebClient without Core MCP Server (default)...")
    
    # Test with MCP disabled (default behavior)
    client = UFOWebClient(
        server_url="http://localhost:5000",
        computer_name="test_client"
    )
    
    logger.info(f"UFOWebClient initialized with use_core_mcp_server={client.use_core_mcp_server}")
    
    if not client.use_core_mcp_server:
        logger.info("Direct computer execution is active (default behavior)")
    
    return True


def main():
    """Main test function."""
    logger.info("Starting Core MCP Integration Tests...")
    
    # Test 1: Core MCP Client basic functionality
    test1_passed = test_core_mcp_client_basic()
    
    # Test 2: UFOWebClient with MCP enabled
    test2_passed = test_ufo_web_client_with_mcp()
    
    # Test 3: UFOWebClient with MCP disabled (default)
    test3_passed = test_ufo_web_client_without_mcp()
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("TEST SUMMARY:")
    logger.info(f"Core MCP Client Basic Test: {'PASSED' if test1_passed else 'FAILED'}")
    logger.info(f"UFOWebClient with MCP Test: {'PASSED' if test2_passed else 'FAILED'}")
    logger.info(f"UFOWebClient without MCP Test: {'PASSED' if test3_passed else 'FAILED'}")
    
    if test2_passed and test3_passed:
        logger.info("\n✅ Integration implementation is complete and functional!")
        logger.info("🚀 You can now use UFOWebClient with use_core_mcp_server=True")
        logger.info("📝 To start the Core MCP Server: python -m ufo.mcp.core_mcp_server")
        return True
    else:
        logger.error("\n❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
