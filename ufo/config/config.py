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
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # Suppress TensorFlow warnings
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

    # Update the API base URL for AOAI
    if configs["API_TYPE"].lower() == "aoai":
        configs["OPENAI_API_BASE"] = "{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}".format(
            endpoint=configs["OPENAI_API_BASE"][:-1] if configs["OPENAI_API_BASE"].endswith(
                "/") else configs["OPENAI_API_BASE"],
            deployment_name=configs["AOAI_DEPLOYMENT"],
            api_version=configs["API_VERSION"]
        )

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