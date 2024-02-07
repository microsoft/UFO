import argparse
from datetime import datetime

from .config.config import load_config
from .module import flow
from .utils import print_with_color


configs = load_config()


args = argparse.ArgumentParser()
args.add_argument("--task", help="The name of current task.",
                  type=str, default=datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
args.add_argument("--gptkey", help="GPT key.", type=str,
                  default=configs["OPENAI_API_KEY"])

parsed_args = args.parse_args()


if configs["API_TYPE"].lower() == "openai":
    headers = {
        "Content-Type": "application/json",
        "api-key": parsed_args.gptkey,
    }
elif configs["API_TYPE"].lower() == "aoai":
    headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {parsed_args.gptkey}"
        }
else:
    raise ValueError("API_TYPE should be either 'openai' or 'aoai'.")


def main():
    """
    Main function.
    """

    session = flow.Session(parsed_args.task)

    step = 0
    status = session.get_status()
    round = session.get_round()

    # Start the task
    while status.upper() not in ["ALLFINISH", "ERROR", "MAX_STEP_REACHED"]:

        round = session.get_round()
        
        if round > 0:
            session.set_new_round()
            status = session.get_status()
            if status == "ALLFINISH":
                break

        while status.upper() not in ["FINISH", "ERROR"] and step <= configs["MAX_STEP"]:

            session.process_application_selection(headers=headers)
            step = session.get_step()
            status = session.get_status()

            while status.upper() not in ["FINISH", "ERROR"] and step <= configs["MAX_STEP"]:
                session.process_action_selection(headers=headers)
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

        session.set_round(round+1)

    # Print the total cost
    total_cost = session.get_cost()
    formatted_cost = '${:.2f}'.format(total_cost)
    print_with_color(f"Request total cost is {formatted_cost}", "yellow")

    return status


if __name__ == "__main__":
    main()
