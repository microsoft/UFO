# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test cases for the refactored Constellation Agent factory and strategy pattern implementation.

This test suite verifies:
1. Strategy factory pattern implementation
2. Prompter factory pattern implementation
3. WeavingMode-specific behavior differentiation
4. Base class inheritance and shared logic
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from galaxy.agents.schema import WeavingMode
from galaxy.agents.processors.strategies.constellation_factory import (
    ConstellationStrategyFactory,
    ConstellationPrompterFactory,
)
from galaxy.agents.processors.strategies.base_constellation_strategy import (
    BaseConstellationLLMInteractionStrategy,
    BaseConstellationActionExecutionStrategy,
)
from galaxy.agents.processors.strategies.constellation_creation_strategy import (
    ConstellationCreationLLMInteractionStrategy,
    ConstellationCreationActionExecutionStrategy,
)
from galaxy.agents.processors.strategies.constellation_editing_strategy import (
    ConstellationEditingLLMInteractionStrategy,
    ConstellationEditingActionExecutionStrategy,
)
from galaxy.agents.prompters.base_constellation_prompter import (
    BaseConstellationPrompter,
)
from galaxy.agents.prompters.constellation_creation_prompter import (
    ConstellationCreationPrompter,
)
from galaxy.agents.prompters.constellation_editing_prompter import (
    ConstellationEditingPrompter,
)
from ufo.agents.processors.core.processor_framework import (
    ProcessingContext,
    ProcessingPhase,
)


class TestConstellationStrategyFactory:
    """Test cases for ConstellationStrategyFactory."""

    def test_create_llm_interaction_strategy_creation_mode(self):
        """Test creating LLM interaction strategy for CREATION mode."""
        strategy = ConstellationStrategyFactory.create_llm_interaction_strategy(
            WeavingMode.CREATION
        )

        assert isinstance(strategy, ConstellationCreationLLMInteractionStrategy)
        assert isinstance(strategy, BaseConstellationLLMInteractionStrategy)
        assert strategy.name == "constellation_llm_interaction_creation"

    def test_create_llm_interaction_strategy_editing_mode(self):
        """Test creating LLM interaction strategy for EDITING mode."""
        strategy = ConstellationStrategyFactory.create_llm_interaction_strategy(
            WeavingMode.EDITING
        )

        assert isinstance(strategy, ConstellationEditingLLMInteractionStrategy)
        assert isinstance(strategy, BaseConstellationLLMInteractionStrategy)
        assert strategy.name == "constellation_llm_interaction_editing"

    def test_create_action_execution_strategy_creation_mode(self):
        """Test creating action execution strategy for CREATION mode."""
        strategy = ConstellationStrategyFactory.create_action_execution_strategy(
            WeavingMode.CREATION
        )

        assert isinstance(strategy, ConstellationCreationActionExecutionStrategy)
        assert isinstance(strategy, BaseConstellationActionExecutionStrategy)
        assert strategy.name == "constellation_action_execution_creation"

    def test_create_action_execution_strategy_editing_mode(self):
        """Test creating action execution strategy for EDITING mode."""
        strategy = ConstellationStrategyFactory.create_action_execution_strategy(
            WeavingMode.EDITING
        )

        assert isinstance(strategy, ConstellationEditingActionExecutionStrategy)
        assert isinstance(strategy, BaseConstellationActionExecutionStrategy)
        assert strategy.name == "constellation_action_execution_editing"

    def test_unsupported_weaving_mode_llm_interaction(self):
        """Test that unsupported weaving mode raises ValueError for LLM interaction."""
        with pytest.raises(ValueError, match="Unsupported weaving mode"):
            ConstellationStrategyFactory.create_llm_interaction_strategy("INVALID_MODE")

    def test_unsupported_weaving_mode_action_execution(self):
        """Test that unsupported weaving mode raises ValueError for action execution."""
        with pytest.raises(ValueError, match="Unsupported weaving mode"):
            ConstellationStrategyFactory.create_action_execution_strategy(
                "INVALID_MODE"
            )

    def test_get_all_strategies_creation_mode(self):
        """Test getting all strategies for CREATION mode."""
        strategies = ConstellationStrategyFactory.create_all_strategies(
            WeavingMode.CREATION
        )

        assert ProcessingPhase.LLM_INTERACTION in strategies
        assert ProcessingPhase.ACTION_EXECUTION in strategies
        assert isinstance(
            strategies[ProcessingPhase.LLM_INTERACTION],
            ConstellationCreationLLMInteractionStrategy,
        )
        assert isinstance(
            strategies[ProcessingPhase.ACTION_EXECUTION],
            ConstellationCreationActionExecutionStrategy,
        )

    def test_get_all_strategies_editing_mode(self):
        """Test getting all strategies for EDITING mode."""
        strategies = ConstellationStrategyFactory.create_all_strategies(
            WeavingMode.EDITING
        )

        assert ProcessingPhase.LLM_INTERACTION in strategies
        assert ProcessingPhase.ACTION_EXECUTION in strategies
        assert isinstance(
            strategies[ProcessingPhase.LLM_INTERACTION],
            ConstellationEditingLLMInteractionStrategy,
        )
        assert isinstance(
            strategies[ProcessingPhase.ACTION_EXECUTION],
            ConstellationEditingActionExecutionStrategy,
        )


class TestConstellationPrompterFactory:
    """Test cases for ConstellationPrompterFactory."""

    def test_create_prompter_creation_mode(self):
        """Test creating prompter for CREATION mode."""
        main_prompt = "Test main prompt"
        example_prompt = "Test example prompt"

        prompter = ConstellationPrompterFactory.create_prompter(
            WeavingMode.CREATION,
            main_prompt,
            example_prompt,
            example_prompt,
            example_prompt,
        )

        assert isinstance(prompter, ConstellationCreationPrompter)
        assert isinstance(prompter, BaseConstellationPrompter)

    def test_create_prompter_editing_mode(self):
        """Test creating prompter for EDITING mode."""
        main_prompt = "Test main prompt"
        example_prompt = "Test example prompt"

        prompter = ConstellationPrompterFactory.create_prompter(
            WeavingMode.EDITING,
            main_prompt,
            example_prompt,
            example_prompt,
            example_prompt,
        )

        assert isinstance(prompter, ConstellationEditingPrompter)
        assert isinstance(prompter, BaseConstellationPrompter)

    def test_unsupported_weaving_mode_prompter(self):
        """Test that unsupported weaving mode raises ValueError for prompter."""
        with pytest.raises(ValueError, match="Unsupported weaving mode"):
            ConstellationPrompterFactory.create_prompter(
                "INVALID_MODE", "prompt", "example", "example", "example"
            )


class TestBaseConstellationStrategy:
    """Test cases for base constellation strategies."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock ConstellationAgent."""
        agent = Mock()
        agent.message_constructor = Mock(return_value={"test": "message"})
        agent.get_response = Mock(return_value=("response_text", 0.1))
        agent.response_to_dict = Mock(
            return_value={"status": "CONTINUE", "thought": "test"}
        )
        agent.print_response = Mock()
        return agent

    @pytest.fixture
    def mock_context(self):
        """Create a mock ProcessingContext."""
        context = Mock(spec=ProcessingContext)
        context.get_local = Mock()
        context.get_global = Mock()
        context.get = Mock()
        return context

    def test_base_llm_interaction_strategy_inheritance(self):
        """Test that base LLM interaction strategy has expected methods."""
        # Test through concrete implementation
        strategy = ConstellationCreationLLMInteractionStrategy()
        assert isinstance(strategy, BaseConstellationLLMInteractionStrategy)
        assert hasattr(strategy, "execute")
        assert hasattr(strategy, "_build_comprehensive_prompt")
        assert hasattr(strategy, "_get_llm_response_with_retry")

    def test_base_action_execution_strategy_inheritance(self):
        """Test that base action execution strategy has expected methods."""
        # Test through concrete implementation
        strategy = ConstellationCreationActionExecutionStrategy()
        assert isinstance(strategy, BaseConstellationActionExecutionStrategy)
        assert hasattr(strategy, "execute")


class TestStrategyBehaviorDifferentiation:
    """Test cases to verify that different weaving modes have different behaviors."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock ConstellationAgent."""
        agent = Mock()
        agent.message_constructor = Mock(return_value={"test": "message"})
        agent.get_response = Mock(return_value=("response_text", 0.1))
        agent.response_to_dict = Mock(
            return_value={"status": "CONTINUE", "thought": "test"}
        )
        agent.print_response = Mock()
        return agent

    @pytest.fixture
    def mock_context(self):
        """Create a mock ProcessingContext."""
        context = Mock(spec=ProcessingContext)
        context.get_local = Mock(
            side_effect=lambda key, default=None: {
                "session_step": 1,
                "device_info": [],
                "weaving_mode": WeavingMode.CREATION,
            }.get(key, default)
        )
        context.get_global = Mock(
            side_effect=lambda key: {
                "CONSTELLATION": Mock(),
                "request_logger": Mock(),
            }.get(key)
        )
        context.get = Mock(return_value="test_request")
        return context

    @pytest.mark.asyncio
    @patch("ufo.galaxy.agents.processors.strategies.base_constellation_strategy.json")
    async def test_creation_vs_editing_llm_strategies_different_behavior(
        self, mock_json, mock_agent, mock_context
    ):
        """Test that creation and editing strategies have different behaviors."""
        mock_json.dumps = Mock(return_value='{"test": "json"}')

        # Create strategies
        creation_strategy = (
            ConstellationStrategyFactory.create_llm_interaction_strategy(
                WeavingMode.CREATION
            )
        )
        editing_strategy = ConstellationStrategyFactory.create_llm_interaction_strategy(
            WeavingMode.EDITING
        )

        # Execute both strategies
        creation_result = await creation_strategy.execute(mock_agent, mock_context)
        editing_result = await editing_strategy.execute(mock_agent, mock_context)

        # Both should succeed but may have different internal logic
        assert creation_result.success
        assert editing_result.success

        # Verify they are different strategy instances
        assert type(creation_strategy) != type(editing_strategy)
        assert creation_strategy.name != editing_strategy.name


class TestPrompterBehaviorDifferentiation:
    """Test cases to verify that different prompters have different behaviors."""

    def test_creation_vs_editing_prompters_different_behavior(self):
        """Test that creation and editing prompters have different behaviors."""
        main_prompt = "Test main prompt"
        example_prompt = "Test example prompt"

        # Create prompters
        creation_prompter = ConstellationPrompterFactory.create_prompter(
            WeavingMode.CREATION,
            main_prompt,
            example_prompt,
            example_prompt,
            example_prompt,
        )
        editing_prompter = ConstellationPrompterFactory.create_prompter(
            WeavingMode.EDITING,
            main_prompt,
            example_prompt,
            example_prompt,
            example_prompt,
        )

        # Verify they are different prompter instances
        assert type(creation_prompter) != type(editing_prompter)

        # Both should have the same base functionality
        assert hasattr(creation_prompter, "get_prompt_template")
        assert hasattr(editing_prompter, "get_prompt_template")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
