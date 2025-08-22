import argparse
import asyncio
import logging
import sys
import tracemalloc

from ufo.client.computer import ComputerManager
from ufo.client.mcp.mcp_server_manager import MCPServerManager
from ufo.client.ufo_client import UFOClient
from ufo.client.websocket import UFOWebSocketClient
from ufo.config import Config

tracemalloc.start()
CONFIGS = Config.get_instance().config_data

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="UFO Web Client")
    parser.add_argument(
        "--server",
        dest="server_url",
        default="http://localhost:5000",
        help="UFO Web Service URL (default: http://localhost:5000)",
    )
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
        help="WebSocket server address (default: ws://localhost:8765)",
    )
    parser.add_argument("--ws", action="store_true", help="Run in WebSocket mode")
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        dest="max_retries",
        help="Maximum retries for failed requests (default: 3)",
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
    args = parser.parse_args()

    # Initialize the MCP server manager and computer manager
    mcp_server_manager = MCPServerManager()
    computer_manager = ComputerManager(CONFIGS, mcp_server_manager)

    # Create UFO client
    client = UFOClient(
        args.server_url,
        mcp_server_manager=mcp_server_manager,
        computer_manager=computer_manager,
        client_id=args.client_id,
    )

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
