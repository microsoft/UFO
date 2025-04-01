# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
from learner import utils
from abc import ABC, abstractmethod


class BasicDocumentLoader(ABC):
    """
    A class to load documents from a list of files with a given extension list.
    """

    def __init__(self, extensions: str = None, directory: str = None):
        """
        Create a new BasicDocumentLoader.
        :param extensions: The extensions to load.
        """
        self.extensions = extensions
        self.directory = directory

    def load_file_name(self):
        """
        Load the documents from the given directory.
        :param directory: The directory to load from.
        :return: The list of loaded documents.
        """
        return utils.find_files_with_extension(self.directory, self.extensions)

    @abstractmethod
    def construct_document(self):
        """
        Load the documents from the given directory.
        :param directory: The directory to load from.
        :return: The list of loaded documents.
        """
        pass
