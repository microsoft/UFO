# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from .. import utils

from art import text2art
from typing import Tuple


WELCOME_TEXT = """
Welcome to use UFO🛸, A UI-focused Agent for Windows OS Interaction. 
{art}
Please enter your request to be completed🛸: """.format(
    art=text2art("UFO")
)


def first_request() -> str:
    """
    Ask for the first request.
    :return: The first request.
    """

    return input()


def new_request() -> Tuple[str, bool]:
    """
    Ask for a new request.
    :return: The new request and whether the conversation is complete.
    """

    utils.print_with_color(
        """Please enter your new request. Enter 'N' for exit.""", "cyan"
    )
    request = input()
    if request.upper() == "N":
        complete = True
    else:
        complete = False

    return request, complete


def experience_asker() -> bool:
    """
    Ask for saving the conversation flow for future reference.
    :return: Whether to save the conversation flow.
    """
    utils.print_with_color(
        """Would you like to save the current conversation flow for future reference by the agent?
[Y] for yes, any other key for no.""",
        "magenta",
    )

    ans = input()

    if ans.upper() == "Y":
        return True
    else:
        return False


def question_asker(question: str, index: int) -> str:
    """
    Ask for the user input for the question.
    :param question: The question to ask.
    :param index: The index of the question.
    :return: The user input.
    """

    utils.print_with_color(
        """[Question {index}:] {question}""".format(index=index, question=question),
        "cyan",
    )

    return input()


def sensitive_step_asker(action, control_text) -> bool:
    """
    Ask for confirmation for sensitive steps.
    :param action: The action to be performed.
    :param control_text: The control text.
    :return: Whether to proceed.
    """

    utils.print_with_color(
        "[Input Required:] UFO🛸 will apply {action} on the [{control_text}] item. Please confirm whether to proceed or not. Please input Y or N.".format(
            action=action, control_text=control_text
        ),
        "magenta",
    )

    while True:
        user_input = input().upper()

        if user_input == "Y":
            return True
        elif user_input == "N":
            return False
        else:
            print("Invalid choice. Please enter either Y or N. Try again.")
