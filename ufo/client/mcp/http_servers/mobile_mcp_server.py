#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Mobile MCP Servers
Provides two MCP servers:
1. Mobile Data Collection Server - for data retrieval operations (screenshots, UI tree, device info, etc.)
2. Mobile Action Server - for device control actions (tap, swipe, type, launch app, etc.)
Both servers share the same MobileServerState for coordinated operations.
Similar to linux_mcp_server.py structure with two separate servers on different ports.
"""

import argparse
import asyncio
import base64
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from typing import Annotated, Any, Dict, List, Optional
from fastmcp import FastMCP
from pydantic import Field
from ufo.agents.processors.schemas.target import TargetInfo, TargetKind


# Singleton Mobile server state
class MobileServerState:
    """
    Singleton state manager for Mobile MCP Servers.
    Caches app and control information to avoid repeated ADB queries.
    Shared between Data Collection and Action servers.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MobileServerState, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            # Cache for installed apps (List[TargetInfo])
            self.installed_apps: Optional[List[TargetInfo]] = None
            self.installed_apps_timestamp: Optional[float] = None

            # Cache for current screen controls (List[TargetInfo])
            self.current_controls: Optional[List[TargetInfo]] = None
            self.current_controls_timestamp: Optional[float] = None

            # Cache for UI tree XML
            self.ui_tree_xml: Optional[str] = None
            self.ui_tree_timestamp: Optional[float] = None

            # Cache for device info
            self.device_info: Optional[Dict[str, Any]] = None
            self.device_info_timestamp: Optional[float] = None

            # Control dictionary for quick lookup by ID
            self.control_dict: Optional[Dict[str, TargetInfo]] = None

            # Cache expiration times (seconds)
            self.apps_cache_duration = 300  # 5 minutes for apps list
            self.controls_cache_duration = 5  # 5 seconds for screen controls
            self.ui_tree_cache_duration = 5  # 5 seconds for UI tree
            self.device_info_cache_duration = 60  # 1 minute for device info

            MobileServerState._initialized = True

    def set_installed_apps(self, apps: List[TargetInfo]) -> None:
        """Cache the installed apps list."""
        import time

        self.installed_apps = apps
        self.installed_apps_timestamp = time.time()

    def get_installed_apps(self) -> Optional[List[TargetInfo]]:
        """Get cached installed apps if not expired."""
        import time

        if self.installed_apps is None or self.installed_apps_timestamp is None:
            return None

        if time.time() - self.installed_apps_timestamp > self.apps_cache_duration:
            return None  # Cache expired

        return self.installed_apps

    def set_current_controls(self, controls: List[TargetInfo]) -> None:
        """Cache the current screen controls and build control dictionary."""
        import time

        self.current_controls = controls
        self.current_controls_timestamp = time.time()

        # Build control dictionary for quick lookup
        self.control_dict = {control.id: control for control in controls}

    def get_current_controls(self) -> Optional[List[TargetInfo]]:
        """Get cached screen controls if not expired."""
        import time

        if self.current_controls is None or self.current_controls_timestamp is None:
            return None

        if time.time() - self.current_controls_timestamp > self.controls_cache_duration:
            return None  # Cache expired

        return self.current_controls

    def get_control_by_id(self, control_id: str) -> Optional[TargetInfo]:
        """Get a control by its ID from cache."""
        if self.control_dict is None:
            return None
        return self.control_dict.get(control_id)

    def set_ui_tree(self, xml: str) -> None:
        """Cache the UI tree XML."""
        import time

        self.ui_tree_xml = xml
        self.ui_tree_timestamp = time.time()

    def get_ui_tree(self) -> Optional[str]:
        """Get cached UI tree if not expired."""
        import time

        if self.ui_tree_xml is None or self.ui_tree_timestamp is None:
            return None

        if time.time() - self.ui_tree_timestamp > self.ui_tree_cache_duration:
            return None  # Cache expired

        return self.ui_tree_xml

    def set_device_info(self, info: Dict[str, Any]) -> None:
        """Cache the device information."""
        import time

        self.device_info = info
        self.device_info_timestamp = time.time()

    def get_device_info(self) -> Optional[Dict[str, Any]]:
        """Get cached device info if not expired."""
        import time

        if self.device_info is None or self.device_info_timestamp is None:
            return None

        if time.time() - self.device_info_timestamp > self.device_info_cache_duration:
            return None  # Cache expired

        return self.device_info

    def invalidate_controls(self) -> None:
        """Invalidate the controls cache (e.g., after screen change)."""
        self.current_controls = None
        self.current_controls_timestamp = None
        self.control_dict = None

    def invalidate_ui_tree(self) -> None:
        """Invalidate the UI tree cache."""
        self.ui_tree_xml = None
        self.ui_tree_timestamp = None

    def invalidate_all(self) -> None:
        """Invalidate all caches."""
        self.installed_apps = None
        self.installed_apps_timestamp = None
        self.current_controls = None
        self.current_controls_timestamp = None
        self.ui_tree_xml = None
        self.ui_tree_timestamp = None
        self.device_info = None
        self.device_info_timestamp = None
        self.control_dict = None


# Helper function for searching apps by name
async def _search_app_by_name(
    app_name: str, adb_path: str, include_system_apps: bool = True
):
    """Internal helper to search for app package by display name."""
    try:
        # Get package list
        list_cmd = [adb_path, "shell", "pm", "list", "packages"]
        if not include_system_apps:
            list_cmd.append("-3")

        proc = await asyncio.create_subprocess_exec(
            *list_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        if proc.returncode != 0:
            return None

        # Parse packages
        packages = []
        for line in stdout.decode("utf-8").split("\n"):
            if line.startswith("package:"):
                pkg = line.replace("package:", "").strip()
                packages.append(pkg)

        # Search for matching packages (simple heuristic)
        # First try: exact match in package name parts
        for pkg in packages:
            parts = pkg.split(".")
            if any(app_name.lower() == part.lower() for part in parts):
                return pkg

        # Second try: partial match in package name
        for pkg in packages:
            if app_name.lower() in pkg.lower():
                return pkg

        return None

    except Exception:
        return None


def create_mobile_data_collection_server(
    host: str = "", port: int = 8020, adb_path: Optional[str] = None
) -> None:
    """
    Create an MCP server for Mobile data collection operations.
    Handles: screenshots, UI tree, device info, app list, controls list, cache status.
    """

    if adb_path is None:
        adb_path = "adb"

    # Initialize shared state manager
    mobile_state = MobileServerState()

    mcp = FastMCP(
        "Mobile Data Collection MCP Server",
        instructions="MCP server for retrieving Android device information via ADB (screenshots, UI tree, device info, etc.).",
        stateless_http=False,
        json_response=True,
        host=host,
        port=port,
    )

    # ========================================
    # Data Collection Tool 1: Capture Screenshot
    # ========================================
    @mcp.tool()
    async def capture_screenshot() -> Annotated[
        str,
        Field(
            description="Base64 encoded image data URI of the screenshot (data:image/png;base64,...)"
        ),
    ]:
        """
        Capture screenshot from Android device.
        Returns base64-encoded image data URI directly (matching ui_mcp_server format).
        """
        try:
            # Create temp file for screenshot
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name

            # Capture screenshot on device
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "screencap",
                "-p",
                "/sdcard/screen_temp.png",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            if proc.returncode != 0:
                raise Exception("Failed to capture screenshot on device")

            # Pull screenshot from device
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "pull",
                "/sdcard/screen_temp.png",
                tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            if proc.returncode != 0:
                raise Exception("Failed to pull screenshot from device")

            # Clean up device temp file
            await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "rm",
                "/sdcard/screen_temp.png",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )

            # Read and encode as base64
            with open(tmp_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()

            # Clean up temp file
            os.unlink(tmp_path)

            # Return base64 data URI directly (like ui_mcp_server)
            return f"data:image/png;base64,{img_data}"

        except Exception as e:
            raise Exception(f"Error capturing screenshot: {str(e)}")

    # ========================================
    # Data Collection Tool 2: Get UI Tree
    # ========================================
    @mcp.tool()
    async def get_ui_tree() -> Annotated[
        Dict[str, Any],
        Field(
            description="Dictionary with keys: 'success' (bool), 'ui_tree' (str XML), 'format' (str), or 'error' (str)"
        ),
    ]:
        """
        Get the UI hierarchy tree in XML format.
        Useful for finding element positions and properties.
        """
        try:
            # Generate UI dump on device
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "uiautomator",
                "dump",
                "/sdcard/window_dump.xml",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            if proc.returncode != 0:
                return {"success": False, "error": "Failed to dump UI hierarchy"}

            # Read XML content
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "cat",
                "/sdcard/window_dump.xml",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                xml_content = stdout.decode("utf-8")
                # Cache the UI tree
                mobile_state.set_ui_tree(xml_content)

                return {
                    "success": True,
                    "ui_tree": xml_content,
                    "format": "xml",
                }
            else:
                return {"success": False, "error": stderr.decode("utf-8")}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================
    # Data Collection Tool 3: Get Device Info
    # ========================================
    @mcp.tool()
    async def get_device_info() -> Annotated[
        Dict[str, Any],
        Field(
            description="Dictionary with device information: model, android_version, sdk_version, screen_size, battery, etc."
        ),
    ]:
        """
        Get comprehensive Android device information.
        Includes model, Android version, screen resolution, battery status.
        Uses cache to improve performance.
        """
        try:
            # Check cache first
            cached_info = mobile_state.get_device_info()
            if cached_info is not None:
                return {"success": True, "device_info": cached_info, "from_cache": True}

            info = {}

            # Device model
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "getprop",
                "ro.product.model",
                stdout=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            info["model"] = stdout.decode("utf-8").strip()

            # Android version
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "getprop",
                "ro.build.version.release",
                stdout=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            info["android_version"] = stdout.decode("utf-8").strip()

            # SDK version
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "getprop",
                "ro.build.version.sdk",
                stdout=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            info["sdk_version"] = stdout.decode("utf-8").strip()

            # Screen size
            proc = await asyncio.create_subprocess_exec(
                adb_path, "shell", "wm", "size", stdout=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            info["screen_size"] = stdout.decode("utf-8").strip()

            # Screen density
            proc = await asyncio.create_subprocess_exec(
                adb_path, "shell", "wm", "density", stdout=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            info["screen_density"] = stdout.decode("utf-8").strip()

            # Battery info
            proc = await asyncio.create_subprocess_exec(
                adb_path, "shell", "dumpsys", "battery", stdout=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            battery_output = stdout.decode("utf-8")

            # Parse battery level
            for line in battery_output.split("\n"):
                if "level:" in line:
                    info["battery_level"] = line.split(":")[1].strip()
                elif "status:" in line:
                    info["battery_status"] = line.split(":")[1].strip()

            # Cache the device info
            mobile_state.set_device_info(info)

            return {"success": True, "device_info": info, "from_cache": False}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================
    # Data Collection Tool 4: Get Mobile App Target Info
    # ========================================
    @mcp.tool()
    async def get_mobile_app_target_info(
        filter: Annotated[
            str,
            Field(
                description="Filter pattern for package names (optional, e.g., 'com.android')"
            ),
        ] = "",
        include_system_apps: Annotated[
            bool,
            Field(
                description="Whether to include system apps (default: False, only show user-installed apps)"
            ),
        ] = False,
        force_refresh: Annotated[
            bool,
            Field(
                description="Force refresh from device, ignoring cache (default: False)"
            ),
        ] = False,
    ) -> Annotated[
        List[TargetInfo],
        Field(
            description="List of TargetInfo objects representing installed applications"
        ),
    ]:
        """
        Get information about installed application packages as TargetInfo list.
        Returns app package name, label (display name), and version if available.
        Uses cache to improve performance (cache duration: 5 minutes).
        """
        try:
            # Check cache first (only if no filter and not forcing refresh)
            if not filter and not force_refresh:
                cached_apps = mobile_state.get_installed_apps()
                if cached_apps is not None:
                    # Filter by include_system_apps setting
                    if include_system_apps:
                        return cached_apps
                    else:
                        return cached_apps

            # Get package list
            list_cmd = ["packages", "-3"] if not include_system_apps else ["packages"]
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "pm",
                "list",
                *list_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                raise Exception(f"Failed to list packages: {stderr.decode('utf-8')}")

            # Parse package list
            packages = []
            for line in stdout.decode("utf-8").split("\n"):
                if line.startswith("package:"):
                    pkg = line.replace("package:", "").strip()
                    if not filter or filter in pkg:
                        packages.append(pkg)

            # Get app labels (display names) for each package
            target_info_list = []
            for i, pkg in enumerate(packages):
                # Create TargetInfo object
                target_info = TargetInfo(
                    kind=TargetKind.THIRD_PARTY_AGENT,
                    id=str(i + 1),
                    name=pkg,  # Default to package name
                    type=pkg,  # Store package name in type field
                )
                target_info_list.append(target_info)

            # Cache the result (only if no filter)
            if not filter:
                mobile_state.set_installed_apps(target_info_list)

            return target_info_list

        except Exception as e:
            raise Exception(f"Failed to get mobile app target info: {str(e)}")

    # ========================================
    # Data Collection Tool 5: Get App Window Controls Target Info
    # ========================================
    @mcp.tool()
    async def get_app_window_controls_target_info(
        force_refresh: Annotated[
            bool,
            Field(
                description="Force refresh from device, ignoring cache (default: False)"
            ),
        ] = False,
    ) -> Annotated[
        List[TargetInfo],
        Field(
            description="List of TargetInfo objects representing UI controls on the current screen"
        ),
    ]:
        """
        Get UI controls information as TargetInfo list.
        Returns a list of TargetInfo objects for all meaningful controls on the screen.
        Each control has an id that can be used with action tools.
        Uses cache to improve performance (cache duration: 5 seconds).
        """
        try:
            # Check cache first
            if not force_refresh:
                cached_controls = mobile_state.get_current_controls()
                if cached_controls is not None:
                    return cached_controls

            # Get UI tree XML
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "uiautomator",
                "dump",
                "/sdcard/window_dump.xml",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            # Read XML content
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "cat",
                "/sdcard/window_dump.xml",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                return []

            xml_content = stdout.decode("utf-8")

            # Cache the UI tree XML
            mobile_state.set_ui_tree(xml_content)

            # Parse XML and extract controls
            root = ET.fromstring(xml_content)
            controls_target_info = []
            control_id = 1

            def parse_node(node):
                nonlocal control_id

                # Extract attributes
                attribs = node.attrib

                # Parse bounds [x,y][x2,y2]
                bounds_str = attribs.get("bounds", "")
                rect = None
                if bounds_str:
                    try:
                        # Parse bounds like "[0,0][1080,100]"
                        import re

                        coords = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
                        if len(coords) == 2:
                            x1, y1 = int(coords[0][0]), int(coords[0][1])
                            x2, y2 = int(coords[1][0]), int(coords[1][1])

                            # Validate coordinates: x2 must be >= x1 and y2 must be >= y1
                            # Some controls have invalid bounds, skip them
                            if x2 >= x1 and y2 >= y1 and x2 > 0 and y2 > 0:
                                # Use bbox format [left, top, right, bottom] to match ui_mcp_server.py
                                rect = [x1, y1, x2, y2]
                    except Exception:
                        pass

                # Get control name (text or content-desc)
                control_name = attribs.get("text") or attribs.get("content-desc") or ""

                # Get control type (short class name)
                control_type = attribs.get("class", "").split(".")[-1]

                # Only add meaningful controls
                is_meaningful = (
                    attribs.get("clickable") == "true"
                    or attribs.get("long-clickable") == "true"
                    or attribs.get("checkable") == "true"
                    or attribs.get("scrollable") == "true"
                    or control_name
                    or "Edit" in control_type
                    or "Button" in control_type
                )

                if is_meaningful and rect:
                    # Create TargetInfo object
                    target_info = TargetInfo(
                        kind=TargetKind.CONTROL,
                        id=str(control_id),
                        name=control_name or control_type,
                        type=control_type,
                        rect=rect,
                    )
                    controls_target_info.append(target_info)
                    control_id += 1

                # Recursively parse children
                for child in node:
                    parse_node(child)

            # Start parsing from root
            parse_node(root)

            # Cache the controls
            mobile_state.set_current_controls(controls_target_info)

            return controls_target_info

        except Exception as e:
            import traceback

            print(f"Error in get_app_window_controls_target_info: {str(e)}")
            print(traceback.format_exc())
            return []

    mcp.run(transport="streamable-http")


def create_mobile_action_server(
    host: str = "", port: int = 8021, adb_path: Optional[str] = None
) -> None:
    """
    Create an MCP server for Mobile action operations.
    Handles: tap, swipe, type_text, launch_app, press_key, click_control, wait, invalidate_cache.
    """

    if adb_path is None:
        adb_path = "adb"

    # Get shared state manager (singleton)
    mobile_state = MobileServerState()

    mcp = FastMCP(
        "Mobile Action MCP Server",
        instructions="MCP server for controlling Android devices via ADB (tap, swipe, type, launch apps, etc.).",
        stateless_http=False,
        json_response=True,
        host=host,
        port=port,
    )

    # ========================================
    # Action Tool 1: Tap/Click
    # ========================================
    @mcp.tool()
    async def tap(
        x: Annotated[int, Field(description="X coordinate to tap (pixels from left)")],
        y: Annotated[int, Field(description="Y coordinate to tap (pixels from top)")],
    ) -> Annotated[
        Dict[str, Any],
        Field(
            description="Dictionary with keys: 'success' (bool), 'action' (str), 'output' (str), or 'error' (str)"
        ),
    ]:
        """
        Tap/click at specified coordinates on the screen.
        Coordinates are in pixels, origin (0,0) is top-left corner.
        Automatically invalidates controls cache after interaction.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "input",
                "tap",
                str(x),
                str(y),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            # Invalidate controls cache after interaction
            if proc.returncode == 0:
                mobile_state.invalidate_controls()

            return {
                "success": proc.returncode == 0,
                "action": f"tap({x}, {y})",
                "output": stdout.decode("utf-8") if stdout else "",
                "error": stderr.decode("utf-8") if stderr else "",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================
    # Action Tool 2: Swipe
    # ========================================
    @mcp.tool()
    async def swipe(
        start_x: Annotated[int, Field(description="Starting X coordinate")],
        start_y: Annotated[int, Field(description="Starting Y coordinate")],
        end_x: Annotated[int, Field(description="Ending X coordinate")],
        end_y: Annotated[int, Field(description="Ending Y coordinate")],
        duration: Annotated[
            int, Field(description="Duration of swipe in milliseconds (default 300)")
        ] = 300,
    ) -> Annotated[
        Dict[str, Any],
        Field(
            description="Dictionary with keys: 'success' (bool), 'action' (str), or 'error' (str)"
        ),
    ]:
        """
        Perform swipe gesture from start to end coordinates.
        Useful for scrolling, dragging, and gesture navigation.
        Automatically invalidates controls cache after interaction.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "input",
                "swipe",
                str(start_x),
                str(start_y),
                str(end_x),
                str(end_y),
                str(duration),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            # Invalidate controls cache after swipe (UI likely changed)
            if proc.returncode == 0:
                mobile_state.invalidate_controls()

            return {
                "success": proc.returncode == 0,
                "action": f"swipe({start_x},{start_y})->({end_x},{end_y}) in {duration}ms",
                "output": stdout.decode("utf-8") if stdout else "",
                "error": stderr.decode("utf-8") if stderr else "",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================
    # Action Tool 3: Type Text
    # ========================================
    @mcp.tool()
    async def type_text(
        text: Annotated[
            str,
            Field(
                description="Text to input. Spaces and special characters are automatically escaped."
            ),
        ],
        control_id: Annotated[
            str,
            Field(
                description="REQUIRED: The precise annotated ID of the control to type into (from get_app_window_controls_target_info). The control will be clicked before typing to ensure focus."
            ),
        ],
        control_name: Annotated[
            str,
            Field(
                description="REQUIRED: The precise name of the control to type into, must match the selected control_id."
            ),
        ],
        clear_current_text: Annotated[
            bool,
            Field(
                description="Whether to clear existing text before typing. If True, selects all text (Ctrl+A) and deletes it first."
            ),
        ] = False,
    ) -> Annotated[
        Dict[str, Any],
        Field(
            description="Dictionary with keys: 'success' (bool), 'action' (str), 'message' (str), or 'error' (str)"
        ),
    ]:
        """
        Type text into a specific input field control.
        Always clicks the target control first to ensure it's focused before typing.

        Usage:
        type_text(text="hello world", control_id="5", control_name="Search")

        Steps:
        1. Call get_app_window_controls_target_info to get the list of controls
        2. Identify the input field control (EditText, etc.)
        3. Call type_text with the control's id and name
        4. The tool will click the control, then type the text

        Note: Spaces and special characters are automatically escaped for Android input.
        """
        try:
            messages = []

            # Verify control exists in cache
            target_control = mobile_state.get_control_by_id(control_id)

            if not target_control:
                return {
                    "success": False,
                    "error": f"Control with ID '{control_id}' not found. Please call get_app_window_controls_target_info first.",
                }

            # Verify name matches (optional warning)
            if target_control.name != control_name:
                messages.append(
                    f"Warning: Control ID {control_id} has name '{target_control.name}', but provided name is '{control_name}'. Using ID {control_id}."
                )

            # Click the control to focus it
            rect = target_control.rect
            if not rect:
                return {
                    "success": False,
                    "error": f"Control '{control_id}' has no rectangle information",
                }

            # rect format is [left, top, right, bottom] (bbox format)
            center_x = (rect[0] + rect[2]) // 2  # (left + right) / 2
            center_y = (rect[1] + rect[3]) // 2  # (top + bottom) / 2

            # Execute tap to focus
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "input",
                "tap",
                str(center_x),
                str(center_y),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            if proc.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to click control at ({center_x}, {center_y})",
                }

            messages.append(
                f"Clicked control '{target_control.name or target_control.type}' at ({center_x}, {center_y})"
            )

            # Small delay to let the input field focus
            await asyncio.sleep(0.2)

            # Clear existing text if requested
            if clear_current_text:
                # Delete characters
                for _ in range(50):  # Clear up to 50 characters
                    proc = await asyncio.create_subprocess_exec(
                        adb_path,
                        "shell",
                        "input",
                        "keyevent",
                        "KEYCODE_DEL",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await proc.communicate()

                messages.append("Cleared existing text")

            # Escape text for shell (replace spaces with %s)
            escaped_text = text.replace(" ", "%s").replace("&", "\\&")

            # Type the text
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "input",
                "text",
                escaped_text,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to type text: {stderr.decode('utf-8')}",
                }

            messages.append(f"Typed text: '{text}'")

            # Invalidate controls cache after typing (UI state may have changed)
            mobile_state.invalidate_controls()

            action_desc = f"type_text(text='{text}', control_id='{control_id}', control_name='{control_name}')"

            return {
                "success": True,
                "action": action_desc,
                "message": " | ".join(messages),
                "control_info": {
                    "id": target_control.id,
                    "name": target_control.name,
                    "type": target_control.type,
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================
    # Action Tool 4: Launch App
    # ========================================
    @mcp.tool()
    async def launch_app(
        package_name: Annotated[
            str,
            Field(
                description="Package name of the app to launch (e.g., 'com.android.settings')"
            ),
        ],
        id: Annotated[
            Optional[str],
            Field(
                description="Optional: The precise annotated ID of the app from get_mobile_app_target_info."
            ),
        ] = None,
    ) -> Annotated[
        Dict[str, Any],
        Field(
            description="Dictionary with keys: 'success' (bool), 'message' (str), or 'error' (str)"
        ),
    ]:
        """
        Launch an application by package name or app ID.

        Usage modes:
        1. Launch by package name: launch_app(package_name="com.android.settings")
        2. Launch from cached app list: launch_app(package_name="com.android.settings", id="5")

        When using id, the function will verify the package name matches the cached app info.
        """
        try:
            actual_package_name = package_name
            warning = None
            app_info = None

            # If id is provided, get app from cache
            if id:
                # Try to get from cache
                cached_apps = mobile_state.get_installed_apps()

                if cached_apps is None:
                    return {
                        "success": False,
                        "error": f"App cache is empty. Please call get_mobile_app_target_info first.",
                    }

                # Find the app by id
                target_app = None
                for app in cached_apps:
                    if app.id == id:
                        target_app = app
                        break

                if not target_app:
                    return {
                        "success": False,
                        "error": f"App with ID '{id}' not found in cached app list.",
                    }

                # The app's 'type' field contains the package name
                actual_package_name = target_app.type
                app_info = {
                    "id": target_app.id,
                    "name": target_app.name,
                    "package": target_app.type,
                }

                # Verify package_name matches (optional warning)
                if package_name != actual_package_name:
                    warning = f"Warning: Provided package_name '{package_name}' differs from cached package '{actual_package_name}'. Using cached package from ID {id}."

            # If no id and input doesn't look like a package name, search by app name
            elif "." not in package_name:
                found_package = await _search_app_by_name(
                    package_name, adb_path, include_system_apps=True
                )

                if not found_package:
                    return {
                        "success": False,
                        "error": f"No app found with name containing '{package_name}'. Try using full package name.",
                    }

                actual_package_name = found_package
                warning = (
                    f"Resolved '{package_name}' to package '{actual_package_name}'"
                )

            # Launch the app using package name
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "monkey",
                "-p",
                actual_package_name,
                "-c",
                "android.intent.category.LAUNCHER",
                "1",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            output = stdout.decode("utf-8")
            success = "Events injected:" in output or proc.returncode == 0

            result = {
                "success": success,
                "message": f"Launched {actual_package_name}",
                "package_name": actual_package_name,
                "output": output,
                "error": stderr.decode("utf-8") if stderr else "",
            }

            if warning:
                result["warning"] = warning

            if id and app_info:
                result["app_info"] = app_info

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================
    # Action Tool 5: Press Key
    # ========================================
    @mcp.tool()
    async def press_key(
        key_code: Annotated[
            str,
            Field(
                description="Key code to press. Common codes: KEYCODE_HOME, KEYCODE_BACK, KEYCODE_ENTER, KEYCODE_MENU"
            ),
        ],
    ) -> Annotated[
        Dict[str, Any],
        Field(
            description="Dictionary with keys: 'success' (bool), 'action' (str), or 'error' (str)"
        ),
    ]:
        """
        Press a hardware or software key.
        Useful for navigation (back, home) and system actions.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "input",
                "keyevent",
                key_code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            return {
                "success": proc.returncode == 0,
                "action": f"press_key({key_code})",
                "output": stdout.decode("utf-8") if stdout else "",
                "error": stderr.decode("utf-8") if stderr else "",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================
    # Action Tool 6: Click Control by ID
    # ========================================
    @mcp.tool()
    async def click_control(
        control_id: Annotated[
            str,
            Field(
                description="The precise annotated ID of the control to click (from get_app_window_controls_target_info)"
            ),
        ],
        control_name: Annotated[
            str,
            Field(
                description="The precise name of the control to click, must match the selected control_id"
            ),
        ],
    ) -> Annotated[
        Dict[str, Any],
        Field(
            description="Dictionary with keys: 'success' (bool), 'action' (str), 'message' (str), or 'error' (str)"
        ),
    ]:
        """
        Click a UI control by its id and name.
        First call get_app_window_controls_target_info to get the list of controls,
        then use the id and name to click the desired control.
        """
        try:
            # Try to get control from cache
            target_control = mobile_state.get_control_by_id(control_id)

            if not target_control:
                return {
                    "success": False,
                    "error": f"Control with ID '{control_id}' not found. Please call get_app_window_controls_target_info first.",
                }

            # Verify name matches
            name_verified = target_control.name == control_name
            warning = None
            if not name_verified:
                warning = f"Warning: Control ID {control_id} has name '{target_control.name}', but provided name is '{control_name}'. Clicking control {control_id}."

            # Get control center position
            rect = target_control.rect
            if not rect:
                return {
                    "success": False,
                    "error": f"Control '{control_id}' has no rectangle information",
                }

            # rect format is [left, top, right, bottom] (bbox format)
            center_x = (rect[0] + rect[2]) // 2  # (left + right) / 2
            center_y = (rect[1] + rect[3]) // 2  # (top + bottom) / 2

            # Execute tap
            proc = await asyncio.create_subprocess_exec(
                adb_path,
                "shell",
                "input",
                "tap",
                str(center_x),
                str(center_y),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            control_name_actual = target_control.name or target_control.type

            # Invalidate controls cache after interaction
            mobile_state.invalidate_controls()

            result = {
                "success": proc.returncode == 0,
                "action": f"click_control(id={control_id}, name={control_name})",
                "message": f"Clicked control '{control_name_actual}' at ({center_x}, {center_y})",
                "control_info": {
                    "id": target_control.id,
                    "name": target_control.name,
                    "type": target_control.type,
                    "rect": target_control.rect,
                },
            }

            if warning:
                result["warning"] = warning

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================
    # Action Tool 7: Wait
    # ========================================
    @mcp.tool()
    async def wait(
        seconds: Annotated[
            float,
            Field(
                description="Number of seconds to wait (can be decimal, e.g., 0.5 for 500ms)"
            ),
        ] = 1.0,
    ) -> Annotated[
        Dict[str, Any],
        Field(
            description="Dictionary with keys: 'success' (bool), 'action' (str), 'message' (str)"
        ),
    ]:
        """
        Wait for a specified number of seconds.
        Useful for waiting for UI transitions, animations, or app loading.
        Examples:
        - wait(seconds=1.0) - Wait 1 second
        - wait(seconds=0.5) - Wait 500 milliseconds
        - wait(seconds=2.5) - Wait 2.5 seconds
        """
        try:
            if seconds < 0:
                return {
                    "success": False,
                    "error": "Wait time must be non-negative",
                }

            if seconds > 60:
                return {
                    "success": False,
                    "error": "Wait time cannot exceed 60 seconds",
                }

            await asyncio.sleep(seconds)

            return {
                "success": True,
                "action": f"wait({seconds}s)",
                "message": f"Waited for {seconds} seconds",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================
    # Action Tool 8: Invalidate Cache
    # ========================================
    @mcp.tool()
    async def invalidate_cache(
        cache_type: Annotated[
            str,
            Field(
                description="Type of cache to invalidate: 'controls', 'apps', 'ui_tree', 'device_info', or 'all'"
            ),
        ] = "all",
    ) -> Annotated[
        Dict[str, Any],
        Field(
            description="Dictionary with keys: 'success' (bool), 'message' (str), or 'error' (str)"
        ),
    ]:
        """
        Manually invalidate cached data to force refresh on next query.
        Useful when you know the state has changed significantly.
        """
        try:
            if cache_type == "controls":
                mobile_state.invalidate_controls()
                message = "Controls cache invalidated"
            elif cache_type == "apps":
                mobile_state.installed_apps = None
                mobile_state.installed_apps_timestamp = None
                message = "Apps cache invalidated"
            elif cache_type == "ui_tree":
                mobile_state.invalidate_ui_tree()
                message = "UI tree cache invalidated"
            elif cache_type == "device_info":
                mobile_state.device_info = None
                mobile_state.device_info_timestamp = None
                message = "Device info cache invalidated"
            elif cache_type == "all":
                mobile_state.invalidate_all()
                message = "All caches invalidated"
            else:
                return {
                    "success": False,
                    "error": f"Invalid cache_type: {cache_type}. Must be 'controls', 'apps', 'ui_tree', 'device_info', or 'all'",
                }

            return {"success": True, "message": message}

        except Exception as e:
            return {"success": False, "error": str(e)}

    mcp.run(transport="streamable-http")


def _detect_adb_path() -> str:
    """Auto-detect ADB path or return 'adb' to use from PATH."""
    # Try common ADB locations
    common_paths = [
        r"C:\Users\{}\AppData\Local\Android\Sdk\platform-tools\adb.exe".format(
            os.environ.get("USERNAME", "")
        ),
        "/usr/bin/adb",
        "/usr/local/bin/adb",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path

    # Try to find in PATH
    try:
        result = subprocess.run(
            ["where" if os.name == "nt" else "which", "adb"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except:
        pass

    return "adb"  # Fallback to PATH


def _run_both_servers_sync(host: str, data_port: int, action_port: int, adb_path: str):
    """
    Run both data collection and action servers in the same process using threading.
    This allows them to share the same MobileServerState singleton.

    Note: MobileServerState uses singleton pattern, which ensures the same instance
    is shared across threads in the same process. This is critical for `click_control`
    to access controls cached by `get_app_window_controls_target_info`.
    """
    import threading
    import time

    print(f"\n✅ Starting both servers in same process (shared MobileServerState)")
    print(f"   - Data Collection Server: {host}:{data_port}")
    print(f"   - Action Server: {host}:{action_port}")
    print("\n" + "=" * 70)
    print("Both servers share MobileServerState cache. Press Ctrl+C to stop.")
    print("=" * 70 + "\n")

    # Create threads for both servers
    data_thread = threading.Thread(
        target=create_mobile_data_collection_server,
        kwargs={"host": host, "port": data_port, "adb_path": adb_path},
        name="DataCollectionServer",
        daemon=False,
    )

    action_thread = threading.Thread(
        target=create_mobile_action_server,
        kwargs={"host": host, "port": action_port, "adb_path": adb_path},
        name="ActionServer",
        daemon=False,
    )

    # Start both server threads
    data_thread.start()
    print(f"✅ Data Collection Server thread started")

    time.sleep(0.5)  # Small delay between starts

    action_thread.start()
    print(f"✅ Action Server thread started")

    print("\n" + "=" * 70)
    print("Both servers are running. Press Ctrl+C to stop.")
    print("=" * 70 + "\n")

    try:
        # Wait for both threads
        data_thread.join()
        action_thread.join()
    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        # FastMCP servers should handle shutdown gracefully
        data_thread.join(timeout=5)
        action_thread.join(timeout=5)
        print("✅ Servers stopped")


def main():
    parser = argparse.ArgumentParser(description="Mobile MCP Servers for Android")
    parser.add_argument(
        "--data-port", type=int, default=8020, help="Port for Data Collection Server"
    )
    parser.add_argument(
        "--action-port", type=int, default=8021, help="Port for Action Server"
    )
    parser.add_argument("--host", default="localhost", help="Host to bind servers to")
    parser.add_argument(
        "--adb-path",
        default=None,
        help="Path to ADB executable (auto-detected if not specified)",
    )
    parser.add_argument(
        "--server",
        choices=["data", "action", "both"],
        default="both",
        help="Which server(s) to start: 'data', 'action', or 'both'",
    )
    args = parser.parse_args()

    # Auto-detect ADB if not provided
    adb = args.adb_path or _detect_adb_path()

    print("=" * 70)
    print("UFO Mobile MCP Servers (Android)")
    print("Android device control via ADB and Model Context Protocol")
    print("=" * 70)
    print(f"\nUsing ADB: {adb}")
    print("\nChecking ADB connection...")

    # Test ADB connection
    try:
        result = subprocess.run(
            [adb, "devices"], capture_output=True, text=True, timeout=5
        )
        print(result.stdout)

        if "device" in result.stdout and "List of devices" in result.stdout:
            devices = [line for line in result.stdout.split("\n") if "\tdevice" in line]
            if devices:
                print(f"✅ Found {len(devices)} connected device(s)")
            else:
                print(
                    "⚠️  No devices connected. Please connect an Android device or emulator."
                )
        else:
            print("⚠️  ADB not working properly. Please check ADB installation.")
    except Exception as e:
        print(f"❌ Error checking ADB: {e}")
        print("   Servers will start but may not function properly.")

    print("=" * 70)

    if args.server == "both":
        # Run both servers in the same process/event loop to share MobileServerState
        import uvicorn

        print(f"\n🚀 Starting both servers on {args.host} (shared state)")
        print(f"   - Data Collection Server: port {args.data_port}")
        print(f"   - Action Server: port {args.action_port}")
        print("\nNote: Both servers share the same MobileServerState for caching")

        # Run both servers concurrently in the same process with shared state
        _run_both_servers_sync(args.host, args.data_port, args.action_port, adb)

    elif args.server == "data":
        print(f"\n🚀 Starting Data Collection Server on {args.host}:{args.data_port}")
        create_mobile_data_collection_server(
            host=args.host, port=args.data_port, adb_path=adb
        )

    elif args.server == "action":
        print(f"🚀 Starting Action Server on {args.host}:{args.action_port}")
        create_mobile_action_server(host=args.host, port=args.action_port, adb_path=adb)


if __name__ == "__main__":
    main()
