# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
import os
import time
import traceback
from abc import ABC, abstractmethod
from logging import Logger
from typing import Optional, Type

from .. import utils
from ..agent.agent import AppAgent, HostAgent
from ..agent.basic import MemoryItem
from ..automator.ui_control import utils as control
from ..automator.ui_control.control_filter import ControlFilterFactory

from ..automator.ui_control.screenshot import PhotographerFacade
from ..config.config import Config
from . import interactor


configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]


class BaseProcessor(ABC):
    """
    The base processor for the session.
    """

    def __init__(self, index: int, log_path: str, photographer: PhotographerFacade, request: str, request_logger: Logger, logger: Logger, 
                 round_step: int, global_step: int, prev_status: str, app_window:Type) -> None:
        """
        Initialize the processor.
        :param log_path: The log path.
        :param photographer: The photographer facade to process the screenshots.
        :param request: The user request.
        :param request_logger: The logger for the request string.
        :param logger: The logger for the response and error.
        :param global_step: The global step of the session.
        :param prev_status: The previous status of the session.
        """

        self.log_path = log_path
        self.photographer = photographer
        self.request = request
        self.request_logger = request_logger
        self.logger = logger
        self._app_window = app_window
        
        self.global_step = global_step
        self.round_step = round_step
        self.prev_status = prev_status
        self.index = index
        
        self._step = 0
        self._status = prev_status
        self._prompt_message = None  
        self._response = None  
        self._cost = 0
        self._control_label = None
        self._control_text = None
        self._response_json = None

        
    def process(self):
        """
        Process the session.
        The process includes the following steps:
        1. Print the step information.
        2. Capture the screenshot.
        3. Get the control information.
        4. Get the prompt message.
        5. Get the response.
        6. Parse the response.
        7. Execute the action.
        8. Update the memory.
        9. Create the app agent if necessary.
        10. Update the step and status.
        """

        self.print_step_info()
        self.capture_screenshot()
        self.get_control_info()
        self.get_prompt_message()
        self.get_response()

        if self.is_error():
            return
        self.parse_response()

        if self.is_error():
            return
        
        self.execute_action()
        self.update_memory()

        if self.should_create_appagent():
            self.create_app_agent()
        self.update_step_and_status()
        
    
    @abstractmethod
    def print_step_info(self):
        """
        Print the step information.
        """
        pass
    
    @abstractmethod 
    def capture_screenshot(self):
        """
        Capture the screenshot.
        """
        pass
    
    @abstractmethod 
    def get_control_info(self): 
        """
        Get the control information.
        """
        pass
  

    @abstractmethod  
    def get_prompt_message(self):
        """
        Get the prompt message.
        """
        pass  
  
    @abstractmethod  
    def get_response(self):  
        """
        Get the response from the LLM.
        """
        pass  
  
    @abstractmethod  
    def parse_response(self):
        """
        Parse the response.
        """
        pass  

    @abstractmethod  
    def execute_action(self):
        """
        Execute the action.
        """
        pass  

    @abstractmethod
    def update_memory(self):
        """
        Update the memory of the Agent.
        """
        pass


    @abstractmethod  
    def update_status(self):
        """
        Update the status of the session.
        """
        pass

    
    def create_app_agent(self):
        """
        Create the app agent.
        """
        pass


    def update_step_and_status(self):
        """
        Update the step and status of the process.
        """
        self._step += 1  
        self.update_status()


    def get_active_window(self):
        """
        Get the active window.
        :return: The active window.
        """
        return self._app_window
    
    
    def get_active_control_text(self):
        """
        Get the active application.
        :return: The active application.
        """
        return self._control_text
    

    def get_process_status(self):
        """
        Get the process status.
        :return: The process status.
        """
        return self._status
    
    def get_process_step(self):
        """
        Get the process step.
        :return: The process step.
        """
        return self._step
    
    def get_process_cost(self):
        """
        Get the process cost.
        :return: The process cost.
        """
        return self._cost
    

    def is_error(self):
        """
        Check if the process is in error.
        :return: The boolean value indicating if the process is in error.
        """

        return self._status == "ERROR"
    

    def should_create_appagent(self):
        """
        Check if the app agent should be created.
        :return: The boolean value indicating if the app agent should be created.
        """

        if isinstance(self, HostAgentProcessor) and self.prev_status == "APP_SELECTION":
            return True
        else:
            return False


    def log(self, response_json: dict) -> dict:
        """
        Set the result of the session, and log the result.
        result: The result of the session.
        response_json: The response json.
        return: The response json.
        """

        self.logger.info(json.dumps(response_json))


    def error_log(self, response_str: str, error: str) -> None:
        """
        Error handler for the session.
        """
        log = json.dumps({"step": self._step, "status": "ERROR", "response": response_str, "error": error})
        self.logger.info(log)
        


    def get_current_action_memory(self):
        """
        Get the current action memory.
        :return: The current action memory.
        """
        pass




class HostAgentProcessor(BaseProcessor):

    def __init__(self, index: int, log_path: str, photographer: PhotographerFacade, request: str, request_logger: Logger, logger: Logger, 
                 host_agent: HostAgent, round_step: int, global_step: int, prev_status: str, app_window=None):
        super().__init__(index, log_path, photographer, request, request_logger, logger, round_step, global_step, prev_status, app_window)

        """
        Initialize the host agent processor.
        :param index: The index of the session.
        :param log_path: The log path.
        :param photographer: The photographer facade to process the screenshots.
        :param request: The user request.
        :param request_logger: The logger for the request string.
        :param logger: The logger for the response and error.
        :param host_agent: The host agent.
        :param round_step: The round step.
        :param global_step: The global step of the session.
        :param prev_status: The previous status of the session.
        """

        self.HostAgent = host_agent  

        self._desktop_screen_url = None
        self._desktop_windows_dict = None
        self._desktop_windows_info = None
        
    
    def print_step_info(self):
        """
        Print the step information.
        """
        utils.print_with_color("Round {index}, Step {step}: Selecting an application.".format(index=self.index+1, step=self.round_step+1), "magenta")

    def capture_screenshot(self):
        """
        Capture the screenshot.
        """
        desktop_save_path = self.log_path + f"action_step{self.global_step}.png"
        self.photographer.capture_desktop_screen_screenshot(all_screens=True, save_path=desktop_save_path)
        self._desktop_screen_url = self.photographer.encode_image_from_path(desktop_save_path)


    def get_control_info(self):
        """
        Get the control information.
        """
        self._desktop_windows_dict, self._desktop_windows_info = control.get_desktop_app_info_dict()


    def get_prompt_message(self):
        """
        Get the prompt message.
        """

        request_history = self.HostAgent.get_request_history_memory().to_json()
        action_history = self.HostAgent.get_global_action_memory().to_json()

        agent_memory = self.HostAgent.memory

        if agent_memory.length > 0:
            plan = agent_memory.get_latest_item().to_dict()["Plan"]
        else:
            plan = ""

        self._prompt_message = self.HostAgent.message_constructor([self._desktop_screen_url], request_history, action_history, 
                                                                                                  self._desktop_windows_info, plan, self.request)
        
        log = json.dumps({"step": self._step, "prompt": self._prompt_message, "control_items": self._desktop_windows_info, "filted_control_items": self._desktop_windows_info, "status": ""})
        self.request_logger.debug(log)
        return self._prompt_message
    
    
    def get_response(self):
        """
        Get the response from the LLM.
        """

        try:
            self._response, self._cost = self.HostAgent.get_response(self._prompt_message, "HOSTAGENT", use_backup_engine=True)
        except Exception as e:
            error_trace = traceback.format_exc()
            log = json.dumps({"step": self._step, "status": str(error_trace), "prompt": self._prompt_message})
            utils.print_with_color("Error occurs when calling LLM: {e}".format(e=str(e)), "red")
            self.request_logger.info(log)
            self._status = "ERROR"
        

    def parse_response(self):
        """
        Parse the response.
        """
        try:
            self._response_json = self.HostAgent.response_to_dict(self._response)
            self.control_label = self._response_json["ControlLabel"]
            self._control_text = self._response_json["ControlText"]
            self.plan = self._response_json["Plan"]
            self._status = self._response_json["Status"]
            
            self.HostAgent.print_response(self._response_json)

            if "FINISH" in self._status.upper() or self._control_text == "":
                self._status = "FINISH"

        except Exception:
            error_trace = traceback.format_exc()
            utils.print_with_color("Error Occurs at application selection.", "red")
            utils.print_with_color(str(error_trace), "red")
            utils.print_with_color(self._response, "red")
            self.error_log(self._response, str(error_trace))
            self._status = "ERROR"


    def execute_action(self):
        """
        Execute the action.
        """

         # Get the application window
        new_app_window = self._desktop_windows_dict.get(self.control_label, None)
        if new_app_window is None:
            return
        # Get the application name
        self.app_root = control.get_application_name(new_app_window)
        
        try:
            new_app_window.is_normal()

        # Handle the case when the window interface is not available
        except Exception:
            utils.print_with_color("Window interface {title} not available for the visual element.".format(title=self._control_text), "red")
            self._status = "ERROR"
            return

        self._status = "CONTINUE"
        
        if new_app_window is not self._app_window and self._app_window is not None:
            utils.print_with_color(  
                "Switching to a new application...", "magenta")
            self._app_window.minimize()

        self._app_window = new_app_window
        self._app_window.set_focus()


    def update_memory(self):
        """
        Update the memory of the Agent.
        """

        host_agent_step_memory = MemoryItem()
        additional_memory = {"Step": self.global_step, "RoundStep": self.get_process_step(), "AgentStep": self.HostAgent.get_step(), "Round": self.index, "ControlLabel": self._control_text, "Action": "set_focus()", 
                                "Request": self.request, "Agent": "HostAgent", "AgentName": self.HostAgent.name, "Application": self.app_root, "Cost": self._cost, "Results": ""}
        
        host_agent_step_memory.set_values_from_dict(self._response_json)
        host_agent_step_memory.set_values_from_dict(additional_memory)
        self.HostAgent.add_memory(host_agent_step_memory)
        
        self.log(host_agent_step_memory.to_dict())
        memorized_action = {key: host_agent_step_memory.to_dict().get(key) for key in configs["HISTORY_KEYS"]}
        self.HostAgent.add_global_action_memory(memorized_action)
        

    def update_status(self):
        """
        Update the status of the session.
        """
        self.HostAgent.update_step()
        self.HostAgent.update_status(self._status)

        if self._status != "FINISH":
            time.sleep(configs["SLEEP_TIME"])


    def create_app_agent(self):
        """
        Create the app agent.
        :return: The app agent.
        """
        appagent = self.HostAgent.create_appagent("AppAgent/{root}/{process}".format(root=self.app_root, process=self._control_text), self._control_text, self.app_root, configs["APP_AGENT"]["VISUAL_MODE"], 
                                     configs["APPAGENT_PROMPT"], configs["APPAGENT_EXAMPLE_PROMPT"], configs["API_PROMPT"])
            
        # Load the retrievers for APP_AGENT.
        if configs["RAG_OFFLINE_DOCS"]:
            utils.print_with_color("Loading offline document indexer for {app}...".format(app=self._control_text), "magenta")
            appagent.build_offline_docs_retriever()
        if configs["RAG_ONLINE_SEARCH"]:
            utils.print_with_color("Creating a Bing search indexer...", "magenta")
            appagent.build_online_search_retriever(self.request, configs["RAG_ONLINE_SEARCH_TOPK"])
        if configs["RAG_EXPERIENCE"]:
            utils.print_with_color("Creating an experience indexer...", "magenta")
            experience_path = configs["EXPERIENCE_SAVED_PATH"]
            db_path = os.path.join(experience_path, "experience_db")
            appagent.build_experience_retriever(db_path)
        if configs["RAG_DEMONSTRATION"]:
            utils.print_with_color("Creating an demonstration indexer...", "magenta")
            demonstration_path = configs["DEMONSTRATION_SAVED_PATH"]
            db_path = os.path.join(demonstration_path, "demonstration_db")
            appagent.build_human_demonstration_retriever(db_path)

        return appagent
    



class AppAgentProcessor(BaseProcessor):
    
        def __init__(self, index: int, log_path: str, photographer: PhotographerFacade, request: str, request_logger: Logger, logger: Logger, app_agent: AppAgent, round_step:int, global_step: int, 
                     process_name: str, app_window: Type, control_reannotate: Optional[list], prev_status: str):
            super().__init__(index, log_path, photographer, request, request_logger, logger, round_step, global_step, prev_status, app_window)

            """
            Initialize the app agent processor.
            :param index: The index of the session.
            :param log_path: The log path.
            :param photographer: The photographer facade to process the screenshots.
            :param request: The user request.
            :param request_logger: The logger for the request string.
            :param logger: The logger for the response and error.
            :param app_agent: The app agent.
            :param round_step: The round step.
            :param global_step: The global step of the session.
            :param process_name: The process name.
            :param app_window: The application window.
            :param control_reannotate: The list of controls to reannotate.
            :param prev_status: The previous status of the session.
            """

            self.AppAgent = app_agent
            self.process_name = process_name
            self.control_reannotate = control_reannotate

            self._annotation_dict = None
            self._control_info = None
            self._operation = None
            self._args = None
            self._image_url = []
            self._control_reannotate = None
            self.control_filter_factory = ControlFilterFactory()
            self.filtered_control_info = None

            
        def print_step_info(self):
            """
            Print the step information.
            """
            utils.print_with_color("Round {index}, Step {step}: Taking an action on application {application}.".format(index=self.index+1, step=self.round_step+1, application=self.process_name), "magenta")


        def capture_screenshot(self):
            """
            Capture the screenshot.
            """
            
            screenshot_save_path = self.log_path + f"action_step{self.global_step}.png"
            annotated_screenshot_save_path = self.log_path + f"action_step{self.global_step}_annotated.png"
            concat_screenshot_save_path = self.log_path + f"action_step{self.global_step}_concat.png"
            agent_memory = self.AppAgent.memory

            if type(self.control_reannotate) == list and len(self.control_reannotate) > 0:
                control_list = self.control_reannotate
            else:
                control_list = control.find_control_elements_in_descendants(BACKEND, self._app_window, control_type_list = configs["CONTROL_LIST"], class_name_list = configs["CONTROL_LIST"])
            
            self._annotation_dict = self.photographer.get_annotation_dict(self._app_window, control_list, annotation_type="number")
            
            if agent_memory.length > 0:
                prev_plan = agent_memory.get_latest_item().to_dict()["Plan"].strip()
                self.filtered_control_info = self.get_filtered_control_info(prev_plan)
            else:
                prev_plan = ""
                self.filtered_control_info = self.get_filtered_control_info(self.AppAgent.get_host().memory.get_latest_item().to_dict()["Plan"])
            
            if self.filtered_control_info:
                filtered_control_info_index = [info['label'] for info in self.filtered_control_info]
            else:
                filtered_control_info_index = []
            
            

            self.photographer.capture_app_window_screenshot(self._app_window, save_path=screenshot_save_path)
            self.photographer.capture_app_window_screenshot_with_annotation(self._app_window, control_list, annotation_type="number",\
                                    save_path=annotated_screenshot_save_path, filtered_control_info_index=filtered_control_info_index)


            if configs["INCLUDE_LAST_SCREENSHOT"]:
                
                last_screenshot_save_path = self.log_path + f"action_step{self.global_step - 1}.png"
                last_control_screenshot_save_path = self.log_path + f"action_step{self.global_step - 1}_selected_controls.png"
                self._image_url += [self.photographer.encode_image_from_path(last_control_screenshot_save_path if os.path.exists(last_control_screenshot_save_path) else last_screenshot_save_path)]

            if configs["CONCAT_SCREENSHOT"]:
                self.photographer.concat_screenshots(screenshot_save_path, annotated_screenshot_save_path, concat_screenshot_save_path)
                self._image_url += [self.photographer.encode_image_from_path(concat_screenshot_save_path)]
            else:
                screenshot_url = self.photographer.encode_image_from_path(screenshot_save_path)
                screenshot_annotated_url = self.photographer.encode_image_from_path(annotated_screenshot_save_path)
                self._image_url += [screenshot_url, screenshot_annotated_url]

        
        def get_control_info(self):
            """
            Get the control information.
            """
            self._control_info = control.get_control_info_dict(self._annotation_dict, ["control_text", "control_type" if BACKEND == "uia" else "control_class"])

        
        def get_filtered_control_info(self, plan:str, is_first_round=False):
            """
            Get the filtered control information.
            
            :param plan: The plan string.
            :param is_first_round: The boolean value indicating whether it is the first round.
            
            Return:
                The filtered control information.
            """
            
            control_filter_type = configs["CONTROL_FILTER_TYPE"]
            topk_plan = configs["CONTROL_FILTER_TOP_K_PLAN"]
            if self._control_info is None:
                self.get_control_info()
                
            if len(control_filter_type) == 0:
                return self._control_info

            
            control_filter_type_lower = [control_filter_type_lower.lower() for control_filter_type_lower in control_filter_type]
            
            filtered_control_info = []

            keywords = self.control_filter_factory.plan_to_keywords(plan, topk_plan, is_first_round)
            
            if 'text' in control_filter_type_lower:
                model_text = self.control_filter_factory.create_control_filter('text')
                filtered_text_control_info = model_text.control_filter(self._control_info, keywords)
                filtered_control_info = self.control_filter_factory.append_filtered_control_info(filtered_control_info, filtered_text_control_info)
                
            if 'semantic' in control_filter_type_lower:
                model_semantic = self.control_filter_factory.create_control_filter('semantic', configs["CONTROL_FILTER_MODEL_SEMANTIC_NAME"])
                filtered_semantic_control_info = model_semantic.control_filter(self._control_info, keywords, configs["CONTROL_FILTER_TOP_K_SEMANTIC"])
                filtered_control_info = self.control_filter_factory.append_filtered_control_info(filtered_control_info, filtered_semantic_control_info)
                
            if 'icon' in control_filter_type_lower:          
                model_icon = self.control_filter_factory.create_control_filter('icon', configs["CONTROL_FILTER_MODEL_ICON_NAME"])

                cropped_icons_dict = self.photographer.get_cropped_icons_dict(self._app_window, self._annotation_dict)
                filtered_icon_control_info = model_icon.control_filter(self._control_info, cropped_icons_dict, keywords, configs["CONTROL_FILTER_TOP_K_ICON"])
                filtered_control_info = self.control_filter_factory.append_filtered_control_info(filtered_control_info, filtered_icon_control_info)

            return filtered_control_info

            
            
        def get_prompt_message(self):
            """
            Get the prompt message for the AppAgent.
            """

            if configs["RAG_EXPERIENCE"]:
                experience_examples, experience_tips = self.AppAgent.rag_experience_retrieve(self.request, configs["RAG_EXPERIENCE_RETRIEVED_TOPK"])
            else:
                experience_examples = []
                experience_tips = []
                
            if configs["RAG_DEMONSTRATION"]:
                demonstration_examples, demonstration_tips = self.AppAgent.rag_demonstration_retrieve(self.request, configs["RAG_DEMONSTRATION_RETRIEVED_TOPK"])
            else:
                demonstration_examples = []
                demonstration_tips = []
            
            examples = experience_examples + demonstration_examples
            tips = experience_tips + demonstration_tips

            external_knowledge_prompt = self.AppAgent.external_knowledge_prompt_helper(self.request, configs["RAG_OFFLINE_DOCS_RETRIEVED_TOPK"], configs["RAG_ONLINE_RETRIEVED_TOPK"])


            HostAgent = self.AppAgent.get_host()

            action_history = HostAgent.get_global_action_memory().to_json()
            request_history = HostAgent.get_request_history_memory().to_json()

            agent_memory = self.AppAgent.memory

            if agent_memory.length > 0:
                prev_plan = agent_memory.get_latest_item().to_dict()["Plan"].strip()
            else:
                prev_plan = ""

            self._prompt_message = self.AppAgent.message_constructor(examples, tips, external_knowledge_prompt, self._image_url, request_history, action_history, 
                                                                                self.filtered_control_info, prev_plan, self.request, configs["INCLUDE_LAST_SCREENSHOT"])
            
            log = json.dumps({"step": self.global_step, "prompt": self._prompt_message, "control_items": self._control_info, 
                              "filted_control_items": self.filtered_control_info, "status": ""})
            self.request_logger.debug(log)


        def get_response(self):
            """
            Get the response from the LLM.
            """
            try:
                self._response, self._cost = self.AppAgent.get_response(self._prompt_message, "APPAGENT", use_backup_engine=True)
            except Exception as e:
                error_trace = traceback.format_exc()
                log = json.dumps({"step": self.global_step, "prompt": self._prompt_message, "status": str(error_trace)})
                utils.print_with_color("Error occurs when calling LLM: {e}".format(e=str(error_trace)), "red")
                self.request_logger.info(log)
                self._status = "ERROR"
                time.sleep(configs["SLEEP_TIME"])
                return
            
            
        def parse_response(self):
            """
            Parse the response.
            """
            try:
                self._response_json = self.AppAgent.response_to_dict(self._response)

                self._control_label = self._response_json["ControlLabel"]
                self._control_text = self._response_json["ControlText"]
                self._operation = self._response_json["Function"]
                self._args = utils.revise_line_breaks(self._response_json["Args"])
                self._status = self._response_json["Status"]

                self.AppAgent.print_response(self._response_json)

            except Exception:
                error_trace = traceback.format_exc()
                utils.print_with_color("Error Occurs at action selection in AppAgent.", "red")
                utils.print_with_color(str(error_trace), "red")
                utils.print_with_color(self._response, "red")
                self.error_log(self._response, str(error_trace))
                self._status = "ERROR"


        def execute_action(self):
            """
            Execute the action.
            """
            try:
                control_selected = self._annotation_dict.get(self._control_label, "")
                self.AppAgent.Puppeteer.create_ui_control_receiver(control_selected, self._app_window)

                # Save the screenshot of the selected control.
                control_screenshot_save_path = self.log_path + f"action_step{self.global_step}_selected_controls.png"
                self.photographer.capture_app_window_screenshot_with_rectangle(self._app_window, sub_control_list=[control_selected], save_path=control_screenshot_save_path)
                # Compose the function call and the arguments string.
                
                self._action = self.AppAgent.Puppeteer.get_command_string(self._operation, self._args)


                # Whether to proceed with the action.
                should_proceed = True

                # Safe guard for the action.
                if self._status.upper() == "PENDING" and configs["SAFE_GUARD"]:
                    should_proceed = self._safe_guard_judgement(self._action, self._control_text)
                    
                if should_proceed:
                    self._results = self.AppAgent.Puppeteer.execute_command(self._operation, self._args)
                    if not utils.is_json_serializable(self._results):
                        self._results = ""
                else:
                    self._results = "The user decide to stop the task."

                    return


                if self._status.upper() == "SCREENSHOT":
                    utils.print_with_color("Annotation is overlapped and the agent is unable to select the control items. New annotated screenshot is taken.", "magenta")
                    self._control_reannotate = self.AppAgent.Puppeteer.execute_command("annotation", self._args, self._annotation_dict)
                    if self._control_reannotate is None or len(self._control_reannotate) == 0:
                        self._status = "CONTINUE"
                else:
                    self._control_reannotate = None


            except Exception:
                error_trace = traceback.format_exc()
                utils.print_with_color(f"Error Occurs at action execution in AppAgent at step {self.global_step}", "red")
                utils.print_with_color(str(error_trace), "red")
                utils.print_with_color(self._response, "red")
                self.error_log(self._response, str(error_trace))
                self._status = "ERROR"
           
        
        def update_memory(self):
            """
            Update the memory of the Agent.
            """
            # Create a memory item for the app agent
            app_agent_step_memory = MemoryItem()

            app_root = control.get_application_name(self._app_window)
            HostAgent = self.AppAgent.get_host()
            
            additional_memory = {"Step": self.global_step, "RoundStep": self.get_process_step(), "AgentStep": self.AppAgent.get_step(), "Round": self.index, "Action": self._action, 
                                 "Request": self.request, "Agent": "ActAgent", "AgentName": self.AppAgent.name, "Application": app_root, "Cost": self._cost, "Results": self._results}
            app_agent_step_memory.set_values_from_dict(self._response_json)
            app_agent_step_memory.set_values_from_dict(additional_memory)

            self.AppAgent.add_memory(app_agent_step_memory)

            self.log(app_agent_step_memory.to_dict())
            memorized_action = {key: app_agent_step_memory.to_dict().get(key) for key in configs["HISTORY_KEYS"]}
            HostAgent.add_global_action_memory(memorized_action)


        def update_status(self):
            """
            Update the status of the session.
            """

            self.AppAgent.update_step()
            self.AppAgent.update_status(self._status)

            if self._status != "FINISH":
                time.sleep(configs["SLEEP_TIME"])



        def _safe_guard_judgement(self, action, control_text):
            """
            Safe guard for the session.
            action: The action to be taken.
            control_text: The text of the control item.
            return: The boolean value indicating whether to proceed or not.
            """
                       
            decision = interactor.sensitive_step_asker(action, control_text)
            if not decision:
                utils.print_with_color("The user decide to stop the task.", "magenta")
                self._status = "FINISH"
                return False
            
            # Handle the PENDING_AND_FINISH case
            elif "FINISH" in self.plan:
                self._status = "FINISH"
            return True


        def get_control_reannotate(self):
            """
            Get the control to reannotate.
            :return: The control to reannotate.
            """

            return self._control_reannotate