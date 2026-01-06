# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Base Presenter Interface

This module defines the abstract base class for all presenters,
ensuring a consistent interface for displaying agent responses.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BasePresenter(ABC):
    """
    Abstract base class for all presenters.
    
    Presenters are responsible for formatting and displaying agent responses,
    separating presentation logic from business logic. This allows for:
    - Easy switching between different output formats (console, JSON, etc.)
    - Consistent display across different agent types
    - Better testability and maintainability
    """

    @abstractmethod
    def present_response(self, response: Any, **kwargs) -> None:
        """
        Present the complete agent response.
        
        :param response: The response object to present (type varies by agent)
        :param kwargs: Additional presentation options
        """
        pass

    @abstractmethod
    def present_thought(self, thought: str) -> None:
        """
        Present agent's thought/reasoning.
        
        :param thought: The thought text to display
        """
        pass

    @abstractmethod
    def present_observation(self, observation: str) -> None:
        """
        Present agent's observation.
        
        :param observation: The observation text to display
        """
        pass

    @abstractmethod
    def present_status(self, status: str, **kwargs) -> None:
        """
        Present agent's status.
        
        :param status: The status string (e.g., "FINISH", "FAIL", "CONTINUE")
        :param kwargs: Additional status display options
        """
        pass

    @abstractmethod
    def present_actions(self, actions: Any, **kwargs) -> None:
        """
        Present agent's planned actions.
        
        :param actions: The actions to display (format varies by agent)
        :param kwargs: Additional action display options
        """
        pass

    @abstractmethod
    def present_plan(self, plan: List[str]) -> None:
        """
        Present agent's plan.
        
        :param plan: List of plan items
        """
        pass

    @abstractmethod
    def present_comment(self, comment: Optional[str]) -> None:
        """
        Present agent's comment/message.
        
        :param comment: The comment text to display
        """
        pass

    @abstractmethod
    def present_results(self, results: Any) -> None:
        """
        Present execution results.
        
        :param results: The results to display
        """
        pass
