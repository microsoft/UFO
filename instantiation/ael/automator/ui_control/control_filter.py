# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import re
import warnings
from ufo.automator.ui_control.control_filter import ControlFilterFactory
from ael.config.config import Config

warnings.filterwarnings("ignore")
configs = Config.get_instance().config_data

class ControlFilterFactory(ControlFilterFactory):
    @staticmethod
    def items_to_keywords(items:list) -> list:
        """
        Gets keywords from the plan and request. 
        We only consider the words in the plan and request that are alphabetic or Chinese characters.
        :param plan (str): The plan to be parsed.
        :param request (str): The request to be parsed.
        Returns:
            list: A list of keywords extracted from the plan.
        """
        keywords = []
        for item in items:
            words = item.replace("\n", "").replace("'", "").replace("*","").strip(".").split()
            words = [word for word in words if word.isalpha() or bool(re.fullmatch(r'[\u4e00-\u9fa5]+', word))]
            keywords.extend(word for word in words if word not in keywords)
        return keywords