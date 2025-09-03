from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

from ufo.agents.processors2.core.processing_context import (
    ProcessingContext,
    ProcessingResult,
)

if TYPE_CHECKING:
    from ufo.agents.processors2.core.processor_framework import ProcessorTemplate


class ProcessorMiddleware(ABC):
    """
    Processor middleware base class.
    """

    def __init__(self, name: Optional[str] = None):
        """
        Initialize the middleware.
        :param name: Optional custom name for the middleware. If not provided, uses class name.
        """
        self.name = name or self.__class__.__name__

    @abstractmethod
    async def before_process(
        self, processor: "ProcessorTemplate", context: ProcessingContext
    ) -> None:
        """
        Before processing hook.
        :param processor: The processor instance.
        :param context: The processing context.
        """
        pass

    @abstractmethod
    async def after_process(
        self, processor: "ProcessorTemplate", result: ProcessingResult
    ) -> None:
        """
        After processing hook.
        :param processor: The processor instance.
        :param result: The processing result.
        """
        pass

    @abstractmethod
    async def on_error(self, processor: "ProcessorTemplate", error: Exception) -> None:
        """
        Error handling hook.
        :param processor: The processor instance.
        :param error: The error that occurred.
        """
        pass
