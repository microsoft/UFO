from typing import List, Dict, Any
from ufo.agents.processors2.core.processor_framework import (
    BaseProcessingStrategy,
    ProcessingResult,
    ProcessingPhase,
    ProcessingContext,
)
from ufo.contracts.contracts import Command
from ufo import utils


class ScreenshotCollectionStrategy(BaseProcessingStrategy):
    """截图收集策略"""

    def __init__(self):
        super().__init__("screenshot_collection")

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
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
            return ProcessingResult(
                success=False,
                error=f"Screenshot collection failed: {str(e)}",
                data={},
                phase=ProcessingPhase.DATA_COLLECTION,
            )

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


class ControlInfoCollectionStrategy(BaseProcessingStrategy):
    """控件信息收集策略"""

    def __init__(self, backends: List[str] = None):
        super().__init__("control_info_collection")
        self.backends = backends or ["uia"]

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        try:
            all_controls = []
            control_info_data = {}

            # 根据配置的后端收集控件信息
            for backend in self.backends:
                if backend == "uia":
                    uia_controls = await self._collect_uia_controls(context)
                    all_controls.extend(uia_controls)
                    control_info_data["uia_controls"] = uia_controls

                elif backend == "omniparser":
                    grounding_controls = await self._collect_grounding_controls(context)
                    all_controls.extend(grounding_controls)
                    control_info_data["grounding_controls"] = grounding_controls

            # 合并和过滤控件
            merged_controls = self._merge_controls(all_controls)
            filtered_controls = self._filter_controls(merged_controls, context)

            return ProcessingResult(
                success=True,
                data={
                    "all_controls": all_controls,
                    "merged_controls": merged_controls,
                    "filtered_controls": filtered_controls,
                    "control_info_data": control_info_data,
                },
                phase=ProcessingPhase.DATA_COLLECTION,
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"Control info collection failed: {str(e)}",
                data={},
                phase=ProcessingPhase.DATA_COLLECTION,
            )

    async def _collect_uia_controls(self, context: Any) -> List[Any]:
        """收集UIA控件信息"""
        command_dispatcher = context.get("command_dispatcher")

        result = await command_dispatcher.execute_commands(
            [
                Command(
                    tool_name="get_app_window_controls_info",
                    parameters={
                        "field_list": ["control_text", "control_type", "control_rect"]
                    },
                    tool_type="data_collection",
                )
            ]
        )

        return result[0].result

    async def _collect_grounding_controls(
        self, context: ProcessingContext
    ) -> List[Any]:
        """收集Grounding控件信息"""
        # 实现grounding控件收集逻辑
        return []

    def _merge_controls(self, controls: List[Any]) -> List[ProcessingContext]:
        """合并控件列表"""
        # 实现控件合并逻辑
        return controls

    def _filter_controls(
        self, controls: List[Any], context: ProcessingContext
    ) -> List[Any]:
        """过滤控件"""
        # 实现控件过滤逻辑
        return controls


class PromptConstructionStrategy(BaseProcessingStrategy):
    """提示构建策略"""

    def __init__(self):
        super().__init__("prompt_construction")

    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        try:
            agent = context.get("agent")

            # 获取各种提示组件
            prompt_components = await self._gather_prompt_components(context)

            # 构建最终提示消息
            prompt_message = agent.message_constructor(**prompt_components)

            return ProcessingResult(
                success=True,
                data={
                    "prompt_message": prompt_message,
                    "prompt_components": prompt_components,
                },
                phase=ProcessingPhase.LLM_INTERACTION,
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"Prompt construction failed: {str(e)}",
                data={},
                phase=ProcessingPhase.LLM_INTERACTION,
            )

    async def _gather_prompt_components(
        self, context: ProcessingContext
    ) -> Dict[str, Any]:
        """收集提示组件"""
        agent = context.get("agent")

        # 获取示例和知识
        experience_results, demonstration_results = agent.demonstration_prompt_helper(
            request=context.get("subtask", "")
        )

        offline_docs, online_docs = agent.external_knowledge_prompt_helper(
            context.get("subtask", ""), 0, 0
        )

        # 获取黑板提示
        blackboard_prompt = []
        if not agent.blackboard.is_empty():
            blackboard_prompt = agent.blackboard.blackboard_to_prompt()

        return {
            "dynamic_examples": experience_results + demonstration_results,
            "dynamic_knowledge": offline_docs + online_docs,
            "image_list": context.get("image_urls", []),
            "control_info": context.get("filtered_controls", []),
            "prev_subtask": context.get("previous_subtasks", []),
            "plan": context.get("prev_plan", []),
            "request": context.get("request", ""),
            "subtask": context.get("subtask", ""),
            "current_application": context.get("application_process_name", ""),
            "host_message": context.get("host_message", []),
            "blackboard_prompt": blackboard_prompt,
            "last_success_actions": context.get("last_success_actions", []),
        }
