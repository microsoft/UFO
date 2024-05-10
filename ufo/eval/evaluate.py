import json
import os
from ufo.llm.llm_call import get_completions
from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.utils import json_parser

class Evaluator():
    def __init__(self, log_path: str):
        self.log_path = log_path
        self.full_trajectory = []

    def load_logs(self):
        """
        Load logs from the log path.
        """
        log_file_path = os.path.join(self.log_path, "response.log")
        with open(log_file_path, "r") as f:
            logs = f.readlines()
            logs = [json.loads(log) for log in logs]
        return logs

    def load_images(self):
        """
        Load images from the log directory.
        """
        # image_paths = glob.glob(self.log_path + "*.png")
        init_image = os.path.join(self.log_path, "action_step1.png")
        final_image = os.path.join(self.log_path, "action_step_final.png")
        init_image_url = PhotographerFacade().encode_image_from_path(init_image)
        final_image_url = PhotographerFacade().encode_image_from_path(final_image)
        images = [init_image_url, final_image_url]
        return images

    def get_xml(self):
        """
        Get the xml.
        """
        pass

    def take_final_screenshot(self):
        """
        Take the final screenshot.
        """
        pass

    def get_trajectory(self):
        """
        Get the trajectory of the logs.
        """
        logs = self.load_logs()
        images = self.load_images()
        for item in logs:
            step_trajectory = {
                            "User Request": item["Request"], 
                            "Step": item["Step"],
                            "Agent": item["Agent"],
                            "AgentName": item["AgentName"],
                            "Observation": item["Observation"],
                            "Thought": item["Thought"],
                            "ControlLabel": item["ControlLabel"],
                            "ControlText":  item["ControlText"],
                            "Status": item["Status"],
                            "Plan": item["Plan"],
                            "Comment": item["Comment"],
                            "RoundStep": item["RoundStep"],
                            "AgentStep": item["AgentStep"],
                            "Round": item["Round"],
                            "Action": item["Action"],
                            "ActionType": item["ActionType"],
                            "Application": item["Application"]
                            }
            self.full_trajectory.append(
                {"type": "text", "text": str(step_trajectory)}
            )
        [self.full_trajectory.append(
            {
                "type": "image_url",
                "image_url": {"url": image}
            }
        ) for image in images]
    
    def __build_prompt(self):
        """
        Build the prompt for the evaluation.
        """
        system_instruction = """You're an evaluator who can evaluate whether an agent has successfully completed a task. The agent is an AI model that can interact with the desktop application and take actions. 
You will be provided with a task and the execution trajectory of the agent, including the agent's thought, observation, plan, actions that have been taken, and etc. Besides, you will also be provided with the screenshot before starting the task and after the task is finished. 
You are required to judge whether the agent has finished the task or not by observing the screenshot differences and the intermediate steps of the agent. The answer should be "yes" or "no" or "unsure". If you are not sure, please select "unsure". 
Don't make up the answer, otherwise, very bad things will happen.
You should follow the below JSON format to your reply:
{
    "reason": "the reason why you identify the agent's output as correct or incorrect.",
    "complete": "yes/no/unsure"
}
"""
        messages = [{"role": "system", 
                     "content": [{
                            "type": "text",
                            "text": system_instruction
                                }
                    ]
                    },
                    {"role": "user", 
                    "content": self.full_trajectory
                    }
                    ]
        return messages

    def evaluate(self):
        """
        Evaluate the trajectory.
        """
        self.get_trajectory()
        messages = self.__build_prompt()
        response_string, cost = get_completions(messages = messages, agent="appagent")
        try:
            response_json = json_parser(response_string[0])
        except:
            response_json = None
        return response_json, cost

# For test
if __name__ == "__main__":
    evaluator = Evaluator(log_path = "./logs/bbb/")
    evaluator.evaluate()

    