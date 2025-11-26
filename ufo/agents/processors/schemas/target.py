import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class TargetKind(str, Enum):
    """
    Enumeration for different types of targets.
    """

    WINDOW = "window"
    CONTROL = "control"
    THIRD_PARTY_AGENT = "third_party_agent"


class TargetInfo(BaseModel):
    """
    The class for the target information.
    """

    kind: TargetKind  # The kind of the target (window, control, or third-party agent)
    name: str  # The name of the target
    id: Optional[str] = None  # The ID of the target (only valid at current step)
    type: Optional[str] = None  # The type of the target (e.g., process, app, etc.)
    rect: Optional[List[int]] = (
        None  # The rectangle of the target [left, top, right, bottom]
    )


class TargetRegistry:
    """
    Registry for managing target information for HostAgent
    """

    def __init__(self) -> None:
        """
        Initialize the target registry.
        """
        self._targets: Dict[str, TargetInfo] = {}
        self._counter = 0
        self.logger = logging.getLogger(self.__class__.__name__)

    def register(self, target: Union[TargetInfo, List[TargetInfo]]) -> List[TargetInfo]:
        """
        Register a target or a list of targets.
        :param target: The target or list of targets to register.
        :return: A list of registered targets.
        """
        if not isinstance(target, list):
            target = [target]

        registered = []
        for t in target:
            if not t.id:  # If no ID is present, generate one
                self._counter += 1
                t.id = str(self._counter)

            if t.id in self._targets:
                self.logger.warning(
                    f"Target with ID {t.id} is already registered, ignoring.",
                )
            else:
                self._targets[t.id] = t
                registered.append(t)

        return registered

    def register_from_dict(self, target_dict: Dict[str, Any]) -> TargetInfo:
        """
        Register a target from a dictionary.
        :param target_dict: The dictionary containing target information.
        :return: The registered target.
        """
        target = TargetInfo(
            kind=TargetKind(target_dict["kind"]),
            name=target_dict["name"],
            id=target_dict.get("id"),
            type=target_dict.get("type"),
            rect=target_dict.get("rect"),
        )
        return self.register(target)

    def register_from_dicts(
        self, target_dicts: List[Dict[str, Any]]
    ) -> List[TargetInfo]:
        """
        Register targets from a list of dictionaries.
        :param target_dicts: The list of dictionaries containing target information.
        :return: A list of registered targets.
        """
        return [self.register_from_dict(d) for d in target_dicts]

    def get(self, target_id: str) -> Optional[TargetInfo]:
        """
        Get a target by its ID.
        :param target_id: The ID of the target to retrieve.
        :return: The target information, or None if not found.
        """
        return self._targets.get(target_id)

    def find_by_name(self, name: str) -> List[TargetInfo]:
        """
        Find targets by their name.
        :param name: The name of the targets to find.
        :return: A list of targets with the given name.
        """
        return [t for t in self._targets.values() if t.name == name]

    def find_by_id(self, target_id: str) -> Optional[TargetInfo]:
        """
        Find a target by its ID.
        :param target_id: The ID of the target to find.
        :return: The target information, or None if not found.
        """
        return self._targets.get(target_id)

    def find_by_kind(self, kind: TargetKind) -> List[TargetInfo]:
        """
        Find targets by their kind.
        :param kind: The kind of the targets to find.
        :return: A list of targets with the given kind.
        """
        return [t for t in self._targets.values() if t.kind == kind]

    def all_targets(self) -> List[TargetInfo]:
        """
        Get all registered targets.
        :return: A list of all registered targets.
        """
        return list(self._targets.values())

    def unregister(self, target_id: str) -> bool:
        """
        Unregister a target by its ID.
        :param target_id: The ID of the target to unregister.
        :return: True if the target was unregistered, False if not found.
        """
        if target_id in self._targets:
            del self._targets[target_id]
            return True
        return False

    def to_list(self, keep_keys: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Convert the registered targets to a list of dictionaries.
        :param keep_keys: Optional list of keys to keep in the output dictionaries.
        :return: A list of dictionaries representing the registered targets.
        """
        if keep_keys:
            return [
                {k: v for k, v in t.model_dump().items() if k in keep_keys}
                for t in self._targets.values()
            ]
        else:
            return [t.model_dump() for t in self._targets.values()]

    def clear(self) -> None:
        """
        Clear all registered targets.
        """
        self._targets.clear()
        self._counter = 0
