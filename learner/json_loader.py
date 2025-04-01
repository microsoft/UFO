# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from typing import Dict, List

from langchain.docstore.document import Document

from . import basic


class JsonLoader(basic.BasicDocumentLoader):
    """
    Class to load JSON documents.
    """

    def __init__(self, directory: str = None):
        """
        Create a new JSONLoader.
        """

        super().__init__()
        self.extensions = ".json"
        self.directory = directory

    @staticmethod
    def load_json_document(file: str) -> Dict:
        """
        Load the JSON document from the given file path.
        :param file: The file path to load the JSON document from.
        :return: The JSON document.
        """
        with open(file, "r") as f:
            try:
                document = json.load(f)
            except json.JSONDecodeError:
                document = {}

        return document

    def construct_document(self):
        """
        Construct a langchain document list.
        Each json file is a document with the following structure:
        {
            "request": "The user request",
            "guidance": ["The step-by-step guidance to fulfill the request"]
        }
        :return: The langchain document list.
        """
        documents = []
        for file in self.load_file_name():

            document = self.load_json_document(file)
            request = document.get("request", "")
            guidance_steps = document.get("guidance", [])
            guidance = "\n".join([step for step in guidance_steps])

            metadata = {"title": request, "summary": request, "text": guidance}
            document = Document(page_content=request, metadata=metadata)

            documents.append(document)
        return documents
