import argparse
import os
import traceback
from ufo.utils import print_with_color
from dataflow.config.config import Config
_configs = Config.get_instance().config_data


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for single and batch task processing.
    :return: Namespace of argparse
    """
    parser = argparse.ArgumentParser(
        description="Run task with different execution modes."
    )

    # Subparsers for different modes
    subparsers = parser.add_subparsers(
        title="commands",
        description="Choose between single or batch task processing modes.",
        dest="command",
        required=True,  # Force the user to choose one subcommand
    )

    # Single task processing
    single_parser = subparsers.add_parser(
        "single", help="Process a single task file."
    )
    single_parser.add_argument(
        "task_type",
        choices=["dataflow", "instantiation", "execution"],
        help="Execution task_type for the task.",
    )
    single_parser.add_argument(
        "task_path",
        type=str,
        help="Path to the task file.",
    )

    # Batch task processing
    batch_parser = subparsers.add_parser(
        "batch", help="Process all tasks in a directory."
    )
    batch_parser.add_argument(
        "task_type",
        default="dataflow",
        choices=["dataflow", "instantiation", "execution"],
        help="Execution task_type for the tasks.",
    )
    batch_parser.add_argument(
        "task_dir",
        default=_configs["TASKS_HUB"],
        type=str,
        help="Path to the directory containing task files.",
    )

    return parser.parse_args()


def validate_path(path: str, path_type: str) -> bool:
    """
    Validate the given path based on type.
    :param path: The path to validate.
    :param path_type: Type of path: "file" or "directory".
    :return: True if the path is valid, otherwise False.
    """
    if path_type == "file":
        if not os.path.isfile(path):
            print_with_color(f"Invalid file path: {path}", "red")
            return False
    elif path_type == "directory":
        if not os.path.isdir(path):
            print_with_color(f"Invalid directory path: {path}", "red")
            return False
    return True


def process_single_task(task_path: str, task_type: str) -> None:
    """
    Single task processing.
    :param task_path: The path to the task file.
    :param task_type: The type of task to process.
    """

    from dataflow.data_flow_controller import DataFlowController

    try:
        print_with_color(f"Starting processing for task: {task_path}", "green")
        flow_controller = DataFlowController(task_path, task_type)
        flow_controller.run()
        print_with_color(f"Task {task_path} completed successfully!", "green")
    except Exception as e:
        print_with_color(f"Error processing {task_path}: {e}", "red")

def process_batch_tasks(task_dir: str, task_type: str) -> None:
    """
    Batch tasks processing.
    :param task_dir: The path to the task directory.
    :param task_type: The type of task to process.
    """

    task_files = [
        os.path.join(task_dir, f)
        for f in os.listdir(task_dir)
        if os.path.isfile(os.path.join(task_dir, f))
    ]

    if not task_files:
        print_with_color(f"No task files found in directory: {task_dir}", "yellow")
        return

    print_with_color(f"Found {len(task_files)} tasks in {task_dir}.", "blue")
    for task_file in task_files:
        print_with_color(f"Processing {task_file}...", "blue")
        process_single_task(task_file, task_type)


def main():
    """
    Main function to run tasks based on the provided arguments.
    You can use dataflow, instantiation, and execution modes to process the task.
    Also, you can run tasks in batch mode by providing the path to the task directory.
    See README to read the detailed usage.
    """
    args = parse_args()

    if args.command == "single":
        if validate_path(args.task_path, "file"):
            process_single_task(args.task_path, args.task_type)
    elif args.command == "batch":
        if validate_path(args.task_dir, "directory"):
            process_batch_tasks(args.task_dir, args.task_type)


if __name__ == "__main__":
    main()
