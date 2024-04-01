"""entrance of exploration with ufo"""
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from datetime import datetime

from .config.config import load_config
from .utils import print_with_color
from .env.state_manager import WindowsAppEnv,calculate_reward,execute_task_summary,execute_exploration

configs = load_config()


args = argparse.ArgumentParser()
args.add_argument("--app", help="The name of exploration app.",
                  type=str, default='word')
args.add_argument("--exit_fail_times", help="The available max continuent times of failure.",
                  type=str, default=5)
parsed_args = args.parse_args()



def main():
    """
    Main function.
    """
    score_threshold = configs['SCORE_THRESHOLD']
    app_env = WindowsAppEnv(parsed_args.app,parsed_args.exit_fail_times,score_threshold)
    # todo: 解耦env class和不同agent的交互，可以修改成并行方式

    # Start the task
    while not app_env.is_done():
        # update the current state
        app_env.update_current_state()
        # not at the initial state
        if app_env.last_state is not None:
            reward = calculate_reward(app_env)
            if reward > score_threshold:
                task = execute_task_summary(app_env)
                # todo: record the task,ROUGE
                app_env.recent_fail_times = 0
            else:
                app_env.recent_fail_times += 1
        if app_env.is_done():
            break
        # at the initial state or not reach the failures times
        _,status = execute_exploration(app_env)
                


if __name__ == "__main__":
    main()
