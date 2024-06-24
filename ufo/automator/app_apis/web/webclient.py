from abc import abstractmethod
import os
import time
from crawl4ai.web_crawler import WebCrawler
from crawl4ai.chunking_strategy import *
from crawl4ai.extraction_strategy import *
from crawl4ai.crawler_strategy import *
from rich import print
from rich.console import Console
from functools import lru_cache

from typing import Dict, Type

from ufo.automator.app_apis.basic import WinCOMCommand, WinCOMReceiverBasic
from ufo.automator.basic import CommandBasic



class WebWinCOMReceiver(WinCOMReceiverBasic):
    """
    The base class for Web COM client using crawl4ai.
    """

    _command_registry: Dict[str, Type[CommandBasic]] = {}

    def __init__(self, url: str) -> None:
        """
        Initialize the Web COM client.
        :param url: The URL of the webpage.
        """
        self.client = self.create_crawler()
        self.chunking_strategy = ChunkingStrategy()
        self.extraction_strategy = ExtractionStrategy()

    @lru_cache()
    def create_crawler(self):
        crawler = WebCrawler(verbose=True)
        crawler.warmup()
        return crawler

    def basic_usage(self, url: str) -> str:
        """
        Fetch the HTML content of the webpage.
        :return: The HTML content.
        """
        result = self.client.run(url=url, only_text=True)
        return result.model_dump().items()['markdown']

    def screenshot_usage(self, url: str) -> str:
        result = self.client.run(url=url, screenshot=True)
        with open("screenshot.png", "wb") as f:
            f.write(base64.b64decode(result.screenshot))
        return result.model_dump().items()['markdown']

    def add_chunking_strategy(self, url: str, strategy, **kwargs) -> str:
        result = self.client.run(url=url, chunking_strategy=strategy(**kwargs))
        
        return result.model_dump().items()['markdown']

    def add_extraction_strategy(self, url: str, strategy, **kwargs) -> str:
        result = self.client.run(url=url, extraction_strategy=strategy(**kwargs))

        return result.model_dump().items()['markdown']

    @property
    def type_name(self):
        return "COM/WEB"

    @property
    def xml_format_code(self) -> int:
        return 0  # This might not be applicable for web, adjust accordingly


# class WebClient(WebCOMReceiverBasic):
#     """
#     The class for handling specific webpage actions.
#     """

#     def get_page_content(self) -> str:
#         """
#         Fetch the HTML content of the webpage.
#         :return: The HTML content.
#         """
#         result = self.client.run(url=self.url, only_text=True)
#         return result.html


@WebWinCOMReceiver.register
class BasicFetchContentCommand(WinCOMCommand):
    """
    The command to find an element by its ID.
    """

    def execute(self):
        """
        Execute the command to find an element by ID.
        :return: The HTML of the found element.
        """
        return self.receiver.basic_usage(self.params.get("url"))

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "basic_fetch_content"


@WebWinCOMReceiver.register
class FetchContentScreenshotCommand(WinCOMCommand):
    """
    The command to find elements by their tag name.
    """

    def execute(self):
        """
        Execute the command to find elements by tag name.
        :return: A list of found elements.
        """
        return self.receiver.screenshot_usage(self.params.get("url"))

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "fetch_content_with_screenshot"


@WebWinCOMReceiver.register
class FetchContentScreenshotCommand(WinCOMCommand):
    """
    The command to find elements by their tag name.
    """

    def execute(self):
        """
        Execute the command to find elements by tag name.
        :return: A list of found elements.
        """
        return self.receiver.find_elements_by_tag(self.params.get("tag_name"))

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "fetch_content_with_screenshot"