"""
Strategy Dependency Management System

This module provides dependency declaration and validation for processing strategies
to ensure proper data flow and early detection of dependency issues.
"""

import logging
from dataclasses import dataclass, field
from typing import Set, List, Dict, Any, Optional

from ufo.agents.processors.context.processing_context import (
    ProcessingPhase,
    ProcessingContext,
)


@dataclass
class StrategyDependency:
    """
    Strategy dependency declaration.

    This class defines what fields a strategy requires as input,
    what it provides as output, and which phases it depends on.
    """

    required_fields: Set[str] = field(default_factory=set)
    """Fields that must be available before the strategy can execute."""

    optional_fields: Set[str] = field(default_factory=set)
    """Fields that are helpful but not required for strategy execution."""

    provides_fields: Set[str] = field(default_factory=set)
    """Fields that the strategy promises to provide in its result."""

    depends_on_phases: Set[ProcessingPhase] = field(default_factory=set)
    """Processing phases that must complete successfully before this strategy runs."""


class DependencyValidationError(Exception):
    """Exception raised when strategy dependencies are not met."""

    def __init__(
        self, message: str, missing_fields: List[str] = None, strategy_name: str = None
    ):
        super().__init__(message)
        self.missing_fields = missing_fields or []
        self.strategy_name = strategy_name


class StrategyDependencyValidator:
    """
    Validator for strategy dependencies.

    This class provides methods to validate strategy dependencies both
    at initialization time and during execution.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def validate_execution_dependencies(
        self,
        strategy_name: str,
        dependencies: StrategyDependency,
        context: ProcessingContext,
    ) -> List[str]:
        """
        Validate that all required dependencies are available in the context.

        :param strategy_name: Name of the strategy being validated
        :param dependencies: Strategy dependency declaration
        :param context: Processing context to check
        :return: List of missing required fields
        """
        missing_fields = []

        # Check required fields
        for field in dependencies.required_fields:
            value = context.get_local(field)
            if value is None:
                missing_fields.append(field)

        # Log optional fields that are missing
        missing_optional = []
        for field in dependencies.optional_fields:
            value = context.get_local(field)
            if value is None:
                missing_optional.append(field)

        if missing_optional:
            self.logger.debug(
                f"Strategy {strategy_name} has missing optional fields: {missing_optional}"
            )

        # Check phase dependencies
        missing_phases = []
        for phase in dependencies.depends_on_phases:
            if not context.has_phase_completed(phase):
                missing_phases.append(phase.value)

        if missing_phases:
            missing_fields.extend([f"phase_{phase}" for phase in missing_phases])

        return missing_fields

    def validate_strategy_chain(
        self, strategies: Dict[ProcessingPhase, Any]
    ) -> Dict[str, Any]:
        """
        Validate the complete strategy chain for dependency consistency.

        :param strategies: Dictionary mapping phases to strategies
        :return: Validation report with issues and dependency graph
        """
        report = {
            "valid": True,
            "issues": [],
            "dependency_graph": {},
            "field_flow": {},
            "phase_order": [],
        }

        provided_fields = set()
        completed_phases = set()

        # Process strategies in phase order
        for phase in ProcessingPhase:
            if phase in strategies:
                strategy = strategies[phase]
                report["phase_order"].append(phase.value)

                # Get strategy dependencies
                if hasattr(strategy, "dependencies"):
                    deps = strategy.dependencies
                else:
                    self.logger.warning(
                        f"Strategy {strategy.__class__.__name__} has no dependency declaration"
                    )
                    continue

                strategy_name = getattr(strategy, "name", strategy.__class__.__name__)

                # Record dependency graph
                report["dependency_graph"][phase.value] = {
                    "strategy": strategy_name,
                    "requires": list(deps.required_fields),
                    "provides": list(deps.provides_fields),
                    "optional": list(deps.optional_fields),
                    "depends_on_phases": [p.value for p in deps.depends_on_phases],
                }

                # Check missing required fields
                missing_required = deps.required_fields - provided_fields
                if missing_required:
                    report["valid"] = False
                    report["issues"].append(
                        {
                            "phase": phase.value,
                            "strategy": strategy_name,
                            "type": "missing_required_fields",
                            "fields": list(missing_required),
                        }
                    )

                # Check phase dependencies
                missing_phases = deps.depends_on_phases - completed_phases
                if missing_phases:
                    report["valid"] = False
                    report["issues"].append(
                        {
                            "phase": phase.value,
                            "strategy": strategy_name,
                            "type": "missing_required_phases",
                            "phases": [p.value for p in missing_phases],
                        }
                    )

                # Record field flow
                for field in deps.required_fields | deps.optional_fields:
                    if field not in report["field_flow"]:
                        report["field_flow"][field] = {"providers": [], "consumers": []}
                    report["field_flow"][field]["consumers"].append(
                        {"phase": phase.value, "strategy": strategy_name}
                    )

                for field in deps.provides_fields:
                    if field not in report["field_flow"]:
                        report["field_flow"][field] = {"providers": [], "consumers": []}
                    report["field_flow"][field]["providers"].append(
                        {"phase": phase.value, "strategy": strategy_name}
                    )

                # Update provided fields and completed phases
                provided_fields.update(deps.provides_fields)
                completed_phases.add(phase)

        return report

    def print_dependency_report(self, report: Dict[str, Any]) -> None:
        """
        Print a detailed dependency validation report.

        :param report: Report from validate_strategy_chain
        """
        print("\n" + "=" * 60)
        print("策略依赖关系验证报告")
        print("=" * 60)

        if report["valid"]:
            print("✅ 所有策略依赖关系都满足")
        else:
            print("❌ 发现依赖问题:")
            for issue in report["issues"]:
                if issue["type"] == "missing_required_fields":
                    print(
                        f"  - {issue['phase']}: {issue['strategy']} 缺少必需字段: {issue['fields']}"
                    )
                elif issue["type"] == "missing_required_phases":
                    print(
                        f"  - {issue['phase']}: {issue['strategy']} 缺少必需阶段: {issue['phases']}"
                    )

        print(f"\n处理阶段顺序: {' -> '.join(report['phase_order'])}")

        print("\n字段流向分析:")
        for field, flow in report["field_flow"].items():
            providers = [f"{p['phase']}({p['strategy']})" for p in flow["providers"]]
            consumers = [f"{c['phase']}({c['strategy']})" for c in flow["consumers"]]

            if not providers:
                print(f"  ⚠️  {field}: 无提供者 -> {', '.join(consumers)}")
            elif not consumers:
                print(f"  ℹ️  {field}: {', '.join(providers)} -> 无消费者")
            else:
                print(f"  ✅ {field}: {', '.join(providers)} -> {', '.join(consumers)}")

        print("\n详细依赖图:")
        for phase, info in report["dependency_graph"].items():
            print(f"  {phase} ({info['strategy']}):")
            if info["requires"]:
                print(f"    需要: {', '.join(info['requires'])}")
            if info["optional"]:
                print(f"    可选: {', '.join(info['optional'])}")
            if info["provides"]:
                print(f"    提供: {', '.join(info['provides'])}")
            if info["depends_on_phases"]:
                print(f"    依赖阶段: {', '.join(info['depends_on_phases'])}")
            print()
