import os
import pkgutil
import importlib.util
import sys

current_dir = os.path.dirname(__file__)

for finder, name, ispkg in pkgutil.iter_modules([current_dir]):
    # Only consider non-package modules (single .py files)
    if not ispkg:
        # Construct the full module name within the package
        full_module_name = f"{__name__}.{name}"

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
