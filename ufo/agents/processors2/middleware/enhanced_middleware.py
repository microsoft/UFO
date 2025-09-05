"""
Middleware implementations with enhanced error handling capabilities.
"""

import asyncio
import logging
import time
import traceback
from typing import Dict, Any, Optional

from flask import json
from ufo.agents.processors2.core.processor_framework import (
    ProcessorMiddleware,
    ProcessorTemplate,
    ProcessingResult,
    ProcessingContext,
    ProcessingException,
)
from ufo.module.context import ContextNames


class EnhancedLoggingMiddleware(ProcessorMiddleware):
    """
    Enhanced logging middleware that handles different types of errors appropriately.
    """

    def __init__(self, log_level: int = logging.INFO, name: Optional[str] = None):
        super().__init__(name)
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{self.name}")
        self.log_level = log_level

    async def before_process(
        self, processor: ProcessorTemplate, context: ProcessingContext
    ) -> None:
        """Log processing start with context information."""
        round_num = context.get("round_num", 0)
        round_step = context.get("round_step", 0)

        self.logger.log(
            self.log_level,
            f"Starting processing: Round {round_num + 1}, Step {round_step + 1}, "
            f"Processor: {processor.__class__.__name__}",
        )

    async def after_process(
        self, processor: ProcessorTemplate, result: ProcessingResult
    ) -> None:
        """Log processing completion with result summary."""
        if result.success:
            self.logger.log(
                self.log_level,
                f"Processing completed successfully in {result.execution_time:.2f}s",
            )

            # Log phase execution times if available
            data_keys = list(result.data.keys())
            if data_keys:
                self.logger.debug(f"Result data keys: {data_keys}")
        else:
            self.logger.warning(f"Processing completed with failure: {result.error}")

        local_logger: logging.Logger = processor.processing_context.global_context.get(
            ContextNames.LOGGER
        )
        local_context = processor.processing_context.local_context

        local_context.total_time = result.execution_time

        phrase_time_cost = {}
        for phrase, phrase_result in processor.processing_context.phase_results.items():
            phrase_time_cost[phrase.name] = phrase_result.execution_time

        local_context.execution_times = phrase_time_cost

        local_context_string = json.dumps(
            local_context.to_dict(selective=True), ensure_ascii=False
        )

        local_logger.info(local_context_string)

        self.logger.info("Log saved successfully.")

    async def on_error(self, processor: ProcessorTemplate, error: Exception) -> None:
        """Enhanced error logging with context information."""
        if isinstance(error, ProcessingException):
            # 详细记录ProcessingException的上下文信息
            self.logger.error(
                f"ProcessingException in {processor.__class__.__name__}:\n"
                f"  Phase: {error.phase}\n"
                f"  Message: {str(error)}\n"
                f"  Context: {error.context_data}\n"
                f"  Original Exception: {error.original_exception}"
            )

            if error.original_exception:
                self.logger.info(f"Original traceback:\n{traceback.format_exc()}")
        else:
            # 记录其他类型的异常
            self.logger.error(
                f"Unexpected error in {processor.__class__.__name__}: {str(error)}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
