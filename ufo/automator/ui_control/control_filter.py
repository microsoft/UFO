# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from .base import ControlFilterModel
import heapq


class TextModel:
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

        Returns:
            None
        """
        for control_item in control_items:
            if control_item not in filtered_control_info:
                control_text = control_item['control_text'].lower()
                if any(keyword in control_text or control_text in keyword for keyword in keywords):
                    filtered_control_info.append(control_item)

class SemanticModel(ControlFilterModel):
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

        Returns:
            None
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
    
class IconModel(ControlFilterModel):
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
            