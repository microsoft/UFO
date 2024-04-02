"""Class to manage the seeds."""
import os
import json
from ..config.config import load_config
import datetime
from ..utils import copy_file

configs = load_config()

seeds_dir = configs['SEEDS_HUB']
cache_path = configs['CACHE_PATH']

class SeedManager:
    def __init__(self,app_name) -> None:
        if not os.path.exists(cache_path):
            os.makedirs(cache_path,exist_ok=True)
        if not os.path.exists(seeds_dir):
            os.makedirs(seeds_dir,exist_ok=True)
        self.seed_app_path = os.path.join(seeds_dir,app_name)
        self.cache_app_path = os.path.join(cache_path,app_name)

    def get_seeds(self):
        """
        Get the seeds from the seeds directory.
        :return: The seed file path.
        """
        for seed in os.listdir(self.seed_app_path):
            seed_file_path = os.path.join(self.seed_app_path, seed)
            copy_file_path = copy_file(
                seed_file_path,
                self.os.path.join(self.cache_app_path,seed.split(".")[-2] + datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + seed.split(".")[-1])
            )
            if os.path.isfile(copy_file_path):
                yield copy_file_path  

