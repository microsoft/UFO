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