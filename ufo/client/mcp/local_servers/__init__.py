import os
import pkgutil
import importlib.util
import sys
import platform

current_dir = os.path.dirname(__file__)

# Windows-specific MCP servers that should not be loaded on Linux
WINDOWS_ONLY_SERVERS = {
    "ui_mcp_server",
    "excel_wincom_mcp_server",
    "ppt_wincom_mcp_server",
    "word_wincom_mcp_server",
    "pdf_reader_mcp_server",  # Uses PyPDF2 which is Windows-only
}


def load_all_servers():
    """
    Lazy load all MCP server modules.
    This function should be called when the servers are actually needed,
    not at module import time, to avoid circular import issues.

    On non-Windows platforms, Windows-specific servers are skipped.
    """
    is_windows = platform.system() == "Windows"

    for finder, name, ispkg in pkgutil.iter_modules([current_dir]):
        # Only consider non-package modules (single .py files)
        if not ispkg:
            # Skip Windows-only servers on non-Windows platforms
            if not is_windows and name in WINDOWS_ONLY_SERVERS:
                print(
                    f"Skipping Windows-only server '{name}' on {platform.system()} platform"
                )
                continue

            # Construct the full module name within the package
            full_module_name = f"ufo.client.mcp.local_servers.{name}"

            try:
                # Check if the module is already loaded to avoid re-importing in complex scenarios
                if full_module_name in sys.modules:
                    continue

                # Load the module specification
                spec = importlib.util.find_spec(full_module_name)
                if spec:
                    # Create a new module object
                    module = importlib.util.module_from_spec(spec)
                    # Add the module to sys.modules (important for correct import behavior)
                    sys.modules[full_module_name] = module
                    # Execute the module's code
                    if spec.loader:
                        spec.loader.exec_module(module)
                else:
                    # This case might happen if find_spec can't locate it, though less likely with pkgutil
                    print(f"Could not find spec for module {full_module_name}")

            except Exception as e:
                import traceback

                traceback.print_exc()
                # Handle potential errors during module loading (e.g., syntax errors)
                print(f"Error loading module '{full_module_name}': {e}")


# Don't load servers at import time - let them be loaded lazily when needed
# load_all_servers()
