#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Framework Main Entry Point

Primary command-line interface for Galaxy Framework with comprehensive functionality.
This script provides both simple and advanced interfaces for Galaxy sessions.

Simple Usage:
    python -m galaxy "Create a machine learning pipeline"
    python -m galaxy --interactive
    python -m galaxy --demo

Advanced Usage:
    python -m galaxy --request "Task description" --session-name "my_session"
    python -m galaxy --request "Task" --output-dir "./results" --log-level DEBUG
    python -m galaxy --interactive --max-rounds 20
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add UFO2 to path to enable imports
UFO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(UFO_ROOT))

# Import setup_logger early, before other project imports
from ufo.logging.setup import setup_logger
from rich.console import Console


def parse_args():
    """Parse command-line arguments with support for both simple and advanced usage."""
    parser = argparse.ArgumentParser(
        description="Galaxy Framework - AI-powered DAG workflow orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Simple Usage:
    python -m galaxy "Create a data analysis pipeline"
    python -m galaxy --demo
    python -m galaxy --interactive

  Advanced Usage:
    python -m galaxy --request "Build ML pipeline" --session-name "ml_session"
    python -m galaxy --interactive --max-rounds 20 --log-level DEBUG
    python -m galaxy --request "Task" --output-dir "./results" --mock
        """,
    )

    # Core functionality
    parser.add_argument(
        "simple_request",
        nargs="*",
        help="Simple request text (alternative to --request)",
    )

    parser.add_argument(
        "--request", dest="request_text", help="Task request text to process"
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive command-line mode",
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demonstration mode with sample workflows",
    )

    parser.add_argument(
        "--webui",
        action="store_true",
        help="Launch Web UI interface on http://localhost:8000",
    )

    # Session configuration
    parser.add_argument(
        "--session-name", dest="session_name", help="Custom name for the Galaxy session"
    )

    parser.add_argument(
        "--task-name", dest="task_name", help="Custom name for the specific task"
    )

    parser.add_argument(
        "--max-rounds",
        type=int,
        default=10,
        help="Maximum rounds per session (default: 10)",
    )

    # Output and logging
    parser.add_argument(
        "--output-dir",
        help="Output directory for results (if not specified, saves to session log path)",
    )

    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: WARNING)",
    )

    # Testing and development
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock agent for testing (no real LLM calls)",
    )

    return parser.parse_args()


# Parse args and setup logger BEFORE importing GalaxyClient
# This ensures config warnings are displayed with correct color
args = parse_args()
setup_logger(args.log_level)

# Now import GalaxyClient after logger is configured
from galaxy.galaxy_client import GalaxyClient

# Initialize rich console
console = Console()


# Utility functions for backward compatibility and convenience


async def galaxy_quick_start(
    request: str,
    session_name: str = "galaxy_quick",
    log_level: str = "WARNING",
    output_dir: str = "./logs",
):
    """
    Quick start function for single requests (programmatic API).

    :param request: User request text to process
    :param session_name: Name for the Galaxy session (default: "galaxy_quick")
    :param log_level: Logging level (default: "WARNING")
    :param output_dir: Output directory for results (default: "./logs")
    :return: Processing result dictionary
    """
    client = GalaxyClient(
        session_name=session_name, log_level=log_level, output_dir=output_dir
    )

    await client.initialize()
    result = await client.process_request(request)
    await client.shutdown()

    return result


async def galaxy_interactive(
    session_name: str = "galaxy_interactive",
    log_level: str = "WARNING",
    max_rounds: int = 10,
    output_dir: str = "./logs",
):
    """
    Interactive function for programmatic use.

    :param session_name: Name for the Galaxy session (default: "galaxy_interactive")
    :param log_level: Logging level (default: "WARNING")
    :param max_rounds: Maximum rounds per session (default: 10)
    :param output_dir: Output directory for results (default: "./logs")
    """
    client = GalaxyClient(
        session_name=session_name,
        log_level=log_level,
        max_rounds=max_rounds,
        output_dir=output_dir,
    )

    await client.initialize()
    await client.interactive_mode()
    await client.shutdown()


async def main():
    """
    Main entry point with unified simple and advanced CLI support.

    Supports both simple usage (direct arguments) and advanced usage (flags).
    Routes to appropriate execution mode based on arguments provided.
    """

    # Handle no arguments case
    if not any(
        [
            args.simple_request,
            args.request_text,
            args.interactive,
            args.demo,
            args.webui,
        ]
    ):
        from galaxy.visualization.client_display import ClientDisplay

        display = ClientDisplay(console)
        display.show_welcome_with_usage()
        return

    # Initialize client with provided configuration
    client = GalaxyClient(
        session_name=args.session_name,
        task_name=args.task_name,
        max_rounds=args.max_rounds,
        log_level=args.log_level,
        output_dir=args.output_dir,
    )

    try:
        await client.initialize()

        # WebUI mode
        if args.webui:
            await run_webui_mode(client)

        # Demo mode
        elif args.demo:
            await run_demo_with_client(client)

        # Interactive mode
        elif args.interactive:
            await client.interactive_mode()

        # Request processing mode
        elif args.request_text or args.simple_request:
            # Determine request text
            request_text = args.request_text or " ".join(args.simple_request)

            # Process request (task_name already passed during client initialization)
            result = await client.process_request(request_text)

            # Display results
            client.display.show_execution_complete()
            client.display.display_result(result)

    except KeyboardInterrupt:
        if "client" in locals():
            client.display.print_warning("\n👋 Interrupted by user")
        else:
            # Fallback display for when client is not yet initialized
            from galaxy.visualization.client_display import ClientDisplay

            display = ClientDisplay(console=console)
            display.print_warning("\n👋 Interrupted by user")
    except asyncio.CancelledError:
        # Gracefully handle cancelled tasks
        if "client" in locals():
            client.display.print_warning("\n👋 Shutting down...")
    except Exception as e:
        if "client" in locals():
            client.display.print_error(f"❌ Galaxy Framework error: {e}")
        else:
            # Fallback display for when client is not yet initialized
            from galaxy.visualization.client_display import ClientDisplay

            display = ClientDisplay(console=console)
            display.print_error(f"❌ Galaxy Framework error: {e}")
        logging.error(f"Galaxy Framework error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Suppress any remaining CancelledError during shutdown
        try:
            await client.shutdown()
        except asyncio.CancelledError:
            pass


async def run_demo_with_client(client: GalaxyClient):
    """
    Run demo mode with initialized client.

    :param client: Initialized GalaxyClient instance
    """
    client.display.show_demo_banner()

    demo_requests = [
        "Create a data analysis pipeline with parallel processing",
        "Build a machine learning workflow with training and evaluation",
        "Design a web scraping system with data validation and storage",
    ]

    for i, request in enumerate(demo_requests, 1):
        client.display.show_demo_step(i, request)

        with client.display.console.status(f"[bold cyan]Processing demo {i}..."):
            # Temporarily set task_name for this demo request
            original_task_name = client.task_name
            client.task_name = f"demo_task_{i}"

            result = await client.process_request(request)

            # Restore original task_name
            client.task_name = original_task_name

        client.display.display_result(result)

    client.display.show_demo_complete()


async def run_webui_mode(client: GalaxyClient):
    """
    Launch WebUI mode with FastAPI server.

    :param client: Initialized GalaxyClient instance
    """
    import socket
    import webbrowser
    import uvicorn
    from galaxy.webui.server import app, set_galaxy_client

    # Set the Galaxy client for the WebUI server
    set_galaxy_client(client)

    # Find available port
    def find_free_port(start_port=8000, max_attempts=10):
        """Find a free port starting from start_port."""
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", port))
                    return port
            except OSError:
                continue
        return None

    port = find_free_port()
    if port is None:
        client.display.print_error(
            "❌ Could not find an available port (tried 8000-8009)"
        )
        return

    # Write port info to frontend config file for development mode
    frontend_dir = Path(__file__).parent / "webui" / "frontend"
    if frontend_dir.exists():
        env_file = frontend_dir / ".env.development.local"
        try:
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(f"# Auto-generated by Galaxy backend\n")
                f.write(f"# This file is updated each time the backend starts\n")
                f.write(f"VITE_BACKEND_URL=http://localhost:{port}\n")
            client.display.print_info(f"📝 Updated frontend config: {env_file}")
        except Exception as e:
            client.display.print_warning(f"⚠️  Could not write frontend config: {e}")

    # Display banner
    client.display.print_info("🌌 Galaxy WebUI Starting...")
    client.display.print_info(f"📡 Server: http://localhost:{port}")
    client.display.print_info(
        f"🎨 Frontend: Open http://localhost:{port} in your browser"
    )
    client.display.print_info(f"🔌 WebSocket: ws://localhost:{port}/ws")
    client.display.print_info("\n💡 Press Ctrl+C to stop the server\n")

    # Configure and run uvicorn server
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)

    # Open browser after a short delay
    async def open_browser_delayed():
        """Open browser after server starts."""
        await asyncio.sleep(1.5)  # Wait for server to start
        url = f"http://localhost:{port}"
        client.display.print_info(f"🌐 Opening browser: {url}")
        webbrowser.open(url)

    # Start browser opening task
    asyncio.create_task(open_browser_delayed())

    try:
        await server.serve()
    except KeyboardInterrupt:
        client.display.print_warning("\n👋 WebUI server stopped by user")
    except asyncio.CancelledError:
        # Gracefully handle cancelled tasks during shutdown
        pass
    finally:
        # Suppress CancelledError during shutdown
        try:
            await server.shutdown()
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
