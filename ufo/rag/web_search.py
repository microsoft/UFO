# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import logging
import requests
from langchain.docstore.document import Document
from langchain.text_splitter import HTMLHeaderTextSplitter
from langchain_community.vectorstores import FAISS

from config.config_loader import get_ufo_config
from ufo.utils import get_hugginface_embedding

ufo_config = get_ufo_config()
logger = logging.getLogger(__name__)


class BingSearchWeb:
    """
    Class to retrieve web documents.
    """

    def __init__(self):
        """
        Create a new WebRetriever.
        """
        self.api_key = ufo_config.rag.bing_api_key

    def search(self, query: str, top_k: int = 1):
        """
        Retrieve the web document from the given URL.
        :param url: The URL to retrieve the web document from.
        :return: The web document from the given URL.
        """
        url = f"https://api.bing.microsoft.com/v7.0/search?q={query}"
        if top_k > 0:
            url += f"&count={top_k}"
        try:
            response = requests.get(
                url, headers={"Ocp-Apim-Subscription-Key": self.api_key}
            )
        except requests.RequestException as e:
            logger.warning(f"Error when searching: {e}")
            return None
        result_list = []

        for item in response.json()["webPages"]["value"]:
            result_list.append(
                {"name": item["name"], "url": item["url"], "snippet": item["snippet"]}
            )

        return result_list

    def get_url_text(self, url: str):
        """
        Retrieve the web document from the given URL.
        :param url: The URL to retrieve the web document from.
        :return: The web text from the given URL.
        """
        print(f"Getting search result for {url}")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=[])
                document = html_splitter.split_text(response.text)
                return document
            else:
                logger.warning(
                    f"Error in getting search result for {url}, error code: {response.status_code}."
                )
                return [Document(page_content="", metadata={"url": url})]
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error in getting search result for {url}: {e}.")
            return [Document(page_content="", metadata={"url": url})]

    def create_documents(self, result_list: list):
        """
        Create documents from the given result list.
        :param result_list: The result list to create documents from.
        :return: The documents from the given result list.
        """
        document_list = []

        for result in result_list:
            documents = self.get_url_text(result["url"])
            for document in documents:
                page_content = document.page_content
                metadata = document.metadata
                metadata["url"] = result["url"]
                metadata["name"] = result["name"]
                metadata["snippet"] = result["snippet"]

                document = Document(page_content=page_content, metadata=metadata)
                document_list.append(document)

        return document_list

    def create_indexer(self, documents: list):
        """
        Create an indexer for the given query.
        :param query: The query to create an indexer for.
        :return: The created indexer.
        """

        db = FAISS.from_documents(documents, get_hugginface_embedding())

        return db
