import argparse
import os
import traceback

from ufo.utils import print_with_color


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """

    parser = argparse.ArgumentParser(description="Run task with different execution modes.")
    
    # Make "mode" optional, with a default value
    parser.add_argument(
        "--mode", 
        default="dataflow",
        choices=["dataflow", "instantiation", "execution"], 
        help="Execution mode."
    )
    
    # Use `--task_path` as an optional argument with a default value
    parser.add_argument(
        "--task_path", 
        default="instantiation/tasks/prefill", 
        help="Path to the task file or directory."
    )
    
    # Optional flag for batch mode
    parser.add_argument(
        "--batch", 
        action="store_true", 
        help="Run tasks in batch mode (process all files in directory)."
    )
    
    return parser.parse_args()


def process_single_task(task_path: str, mode: str) -> None:
    """
    Single task processing.
    :param task_path: The path to the task file.
    :param mode: The execution mode.
    """
 
    from instantiation.controller.data_flow_controller import DataFlowController, TaskObject

    try:
        flow_controller = DataFlowController(task_path, mode)
        flow_controller.run()
    except Exception as e:
        # Catch exceptions and continue to the next task
        print_with_color(f"Error processing {task_path}: {e}", "red")
        traceback.print_exc() 
        raise e

def process_batch_tasks(task_dir: str, mode: str) -> None:
    """
    Batch tasks processing.
    :param task_dir: The path to the task directory.
    :param mode: The execution mode
    """
    
    # Get all task files in the directory
    task_files = [os.path.join(task_dir, f) for f in os.listdir(task_dir) if os.path.isfile(os.path.join(task_dir, f))]
    
    for task_file in task_files:
        try:
            print_with_color(f"Processing {task_file}...", "blue")

            # Process each individual task
            process_single_task(task_file, mode)
        except Exception:
            continue  

def main():
    """
    The main function to run the task.
    You can use dataflow, instantiation, and execution modes to process the task.
    Also, you can run tasks in batch mode by providing the path to the task directory.
    See README to read the detailed usage.
    """

    args = parse_args()

    if args.batch:
        if os.path.isdir(args.task_path):
            process_batch_tasks(args.task_path, args.mode)
        else:
            print(f"{args.task_path} is not a valid directory for batch processing.")
    else:
        if os.path.isfile(args.task_path):
            process_single_task(args.task_path, args.mode)
        else:
            print(f"{args.task_path} is not a valid file.")

if __name__ == "__main__":
    main()