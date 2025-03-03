import argparse
import os
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor

from tqdm import tqdm

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from ufo.utils import print_with_color
from ufo.utils.azure_storage import AzureBlobStorage
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

    blob_storage = None
    if _configs["UPLOAD"]:
        blob_storage = AzureBlobStorage()
    total = len(task_files)

    with ThreadPoolExecutor(max_workers=16) as executor:
        for idx, task_file in enumerate(tqdm(task_files), start=1):
            process_task(task_file, task_type)

            if _configs["MONITOR"]:
                # Send email notify
                send_point = _configs["SEND_POINT"].split(",")
                if str(idx) in send_point:
                    message = f"Task Completed {idx}/{total}"
                    send_message(message)

            if _configs["UPLOAD"] and (idx % _configs["UPLOAD_INTERVAL"] == 0 or idx == total):
                executor.submit(
                    lambda :blob_storage.upload_folder(_configs["REFORMAT_TO_BATCH_HUB"], _configs["DATA_SOURCE"], overwrite=False))
                executor.submit(
                    lambda: blob_storage.upload_folder(_configs["RESULT_LOG"], _configs["DATA_SOURCE"], overwrite=False))



def send_message(message: str) -> None:
    """
    Send a message.
    :param message: message to send.
    """
    # email info
    sender_email = _configs["FROM_EMAIL"]
    sender_password = _configs["SENDER_PASSWORD"]
    receiver_email = _configs["TO_EMAIL"]
    server_host = _configs["SMTP_SERVER"]
    machine_id = _configs["MACHINE_ID"]

    msg = MIMEMultipart()
    msg["From"] = _configs["FROM_EMAIL"]
    msg["TO"] = _configs["TO_EMAIL"]
    msg["Subject"] = Header(f"Prefill Progress Reminder: {machine_id}")
    msg.attach(MIMEText(message, "plain", 'utf-8'))

    server = None
    try:
        # Connect SMTP Server
        server = smtplib.SMTP(server_host, 587)
        server.starttls()
        server.login(sender_email, sender_password)

        # 发送邮件
        server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"Send Email to {receiver_email} sucessfully.")
    except Exception as e:
        print(f"Send Email to {receiver_email} failed: {e}.")
    finally:
        try:
            if server:
                server.quit()
        except Exception:
            return

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
