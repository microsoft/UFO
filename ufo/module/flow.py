# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import logging
import os
import time
import json

from art import text2art
from pywinauto.uia_defines import NoPatternInterfaceError
from ..experience.summarizer import ExperienceSummarizer

from ..config.config import load_config
from ..ui_control import control, screenshot as screen
from ..ui_control.executor import ActionExecutor
from .. import utils
from ..agent.agent import HostAgent, AppAgent

configs = load_config()
BACKEND = configs["CONTROL_BACKEND"]



class Session(object):
    """
    A session for UFO.
    """
    def __init__(self, task):
        """
        Initialize a session.
        :param task: The name of current task.
        :param gpt_key: GPT key.
        """
        self.task = task
        self.step = 0
        self.round = 0
        self.action_history = []

        self.log_path = f"logs/{self.task}/"
        utils.create_folder(self.log_path)
        self.logger = self.initialize_logger(self.log_path, "response.log")
        self.request_logger = self.initialize_logger(self.log_path, "request.log")

        self.HostAgent = HostAgent("HostAgent", configs["APP_AGENT"]["VISUAL_MODE"], configs["APP_SELECTION_PROMPT"], configs["APP_SELECTION_EXAMPLE_PROMPT"], configs["API_PROMPT"])
        self.AppAgent = None

        self.status = "APP_SELECTION"
        self.application = ""
        self.app_root = ""
        self.app_window = None
        self.plan = ""
        self.request = ""
        self.results = ""
        self.cost = 0
        self.offline_doc_retriever = None
        self.online_doc_retriever = None
        self.experience_retriever = None
        self.control_reannotate = None

        welcome_text = """
Welcome to use UFO🛸, A UI-focused Agent for Windows OS Interaction. 
{art}
Please enter your request to be completed🛸: """.format(art=text2art("UFO"))

        utils.print_with_color(welcome_text, "cyan")
        
        self.request = input()
        self.request_history = []

    def process_application_selection(self):

        """
        Select an action.
        header: The headers of the request.
        return: The outcome, the application window, and the action log.
        """
        
        # Code for selecting an action
        utils.print_with_color("Step {step}: Selecting an application.".format(step=self.step), "magenta")
        desktop_save_path = self.log_path + f"action_step{self.step}.png"
        _ = screen.capture_screenshot_multiscreen(desktop_save_path)
        desktop_screen_url = utils.encode_image_from_path(desktop_save_path)

        self.results = ""

        desktop_windows_dict, desktop_windows_info = control.get_desktop_app_info_dict()

        
        app_selection_prompt_message = self.HostAgent.message_constructor([desktop_screen_url], self.request_history, self.action_history, 
                                                                                                  desktop_windows_info, self.plan, self.request)
        
        
        self.request_logger.debug(json.dumps({"step": self.step, "prompt": app_selection_prompt_message, "status": ""}))

        try:
            response_string, cost = self.HostAgent.get_response(app_selection_prompt_message, "APP", use_backup_engine=True)

        except Exception as e:
            log = json.dumps({"step": self.step, "status": str(e), "prompt": app_selection_prompt_message})
            utils.print_with_color("Error occurs when calling LLM: {e}".format(e=str(e)), "red")
            self.request_logger.info(log)
            self.status = "ERROR"
            return

        self.cost += cost

        try:
            response_json = self.HostAgent.response_to_dict(response_string)

            application_label = response_json["ControlLabel"]
            self.application = response_json["ControlText"]
            self.plan = response_json["Plan"]
            self.status = response_json["Status"]

            self.HostAgent.print_response(response_json)
            
            response_json["Step"] = self.step
            response_json["Round"] = self.round
            response_json["ControlLabel"] = self.application
            response_json["Action"] = "set_focus()"
            response_json["Request"] = self.request
            response_json["Agent"] = "AppAgent"
        
            
            if "FINISH" in self.status.upper() or self.application == "":
                self.status = "FINISH"
                response_json["Application"] = ""
                response_json = self.set_result_and_log("", response_json)
                return
                
            app_window = desktop_windows_dict[application_label]

            self.app_root = control.get_application_name(app_window)
            response_json["Application"] = self.app_root
            response_json = self.set_result_and_log("", response_json)

            try:
                app_window.is_normal()

            # Handle the case when the window interface is not available
            except NoPatternInterfaceError as e:
                self.error_logger(response_string, str(e))
                utils.print_with_color("Window interface {title} not available for the visual element.".format(title=self.application), "red")
                self.status = "ERROR"
                return
            
            self.status = "CONTINUE"
            self.app_window = app_window

            self.app_window.set_focus()

            # Initialize the AppAgent
            self.AppAgent = AppAgent("AppAgent", self.application, self.app_root, configs["ACTION_AGENT"]["VISUAL_MODE"], 
                                     configs["ACTION_SELECTION_PROMPT"], configs["ACTION_SELECTION_EXAMPLE_PROMPT"], configs["API_PROMPT"], self.app_window)
            
            # Initialize the document retriever
            if configs["RAG_OFFLINE_DOCS"]:
                utils.print_with_color("Loading offline document indexer for {app}...".format(app=self.application), "magenta")
                self.offline_doc_retriever = self.AppAgent.build_offline_docs_retriever()
            if configs["RAG_ONLINE_SEARCH"]:
                utils.print_with_color("Creating a Bing search indexer...", "magenta")
                self.online_doc_retriever = self.AppAgent.build_online_search_retriever(self.request, configs["RAG_ONLINE_SEARCH_TOPK"])
            if configs["RAG_EXPERIENCE"]:
                utils.print_with_color("Creating an experience indexer...", "magenta")
                experience_path = configs["EXPERIENCE_SAVED_PATH"]
                db_path = os.path.join(experience_path, "experience_db")
                self.experience_retriever = self.AppAgent.build_experience_retriever(db_path)

            time.sleep(configs["SLEEP_TIME"])

            self.step += 1
            self.HostAgent.update_step()
            self.HostAgent.update_status(self.status)

        except Exception as e:
            utils.print_with_color("Error Occurs at application selection.", "red")
            utils.print_with_color(str(e), "red")
            utils.print_with_color(response_string, "red")
            self.error_logger(response_string, str(e))
            self.status = "ERROR"

            return


    def process_action_selection(self):
        """
        Select an action.
        header: The headers of the request.
        return: The outcome, the application window, and the action log.
        """

        utils.print_with_color("Step {step}: Taking an action on application {application}.".format(step=self.step, application=self.application), "magenta")
        screenshot_save_path = self.log_path + f"action_step{self.step}.png"
        annotated_screenshot_save_path = self.log_path + f"action_step{self.step}_annotated.png"
        concat_screenshot_save_path = self.log_path + f"action_step{self.step}_concat.png"
        control_screenshot_save_path = self.log_path + f"action_step{self.step}_selected_controls.png"

        if type(self.control_reannotate) == list and len(self.control_reannotate) > 0:
            control_list = self.control_reannotate
        else:
            control_list = control.find_control_elements_in_descendants(self.app_window, configs["CONTROL_TYPE_LIST"])

        if self.app_window == None:
            self.status = "ERROR"
            utils.print_with_color("Required Application window is not available.", "red")
            return

            
        annotation_dict, _, _ = screen.control_annotations(self.app_window, screenshot_save_path, annotated_screenshot_save_path, control_list, anntation_type="number")
        control_info = control.get_control_info_dict(annotation_dict, ["control_text", "control_type" if BACKEND == "uia" else "control_class"])

        image_url = []

        if configs["INCLUDE_LAST_SCREENSHOT"]:
            
            last_screenshot_save_path = self.log_path + f"action_step{self.step - 1}.png"
            last_control_screenshot_save_path = self.log_path + f"action_step{self.step - 1}_selected_controls.png"
            image_url += [utils.encode_image_from_path(last_control_screenshot_save_path if os.path.exists(last_control_screenshot_save_path) else last_screenshot_save_path)]

        if configs["CONCAT_SCREENSHOT"]:
            screen.concat_images_left_right(screenshot_save_path, annotated_screenshot_save_path, concat_screenshot_save_path)
            image_url += [utils.encode_image_from_path(concat_screenshot_save_path)]
        else:
            screenshot_url = utils.encode_image_from_path(screenshot_save_path)
            screenshot_annotated_url = utils.encode_image_from_path(annotated_screenshot_save_path)
            image_url += [screenshot_url, screenshot_annotated_url]


        if configs["RAG_EXPERIENCE"]:
            examples, tips = self.AppAgent.rag_experience_retrieve(self.request, configs["RAG_EXPERIENCE_RETRIEVED_TOPK"])
        else:
            examples = []
            tips = []

        external_knowledge_prompt = self.AppAgent.external_knowledge_prompt_helper(self.request, configs["RAG_OFFLINE_DOCS_RETRIEVED_TOPK"], configs["RAG_ONLINE_RETRIEVED_TOPK"])
        action_selection_prompt_message = self.AppAgent.message_constructor(examples, tips, external_knowledge_prompt, image_url, self.request_history, self.action_history, control_info, self.plan, self.request, configs["INCLUDE_LAST_SCREENSHOT"])
        
        self.request_logger.debug(json.dumps({"step": self.step, "prompt": action_selection_prompt_message, "status": ""}))

        try:
            response_string, cost = self.AppAgent.get_response(action_selection_prompt_message, "ACTION", use_backup_engine=True)
        except Exception as e:
            log = json.dumps({"step": self.step, "status": str(e), "prompt": action_selection_prompt_message})
            utils.print_with_color("Error occurs when calling LLM: {e}".format(e=str(e)), "red")
            self.request_logger.info(log)
            self.status = "ERROR"
            time.sleep(configs["SLEEP_TIME"])
            return 
        
        self.cost += cost

        try:
            response_json = self.AppAgent.response_to_dict(response_string)

            control_label = response_json["ControlLabel"]
            control_text = response_json["ControlText"]
            function_call = response_json["Function"]
            args = utils.revise_line_breaks(response_json["Args"])

            control_selected = annotation_dict.get(control_label, "")

            self.AppAgent.print_response(response_json)


            # Build the executor for over the control item.
            executor = ActionExecutor(control_selected, self.app_window)

            # Compose the function call and the arguments string.
            action = utils.generate_function_call(function_call, args)

            # Set the result and log the result.
            self.plan = response_json["Plan"]
            self.status = response_json["Status"]

            response_json["Step"] = self.step
            response_json["Round"] = self.round
            response_json["Action"] = action
            response_json["Agent"] = "ActAgent"
            response_json["Request"] = self.request
            response_json["Application"] = self.app_root


        except Exception as e:
            # Return the error message and log the error.
            utils.print_with_color("Error occurs at step {step}".format(step=self.step), "red")
            utils.print_with_color(str(e), "red")
            self.status = "ERROR"

            self.error_logger(response_string, str(e))
            
            return
        
        self.step += 1
        self.AppAgent.update_step()
        self.AppAgent.update_status(self.status)

        # Handle the case when the control item is overlapped and the agent is unable to select the control item. Retake the annotated screenshot.
        if "SCREENSHOT" in self.status.upper():
            utils.print_with_color("Annotation is overlapped and the agent is unable to select the control items. New annotated screenshot is taken.", "magenta")
            self.control_reannotate = executor.annotation(args, annotation_dict)
            return


        self.control_reannotate = None
            

        # The task is finished and no further action is needed
        if self.status.upper() == "FINISH" and not control_selected:
            self.status = self.status.upper()
            response_json = self.set_result_and_log("", response_json)
            
            return
        
        if not self.safe_guard(action, control_text):
            return 
        
        # Take screenshot of the selected control
        screen.capture_screenshot_controls(self.app_window, [control_selected], control_screenshot_save_path)


        # Execute the action
        results = executor.execution(function_call, args)  
        response_json = self.set_result_and_log(results, response_json)

        time.sleep(configs["SLEEP_TIME"])

        return
    

    def experience_asker(self):
        utils.print_with_color("""Would you like to save the current conversation flow for future reference by the agent?
[Y] for yes, any other key for no.""", "cyan")
        
        ans = input()

        if ans == "Y":
            return True
        else:
            return False
        

    def experience_saver(self):
        """
        Save the current agent experience.
        """
        utils.print_with_color("Summarizing and saving the execution flow as experience...", "yellow")

        summarizer = ExperienceSummarizer(configs["ACTION_AGENT"]["VISUAL_MODE"], configs["EXPERIENCE_PROMPT"], configs["ACTION_SELECTION_EXAMPLE_PROMPT"], configs["API_PROMPT"])
        experience = summarizer.read_logs(self.log_path)
        summaries, total_cost = summarizer.get_summary_list(experience)

        experience_path = configs["EXPERIENCE_SAVED_PATH"]
        utils.create_folder(experience_path)
        summarizer.create_or_update_yaml(summaries, os.path.join(experience_path, "experience.yaml"))
        summarizer.create_or_update_vector_db(summaries, os.path.join(experience_path, "experience_db"))

        self.cost += total_cost
        utils.print_with_color("The experience has been saved.", "cyan")


    def set_new_round(self):
        """
        Start a new round.
        """
        self.request_history.append({self.round: self.request})
        self.round += 1
        utils.print_with_color("""Please enter your new request. Enter 'N' for exit.""", "cyan")
        
        self.request = input()

        if self.request.upper() == "N":
            self.status = "ALLFINISH"
            return
        else:
            self.status = "APP_SELECTION"
            return
        
    def get_round(self):
        """
        Get the round of the session.
        return: The round of the session.
        """
        return self.round
    
    def set_round(self, new_round):
        """
        Set the round of the session.
        """
        self.round = new_round


    def get_status(self):
        """
        Get the status of the session.
        return: The status of the session.
        """
        return self.status
    
    def get_step(self):
        """
        Get the step of the session.
        return: The step of the session.
        """
        return self.step

    def get_results(self):
        """
        Get the results of the session.
        return: The results of the session.
        """
        return self.results
    
    def get_cost(self):
        """
        Get the cost of the session.
        return: The cost of the session.
        """
        return self.cost
    
    def get_application_window(self):
        """
        Get the application of the session.
        return: The application of the session.
        """
        return self.app_window
    

    def set_result_and_log(self, result, response_json):
        """
        Set the result of the session, and log the result.
        """
        if type(result) != str and type(result) != list:
            result = ""
        response_json["Results"] = result
        self.logger.info(json.dumps(response_json))
        self.action_history.append({key: response_json[key] for key in configs["HISTORY_KEYS"]})
        self.results = result

        return response_json
    
    def safe_guard(self, action, control_text):
        """
        Safe guard for the session.
        """
        if "PENDING" in self.status.upper() and configs["SAFE_GUARD"]:
            utils.print_with_color("[Input Required:] UFO🛸 will apply {action} on the [{control_text}] item. Please confirm whether to proceed or not. Please input Y or N.".format(action=action, control_text=control_text), "magenta")
            decision = utils.yes_or_no()
            if not decision:
                utils.print_with_color("The user decide to stop the task.", "magenta")
                self.status = "FINISH"
                return False
            
            # Handle the PENDING_AND_FINISH case
            elif "FINISH" in self.plan:
                self.status = "FINISH"
        return True
    
    def error_logger(self, response_str, error):
        """
        Error handler for the session.
        """
        log = json.dumps({"step": self.step, "status": "ERROR", "response": response_str, "error": error})
        self.logger.info(log)

    @staticmethod
    def initialize_logger(log_path, log_filename):
        """
        Initialize logging.
        log_path: The path of the log file.
        log_filename: The name of the log file.
        return: The logger.
        """
        # Code for initializing logging
        logger = logging.Logger(log_filename)

        if not configs["PRINT_LOG"]:
            # Remove existing handlers if PRINT_LOG is False
            logger.handlers = []


        log_file_path = os.path.join(log_path, log_filename)
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.setLevel(configs["LOG_LEVEL"])

        return logger