"""
Data collection strategies with improved error handling and dependency management.
"""

from typing import Dict, Any, List
from ufo.agents.processors2.strategies.processing_strategy import BaseProcessingStrategy
from ufo.agents.processors2.core.processing_context import (
    ProcessingResult,
    ProcessingPhase,
    ProcessingContext,
)
from ufo.agents.processors2.core.processor_framework import ProcessingException
from ufo.contracts.contracts import Command
from ufo import utils

# Import for type hints only
try:
    from ufo.agents.processors2.core.strategy_dependency import StrategyDependency
except ImportError:
    # Fallback for when dependency module isn't available yet
    StrategyDependency = Any


class HostDataCollectionStrategy(BaseProcessingStrategy):
    """
    Host Agent data collection strategy with configurable error handling and dependency management.
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize the strategy.
        :param fail_fast: If True, raises exceptions immediately. If False, returns failed results.
        """
        super().__init__("host_data_collection", fail_fast=fail_fast)

    def get_dependencies(self) -> List["StrategyDependency"]:
        """
        Declare dependencies for host data collection.
        """
        try:
            from ufo.agents.processors2.core.strategy_dependency import (
                StrategyDependency,
            )

            return [
                StrategyDependency(
                    field_name="command_dispatcher",
                    required=True,
                    description="Command dispatcher for executing data collection commands",
                ),
                StrategyDependency(
                    field_name="log_path",
                    required=False,
                    default_value="",
                    description="Log path for saving screenshots",
                ),
                StrategyDependency(
                    field_name="session_step",
                    required=False,
                    default_value=0,
                    expected_type=int,
                    description="Current session step for file naming",
                ),
            ]
        except ImportError:
            return []  # Fallback when dependency system not available

    def get_provides(self) -> List[str]:
        """
        Declare what this strategy provides to subsequent strategies.
        """
        return [
            "desktop_screen_url",
            "control_info",
            "target_registry",
            "screenshot_path",
        ]

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        """Execute data collection with proper error handling and dependency validation."""
        try:
            # Validate dependencies using the new type-safe methods
            command_dispatcher = self.require_dependency(context, "command_dispatcher")
            log_path = context.get_local_safe("log_path", str, "")
            session_step = context.get_local_safe("session_step", int, 0)

            # 捕获桌面截图
            screenshot_data = await self._capture_desktop_screenshot(
                command_dispatcher, log_path, session_step
            )

            # 获取控件信息
            control_info = await self._get_desktop_control_info(command_dispatcher)

            # 注册第三方代理
            target_registry = self._register_third_party_agents(context, control_info)

            return ProcessingResult(
                success=True,
                data={
                    "desktop_screen_url": screenshot_data["url"],
                    "control_info": control_info,
                    "target_registry": target_registry,
                    "screenshot_path": screenshot_data["path"],
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            # 使用统一的错误处理方法
            return self.handle_error(e, ProcessingPhase.DATA_COLLECTION, context)

    async def _capture_desktop_screenshot(
        self, command_dispatcher, log_path: str, session_step: int
    ) -> Dict[str, Any]:
        """捕获桌面截图"""
        try:
            desktop_save_path = f"{log_path}action_step{session_step}.png"

            result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name="capture_desktop_screenshot",
                        parameters={"all_screens": True},
                        tool_type="data_collection",
                    )
                ]
            )

            desktop_screen_url = result[0].result
            utils.save_image_string(desktop_screen_url, desktop_save_path)

            return {"url": desktop_screen_url, "path": desktop_save_path}
        except Exception as e:
            # 如果fail_fast=True，这里会抛出ProcessingException
            # 如果fail_fast=False，会返回失败的ProcessingResult
            raise Exception(f"Failed to capture desktop screenshot: {str(e)}")

    async def _get_desktop_control_info(self, command_dispatcher) -> list:
        """获取桌面控件信息"""
        try:
            result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name="get_desktop_app_info",
                        parameters={"remove_empty": True, "refresh_app_windows": True},
                        tool_type="data_collection",
                    )
                ]
            )

            return result[0].result
        except Exception as e:
            raise Exception(f"Failed to get desktop control info: {str(e)}")

    def _register_third_party_agents(
        self, context: ProcessingContext, desktop_windows_info: list
    ) -> Any:
        """注册第三方代理"""
        try:
            from ufo.agents.processors.target import TargetRegistry, TargetKind

            target_registry = context.get_local("target_registry")
            if not target_registry:
                target_registry = TargetRegistry()
                context.set_local("target_registry", target_registry)

            # 注册桌面窗口
            target_registry.register_from_dicts(desktop_windows_info)

            # 注册第三方代理
            from ufo.config import Config

            configs = Config.get_instance().config_data
            third_party_agent_names = configs.get("ENABLED_THIRD_PARTY_AGENTS", [])

            third_party_agent_list = []
            start_index = len(desktop_windows_info) + 1

            for i, agent_name in enumerate(third_party_agent_names):
                label = str(i + start_index)
                third_party_agent_list.append(
                    {
                        "kind": TargetKind.THIRD_PARTY_AGENT.value,
                        "id": label,
                        "type": "ThirdPartyAgent",
                        "name": agent_name,
                    }
                )

            target_registry.register_from_dicts(third_party_agent_list)

            return target_registry

        except Exception as e:
            raise Exception(f"Failed to register third party agents: {str(e)}")


class ScreenshotCollectionStrategy(BaseProcessingStrategy):
    """
    Screenshot collection strategy with graceful error handling and dependency on host data.
    """

    def __init__(
        self, fail_fast: bool = False
    ):  # 默认不快速失败，适合截图这种非关键操作
        super().__init__("screenshot_collection", fail_fast=fail_fast)

    def get_dependencies(self) -> List["StrategyDependency"]:
        """
        Declare dependencies for screenshot collection.
        This strategy depends on data from HostDataCollectionStrategy.
        """
        try:
            from ufo.agents.processors2.core.strategy_dependency import (
                StrategyDependency,
            )

            return [
                StrategyDependency(
                    field_name="command_dispatcher",
                    required=True,
                    description="Command dispatcher for capturing screenshots",
                ),
                StrategyDependency(
                    field_name="log_path",
                    required=False,
                    default_value="",
                    description="Log path for saving screenshots",
                ),
                StrategyDependency(
                    field_name="session_step",
                    required=False,
                    default_value=0,
                    expected_type=int,
                    description="Session step for file naming",
                ),
                # Dependencies on previous strategy output
                StrategyDependency(
                    field_name="control_info",
                    required=True,
                    expected_type=list,
                    description="Control info from host data collection (provided by HostDataCollectionStrategy)",
                ),
                StrategyDependency(
                    field_name="target_registry",
                    required=False,
                    description="Target registry from host data collection",
                ),
            ]
        except ImportError:
            return []  # Fallback when dependency system not available

    def get_provides(self) -> List[str]:
        """
        Declare what this strategy provides to subsequent strategies.
        """
        return [
            "screenshot_paths",
            "screenshot_data",
            "image_urls",
            "clean_screenshot_url",
            "annotated_screenshot_path",
        ]

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        """Execute screenshot collection with graceful error handling and dependency validation."""
        try:
            # Use type-safe dependency access
            command_dispatcher = self.require_dependency(context, "command_dispatcher")
            log_path = context.get_local_safe("log_path", str, "")
            session_step = context.get_local_safe("session_step", int, 0)

            # Access data from previous strategy (HostDataCollectionStrategy)
            control_info = self.require_dependency(context, "control_info", list)
            target_registry = context.get_local_safe("target_registry")

            # 定义截图路径
            screenshot_paths = self._generate_screenshot_paths(log_path, session_step)

            # 执行截图命令
            screenshot_data = await self._capture_screenshots(
                command_dispatcher, screenshot_paths
            )

            # Log that we successfully accessed previous strategy's output
            self.logger.info(
                f"Successfully accessed control_info from previous strategy: "
                f"{len(control_info)} controls found"
            )

            return ProcessingResult(
                success=True,
                data={
                    "screenshot_paths": screenshot_paths,
                    "screenshot_data": screenshot_data,
                    "image_urls": screenshot_data.get("image_urls", []),
                    "clean_screenshot_url": screenshot_data.get("clean_url"),
                    "annotated_screenshot_path": screenshot_paths.get("annotated"),
                    # Also pass through previous data for subsequent strategies
                    "control_info": control_info,  # Pass through for next strategies
                    "target_registry": target_registry,  # Pass through for next strategies
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            # 截图失败通常不应该终止整个处理流程，所以返回失败结果而不抛出异常
            return self.handle_error(e, ProcessingPhase.DATA_COLLECTION, context)

    def _generate_screenshot_paths(
        self, log_path: str, session_step: int
    ) -> Dict[str, str]:
        """生成截图路径"""
        return {
            "clean": f"{log_path}action_step{session_step}.png",
            "annotated": f"{log_path}action_step{session_step}_annotated.png",
            "concat": f"{log_path}action_step{session_step}_concat.png",
        }

    async def _capture_screenshots(
        self, command_dispatcher, paths: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行截图捕获"""
        # 捕获应用窗口截图
        result = await command_dispatcher.execute_commands(
            [
                Command(
                    tool_name="capture_window_screenshot",
                    parameters={},
                    tool_type="data_collection",
                )
            ]
        )

        clean_screenshot_url = result[0].result
        utils.save_image_string(clean_screenshot_url, paths["clean"])

        return {
            "clean_url": clean_screenshot_url,
            "image_urls": [clean_screenshot_url],
            "paths": paths,
        }


class CriticalDataCollectionStrategy(BaseProcessingStrategy):
    """
    Critical data collection strategy that must succeed.
    """

    def __init__(self):
        super().__init__(
            "critical_data_collection", fail_fast=True
        )  # 关键数据收集必须快速失败

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        """Execute critical data collection."""
        try:
            # 关键数据收集逻辑
            critical_data = await self._collect_critical_data(context)

            return ProcessingResult(
                success=True,
                data={"critical_data": critical_data},
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            # 关键数据收集失败时，抛出异常以触发所有中间件的on_error
            return self.handle_error(e, ProcessingPhase.DATA_COLLECTION, context)

    async def _collect_critical_data(
        self, context: ProcessingContext
    ) -> Dict[str, Any]:
        """收集关键数据"""
        # 模拟关键数据收集
        return {"timestamp": context.get("session_step"), "status": "active"}
