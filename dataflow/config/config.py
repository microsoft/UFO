# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from ufo.config.config import Config


class Config(Config):
    _instance = None

    def __init__(self, config_path="dataflow/config/"):
        """
        Initializes the Config class.
        :param config_path: The path to the config file.
        """

        self.config_data = self.load_config(config_path)

    @staticmethod
    def get_instance():
        """
        Get the instance of the Config class.
        :return: The instance of the Config class.
        """

        if Config._instance is None:
            Config._instance = Config()

        return Config._instance

    def optimize_configs(self, configs):
        """
        Optimize the configurations.
        :param configs: The configurations to optimize.
        :return: The optimized configurations.
        """
        
        self.update_api_base(configs, "PREFILL_AGENT")
        self.update_api_base(configs, "FILTER_AGENT")

        return configs
