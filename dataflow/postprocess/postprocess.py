import base64
import json
import os
from argparse import ArgumentParser
from json import JSONDecodeError
from typing import List

from tqdm import tqdm


class PostProcess:
    """
    PostProcess log files to dataset
    """

    def __init__(self, encode_type: str = "base64"):
        self.encode_type = encode_type

    def process(self, prefill_log_path: str, log_folder_path: str, output_folder_path: str):
        log_files = [
            f for f in os.listdir(log_folder_path)
            if os.path.isdir(os.path.join(log_folder_path, f))
        ]

        for log_file in tqdm(log_files, desc="Process Dateset..."):
            try:
                # filter error case
                if self.process_evaluation(os.path.join(log_folder_path, log_file)):
                    result = self.process_one(
                        prefill_log_path,
                        os.path.join(log_folder_path, log_file),
                        log_file
                    )

                    with open(os.path.join(output_folder_path, f"{log_file}.json"), 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"{log_file}: {e}")

    def process_one(self, prefill_log_path: str, log_file_path: str, log_name: str) -> dict:

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
        steps = self.process_steps(request_steps, response_steps, log_file_path)

        for idx, step in enumerate(steps, start=1):
            step["step_id"] = idx

        evaluation = self.process_evaluation(log_file_path)

        return {
            "execution_id": execution_id,
            "app_domain": app_domain,
            "request": request,
            "template": template,
            "step_num": len(steps),
            "steps": steps,
            "evaluation": evaluation
        }

    def process_steps(self, request_steps: List, response_steps: List, log_file_path: str) -> List:
        """
        Process steps info
        :param request_steps: request logs
        :param response_steps:  response logs
        :param log_file_path: current log file path
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
                "step_id": step_id,
                "screenshot_clean": self.encode_image(os.path.join(log_file_path, f"action_step{step_id}.png")),
                "screenshot_desktop": self.encode_image(
                    os.path.join(log_file_path, f"desktop_action_step{step_id}.png")),
                "screenshot_annotated": self.encode_image(
                    os.path.join(log_file_path, f"action_step{step_id}_annotated.png")),
                "screenshot_selected_controls": self.encode_image(
                    os.path.join(log_file_path, f"action_step{step_id}_selected_controls.png")),
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
    parser.add_argument("--encode_type", choices=["base64"], default="base64")

    args = parser.parse_args()
    postprocess = PostProcess(args.encode_type)
    postprocess.process(args.prefill_path, args.log_path, args.output_path)
