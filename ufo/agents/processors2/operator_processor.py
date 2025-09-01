from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict
from ufo.agents.processors2.core.processor_framework import (
    ProcessorTemplate,
    ProcessingPhase,
)
from ufo.agents.processors2.middleware.common_middleware import (
    TimingMiddleware,
    LoggingMiddleware,
    MemoryMiddleware,
    ExceptionHandlingMiddleware,
)
from ufo.agents.processors.operator_processor import (
    OperatorAdditionalMemory,
    OpenAIOperatorRequestLog,
)
from ufo.agents.processors.actions import ActionCommandInfo
from ufo.contracts.contracts import Command
from ufo.module.context import Context, ContextNames
from ufo import utils
import json


class OperatorProcessorV2(ProcessorTemplate):
    """重构后的Operator Agent处理器"""

    def __init__(self, agent, context: Context, scaler: Optional[List[int]] = None):
        self.app_agent = agent
        self.host_agent = agent.host if hasattr(agent, "host") else None
        self.scaler = scaler

        # 初始化处理器状态
        self._image_url = ""
        self.width = None
        self.height = None
        self._operation = None
        self._args = {}
        self._response_json = {}

        # 如果没有host agent，则将subtask设置为用户请求
        if not self.host_agent:
            context.set("subtask", context.get("request", ""))

        super().__init__(agent, context)

    def _setup_strategies(self) -> None:
        """配置Operator Agent特定的处理策略"""

        self.strategies[ProcessingPhase.DATA_COLLECTION] = (
            OperatorDataCollectionStrategy(self.scaler)
        )
        self.strategies[ProcessingPhase.LLM_INTERACTION] = OperatorLLMStrategy()
        self.strategies[ProcessingPhase.ACTION_EXECUTION] = OperatorActionStrategy()
        self.strategies[ProcessingPhase.MEMORY_UPDATE] = OperatorMemoryStrategy()

    def _setup_middleware(self) -> None:
        """设置中间件链"""
        self.middleware_chain = [
            TimingMiddleware(),
            OperatorLoggingMiddleware(),
            ExceptionHandlingMiddleware(),
            MemoryMiddleware(),
        ]


class OperatorDataCollectionStrategy:
    """Operator Agent数据收集策略"""

    def __init__(self, scaler: Optional[List[int]] = None):
        self.scaler = scaler

    async def execute(self, context: Any):
        """执行数据收集"""
        try:
            # 捕获截图
            screenshot_data = await self._capture_screenshot(context)

            # 获取工具信息
            tools_info = self._get_tools_info(screenshot_data)

            from ufo.agents.processors2.core.processor_framework import (
                ProcessingResult,
                ProcessingPhase,
            )

            return ProcessingResult(
                success=True,
                data={
                    "image_url": screenshot_data["image_url"],
                    "screenshot_path": screenshot_data["path"],
                    "width": screenshot_data["width"],
                    "height": screenshot_data["height"],
                    "tools_info": tools_info,
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
                error=f"Operator data collection failed: {str(e)}",
                data={},
                phase=ProcessingPhase.DATA_COLLECTION,
            )

    async def _capture_screenshot(self, context: Any) -> Dict[str, Any]:
        """捕获截图"""
        log_path = context.get("log_path", "")
        session_step = context.get("session_step", 0)
        command_dispatcher = context.get("command_dispatcher")

        screenshot_save_path = f"{log_path}action_step{session_step}.png"

        # 根据模式选择截图命令
        mode = context.get("mode", "operator")
        if mode == "normal_operator":
            command = Command(
                tool_name="capture_window_screenshot",
                parameters={},
                tool_type="data_collection",
            )
        else:  # operator模式
            command = Command(
                tool_name="capture_desktop_screenshot",
                parameters={"all_screens": False},
                tool_type="data_collection",
            )

        result = await command_dispatcher.execute_commands([command])
        clean_screenshot_url = result[0].result

        # 保存截图并获取尺寸
        screenshot = utils.save_image_string(clean_screenshot_url, screenshot_save_path)
        width, height = screenshot.size

        return {
            "image_url": clean_screenshot_url,
            "path": screenshot_save_path,
            "width": width,
            "height": height,
        }

    def _get_tools_info(self, screenshot_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取工具信息"""
        return [
            {
                "type": "computer-preview",
                "display_width": screenshot_data["width"],
                "display_height": screenshot_data["height"],
                "environment": "windows",
            }
        ]


class OperatorLLMStrategy:
    """Operator Agent LLM交互策略"""

    async def execute(self, context: Any):
        """执行LLM交互"""
        try:
            agent = context.get("agent")

            # 构建提示消息
            prompt_message = self._build_prompt_message(context)

            # 记录请求日志
            self._log_request(context, prompt_message)

            # 获取LLM响应
            response, cost = agent.get_response(
                prompt_message, "OPERATOR", use_backup_engine=False
            )

            # 解析响应
            parsed_response = self._parse_response(response, context)

            from ufo.agents.processors2.core.processor_framework import (
                ProcessingResult,
                ProcessingPhase,
            )

            return ProcessingResult(
                success=True,
                data={
                    "response": response,
                    "parsed_response": parsed_response,
                    "cost": cost,
                    "prompt_message": prompt_message,
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
                error=f"Operator LLM interaction failed: {str(e)}",
                data={},
                phase=ProcessingPhase.LLM_INTERACTION,
            )

    def _build_prompt_message(self, context: Any) -> Dict[str, Any]:
        """构建提示消息"""
        agent = context.get("agent")
        is_first_step = agent.step == 0

        return agent.message_constructor(
            subtask=context.get("subtask", ""),
            tools=context.get("tools_info", []),
            image=context.get("image_url", ""),
            host_message=context.get("host_message", []),
            response_id=agent.response_id,
            previous_computer_id=agent.previous_computer_id,
            acknowledged_safety_checks=agent.pending_safety_checks,
            is_first_step=is_first_step,
        )

    def _log_request(self, context: Any, prompt_message: Dict[str, Any]) -> None:
        """记录请求日志"""
        agent = context.get("agent")
        is_first_step = agent.step == 0

        request_data = OpenAIOperatorRequestLog(
            step=context.get("session_step", 0),
            image_list=context.get("image_url", ""),
            subtask=context.get("subtask", ""),
            current_application=context.get("application_process_name", ""),
            response_id=agent.response_id,
            is_first_step=is_first_step,
            acknowledged_safety_checks=agent.pending_safety_checks,
            host_message=context.get("host_message", []),
            prompt=prompt_message,
        )

        request_log_str = json.dumps(asdict(request_data), ensure_ascii=False)
        request_logger = context.get("request_logger")
        if request_logger:
            request_logger.debug(request_log_str)

    def _parse_response(self, response: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """解析响应"""
        agent = context.get("agent")

        # 获取响应ID
        agent.response_id = response.get("id", "")

        # 解析输出列表
        model_output_list = response.get("output", [])
        response_json = {}

        thought = ""
        message = ""
        operation = None
        args = {}
        status = "CONTINUE"

        for output in model_output_list:
            output_type = output.get("type", "")

            if output_type == "computer_call":
                computer_call_output = self._parse_computer_call_output(output)
                operation = computer_call_output["operation"]
                args = computer_call_output["args"]

                # 添加scaler到参数中
                scaler = context.get("scaler")
                if scaler is not None:
                    args["scaler"] = scaler

                agent.previous_computer_id = computer_call_output["call_id"]
                agent.pending_safety_checks = computer_call_output[
                    "pending_safety_checks"
                ]
                response_json.update(computer_call_output)
                status = "CONTINUE"

            elif output_type == "reasoning":
                reasoning_message = self._parse_reasoning_output(output)
                thought += reasoning_message
                response_json.update({"thought": reasoning_message})

            elif output_type == "message":
                agent_message = self._parse_message_output(output)
                message += agent_message
                agent.message = message
                response_json.update({"message": message})
                status = "FINISH"

            else:
                status = "FINISH"
                print(f"Unknown output type: {output_type}")

        # 更新上下文
        context.update(
            {
                "operation": operation,
                "args": args,
                "status": status,
                "response_json": response_json,
            }
        )

        return response_json

    def _parse_computer_call_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """解析计算机调用输出"""
        computer_call_output = {}

        computer_call_output["call_id"] = output.get("call_id", "")
        action_dict = output.get("action", {})
        computer_call_output["operation"] = action_dict.get("type", "")
        computer_call_output["args"] = {
            k: v for k, v in action_dict.items() if k != "type"
        }
        computer_call_output["pending_safety_checks"] = output.get(
            "pending_safety_checks", []
        )

        return computer_call_output

    def _parse_reasoning_output(self, output: Dict[str, Any]) -> str:
        """解析推理输出"""
        reasoning_output = output.get("summary", [])
        return "\n".join([item.get("text", "") for item in reasoning_output])

    def _parse_message_output(self, output: Dict[str, Any]) -> str:
        """解析消息输出"""
        message_output = output.get("content", [])
        if len(message_output) > 0:
            return message_output[-1].get("text", "")
        else:
            return ""


class OperatorActionStrategy:
    """Operator Agent动作执行策略"""

    async def execute(self, context: Any):
        """执行动作"""
        try:
            operation = context.get("operation")
            args = context.get("args", {})
            status = context.get("status", "CONTINUE")

            if not operation:
                from ufo.agents.processors2.core.processor_framework import (
                    ProcessingResult,
                    ProcessingPhase,
                )

                return ProcessingResult(
                    success=True,
                    data={"message": "No operation to execute"},
                    phase=ProcessingPhase.ACTION_EXECUTION,
                )

            # 创建动作信息
            action = ActionCommandInfo(
                function=operation,
                arguments=args,
                status=status,
            )

            # 执行命令
            command_dispatcher = context.get("command_dispatcher")
            result = await command_dispatcher.execute_commands(
                [
                    Command(
                        tool_name=action.function,
                        parameters=action.arguments,
                        tool_type="action",
                    )
                ]
            )

            # 可选：捕获控件截图
            # point_list = action.get_operation_point_list()
            # self._capture_control_screenshot(context, point_list)

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
                error=f"Operator action execution failed: {str(e)}",
                data={},
                phase=ProcessingPhase.ACTION_EXECUTION,
            )

    def _capture_control_screenshot(
        self, context: Any, point_list: Optional[List[Tuple[int]]]
    ) -> None:
        """捕获控件截图"""
        if not point_list:
            return

        log_path = context.get("log_path", "")
        session_step = context.get("session_step", 0)
        screenshot_path = context.get("screenshot_path", "")

        control_screenshot_save_path = (
            f"{log_path}action_step{session_step}_selected_controls.png"
        )

        # 这里需要根据实际的photographer实现来调用
        # photographer.capture_app_window_screenshot_with_point_from_path(
        #     point_list=point_list,
        #     save_path=control_screenshot_save_path,
        #     background_screenshot_path=screenshot_path,
        # )


class OperatorMemoryStrategy:
    """Operator Agent内存更新策略"""

    async def execute(self, context: Any):
        """更新内存"""
        try:
            agent = context.get("agent")
            action = context.get("action")
            response_json = context.get("response_json", {})

            # 获取应用根名称
            app_root = context.get("app_root", "")

            # 计算动作类型
            action_type = []
            if action and hasattr(agent, "Puppeteer"):
                action_type = [agent.Puppeteer.get_command_types(action.function)]

            # 获取成功动作
            all_previous_success_actions = self._get_all_success_actions(context)

            actions_list = [action] if action else []
            action_success = self._get_action_success(
                actions_list, all_previous_success_actions
            )

            # 创建额外内存数据
            additional_memory = OperatorAdditionalMemory(
                Step=context.get("session_step", 0),
                RoundStep=context.get("round_step", 0),
                AgentStep=agent.step,
                Round=context.get("round_num", 0),
                Subtask=context.get("subtask", ""),
                SubtaskIndex=context.get("round_subtask_amount", 0),
                FunctionCall=[action.function] if action else [],
                Action=[asdict(action)] if action else [],
                ActionSuccess=action_success,
                ActionType=action_type,
                Request=context.get("request", ""),
                Agent="AppAgent",
                AgentName=agent.name,
                Application=app_root,
                Cost=context.get("cost", 0.0),
                Results="",  # 需要根据实际结果填充
                error="",
                time_cost=context.get("time_cost", {}),
                ControlLog={},  # 需要根据实际控件日志填充
                Comment=getattr(agent, "message", ""),
                UserConfirm=self._get_user_confirm_status(context),
            )

            from ufo.agents.processors2.core.processor_framework import (
                ProcessingResult,
                ProcessingPhase,
            )

            return ProcessingResult(
                success=True,
                data={
                    "additional_memory": additional_memory,
                    "response_json": response_json,
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
                error=f"Operator memory update failed: {str(e)}",
                data={},
                phase=ProcessingPhase.MEMORY_UPDATE,
            )

    def _get_all_success_actions(self, context: Any) -> List[Dict[str, Any]]:
        """获取所有成功动作"""
        agent = context.get("agent")

        if hasattr(agent, "memory") and agent.memory.length > 0:
            success_action_memory = agent.memory.filter_memory_from_keys(
                ["ActionSuccess"]
            )
            success_actions = []
            for success_action in success_action_memory:
                success_actions += success_action.get("ActionSuccess", [])
            return success_actions

        return []

    def _get_action_success(
        self, actions_list: List, previous_actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """获取成功动作列表"""
        # 这里应该根据实际的actions对象来实现
        # 简化实现
        return []

    def _get_user_confirm_status(self, context: Any) -> Optional[str]:
        """获取用户确认状态"""
        status = context.get("status", "")
        is_resumed = context.get("_is_resumed", False)

        if status.upper() == "CONFIRM":
            return "Yes" if is_resumed else "No"
        return None


class OperatorLoggingMiddleware(LoggingMiddleware):
    """Operator Agent特定的日志中间件"""

    async def before_process(self, processor, context) -> None:
        round_num = context.get("round_num", 0)
        round_step = context.get("round_step", 0)
        subtask = context.get("subtask", "")
        application = context.get("application_process_name", "")

        from ufo import utils

        utils.print_with_color(
            f"Round {round_num + 1}, Step {round_step + 1}, OperatorAgent: "
            f"Completing the subtask [{subtask}] on application [{application}].",
            "magenta",
        )

        processor.logger.info(
            f"Round {round_num + 1}, Step {round_step + 1}, OperatorAgent: "
            f"Processing subtask [{subtask}]"
        )

    async def after_process(self, processor, result) -> None:
        if result.success:
            response_json = result.data.get("response_json", {})
            if hasattr(processor, "app_agent"):
                processor.app_agent.print_response(response_json)
            processor.logger.info("Operator processing completed successfully")
        else:
            processor.logger.error(f"Operator processing failed: {result.error}")
