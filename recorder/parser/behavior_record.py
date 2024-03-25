# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

class BehaviorStep:
    """
    Class for the single step information in the user behavior record.
    Multiple steps will be recorded to achieve a specific request.
    """

    def __init__(self, application: str, description: str, action: str, screenshot: str, comment: str):
        """
        Create a new step.
        """
        self.application = application
        self.description = description
        self.action = action
        self.comment = comment
        self.screenshot = screenshot


class BehaviorRecord:
    """
    Class for the user behavior record.
    A serise of steps user performed to achieve a specific request will be recorded in this class.
    """

    def __init__(self, applications: list, step_num: int, **steps: BehaviorStep):
        """
        Create a new Record.
        """
        self.request = ""
        self.round = 0
        self.applications = applications
        self.step_num = step_num
        for index, step in steps.items():
            setattr(self, index, step.__dict__)

    def set_request(self, request):
        """
        Set the request.
        """
        self.request = request
