# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from ..config.config import get_offline_learner_indexer_config, load_config
from ..utils import print_with_color
from . import web_retriever


configs = load_config()

class Retriever:
    """
    Class to retrieve documents.
    """

    def __init__(self, indexer) -> None:
        self.indexer = indexer


    def retrieve(self, query: str, top_k: int, filter=None):
        """
        Retrieve the document from the given query.
        :param query: The query to retrieve the document from.
        :param top_k: The number of documents to retrieve.
        :filter: The filter to apply to the retrieved documents.
        :return: The document from the given query.
        """
        return self.indexer.similarity_search(query, top_k, filter=filter)
    



class OfflineDocRetrieverFactory:
    """
    Class to create offline retrievers.
    """
    def __init__(self, app_name:str) -> None:
        """
        Create a new OfflineDocRetrieverFactory.
        :appname: The name of the application.
        """
        self.app_name = app_name


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
    

    def load_indexer(self, path: str):
        """
        Load the retriever.
        :param path: The path to load the retriever from.
        :return: The loaded retriever.
        """

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        db = FAISS.load_local(path, embeddings)

        return db
    

    def create_offline_doc_retriever(self):
        """
        Create an offline document indexer.
        :return: The created indexer.
        """

        path = self.get_offline_indexer_path()

        if path:
            print_with_color("Loading offline indexer from {path}...".format(path=path), "cyan")
            try:
                indexer = self.load_indexer(path)
                return Retriever(indexer)
            except:
                print_with_color("Error: Failed to load offline indexer from {path}.".format(path=path), "red")
                return None
        
        return None



class OnlineDocRetrieverFactory:
    """
    Class to create online retrievers.
    """

    def __init__(self, query:str) -> None:
        """
        Create a new OfflineDocRetrieverFactory.
        :appname: The name of the application.
        """
        self.query = query

    def create_online_search_retriever(self):
        """
        Create an online search indexer.
        :param query: The query to create an indexer for.
        """
        
        bing_retriever = web_retriever.BingSearchWeb()
        result_list = bing_retriever.search(self.query, top_k=configs["RAG_ONLINE_SEARCH_TOPK"])
        documents = bing_retriever.create_documents(result_list)
        if len(documents) == 0:
            return None
        indexer = bing_retriever.create_indexer(documents)
        print_with_color("Online indexer created successfully for {num} searched results.".format(num=len(documents)), "cyan")
        return Retriever(indexer)












    