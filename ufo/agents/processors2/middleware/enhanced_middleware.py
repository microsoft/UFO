"""
Middleware implementations with enhanced error handling capabilities.
"""

import asyncio
import logging
import time
import traceback
from typing import Dict, Any
from ufo.agents.processors2.core.processor_framework import (
    ProcessorMiddleware,
    ProcessorTemplate,
    ProcessingResult,
    ProcessingContext,
    ProcessingException,
)


class EnhancedLoggingMiddleware(ProcessorMiddleware):
    """
    Enhanced logging middleware that handles different types of errors appropriately.
    """

    def __init__(self, log_level: int = logging.INFO):
        self.logger = logging.getLogger(self.__class__.__name__)
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
                self.logger.debug(f"Original traceback:\n{traceback.format_exc()}")
        else:
            # 记录其他类型的异常
            self.logger.error(
                f"Unexpected error in {processor.__class__.__name__}: {str(error)}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )


class ErrorRecoveryMiddleware(ProcessorMiddleware):
    """
    Error recovery middleware that attempts to recover from certain types of failures.
    """

    def __init__(self, max_retries: int = 3, recoverable_errors: list = None):
        self.max_retries = max_retries
        self.recoverable_errors = recoverable_errors or [
            "timeout",
            "network",
            "temporary",
        ]
        self.logger = logging.getLogger(self.__class__.__name__)
        self.retry_count = 0

    async def before_process(
        self, processor: ProcessorTemplate, context: ProcessingContext
    ) -> None:
        """Initialize retry state."""
        self.retry_count = 0

    async def after_process(
        self, processor: ProcessorTemplate, result: ProcessingResult
    ) -> None:
        """Reset retry state on successful completion."""
        self.retry_count = 0

    async def on_error(self, processor: ProcessorTemplate, error: Exception) -> None:
        """Attempt error recovery for recoverable errors."""
        if self._is_recoverable_error(error) and self.retry_count < self.max_retries:
            self.retry_count += 1
            self.logger.warning(
                f"Attempting recovery for error (attempt {self.retry_count}/{self.max_retries}): {str(error)}"
            )

            # 执行恢复逻辑
            await self._attempt_recovery(processor, error)
        else:
            self.logger.error(
                f"Error is not recoverable or max retries exceeded: {str(error)}"
            )

    def _is_recoverable_error(self, error: Exception) -> bool:
        """Check if the error is recoverable."""
        error_message = str(error).lower()
        return any(
            recoverable in error_message for recoverable in self.recoverable_errors
        )

    async def _attempt_recovery(
        self, processor: ProcessorTemplate, error: Exception
    ) -> None:
        """Attempt to recover from the error."""
        # 实现具体的恢复逻辑，例如：
        # - 清理临时资源
        # - 重置状态
        # - 等待一段时间后重试
        await asyncio.sleep(1)  # 简单的延迟重试
        self.logger.info("Recovery attempt completed")


class ResourceCleanupMiddleware(ProcessorMiddleware):
    """
    Resource cleanup middleware that ensures proper cleanup regardless of success or failure.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.allocated_resources = []

    async def before_process(
        self, processor: ProcessorTemplate, context: ProcessingContext
    ) -> None:
        """Initialize resource tracking."""
        self.allocated_resources = []
        self.logger.debug("Resource tracking initialized")

    async def after_process(
        self, processor: ProcessorTemplate, result: ProcessingResult
    ) -> None:
        """Clean up resources after successful processing."""
        await self._cleanup_resources("normal completion")

    async def on_error(self, processor: ProcessorTemplate, error: Exception) -> None:
        """Clean up resources after error."""
        await self._cleanup_resources(f"error: {str(error)}")

    async def _cleanup_resources(self, reason: str) -> None:
        """Perform actual resource cleanup."""
        if self.allocated_resources:
            self.logger.info(
                f"Cleaning up {len(self.allocated_resources)} resources due to: {reason}"
            )

            for resource in self.allocated_resources:
                try:
                    # 清理具体资源
                    if hasattr(resource, "close"):
                        resource.close()
                    elif hasattr(resource, "cleanup"):
                        resource.cleanup()
                except Exception as cleanup_error:
                    self.logger.warning(f"Failed to cleanup resource: {cleanup_error}")

            self.allocated_resources.clear()
        else:
            self.logger.debug(f"No resources to cleanup due to: {reason}")


class MetricsCollectionMiddleware(ProcessorMiddleware):
    """
    Metrics collection middleware that tracks processing performance and error rates.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.metrics = {
            "total_processes": 0,
            "successful_processes": 0,
            "failed_processes": 0,
            "processing_times": [],
            "error_types": {},
            "phase_failures": {},
        }

    async def before_process(
        self, processor: ProcessorTemplate, context: ProcessingContext
    ) -> None:
        """Start metrics collection."""
        self.metrics["total_processes"] += 1
        context.set_local("metrics_start_time", time.time())

    async def after_process(
        self, processor: ProcessorTemplate, result: ProcessingResult
    ) -> None:
        """Record completion metrics."""
        start_time = processor.processing_context.get_local(
            "metrics_start_time", time.time()
        )
        duration = time.time() - start_time

        self.metrics["processing_times"].append(duration)

        if result.success:
            self.metrics["successful_processes"] += 1
            self.logger.debug(f"Process succeeded in {duration:.2f}s")
        else:
            self.metrics["failed_processes"] += 1
            if result.phase:
                phase_name = result.phase.value
                self.metrics["phase_failures"][phase_name] = (
                    self.metrics["phase_failures"].get(phase_name, 0) + 1
                )
            self.logger.debug(
                f"Process failed in {duration:.2f}s at phase: {result.phase}"
            )

    async def on_error(self, processor: ProcessorTemplate, error: Exception) -> None:
        """Record error metrics."""
        error_type = type(error).__name__
        self.metrics["error_types"][error_type] = (
            self.metrics["error_types"].get(error_type, 0) + 1
        )

        if isinstance(error, ProcessingException) and error.phase:
            phase_name = error.phase.value
            self.metrics["phase_failures"][phase_name] = (
                self.metrics["phase_failures"].get(phase_name, 0) + 1
            )

        self.logger.debug(f"Recorded error: {error_type}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of collected metrics."""
        total_processes = self.metrics["total_processes"]
        if total_processes == 0:
            return {"message": "No processes recorded"}

        success_rate = (self.metrics["successful_processes"] / total_processes) * 100
        avg_processing_time = (
            sum(self.metrics["processing_times"])
            / len(self.metrics["processing_times"])
            if self.metrics["processing_times"]
            else 0
        )

        return {
            "total_processes": total_processes,
            "success_rate": f"{success_rate:.1f}%",
            "average_processing_time": f"{avg_processing_time:.2f}s",
            "error_types": self.metrics["error_types"],
            "phase_failures": self.metrics["phase_failures"],
        }
