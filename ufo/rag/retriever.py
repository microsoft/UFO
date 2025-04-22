# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from abc import ABC, abstractmethod

from langchain_community.vectorstores import FAISS

from ufo.config.config import get_offline_learner_indexer_config
from ufo.rag import web_search
from ufo.utils import print_with_color, get_hugginface_embedding


class RetrieverFactory:
    """
    Factory class to create retrievers.
    """

    @staticmethod
    def create_retriever(retriever_type: str, *args, **kwargs):
        """
        Create a retriever based on the given type.
        :param retriever_type: The type of retriever to create.
        :return: The created retriever.
        """
        if retriever_type == "offline":
            return OfflineDocRetriever(*args, **kwargs)
        elif retriever_type == "experience":
            return ExperienceRetriever(*args, **kwargs)
        elif retriever_type == "online":
            return OnlineDocRetriever(*args, **kwargs)
        elif retriever_type == "demonstration":
            return DemonstrationRetriever(*args, **kwargs)
        else:
            raise ValueError("Invalid retriever type: {}".format(retriever_type))


class Retriever(ABC):
    """
    Class to retrieve documents.
    """

    def __init__(self) -> None:
        """
        Create a new Retriever.
        """

        self.indexer = self.get_indexer()

        pass

    @abstractmethod
    def get_indexer(self):
        """
        Get the indexer.
        :return: The indexer.
        """
        pass

    def retrieve(self, query: str, top_k: int, filter=None):
        """
        Retrieve the document from the given query.
        :param query: The query to retrieve the document from.
        :param top_k: The number of documents to retrieve.
        :filter: The filter to apply to the retrieved documents.
        :return: The document from the given query.
        """
        if not self.indexer:
            return []

        results = self.indexer.similarity_search(query, top_k, filter=filter)

        if not results:
            return []
        else:
            return results


class OfflineDocRetriever(Retriever):
    """
    Class to create offline retrievers.
    """

    def __init__(self, app_name: str) -> None:
        """
        Create a new OfflineDocRetriever.
        :appname: The name of the application.
        """
        self.app_name = app_name
        indexer_path = self.get_offline_indexer_path()
        self.indexer = self.get_indexer(indexer_path)

    def get_offline_indexer_path(self):
        """
        Get the path to the offline indexer.
        :return: The path to the offline indexer.
        """
        offline_records = get_offline_learner_indexer_config()
        for key in offline_records:
            if key.lower() in self.app_name.lower():
                return offline_records[key]

        return None

    def get_indexer(self, path: str):
        """
        Load the retriever.
        :param path: The path to load the retriever from.
        :return: The loaded retriever.
        """

        if path:
            print_with_color(
                "Loading offline indexer from {path}...".format(path=path), "cyan"
            )
        else:
            return None

        try:
            db = FAISS.load_local(
                path, get_hugginface_embedding(), allow_dangerous_deserialization=True
            )
            return db
        except Exception as e:
            print_with_color(
                "Warning: Failed to load experience indexer from {path}, error: {error}.".format(
                    path=path, error=e
                ),
                "yellow",
            )
            return None


class ExperienceRetriever(Retriever):
    """
    Class to create experience retrievers.
    """

    def __init__(self, db_path) -> None:
        """
        Create a new ExperienceRetriever.
        :param db_path: The path to the database.
        """
        self.indexer = self.get_indexer(db_path)

    def get_indexer(self, db_path: str):
        """
        Create an experience indexer.
        :param db_path: The path to the database.
        """

        try:
            db = FAISS.load_local(
                db_path,
                get_hugginface_embedding(),
                allow_dangerous_deserialization=True,
            )
            return db
        except Exception as e:
            print_with_color(
                "Warning: Failed to load experience indexer from {path}, error: {error}.".format(
                    path=db_path, error=e
                ),
                "yellow",
            )
            return None


class OnlineDocRetriever(Retriever):
    """
    Class to create online retrievers.
    """

    def __init__(self, query: str, top_k: int) -> None:
        """
        Create a new OfflineDocRetriever.
        :query: The query to create an indexer for.
        :top_k: The number of documents to retrieve.
        """
        self.query = query
        self.indexer = self.get_indexer(top_k)

    def get_indexer(self, top_k: int):
        """
        Create an online search indexer.
        :param top_k: The number of documents to retrieve.
        :return: The created indexer.
        """

        bing_retriever = web_search.BingSearchWeb()
        result_list = bing_retriever.search(self.query, top_k=top_k)
        documents = bing_retriever.create_documents(result_list)
        if len(documents) == 0:
            return None
        try:
            indexer = bing_retriever.create_indexer(documents)
            print_with_color(
                "Online indexer created successfully for {num} searched results.".format(
                    num=len(documents)
                ),
                "cyan",
            )
        except Exception as e:
            print_with_color(
                "Warning: Failed to create online indexer, error: {error}.".format(
                    error=e
                ),
                "yellow",
            )
            return None

        return indexer


class DemonstrationRetriever(Retriever):
    """
    Class to create demonstration retrievers.
    """

    def __init__(self, db_path) -> None:
        """
        Create a new DemonstrationRetriever.
        :db_path: The path to the database.
        """
        self.indexer = self.get_indexer(db_path)

    def get_indexer(self, db_path: str):
        """
        Create a demonstration indexer.
        :db_path: The path to the database.
        """

        try:
            db = FAISS.load_local(
                db_path,
                get_hugginface_embedding(),
                allow_dangerous_deserialization=True,
            )
            return db
        except Exception as e:
            print_with_color(
                "Warning: Failed to load experience indexer from {path}, error: {error}.".format(
                    path=db_path, error=e
                ),
                "yellow",
            )
            return None
