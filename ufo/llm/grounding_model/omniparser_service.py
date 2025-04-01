# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from ufo.llm.base import BaseService
from gradio_client import Client, handle_file


class OmniParser(BaseService):
    """
    The parser for the OmniParser.
    """

    def __init__(self, endpoint: str):
        """
        Initialize the OmniParser service.
        :param endpoint: The endpoint address of the OmniParser service.
        """
        self.client = Client(endpoint)

    def chat_completion(
        self,
        image_path: str,
        box_threshold: float = 0.05,
        iou_threshold: float = 0.1,
        use_paddleocr: bool = True,
        imgsz: int = 640,
        api_name: str = "/process",
    ):
        """
        Get the chat completion from the OmniParser service.
        :param text: The input text.
        :return: The chat completion.
        """
        results = self.client.predict(
            image_input=handle_file(filepath_or_url=image_path),
            box_threshold=box_threshold,
            iou_threshold=iou_threshold,
            use_paddleocr=use_paddleocr,
            imgsz=imgsz,
            api_name=api_name,
        )
        return results
