import os
import json

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




def load_json_file(file_path):
    """
    Load a JSON file.
    :param file_path: The path to the file to load.
    :return: The loaded JSON data.
    """

    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def get_offline_config():
    """
    Get the list of offline indexers.
    :return: The list of offline indexers.
    """

    if os.path.exists("learner/records.json"):
        records = load_json_file("./learner/records.json")
    else:
        records = {}
    return records




    