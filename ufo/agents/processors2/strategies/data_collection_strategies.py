"""
Data collection strategies with improved error handling.
"""

from typing import Dict, Any
from ufo.agents.processors2.core.processor_framework import (
    BaseProcessingStrategy,
    ProcessingResult,
    ProcessingPhase,
    ProcessingContext,
    ProcessingException,
)
from ufo.contracts.contracts import Command
from ufo import utils


class HostDataCollectionStrategy(BaseProcessingStrategy):
    """
    Host Agent data collection strategy with configurable error handling.
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Initialize the strategy.
        :param fail_fast: If True, raises exceptions immediately. If False, returns failed results.
        """
        super().__init__("host_data_collection", fail_fast=fail_fast)

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        """Execute data collection with proper error handling."""
        try:
            # 捕获桌面截图
            screenshot_data = await self._capture_desktop_screenshot(context)

            # 获取控件信息
            control_info = await self._get_desktop_control_info(context)

            # 注册第三方代理
            self._register_third_party_agents(context, control_info)

            return ProcessingResult(
                success=True,
                data={
                    "desktop_screen_url": screenshot_data["url"],
                    "control_info": control_info,
                    "target_registry": context.get_local("target_registry"),
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            # 使用统一的错误处理方法
            return self.handle_error(e, ProcessingPhase.DATA_COLLECTION, context)

    async def _capture_desktop_screenshot(
        self, context: ProcessingContext
    ) -> Dict[str, Any]:
        """捕获桌面截图"""
        try:
            command_dispatcher = context.get("command_dispatcher")
            log_path = context.get("log_path", "")
            session_step = context.get("session_step", 0)

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

    async def _get_desktop_control_info(self, context: ProcessingContext) -> list:
        """获取桌面控件信息"""
        try:
            command_dispatcher = context.get("command_dispatcher")

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
    ) -> None:
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

        except Exception as e:
            raise Exception(f"Failed to register third party agents: {str(e)}")


class ScreenshotCollectionStrategy(BaseProcessingStrategy):
    """
    Screenshot collection strategy with graceful error handling.
    """

    def __init__(
        self, fail_fast: bool = False
    ):  # 默认不快速失败，适合截图这种非关键操作
        super().__init__("screenshot_collection", fail_fast=fail_fast)

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        """Execute screenshot collection with graceful error handling."""
        try:
            # 定义截图路径
            screenshot_paths = self._generate_screenshot_paths(context)

            # 执行截图命令
            screenshot_data = await self._capture_screenshots(context, screenshot_paths)

            return ProcessingResult(
                success=True,
                data={
                    "screenshot_paths": screenshot_paths,
                    "screenshot_data": screenshot_data,
                    "image_urls": screenshot_data.get("image_urls", []),
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            # 截图失败通常不应该终止整个处理流程，所以返回失败结果而不抛出异常
            return self.handle_error(e, ProcessingPhase.DATA_COLLECTION, context)

    def _generate_screenshot_paths(self, context: ProcessingContext) -> Dict[str, str]:
        """生成截图路径"""
        log_path = context.get("log_path", "")
        session_step = context.get("session_step", 0)

        return {
            "clean": f"{log_path}action_step{session_step}.png",
            "annotated": f"{log_path}action_step{session_step}_annotated.png",
            "concat": f"{log_path}action_step{session_step}_concat.png",
        }

    async def _capture_screenshots(
        self, context: ProcessingContext, paths: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行截图捕获"""
        command_dispatcher = context.get("command_dispatcher")

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
