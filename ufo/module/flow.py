# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import logging
import os
import time
import json
import yaml

from art import text2art
from pywinauto.uia_defines import NoPatternInterfaceError

from ..rag import retriever_factory
from ..config.config import load_config
from ..llm import llm_call
from ..llm import prompter
from ..ui_control import control
from ..ui_control import screenshot as screen
from ..utils import (create_folder, encode_image_from_path,
                     generate_function_call, json_parser, print_with_color,
                     revise_line_breaks, yes_or_no)

configs = load_config()
BACKEND = configs["CONTROL_BACKEND"]
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 



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
        create_folder(self.log_path)
        self.logger = initialize_logger(self.log_path, "response.log")
        self.request_logger = initialize_logger(self.log_path, "request.log")

        self.app_selection_prompt = prompter.load_prompt(configs["APP_SELECTION_PROMPT"], configs["APP_AGENT_VISUAL_MODE"])
        self.action_selection_prompt = prompter.load_prompt(configs["ACTION_SELECTION_PROMPT"], configs["ACTION_AGENT_VISUAL_MODE"])

        self.app_selection_example_prompt = prompter.load_prompt(configs["APP_SELECTION_EXAMPLE_PROMPT"], configs["APP_AGENT_VISUAL_MODE"])
        self.action_selection_example_prompt = prompter.load_prompt(configs["ACTION_SELECTION_EXAMPLE_PROMPT"], configs["ACTION_AGENT_VISUAL_MODE"])

        self.app_selection_api_prompt = prompter.load_prompt(configs["API_PROMPT"], configs["APP_AGENT_VISUAL_MODE"])
        self.action_selection_api_prompt = prompter.load_prompt(configs["API_PROMPT"], configs["ACTION_AGENT_VISUAL_MODE"])


        self.status = "APP_SELECTION"
        self.application = ""
        self.app_window = None
        self.plan = ""
        self.request = ""
        self.results = ""
        self.cost = 0
        self.offline_doc_retriever = None
        self.online_doc_retriever = None

        

        print_with_color("""Welcome to use UFO🛸, A UI-focused Agent for Windows OS Interaction. 
{art}
Please enter your request to be completed🛸: """.format(art=text2art("UFO")), "cyan")
        
        self.request = input()
        self.request_history = []

    def process_application_selection(self):

        """
        Select an action.
        header: The headers of the request.
        return: The outcome, the application window, and the action log.
        """
        
        # Code for selecting an action
        print_with_color("Step {step}: Selecting an application.".format(step=self.step), "magenta")
        desktop_save_path = self.log_path + f"action_step{self.step}.png"
        _ = screen.capture_screenshot_multiscreen(desktop_save_path)
        desktop_screen_url = encode_image_from_path(desktop_save_path)

        self.results = ""

        desktop_windows_dict, desktop_windows_info = control.get_desktop_app_info_dict()

        app_example_prompt = prompter.examples_prompt_helper(self.app_selection_example_prompt)
        api_prompt = prompter.api_prompt_helper(self.app_selection_api_prompt, verbose=0)

        app_selection_prompt_system_message = prompter.system_prompt_construction(self.app_selection_prompt, api_prompt, app_example_prompt)
        app_selection_prompt_user_message = prompter.user_prompt_construction(self.app_selection_prompt, self.request_history, self.action_history, desktop_windows_info, self.plan, self.request)
        
        app_selection_prompt_message = prompter.prompt_construction(app_selection_prompt_system_message, [desktop_screen_url], app_selection_prompt_user_message, False, configs["APP_AGENT_VISUAL_MODE"])

        
        self.request_logger.debug(json.dumps({"step": self.step, "prompt": app_selection_prompt_message, "status": ""}))

        try:
            response_string, cost = llm_call.get_completion(app_selection_prompt_message, configs["APP_AGENT_VISUAL_MODE"])

        except Exception as e:
            log = json.dumps({"step": self.step, "status": str(e), "prompt": app_selection_prompt_message})
            print_with_color("Error occurs when calling LLM: {e}".format(e=str(e)), "red")
            self.request_logger.info(log)
            self.status = "ERROR"
            return


        self.cost += cost

        try:
            response_json = json_parser(response_string)

            application_label = response_json["ControlLabel"]
            self.application = response_json["ControlText"]
            observation = response_json["Observation"]
            thought = response_json["Thought"]
            self.plan = response_json["Plan"]
            self.status = response_json["Status"]
            comment = response_json["Comment"]

            print_with_color("Observations👀: {observation}".format(observation=observation), "cyan")
            print_with_color("Thoughts💡: {thought}".format(thought=thought), "green")
            print_with_color("Selected application📲: {application}".format(application=self.application), "yellow")
            print_with_color("Next Plan📚: {plan}".format(plan=str(self.plan).replace("\\n", "\n")), "cyan")
            print_with_color("Comment💬: {comment}".format(comment=comment), "green")
            
            
            response_json["Step"] = self.step
            response_json["ControlLabel"] = self.application
            response_json["Action"] = "set_focus()"
            response_json["Agent"] = "AppAgent"
        
            

            if "FINISH" in self.status.upper() or self.application == "":
                self.status = "FINISH"
                response_json["Application"] = ""
                response_json = self.set_result_and_log("", response_json)
                return
                
            app_window = desktop_windows_dict[application_label]

            response_json["Application"] = control.get_application_name(app_window)
            response_json = self.set_result_and_log("", response_json)

            try:
                app_window.is_normal()

            # Handle the case when the window interface is not available
            except NoPatternInterfaceError as e:
                self.error_logger(response_string, str(e))
                print_with_color("Window interface {title} not available for the visual element.".format(title=self.application), "red")
                self.status = "ERROR"
                return
            
            self.status = "CONTINUE"
            self.app_window = app_window

            self.app_window.set_focus()

            if configs["RAG_OFFLINE_DOCS"]:
                print_with_color("Loading offline document indexer for {app}...".format(app=self.application), "magenta")
                offline_retriever_factory = retriever_factory.OfflineDocRetrieverFactory(self.application)
                self.offline_doc_retriever = offline_retriever_factory.create_offline_doc_retriever()
            if configs["RAG_ONLINE_SEARCH"]:
                print_with_color("Creating a Bing search indexer...", "magenta")
                offline_retriever_factory = retriever_factory.OnlineDocRetrieverFactory(self.request)
                self.online_doc_retriever = offline_retriever_factory.create_online_search_retriever()

            time.sleep(configs["SLEEP_TIME"])

            self.step += 1

        except Exception as e:
            print_with_color("Error Occurs at application selection.", "red")
            print_with_color(str(e), "red")
            print_with_color(response_string, "red")
            self.error_logger(response_string, str(e))
            self.status = "ERROR"

            return


    def process_action_selection(self):
        """
        Select an action.
        header: The headers of the request.
        return: The outcome, the application window, and the action log.
        """

        print_with_color("Step {step}: Taking an action on application {application}.".format(step=self.step, application=self.application), "magenta")
        screenshot_save_path = self.log_path + f"action_step{self.step}.png"
        annotated_screenshot_save_path = self.log_path + f"action_step{self.step}_annotated.png"
        concat_screenshot_save_path = self.log_path + f"action_step{self.step}_concat.png"
        control_screenshot_save_path = self.log_path + f"action_step{self.step}_selected_controls.png"



        if BACKEND == "uia":
            control_list = control.find_control_elements_in_descendants(self.app_window, configs["CONTROL_TYPE_LIST"])
        else:
            control_list = control.find_control_elements_in_descendants(self.app_window, configs["CONTROL_TYPE_LIST"])

        while True:
            if self.app_window == None:
                self.status = "ERROR"
                print_with_color("Required Application window is not available.", "red")
                return
            
            annotation_dict, _, _ = screen.control_annotations(self.app_window, screenshot_save_path, annotated_screenshot_save_path, control_list, anntation_type="number")
            control_info = control.get_control_info_dict(annotation_dict, ["control_text", "control_type" if BACKEND == "uia" else "control_class"])

            image_url = []

            if configs["INCLUDE_LAST_SCREENSHOT"]:
                
                last_screenshot_save_path = self.log_path + f"action_step{self.step - 1}.png"
                last_control_screenshot_save_path = self.log_path + f"action_step{self.step - 1}_selected_controls.png"
                image_url += [encode_image_from_path(last_control_screenshot_save_path if os.path.exists(last_control_screenshot_save_path) else last_screenshot_save_path)]

            if configs["CONCAT_SCREENSHOT"]:
                screen.concat_images_left_right(screenshot_save_path, annotated_screenshot_save_path, concat_screenshot_save_path)
                image_url += [encode_image_from_path(concat_screenshot_save_path)]
            else:
                screenshot_url = encode_image_from_path(screenshot_save_path)
                screenshot_annotated_url = encode_image_from_path(annotated_screenshot_save_path)
                image_url += [screenshot_url, screenshot_annotated_url]

            action_example_prompt = prompter.examples_prompt_helper(self.action_selection_example_prompt)
            api_prompt = prompter.api_prompt_helper(self.action_selection_api_prompt, verbose=1)

            action_selection_prompt_system_message = prompter.system_prompt_construction(self.action_selection_prompt, api_prompt, action_example_prompt)
            action_selection_prompt_user_message = prompter.user_prompt_construction(self.action_selection_prompt, self.request_history, self.action_history, control_info, self.plan, self.request, self.rag_prompt())
            
            action_selection_prompt_message = prompter.prompt_construction(action_selection_prompt_system_message, image_url, action_selection_prompt_user_message, configs["INCLUDE_LAST_SCREENSHOT"], configs["ACTION_AGENT_VISUAL_MODE"])
            
            
            self.request_logger.debug(json.dumps({"step": self.step, "prompt": action_selection_prompt_message, "status": ""}))

            try:
                response_string, cost = llm_call.get_completion(action_selection_prompt_message, configs["ACTION_AGENT_VISUAL_MODE"])
            except Exception as e:
                log = json.dumps({"step": self.step, "status": str(e), "prompt": action_selection_prompt_message})
                print_with_color("Error occurs when calling LLM: {e}".format(e=str(e)), "red")
                self.request_logger.info(log)
                self.status = "ERROR"
                time.sleep(configs["SLEEP_TIME"])
                return 
            
            self.cost += cost

            try:
                response_json = json_parser(response_string)

                observation = response_json["Observation"]
                thought = response_json["Thought"]
                control_label = response_json["ControlLabel"]
                control_text = response_json["ControlText"]
                function_call = response_json["Function"]
                args = revise_line_breaks(response_json["Args"])

                action = generate_function_call(function_call, args)
                self.plan = response_json["Plan"]
                self.status = response_json["Status"]
                comment = response_json["Comment"]
                response_json["Step"] = self.step
                response_json["Action"] = action
                response_json["Agent"] = "ActAgent"
                response_json["Application"] = control.get_application_name(self.app_window)


                print_with_color("Observations👀: {observation}".format(observation=observation), "cyan")
                print_with_color("Thoughts💡: {thought}".format(thought=thought), "green")
                print_with_color("Selected item🕹️: {control_text}, Label: {label}".format(control_text=control_text, label=control_label), "yellow")
                print_with_color("Action applied⚒️: {action}".format(action=action), "blue")
                print_with_color("Status📊: {status}".format(status=self.status), "blue")
                print_with_color("Next Plan📚: {plan}".format(plan=str(self.plan).replace("\\n", "\n")), "cyan")
                print_with_color("Comment💬: {comment}".format(comment=comment), "green")


            except Exception as e:
                print_with_color("Error occurs at step {step}".format(step=self.step), "red")
                print_with_color(str(e), "red")
                print_with_color(response_string, "red")
                self.status = "ERROR"

                self.error_logger(response_string, str(e))
                
                return
            
            if "SCREENSHOT" in self.status.upper():
                print_with_color("Annotation is overlapped and the agent is unable to select the control items. New annotated screenshot is taken.", "magenta")
                annotated_screenshot_save_path = self.log_path + f"action_step{self.step}_annotated_retake.png"
                if "control_labels" in args:
                    selected_controls_labels = args["control_labels"]
                    control_list = [annotation_dict[str(label)] for label in selected_controls_labels]
                continue
            
            break

        # The task is finish and no further action is needed
        if self.status.upper() == "FINISH" and function_call == "":
            self.status = self.status.upper()
            response_json = self.set_result_and_log("", response_json)
            
            return
        
        self.step += 1

        if function_call:
        # Handle the case when the action is an image summary or switch app
            if function_call.lower() == "summary":
                response_json = self.set_result_and_log(args["text"], response_json)
                return
        else:
            response_json = self.set_result_and_log("", response_json)
            return
        
        # Action needed.
        control_selected = annotation_dict.get(control_label, self.app_window)
        # print_with_color("Actual control name: {name}".format(name=control_selected.element_info.name), "magenta")
        control_selected.set_focus()

        if not self.safe_guard(action, control_text):
            return 
        
        
        # Take screenshot of the selected control
        screen.capture_screenshot_controls(self.app_window, [control_selected], control_screenshot_save_path)
        control.wait_enabled(control_selected)
        results = control.execution(control_selected, function_call, args)
        response_json = self.set_result_and_log(results, response_json)

        time.sleep(configs["SLEEP_TIME"])

        return
    

    def rag_prompt(self):
        """
        Retrieving documents for the user request.
        :return: The retrieved documents string.
        """
        
        retrieved_docs = ""
        if self.offline_doc_retriever:
            offline_docs = self.offline_doc_retriever.retrieve("How to {query} for {app}".format(query=self.request, app=self.application), configs["RAG_OFFLINE_DOCS_RETRIEVED_TOPK"], filter=None)
            offline_docs_prompt = prompter.retrived_documents_prompt_helper("Help Documents", "Document", [doc.metadata["text"] for doc in offline_docs])
            retrieved_docs += offline_docs_prompt

        if self.online_doc_retriever:
            online_search_docs = self.online_doc_retriever.retrieve(self.request, configs["RAG_ONLINE_RETRIEVED_TOPK"], filter=None)
            online_docs_prompt = prompter.retrived_documents_prompt_helper("Online Search Results", "Search Result", [doc.page_content for doc in online_search_docs])
            retrieved_docs += online_docs_prompt

        return retrieved_docs


    def set_new_round(self):
        """
        Start a new round.
        """
        self.request_history.append({self.round: self.request})
        self.round += 1
        print_with_color("""Please enter your new request. Enter 'N' for exit.""", "cyan")
        
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
            print_with_color("[Input Required:] UFO🛸 will apply {action} on the [{control_text}] item. Please confirm whether to proceed or not. Please input Y or N.".format(action=action, control_text=control_text), "magenta")
            decision = yes_or_no()
            if not decision:
                print_with_color("The user decide to stop the task.", "magenta")
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