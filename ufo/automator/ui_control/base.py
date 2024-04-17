# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import warnings, sentence_transformers
warnings.filterwarnings("ignore")

class ControlFilterModel:
    """
    ControlFilterModel represents a model for filtering control items.
    """

    _instances = {}

    def __new__(cls, model_path):
        """
        Creates a new instance of ControlFilterModel.

        Args:
            model_path (str): The path to the model.

        Returns:
            ControlFilterModel: The ControlFilterModel instance.
        """
        if model_path not in cls._instances: 
            instance = super(ControlFilterModel, cls).__new__(cls)
            instance.model = cls.load_model(model_path)
            cls._instances[model_path] = instance
        return cls._instances[model_path]
    
    @staticmethod
    def load_model(model_path):
        """
        Loads the model from the given model path.

        Args:
            model_path (str): The path to the model.

        Returns:
            SentenceTransformer: The loaded SentenceTransformer model.
        """
        return sentence_transformers.SentenceTransformer(model_path)
    
    def get_embedding(self, obj):
        """
        Encodes the given object into an embedding.

        Args:
            obj: The object to encode.

        Returns:
            The embedding of the object.
        """
        return self.model.encode(obj)
    
    def control_filter(self, keywords, control_item):
            """
            Calculates the cosine similarity between the embeddings of the given keywords and the control item.

            Args:
                keywords (str): The keywords to be used for calculating the similarity.
                control_item (str): The control item to be compared with the keywords.

            Returns:
                float: The cosine similarity between the embeddings of the keywords and the control item.
            """
            keywords_embedding = self.get_embedding(keywords)
            control_item_embedding = self.get_embedding(control_item)
            return self.cos_sim(keywords_embedding, control_item_embedding)
    
    def cos_sim(self, embedding1, embedding2):
        """
        Computes the cosine similarity between two embeddings.
        """
        return sentence_transformers.util.cos_sim(embedding1, embedding2)
            