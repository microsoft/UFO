# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import heapq
from ...utils import LazyImport

import time
import re
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
    
    @staticmethod
    def append_filtered_control_info(filtered_control_info, control_infos):
            """
            Appends the given control_info to the filtered_control_info list if it is not already present.

            Args:
                filtered_control_info (list): The list of filtered control information.
                control_info: The control information to be appended.

            Returns:
                list: The updated filtered_control_info list.
            """
            if control_infos:
                if filtered_control_info:
                    filtered_control_info.extend([control_info for control_info in control_infos\
                        if control_info not in filtered_control_info])
                    return filtered_control_info
                else:
                    return control_infos
            
            return filtered_control_info
    
    @staticmethod
    def plan_to_keywords(plan:str, topk_plan:int, is_first_round: bool) -> list:
        """
        Gets keywords from the plan. 
        We only consider the words in the plan that are alphabetic or Chinese characters.
        Args:
            plan (str): The plan to be parsed.
            topk_plan (int): The number of top plans to be considered.
            is_first_round(boolean): The boolean value indicating whether it is the first round.
        Returns:
            list: A list of keywords extracted from the plan.
        """
        if is_first_round:
            plans = str(plan).split("\n")
        else:
            plans = str(plan).split("\n")[:topk_plan]
            
        keywords = []
        for plan in plans:
            words = plan.replace("'", "").strip(".").split()
            words = [word for word in words if word.isalpha() or bool(re.fullmatch(r'[\u4e00-\u9fa5]+', word))]
            keywords.extend(words)
        return keywords
    

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
        import sentence_transformers
        
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
    def remove_stopwords(keywords):
        """
        Removes stopwords from the given list of keywords.
        Note:
            If you are using stopwords for the first time, you need to download them using nltk.download('stopwords').
        Args:
            keywords (list): A list of keywords.
        Returns:
            list: A list of keywords with the stopwords removed.
        """

        try:
            from nltk.corpus import stopwords
            
            stopwords_list = stopwords.words('english')
        except LookupError as e:
            import nltk
            
            nltk.download('stopwords')
            stopwords_list = nltk.corpus.stopwords.words('english')
        
        return [keyword for keyword in keywords if keyword in stopwords_list]
    

    @staticmethod
    def cos_sim(embedding1, embedding2):
        """
        Computes the cosine similarity between two embeddings.
        """
        import sentence_transformers

        return sentence_transformers.util.cos_sim(embedding1, embedding2)


class TextControlFilter:
    """
    A class that provides methods for filtering control items based on keywords.
    """

    @staticmethod
    def control_filter(control_items, keywords):
        """
        Filters control items based on keywords.
        Args:
            control_items (list): A list of control items to be filtered.
            keywords (list): A list of keywords to filter the control items.
        """
        return [control_item for control_item in control_items if any(keyword in control_item['control_text'].lower() or \
                                control_item['control_text'].lower() in keyword for keyword in keywords)]
    

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

    def control_filter(self, control_items, keywords, top_k):
        """
        Filters control items based on their similarity to a set of keywords.
        Args:
            control_items (list): A list of control items to be filtered.
            keywords (list): A list of keywords.
            top_k (int): The number of top control items to be selected.
        """
        scores = []
        keywords_without_stopwords = self.remove_stopwords(keywords)
        for control_item in control_items:
            control_text = control_item['control_text'].lower()
            score = self.control_filter_score(control_text, keywords_without_stopwords)
            scores.append(score)
        topk_scores_items = heapq.nlargest(top_k, enumerate(scores), key=lambda x: x[1])
        topk_indices = [score_item[0] for score_item in topk_scores_items]

        return [control_items[i] for i in topk_indices]

class IconControlFilter(ControlFilterModel):
    """
    Represents a model for filtering control icons based on keywords.
    Attributes:
        Inherits attributes from ControlFilterModel.
    Methods:
        control_filter_score(control_icon, keywords): Calculates the score of a control icon based on its similarity to the given keywords.
        control_filter(filtered_control_info, control_items, cropped_icons_dict, keywords, top_k): Filters control items based on their scores and returns the top-k items.
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

    def control_filter(self, control_items, cropped_icons_dict, keywords, top_k):
        """
        Filters control items based on their scores and returns the top-k items.
        Args:
            control_items: The list of all control items.
            cropped_icons: The dictionary of the cropped icons.
            keywords: The keywords to compare the control icons against.
            top_k: The number of top items to return.
        Returns:
            The list of top-k control items based on their scores.
        """
        scores_items = []
        keywords_without_stopwords = self.remove_stopwords(keywords)
        for label, cropped_icon in cropped_icons_dict.items():
            score = self.control_filter_score(cropped_icon, keywords_without_stopwords)
            scores_items.append((score, label))
        topk_scores_items = heapq.nlargest(top_k, scores_items, key=lambda x: x[0])
        topk_labels = [scores_items[1] for scores_items in topk_scores_items]

        return [control_item for control_item in control_items if control_item['label'] in topk_labels ]