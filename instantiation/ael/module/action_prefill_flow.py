import json
import os
from langchain.storage import LocalFileStore
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.embeddings import CacheBackedEmbeddings

from ael.automator.ui_control.control_filter import ControlFilterFactory
from ael.env.state_manager import WindowsAppEnv
from ael.agent.agent import ActionPrefillAgent
from ael.config.config import Config

from ufo.automator.ui_control.inspector import ControlInspectorFacade
from ufo.automator.ui_control.screenshot import PhotographerFacade
from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.module.basic import BaseSession


configs = Config.get_instance().config_data
if configs is not None:
    BACKEND = configs["CONTROL_BACKEND"]

def load_embedding_model(model_name: str):
    store = LocalFileStore(configs["CONTROL_EMBEDDING_CACHE_PATH"])
    if not model_name.startswith("sentence-transformers"):
        model_name = "sentence-transformers/" + model_name
    embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    cached_embedder = CacheBackedEmbeddings.from_bytes_store(
        embedding_model, store, namespace=model_name
    )
    return cached_embedder


class ActionPrefillFlow(AppAgentProcessor):
    """
    The class to refine the plan steps and prefill the file.
    """
    def __init__(self, app_name: str, environment: WindowsAppEnv = None, embedding_model: str = configs["CONTROL_FILTER_MODEL_SEMANTIC_NAME"]):
        """
        Initialize the follow flow.
        :param app_name: The name of the operated app.
        :param app_root_name: The root name of the app.
        :param environment: The environment of the app.
        """
        self.app_env = environment
        self.action_prefill_agent = ActionPrefillAgent('action_prefill', 
                                                       app_name, is_visual=True, 
                                                       main_prompt=configs["ACTION_PREFILL_PROMPT"], 
                                                       example_prompt=configs["ACTION_PREFILL_EXAMPLE_PROMPT"],
                                                       api_prompt=configs["API_PROMPT"])
        # self._image_url = []
        # Control filter
        self.file_path = ""
        self.embedding_model = load_embedding_model(embedding_model)


    def init_flow(self, task):
        """
        Init the flow.
        :param task: The label of the task.
        """
        self.execute_step = 0
        self.canvas_state = None
        self.control_inspector = ControlInspectorFacade(BACKEND)
        self.photographer = PhotographerFacade()

        self.control_state = None
        self.custom_doc = None
        self.status = ""
        self.file_path = ""
        self.control_annotation = None

        self.log_path_configs = configs["PREFILL_LOG_PATH"].format(task=task)
        os.makedirs(self.log_path_configs, exist_ok=True)
        self.prefill_logger = BaseSession.initialize_logger(self.log_path_configs, f"prefill_agent.json",'w', configs)
        self.execute_logger = BaseSession.initialize_logger(self.log_path_configs, f"execute.jsonl",'a', configs)


    def update_state(self, file_path: str):
        """
        Get current states of app with pywinauto、win32com
        :param file_path: The file path of the app.
        """
        print(f"updating the state of app file: {file_path}")

        control_list = self.control_inspector.find_control_elements_in_descendants(
                self.app_env.app_window,
                control_type_list=configs["CONTROL_LIST"],
                class_name_list=configs["CONTROL_LIST"],
        )
        self._annotation_dict = self.photographer.get_annotation_dict(
            self.app_env.app_window, control_list, annotation_type="number"
        )

        # Attempt to filter out irrelevant control items based on the previous plan.
        self.filtered_annotation_dict = self.get_filtered_annotation_dict(
            self._annotation_dict, configs = configs
        )

        self._control_info = self.control_inspector.get_control_info_list_of_dict(
            self._annotation_dict,
            ["control_text", "control_type" if BACKEND == "uia" else "control_class"],
        )
        self.filtered_control_info = (
            self.control_inspector.get_control_info_list_of_dict(
                self.filtered_annotation_dict,
                [
                    "control_text",
                    "control_type" if BACKEND == "uia" else "control_class",
                ],
            )
        )
        

    def log_execute_info(self, messages: list[dict], agent_response: dict, error: str = ""):
        """
        Record the execution information.
        :param messages: The messages of the conversation.
        :param agent_response: The response of the agent.
        :param error: The error message.
        """

        messages = messages
        history_json = {
            "step": self.execute_step,
            "messages": messages,
            "agent_response": agent_response,
            "error": error
        }
        # add not replace
        self.prefill_logger.info(json.dumps(history_json))

    def get_target_file(self, given_task: str, doc_files_description: dict):
        """
        Get the target file based on the semantic similarity of given task and the template file decription.
        """
        candidates = [doc_file_description for doc,
                      doc_file_description in doc_files_description.items()]
        file_doc_descriptions = {doc_file_description: doc for doc,
                                 doc_file_description in doc_files_description.items()}
        # use FAISS to get the top k control items texts
        db = FAISS.from_texts(candidates, self.embedding_model)
        doc_descriptions = db.similarity_search(given_task, k=1)
        doc_description = doc_descriptions[0].page_content
        doc = file_doc_descriptions[doc_description]
        return doc

    def get_prefill_actions(self, given_task, reference_steps, file_path):
        """
        Call the PlanRefine Agent to select files
        :return: The file to open
        """
        error_msg = ""
        # update the canvas state and control states
        self.update_state(file_path)

        screenshot_path = self.log_path_configs + "/screenshot.png"
        self.photographer.capture_desktop_screen_screenshot(save_path = screenshot_path)

        # filter the controls
        filter_control_state = self.filtered_control_info
        # filter the apis
        prompt_message = self.action_prefill_agent.message_constructor(
            "",
            given_task,reference_steps, filter_control_state,
            self.log_path_configs)
        try:
            response_string, cost = self.action_prefill_agent.get_response(
                prompt_message, "action_prefill", use_backup_engine=True, configs=configs)
            response_json = self.action_prefill_agent.response_to_dict(
                response_string)
            new_task = response_json["new_task"]
            action_plans = response_json["actions_plan"]

        except Exception as e:
            self.status = "ERROR"
            error_msg = str(e)
            self.log_execute_info(
                prompt_message, {"ActionPrefillAgent": response_json}, error_msg)
            
            return None, None
        else:
            self.log_execute_info(
                prompt_message, {"ActionPrefillAgent": response_json}, error_msg)

        return new_task, action_plans