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
from ufo.automator.ui_control.screenshot import PhotographerFacade

# Add UFO2 to the path
ufo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if ufo_root not in sys.path:
    sys.path.insert(0, ufo_root)


#!/usr/bin/env python3
"""
Mock MCP server for testing hardware control tools.
This server provides dummy implementations for various hardware control tools.
"""
from typing import Annotated, Any, Dict, List, Optional, Tuple

from fastmcp import FastMCP
from pydantic import Field


def create_hardware_mcp_server(host: str = "", port: int = 8006) -> None:
    """Create a mock MCP server for hardware control.
    This server provides dummy implementations for various hardware control tools.
    It simulates the functionality of controlling hardware components like Arduino HID,
    mouse, BB-8, and robot arm without actual hardware interaction.
    """

    mcp = FastMCP(
        "Echo Base MCP Server",
        instructions="MCP server for controlling various hardware components (mock)",
        stateless_http=True,  # one‐shot JSON (no SSE/session)
        json_response=True,  # return pure JSON bodies
        host=host,
        port=port,
    )

    # Register MCP tools (all return dummy values)
    @mcp.tool()
    async def arduino_hid_status() -> Dict[str, Any]:
        """
        Get the current status of the Arduino HID device (dummy).
        """
        return {"connected": True, "status": "OK", "device": "Arduino HID (mock)"}

    @mcp.tool()
    async def arduino_hid_connect() -> Dict[str, Any]:
        """
        Connect to the Arduino HID device (dummy).
        """

        return {"success": True, "message": "Connected to Arduino HID device (mock)"}

    @mcp.tool()
    async def arduino_hid_disconnect() -> Dict[str, Any]:
        """
        Disconnect from the Arduino HID device (dummy).
        """
        return {
            "success": True,
            "message": "Disconnected from Arduino HID device (mock)",
        }

    @mcp.tool()
    async def type_text(text: str) -> Dict[str, Any]:
        """
        Type a string of text (dummy).
        """
        if not text:
            return {"success": False, "message": "Text is empty (mock)"}
        return {
            "success": True,
            "message": f"Typed text: {text[:20]}{'...' if len(text) > 20 else ''} (mock)",
        }

    @mcp.tool()
    async def press_key_sequence(
        keys: List[str], interval: float = 0.1
    ) -> Dict[str, Any]:
        """
        Press a sequence of keys (dummy).
        """
        if not keys:
            return {"success": False, "message": "Key sequence is empty (mock)"}
        return {
            "success": True,
            "message": f"Pressed key sequence: {keys[:5]}{'...' if len(keys) > 5 else ''} (mock)",
        }

    @mcp.tool()
    async def press_hotkey(keys: List[str]) -> Dict[str, Any]:
        """
        Press multiple keys simultaneously (dummy).
        """
        if not keys:
            return {"success": False, "message": "Hotkey list is empty (mock)"}
        return {"success": True, "message": f"Pressed hotkey: {keys} (mock)"}

    # Mouse functionality tools (dummy)
    @mcp.tool()
    async def move_mouse(x: int, y: int, absolute: bool = False) -> Dict[str, Any]:
        """
        Move the mouse pointer (dummy).
        """
        position_type = "absolute" if absolute else "relative"
        return {
            "success": True,
            "message": f"Moved mouse to {position_type} position ({x}, {y}) (mock)",
        }

    @mcp.tool()
    async def click_mouse(
        button: str = "left", count: int = 1, interval: float = 0.1
    ) -> Dict[str, Any]:
        """
        Click the specified mouse button (dummy).
        """
        return {
            "success": True,
            "message": f"Clicked {button} mouse button {count} times (mock)",
        }

    @mcp.tool()
    async def press_mouse_button(button: str = "left") -> Dict[str, Any]:
        """
        Press and hold the specified mouse button (dummy).
        """
        return {"success": True, "message": f"Pressed {button} mouse button (mock)"}

    @mcp.tool()
    async def release_mouse_button(button: str = "left") -> Dict[str, Any]:
        """
        Release the specified mouse button (dummy).
        """
        return {"success": True, "message": f"Released {button} mouse button (mock)"}

    @mcp.tool()
    async def scroll_mouse(vertical: int = 0, horizontal: int = 0) -> Dict[str, Any]:
        """
        Scroll the mouse wheel (dummy).
        """
        direction = []
        if vertical > 0:
            direction.append("up")
        elif vertical < 0:
            direction.append("down")
        if horizontal > 0:
            direction.append("right")
        elif horizontal < 0:
            direction.append("left")
        direction_text = " and ".join(direction) if direction else "no"
        return {
            "success": True,
            "message": f"Scrolled mouse in {direction_text} direction (mock)",
        }

    @mcp.tool()
    async def drag_mouse(
        start: Tuple[int, int],
        end: Tuple[int, int],
        button: str = "left",
        duration: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Drag the mouse from start to end position (dummy).
        """
        return {
            "success": True,
            "message": f"Dragged mouse from {start} to {end} using {button} button (mock)",
        }

    @mcp.tool()
    async def double_click_mouse(button: str = "left") -> Dict[str, Any]:
        """
        Perform a double-click (dummy).
        """
        return {
            "success": True,
            "message": f"Double-clicked {button} mouse button (mock)",
        }

    @mcp.tool()
    async def right_click_mouse() -> Dict[str, Any]:
        """
        Shortcut for right mouse button click (dummy).
        """
        return {"success": True, "message": "Right-clicked mouse (mock)"}

    @mcp.tool()
    async def middle_click_mouse() -> Dict[str, Any]:
        """
        Shortcut for middle mouse button click (dummy).
        """
        return {"success": True, "message": "Middle-clicked mouse (mock)"}

    # BB-8 mock tools
    @mcp.tool()
    async def bb8_status(ctx: Optional[Any] = None) -> Dict[str, Any]:
        """Get the current status of the BB-8 test fixture (mock)."""
        return {"connected": True, "status": "OK", "device": "BB-8 test fixture (mock)"}

    @mcp.tool()
    async def bb8_connect(ctx: Optional[Any] = None) -> Dict[str, Any]:
        """Connect to the BB-8 test fixture (mock)."""
        return {"success": True, "message": "Connected to BB-8 test fixture (mock)"}

    @mcp.tool()
    async def bb8_disconnect(ctx: Optional[Any] = None) -> Dict[str, Any]:
        """Disconnect from the BB-8 test fixture (mock)."""
        return {
            "success": True,
            "message": "Disconnected from BB-8 test fixture (mock)",
        }

    @mcp.tool()
    async def bb8_usb_port_plug(
        port_name: str, ctx: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Plug in a USB device to the specified port (mock)."""
        return {"success": True, "message": f"Plugged in {port_name} (mock)"}

    @mcp.tool()
    async def bb8_usb_port_unplug(
        port_name: str, ctx: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Unplug a USB device from the specified port (mock)."""
        return {"success": True, "message": f"Unplugged {port_name} (mock)"}

    @mcp.tool()
    async def bb8_psu_charger_plug(ctx: Optional[Any] = None) -> Dict[str, Any]:
        """Plug in the PSU charger (mock)."""
        return {"success": True, "message": "Plugged in PSU charger (mock)"}

    @mcp.tool()
    async def bb8_psu_charger_unplug(ctx: Optional[Any] = None) -> Dict[str, Any]:
        """Unplug the PSU charger (mock)."""
        return {"success": True, "message": "Unplugged PSU charger (mock)"}

    @mcp.tool()
    async def bb8_blade_attach(ctx: Optional[Any] = None) -> Dict[str, Any]:
        """Attach the blade (mock)."""
        return {"success": True, "message": "Attached blade (mock)"}

    @mcp.tool()
    async def bb8_blade_detach(ctx: Optional[Any] = None) -> Dict[str, Any]:
        """Detach the blade (mock)."""
        return {"success": True, "message": "Detached blade (mock)"}

    @mcp.tool()
    async def bb8_lid_open(ctx: Optional[Any] = None) -> Dict[str, Any]:
        """Open the lid (mock)."""
        return {"success": True, "message": "Opened lid (mock)"}

    @mcp.tool()
    async def bb8_lid_close(ctx: Optional[Any] = None) -> Dict[str, Any]:
        """Close the lid (mock)."""
        return {"success": True, "message": "Closed lid (mock)"}

    @mcp.tool()
    async def bb8_button_press(
        button_name: str, ctx: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Press a physical button (mock)."""
        return {"success": True, "message": f"Pressed {button_name} button (mock)"}

    @mcp.tool()
    async def bb8_button_long_press(
        button_name: str, ctx: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Long press a physical button (mock)."""
        return {"success": True, "message": f"Long pressed {button_name} button (mock)"}

    # Robot Arm mock tools
    @mcp.tool()
    async def robot_arm_status(ctx: Optional[Any] = None) -> Dict[str, Any]:
        """Get the current status of the Robot Arm (mock)."""
        return {
            "connected": True,
            "status": "OK",
            "position": [0, 0],
            "device": "Robot Arm (mock)",
        }

    @mcp.tool()
    async def robot_arm_connect(
        ctx: Annotated[str, Field(description="Text content of the control")] = None,
    ) -> Annotated[Dict[str, Any], Field(description="Response from the control")]:
        """Connect to the Robot Arm (mock).
        :param ctx: Optional context for the control.
        """
        return {"success": True, "message": "Connected to Robot Arm (mock)"}

    @mcp.tool()
    async def robot_arm_disconnect(ctx: Optional[Any] = None) -> Dict[str, Any]:
        """Disconnect from the Robot Arm (mock)."""
        return {"success": True, "message": "Disconnected from Robot Arm (mock)"}

    @mcp.tool()
    async def touch_screen(
        location: Tuple[int, int], ctx: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Simulate a touch at the specified location on the screen (mock)."""
        return {"success": True, "message": f"Touched screen at {location} (mock)"}

    @mcp.tool()
    async def draw_on_screen(
        path: List[Tuple[int, int]], ctx: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Simulate drawing on the screen by following a path of coordinates (mock)."""
        if not path:
            return {"success": False, "message": "Path is empty (mock)"}
        return {
            "success": True,
            "message": f"Drew path on screen with {len(path)} points (mock)",
        }

    @mcp.tool()
    async def tap_screen(
        ctx: Optional[Any] = None,
        location: Tuple[int, int] = (0, 0),
        count: int = 1,
        interval: float = 0.1,
    ) -> Dict[str, Any]:
        """Simulate tap(s) at the specified location on the screen (mock)."""
        return {
            "success": True,
            "message": f"Tapped screen {count} times at {location} (mock)",
        }

    @mcp.tool()
    async def swipe_screen(
        ctx: Optional[Any] = None,
        start_location: Tuple[int, int] = (0, 0),
        end_location: Tuple[int, int] = (0, 0),
        duration: float = 0.5,
    ) -> Dict[str, Any]:
        """Simulate a swipe gesture from start to end location (mock)."""
        return {
            "success": True,
            "message": f"Swiped screen from {start_location} to {end_location} (mock)",
        }

    @mcp.tool()
    async def long_press_screen(
        ctx: Optional[Any] = None,
        location: Tuple[int, int] = (0, 0),
        duration: float = 1.0,
    ) -> Dict[str, Any]:
        """Simulate a long press at the specified location (mock)."""
        return {
            "success": True,
            "message": f"Long pressed screen at {location} for {duration} seconds (mock)",
        }

    @mcp.tool()
    async def double_tap_screen(
        location: Tuple[int, int], ctx: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Simulate a double tap at the specified location (mock)."""
        return {
            "success": True,
            "message": f"Double tapped screen at {location} (mock)",
        }

    @mcp.tool()
    async def press_key(
        ctx: Optional[Any] = None,
        key: str = "",
        modifiers: Optional[List[str]] = None,
        duration: float = 0.1,
    ) -> Dict[str, Any]:
        """Simulate pressing a keyboard key, optionally with modifier keys (mock)."""
        modifiers = modifiers or []
        modifier_text = f" with modifiers {modifiers}" if modifiers else ""
        return {"success": True, "message": f"Pressed key {key}{modifier_text} (mock)"}

    @mcp.tool()
    async def tap_trackpad(
        ctx: Optional[Any] = None,
        location: Tuple[int, int] = (0, 0),
        count: int = 1,
        interval: float = 0.1,
    ) -> Dict[str, Any]:
        """Simulate tap(s) at the specified location on the trackpad (mock)."""
        return {
            "success": True,
            "message": f"Tapped trackpad {count} times at {location} (mock)",
        }

    @mcp.tool()
    async def swipe_trackpad(
        ctx: Optional[Any] = None,
        start_location: Tuple[int, int] = (0, 0),
        end_location: Tuple[int, int] = (0, 0),
        duration: float = 0.5,
    ) -> Dict[str, Any]:
        """Simulate a swipe gesture on the trackpad from start to end location (mock)."""
        return {
            "success": True,
            "message": f"Swiped trackpad from {start_location} to {end_location} (mock)",
        }

    @mcp.tool()
    async def take_screenshot() -> str:
        """Simulate taking a screenshot (mock)."""

        image_path = "./tests/image.png"
        image_data = PhotographerFacade().encode_image_from_path(image_path)
        return image_data

    mcp.run(transport="streamable-http")


def main():
    """
    Main entry point for the Excel MCP server.
    """
    parser = argparse.ArgumentParser(description="Hardware MCP Server")
    parser.add_argument(
        "--port", type=int, default=8006, help="Port to run the server on"
    )
    parser.add_argument(
        "--host", default="localhost", help="Host to bind the server to"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("UFO Hardware MCP Server")
    print("Hareware automation via Model Context Protocol")
    print(f"Running on {args.host}:{args.port}")
    print("=" * 50)

    # Create and run the Excel MCP server
    create_hardware_mcp_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
