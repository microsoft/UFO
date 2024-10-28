import argparse
import os
import sys


# Add the project root to the system path.
def add_project_root_to_sys_path() -> None:
    """Add project root to system path if not already present."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    if project_root not in sys.path:
        sys.path.append(project_root)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    :return: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--task", help="The name of the task.", type=str, default="prefill"
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point of the script."""
    add_project_root_to_sys_path()  # Ensure project root is added
    task_dir_name = parse_arguments().task.lower()
    from controller.instantiation_process import InstantiationProcess

    InstantiationProcess().instantiate_files(task_dir_name)


if __name__ == "__main__":
    main()
