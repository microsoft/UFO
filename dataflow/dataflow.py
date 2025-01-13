import argparse
import os
import traceback
from ufo.utils import print_with_color
from dataflow.config.config import Config

_configs = Config.get_instance().config_data


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments. Automatically detect batch or single mode.
    """
    parser = argparse.ArgumentParser(
        description="Run tasks automatically in single or batch mode."
    )

    # Add options for -dataflow, -instantiation, and -execution
    parser.add_argument(
        "--dataflow",
        action="store_const",
        const="dataflow",
        help="Indicates that the task type is dataflow.",
    )
    parser.add_argument(
        "--instantiation",
        action="store_const",
        const="instantiation",
        help="Indicates that the task type is instantiation.",
    )
    parser.add_argument(
        "--execution",
        action="store_const",
        const="execution",
        help="Indicates that the task type is execution.",
    )

    # Task path argument
    parser.add_argument(
        "--task_path",
        type=str,
        default=_configs["TASKS_HUB"],
        help="Path to the task file or directory.",
    )

    return parser.parse_args()


def validate_path(path: str) -> str:
    """
    Validate the given path and determine its type.
    :param path: The path to validate.
    :return: "file", "directory", or raises an error if invalid.
    """
    if os.path.isfile(path):
        return "file"
    elif os.path.isdir(path):
        return "directory"
    else:
        print_with_color(f"Invalid path: {path}", "red")
        raise ValueError(f"Path {path} is neither a file nor a directory.")


def process_task(task_path: str, task_type: str) -> None:
    """
    Process a single task file using the DataFlowController.
    """
    from dataflow.data_flow_controller import DataFlowController

    try:
        print_with_color(f"Processing task: {task_path}", "green")
        flow_controller = DataFlowController(task_path, task_type)
        flow_controller.run()
        print_with_color(f"Task {task_path} completed successfully.", "green")
    except Exception as e:
        print_with_color(
            f"Error processing {task_path}: {traceback.format_exc()}", "red"
        )


def process_batch(task_dir: str, task_type: str) -> None:
    """
    Process all task files in a directory.
    """
    task_files = [
        os.path.join(task_dir, f)
        for f in os.listdir(task_dir)
        if os.path.isfile(os.path.join(task_dir, f))
    ]
    if not task_files:
        print_with_color(f"No tasks found in directory: {task_dir}.", "yellow")
        return

    print_with_color(f"Found {len(task_files)} tasks in {task_dir}.", "blue")
    for task_file in task_files:
        process_task(task_file, task_type)


def main():
    """
    Main function to run tasks based on the provided arguments.
    You can use dataflow, instantiation, and execution modes to process the task.
    Also, you can run tasks in batch mode by providing the path to the task directory.
    See README to read the detailed usage.
    """
    args = parse_args()

    # Ensure that a task type has been provided; if not, raise an error
    if not any([args.dataflow, args.instantiation, args.execution]):
        print_with_color(
            "Error: You must specify one of the task types (--dataflow, --instantiation, or --execution).",
            "red",
        )
        return

    task_type = args.dataflow or args.instantiation or args.execution

    path_type = validate_path(args.task_path)

    if path_type == "file":
        process_task(args.task_path, task_type)
    elif path_type == "directory":
        process_batch(args.task_path, task_type)


if __name__ == "__main__":
    main()
