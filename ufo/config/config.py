# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import yaml
import json
from ..utils import print_with_color

def load_config(config_path="ufo/config/"):
    """
    Load the configuration from a YAML file and environment variables.

    :param config_path: The path to the YAML config file. Defaults to "./config.yaml".
    :return: Merged configuration from environment variables and YAML file.
    """
    # Copy environment variables to avoid modifying them directly
    configs = dict(os.environ)

    path = config_path

    try:
        with open(path + "config.yaml", "r") as file:
            yaml_data = yaml.safe_load(file)
        # Update configs with YAML data
        if yaml_data:
            configs.update(yaml_data)
        with open(path + "config_llm.yaml", "r") as file:
            yaml_llm_data = yaml.safe_load(file)
        # Update configs with YAML data
        if yaml_data:
            configs.update(yaml_llm_data)
    except FileNotFoundError:
        print_with_color(
            f"Warning: Config file not found at {config_path}. Using only environment variables.", "yellow")


    return optimize_configs(configs)


def update_api_base(configs, agent, key):
    if configs[agent][key]["API_TYPE"].lower() == "aoai":
        if 'deployments' not in configs[agent][key]["API_BASE"]:
            configs[agent][key]["API_BASE"] = "{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}".format(
                    endpoint=configs[agent][key]["API_BASE"][:-1] if configs[agent][key]["API_BASE"].endswith(
                        "/") else configs[agent][key]["API_BASE"],
                    deployment_name=configs[agent][key]["API_MODEL"],
                    api_version=configs[agent][key]["API_VERSION"]
            )
        

def optimize_configs(configs):
    update_api_base(configs,'APP_AGENT', 'VISUAL')
    update_api_base(configs,'APP_AGENT', 'NON_VISUAL')
    update_api_base(configs, 'ACTION_AGENT', 'VISUAL')
    update_api_base(configs, 'ACTION_AGENT', 'NON_VISUAL')
    
    return configs

def get_offline_learner_indexer_config():
    """
    Get the list of offline indexers obtained from the learner.
    :return: The list of offline indexers.
    """

    # The fixed path of the offline indexer config file.
    file_path = "learner/records.json"
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            records = json.load(file)
    else:
        records = {}
    return records