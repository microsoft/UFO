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

    def process(self, prefill_log_path: str, log_folder_path: str, output_folder_path: str):
        # Ensure output folder exists
        os.makedirs(output_folder_path, exist_ok=True)
        
        # Ensure image output folder exists if using path encoding
        if self.encode_type == "path" and self.image_output_path:
            os.makedirs(self.image_output_path, exist_ok=True)
        
        log_files = [
            f for f in os.listdir(log_folder_path)
            if os.path.isdir(os.path.join(log_folder_path, f))
        ]

        for log_file in tqdm(log_files, desc="Process Dateset..."):
            try:
                # filter error case
                if self.process_evaluation(os.path.join(log_folder_path, log_file)):
                    self.process_one(
                        prefill_log_path,
                        os.path.join(log_folder_path, log_file),
                        log_file,
                        output_folder_path
                    )
            except Exception as e:
                print(f"{log_file}: {e}")

    def process_one(self, prefill_log_path: str, log_file_path: str, log_name: str, output_folder_path: str):

        with open(prefill_log_path, 'r', encoding='utf-8') as prefill_file:
            prefill_log = json.load(prefill_file)
        prefill_log = prefill_log[log_name]
        execution_id = prefill_log["unique_id"]
        app_domain = prefill_log["app"]
        request = prefill_log["request"]
        template = prefill_log["template"]

        # Load request.log
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

        # Load response.log
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
            # response_steps = [json.loads(step) for step in response_steps]
            # Filter only app agent response log
            response_steps = [step for step in response_steps if step["Agent"] == "AppAgent"]

        # Construct steps info
        steps = self.process_steps(request_steps, response_steps, log_file_path, execution_id)

        evaluation = self.process_evaluation(log_file_path)

        # Write JSONL format - each line is a single step
        output_file_path = os.path.join(output_folder_path, f"{execution_id}.jsonl")
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

    def process_steps(self, request_steps: List, response_steps: List, log_file_path: str, execution_id: str) -> List:
        """
        Process steps info
        :param request_steps: request logs
        :param response_steps:  response logs
        :param log_file_path: current log file path
        :param execution_id: execution id for creating image folder
        :return: steps info
        """
        steps = []
        for step in response_steps:
            step_id = step["Step"]

            with open(os.path.join(log_file_path, "ui_trees", f"ui_tree_step{step_id}.json"), 'r',
                      encoding='utf-8') as ui_tree_file:
                ui_tree_content = json.load(ui_tree_file)

            # parse control infos
            request_json = request_steps[step_id]


            step_format = {
                "screenshot_clean": self.copy_image(os.path.join(log_file_path, f"action_step{step_id}.png"), execution_id, f"action_step{step_id}.png"),
                "screenshot_desktop": self.copy_image(
                    os.path.join(log_file_path, f"desktop_action_step{step_id}.png"), execution_id, f"desktop_action_step{step_id}.png"),
                "screenshot_annotated": self.copy_image(
                    os.path.join(log_file_path, f"action_step{step_id}_annotated.png"), execution_id, f"action_step{step_id}_annotated.png"),
                "screenshot_selected_controls": self.copy_image(
                    os.path.join(log_file_path, f"action_step{step_id}_selected_controls.png"), execution_id, f"action_step{step_id}_selected_controls.png"),
                "ui_tree": ui_tree_content,
                "control_infos": request_json["control_info_recording"],

                "observation": step["Observation"],
                "thought": step["Thought"],

                "action": {
                    "control_test": "",
                    "control_label": "",
                    "function": "",
                    "args": {},
                    "coordinate": [],
                    "centor_point_x": None,
                    "centor_point_y": None,
                },
                "status": step["Status"]
            }

            # parse action
            step_action = step["Action"] if "Action" in step else {}
            if step_action:
                step_action = step_action[0]
                step_format["action"]["control_test"] = step_action["ControlText"]
                step_format["action"]["control_label"] = step_action["ControlLabel"]
                step_format["action"]["function"] = step_action["Function"]
                step_format["action"]["args"] = step_action["Args"]
            control_log = step["ControlLog"] if "ControlLog" in step else {}
            if control_log and (control_coordinates := control_log[0]["control_coordinates"]):
                step_format["action"]["coordinate"] = control_coordinates
                step_format["action"]["centor_point_x"] = (control_coordinates["left"] + control_coordinates["right"]) / 2
                step_format["action"]["centor_point_y"] = (control_coordinates["top"] + control_coordinates["bottom"]) / 2

            steps.append(step_format)

        return steps

    def process_evaluation(self, log_file_path: str) -> dict:
        try:
            with open(os.path.join(log_file_path, "evaluation.log"), 'r', encoding='utf-8') as eva_file:
                evaluation_content = eva_file.read()
                evaluation_content = evaluation_content.strip().split("\n")[0]
                evaluation_content = json.loads(evaluation_content)

            evaluation_content.pop("level")
            evaluation_content.pop("request")
            evaluation_content.pop("id")
            return evaluation_content
        except FileNotFoundError or JSONDecodeError:
            return {}

    def copy_image(self, image_path: str, folder_id: str, image_name: str) -> str:
        """
        Copy image to specified folder and return relative path
        :param image_path: source image path
        :param folder_id: execution id for creating image folder
        :param image_name: target image name
        :return: relative path of the copied image
        """
        if self.encode_type == "base64":
            # Keep original base64 encoding behavior
            with open(image_path, "rb") as img_file:
                base64_str = base64.b64encode(img_file.read()).decode("utf-8")
            return base64_str
        elif self.image_output_path:
            # Create image folder for this execution
            image_folder = os.path.join(self.image_output_path, folder_id)
            os.makedirs(image_folder, exist_ok=True)
            
            # Copy image to the folder
            target_path = os.path.join(image_folder, image_name)
            if os.path.exists(image_path):
                shutil.copy2(image_path, target_path)
                # Return relative path from image_output_path
                return os.path.join(folder_id, image_name).replace("\\", "/")
            else:
                print(f"Warning: Image not found: {image_path}")
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
    parser.add_argument("--image_output_path", type=str, help="Top-level folder for storing images (required when encode_type is 'path')")

    args = parser.parse_args()
    
    if args.encode_type == "path" and not args.image_output_path:
        parser.error("--image_output_path is required when --encode_type is 'path'")
    
    # Ensure all required directories exist
    os.makedirs(args.output_path, exist_ok=True)
    if args.encode_type == "path" and args.image_output_path:
        os.makedirs(args.image_output_path, exist_ok=True)
    
    postprocess = PostProcess(args.encode_type, args.image_output_path)
    postprocess.process(args.prefill_path, args.log_path, args.output_path)
