import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from ufo.agents.agent.basic import BasicAgent
from ufo.module.context import Context

T = TypeVar("T")


class ProcessingPhase(Enum):
    """
    Enum for processing phases.
    """

    SETUP = "setup"
    DATA_COLLECTION = "data_collection"
    LLM_INTERACTION = "llm_interaction"
    ACTION_EXECUTION = "action_execution"
    MEMORY_UPDATE = "memory_update"
    CLEANUP = "cleanup"


class ProcessingException(Exception):
    """
    Exception raised during processing that contains additional context.
    """
    
    def __init__(self, message: str, phase: Optional[ProcessingPhase] = None, 
                 context_data: Optional[Dict[str, Any]] = None, 
                 original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.phase = phase
        self.context_data = context_data or {}
        self.original_exception = original_exception


@dataclass
class ProcessingResult:
    """
    Data class for processing results.
    """

    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    phase: Optional[ProcessingPhase] = None
    execution_time: float = 0.0


@dataclass
class ProcessingContext:
    """
    Processing context that combines global context with local processing data.
    """

    global_context: Context  # Global context shared across the entire session
    local_data: Dict[str, Any] = field(
        default_factory=dict
    )  # Temporary data for this processing

    def get_global(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the global context.
        :param key: The key to retrieve.
        :param default: The default value if the key is not found.
        :return: The value from the global context or the default value.
        """
        return self.global_context.get(key, default)

    def set_global(self, key: str, value: Any) -> None:
        """
        Set global context data.
        :param key: The key to set.
        :param value: The value to set.
        """
        self.global_context.set(key, value)

    def get_local(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the local temporary data.
        :param key: The key to retrieve.
        :param default: The default value if the key is not found.
        :return: The value from the local temporary data or the default value.
        """
        return self.local_data.get(key, default)

    def set_local(self, key: str, value: Any) -> None:
        """
        Set a value in the local temporary data.
        :param key: The key to set.
        :param value: The value to set.
        """
        self.local_data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from local data, falling back to global context.
        """
        if key in self.local_data:
            return self.local_data[key]
        return self.global_context.get(key, default)

    def update_local(self, data: Dict[str, Any]) -> None:
        """
        Batch update local data.
        :param data: The data to update.
        """
        self.local_data.update(data)

    def promote_to_global(self, key: str) -> None:
        """
        Promote local data to global context.
        :param key: The key to promote.
        """
        if key in self.local_data:
            self.global_context.set(key, self.local_data[key])

    def promote_multiple_to_global(self, keys: List[str]) -> None:
        """
        Promote multiple local data to global context.
        :param keys: The keys to promote.
        """
        for key in keys:
            self.promote_to_global(key)


class ProcessingStrategy(Protocol):
    """
    Protocol for processing strategies.
    """

    async def execute(self, context: ProcessingContext) -> ProcessingResult: ...


class ProcessorMiddleware(ABC):
    """
    Processor middleware base class.
    """

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


class ProcessorTemplate(ABC):
    """
    Processor template base class - defines the processing workflow.
    """

    def __init__(self, agent: BasicAgent, global_context: Context):
        """
        Initialize the processor template.
        :param agent: The agent instance which this processor serves.
        :param context: The global context.
        """
        self.agent = agent
        self.global_context = global_context  # Shared global context
        self.strategies: Dict[ProcessingPhase, ProcessingStrategy] = {}
        self.middleware_chain: List[ProcessorMiddleware] = []
        self.logger = logging.getLogger(self.__class__.__name__)
        self._exceptions: List[Dict[str, Any]] = []
        self._setup_strategies()
        self._setup_middleware()

        self.processing_context = self._create_processing_context()

    @abstractmethod
    def _setup_strategies(self) -> None:
        """
        Set up processing strategies.
        """
        pass

    @abstractmethod
    def _setup_middleware(self) -> None:
        """
        Set up middleware.
        """
        pass

    @abstractmethod
    def _create_memory_item(self) -> None:
        """
        Create a memory item for this processor.
        """
        pass

    def _create_processing_context(self) -> ProcessingContext:
        """
        Create a processing context for this execution.
        Can be overridden by subclasses to customize initial local data.
        """
        initial_local_data = self._get_initial_local_data()
        return ProcessingContext(
            global_context=self.global_context, local_data=initial_local_data
        )

    def _get_initial_local_data(self) -> Dict[str, Any]:
        """
        Get initial local data for processing context.
        Can be overridden by subclasses.
        """
        return {
            "agent": self.agent,
            "processor": self,
            # Copy some common data from global context to local, avoiding frequent access to global context
            "session_step": self.global_context.get("session_step", 0),
            "round_step": self.global_context.get("round_step", 0),
            "round_num": self.global_context.get("round_num", 0),
        }

    def _finalize_processing_context(
        self, processing_context: ProcessingContext
    ) -> None:
        """
        Finalize processing context, deciding what to promote to global context.
        Can be overridden by subclasses.
        :param processing_context: The processing context to finalize.
        """
        # Promote keys from local context to global context
        keys_to_promote = self._get_keys_to_promote()
        processing_context.promote_multiple_to_global(keys_to_promote)

    def _get_keys_to_promote(self) -> List[str]:
        """
        Get keys that should be promoted to global context.
        Can be overridden by subclasses.
        :return: A list of keys to promote.
        """
        # This method can be overridden by subclasses to customize the keys to promote
        return []

    async def process(self) -> ProcessingResult:
        """
        A template method that defines the processing workflow.
        Process the input data through the defined strategies and middleware.
        """
        start_time = time.time()

        try:
            # Execute pre-processing middleware
            for middleware in self.middleware_chain:
                self.logger.info(
                    f"Executing middleware before_process: {middleware.__class__.__name__}"
                )
                await middleware.before_process(self, self.processing_context)

            # Execute each phase processing
            combined_result = ProcessingResult(success=True, data={})

            for phase in ProcessingPhase:
                if phase in self.strategies:
                    phase_start = time.time()

                    strategy = self.strategies[phase]

                    self.logger.info(
                        f"Starting phase: {phase.value}, with strategy: {strategy.__class__.__name__}"
                    )

                    result = await strategy.execute(self.processing_context)
                    result.execution_time = time.time() - phase_start
                    result.phase = phase

                    if not result.success:
                        # Strategy返回失败结果，创建异常并触发on_error中间件
                        strategy_error = Exception(f"Strategy {strategy.__class__.__name__} failed: {result.error}")
                        
                        # 执行错误处理中间件
                        for middleware in self.middleware_chain:
                            self.logger.info(
                                f"Executing middleware on_error for strategy failure: {middleware.__class__.__name__}"
                            )
                            await middleware.on_error(self, strategy_error)
                        
                        combined_result = result
                        break

                    # Merge strategy results into local context for the next strategy
                    self.processing_context.update_local(result.data)

                    # Merge into final result
                    combined_result.data.update(result.data)

            combined_result.execution_time = time.time() - start_time

            # Decide what data needs to be promoted to global context
            self._finalize_processing_context(self.processing_context)

            # Execute post-processing middleware
            for middleware in reversed(self.middleware_chain):
                self.logger.info(
                    f"Executing middleware after_process: {middleware.__class__.__name__}"
                )
                await middleware.after_process(self, combined_result)

            return combined_result

        except Exception as e:
            error_result = ProcessingResult(
                success=False,
                error=str(e),
                data={},
                execution_time=time.time() - start_time,
            )

            self.logger.error(f"Processing failed: {error_result.error}")

            # 如果是ProcessingException，提取更多上下文信息
            if isinstance(e, ProcessingException):
                error_result.phase = e.phase
                error_result.data = e.context_data
                self.logger.error(f"Processing failed at phase: {e.phase}, context: {e.context_data}")

            # Execute error handling middleware
            for middleware in self.middleware_chain:
                self.logger.info(
                    f"Executing middleware on_error: {middleware.__class__.__name__}"
                )
                await middleware.on_error(self, e)

            return error_result


class BaseProcessingStrategy(ABC):
    """
    Base class for processing strategies.
    """

    def __init__(self, name: str, fail_fast: bool = True):
        """
        Initialize the processing strategy.
        :param name: The name of the strategy.
        :param fail_fast: Whether to raise exceptions immediately or return failed results.
        """
        self.name = name
        self.fail_fast = fail_fast
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{name}")

    @abstractmethod
    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        """
        Execute the processing strategy.
        :param context: The processing context with both global and local data.
        :return: The processing result.
        """
        pass
    
    def handle_error(self, error: Exception, phase: ProcessingPhase, context: ProcessingContext) -> ProcessingResult:
        """
        Handle errors in a consistent way.
        :param error: The exception that occurred.
        :param phase: The processing phase where the error occurred.
        :param context: The processing context.
        :return: Either raises an exception or returns a failed result.
        """
        error_message = f"{self.__class__.__name__} failed: {str(error)}"
        
        if self.fail_fast:
            # 抛出ProcessingException，让中间件的on_error被触发
            raise ProcessingException(
                message=error_message,
                phase=phase,
                context_data={"strategy_name": self.name},
                original_exception=error
            )
        else:
            # 返回失败结果，不触发on_error中间件
            self.logger.error(error_message)
            return ProcessingResult(
                success=False,
                error=error_message,
                data={},
                phase=phase
            )
