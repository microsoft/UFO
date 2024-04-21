# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from datetime import datetime

from .config.config import Config
from .module import flow, sessions, interactor
from .utils import print_with_color


configs = Config.get_instance().config_data


args = argparse.ArgumentParser()
args.add_argument("--task", help="The name of current task.",
                  type=str, default=datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))

parsed_args = args.parse_args()



def main():
    """
    Main function.
    """

    session = sessions.Session(parsed_args.task)

    step = 0
    status = session.get_status()
    round = session.get_round()

    # Start the task
    while status.upper() not in ["COMPLETE", "ERROR", "MAX_STEP_REACHED"]:

        round = session.get_round()
        
        if status == "FINISH":
            session.set_new_round()
            status = session.get_status()
            if status == "COMPLETE":
                if interactor.experience_asker():
                    session.experience_saver()
                break

        while status.upper() not in ["FINISH", "ERROR"] and step <= configs["MAX_STEP"]:
            session.process_application_selection()
            step = session.get_step()
            status = session.get_status()

            while status.upper() == "CONTINUE" and step <= configs["MAX_STEP"]:
                session.process_action_selection()
                status = session.get_status()
                step = session.get_step()

                if status == "APP_SELECTION":
                    print_with_color(
                        "Step {step}: Switching to New Application".format(step=step), "magenta")
                    app_window = session.get_application_window()
                    app_window.minimize()
                    break

            if status == "FINISH":
                print_with_color("Task Completed.", "magenta")
                break

            if step > configs["MAX_STEP"]:
                print_with_color("Max step reached.", "magenta")
                status = "MAX_STEP_REACHED"
                break

        result = session.get_results()
        round = session.get_round()


        # Print the result
        if result != "":
            print_with_color("Result for round {round}:".format(
                round=round), "magenta")
            print_with_color("{result}".format(result=result), "yellow")


    # Print the total cost
    total_cost = session.get_cost()
    if isinstance(total_cost, float):
        formatted_cost = '${:.2f}'.format(total_cost)
        print_with_color(f"Request total cost is {formatted_cost}", "yellow")

    return status


if __name__ == "__main__":
    main()
