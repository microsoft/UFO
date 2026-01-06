# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import logging
import os
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class Config:
    _instance = None

    def __init__(self):
        # Load config here
        if os.getenv("RUN_CONFIGS", "true").lower() != "false":
            self.config_data = self.load_config()
        else:
            self.config_data = None

    @staticmethod
    def get_instance():
        """
        Get the instance of the Config class.
        :return: The instance of the Config class.
        """
        if Config._instance is None:
            Config._instance = Config()
        return Config._instance

    def load_config(self, config_path="ufo/config/") -> Dict[str, Any]:
        """
        Load the configuration from a YAML file and environment variables.

        :param config_path: The path to the YAML config file. Defaults to "./config.yaml".
        :return: Merged configuration from environment variables and YAML file.
        """

        # Copy environment variables to avoid modifying them directly
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TensorFlow warnings
        configs = dict(os.environ)

        current_path = os.getcwd()
        path = os.path.join(current_path, config_path)

        try:
            with open(os.path.join(path, "config.yaml"), "r") as file:
                yaml_data = yaml.safe_load(file)
            # Update configs with YAML data
            if yaml_data:
                configs.update(yaml_data)
            if os.path.exists(path + "config_dev.yaml"):
                with open(path + "config_dev.yaml", "r") as file:
                    yaml_dev_data = yaml.safe_load(file)
                configs.update(yaml_dev_data)
            if os.path.exists(path + "config_prices.yaml"):
                with open(path + "config_prices.yaml", "r") as file:
                    yaml_prices_data = yaml.safe_load(file)
                configs.update(yaml_prices_data)

            # Load MCP config from new location: config/ufo/mcp.yaml (preferred)
            new_mcp_path = os.path.join(current_path, "config/ufo/mcp.yaml")
            if os.path.exists(new_mcp_path):
                with open(new_mcp_path, "r") as file:
                    yaml_mcp_data = yaml.safe_load(file)
                configs["mcp"] = yaml_mcp_data
            # Fallback to legacy location: ufo/config/agent_mcp.yaml
            elif os.path.exists(path + "agent_mcp.yaml"):
                with open(path + "agent_mcp.yaml", "r") as file:
                    yaml_agent_mcp_data = yaml.safe_load(file)
                configs["mcp"] = yaml_agent_mcp_data
        except FileNotFoundError as e:

            logger.warning(
                f"Config file not found at {path}. Using only environment variables. Error: {e}"
            )

        return self.optimize_configs(configs)

    @staticmethod
    def update_api_base(configs: dict, agent: str) -> None:
        """
        Update the API base URL based on the API type.
        :param configs: The configuration dictionary.
        :param agent: The agent name.
        """

        # Check if the agent is in the configurations
        if agent not in configs:
            Warning(f"Agent {agent} not found in the configurations.")
            return

        if configs[agent]["API_TYPE"].lower() == "aoai":
            if "deployments" not in configs[agent]["API_BASE"]:
                configs[agent]["API_BASE"] = (
                    "{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}".format(
                        endpoint=(
                            configs[agent]["API_BASE"][:-1]
                            if configs[agent]["API_BASE"].endswith("/")
                            else configs[agent]["API_BASE"]
                        ),
                        deployment_name=configs[agent]["API_DEPLOYMENT_ID"],
                        api_version=configs[agent]["API_VERSION"],
                    )
                )
            configs[agent]["API_MODEL"] = configs[agent]["API_DEPLOYMENT_ID"]
        elif configs[agent]["API_TYPE"].lower() == "openai":
            if "chat/completions" in configs[agent]["API_BASE"]:
                configs[agent]["API_BASE"] = (
                    configs[agent]["API_BASE"][:-18]
                    if configs[agent]["API_BASE"].endswith("/")
                    else configs[agent]["API_BASE"][:-17]
                )

    @classmethod
    def optimize_configs(cls, configs: dict) -> Dict[str, Any]:
        """
        Optimize the configurations.
        :param configs: The configurations.
        :return: The optimized configurations.
        """
        cls.update_api_base(configs, "HOST_AGENT")
        cls.update_api_base(configs, "APP_AGENT")
        cls.update_api_base(configs, "BACKUP_AGENT")

        if isinstance(configs.get("CONTROL_BACKEND"), str):
            configs["CONTROL_BACKEND"] = [configs["CONTROL_BACKEND"]]

        return configs


def get_offline_learner_indexer_config():
    """
    Get the list of offline indexers obtained from the learner.
    :return: The list of offline indexers.
    """

    # The fixed path of the offline indexer config file.
    file_path = "learner/records.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            records = json.load(file)
    else:
        records = {}
    return records


def get_config() -> Optional[Dict[str, Any]]:
    """
    Get the configuration data from the Config singleton instance.

    NOTE: This function now uses the new ConfigLoader for consistency.
    The old Config class is kept for backward compatibility but delegates
    to the new loader.

    :return: The configuration data dictionary.
    """
    # Use new ConfigLoader instead of old Config class
    from config.config_loader import get_ufo_config

    config = get_ufo_config()
    # Convert to dict for backward compatibility
    return config.to_dict() if hasattr(config, "to_dict") else config._data
