from typing import List, Dict, Any, Optional
from dataclasses import asdict
from ufo.agents.processors2.core.processor_framework import (
    BaseProcessingStrategy,
    ProcessorTemplate,
    ProcessingPhase,
)
from ufo.agents.processors2.strategies.strategy import (
    ScreenshotCollectionStrategy,
    ControlInfoCollectionStrategy,
    PromptConstructionStrategy,
)

# from ufo.agents.processors2.strategies.strategy import LLMInteractionStrategy
# from ufo.agents.processors2.strategies.strategy import ActionExecutionStrategy
from ufo.agents.processors2.middleware.common_middleware import (
    TimingMiddleware,
    LoggingMiddleware,
    MemoryMiddleware,
    ExceptionHandlingMiddleware,
)
from ufo.agents.processors.actions import ActionCommandInfo
from ufo.agents.processors.app_agent_processor import (
    AppAgentResponse,
    AppAgentAdditionalMemory,
)
from ufo.agents.memory.memory import MemoryItem


class AppAgentProcessorV2(ProcessorTemplate):
    """重构后的App Agent处理器"""

    def __init__(self, agent, context, ground_service=None):
        self.app_agent = agent
        self.host_agent = agent.host
        self.grounding_service = ground_service

        # 初始化处理器状态
        self._image_urls = []
        self._memory_data = MemoryItem()
        self._response = None
        self._cost = 0.0

        super().__init__(agent, context)

    def _setup_strategies(self) -> None:
        """配置App Agent特定的处理策略"""

        # 数据收集阶段策略
        self.strategies[ProcessingPhase.DATA_COLLECTION] = (
            CompositeDataCollectionStrategy(
                [
                    ScreenshotCollectionStrategy(),
                    ControlInfoCollectionStrategy(backends=["uia", "omniparser"]),
                    PromptConstructionStrategy(),
                ]
            )
        )

        # LLM交互阶段策略
        self.strategies[ProcessingPhase.LLM_INTERACTION] = AppAgentLLMStrategy()

        # 动作执行阶段策略
        self.strategies[ProcessingPhase.ACTION_EXECUTION] = AppAgentActionStrategy()

        # 内存更新阶段策略
        self.strategies[ProcessingPhase.MEMORY_UPDATE] = AppAgentMemoryStrategy()

    def _setup_middleware(self) -> None:
        """设置中间件链"""
        self.middleware_chain = [
            TimingMiddleware(),
            LoggingMiddleware(),
            ExceptionHandlingMiddleware(),
            MemoryMiddleware(),
        ]

    def _create_memory_item(self) -> MemoryItem:
        """创建内存项"""
        return MemoryItem()

    def _sync_memory_with_result(self, result) -> None:
        """同步内存数据"""
        # 实现内存同步逻辑
        if hasattr(self, "_response") and self._response:
            self._memory_data.add_values_from_dict(asdict(self._response))


# 复合数据收集策略
class CompositeDataCollectionStrategy(BaseProcessingStrategy):
    """复合数据收集策略"""

    def __init__(self, strategies: List[BaseProcessingStrategy]):
        self.strategies = strategies

    async def execute(self, context: Any):
        """执行所有数据收集策略"""
        combined_data = {}

        for strategy in self.strategies:
            result = await strategy.execute(context)
            if not result.success:
                return result
            combined_data.update(result.data)

        # 准备上下文数据
        self._prepare_context_data(context, combined_data)

        from ufo.agents.processors2.core.processor_framework import (
            ProcessingResult,
            ProcessingPhase,
        )

        return ProcessingResult(
            success=True, data=combined_data, phase=ProcessingPhase.DATA_COLLECTION
        )

    def _prepare_context_data(self, context: Any, data: Dict[str, Any]) -> None:
        """准备上下文数据供后续阶段使用"""
        context.update(
            {
                "image_urls": data.get("image_urls", []),
                "filtered_controls": data.get("filtered_controls", []),
                "prompt_message": data.get("prompt_message"),
                "screenshot_paths": data.get("screenshot_paths", {}),
            }
        )


# App Agent特定的LLM策略
class AppAgentLLMStrategy(BaseProcessingStrategy):
    """App Agent LLM交互策略"""

    async def execute(self, context: Any):
        """执行LLM交互"""
        try:
            agent = context.get("agent")
            prompt_message = context.get("prompt_message")

            if not prompt_message:
                raise ValueError("No prompt message available")

            # 获取LLM响应
            response_text, cost = agent.get_response(
                prompt_message, agent_type="APP", use_backup_engine=True
            )

            # 解析响应
            response_dict = agent.response_to_dict(response_text)
            response = AppAgentResponse(**response_dict)

            from ufo.agents.processors2.core.processor_framework import (
                ProcessingResult,
                ProcessingPhase,
            )

            return ProcessingResult(
                success=True,
                data={
                    "response": response,
                    "response_text": response_text,
                    "cost": cost,
                },
                phase=ProcessingPhase.LLM_INTERACTION,
            )

        except Exception as e:
            from ufo.agents.processors2.core.processor_framework import (
                ProcessingResult,
                ProcessingPhase,
            )

            return ProcessingResult(
                success=False,
                error=f"LLM interaction failed: {str(e)}",
                data={},
                phase=ProcessingPhase.LLM_INTERACTION,
            )


# App Agent动作执行策略
class AppAgentActionStrategy(BaseProcessingStrategy):
    """App Agent动作执行策略"""

    async def execute(self, context: Any):
        """执行动作"""
        try:
            response = context.get("response")
            command_dispatcher = context.get("command_dispatcher")

            if not response or not response.function:
                from ufo.agents.processors2.core.processor_framework import (
                    ProcessingResult,
                    ProcessingPhase,
                )

                return ProcessingResult(
                    success=True,
                    data={"message": "No action to execute"},
                    phase=ProcessingPhase.ACTION_EXECUTION,
                )

            # 执行命令
            from ufo.contracts.contracts import Command

            result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name=response.function,
                        parameters=response.arguments,
                        tool_type="action",
                    )
                ]
            )

            # 创建动作信息
            action = ActionCommandInfo(
                function=response.function,
                arguments=response.arguments,
                target=None,  # 需要根据实际情况设置
                status=response.status,
                result=result[0],
            )

            from ufo.agents.processors2.core.processor_framework import (
                ProcessingResult,
                ProcessingPhase,
            )

            return ProcessingResult(
                success=True,
                data={"action": action, "execution_result": result},
                phase=ProcessingPhase.ACTION_EXECUTION,
            )

        except Exception as e:
            from ufo.agents.processors2.core.processor_framework import (
                ProcessingResult,
                ProcessingPhase,
            )

            return ProcessingResult(
                success=False,
                error=f"Action execution failed: {str(e)}",
                data={},
                phase=ProcessingPhase.ACTION_EXECUTION,
            )


# App Agent内存更新策略
class AppAgentMemoryStrategy(BaseProcessingStrategy):
    """App Agent内存更新策略"""

    async def execute(self, context: Any):
        """更新内存"""
        try:
            agent = context.get("agent")
            response = context.get("response")
            action = context.get("action")

            # 创建额外内存数据
            additional_memory = AppAgentAdditionalMemory(
                Step=context.get("session_step", 0),
                RoundStep=context.get("round_step", 0),
                AgentStep=agent.step,
                Round=context.get("round_num", 0),
                Subtask=context.get("subtask", ""),
                SubtaskIndex=context.get("round_subtask_amount", 0),
                FunctionCall=[action.function] if action else [],
                Action=[asdict(action)] if action else [],
                ActionSuccess=[],  # 需要根据实际成功动作填充
                ActionType=(
                    [action.result.namespace] if action and action.result else []
                ),
                Request=context.get("request", ""),
                Agent=agent.__class__.__name__,
                AgentName=agent.name,
                Application=context.get("app_root", ""),
                Cost=context.get("cost", 0.0),
                Results="",  # 需要根据实际结果填充
                error="",
                time_cost=context.get("time_cost", {}),
                ControlLog={},
            )

            from ufo.agents.processors2.core.processor_framework import (
                ProcessingResult,
                ProcessingPhase,
            )

            return ProcessingResult(
                success=True,
                data={
                    "additional_memory": additional_memory,
                    "response_data": asdict(response) if response else {},
                },
                phase=ProcessingPhase.MEMORY_UPDATE,
            )

        except Exception as e:
            from ufo.agents.processors2.core.processor_framework import (
                ProcessingResult,
                ProcessingPhase,
            )

            return ProcessingResult(
                success=False,
                error=f"Memory update failed: {str(e)}",
                data={},
                phase=ProcessingPhase.MEMORY_UPDATE,
            )
