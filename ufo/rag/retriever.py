# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from ..config.config import get_offline_learner_indexer_config, load_config
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
    


def get_offline_indexer_path(app_name: str):
    """
    Get the path to the offline indexer.
    :param app_name: The name of the application.
    :return: The path to the offline indexer.
    """
    offline_records = get_offline_learner_indexer_config()
    for key in offline_records:
        if key.lower() in app_name.lower():
            return offline_records[key]
        
    return None



def load_indexer(path: str):
    """
    Load the retriever.
    :param path: The path to load the retriever from.
    :return: The loaded retriever.
    """

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    db = FAISS.load_local(path, embeddings)

    return db



def create_online_search_retriever(query):
    """
    Create an online search indexer.
    :param query: The query to create an indexer for.
    :return: The created indexer.
    """
    
    bing_retriever = web_retriever.BingWebRetriever()

    result_list = bing_retriever.search(query, top_k=configs["RAG_ONLINE_SEARCH_TOPK"])
    documents = bing_retriever.create_documents(result_list)
    if len(documents) == 0:
        return None
    indexer = bing_retriever.create_indexer(documents)

    return Retriever(indexer)




def create_offline_doc_retriever(app_name):
    """
    Create an offline document indexer.
    :param app_name: The name of the application to create an indexer for.
    :return: The created indexer.
    """

    path = get_offline_indexer_path(app_name)

    if path:
        indexer = load_indexer(path)
        return Retriever(indexer)
    
    return None












    