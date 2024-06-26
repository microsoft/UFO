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

from ufo.automator.basic import CommandBasic, ReceiverBasic




class WebWinCOMReceiver(ReceiverBasic):
    """
    The base class for Web COM client using crawl4ai.
    """

    _command_registry: Dict[str, Type[CommandBasic]] = {}

    def __init__(self) -> None:
        """
        Initialize the Web COM client.
        :param url: The URL of the webpage.
        """
        self.client = self.create_crawler()
        self.chunking_strategy = RegexChunking(patterns=["\n\n"])
        self.extraction_strategy = None

    @lru_cache()
    def create_crawler(self):
        crawler = WebCrawler(verbose=True)
        crawler.warmup()
        return crawler

    def run_crawler(self, url: str, only_text: bool = False, screenshot: bool = False, 
                    chunking_strategy: Optional[Type] = None, extraction_strategy: Optional[Type] = None,
                    css_selector: Optional[str] = None, **kwargs) -> str:
        """
        Run the crawler with various options.
        :param url: The URL of the webpage.
        :param only_text: Whether to fetch only text.
        :param screenshot: Whether to take a screenshot.
        :param chunking_strategy: The chunking strategy to apply.
        :param extraction_strategy: The extraction strategy to apply.
        :param css_selector: The CSS selector for targeted extraction.
        :return: The result content.
        """
        print("-----------------------------callig crawler-------------------------------")
        result = self.client.run(
            url=url,
            only_text=only_text,
            screenshot=screenshot,
            chunking_strategy=self.chunking_strategy,
            extraction_strategy=self.extraction_strategy,
            css_selector=css_selector
        )

        if screenshot:
            with open("screenshot.png", "wb") as f:
                f.write(base64.b64decode(result.screenshot))
            return "Screenshot saved to 'screenshot.png'"
        return result.model_dump().get('markdown', '')

    @property
    def type_name(self):
        return "COM/WEB"

    @property
    def xml_format_code(self) -> int:
        return 0  # This might not be applicable for web, adjust accordingly


@WebWinCOMReceiver.register
class RunCrawlerCommand(CommandBasic):
    """
    The command to run the crawler with various options.
    """

    def execute(self):
        """
        Execute the command to run the crawler.
        :return: The result content.
        """
        return self.receiver.run_crawler(
            url=self.params.get("url"),
            only_text=self.params.get("only_text", False),
            screenshot=self.params.get("screenshot", False),
            chunking_strategy=self.params.get("chunking_strategy", RegexChunking()),
            extraction_strategy=self.params.get("extraction_strategy", None),
            css_selector=self.params.get("css_selector", None),
            **self.params.get("kwargs", {})
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "run_crawler"