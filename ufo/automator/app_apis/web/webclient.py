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
        self.browser = None
        self.current_page = None

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

    def navigate_to_url(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Navigate browser to a specific URL.
        """
        url = params.get("url")
        try:
            # For now, use requests to fetch the page
            response = requests.get(url, headers=self._headers)
            response.raise_for_status()
            self.current_page = response.text
            return {"success": True, "url": url, "status_code": response.status_code}
        except Exception as e:
            return {"error": f"Failed to navigate to URL: {str(e)}", "url": url}

    def click_element(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Click on a web page element.
        """
        selector = params.get("selector")
        wait_time = params.get("wait_time", 1.0)

        # Note: This would require a browser automation library like Selenium
        return {
            "info": "Browser automation not available. Would require Selenium/Playwright.",
            "selector": selector,
        }

    def type_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Type text into a web form field.
        """
        selector = params.get("selector")
        text = params.get("text")
        clear_first = params.get("clear_first", True)

        # Note: This would require a browser automation library
        return {
            "info": "Browser automation not available. Would require Selenium/Playwright.",
            "selector": selector,
            "text": text,
        }

    def get_page_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the text content of the current web page.
        """
        selector = params.get("selector")

        try:
            if not self.current_page:
                return {"error": "No page loaded. Use navigate_to_url first."}

            if selector:
                # Would need BeautifulSoup for CSS selector parsing
                try:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(self.current_page, "html.parser")
                    elements = soup.select(selector)
                    content = [elem.get_text().strip() for elem in elements]
                    return {"selector": selector, "content": content}
                except ImportError:
                    return {"error": "BeautifulSoup not available for CSS selectors"}
            else:
                # Return full page text
                try:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(self.current_page, "html.parser")
                    text_content = soup.get_text()
                    return {"content": text_content.strip()}
                except ImportError:
                    # Fallback to html2text
                    h = html2text.HTML2Text()
                    h.ignore_links = True
                    text_content = h.handle(self.current_page)
                    return {"content": text_content}
        except Exception as e:
            return {"error": f"Failed to get page content: {str(e)}"}

    def get_page_title(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the title of the current web page.
        """
        try:
            if not self.current_page:
                return {"error": "No page loaded. Use navigate_to_url first."}

            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(self.current_page, "html.parser")
                title = soup.find("title")
                title_text = title.get_text().strip() if title else "No title found"
                return {"title": title_text}
            except ImportError:
                # Fallback using regex
                import re

                title_match = re.search(
                    r"<title[^>]*>([^<]+)</title>", self.current_page, re.IGNORECASE
                )
                title_text = title_match.group(1) if title_match else "No title found"
                return {"title": title_text}
        except Exception as e:
            return {"error": f"Failed to get page title: {str(e)}"}

    def scroll_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scroll the web page.
        """
        direction = params.get("direction")
        amount = params.get("amount", 300)

        # Note: This would require browser automation
        return {
            "info": "Browser automation not available. Would require Selenium/Playwright.",
            "direction": direction,
            "amount": amount,
        }

    def wait_for_element(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wait for an element to appear on the page.
        """
        selector = params.get("selector")
        timeout = params.get("timeout", 10.0)

        # Note: This would require browser automation with wait capabilities
        return {
            "info": "Browser automation not available. Would require Selenium/Playwright.",
            "selector": selector,
            "timeout": timeout,
        }

    def take_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Take a screenshot of the current web page.
        """
        full_page = params.get("full_page", False)

        # Note: This would require browser automation
        return {
            "info": "Browser automation not available. Would require Selenium/Playwright.",
            "full_page": full_page,
        }

    def execute_javascript(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute JavaScript code on the current page.
        """
        script = params.get("script")

        # Note: This would require browser automation
        return {
            "info": "Browser automation not available. Would require Selenium/Playwright.",
            "script": script,
        }

    def get_element_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the text content of a specific element.
        """
        selector = params.get("selector")

        try:
            if not self.current_page:
                return {"error": "No page loaded. Use navigate_to_url first."}

            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(self.current_page, "html.parser")
                element = soup.select_one(selector)
                if element:
                    return {"selector": selector, "text": element.get_text().strip()}
                else:
                    return {"error": f"Element not found: {selector}"}
            except ImportError:
                return {"error": "BeautifulSoup not available for CSS selectors"}
        except Exception as e:
            return {"error": f"Failed to get element text: {str(e)}"}

    def get_element_attribute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get an attribute value of a specific element.
        """
        selector = params.get("selector")
        attribute = params.get("attribute")

        try:
            if not self.current_page:
                return {"error": "No page loaded. Use navigate_to_url first."}

            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(self.current_page, "html.parser")
                element = soup.select_one(selector)
                if element:
                    attr_value = element.get(attribute)
                    return {
                        "selector": selector,
                        "attribute": attribute,
                        "value": attr_value,
                    }
                else:
                    return {"error": f"Element not found: {selector}"}
            except ImportError:
                return {"error": "BeautifulSoup not available for CSS selectors"}
        except Exception as e:
            return {"error": f"Failed to get element attribute: {str(e)}"}

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


@WebReceiver.register
class NavigateToUrlCommand(WebCommand):
    def execute(self):
        return self.receiver.navigate_to_url(params=self.params)

    @classmethod
    def name(cls) -> str:
        return "navigate_to_url"


@WebReceiver.register
class ClickElementCommand(WebCommand):
    def execute(self):
        return self.receiver.click_element(params=self.params)

    @classmethod
    def name(cls) -> str:
        return "click_element"


@WebReceiver.register
class TypeTextCommand(WebCommand):
    def execute(self):
        return self.receiver.type_text(params=self.params)

    @classmethod
    def name(cls) -> str:
        return "type_text"


@WebReceiver.register
class GetPageContentCommand(WebCommand):
    def execute(self):
        return self.receiver.get_page_content(params=self.params)

    @classmethod
    def name(cls) -> str:
        return "get_page_content"


@WebReceiver.register
class GetPageTitleCommand(WebCommand):
    def execute(self):
        return self.receiver.get_page_title(params=self.params)

    @classmethod
    def name(cls) -> str:
        return "get_page_title"


@WebReceiver.register
class ScrollPageCommand(WebCommand):
    def execute(self):
        return self.receiver.scroll_page(params=self.params)

    @classmethod
    def name(cls) -> str:
        return "scroll_page"


@WebReceiver.register
class WaitForElementCommand(WebCommand):
    def execute(self):
        return self.receiver.wait_for_element(params=self.params)

    @classmethod
    def name(cls) -> str:
        return "wait_for_element"


@WebReceiver.register
class TakeScreenshotCommand(WebCommand):
    def execute(self):
        return self.receiver.take_screenshot(params=self.params)

    @classmethod
    def name(cls) -> str:
        return "take_screenshot"


@WebReceiver.register
class ExecuteJavascriptCommand(WebCommand):
    def execute(self):
        return self.receiver.execute_javascript(params=self.params)

    @classmethod
    def name(cls) -> str:
        return "execute_javascript"


@WebReceiver.register
class GetElementTextCommand(WebCommand):
    def execute(self):
        return self.receiver.get_element_text(params=self.params)

    @classmethod
    def name(cls) -> str:
        return "get_element_text"


@WebReceiver.register
class GetElementAttributeCommand(WebCommand):
    def execute(self):
        return self.receiver.get_element_attribute(params=self.params)

    @classmethod
    def name(cls) -> str:
        return "get_element_attribute"
