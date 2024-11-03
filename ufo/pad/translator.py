# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod


from ufo.pad.robin_script_translator import *


class Action2Pad(ABC):

    def __init__(self, parameters: Dict[str, Any] = {}, control_info: str = ""):
        """
        Initialize the action.
        :param parameters: The parameters of the action.
        :param control_info: The control information of the action.
        """
        self.parameters = parameters
        self.control_info = control_info

    @abstractmethod
    def to_pad(self) -> RobinAction:
        """
        Convert the action to a Robin action.
        :return: The Robin action.
        """
        pass


class ClickInput2Pad(Action2Pad):

    def to_pad(self) -> RobinAction:
        """
        Convert the action to a Robin action.
        :return: The Robin action.
        """
        control_name = self.control_info
        if (
            "power bi" in control_name.lower()
            or "team chat" in control_name.lower()
            or "new tab" in control_name.lower()
        ):
            return UIAutomationPressButton(
                parameters={"Button": f"appmask['{control_name}']"}
            )
        else:
            return WebAutomationClickAction(
                parameters={"Control": f"appmask['{control_name}']"}
            )


class SetEditText2Pad(Action2Pad):

    def to_pad(self) -> RobinAction:
        """
        Convert the action to a Robin action.
        :return: The Robin action.
        """

        text = self.parameters.get("text")
        return MouseAndKeyboardSendKeys(parameters={"TextToSend": f"'{text}'"})


class NoneAction(Action2Pad):

    def to_pad(self) -> RobinAction:
        """
        Convert the action to a Robin action.
        :return: The Robin action.
        """
        return WaitAction()


class ActionMapping:
    """
    Mapping from action names in UFO to action classes.
    """

    _mapping = {
        "click_input": ClickInput2Pad,
        "set_edit_text": SetEditText2Pad,
        "": NoneAction,
    }

    @staticmethod
    def get_action(action: str) -> Action2Pad:
        """
        Get the Robin action class from the UFO action.
        :param action: The UFO action.
        :return: The Robin action class.
        """
        return ActionMapping._mapping.get(action, NoneAction)

    def mapper(self, action: Dict[str, Any]) -> Action2Pad:
        """
        Get the Robin action class from the UFO action.
        :param action: The UFO action.
        :return: The Robin action class.
        """

        robin_action_class = ActionMapping.get_action(action.get("Function", ""))

        return robin_action_class(
            parameters=action.get("Args", ""),
            control_info=action.get("ControlText", ""),
        )

    def robin_action_mapper(self, action: Dict[str, Any]) -> RobinAction:
        """
        Get the Robin action class from the UFO action.
        :param action: The UFO action.
        :return: The Robin action class.
        """
        return self.mapper(action).to_pad()

    def batch_robin_action_mapper(
        self, actions: List[Dict[str, Any]]
    ) -> List[RobinAction]:
        """
        Get the Robin action class from the UFO action.
        :param action: The UFO action.
        :return: The Robin action class.
        """
        return [self.mapper(action).to_pad() for action in actions]


if __name__ == "__main__":

    import json

    action_path = "logs/rpa_new1/response.log"

    action_list = []
    with open(action_path, "r") as file:
        for line in file:
            action_dict = json.loads(line)
            if action_dict.get("Agent") == "AppAgent":
                action_list.append(action_dict)

    mapper = ActionMapping()
    robin_actions = mapper.batch_robin_action_mapper(action_list)
    print(RobinActionSequenceGenerator().generate(robin_actions))
