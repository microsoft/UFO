# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

class Record:
    """
    Class for the user behavior record.
    """

    def __init__(self, applications, step_num, **steps):
        """
        Create a new Record.
        """
        self.request = ""
        self.round = 0
        self.applications = applications
        self.step_num = step_num
        for index, step  in steps.items():
            setattr(self, index, step.__dict__)

    def set_request(self, request):
        """
        Set the request.
        """
        self.request = request
        
    

class Step:
    """
    Class for the single step information in the user behavior record.
    """

    def __init__(self, application, description, action, screenshot, comment):
        """
        Create a new step.
        """
        self.application = application
        self.description = description
        self.action = action
        self.comment = comment
        self.screenshot = screenshot
