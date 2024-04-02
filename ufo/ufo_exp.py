"""entrance of exploration with ufo"""
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from datetime import datetime

from .config.config import load_config
from .utils import print_with_color
from .env.state_manager import WindowsAppEnv,calculate_reward,execute_task_summary,execute_exploration
from .env.tasks_recorder import TaskRecorder
from .env.seeds_manager import SeedManager
configs = load_config()


args = argparse.ArgumentParser()
args.add_argument("--app", help="The name of exploration app.",
                  type=str, default='word')
parsed_args = args.parse_args()


# todo: action agent,summary agent parallel
# todo: record tasks and ROUGE

def main():
    """
    Main function.
    """
    assert parsed_args.app.lower() in configs['EXP_APPS'].keys(), f"Exploration for App {parsed_args.app} is not supported."
    score_threshold = configs['SCORE_THRESHOLD']
    exit_fail_times = configs['EXIT_FAIL_TIMES']
    app_root_name = configs['EXP_APPS'][parsed_args.app.lower()]
    task_recorder = TaskRecorder(parsed_args.app.lower())
    seed_manager = SeedManager(parsed_args.app.lower())
    app_env = WindowsAppEnv(app_root_name,exit_fail_times,score_threshold)

    for seed in seed_manager.get_seeds():
        # Start by open a copy of the original seed file
        app_env.start(seed)
        # get the current state
        app_env.update_current_state()
        init_state = app_env.init_state
        # Start exploration loop
        while not app_env.is_done():
            # update the current state
            app_env.update_current_state()
            # not at the initial state
            if app_env.last_state is not None:
                reward = calculate_reward(app_env)
                if reward > score_threshold:
                    task_description = execute_task_summary(app_env)
                    task_recorder.record_task(app_env.history_actions,app_env.history_states,init_state,task_description)
                    app_env.recent_fail_times = 0
                else:
                    app_env.recent_fail_times += 1
            if app_env.is_done():
                break
            # at the initial state or not reach the failures times
            _,status = execute_exploration(app_env)
            if not status:
                app_env.reset()
            app_env.step()
        # Close the seed file and open the next seed file
        app_env.quit()


if __name__ == "__main__":
    main()
