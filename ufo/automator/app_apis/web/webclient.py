# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from typing import Any, Dict, Type

import html2text
import requests

from ufo.automator.basic import CommandBasic, ReceiverBasic


class WebReceiver(ReceiverBasic):
    """
    The base class for Web COM client using crawl4ai.
    """

    _command_registry: Dict[str, Type[WebCommand]] = {}

    def __init__(self) -> None:
        """
        Initialize the Web COM client.
        """
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

    def web_crawler(self, url: str, ignore_link: bool) -> str:
        """
        Run the crawler with various options.
        :param url: The URL of the webpage.
        :param ignore_link: Whether to ignore the links.
        :return: The result markdown content.
        """

        try:
            # Get the HTML content of the webpage
            response = requests.get(url, headers=self._headers)
            response.raise_for_status()

            html_content = response.text

            # Convert the HTML content to markdown
            h = html2text.HTML2Text()
            h.ignore_links = ignore_link
            markdown_content = h.handle(html_content)

            return markdown_content

        except requests.RequestException as e:
            print(f"Error fetching the URL: {e}")

            return f"Error fetching the URL: {e}"

    @property
    def type_name(self):
        return "WEB"

    @property
    def xml_format_code(self) -> int:
        return 0  # This might not be applicable for web, adjust accordingly


class WebCommand(CommandBasic):
    """
    The base class for Web commands.
    """

    def __init__(self, receiver: WebReceiver, params: Dict[str, Any]) -> None:
        """
        Initialize the Web command.
        :param receiver: The receiver of the command.
        :param params: The parameters of the command.
        """
        super().__init__(receiver, params)
        self.receiver = receiver

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "web"


@WebReceiver.register
class WebCrawlerCommand(WebCommand):
    """
    The command to run the crawler with various options.
    """

    def execute(self):
        """
        Execute the command to run the crawler.
        :return: The result content.
        """
        return self.receiver.web_crawler(
            url=self.params.get("url"),
            ignore_link=self.params.get("ignore_link", False),
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "web_crawler"
