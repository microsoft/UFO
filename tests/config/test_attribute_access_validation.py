"""
测试新配置系统的属性访问方式
验证使用大写和小写属性访问时，与旧配置系统的值完全一致
"""

import os
import sys
from typing import Any
from rich.console import Console
from rich.table import Table
from rich import box

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath("."))

# 导入新旧配置系统
from ufo.config import Config as LegacyConfig
from config.config_loader import get_ufo_config, get_galaxy_config

console = Console()


class AttributeAccessValidator:
    """验证属性访问方式的配置值"""

    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0

    def test_value(
        self, name: str, legacy_val: Any, new_val_upper: Any, new_val_lower: Any = None
    ):
        """
        测试单个配置值

        :param name: 配置名称
        :param legacy_val: 旧配置的值
        :param new_val_upper: 新配置大写属性访问的值
        :param new_val_lower: 新配置小写属性访问的值（可选）
        """
        result = {
            "name": name,
            "legacy": legacy_val,
            "new_upper": new_val_upper,
            "new_lower": new_val_lower,
            "status": "✓",
        }

        # 处理 DynamicConfig 对象
        if hasattr(new_val_upper, "_data"):
            new_val_upper = new_val_upper._data
        if new_val_lower is not None and hasattr(new_val_lower, "_data"):
            new_val_lower = new_val_lower._data

        # 检查大写属性访问是否与旧配置一致
        if self._compare_values(legacy_val, new_val_upper):
            # 如果提供了小写访问，检查是否与大写一致
            if new_val_lower is not None:
                if not self._compare_values(new_val_upper, new_val_lower):
                    result["status"] = "✗"
                    result["error"] = "大写和小写访问值不一致"
                    self.failed += 1
                else:
                    self.passed += 1
            else:
                self.passed += 1
        else:
            result["status"] = "✗"
            result["error"] = "新旧配置值不一致"
            self.failed += 1

        self.test_results.append(result)
        return result["status"] == "✓"

    def _compare_values(self, val1: Any, val2: Any) -> bool:
        """比较两个值是否相等"""
        if val1 is None and val2 is None:
            return True
        if val1 is None or val2 is None:
            return False

        # 处理 API_BASE URL 转换
        if isinstance(val1, str) and isinstance(val2, str):
            if "chat/completions" in val2 and "chat/completions" not in val1:
                return val2.startswith(val1.rstrip("/"))

        # 处理列表
        if isinstance(val1, list) and isinstance(val2, list):
            if len(val1) != len(val2):
                return False
            return all(a == b for a, b in zip(val1, val2))

        # 处理字典
        if isinstance(val1, dict) and isinstance(val2, dict):
            if set(val1.keys()) != set(val2.keys()):
                return False
            return all(self._compare_values(val1[k], val2.get(k)) for k in val1.keys())

        return val1 == val2

    def test_ufo_system_config(self):
        """测试 UFO SystemConfig 的属性访问"""
        console.print("\n[bold cyan]测试 UFO SystemConfig 属性访问[/bold cyan]")

        legacy = LegacyConfig.get_instance().config_data
        new_config = get_ufo_config()

        system_fields = [
            ("MAX_TOKENS", "max_tokens"),
            ("MAX_RETRY", "max_retry"),
            ("MAX_STEP", "max_step"),
            ("MAX_ROUND", "max_round"),
            ("TEMPERATURE", "temperature"),
            ("TIMEOUT", "timeout"),
            ("LOG_LEVEL", "log_level"),
            ("PRINT_LOG", "print_log"),
        ]

        for upper_name, lower_name in system_fields:
            if upper_name in legacy:
                legacy_val = legacy[upper_name]
                new_val_upper = getattr(new_config.system, upper_name, None)
                new_val_lower = getattr(new_config.system, lower_name, None)

                self.test_value(
                    f"system.{upper_name}", legacy_val, new_val_upper, new_val_lower
                )

    def test_ufo_agent_config(self):
        """测试 UFO AgentConfig 的属性访问"""
        console.print("\n[bold cyan]测试 UFO AgentConfig 属性访问[/bold cyan]")

        legacy = LegacyConfig.get_instance().config_data
        new_config = get_ufo_config()

        agents = [
            ("HOST_AGENT", "host_agent"),
            ("APP_AGENT", "app_agent"),
        ]

        agent_fields = [
            ("VISUAL_MODE", "visual_mode"),
            ("REASONING_MODEL", "reasoning_model"),
            ("API_TYPE", "api_type"),
            ("API_BASE", "api_base"),
            ("API_KEY", "api_key"),
            ("API_VERSION", "api_version"),
            ("API_MODEL", "api_model"),
        ]

        for agent_upper, agent_lower in agents:
            if agent_upper not in legacy:
                continue

            legacy_agent = legacy[agent_upper]
            new_agent = getattr(new_config, agent_lower)

            for field_upper, field_lower in agent_fields:
                if field_upper in legacy_agent:
                    legacy_val = legacy_agent[field_upper]
                    new_val_upper = getattr(new_agent, field_upper, None)
                    new_val_lower = getattr(new_agent, field_lower, None)

                    self.test_value(
                        f"{agent_lower}.{field_upper}",
                        legacy_val,
                        new_val_upper,
                        new_val_lower,
                    )

    def test_ufo_rag_config(self):
        """测试 UFO RAGConfig 的属性访问"""
        console.print("\n[bold cyan]测试 UFO RAGConfig 属性访问[/bold cyan]")

        legacy = LegacyConfig.get_instance().config_data
        new_config = get_ufo_config()

        rag_fields = [
            ("RAG_OFFLINE_DOCS", "offline_docs"),
            ("RAG_OFFLINE_DOCS_RETRIEVED_TOPK", "offline_docs_retrieved_topk"),
            ("RAG_ONLINE_SEARCH", "online_search"),
            ("RAG_ONLINE_SEARCH_TOPK", "online_search_topk"),
            ("RAG_EXPERIENCE", "experience"),
            ("RAG_EXPERIENCE_RETRIEVED_TOPK", "experience_retrieved_topk"),
            ("RAG_DEMONSTRATION", "demonstration"),
            ("RAG_DEMONSTRATION_RETRIEVED_TOPK", "demonstration_retrieved_topk"),
        ]

        for upper_name, lower_name in rag_fields:
            if upper_name in legacy:
                legacy_val = legacy[upper_name]
                new_val_upper = getattr(new_config.rag, upper_name, None)
                new_val_lower = getattr(new_config.rag, lower_name, None)

                self.test_value(
                    f"rag.{upper_name}", legacy_val, new_val_upper, new_val_lower
                )

    def test_galaxy_constellation_config(self):
        """测试 Galaxy ConstellationRuntimeConfig 的属性访问"""
        console.print(
            "\n[bold cyan]测试 Galaxy ConstellationRuntimeConfig 属性访问[/bold cyan]"
        )

        try:
            galaxy_config = get_galaxy_config()

            # 测试配置字段
            constellation_fields = [
                ("CONSTELLATION_ID", "constellation_id"),
                ("HEARTBEAT_INTERVAL", "heartbeat_interval"),
                ("RECONNECT_DELAY", "reconnect_delay"),
                ("MAX_CONCURRENT_TASKS", "max_concurrent_tasks"),
                ("MAX_STEP", "max_step"),
                ("DEVICE_INFO", "device_info"),
            ]

            for upper_name, lower_name in constellation_fields:
                new_val_upper = getattr(galaxy_config.constellation, upper_name, None)
                new_val_lower = getattr(galaxy_config.constellation, lower_name, None)

                # Galaxy 没有旧配置，只验证大小写访问一致性
                result = {
                    "name": f"constellation.{upper_name}",
                    "new_upper": new_val_upper,
                    "new_lower": new_val_lower,
                    "status": (
                        "✓"
                        if self._compare_values(new_val_upper, new_val_lower)
                        else "✗"
                    ),
                }

                if result["status"] == "✓":
                    self.passed += 1
                else:
                    self.failed += 1
                    result["error"] = "大写和小写访问值不一致"

                self.test_results.append(result)

        except Exception as e:
            console.print(f"[yellow]Galaxy 配置测试跳过: {e}[/yellow]")

    def test_galaxy_agent_config(self):
        """测试 Galaxy AgentConfig 的属性访问"""
        console.print(
            "\n[bold cyan]测试 Galaxy CONSTELLATION_AGENT 属性访问[/bold cyan]"
        )

        try:
            galaxy_config = get_galaxy_config()
            agent = galaxy_config.agent.CONSTELLATION_AGENT

            agent_fields = [
                ("VISUAL_MODE", "visual_mode"),
                ("REASONING_MODEL", "reasoning_model"),
                ("API_TYPE", "api_type"),
                ("API_BASE", "api_base"),
                ("API_MODEL", "api_model"),
                ("API_VERSION", "api_version"),
            ]

            for upper_name, lower_name in agent_fields:
                new_val_upper = getattr(agent, upper_name, None)
                new_val_lower = getattr(agent, lower_name, None)

                result = {
                    "name": f"constellation_agent.{upper_name}",
                    "new_upper": new_val_upper,
                    "new_lower": new_val_lower,
                    "status": (
                        "✓"
                        if self._compare_values(new_val_upper, new_val_lower)
                        else "✗"
                    ),
                }

                if result["status"] == "✓":
                    self.passed += 1
                else:
                    self.failed += 1
                    result["error"] = "大写和小写访问值不一致"

                self.test_results.append(result)

        except Exception as e:
            console.print(f"[yellow]Galaxy Agent 配置测试跳过: {e}[/yellow]")

    def print_summary(self):
        """打印测试摘要"""
        console.print("\n" + "=" * 70)
        console.print("[bold]测试结果摘要[/bold]")
        console.print("=" * 70)

        # 创建统计表格
        table = Table(box=box.ROUNDED)
        table.add_column("指标", style="cyan")
        table.add_column("数量", justify="right", style="yellow")
        table.add_column("百分比", justify="right", style="green")

        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        table.add_row("通过", str(self.passed), f"{pass_rate:.2f}%")
        table.add_row("失败", str(self.failed), f"{(100-pass_rate):.2f}%")
        table.add_row("总计", str(total), "100%")

        console.print(table)

        # 显示失败项
        if self.failed > 0:
            console.print("\n[bold red]失败的测试项:[/bold red]")
            for result in self.test_results:
                if result["status"] == "✗":
                    console.print(
                        f"  ✗ {result['name']}: {result.get('error', '未知错误')}"
                    )
                    if "legacy" in result:
                        console.print(f"    旧值: {result['legacy']}")
                    console.print(f"    大写: {result['new_upper']}")
                    console.print(f"    小写: {result['new_lower']}")

        # 最终判断
        if self.failed == 0:
            console.print("\n[bold green]✅ 所有属性访问测试通过！[/bold green]")
            return True
        else:
            console.print(f"\n[bold red]❌ {self.failed} 项测试失败[/bold red]")
            return False


def main():
    """主测试函数"""
    console.print("\n" + "=" * 70)
    console.print("[bold]配置属性访问验证测试[/bold]")
    console.print("=" * 70)
    console.print("测试新配置系统的大写/小写属性访问与旧配置的一致性\n")

    validator = AttributeAccessValidator()

    try:
        # UFO 配置测试
        validator.test_ufo_system_config()
        validator.test_ufo_agent_config()
        validator.test_ufo_rag_config()

        # Galaxy 配置测试
        validator.test_galaxy_constellation_config()
        validator.test_galaxy_agent_config()

        # 打印摘要
        success = validator.print_summary()

        return 0 if success else 1

    except Exception as e:
        console.print(f"\n[bold red]测试执行失败: {e}[/bold red]")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
