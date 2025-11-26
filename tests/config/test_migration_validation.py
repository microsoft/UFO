"""
配置迁移验证脚本
比较新旧配置系统的所有配置项，确保值完全一致
"""

import os
import sys
from typing import Any, Dict, List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath("."))

# 导入新旧配置系统
from ufo.config import Config as LegacyConfig
from config.config_loader import get_ufo_config

console = Console()


class ConfigValidator:
    """配置验证器：比较新旧配置系统"""

    def __init__(self):
        self.mismatches = []
        self.matches = []
        self.legacy_only = []
        self.new_only = []

    def load_configs(self):
        """加载新旧配置"""
        console.print("[yellow]正在加载配置...[/yellow]")

        # 加载旧配置
        try:
            legacy_instance = LegacyConfig.get_instance()
            self.legacy_config = legacy_instance.config_data
            console.print("✓ 旧配置加载成功", style="green")
        except Exception as e:
            console.print(f"✗ 旧配置加载失败: {e}", style="red")
            raise

        # 加载新配置
        try:
            self.new_config = get_ufo_config()
            console.print("✓ 新配置加载成功", style="green")
        except Exception as e:
            console.print(f"✗ 新配置加载失败: {e}", style="red")
            raise

    def get_nested_value(self, config, path: str):
        """获取嵌套配置值"""
        try:
            keys = path.split(".")
            value = config
            for key in keys:
                if isinstance(value, dict):
                    value = value[key]
                else:
                    value = getattr(value, key)
            return value
        except (KeyError, AttributeError):
            return None

    def compare_value(self, path: str, legacy_val, new_val) -> bool:
        """比较两个值是否相等"""
        # 处理None的情况
        if legacy_val is None and new_val is None:
            return True
        if legacy_val is None or new_val is None:
            return False

        # 处理 DynamicConfig 对象（如 ANNOTATION_COLORS）
        if hasattr(new_val, "_data"):
            # new_val 是 DynamicConfig，比较其内部数据
            if isinstance(legacy_val, dict):
                return self.compare_value(path, legacy_val, new_val._data)

        # 特殊处理：API_BASE URL 转换（新配置会自动转换完整URL）
        if (
            path.endswith("API_BASE")
            and isinstance(legacy_val, str)
            and isinstance(new_val, str)
        ):
            # 如果新值是完整 chat/completions URL，旧值可能是基础 URL
            if "chat/completions" in new_val and "chat/completions" not in legacy_val:
                # 检查基础URL是否匹配
                return new_val.startswith(legacy_val.rstrip("/"))

        # 处理列表
        if isinstance(legacy_val, list) and isinstance(new_val, list):
            if len(legacy_val) != len(new_val):
                return False
            return all(a == b for a, b in zip(legacy_val, new_val))

        # 处理字典（递归比较）
        if isinstance(legacy_val, dict) and isinstance(new_val, dict):
            if set(legacy_val.keys()) != set(new_val.keys()):
                return False
            return all(
                self.compare_value(f"{path}.{k}", legacy_val[k], new_val.get(k))
                for k in legacy_val.keys()
            )

        # 简单值比较
        return legacy_val == new_val

    def validate_flat_configs(self):
        """验证顶层配置项"""
        console.print("\n[cyan]验证顶层配置项...[/cyan]")

        # 需要检查的顶层配置项
        flat_configs = [
            "MAX_TOKENS",
            "MAX_RETRY",
            "TEMPERATURE",
            "TOP_P",
            "TIMEOUT",
            "MAX_STEP",
            "MAX_ROUND",
            "SLEEP_TIME",
            "RECTANGLE_TIME",
            "ACTION_SEQUENCE",
            "SHOW_VISUAL_OUTLINE_ON_SCREEN",
            "MAXIMIZE_WINDOW",
            "JSON_PARSING_RETRY",
            "SAFE_GUARD",
            "CONTROL_LIST",
            "HISTORY_KEYS",
            "ANNOTATION_COLORS",
            "HIGHLIGHT_BBOX",
            "ANNOTATION_FONT_SIZE",
            "PRINT_LOG",
            "CONCAT_SCREENSHOT",
            "LOG_LEVEL",
            "INCLUDE_LAST_SCREENSHOT",
            "REQUEST_TIMEOUT",
            "LOG_XML",
            "LOG_TO_MARKDOWN",
            "SCREENSHOT_TO_MEMORY",
            "ASK_QUESTION",
            "USE_CUSTOMIZATION",
            "QA_PAIR_FILE",
            "QA_PAIR_NUM",
            "EVA_SESSION",
            "EVA_ROUND",
            "EVA_ALL_SCREENSHOTS",
            "DEFAULT_PNG_COMPRESS_LEVEL",
            "SAVE_UI_TREE",
            "SAVE_FULL_SCREEN",
            "TASK_STATUS",
            "SAVE_EXPERIENCE",
            "USE_MCP",
            "MCP_FALLBACK_TO_UI",
            "MCP_TOOL_TIMEOUT",
            "MCP_LOG_EXECUTION",
            "CLICK_API",
            "AFTER_CLICK_WAIT",
            "INPUT_TEXT_API",
            "INPUT_TEXT_ENTER",
            "INPUT_TEXT_INTER_KEY_PAUSE",
            "USE_APIS",
            "API_PROMPT",
            "CONTROL_BACKEND",
            "IOU_THRESHOLD_FOR_MERGE",
            "HOSTAGENT_PROMPT",
            "APPAGENT_PROMPT",
            "FOLLOWERAGENT_PROMPT",
            "EVALUATION_PROMPT",
        ]

        for config_key in flat_configs:
            legacy_val = self.legacy_config.get(config_key)

            # 尝试从新配置的不同位置获取
            new_val = None
            if hasattr(self.new_config, config_key):
                new_val = getattr(self.new_config, config_key)
            elif hasattr(self.new_config, "system") and hasattr(
                self.new_config.system, config_key.lower()
            ):
                new_val = getattr(self.new_config.system, config_key.lower())

            if legacy_val is not None:
                if self.compare_value(config_key, legacy_val, new_val):
                    self.matches.append((config_key, legacy_val, new_val))
                else:
                    self.mismatches.append((config_key, legacy_val, new_val))

    def validate_agent_configs(self):
        """验证 Agent 配置"""
        console.print("\n[cyan]验证 Agent 配置...[/cyan]")

        agents = [
            "HOST_AGENT",
            "APP_AGENT",
            "BACKUP_AGENT",
            "EVALUATION_AGENT",
            "OPERATOR",
        ]
        agent_fields = [
            "VISUAL_MODE",
            "REASONING_MODEL",
            "API_TYPE",
            "API_BASE",
            "API_KEY",
            "API_VERSION",
            "API_MODEL",
            "API_DEPLOYMENT_ID",
            "AAD_TENANT_ID",
            "AAD_API_SCOPE",
            "AAD_API_SCOPE_BASE",
        ]

        for agent in agents:
            if agent not in self.legacy_config:
                continue

            for field in agent_fields:
                legacy_val = self.legacy_config[agent].get(field)
                if legacy_val is None:
                    continue

                # 获取新配置中的值 - 尝试多种访问方式
                new_val = None
                agent_lower = agent.lower()

                # 方式 1: 直接从顶层访问（向后兼容）
                if hasattr(self.new_config, agent):
                    agent_obj = getattr(self.new_config, agent)
                    if hasattr(agent_obj, field):
                        new_val = getattr(agent_obj, field)
                    elif hasattr(agent_obj, field.lower()):
                        new_val = getattr(agent_obj, field.lower())

                # 方式 2: 从 agents 模块访问
                if new_val is None and hasattr(self.new_config, agent_lower):
                    agent_obj = getattr(self.new_config, agent_lower)
                    if hasattr(agent_obj, field.lower()):
                        new_val = getattr(agent_obj, field.lower())

                # 方式 3: 字典方式访问
                if new_val is None:
                    try:
                        new_val = self.new_config[agent][field]
                    except (KeyError, TypeError):
                        pass

                full_path = f"{agent}.{field}"
                if self.compare_value(full_path, legacy_val, new_val):
                    self.matches.append((full_path, legacy_val, new_val))
                else:
                    self.mismatches.append((full_path, legacy_val, new_val))

    def validate_rag_configs(self):
        """验证 RAG 配置"""
        console.print("\n[cyan]验证 RAG 配置...[/cyan]")

        rag_configs = [
            "RAG_OFFLINE_DOCS",
            "RAG_OFFLINE_DOCS_RETRIEVED_TOPK",
            "BING_API_KEY",
            "RAG_ONLINE_SEARCH",
            "RAG_ONLINE_SEARCH_TOPK",
            "RAG_ONLINE_RETRIEVED_TOPK",
            "RAG_EXPERIENCE",
            "RAG_EXPERIENCE_RETRIEVED_TOPK",
            "EXPERIENCE_SAVED_PATH",
            "EXPERIENCE_PROMPT",
            "RAG_DEMONSTRATION",
            "RAG_DEMONSTRATION_RETRIEVED_TOPK",
            "RAG_DEMONSTRATION_COMPLETION_N",
            "DEMONSTRATION_SAVED_PATH",
            "DEMONSTRATION_PROMPT",
        ]

        for config_key in rag_configs:
            legacy_val = self.legacy_config.get(config_key)
            if legacy_val is None:
                continue

            # 尝试从 RAG 配置获取
            new_val = None
            if hasattr(self.new_config, "rag"):
                field_name = config_key.lower().replace("rag_", "")
                if hasattr(self.new_config.rag, field_name):
                    new_val = getattr(self.new_config.rag, field_name)

            # 如果不在 RAG 下，尝试顶层
            if new_val is None and hasattr(self.new_config, config_key):
                new_val = getattr(self.new_config, config_key)

            if self.compare_value(config_key, legacy_val, new_val):
                self.matches.append((config_key, legacy_val, new_val))
            else:
                self.mismatches.append((config_key, legacy_val, new_val))

    def validate_omniparser_config(self):
        """验证 Omniparser 配置"""
        console.print("\n[cyan]验证 Omniparser 配置...[/cyan]")

        if "OMNIPARSER" in self.legacy_config:
            legacy_omni = self.legacy_config["OMNIPARSER"]

            for field in [
                "ENDPOINT",
                "BOX_THRESHOLD",
                "IOU_THRESHOLD",
                "USE_PADDLEOCR",
                "IMGSZ",
            ]:
                legacy_val = legacy_omni.get(field)
                if legacy_val is None:
                    continue

                new_val = None
                # 尝试多种访问方式
                if hasattr(self.new_config, "OMNIPARSER"):
                    omni = self.new_config.OMNIPARSER
                    if hasattr(omni, field):
                        new_val = getattr(omni, field)
                    elif hasattr(omni, field.lower()):
                        new_val = getattr(omni, field.lower())

                if new_val is None and hasattr(self.new_config, "system"):
                    if hasattr(self.new_config.system, "OMNIPARSER"):
                        omni = self.new_config.system.OMNIPARSER
                        if hasattr(omni, field):
                            new_val = getattr(omni, field)
                        elif hasattr(omni, field.lower()):
                            new_val = getattr(omni, field.lower())
                    elif hasattr(self.new_config.system, "omniparser"):
                        omni = self.new_config.system.omniparser
                        if hasattr(omni, field.lower()):
                            new_val = getattr(omni, field.lower())

                full_path = f"OMNIPARSER.{field}"
                if self.compare_value(full_path, legacy_val, new_val):
                    self.matches.append((full_path, legacy_val, new_val))
                else:
                    self.mismatches.append((full_path, legacy_val, new_val))

    def validate_third_party_configs(self):
        """验证第三方 Agent 配置"""
        console.print("\n[cyan]验证第三方 Agent 配置...[/cyan]")

        if "ENABLED_THIRD_PARTY_AGENTS" in self.legacy_config:
            legacy_val = self.legacy_config["ENABLED_THIRD_PARTY_AGENTS"]
            new_val = None

            # 尝试多种访问方式
            if hasattr(self.new_config, "ENABLED_THIRD_PARTY_AGENTS"):
                new_val = self.new_config.ENABLED_THIRD_PARTY_AGENTS
            elif hasattr(self.new_config, "third_party"):
                if hasattr(self.new_config.third_party, "ENABLED_THIRD_PARTY_AGENTS"):
                    new_val = self.new_config.third_party.ENABLED_THIRD_PARTY_AGENTS
                elif hasattr(self.new_config.third_party, "enabled_third_party_agents"):
                    new_val = self.new_config.third_party.enabled_third_party_agents
            elif hasattr(self.new_config, "system"):
                if hasattr(self.new_config.system, "ENABLED_THIRD_PARTY_AGENTS"):
                    new_val = self.new_config.system.ENABLED_THIRD_PARTY_AGENTS
                elif hasattr(self.new_config.system, "enabled_third_party_agents"):
                    new_val = self.new_config.system.enabled_third_party_agents

            if self.compare_value("ENABLED_THIRD_PARTY_AGENTS", legacy_val, new_val):
                self.matches.append(("ENABLED_THIRD_PARTY_AGENTS", legacy_val, new_val))
            else:
                self.mismatches.append(
                    ("ENABLED_THIRD_PARTY_AGENTS", legacy_val, new_val)
                )

    def generate_report(self):
        """生成验证报告"""
        console.print("\n" + "=" * 80)
        console.print(
            Panel.fit("[bold green]配置迁移验证报告[/bold green]", border_style="green")
        )

        # 统计信息
        total = len(self.matches) + len(self.mismatches)
        match_rate = (len(self.matches) / total * 100) if total > 0 else 0

        stats_table = Table(title="验证统计", box=box.ROUNDED)
        stats_table.add_column("指标", style="cyan")
        stats_table.add_column("数量", style="yellow")
        stats_table.add_column("百分比", style="green")

        stats_table.add_row("匹配项", str(len(self.matches)), f"{match_rate:.2f}%")
        stats_table.add_row(
            "不匹配项", str(len(self.mismatches)), f"{100-match_rate:.2f}%"
        )
        stats_table.add_row("总计", str(total), "100%")

        console.print(stats_table)

        # 不匹配项详情
        if self.mismatches:
            console.print("\n[red]⚠️  发现不匹配的配置项：[/red]")

            mismatch_table = Table(title="不匹配配置详情", box=box.ROUNDED)
            mismatch_table.add_column("配置路径", style="cyan", no_wrap=True)
            mismatch_table.add_column("旧值", style="yellow")
            mismatch_table.add_column("新值", style="magenta")

            for path, legacy_val, new_val in self.mismatches[:20]:  # 只显示前20个
                legacy_str = str(legacy_val)[:50] if legacy_val is not None else "None"
                new_str = str(new_val)[:50] if new_val is not None else "None"
                mismatch_table.add_row(path, legacy_str, new_str)

            console.print(mismatch_table)

            if len(self.mismatches) > 20:
                console.print(f"\n... 还有 {len(self.mismatches) - 20} 项不匹配")
        else:
            console.print("\n[bold green]✅ 所有配置项完全匹配！[/bold green]")

        # 成功率判断
        console.print("\n" + "=" * 80)
        if match_rate >= 95:
            console.print("[bold green]✅ 验证通过！配置迁移成功率 >= 95%[/bold green]")
            return True
        else:
            console.print(
                f"[bold red]❌ 验证失败！配置迁移成功率: {match_rate:.2f}% < 95%[/bold red]"
            )
            return False

    def run(self):
        """执行完整验证流程"""
        try:
            self.load_configs()
            self.validate_flat_configs()
            self.validate_agent_configs()
            self.validate_rag_configs()
            self.validate_omniparser_config()
            self.validate_third_party_configs()

            success = self.generate_report()
            return success
        except Exception as e:
            console.print(f"\n[bold red]验证过程出错: {e}[/bold red]")
            import traceback

            console.print(traceback.format_exc())
            return False


if __name__ == "__main__":
    console.print(
        Panel.fit(
            "[bold cyan]UFO³ 配置迁移验证工具[/bold cyan]\n"
            "比较新旧配置系统，确保配置值完全一致",
            border_style="cyan",
        )
    )

    validator = ConfigValidator()
    success = validator.run()

    sys.exit(0 if success else 1)
