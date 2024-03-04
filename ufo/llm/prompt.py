# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import List
import json

def prompt_construction(system_prompt: str, image_list: List, user_prompt: str, include_last_screenshot=False):
    """
    Construct the prompt for GPT-4 Visual.
    :param system_prompt: The system prompt.
    :param image_list: The list of images.
    :param user_prompt: The user prompt.
    :param include_last_screenshot: Whether to include the last screenshot.
    return: The prompt for GPT-4 Visual.
    """
    prompt_message = []
    if len(system_prompt) > 0:
        system_message = {
            "role": "system",
            "content": system_prompt
        }
        prompt_message.append(system_message)

    screenshot_text = []
    if include_last_screenshot:
        screenshot_text += ["Screenshot for the last step:"]

    screenshot_text += ["Current Screenshots:", "Annotated Screenshot:"]

    user_content = []

    for i, image in enumerate(image_list):
        user_content.append({
            "type": "text",
            "text": screenshot_text[i]
        })
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": image
            }
        })

    user_content.append({
        "type": "text",
        "text": user_prompt
    })

    user_message = {"role": "user", "content": user_content}
    prompt_message.append(user_message)

    return prompt_message


def app_selection_prompt_construction(prompt_template: str, user_request: str, app_info: dict):
    """
    Construct the prompt for app selection.
    :param prompt_template: The template of the prompt.
    :param user_request: The user request.
    :param app_info: The app info.
    return: The prompt for app selection.
    """

    return prompt_template["user"].format(user_request=user_request, applications=app_info)


def action_selection_prompt_construction(prompt_template: str, request_history: list, action_history: list, control_item: list, prev_plan: str, user_request: str, retrieved_docs: str=""):
    """
    Construct the prompt for action selection.
    :param prompt_template: The template of the prompt.
    :param action_history: The action history.
    :param control_item: The control item.
    :param user_request: The user request.
    :param retrieved_docs: The retrieved documents.
    return: The prompt for action selection.
    """

    prompt =  prompt_template["user"].format(action_history=json.dumps(action_history), request_history=json.dumps(request_history), 
                                          control_item=json.dumps(control_item), prev_plan=prev_plan, user_request=user_request)
    
    if retrieved_docs:
        prompt = prompt.format(retrieved_docs=retrieved_docs)
    return prompt



def retrived_documents_prompt_construction(header: str, separator: str, documents: list):
    """
    Construct the prompt for retrieved documents.
    :param header: The header of the prompt.
    :param separator: The separator of the prompt.
    :param documents: The retrieved documents.
    return: The prompt for retrieved documents.
    """

    prompts = "\n<{header}:>\n".format(header=header)
    for i, document in enumerate(documents):
        prompts += "\n"
        prompts += "[{separator} {i}:]".format(separator=separator, i=i+1)
        prompts += "\n"
        prompts += document
        prompts += "\n"
    return prompts

    
