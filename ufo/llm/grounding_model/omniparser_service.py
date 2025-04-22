# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from ufo.llm.base import BaseService
import requests
import base64

class OmniParser(BaseService):
    """
    The parser for the OmniParser.
    """

    def __init__(self, endpoint: str):
        """
        Initialize the OmniParser service.
        :param endpoint: The endpoint address of the OmniParser service.
        """
        try:
            probe_response = requests.get(f"{endpoint}/probe/")
            probe_response.raise_for_status()
            print("Connected to Omniparser server successfully.")
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to server: {e}")
            return 1
        self.endpoint = endpoint

    def chat_completion(
        self,
        image_path: str,
    ):
        """
        Get the chat completion from the OmniParser service.
        :param text: The input text.
        :return: The chat completion.
        """
        try:
            base64_image = self.encode_image_to_base64(image_path)
        except Exception as e:
            print(f"Error reading image file: {e}")
            return 1
        
        # Prepare request payload
        payload = {
            "base64_image": base64_image
        }

        parse_endpoint = f"{self.endpoint}/parse/"

        try:
            response = requests.post(parse_endpoint, json=payload)
            response.raise_for_status()
            
            # Process response
            result = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to server: {e}")
            return None

        return result
    
    def encode_image_to_base64(self, image_path):
        with open(image_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string
