from typing import Dict, List, Type, Any, Optional
from ufo.agents.processors2.core.processor_framework import ProcessorTemplate
from ufo.agents.processors2.app_agent_processor import AppAgentProcessorV2
from ufo.agents.processors2.host_agent_processor import (
    HostAgentProcessorV2,
)
from ufo.agents.processors2.custom_processor_example import (
    WeatherAgentProcessorV2,
)


class ProcessorFactory:
    """处理器工厂类"""

    _registry: Dict[str, Type[ProcessorTemplate]] = {
        "app_agent": AppAgentProcessorV2,
        "host_agent": HostAgentProcessorV2,
        "weather_agent": WeatherAgentProcessorV2,
    }

    @classmethod
    def register_processor(
        cls, agent_type: str, processor_class: Type[ProcessorTemplate]
    ):
        """注册新的处理器类型"""
        cls._registry[agent_type] = processor_class

    @classmethod
    def create_processor(
        cls, agent_type: str, agent: Any, context: Any, **kwargs
    ) -> ProcessorTemplate:
        """创建处理器实例"""
        processor_class = cls._registry.get(agent_type)

        if not processor_class:
            raise ValueError(f"Unknown processor type: {agent_type}")

        return processor_class(agent, context, **kwargs)

    @classmethod
    def list_available_processors(cls) -> List[str]:
        """列出可用的处理器类型"""
        return list(cls._registry.keys())


# 使用示例
# class ProcessorUsageExample:
#     """处理器使用示例"""

#     async def example_usage(self):
#         """展示如何使用新的处理器框架"""

#         # 1. 创建App Agent处理器
#         app_processor = ProcessorFactory.create_processor(
#             agent_type="app_agent",
#             agent=app_agent,
#             context=context,
#             ground_service=grounding_service,
#         )

#         # 执行处理
#         result = await app_processor.process()

#         if result.success:
#             print(f"Processing completed successfully in {result.execution_time:.2f}s")
#             print(f"Result data keys: {list(result.data.keys())}")
#         else:
#             print(f"Processing failed: {result.error}")

#         # 2. 创建自定义天气代理处理器
#         weather_processor = ProcessorFactory.create_processor(
#             agent_type="weather_agent", agent=weather_agent, context=weather_context
#         )

#         weather_result = await weather_processor.process()

#         # 3. 注册新的处理器类型
#         class CustomTaskProcessor(ProcessorTemplate):
#             def _setup_strategies(self):
#                 # 自定义策略设置
#                 pass

#             def _setup_middleware(self):
#                 # 自定义中间件设置
#                 pass

#         ProcessorFactory.register_processor("custom_task", CustomTaskProcessor)

#         # 4. 使用新注册的处理器
#         custom_processor = ProcessorFactory.create_processor(
#             agent_type="custom_task", agent=custom_agent, context=custom_context
#         )
