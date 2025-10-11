# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Factory classes for creating Constellation Agent strategies and prompters.

This module provides factory classes that create appropriate strategies and prompters
based on the weaving mode, following the Factory pattern for better modularity.
"""

from typing import Dict, Type

from galaxy.agents.processors.strategies.base_constellation_strategy import (
    ConstellationLLMInteractionStrategy,
    ConstellationMemoryUpdateStrategy,
)
from galaxy.agents.processors.strategies.constellation_creation_strategy import (
    ConstellationCreationActionExecutionStrategy,
)
from galaxy.agents.processors.strategies.constellation_editing_strategy import (
    ConstellationEditingActionExecutionStrategy,
)
from galaxy.agents.schema import WeavingMode
from ufo.agents.processors.strategies.processing_strategy import BaseProcessingStrategy


class ConstellationStrategyFactory:
    """
    Factory class for creating Constellation processing strategies based on weaving mode.

    This factory ensures that the correct strategy implementations are used for each
    processing phase based on the current weaving mode (CREATION or EDITING).

    Benefits:
    - Centralized strategy creation logic
    - Type-safe strategy selection
    - Easy extensibility for new modes
    - Clear separation of concerns
    """

    _action_execution_strategies: Dict[WeavingMode, Type[BaseProcessingStrategy]] = {
        WeavingMode.CREATION: ConstellationCreationActionExecutionStrategy,
        WeavingMode.EDITING: ConstellationEditingActionExecutionStrategy,
    }

    @classmethod
    def create_llm_interaction_strategy(
        cls, fail_fast: bool = True
    ) -> BaseProcessingStrategy:
        """
        Create LLM interaction strategy based on weaving mode.

        :param weaving_mode: The weaving mode (CREATION or EDITING)
        :param fail_fast: Whether to raise exceptions immediately on errors
        :return: Appropriate LLM interaction strategy instance
        :raises ValueError: If weaving mode is not supported
        """

        return ConstellationLLMInteractionStrategy(fail_fast)

    @classmethod
    def create_action_execution_strategy(
        cls, weaving_mode: WeavingMode, fail_fast: bool = False
    ) -> BaseProcessingStrategy:
        """
        Create action execution strategy based on weaving mode.

        :param weaving_mode: The weaving mode (CREATION or EDITING)
        :param fail_fast: Whether to raise exceptions immediately on errors
        :return: Appropriate action execution strategy instance
        :raises ValueError: If weaving mode is not supported
        """
        if weaving_mode not in cls._action_execution_strategies:
            raise ValueError(
                f"Unsupported weaving mode for action execution: {weaving_mode}"
            )

        strategy_class = cls._action_execution_strategies[weaving_mode]
        return strategy_class(fail_fast=fail_fast)

    @classmethod
    def create_memory_update_strategy(
        cls, fail_fast: bool = False
    ) -> BaseProcessingStrategy:
        """
        Create memory update strategy (shared across all weaving modes).

        :param fail_fast: Whether to raise exceptions immediately on errors
        :return: Memory update strategy instance
        """
        return ConstellationMemoryUpdateStrategy(fail_fast=fail_fast)

    @classmethod
    def create_all_strategies(
        cls,
        weaving_mode: WeavingMode,
        llm_fail_fast: bool = True,
        action_fail_fast: bool = False,
        memory_fail_fast: bool = False,
    ) -> Dict[str, BaseProcessingStrategy]:
        """
        Create all required strategies for a weaving mode.

        :param weaving_mode: The weaving mode (CREATION or EDITING)
        :param llm_fail_fast: Whether LLM interaction should fail fast
        :param action_fail_fast: Whether action execution should fail fast
        :param memory_fail_fast: Whether memory update should fail fast
        :return: Dictionary mapping strategy names to strategy instances
        """
        return {
            "llm_interaction": cls.create_llm_interaction_strategy(
                weaving_mode, llm_fail_fast
            ),
            "action_execution": cls.create_action_execution_strategy(
                weaving_mode, action_fail_fast
            ),
            "memory_update": cls.create_memory_update_strategy(memory_fail_fast),
        }

    @classmethod
    def get_supported_weaving_modes(cls) -> list[WeavingMode]:
        """
        Get list of supported weaving modes.

        :return: List of supported WeavingMode values
        """
        return list(cls._action_execution_strategies.keys())


# Convenience functions for common factory operations


def create_constellation_strategies_for_mode(
    weaving_mode: WeavingMode,
) -> Dict[str, BaseProcessingStrategy]:
    """
    Convenience function to create all strategies for a specific weaving mode.

    :param weaving_mode: The weaving mode
    :return: Dictionary of strategy instances
    """
    return ConstellationStrategyFactory.create_all_strategies(weaving_mode)
