from ufo.agents.processors2.core.processor_framework import (
    ProcessorMiddleware,
    ProcessingResult,
    ProcessingContext,
    ProcessorTemplate,
)
import time
import traceback


class TimingMiddleware(ProcessorMiddleware):
    """
    Timing middleware for measuring processing duration.
    """

    async def before_process(
        self, processor: ProcessorTemplate, context: ProcessingContext
    ) -> None:
        """
        Initialize timing before processing starts.
        :param processor: The processor instance.
        :param context: The processing context.
        """
        processor._start_time = time.time()
        processor.logger.info(f"Starting processing for {processor.__class__.__name__}")

    async def after_process(
        self, processor: ProcessorTemplate, result: ProcessingResult
    ) -> None:
        """
        Finalize timing after processing completes.
        :param processor: The processor instance.
        :param result: The processing result.
        """
        duration = time.time() - processor._start_time
        processor.logger.info(f"Processing completed in {duration:.2f}s")

        # Update context with time cost
        processor.processing_context.set_local("total_time_cost", duration)

    async def on_error(self, processor: ProcessorTemplate, error: Exception) -> None:
        """
        Handle errors that occur during processing.
        :param processor: The processor instance.
        :param error: The error that occurred.
        """
        duration = time.time() - getattr(processor, "_start_time", time.time())
        processor.logger.error(f"Processing failed after {duration:.2f}s: {str(error)}")


class LoggingMiddleware(ProcessorMiddleware):
    """
    Logging middleware for processing steps.
    """

    async def before_process(
        self, processor: ProcessorTemplate, context: ProcessingContext
    ) -> None:
        """
        Initialize logging before processing starts.
        :param processor: The processor instance.
        :param context: The processing context.
        """
        processor.logger.info(
            f"Processing step info: Round {context.get('round_num', 0) + 1}, "
            f"Step {context.get('round_step', 0) + 1}"
        )

    async def after_process(
        self, processor: ProcessorTemplate, result: ProcessingResult
    ) -> None:
        """
        Finalize logging after processing completes.
        :param processor: The processor instance.
        :param result: The processing result.
        """
        if result.success:
            processor.logger.info("Processing completed successfully")
        else:
            processor.logger.error(f"Processing failed: {result.error}")

    async def on_error(self, processor: ProcessorTemplate, error: Exception) -> None:
        """
        Handle errors that occur during processing.
        :param processor: The processor instance.
        :param error: The error that occurred.
        """
        processor.logger.error(
            f"Unexpected error in {processor.__class__.__name__}: {str(error)}"
        )
        processor.logger.debug(traceback.format_exc())


class MemoryMiddleware(ProcessorMiddleware):
    """
    Memory management middleware.
    """

    async def before_process(
        self, processor: ProcessorTemplate, context: ProcessingContext
    ) -> None:
        """
        Initialize memory item.
        :param processor: The processor instance.
        :param context: The processing context.
        """
        processor._memory_data = processor._create_memory_item()

    async def after_process(
        self, processor: ProcessorTemplate, result: ProcessingResult
    ) -> None:
        """
        Finalize memory after processing completes.
        :param processor: The processor instance.
        :param result: The processing result.
        """
        if result.success:
            # Sync memory
            processor._sync_memory_with_result(result)
            processor.agent.add_memory(processor._memory_data)

            # Add to structural logs
            processor.global_context.add_to_structural_logs(
                processor._memory_data.to_dict()
            )

    async def on_error(self, processor: ProcessorTemplate, error: Exception) -> None:
        """
        Handle errors that occur during processing.
        :param processor: The processor instance.
        :param error: The error that occurred.
        """
        processor.logger.error(f"Processing failed: {str(error)}")

        # Record error to memory
        if processor._memory_data:
            processor._memory_data.add_values_from_dict(
                {"error": str(error), "status": "ERROR"}
            )


class ExceptionHandlingMiddleware(ProcessorMiddleware):
    """
    Exception handling middleware.
    """

    async def before_process(
        self, processor: ProcessorTemplate, context: ProcessingContext
    ) -> None:
        """
        Initialize exception list before processing starts.
        :param processor: The processor instance.
        :param context: The processing context.
        """
        processor._exceptions = []

    async def after_process(
        self, processor: ProcessorTemplate, result: ProcessingResult
    ) -> None:
        """
        Finalize exception handling after processing completes.
        :param processor: The processor instance.
        :param result: The processing result.
        """
        if result.success:
            processor.logger.info("Processing completed successfully")
        else:
            processor.logger.error(f"Processing failed: {result.error}")

    async def on_error(self, processor: ProcessorTemplate, error: Exception) -> None:
        """
        Handle errors that occur during processing.
        :param processor: The processor instance.
        :param error: The error that occurred.
        """
        exception_info = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
        processor._exceptions.append(exception_info)

        if processor.agent:
            processor.agent.status = "ERROR"
