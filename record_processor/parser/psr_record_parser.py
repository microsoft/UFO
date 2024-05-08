# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import re
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from .demonstration_record import DemonstrationRecord, DemonstrationStep


class PSRRecordParser:
    """
    Class for parsing the steps recorder .mht file content to user demonstration record.
    """

    def __init__(self, content: str):
        """
        Constructor for the RecordParser class.
        """
        self.content = content
        self.parts_dict = {}
        self.applications = []
        self.comments = []
        self.steps = []

    def parse_to_record(self) -> DemonstrationRecord:
        """
        Parse the steps recorder .mht file content to record in following steps:
        1. Find the boundary in the .mht file.
        2. Split the file by the boundary into parts.
        3. Get the comments for each step.
        4. Get the steps from the content.
        5. Construct the record object and return it.
        return: A record object.
        """
        boundary = self.__find_boundary()
        self.parts_dict = self.__split_file_by_boundary(boundary)
        self.comments = self.__get_comments(self.parts_dict["main.htm"]["Content"])
        self.steps = self.__get_steps(self.parts_dict["main.htm"]["Content"])
        record = DemonstrationRecord(
            list(set(self.applications)), len(self.steps), **self.steps
        )

        return record

    def __find_boundary(self) -> str:
        """
        Find the boundary in the .mht file.
        """

        boundary_start = self.content.find("boundary=")

        if boundary_start != -1:
            boundary_start += len("boundary=")
            boundary_end = self.content.find("\n", boundary_start)
            boundary = self.content[boundary_start:boundary_end].strip('"')
            return boundary
        else:
            raise ValueError("Boundary not found in the .mht file.")

    def __split_file_by_boundary(self, boundary: str) -> dict:
        """
        Split the file by the boundary into parts,
        Store the parts in a dictionary, including the content type,
        content location and content transfer encoding.
        boundary: The boundary of the file.
        return: A dictionary of parts in the file.
        """
        parts = self.content.split("--" + boundary)
        part_dict = {}
        for part in parts:
            content_type_start = part.find("Content-Type:")
            content_location_start = part.find("Content-Location:")
            content_transfer_encoding_start = part.find("Content-Transfer-Encoding:")
            part_info = {}
            if content_location_start != -1:
                content_location_end = part.find("\n", content_location_start)
                content_location = (
                    part[content_location_start:content_location_end]
                    .split(":")[1]
                    .strip()
                )

                # add the content location
                if content_type_start != -1:
                    content_type_end = part.find("\n", content_type_start)
                    content_type = (
                        part[content_type_start:content_type_end].split(":")[1].strip()
                    )
                    part_info["Content-Type"] = content_type

                # add the content transfer encoding
                if content_transfer_encoding_start != -1:
                    content_transfer_encoding_end = part.find(
                        "\n", content_transfer_encoding_start
                    )
                    content_transfer_encoding = (
                        part[
                            content_transfer_encoding_start:content_transfer_encoding_end
                        ]
                        .split(":")[1]
                        .strip()
                    )
                    part_info["Content-Transfer-Encoding"] = content_transfer_encoding

                content = part[content_location_end:].strip()
                part_info["Content"] = content
                part_dict[content_location] = part_info
        return part_dict

    def __get_steps(self, content: str) -> dict:
        """
        Get the steps from the content in fllowing steps:
        1. Find the UserActionData tag in the content.
        2. Parse the UserActionData tag to get the steps.
        3. Get the screenshot for each step.
        4. Get the comments for each step.
        content: The content of the main.htm file.
        return: A dictionary of steps.
        """

        user_action_data = re.search(
            r"<UserActionData>(.*?)</UserActionData>", content, re.DOTALL
        )
        if user_action_data:

            root = ET.fromstring(user_action_data.group(1))
            steps = {}

            for each_action in root.findall("EachAction"):

                action_number = each_action.get("ActionNumber")
                application = each_action.get("FileName")
                description = each_action.find("Description").text
                action = each_action.find("Action").text
                screenshot_file_name = each_action.find("ScreenshotFileName").text
                screenshot = self.__get_screenshot(screenshot_file_name)
                step_key = f"step_{int(action_number) - 1}"

                step = DemonstrationStep(
                    application,
                    description,
                    action,
                    screenshot,
                    self.comments.get(step_key),
                )
                steps[step_key] = step
                self.applications.append(application)
            return steps
        else:
            raise ValueError("UserActionData not found in the file.")

    def __get_comments(self, content: str) -> dict:
        """
        Get the user input comments for each step
        content: The content of the main.htm file.
        return: A dictionary of comments for each step.
        """
        soup = BeautifulSoup(content, "html.parser")
        body = soup.body
        steps_html = body.find("div", id="Steps")
        steps = steps_html.find_all(
            lambda tag: tag.name == "div"
            and tag.has_attr("id")
            and re.match(r"^Step\d+$", tag["id"])
        )

        comments = {}
        for index, step in enumerate(steps):
            comment_tag = step.find("b", text="Comment: ")
            comments[f"step_{index}"] = (
                comment_tag.next_sibling if comment_tag else None
            )
        return comments

    def __get_screenshot(self, screenshot_file_name: str) -> str:
        """
        Get the screenshot by screenshot file name.
        The screenshot related information is stored in the parts_dict.
        screenshot_file_name: The file name of the screenshot.
        return: The screenshot in base64 string.
        """
        screenshot_part = self.parts_dict[screenshot_file_name]
        content = screenshot_part["Content"]
        content_type = screenshot_part["Content-Type"]
        content_transfer_encoding = screenshot_part["Content-Transfer-Encoding"]

        screenshot = "data:{type};{encoding}, {content}".format(
            type=content_type, encoding=content_transfer_encoding, content=content
        )

        return screenshot
