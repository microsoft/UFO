# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import heapq
import sentence_transformers
import warnings

warnings.filterwarnings("ignore")

class ControlFilterFactory:  
    """  
    Factory class to filter control items.  
    """  
  
    @staticmethod  
    def create_control_filter(control_filter_type: str, *args, **kwargs):  
        """  
        Create a control filter model based on the given type.  
        :param control_filter_type: The type of control filter model to create.  
        :return: The created retriever.  
        """  
        if control_filter_type == "text":  
            return TextControlFilter(*args, **kwargs)  
        elif control_filter_type == "semantic":  
            return SemanticControlFilter(*args, **kwargs)  
        elif control_filter_type == "icon":  
            return IconControlFilter(*args, **kwargs)  
        else:  
            raise ValueError("Invalid retriever type: {}".format(control_filter_type)) 
        
      

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

    def get_embedding(self, content):
        """
        Encodes the given object into an embedding.
        Args:
            content: The content to encode.
        Returns:
            The embedding of the object.
        """
        return self.model.encode(content)

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

    @staticmethod
    def cos_sim(embedding1, embedding2):
        """
        Computes the cosine similarity between two embeddings.
        """
        return sentence_transformers.util.cos_sim(embedding1, embedding2)


class TextControlFilter:
    """
    A class that provides methods for filtering control items based on keywords.
    """

    @staticmethod
    def control_filter(filtered_control_info, control_items, keywords):
        """
        Filters control items based on keywords.
        Args:
            filtered_control_info (list): A list of control items that have already been filtered.
            control_items (list): A list of control items to be filtered.
            keywords (list): A list of keywords to filter the control items.
        """
        for control_item in control_items:
            if control_item not in filtered_control_info:
                control_text = control_item['control_text'].lower()
                if any(keyword in control_text or control_text in keyword for keyword in keywords):
                    filtered_control_info.append(control_item)

class SemanticControlFilter(ControlFilterModel):
    """
    A class that represents a semantic model for control filtering.
    """

    def control_filter_score(self, control_text, keywords):
        """
        Calculates the score for a control item based on the similarity between its text and a set of keywords.
        Args:
            control_text (str): The text of the control item.
            keywords (list): A list of keywords.
        Returns:
            float: The score indicating the similarity between the control text and the keywords.
        """
        keywords_embedding = self.get_embedding(keywords)
        control_text_embedding = self.get_embedding(control_text)
        return max(self.cos_sim(control_text_embedding, keywords_embedding).tolist()[0])

    def control_filter(self, filtered_control_info, control_items, keywords, top_k):
        """
        Filters control items based on their similarity to a set of keywords.
        Args:
            filtered_control_info (list): A list of already filtered control items.
            control_items (list): A list of control items to be filtered.
            keywords (list): A list of keywords.
            top_k (int): The number of top control items to be selected.
        """
        scores = []
        for control_item in control_items:
            if control_item not in filtered_control_info:
                control_text = control_item['control_text'].lower()
                score = self.control_filter_score(control_text, keywords)
            else:
                score = -100.0
            scores.append(score)
        topk_items = heapq.nlargest(top_k, enumerate(scores), key=lambda x: x[1])
        topk_indices = [item[0] for item in topk_items]

        filtered_control_info.extend([control_items[i] for i in topk_indices])

class IconControlFilter(ControlFilterModel):
    """
    Represents a model for filtering control icons based on keywords.
    Attributes:
        Inherits attributes from ControlFilterModel.
    Methods:
        control_filter_score(control_icon, keywords): Calculates the score of a control icon based on its similarity to the given keywords.
        control_filter(filtered_control_info, control_items, annotation_coor_dict, screenshot, keywords, top_k): Filters control items based on their scores and returns the top-k items.
    """

    def control_filter_score(self, control_icon, keywords):
        """
        Calculates the score of a control icon based on its similarity to the given keywords.
        Args:
            control_icon: The control icon image.
            keywords: The keywords to compare the control icon against.
        Returns:
            The maximum similarity score between the control icon and the keywords.
        """
        keywords_embedding = self.get_embedding(keywords)
        control_icon_embedding = self.get_embedding(control_icon)
        return max(self.cos_sim(control_icon_embedding, keywords_embedding).tolist()[0])

    def control_filter(self, filtered_control_info, control_items, annotation_coor_dict, screenshot, keywords, top_k):
        """
        Filters control items based on their scores and returns the top-k items.
        Args:
            filtered_control_info: The list of already filtered control items.
            control_items: The list of all control items.
            annotation_coor_dict: A dictionary mapping control labels to their coordinates.
            screenshot: The screenshot image.
            keywords: The keywords to compare the control icons against.
            top_k: The number of top items to return.
        Returns:
            The list of top-k control items based on their scores.
        """
        scores = []
        for label, coor in annotation_coor_dict.items():
            if label not in [info['label'] for info in filtered_control_info]:
                crop_img = screenshot.crop(coor)
                score = self.control_filter_score(crop_img, keywords)
                scores.append((score, label))
            else:
                scores.append((-100.0, label))
        topk_items = heapq.nlargest(top_k, scores, key=lambda x: x[0])
        topk_labels = [item[1] for item in topk_items]

        filtered_control_info.extend([control_item for control_item in control_items if control_item['label'] in topk_labels ])