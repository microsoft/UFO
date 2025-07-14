import base64
import json
import os
import shutil
from argparse import ArgumentParser
from json import JSONDecodeError
from typing import List, Optional

from tqdm import tqdm


class PostProcess:
    """
    PostProcess log files to dataset
    """

    def __init__(self, encode_type: str = "base64", image_output_path: Optional[str] = None):
        self.encode_type = encode_type
        self.image_output_path = image_output_path

        # Processing counters
        self.total_logs = 0
        self.successful_logs = 0
        self.failed_logs = 0
        self.success_complete_logs = 0  # Cases where complete="yes"
        self.fail_complete_logs = 0  # Cases where complete!="yes"

    def process(self, prefill_log_path: str, log_folder_path: str, output_folder_path: str):
        # Ensure output folder exists
        os.makedirs(output_folder_path, exist_ok=True)

        # Ensure image output folder exists if using path encoding
        if self.encode_type == "path" and self.image_output_path:
            os.makedirs(self.image_output_path, exist_ok=True)

        # Extract chunk information from log folder path
        chunk_info = self.extract_chunk_info(log_folder_path)

        log_files = [
            f for f in os.listdir(log_folder_path)
            if os.path.isdir(os.path.join(log_folder_path, f))
        ]

        self.total_logs = len(log_files)
        print(f"Found {self.total_logs} log directories to process in {chunk_info}")

        for log_file in tqdm(log_files, desc="Process Dataset..."):
            try:
                # filter error case
                if self.process_evaluation(os.path.join(log_folder_path, log_file)):
                    self.process_one(
                        prefill_log_path,
                        os.path.join(log_folder_path, log_file),
                        log_file,
                        output_folder_path,
                        chunk_info
                    )
                    self.successful_logs += 1
                else:
                    # Case failed evaluation
                    print(f"Failed evaluation: {log_file}")
                    self.failed_logs += 1
            except Exception as e:
                print(f"{log_file}: {e}")
                self.failed_logs += 1

        # Print final processing statistics
        self.print_processing_summary()

        # Check for missing image folders
        self.check_missing_image_folders(output_folder_path)

    def extract_chunk_info(self, log_folder_path: str) -> str:
        """Extract chunk information from the log folder path"""
        path_parts = log_folder_path.replace("\\", "/").split("/")
        for part in path_parts:
            if part.startswith("chunk"):
                return part
        return "unknown_chunk"

    def print_processing_summary(self):
        """Print a comprehensive summary of processing results"""
        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total logs found: {self.total_logs}")
        print(f"Successfully processed: {self.successful_logs}")
        print(f"Failed/Thrown: {self.failed_logs}")
        print(
            f"  - Success rate: {(self.successful_logs / self.total_logs * 100):.1f}%" if self.total_logs > 0 else "  - Success rate: 0.0%")
        print(
            f"  - Failure rate: {(self.failed_logs / self.total_logs * 100):.1f}%" if self.total_logs > 0 else "  - Failure rate: 0.0%")

        if hasattr(self, 'success_complete_logs') and hasattr(self, 'fail_complete_logs'):
            total_complete_evaluated = self.success_complete_logs + self.fail_complete_logs
            if total_complete_evaluated > 0:
                print(f"\nCompletion Status Breakdown:")
                print(f"  - Cases with complete='yes': {self.success_complete_logs}")
                print(f"  - Cases with complete!='yes': {self.fail_complete_logs}")
                print(
                    f"  - Success completion rate: {(self.success_complete_logs / total_complete_evaluated * 100):.1f}%")

        print("=" * 60)

    def check_missing_image_folders(self, output_folder_path: str):
        """
        Check if every JSONL file has a corresponding image folder and delete JSONL files without image folders
        :param output_folder_path: path to the output folder containing success/fail subfolders
        """
        if self.encode_type != "path" or not self.image_output_path:
            return

        missing_folders = []
        deleted_files = []

        # Check both success and fail folders
        for status in ["success", "fail"]:
            jsonl_folder = os.path.join(output_folder_path, status)
            image_folder = os.path.join(self.image_output_path, status)

            if not os.path.exists(jsonl_folder):
                continue

            # Get all JSONL files
            jsonl_files = [f for f in os.listdir(jsonl_folder) if f.endswith('.jsonl')]

            for jsonl_file in jsonl_files:
                execution_id = os.path.splitext(jsonl_file)[0]
                expected_image_folder = os.path.join(image_folder, execution_id)
                jsonl_path = os.path.join(jsonl_folder, jsonl_file)

                if not os.path.exists(expected_image_folder):
                    missing_folders.append(f"{status}/{execution_id}")
                    # Delete the JSONL file if image folder is missing
                    try:
                        os.remove(jsonl_path)
                        deleted_files.append(jsonl_path)
                    except Exception as e:
                        print(f"Error deleting {jsonl_path}: {str(e)}")

        if missing_folders:
            print("\nProcessing Missing Image Folders:")
            print("-" * 60)
            print(f"Found {len(missing_folders)} entries with missing image folders")
            print(f"Successfully deleted {len(deleted_files)} JSONL files")
            print("-" * 60)
            print("Deleted JSONL files:")
            for file in deleted_files:
                print(f"- {file}")
            print("-" * 60)

    def process_one(self, prefill_log_path: str, log_file_path: str, log_name: str, output_folder_path: str,
                    chunk_info: str):

        try:
            with open(prefill_log_path, 'r', encoding='utf-8') as prefill_file:
                prefill_log = json.load(prefill_file)
            prefill_log = prefill_log[log_name]
            execution_id = prefill_log["unique_id"]
            app_domain = prefill_log["app"]
            request = prefill_log["request"]
            template = prefill_log["template"]
        except (KeyError, JSONDecodeError, FileNotFoundError) as e:
            print(f"Prefill parsing error for {log_name}: {str(e)}")
            return

        # Load request.log
        try:
            with open(os.path.join(log_file_path, "request.log"), 'r', encoding='utf-8') as request_file:
                request_content = request_file.read()
                lines = request_content.strip().split("}\n{")

                request_steps = []
                if len(lines) == 1:
                    request_steps.append(json.loads(lines[0]))
                else:
                    for idx, line in enumerate(lines):
                        if idx == 0:
                            json_str = line + '}'
                        elif idx == len(lines) - 1:
                            json_str = '{' + line
                        else:
                            json_str = '{' + line + '}'
                        try:
                            request_steps.append(json.loads(json_str))
                        except JSONDecodeError as e:
                            request_steps.append({"ERROR": e})
                            print(f"Request log parsing error for {log_name} step {idx}: {str(e)}")
        except FileNotFoundError as e:
            print(f"Missing request.log for {log_name}: {str(e)}")
            return

        # Load response.log
        try:
            with open(os.path.join(log_file_path, "response.log"), 'r', encoding='utf-8') as log_file:
                response_content = log_file.read()

                lines = response_content.strip().split("}\n\n{")
                if len(lines) == 1:
                    lines = response_content.strip().split("}\n{")

                response_steps = []
                if len(lines) == 1:
                    response_steps.append(json.loads(lines[0]))
                else:
                    for idx, line in enumerate(lines):
                        if idx == 0:
                            json_str = line + '}'
                        elif idx == len(lines) - 1:
                            json_str = '{' + line
                        else:
                            json_str = '{' + line + '}'
                        try:
                            response_steps.append(json.loads(json_str))
                        except JSONDecodeError as e:
                            response_steps.append({"ERROR": e})
                            print(f"Response log parsing error for {log_name} step {idx}: {str(e)}")
                # response_steps = [json.loads(step) for step in response_steps]
                # Filter only app agent response log
                response_steps = [step for step in response_steps if step.get("Agent") == "AppAgent"]
        except FileNotFoundError as e:
            print(f"Missing response.log for {log_name}: {str(e)}")
            return

        try:
            evaluation = self.process_evaluation(log_file_path)
        except Exception as e:
            print(f"Evaluation processing error for {log_name}: {str(e)}")
            evaluation = {}

        # Determine if case is successful based on evaluation
        is_success = evaluation.get("complete", "").lower() == "yes"

        # Construct steps info
        try:
            steps = self.process_steps(request_steps, response_steps, log_file_path, execution_id, log_name, chunk_info,
                                       is_success)
        except Exception as e:
            print(f"Steps processing error for {log_name}: {str(e)}")
            return

        # Choose output path based on success/failure
        if is_success:
            final_output_path = os.path.join(output_folder_path, "success")
        else:
            final_output_path = os.path.join(output_folder_path, "fail")

        os.makedirs(final_output_path, exist_ok=True)

        # Write JSONL format - each line is a single step
        try:
            output_file_path = os.path.join(final_output_path, f"{execution_id}.jsonl")
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            with open(output_file_path, 'w', encoding='utf-8') as f:
                for idx, step in enumerate(steps, start=1):
                    step_json = {
                        "execution_id": execution_id,
                        "app_domain": app_domain,
                        "request": request,
                        "template": template,
                        "step_id": idx,
                        "total_steps": len(steps),
                        "evaluation": evaluation,
                        "step": step
                    }
                    f.write(json.dumps(step_json, ensure_ascii=False) + '\n')

            # Track completion statistics only after successful processing
            if is_success:
                self.success_complete_logs += 1
            else:
                self.fail_complete_logs += 1

        except Exception as e:
            print(f"Output writing error for {log_name}: {str(e)}")
            return

    def process_steps(self, request_steps: List, response_steps: List, log_file_path: str, execution_id: str,
                      log_name: str = "", chunk_info: str = "", is_success: bool = False) -> List:
        """
        Process steps info
        :param request_steps: request logs
        :param response_steps:  response logs
        :param log_file_path: current log file path
        :param execution_id: execution id for creating image folder
        :param log_name: case name for error tracking
        :param chunk_info: chunk information for error tracking
        :param is_success: whether the case was successful (for path routing)
        :return: steps info
        """
        steps = []
        for step in response_steps:
            try:
                step_id = step["Step"]

                # Check if UI tree file exists
                ui_tree_path = os.path.join(log_file_path, "ui_trees", f"ui_tree_step{step_id}.json")
                if not os.path.exists(ui_tree_path):
                    print(f"Missing UI tree for {log_name} step {step_id}")
                    continue

                with open(ui_tree_path, 'r', encoding='utf-8') as ui_tree_file:
                    ui_tree_content = json.load(ui_tree_file)

                # parse control infos
                if step_id >= len(request_steps):
                    print(f"Step index out of range for {log_name} step {step_id}")
                    continue

                request_json = request_steps[step_id]

                # Get step status first
                step_status = step.get("Status", "")

                # Copy images and check if any are missing
                screenshot_clean = self.copy_image(os.path.join(log_file_path, f"action_step{step_id}.png"),
                                                   execution_id, f"action_step{step_id}.png", log_name, chunk_info,
                                                   is_success)
                screenshot_desktop = self.copy_image(
                    os.path.join(log_file_path, f"desktop_action_step{step_id}.png"), execution_id,
                    f"desktop_action_step{step_id}.png", log_name, chunk_info, is_success)
                screenshot_annotated = self.copy_image(
                    os.path.join(log_file_path, f"action_step{step_id}_annotated.png"), execution_id,
                    f"action_step{step_id}_annotated.png", log_name, chunk_info, is_success)
                screenshot_selected_controls = self.copy_image(
                    os.path.join(log_file_path, f"action_step{step_id}_selected_controls.png"), execution_id,
                    f"action_step{step_id}_selected_controls.png", log_name, chunk_info, is_success)

                # Check if any screenshot is empty
                screenshots = [screenshot_clean, screenshot_desktop, screenshot_annotated, screenshot_selected_controls]
                has_missing_screenshot = any(screenshot == "" for screenshot in screenshots)

                if has_missing_screenshot:
                    if step_status != "FINISH":
                        # If status is not FINISH and screenshot is missing, throw entire case
                        print(
                            f"Missing screenshot in step {step_id} with status '{step_status}' - throwing entire case: {log_name}")
                        raise Exception(f"Throw entire case: Missing screenshot in non-FINISH step {step_id}")
                    else:
                        # If status is FINISH and screenshot is missing, just skip this step
                        print(f"Missing screenshot in FINISH step {step_id} - skipping step: {log_name}")
                        raise Exception(f"Missing screenshot in non-FINISH step {step_id}")

                step_format = {
                    "screenshot_clean": screenshot_clean,
                    "screenshot_desktop": screenshot_desktop,
                    "screenshot_annotated": screenshot_annotated,
                    "screenshot_selected_controls": screenshot_selected_controls,
                    "ui_tree": ui_tree_content,
                    "control_infos": request_json.get("control_info_recording", {}),

                    "subtask": step.get("Subtask", ""),
                    "observation": step.get("Observation", ""),
                    "thought": step.get("Thought", ""),

                    "action": {
                        "control_test": "",
                        "control_label": "",
                        "function": "",
                        "args": {},
                        "coordinate": [],
                        "centor_point_x": None,
                        "centor_point_y": None,
                    },
                    "status": step_status
                }

                # parse action
                step_action = step["Action"] if "Action" in step else {}
                if step_action:
                    step_action = step_action[0]
                    step_format["action"]["control_test"] = step_action.get("ControlText", "")
                    step_format["action"]["control_label"] = step_action.get("ControlLabel", "")
                    step_format["action"]["function"] = step_action.get("Function", "")
                    step_format["action"]["args"] = step_action.get("Args", {})
                control_log = step["ControlLog"] if "ControlLog" in step else {}
                if control_log and len(control_log) > 0 and (
                control_coordinates := control_log[0].get("control_coordinates")):
                    step_format["action"]["coordinate"] = control_coordinates
                    step_format["action"]["centor_point_x"] = (control_coordinates["left"] + control_coordinates[
                        "right"]) / 2
                    step_format["action"]["centor_point_y"] = (control_coordinates["top"] + control_coordinates[
                        "bottom"]) / 2

                steps.append(step_format)
            except Exception as e:
                print(f"Step processing error for {log_name} step {step.get('Step', 'unknown')}: {str(e)}")
                if "Throw entire case" in str(e):
                    raise e
                continue

        # Change the status of the final step from 'FINISH' to 'OVERALL_FINISH'
        if steps and steps[-1]['status'] == 'FINISH':
            steps[-1]['status'] = 'OVERALL_FINISH'

        return steps

    def process_evaluation(self, log_file_path: str) -> dict:
        try:
            with open(os.path.join(log_file_path, "evaluation.log"), 'r', encoding='utf-8') as eva_file:
                evaluation_content = eva_file.read()
                evaluation_content = json.loads(evaluation_content)

            evaluation_content.pop("level", None)
            evaluation_content.pop("request", None)
            evaluation_content.pop("id", None)
            return evaluation_content
        except (FileNotFoundError, JSONDecodeError):
            return {}

    def copy_image(self, image_path: str, folder_id: str, image_name: str, log_name: str = "", chunk_info: str = "",
                   is_success: bool = False) -> str:
        """
        Copy image to specified folder and return relative path
        :param image_path: source image path
        :param folder_id: execution id for creating image folder
        :param image_name: target image name
        :param log_name: case name for error tracking
        :param chunk_info: chunk information for error tracking
        :param is_success: whether the case was successful (for path routing)
        :return: relative path of the copied image
        """
        if self.encode_type == "base64":
            # Keep original base64 encoding behavior
            try:
                with open(image_path, "rb") as img_file:
                    base64_str = base64.b64encode(img_file.read()).decode("utf-8")
                return base64_str
            except FileNotFoundError:
                if log_name and chunk_info:
                    print(f"Missing image for {log_name}: {image_path}")
                return ""
        elif self.image_output_path:
            # Choose success or fail subfolder
            status_folder = "success" if is_success else "fail"
            # Create image folder for this execution
            image_folder = os.path.join(self.image_output_path, status_folder, folder_id)
            os.makedirs(image_folder, exist_ok=True)

            # Copy image to the folder
            target_path = os.path.join(image_folder, image_name)
            if os.path.exists(image_path):
                try:
                    shutil.copy2(image_path, target_path)
                    # Return relative path from image_output_path
                    return os.path.join(status_folder, folder_id, image_name).replace("\\", "/")
                except Exception as e:
                    if log_name and chunk_info:
                        print(f"Image copy error for {log_name}: Failed to copy {image_path}: {str(e)}")
                    return ""
            else:
                if log_name and chunk_info:
                    print(f"Missing image for {log_name}: {image_path}")
                return ""
        return ""

    def encode_image(self, image_path: str) -> str:
        if self.encode_type == "base64":
            with open(image_path, "rb") as img_file:
                base64_str = base64.b64encode(img_file.read()).decode("utf-8")
            return base64_str
        return ""

    def decode_image(self, base64_str: str, output_path: str):
        if self.encode_type == "base64":
            image_data = base64.b64decode(base64_str)
            with open(output_path, "wb") as img_file:
                img_file.write(image_data)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--prefill_path", required=True, type=str)
    parser.add_argument("--log_path", required=True, type=str)
    parser.add_argument("--output_path", required=True, type=str)
    parser.add_argument("--encode_type", choices=["base64", "path"], default="path")
    parser.add_argument("--image_output_path", type=str,
                        help="Top-level folder for storing images (required when encode_type is 'path')")

    args = parser.parse_args()

    if args.encode_type == "path" and not args.image_output_path:
        parser.error("--image_output_path is required when --encode_type is 'path'")

    # Ensure all required directories exist
    os.makedirs(args.output_path, exist_ok=True)
    if args.encode_type == "path" and args.image_output_path:
        os.makedirs(args.image_output_path, exist_ok=True)

    postprocess = PostProcess(args.encode_type, args.image_output_path)
    postprocess.process(args.prefill_path, args.log_path, args.output_path)
