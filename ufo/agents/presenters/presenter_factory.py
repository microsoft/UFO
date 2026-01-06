# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Presenter Factory

This module provides a factory for creating presenter instances,
allowing easy extension and configuration of different output formats.
"""

from typing import Optional

from rich.console import Console

from .base_presenter import BasePresenter
from .rich_presenter import RichPresenter


class PresenterFactory:
    """
    Factory class for creating presenters.
    
    This factory allows for:
    - Easy creation of presenter instances
    - Future extension to support multiple presenter types (JSON, Markdown, etc.)
    - Centralized presenter configuration
    """

    _presenters = {
        "rich": RichPresenter,
        # Future extensions:
        # "json": JsonPresenter,
        # "markdown": MarkdownPresenter,
        # "html": HtmlPresenter,
    }

    @classmethod
    def create_presenter(
        cls,
        presenter_type: str = "rich",
        console: Optional[Console] = None,
    ) -> BasePresenter:
        """
        Create a presenter instance.
        
        :param presenter_type: Type of presenter to create (default: "rich")
        :param console: Optional Rich Console instance for RichPresenter
        :return: Presenter instance
        :raises ValueError: If presenter_type is not recognized
        """
        presenter_cls = cls._presenters.get(presenter_type)
        if not presenter_cls:
            raise ValueError(
                f"Unknown presenter type: {presenter_type}. "
                f"Available types: {list(cls._presenters.keys())}"
            )

        # Create presenter based on type
        if presenter_type == "rich":
            return presenter_cls(console=console)
        else:
            return presenter_cls()

    @classmethod
    def register_presenter(cls, presenter_type: str, presenter_class: type) -> None:
        """
        Register a new presenter type.
        
        This allows for custom presenter implementations to be registered
        and used by the factory.
        
        :param presenter_type: Name/identifier for the presenter type
        :param presenter_class: The presenter class to register
        :raises TypeError: If presenter_class doesn't inherit from BasePresenter
        """
        if not issubclass(presenter_class, BasePresenter):
            raise TypeError(
                f"Presenter class must inherit from BasePresenter, "
                f"got {presenter_class.__name__}"
            )

        cls._presenters[presenter_type] = presenter_class

    @classmethod
    def get_available_presenters(cls) -> list:
        """
        Get list of available presenter types.
        
        :return: List of available presenter type names
        """
        return list(cls._presenters.keys())
