# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import basic
import utils
import os
from langchain_community.document_loaders import UnstructuredXMLLoader
import xml.etree.ElementTree as ET


class XMLLoader(basic.Loader):
    """
    Class to load XML documents.
    """

    def __init__(self, directory: str = None):
        """
        Create a new XMLLoader.
        """

        super().__init__()
        self.extensions = ".xml"
        self.directory = directory
    

    def get_microsoft_document_metadata(self, file: str):
        """
        Get the metadata for the given file.
        :param file: The file to get the metadata for.
        :return: The metadata for the given file.
        """

        if not os.path.exists(file):
            return {'title': os.path.basename(file), 'summary': os.path.basename(file)}

        tree = ET.parse(file)
        root = tree.getroot()

        # Extracting title
        if root.find('title') is not None:
            title = root.find('title').text
        else:
            title = None

        # Extracting content summary
            
        if root.find('Content-Summary') is not None:
            summary = root.find('Content-Summary').attrib['value']
        else:
            summary = None

        return {'title': title, 'summary': summary}
    

    def get_microsoft_document_text(self, file: str):
        """
        Get the text for the given file.
        :param file: The file to get the text for.
        :return: The text for the given file.
        """
        return UnstructuredXMLLoader(file).load()[0]
    

    def construct_document_list(self):
        """
        Construct a document from the given file.
        :param file: The file to construct the document from.
        :return: The constructed document.
        """
        documents = []
        for file in self.load_file_name():
            text = self.get_microsoft_document_text(file)
            metadata = self.get_microsoft_document_metadata(file + ".meta")
            title = metadata["title"]
            summary = metadata["summary"]

            document = {
                'title': title,
                'summary': summary,
                'text':text
            }
            documents.append(document)

        return documents

    
    
