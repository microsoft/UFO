"""
Strategy Dependency Management System

This module provides dependency declaration and validation for processing strategies
to ensure proper data flow and early detection of dependency issues.
"""

import logging
from dataclasses import dataclass, field
from typing import Set, List, Dict, Any, Optional
from abc import ABC, abstractmethod

from ufo.agents.processors2.core.processing_context import (
    ProcessingPhase,
    ProcessingContext,
)


@dataclass
class StrategyDependency:
    """
    Strategy dependency declaration for a single field.

    This class defines a single field dependency with its requirements,
    type constraints, and default values.
    """

    field_name: str
    """Name of the field this dependency refers to."""

    required: bool = True
    """Whether this field is required for the strategy to execute."""

    expected_type: Optional[type] = None
    """Expected type of the field value."""

    default_value: Any = None
    """Default value if field is not present (only for optional fields)."""

    description: str = ""
    """Human-readable description of what this dependency is for."""


@dataclass
class StrategyMetadata:
    """
    Complete strategy metadata including dependencies and outputs.

    This class aggregates all dependency information for a strategy.
    """

    strategy_name: str
    """Name of the strategy."""

    dependencies: List[StrategyDependency] = field(default_factory=list)
    """List of field dependencies."""

    provides: List[str] = field(default_factory=list)
    """List of field names this strategy provides."""

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


@dataclass
class DependencyValidationResult:
    """Result of dependency validation."""

    is_valid: bool
    """Whether all dependencies are satisfied."""

    errors: List[str] = field(default_factory=list)
    """List of validation errors (missing required fields, etc.)."""

    warnings: List[str] = field(default_factory=list)
    """List of validation warnings (type mismatches, missing optional fields, etc.)."""

    @property
    def report(self) -> str:
        """Generate a human-readable validation report."""
        lines = []

        if self.is_valid:
            lines.append("✓ Dependency validation passed")
        else:
            lines.append("✗ Dependency validation failed")

        if self.errors:
            lines.append("Errors:")
            for error in self.errors:
                lines.append(f"  - {error}")

        if self.warnings:
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)


class StrategyDependencyValidator:
    """
    Validator for strategy dependencies.

    This class provides methods to validate strategy dependencies both
    at initialization time and during execution.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def validate_runtime_dependencies(
        self, dependencies: List[StrategyDependency], context: ProcessingContext
    ) -> "DependencyValidationResult":
        """
        Validate that all required dependencies are available in the context at runtime.

        :param dependencies: List of strategy dependencies to validate
        :param context: Processing context to check
        :return: Validation result
        """
        missing_fields = []
        warnings = []

        # Check each dependency
        for dep in dependencies:
            value = context.get_local(dep.field_name)

            if value is None:
                if dep.required:
                    missing_fields.append(dep.field_name)
                else:
                    # Optional field, could use default
                    if dep.default_value is not None:
                        warnings.append(
                            f"Optional field '{dep.field_name}' missing, will use default: {dep.default_value}"
                        )
            else:
                # Check type if specified
                if dep.expected_type and not isinstance(value, dep.expected_type):
                    warnings.append(
                        f"Field '{dep.field_name}' has type {type(value).__name__} "
                        f"but expected {dep.expected_type.__name__}"
                    )

        errors = [f"Missing required field: {field}" for field in missing_fields]

        return DependencyValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_strategy_chain(
        self, strategies: List[Any]
    ) -> "DependencyValidationResult":
        """
        Validate the complete strategy chain for dependency consistency.

        :param strategies: List of strategy instances
        :return: Validation result
        """
        errors = []
        warnings = []
        available_fields = set()

        for i, strategy in enumerate(strategies):
            strategy_name = getattr(strategy, "name", f"Strategy{i}")

            # Get dependencies and provides from strategy
            try:
                dependencies = getattr(strategy, "get_dependencies", lambda: [])()
                provides = getattr(strategy, "get_provides", lambda: [])()
            except Exception as e:
                warnings.append(
                    f"Could not get dependency info from {strategy_name}: {e}"
                )
                continue

            # Check if all required dependencies are available
            for dep in dependencies:
                if dep.required and dep.field_name not in available_fields:
                    # Check if it could come from global context or initial setup
                    if not dep.field_name.startswith(
                        ("global_", "command_", "log_", "session_")
                    ):
                        errors.append(
                            f"Strategy {strategy_name} requires '{dep.field_name}' "
                            f"but no previous strategy provides it"
                        )

            # Add fields this strategy provides to available set
            available_fields.update(provides)

        return DependencyValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_strategy_chain_detailed(
        self, strategies: Dict[ProcessingPhase, Any]
    ) -> Dict[str, Any]:
        """
        Validate the complete strategy chain for dependency consistency with detailed analysis.

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

                # Get strategy dependencies using the new interface
                try:
                    dependencies = getattr(strategy, "get_dependencies", lambda: [])()
                    provides = getattr(strategy, "get_provides", lambda: [])()
                except Exception as e:
                    self.logger.warning(
                        f"Could not get dependency info from {strategy.__class__.__name__}: {e}"
                    )
                    continue

                strategy_name = getattr(strategy, "name", strategy.__class__.__name__)

                # Convert dependencies to sets for compatibility
                required_fields = {
                    dep.field_name for dep in dependencies if dep.required
                }
                optional_fields = {
                    dep.field_name for dep in dependencies if not dep.required
                }
                provides_fields = set(provides)

                # Record dependency graph
                report["dependency_graph"][phase.value] = {
                    "strategy": strategy_name,
                    "requires": list(required_fields),
                    "provides": list(provides_fields),
                    "optional": list(optional_fields),
                    "depends_on_phases": [],  # Phase dependencies not implemented in current interface
                }

                # Check missing required fields
                missing_required = required_fields - provided_fields
                if missing_required:
                    # Filter out fields that might come from global context
                    actual_missing = {
                        field
                        for field in missing_required
                        if not field.startswith(
                            ("global_", "command_", "log_", "session_")
                        )
                    }

                    if actual_missing:
                        report["valid"] = False
                        report["issues"].append(
                            {
                                "phase": phase.value,
                                "strategy": strategy_name,
                                "type": "missing_required_fields",
                                "fields": list(actual_missing),
                            }
                        )

                # Record field flow
                for field in required_fields | optional_fields:
                    if field not in report["field_flow"]:
                        report["field_flow"][field] = {"providers": [], "consumers": []}
                    report["field_flow"][field]["consumers"].append(
                        {"phase": phase.value, "strategy": strategy_name}
                    )

                for field in provides_fields:
                    if field not in report["field_flow"]:
                        report["field_flow"][field] = {"providers": [], "consumers": []}
                    report["field_flow"][field]["providers"].append(
                        {"phase": phase.value, "strategy": strategy_name}
                    )

                # Update provided fields and completed phases
                provided_fields.update(provides_fields)
                completed_phases.add(phase)

        return report

    def print_dependency_report(self, report: Dict[str, Any]) -> None:
        """
        Print a detailed dependency validation report.

        :param report: Report from validate_strategy_chain_detailed
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
