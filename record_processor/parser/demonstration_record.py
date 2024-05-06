# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


class DemonstrationStep:
    """
    Class for the single step information in the user demonstration record.
    Multiple steps will be recorded to achieve a specific request.
    """

    def __init__(
        self,
        application: str,
        description: str,
        action: str,
        screenshot: str,
        comment: str,
    ):
        """
        Create a new step.
        """
        self.application = application
        self.description = description
        self.action = action
        self.comment = comment
        self.screenshot = screenshot


class DemonstrationRecord:
    """
    Class for the user demonstration record.
    A serise of steps user performed to achieve a specific request will be recorded in this class.
    """

    def __init__(self, applications: list, step_num: int, **steps: DemonstrationStep):
        """
        Create a new Record.
        """
        self.__request = ""
        self.__round = 0
        self.__applications = applications
        self.__step_num = step_num
        # adding each key-value pair in steps to the record
        for index, step in steps.items():
            setattr(self, index, step.__dict__)

    def set_request(self, request: str):
        """
        Set the request.
        """
        self.__request = request

    def get_request(self) -> str:
        """
        Get the request.
        """
        return self.__request

    def get_applications(self) -> list:
        """
        Get the application.
        """
        return self.__applications

    def get_step_num(self) -> int:
        """
        Get the step number.
        """
        return self.__step_num
