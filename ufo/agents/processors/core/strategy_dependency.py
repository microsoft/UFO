"""
Strategy Dependency Management System

This module provides dependency declaration and validation for processing strategies
to ensure proper data flow and early detection of dependency issues.
"""

import logging
from dataclasses import dataclass, field
from typing import Set, List, Dict, Any, Optional, Type


from ufo.agents.processors.context.processing_context import (
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


class StrategyMetadataRegistry:
    """
    Centralized registry for strategy metadata including dependencies and provides.
    This class manages all decorator-declared information in one place.
    """

    _registry: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_strategy(
        cls,
        strategy_class: Type,
        dependencies: List[StrategyDependency] = None,
        provides: List[str] = None,
    ):
        """
        Register a strategy with its metadata.

        :param strategy_class: The strategy class
        :param dependencies: List of strategy dependencies
        :param provides: List of provided fields
        """
        class_name = strategy_class.__name__
        cls._registry[class_name] = {
            "dependencies": dependencies or [],
            "provides": provides or [],
            "class": strategy_class,
        }

    @classmethod
    def get_dependencies(cls, strategy_class: Type) -> List[StrategyDependency]:
        """
        Get dependencies for a strategy class.

        :param strategy_class: The strategy class
        :return: List of dependencies
        """
        class_name = strategy_class.__name__
        return cls._registry.get(class_name, {}).get("dependencies", [])

    @classmethod
    def get_provides(cls, strategy_class: Type) -> List[str]:
        """
        Get provides for a strategy class.

        :param strategy_class: The strategy class
        :return: List of provided fields
        """
        class_name = strategy_class.__name__
        return cls._registry.get(class_name, {}).get("provides", [])

    @classmethod
    def is_registered(cls, strategy_class: Type) -> bool:
        """
        Check if a strategy class is registered.

        :param strategy_class: The strategy class
        :return: True if registered
        """
        return strategy_class.__name__ in cls._registry

    @classmethod
    def get_all_registered(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered strategy metadata.

        :return: Dictionary of all registered strategies
        """
        return cls._registry.copy()


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

            # Get dependencies and provides from strategy metadata registry
            try:
                dependencies = StrategyMetadataRegistry.get_dependencies(
                    strategy.__class__
                )
                provides = StrategyMetadataRegistry.get_provides(strategy.__class__)
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

                # Get strategy dependencies using metadata registry
                try:
                    dependencies = StrategyMetadataRegistry.get_dependencies(
                        strategy.__class__
                    )
                    provides = StrategyMetadataRegistry.get_provides(strategy.__class__)
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
        :return: None
        """
        print("\n" + "=" * 60)
        print("Strategy Dependency Validation Report")
        print("=" * 60)

        if report["valid"]:
            print("✅ All strategy dependencies are satisfied")
        else:
            print("❌ Dependency issues found:")
            for issue in report["issues"]:
                if issue["type"] == "missing_required_fields":
                    print(
                        f"  - {issue['phase']}: {issue['strategy']} missing required fields: {issue['fields']}"
                    )
                elif issue["type"] == "missing_required_phases":
                    print(
                        f"  - {issue['phase']}: {issue['strategy']} missing required phases: {issue['phases']}"
                    )

        print(f"\nProcessing phase order: {' -> '.join(report['phase_order'])}")

        print("\nField flow analysis:")
        for field, flow in report["field_flow"].items():
            providers = [f"{p['phase']}({p['strategy']})" for p in flow["providers"]]
            consumers = [f"{c['phase']}({c['strategy']})" for c in flow["consumers"]]

            if not providers:
                print(f"  ⚠️  {field}: No providers -> {', '.join(consumers)}")
            elif not consumers:
                print(f"  ℹ️  {field}: {', '.join(providers)} -> No consumers")
            else:
                print(f"  ✅ {field}: {', '.join(providers)} -> {', '.join(consumers)}")

        print("\nDetailed dependency graph:")
        for phase, info in report["dependency_graph"].items():
            print(f"  {phase} ({info['strategy']}):")
            if info["requires"]:
                print(f"    Requires: {', '.join(info['requires'])}")
            if info["optional"]:
                print(f"    Optional: {', '.join(info['optional'])}")
            if info["provides"]:
                print(f"    Provides: {', '.join(info['provides'])}")
            if info["depends_on_phases"]:
                print(f"    Depends on phases: {', '.join(info['depends_on_phases'])}")
            print()


# ===== Strategy Decorator Implementation =====
from functools import wraps
from typing import Union, Type


def strategy_config(
    dependencies: Union[List[str], List[Dict[str, Any]]] = None,
    provides: List[str] = None,
    fail_fast: bool = True,
    description: str = "",
):
    """
    Strategy configuration decorator that declares strategy dependencies and provided fields.
    :param dependencies: List of dependency fields, can be simple string list or detailed config dict list
    :param provides: List of provided fields
    :param fail_fast: Whether to fail fast on errors
    :param description: Strategy description
    :return: Decorated class
    """

    def decorator(cls: Type) -> Type:
        # Store configuration information in class attributes
        cls._strategy_dependencies = _parse_dependencies(dependencies or [])
        cls._strategy_provides = provides or []
        cls._strategy_fail_fast = fail_fast
        cls._strategy_description = description

        # Add get_dependencies and get_provides methods
        def get_dependencies(self) -> List[StrategyDependency]:
            return self.__class__._strategy_dependencies

        def get_provides(self) -> List[str]:
            return self.__class__._strategy_provides

        def get_description(self) -> str:
            return self.__class__._strategy_description

        # Add methods to the class
        cls.get_dependencies = get_dependencies
        cls.get_provides = get_provides
        cls.get_description = get_description

        return cls

    return decorator


def depends_on(*dependencies: str):
    """
    Simplified dependency declaration decorator that registers dependencies in the metadata registry.
    :param dependencies: Field names that this strategy depends on
    :return: Decorated class
    """

    def decorator(cls: Type) -> Type:
        # Convert string dependencies to StrategyDependency objects
        dep_objects = [StrategyDependency(field_name=dep) for dep in dependencies]

        # Get existing provides if already registered
        existing_provides = StrategyMetadataRegistry.get_provides(cls)

        # Register in the metadata registry
        StrategyMetadataRegistry.register_strategy(
            cls, dependencies=dep_objects, provides=existing_provides
        )

        # Keep the old method for backward compatibility
        def get_dependencies(self) -> List[StrategyDependency]:
            return StrategyMetadataRegistry.get_dependencies(self.__class__)

        cls.get_dependencies = get_dependencies
        return cls

    return decorator


def provides(*fields: str):
    """
    Simplified provides declaration decorator that registers provides in the metadata registry.
    :param fields: Field names that this strategy provides
    :return: Decorated class
    """

    def decorator(cls: Type) -> Type:
        # Get existing dependencies if already registered
        existing_dependencies = StrategyMetadataRegistry.get_dependencies(cls)

        # Register in the metadata registry
        StrategyMetadataRegistry.register_strategy(
            cls, dependencies=existing_dependencies, provides=list(fields)
        )

        # Keep the old method for backward compatibility
        def get_provides(self) -> List[str]:
            return StrategyMetadataRegistry.get_provides(self.__class__)

        cls.get_provides = get_provides
        return cls

    return decorator


def _parse_dependencies(
    dependencies: Union[List[str], List[Dict[str, Any]]],
) -> List[StrategyDependency]:
    """
    Parse dependency configuration, supporting both simple strings and detailed dictionary formats.
    :param dependencies: List of dependency configurations
    :return: List of parsed StrategyDependency objects
    """
    parsed_dependencies = []

    for dep in dependencies:
        if isinstance(dep, str):
            # Simple string format
            parsed_dependencies.append(StrategyDependency(field_name=dep))
        elif isinstance(dep, dict):
            # Detailed dictionary format
            parsed_dependencies.append(StrategyDependency(**dep))
        else:
            raise ValueError(f"Invalid dependency format: {dep}")

    return parsed_dependencies


def validate_provides_consistency(
    strategy_name: str, declared_provides: List[str], actual_provides: List[str], logger
) -> None:
    """
    Validate consistency between declared provides fields and actual returned fields.
    :param strategy_name: Strategy name
    :param declared_provides: List of declared provided fields
    :param actual_provides: List of actually provided fields
    :param logger: Logger instance
    """
    declared_set = set(declared_provides)
    actual_set = set(actual_provides)

    # Check for missing fields (declared but not provided)
    missing_fields = declared_set - actual_set
    if missing_fields:
        logger.warning(
            f"Strategy '{strategy_name}' declared to provide {list(missing_fields)} "
            f"but didn't return them in execution result"
        )

    # Check for extra fields (provided but not declared)
    extra_fields = actual_set - declared_set
    if extra_fields:
        logger.warning(
            f"Strategy '{strategy_name}' returned extra fields {list(extra_fields)} "
            f"that were not declared in provides"
        )

    # If perfectly matched, log debug information
    if declared_set == actual_set:
        logger.debug(f"Strategy '{strategy_name}' provides consistency: PASS")
