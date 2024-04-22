# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from abc import ABC, abstractmethod
from .. import utils
from ..automator.ui_control import utils as control
import json
import os
import time
import traceback
from ..agent.basic import MemoryItem
from ..config.config import Config

from . import interactor

configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]


class BaseProcessor(ABC):
    def __init__(self, log_path, photographer, request, request_logger, logger, global_step, prev_status):
        self.log_path = log_path
        self.photographer = photographer
        self.request = request
        self.request_logger = request_logger
        self.logger = logger
        self.global_step = global_step
        self.prev_status = prev_status
        
        self._step = 0
        self._status = prev_status
        self._prompt_message = None  
        self._response = None  
        self._cost = 0
        self._control_label = None
        self._app_window = None
        self._control_text = None
        self._response_json = None

        
    def process(self):

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
        pass
    
    @abstractmethod 
    def capture_screenshot(self):  
        pass
    
    @abstractmethod 
    def get_control_info(self):  
        pass
  

    @abstractmethod  
    def get_prompt_message(self):  
        pass  
  
    @abstractmethod  
    def get_response(self):  
        pass  
  
    @abstractmethod  
    def parse_response(self):  
        pass  

    @abstractmethod  
    def execute_action(self):  
        pass  

    @abstractmethod
    def update_memory(self):
        pass

    
    def create_app_agent(self):
        pass


    def update_step_and_status(self):  
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

        return self._status == "ERROR"
    

    def should_create_appagent(self):

        if isinstance(self, HostAgentProcessor) and self.prev_status == "APP_SELECTION":
            return True
        else:
            return False


  
    @abstractmethod  
    def update_status(self):  
        pass


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

    def __init__(self, log_path, photographer, request, request_logger, logger, host_agent, global_step, prev_status):
        super().__init__(log_path, photographer, request, request_logger, logger, global_step, prev_status)
        self.HostAgent = host_agent  

        self._desktop_screen_url = None
        self._desktop_windows_dict = None
        self._desktop_windows_info = None
        
    
    def print_step_info(self):
        utils.print_with_color("Step {step}: Selecting an application.".format(step=self.global_step), "magenta")

    def capture_screenshot(self):

        desktop_save_path = self.log_path + f"action_step{self._step}.png"
        self.photographer.capture_desktop_screen_screenshot(all_screens=True, save_path=desktop_save_path)
        self._desktop_screen_url = self.photographer.encode_image_from_path(desktop_save_path)


    def get_control_info(self):  
        self._desktop_windows_dict, self._desktop_windows_info = control.get_desktop_app_info_dict()


    def get_prompt_message(self):

        request_history = self.HostAgent.get_request_history_memory().to_json()
        action_history = self.HostAgent.get_global_action_memory().to_json()

        agent_memory = self.HostAgent.memory

        if agent_memory.length > 0:
            plan = agent_memory.get_latest_item().to_dict()["Plan"]
        else:
            plan = ""

        self._prompt_message = self.HostAgent.message_constructor([self._desktop_screen_url], request_history, action_history, 
                                                                                                  self._desktop_windows_info, plan, self.request)
        self.request_logger.debug(json.dumps({"step": self._step, "prompt": self._prompt_message, "status": ""}))
        return self._prompt_message
    
    
    def get_response(self):

        try:
            self._response, self._cost = self.HostAgent.get_response(self._prompt_message, "HOSTAGENT", use_backup_engine=True)
        except Exception as e:
            log = json.dumps({"step": self._step, "status": str(e), "prompt": self._prompt_message})
            utils.print_with_color("Error occurs when calling LLM: {e}".format(e=str(e)), "red")
            self.request_logger.info(log)
            self._status = "ERROR"
        

    def parse_response(self):  
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

         # Get the application window
        self._app_window = self._desktop_windows_dict.get(self.control_label)
        # Get the application name
        self.app_root = control.get_application_name(self._app_window)
        try:
            self._app_window.is_normal()

        # Handle the case when the window interface is not available
        except Exception:
            utils.print_with_color("Window interface {title} not available for the visual element.".format(title=self._control_text), "red")
            self._status = "ERROR"
            return

        self._status = "CONTINUE"
        self._app_window.set_focus()


    def update_memory(self):

        round = self.HostAgent.get_round()

        host_agent_step_memory = MemoryItem()
        additional_memory = {"Step": self._step, "AgentStep": self.HostAgent.get_step(), "Round": round, "ControlLabel": self._control_text, "Action": "set_focus()", 
                                "Request": self.request, "Agent": "HostAgent", "AgentName": self.HostAgent.name, "Application": self.app_root, "Cost": self._cost, "Results": ""}
        
        host_agent_step_memory.set_values_from_dict(self._response_json)
        host_agent_step_memory.set_values_from_dict(additional_memory)
        self.HostAgent.add_memory(host_agent_step_memory)
        
        self.log(host_agent_step_memory.to_dict())
        memorized_action = {key: host_agent_step_memory.to_dict().get(key) for key in configs["HISTORY_KEYS"]}
        self.HostAgent.add_global_action_memory(memorized_action)
        

    def update_status(self):
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
    
        def __init__(self, log_path, photographer, request, request_logger, logger, app_agent, global_step, process_name, app_window, control_reannotate, prev_status):
            super().__init__(log_path, photographer, request, request_logger, logger, global_step, prev_status)

            self.AppAgent = app_agent
            self.process_name = process_name
            self.control_reannotate = control_reannotate
            self._app_window= app_window

            self._annotation_dict = None
            self._control_info = None
            self._operation = None
            self._args = None
            self._image_url = []
            self._control_reannotate = None



        def print_step_info(self):
            utils.print_with_color("Step {step}: Taking an action on application {application}.".format(step=self.global_step, application=self.process_name), "magenta")


        def capture_screenshot(self):
            
            screenshot_save_path = self.log_path + f"action_step{self.global_step}.png"
            annotated_screenshot_save_path = self.log_path + f"action_step{self.global_step}_annotated.png"
            concat_screenshot_save_path = self.log_path + f"action_step{self.global_step}_concat.png"

            if type(self.control_reannotate) == list and len(self.control_reannotate) > 0:
                control_list = self.control_reannotate
            else:
                control_list = control.find_control_elements_in_descendants(BACKEND, self._app_window, control_type_list = configs["CONTROL_LIST"], class_name_list = configs["CONTROL_LIST"])

            self._annotation_dict = self.photographer.get_annotation_dict(self._app_window, control_list, annotation_type="number")

            self.photographer.capture_app_window_screenshot(self._app_window, save_path=screenshot_save_path)
            self.photographer.capture_app_window_screenshot_with_annotation(self._app_window, control_list, annotation_type="number", save_path=annotated_screenshot_save_path)


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
            self._control_info = control.get_control_info_dict(self._annotation_dict, ["control_text", "control_type" if BACKEND == "uia" else "control_class"])


        def get_prompt_message(self):
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
                                                                                self._control_info, prev_plan, self.request, configs["INCLUDE_LAST_SCREENSHOT"])
            
            self.request_logger.debug(json.dumps({"step": self._step, "prompt": self._prompt_message, "status": ""}))


        def get_response(self):
            try:
                self._response, self._cost = self.AppAgent.get_response(self._prompt_message, "APPAGENT", use_backup_engine=True)
            except Exception as e:
                error_trace = traceback.format_exc()
                log = json.dumps({"step": self._step, "status": str(error_trace), "prompt": self._prompt_messag})
                utils.print_with_color("Error occurs when calling LLM: {e}".format(e=str(error_trace)), "red")
                self.request_logger.info(log)
                self._status = "ERROR"
                time.sleep(configs["SLEEP_TIME"])
                return
            
        def parse_response(self):
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


            except Exception as e:
                error_trace = traceback.format_exc()
                utils.print_with_color(f"Error Occurs at action execution in AppAgent at step {self.global_step}", "red")
                utils.print_with_color(str(error_trace), "red")
                utils.print_with_color(self._response, "red")
                self.error_log(self._response, str(error_trace))
                self._status = "ERROR"
           
        
        def update_memory(self):
            # Create a memory item for the app agent
            app_agent_step_memory = MemoryItem()

            app_root = control.get_application_name(self._app_window)
            HostAgent = self.AppAgent.get_host()
            round = HostAgent.get_round()
            
            additional_memory = {"Step": self._step, "AgentStep": self.AppAgent.get_step(), "Round": round, "Action": self._action, 
                                 "Request": self.request, "Agent": "ActAgent", "AgentName": self.AppAgent.name, "Application": app_root, "Cost": self._cost, "Results": self._results}
            app_agent_step_memory.set_values_from_dict(self._response_json)
            app_agent_step_memory.set_values_from_dict(additional_memory)

            self.AppAgent.add_memory(app_agent_step_memory)

            memorized_action = {key: app_agent_step_memory.to_dict().get(key) for key in configs["HISTORY_KEYS"]}
            HostAgent.add_global_action_memory(memorized_action)


        def update_status(self):
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

            return self._control_reannotate
 