"""
示例：使用新装饰器API的策略实现

这个文件展示了如何使用新的装饰器系统来声明策略依赖关系。
"""

import logging
from typing import Dict, Any

from ufo.agents.processors2.core.processing_context import (
    ProcessingContext,
    ProcessingResult,
)
from ufo.agents.processors2.strategies.processing_strategy import ProcessingStrategy
from ufo.agents.processors2.core.strategy_dependency import (
    strategy_config,
    depends_on,
    provides,
    StrategyDependency,
    DependencyType,
)


# 示例1: 使用组合装饰器
@strategy_config(
    dependencies=[
        StrategyDependency(
            "user_request", DependencyType.REQUIRED, "User's original request"
        ),
        StrategyDependency(
            "current_app", DependencyType.OPTIONAL, "Currently active application"
        ),
    ],
    provides=["parsed_request", "request_intent", "target_elements"],
)
class RequestParsingStrategy(ProcessingStrategy):
    """解析用户请求的策略"""

    def __init__(self):
        super().__init__("request_parsing")
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        """执行请求解析"""
        try:
            # 获取依赖字段
            user_request = context.get_local("user_request")
            current_app = context.get_local("current_app", "Unknown")

            # 模拟解析逻辑
            parsed_request = f"Parsed: {user_request}"
            request_intent = "click_action"  # 简化的意图识别
            target_elements = ["button_1", "text_field_2"]

            # 返回结果 - 这些应该与provides声明一致
            result_data = {
                "parsed_request": parsed_request,
                "request_intent": request_intent,
                "target_elements": target_elements,
            }

            self.logger.info(f"Request parsed successfully for app: {current_app}")

            return ProcessingResult(
                success=True, data=result_data, message="Request parsing completed"
            )

        except Exception as e:
            self.logger.error(f"Request parsing failed: {e}")
            return ProcessingResult(
                success=False, error=str(e), message="Request parsing failed"
            )


# 示例2: 使用单独的装饰器
@depends_on("parsed_request", DependencyType.REQUIRED, "Parsed user request")
@depends_on("target_elements", DependencyType.REQUIRED, "Target UI elements")
@depends_on("app_context", DependencyType.OPTIONAL, "Application context information")
@provides("action_plan", "execution_steps", "validation_criteria")
class ActionPlanningStrategy(ProcessingStrategy):
    """制定行动计划的策略"""

    def __init__(self):
        super().__init__("action_planning")
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        """执行行动规划"""
        try:
            # 获取依赖字段
            parsed_request = context.get_local("parsed_request")
            target_elements = context.get_local("target_elements")
            app_context = context.get_local("app_context", {})

            # 模拟规划逻辑
            action_plan = {
                "type": "ui_interaction",
                "target": target_elements[0] if target_elements else "unknown",
                "action": "click",
            }

            execution_steps = [
                "1. Locate target element",
                "2. Verify element accessibility",
                "3. Perform click action",
                "4. Validate result",
            ]

            validation_criteria = {
                "expected_changes": ["ui_state_change"],
                "timeout": 5000,
            }

            # 返回结果
            result_data = {
                "action_plan": action_plan,
                "execution_steps": execution_steps,
                "validation_criteria": validation_criteria,
            }

            self.logger.info("Action plan created successfully")

            return ProcessingResult(
                success=True, data=result_data, message="Action planning completed"
            )

        except Exception as e:
            self.logger.error(f"Action planning failed: {e}")
            return ProcessingResult(
                success=False, error=str(e), message="Action planning failed"
            )


# 示例3: 错误示例 - provides声明与实际返回不一致
@depends_on("action_plan", DependencyType.REQUIRED, "Action plan to execute")
@depends_on("validation_criteria", DependencyType.REQUIRED, "Validation criteria")
@provides("execution_result", "success_status", "error_details")  # 声明了这些字段
class ActionExecutionStrategy(ProcessingStrategy):
    """执行行动的策略（故意包含不一致的示例）"""

    def __init__(self):
        super().__init__("action_execution")
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        """执行行动"""
        try:
            action_plan = context.get_local("action_plan")
            validation_criteria = context.get_local("validation_criteria")

            # 模拟执行
            execution_success = True

            # 故意返回与provides不完全一致的字段来演示验证功能
            result_data = {
                "execution_result": "completed",
                "success_status": execution_success,
                # 缺少 error_details - 这会触发警告
                "extra_field": "not_declared",  # 额外字段 - 这也会触发警告
            }

            return ProcessingResult(
                success=True, data=result_data, message="Action execution completed"
            )

        except Exception as e:
            self.logger.error(f"Action execution failed: {e}")
            return ProcessingResult(
                success=False, error=str(e), message="Action execution failed"
            )


# 示例4: 正确的策略实现
@strategy_config(
    dependencies=[
        StrategyDependency(
            "execution_result", DependencyType.REQUIRED, "Result of action execution"
        ),
        StrategyDependency(
            "success_status", DependencyType.REQUIRED, "Whether execution succeeded"
        ),
    ],
    provides=["final_result", "summary", "next_suggestions"],
)
class ResultSummaryStrategy(ProcessingStrategy):
    """总结结果的策略"""

    def __init__(self):
        super().__init__("result_summary")
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        """执行结果总结"""
        try:
            execution_result = context.get_local("execution_result")
            success_status = context.get_local("success_status")

            # 生成总结
            final_result = {
                "status": "success" if success_status else "failed",
                "execution": execution_result,
                "timestamp": "2024-01-01T12:00:00Z",  # 简化时间戳
            }

            summary = f"Task {'completed successfully' if success_status else 'failed'}"

            next_suggestions = (
                ["Continue with next task", "Review execution logs"]
                if success_status
                else ["Retry with different approach", "Check error details"]
            )

            # 正确返回所有声明的字段
            result_data = {
                "final_result": final_result,
                "summary": summary,
                "next_suggestions": next_suggestions,
            }

            self.logger.info("Result summary generated successfully")

            return ProcessingResult(
                success=True, data=result_data, message="Result summary completed"
            )

        except Exception as e:
            self.logger.error(f"Result summary failed: {e}")
            return ProcessingResult(
                success=False, error=str(e), message="Result summary failed"
            )
