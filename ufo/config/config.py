# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import yaml
import json
from ..utils import print_with_color

def load_config(config_path="ufo/config/config.yaml"):
    """
    Load the configuration from a YAML file and environment variables.

    :param config_path: The path to the YAML config file. Defaults to "./config.yaml".
    :return: Merged configuration from environment variables and YAML file.
    """
    # Copy environment variables to avoid modifying them directly
    configs = dict(os.environ)

    try:
        with open(config_path, "r") as file:
            yaml_data = yaml.safe_load(file)
        # Update configs with YAML data
        if yaml_data:
            configs.update(yaml_data)
    except FileNotFoundError:
        print_with_color(
            f"Warning: Config file not found at {config_path}. Using only environment variables.", "yellow")


    return configs

def load_llm_config(config_path="ufo/config/config_llm.yaml"):
    """
    Load the configuration from a YAML file and environment variables.

    :param config_path: The path to the YAML config file. Defaults to "./config.yaml".
    :return: Merged configuration from environment variables and YAML file.
    """
    # Copy environment variables to avoid modifying them directly
    configs = dict(os.environ)

    try:
        with open(config_path, "r") as file:
            yaml_data = yaml.safe_load(file)
        # Update configs with YAML data
        if yaml_data:
            configs.update(yaml_data)
    except FileNotFoundError:
        print_with_color(
            f"Warning: Config file not found at {config_path}. Using only environment variables.", "yellow")

    
    return optimize_configs(configs)


def parse_aoai_base(config):
    if 'deployments' not in config["API_BASE"]:
        config["API_BASE"] = "{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}".format(
                endpoint=config["API_BASE"][:-1] if config["API_BASE"].endswith(
                    "/") else config["API_BASE"],
                deployment_name=config["API_MODEL"],
                api_version=config["API_VERSION"]
        )
    return config["API_BASE"]

def update_api_base(configs, key):
    if not isinstance(configs[key], list):
        configs[key] = [configs[key]]
    for config in configs[key][1:]:
        if config["API_TYPE"].lower() == "aoai":
            config["API_BASE"] = parse_aoai_base(config)

def optimize_configs(configs):
    if len(configs["VISUAL"]) != configs["VISUAL"][0]["NUM"]+1 or \
        len(configs["NON_VISUAL"]) != configs["NON_VISUAL"][0]["NUM"]+1:
            raise ValueError("Number of APIs does not match number of API listt")
    update_api_base(configs, 'VISUAL')
    update_api_base(configs, 'NON_VISUAL')
    
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