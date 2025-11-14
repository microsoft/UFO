import argparse
import asyncio
import logging
import platform as platform_module
import sys
import tracemalloc

from ufo.client.computer import ComputerManager
from ufo.client.mcp.mcp_server_manager import MCPServerManager
from ufo.client.ufo_client import UFOClient
from ufo.client.websocket import UFOWebSocketClient
from config.config_loader import get_ufo_config
from ufo.logging.setup import setup_logger

tracemalloc.start()

parser = argparse.ArgumentParser(description="UFO Web Client")
parser.add_argument(
    "--client-id",
    dest="client_id",
    default="client_001",
    help="Client ID for the UFO Web Client (default: client_001)",
)
parser.add_argument(
    "--ws-server",
    dest="ws_server_url",
    default="ws://localhost:5000/ws",
    help="WebSocket server address (default: ws://localhost:5000/ws)",
)
parser.add_argument("--ws", action="store_true", help="Run in WebSocket mode")
parser.add_argument(
    "--max-retries",
    type=int,
    default=5,
    dest="max_retries",
    help="Maximum retries for failed requests (default: 5)",
)
parser.add_argument(
    "--request",
    dest="request_text",
    default=None,
    help="The task request text",
)
parser.add_argument(
    "--task_name",
    dest="task_name",
    default=None,
    help="The name of the task",
)
parser.add_argument(
    "--log-level",
    dest="log_level",
    default="WARNING",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL, OFF). Use OFF to disable logs (default: WARNING)",
)
parser.add_argument(
    "--platform",
    dest="platform",
    default=None,
    choices=["windows", "linux", "mobile"],
    help="Platform override (windows, linux, or mobile). If not specified, auto-detected from system.",
)
args = parser.parse_args()

# Auto-detect platform if not specified
if args.platform is None:
    detected_platform = platform_module.system().lower()
    if detected_platform in ["windows", "linux", "mobile"]:
        args.platform = detected_platform
    else:
        # Fallback to windows for unsupported platforms
        args.platform = "windows"

# Configure logging
setup_logger(args.log_level)
logger = logging.getLogger(__name__)

logger.info(f"Platform detected/specified: {args.platform}")


async def main():
    # Parse command line arguments

    # Get UFO config
    ufo_config = get_ufo_config()

    # Initialize the MCP server manager and computer manager
    mcp_server_manager = MCPServerManager()
    computer_manager = ComputerManager(ufo_config.to_dict(), mcp_server_manager)

    # Create UFO client with platform information
    client = UFOClient(
        mcp_server_manager=mcp_server_manager,
        computer_manager=computer_manager,
        client_id=args.client_id,
        platform=args.platform,
    )

    logger.info(f"UFO Client initialized for platform: {args.platform}")

    # Create WebSocket client and build the connection
    ws_client = UFOWebSocketClient(
        args.ws_server_url, client, max_retries=args.max_retries
    )
    try:
        asyncio.create_task(ws_client.connect_and_listen())
    except Exception as e:
        logger.error(f"[WS] WebSocket client error: {str(e)}", exc_info=True)
        sys.exit(1)

    if args.request_text:
        # Wait for the WebSocket connection to be established
        await ws_client.connected_event.wait()
        await ws_client.start_task(args.request_text, args.task_name)

    await asyncio.Future()  # Run forever


if __name__ == "__main__":

    asyncio.run(main())
