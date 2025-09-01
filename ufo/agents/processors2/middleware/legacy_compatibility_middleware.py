"""
Legacy compatibility middleware that provides functionality equivalent to BaseProcessor decorators.

This middleware implements the @method_timer and @exception_capture decorator functionality
from the original BaseProcessor in the new middleware-based architecture.
"""

import logging
import time
import traceback
from typing import Dict, Any, Optional

from ufo import utils
from ufo.agents.processors2.core.processor_framework import (
    ProcessorMiddleware,
    ProcessorTemplate,
    ProcessingContext,
    ProcessingResult,
    ProcessingException,
)


class LegacyCompatibilityMiddleware(ProcessorMiddleware):
    """
    Middleware that provides compatibility with BaseProcessor decorator functionality.
    
    This middleware implements:
    - Method timing equivalent to @method_timer decorator
    - Exception capture equivalent to @exception_capture decorator
    - Error logging and state management from original BaseProcessor
    """

    def __init__(self) -> None:
        """Initialize legacy compatibility middleware."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._start_time: Optional[float] = None
        self._phase_times: Dict[str, float] = {}
        self._exception_traceback: Dict[str, Dict[str, Any]] = {}

    async def before_process(
        self, processor: ProcessorTemplate, context: ProcessingContext
    ) -> None:
        """
        Initialize timing and error tracking before processing.
        
        Args:
            processor: Processor instance
            context: Processing context
        """
        self._start_time = time.time()
        self._phase_times = {}
        self._exception_traceback = {}
        
        # Initialize processor attributes for compatibility
        if not hasattr(processor, '_time_cost'):
            processor._time_cost = {}
        if not hasattr(processor, '_exeception_traceback'):
            processor._exeception_traceback = {}
        if not hasattr(processor, '_total_time_cost'):
            processor._total_time_cost = 0

        self.logger.debug("Legacy compatibility middleware initialized")

    async def after_process(
        self, processor: ProcessorTemplate, result: ProcessingResult
    ) -> None:
        """
        Finalize timing and update processor state after successful processing.
        
        Args:
            processor: Processor instance
            result: Processing result
        """
        if self._start_time:
            total_time = time.time() - self._start_time
            processor._total_time_cost = total_time
            
            # Update context with timing information
            result.execution_time = total_time
            
        # Update processor timing information
        processor._time_cost.update(self._phase_times)
        
        self.logger.debug(
            f"Processing completed - Total time: {processor._total_time_cost:.3f}s, "
            f"Phase times: {self._phase_times}"
        )

    async def on_error(self, processor: ProcessorTemplate, error: Exception) -> None:
        """
        Handle errors with legacy BaseProcessor compatibility.
        
        Args:
            processor: Processor instance 
            error: Exception that occurred
        """
        # Calculate timing even on error
        if self._start_time:
            total_time = time.time() - self._start_time
            processor._total_time_cost = total_time

        # Handle ProcessingException with enhanced context
        if isinstance(error, ProcessingException):
            error_info = self._create_error_info("ProcessingException", error)
            phase_name = error.phase.value if error.phase else "unknown"
        else:
            error_info = self._create_error_info("Exception", error)
            phase_name = "unknown"

        # Store exception information in processor (legacy compatibility)
        processor._exeception_traceback[phase_name] = error_info
        self._exception_traceback[phase_name] = error_info

        # Log error with color (maintaining original BaseProcessor behavior)
        utils.print_with_color(f"Error Occurs at {phase_name}", "red")
        utils.print_with_color(error_info["traceback"], "red")

        # Log response if available (legacy compatibility)
        if hasattr(processor, '_response') and processor._response:
            utils.print_with_color("Response: ", "red")
            utils.print_with_color(str(processor._response), "red")

        # Update agent status if available (legacy compatibility) 
        if hasattr(processor, 'agent') and hasattr(processor.agent, 'status_manager'):
            processor._status = processor.agent.status_manager.ERROR.value

        # Sync memory and add error information (legacy compatibility)
        try:
            await self._sync_memory_compatibility(processor)
            await self._add_error_to_memory(processor, error_info)
        except Exception as memory_error:
            self.logger.error(f"Failed to sync memory on error: {memory_error}")

        self.logger.error(f"Legacy compatibility error handling completed for: {error}")

    def record_phase_timing(self, phase_name: str, duration: float) -> None:
        """
        Record timing for a specific phase (used by strategies).
        
        Args:
            phase_name: Name of the processing phase
            duration: Duration in seconds
        """
        self._phase_times[phase_name] = duration
        self.logger.debug(f"Phase {phase_name} completed in {duration:.3f}s")

    def _create_error_info(self, error_type: str, error: Exception) -> Dict[str, Any]:
        """
        Create error information dictionary compatible with legacy format.
        
        Args:
            error_type: Type of error
            error: Exception instance
            
        Returns:
            Dictionary with error information in legacy format
        """
        return {
            "type": error_type,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }

    async def _sync_memory_compatibility(self, processor: ProcessorTemplate) -> None:
        """
        Sync memory for legacy compatibility.
        
        Args:
            processor: Processor instance
        """
        try:
            # Call sync_memory if it exists (legacy compatibility)
            if hasattr(processor, 'sync_memory'):
                if callable(processor.sync_memory):
                    processor.sync_memory()
            else:
                self.logger.debug("No sync_memory method found on processor")
        except Exception as e:
            self.logger.error(f"Error syncing memory: {e}")

    async def _add_error_to_memory(
        self, processor: ProcessorTemplate, error_info: Dict[str, Any]
    ) -> None:
        """
        Add error information to memory for legacy compatibility.
        
        Args:
            processor: Processor instance
            error_info: Error information dictionary
        """
        try:
            # Add error to memory if method exists (legacy compatibility)
            if hasattr(processor, 'add_to_memory'):
                if callable(processor.add_to_memory):
                    processor.add_to_memory({"error": self._exception_traceback})
                    processor.add_to_memory({"status": getattr(processor, '_status', 'ERROR')})

            # Save logs if method exists (legacy compatibility)
            if hasattr(processor, 'log_save'):
                if callable(processor.log_save):
                    processor.log_save()
                    
        except Exception as e:
            self.logger.error(f"Error adding error to memory: {e}")

    def get_timing_summary(self) -> Dict[str, Any]:
        """
        Get timing summary for all phases.
        
        Returns:
            Dictionary with timing information
        """
        return {
            "phase_times": self._phase_times.copy(),
            "total_time": sum(self._phase_times.values()),
        }

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get error summary for debugging.
        
        Returns:
            Dictionary with error information
        """
        return {
            "exception_traceback": self._exception_traceback.copy(),
            "error_count": len(self._exception_traceback),
        }


class StrategyTimingWrapper:
    """
    Wrapper class that provides method timing functionality equivalent to @method_timer decorator.
    
    This can be used by strategies to measure execution time of specific operations.
    """

    def __init__(self, middleware: LegacyCompatibilityMiddleware):
        """
        Initialize timing wrapper.
        
        Args:
            middleware: Legacy compatibility middleware instance
        """
        self.middleware = middleware
        self.logger = logging.getLogger(self.__class__.__name__)

    async def time_async_operation(self, operation_name: str, operation_func):
        """
        Time an async operation and record the duration.
        
        Args:
            operation_name: Name of the operation
            operation_func: Async function to time
            
        Returns:
            Result of the operation function
        """
        start_time = time.time()
        try:
            result = await operation_func()
            return result
        finally:
            duration = time.time() - start_time
            self.middleware.record_phase_timing(operation_name, duration)

    def time_sync_operation(self, operation_name: str, operation_func):
        """
        Time a synchronous operation and record the duration.
        
        Args:
            operation_name: Name of the operation
            operation_func: Sync function to time
            
        Returns:
            Result of the operation function
        """
        start_time = time.time()
        try:
            result = operation_func()
            return result
        finally:
            duration = time.time() - start_time
            self.middleware.record_phase_timing(operation_name, duration)
