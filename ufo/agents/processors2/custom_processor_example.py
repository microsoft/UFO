from typing import Dict, Any
from ufo.agents.processors2.core.processor_framework import (
    ProcessorTemplate,
    ProcessingPhase,
)
from ufo.agents.processors2.middleware.common_middleware import (
    TimingMiddleware,
    LoggingMiddleware,
)


class WeatherAgentProcessorV2(ProcessorTemplate):
    """天气代理处理器示例 - 展示如何创建新的处理器"""

    def __init__(self, agent, context):
        self.weather_agent = agent
        super().__init__(agent, context)

    def _setup_strategies(self) -> None:
        """配置天气代理特定的处理策略"""

        # 只需要数据收集和LLM交互，不需要复杂的UI操作
        self.strategies[ProcessingPhase.DATA_COLLECTION] = (
            WeatherDataCollectionStrategy()
        )
        self.strategies[ProcessingPhase.LLM_INTERACTION] = WeatherLLMStrategy()
        # 跳过ACTION_EXECUTION阶段，因为天气查询不需要UI操作
        self.strategies[ProcessingPhase.MEMORY_UPDATE] = SimpleMemoryStrategy()

    def _setup_middleware(self) -> None:
        """设置中间件链"""
        self.middleware_chain = [
            TimingMiddleware(),
            WeatherLoggingMiddleware(),  # 自定义日志中间件
        ]


class WeatherDataCollectionStrategy:
    """天气数据收集策略"""

    async def execute(self, context: Any):
        """收集天气相关数据"""
        try:
            # 获取位置信息
            location = await self._get_user_location(context)

            # 获取天气API密钥
            api_key = context.get("weather_api_key")

            from ufo.agents.processors2.core.processor_framework import (
                ProcessingResult,
                ProcessingPhase,
            )

            return ProcessingResult(
                success=True,
                data={
                    "location": location,
                    "api_key": api_key,
                    "timestamp": context.get("timestamp"),
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            from ufo.agents.processors2.core.processor_framework import (
                ProcessingResult,
                ProcessingPhase,
            )

            return ProcessingResult(
                success=False,
                error=f"Weather data collection failed: {str(e)}",
                data={},
                phase=ProcessingPhase.DATA_COLLECTION,
            )

    async def _get_user_location(self, context: Any) -> str:
        """获取用户位置"""
        # 从请求中解析位置信息
        request = context.get("request", "")
        # 简化的位置提取逻辑
        if "beijing" in request.lower():
            return "Beijing"
        elif "shanghai" in request.lower():
            return "Shanghai"
        else:
            return "Unknown"


class WeatherLLMStrategy:
    """天气LLM交互策略"""

    async def execute(self, context: Any):
        """执行天气查询的LLM交互"""
        try:
            agent = context.get("agent")
            location = context.get("location")

            # 构建天气查询的特定提示
            prompt = self._build_weather_prompt(context)

            # 获取LLM响应
            response_text, cost = agent.get_response(
                prompt, agent_type="WEATHER", use_backup_engine=True
            )

            # 解析天气响应
            weather_info = self._parse_weather_response(response_text)

            from ufo.agents.processors2.core.processor_framework import (
                ProcessingResult,
                ProcessingPhase,
            )

            return ProcessingResult(
                success=True,
                data={
                    "weather_info": weather_info,
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
                error=f"Weather LLM interaction failed: {str(e)}",
                data={},
                phase=ProcessingPhase.LLM_INTERACTION,
            )

    def _build_weather_prompt(self, context: Any) -> Dict[str, Any]:
        """构建天气查询提示"""
        location = context.get("location", "Unknown")
        request = context.get("request", "")

        return {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a weather assistant. Provide accurate weather information.",
                },
                {
                    "role": "user",
                    "content": f"What's the weather like in {location}? User request: {request}",
                },
            ]
        }

    def _parse_weather_response(self, response: str) -> Dict[str, Any]:
        """解析天气响应"""
        # 简化的天气信息解析
        return {
            "temperature": "25°C",
            "condition": "Sunny",
            "humidity": "60%",
            "raw_response": response,
        }


class SimpleMemoryStrategy:
    """简单内存策略"""

    async def execute(self, context: Any):
        """更新内存"""
        try:
            weather_info = context.get("weather_info", {})

            memory_data = {
                "query_time": context.get("timestamp"),
                "location": context.get("location"),
                "weather_result": weather_info,
                "cost": context.get("cost", 0.0),
            }

            from ufo.agents.processors2.core.processor_framework import (
                ProcessingResult,
                ProcessingPhase,
            )

            return ProcessingResult(
                success=True,
                data={"memory_data": memory_data},
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


class WeatherLoggingMiddleware(LoggingMiddleware):
    """天气代理专用日志中间件"""

    async def before_process(self, processor, context) -> None:
        location = context.get("location", "Unknown")
        processor.logger.info(
            f"WeatherAgent: Starting weather query for location: {location}"
        )

    async def after_process(self, processor, result) -> None:
        if result.success:
            weather_info = result.data.get("weather_info", {})
            processor.logger.info(
                f"Weather query completed: {weather_info.get('condition', 'N/A')}"
            )
        else:
            processor.logger.error(f"Weather query failed: {result.error}")
