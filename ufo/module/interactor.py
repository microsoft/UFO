# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from .. import utils

from art import text2art


WELCOME_TEXT = """
Welcome to use UFO🛸, A UI-focused Agent for Windows OS Interaction. 
{art}
Please enter your request to be completed🛸: """.format(art=text2art("UFO"))


def first_request():

    return input()


def new_request():
     
    utils.print_with_color("""Please enter your new request. Enter 'N' for exit.""", "cyan")
    return input()



def experience_asker() -> bool:
        utils.print_with_color("""Would you like to save the current conversation flow for future reference by the agent?
[Y] for yes, any other key for no.""", "magenta")
        
        ans = input()

        if ans.upper() == "Y":
            return True
        else:
            return False
        

def sensitive_step_asker(action, control_text) -> bool:

    utils.print_with_color("[Input Required:] UFO🛸 will apply {action} on the [{control_text}] item. Please confirm whether to proceed or not. Please input Y or N.".format(action=action, control_text=control_text), "magenta")

    while True:
        user_input = input().upper()

        if user_input == 'Y':
            return True
        elif user_input == 'N':
            return False
        else:
            print("Invalid choice. Please enter either Y or N. Try again.")
        

