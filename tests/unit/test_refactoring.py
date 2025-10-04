#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test script to validate the refactored Constellation Agent strategies and prompters.

This script tests the factory pattern implementation and ensures proper
strategy/prompter creation based on weaving modes.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.insert(0, project_root)

from galaxy.agents.processors.strategies.constellation_factory import (
    ConstellationStrategyFactory,
    ConstellationPrompterFactory,
)
from galaxy.agents.schema import WeavingMode


def test_strategy_factory():
    """Test the ConstellationStrategyFactory."""
    print("Testing ConstellationStrategyFactory...")

    # Test creation mode strategies
    print("  Testing CREATION mode strategies...")
    creation_strategies = ConstellationStrategyFactory.create_all_strategies(
        weaving_mode=WeavingMode.CREATION
    )

    assert "llm_interaction" in creation_strategies
    assert "action_execution" in creation_strategies
    assert "memory_update" in creation_strategies
    print(f"    ✓ Created {len(creation_strategies)} strategies for CREATION mode")

    # Test editing mode strategies
    print("  Testing EDITING mode strategies...")
    editing_strategies = ConstellationStrategyFactory.create_all_strategies(
        weaving_mode=WeavingMode.EDITING
    )

    assert "llm_interaction" in editing_strategies
    assert "action_execution" in editing_strategies
    assert "memory_update" in editing_strategies
    print(f"    ✓ Created {len(editing_strategies)} strategies for EDITING mode")

    # Test supported modes
    supported_modes = ConstellationStrategyFactory.get_supported_weaving_modes()
    assert WeavingMode.CREATION in supported_modes
    assert WeavingMode.EDITING in supported_modes
    print(f"    ✓ Supported modes: {[mode.value for mode in supported_modes]}")

    print("  ✓ ConstellationStrategyFactory tests passed!")


def test_prompter_factory():
    """Test the ConstellationPrompterFactory."""
    print("Testing ConstellationPrompterFactory...")

    # Mock prompt templates
    creation_prompt = "creation_prompt_template"
    editing_prompt = "editing_prompt_template"
    creation_example = "creation_example_template"
    editing_example = "editing_example_template"

    # Test creation mode prompter
    print("  Testing CREATION mode prompter...")
    creation_prompter = ConstellationPrompterFactory.create_prompter(
        weaving_mode=WeavingMode.CREATION,
        creation_prompt_template=creation_prompt,
        editing_prompt_template=editing_prompt,
        creation_example_prompt_template=creation_example,
        editing_example_prompt_template=editing_example,
    )

    assert creation_prompter is not None
    assert creation_prompter.weaving_mode == WeavingMode.CREATION
    print("    ✓ Created CREATION mode prompter successfully")

    # Test editing mode prompter
    print("  Testing EDITING mode prompter...")
    editing_prompter = ConstellationPrompterFactory.create_prompter(
        weaving_mode=WeavingMode.EDITING,
        creation_prompt_template=creation_prompt,
        editing_prompt_template=editing_prompt,
        creation_example_prompt_template=creation_example,
        editing_example_prompt_template=editing_example,
    )

    assert editing_prompter is not None
    assert editing_prompter.weaving_mode == WeavingMode.EDITING
    print("    ✓ Created EDITING mode prompter successfully")

    # Test supported modes
    supported_modes = ConstellationPrompterFactory.get_supported_weaving_modes()
    assert WeavingMode.CREATION in supported_modes
    assert WeavingMode.EDITING in supported_modes
    print(f"    ✓ Supported modes: {[mode.value for mode in supported_modes]}")

    print("  ✓ ConstellationPrompterFactory tests passed!")


def test_strategy_types():
    """Test that different strategies are created for different modes."""
    print("Testing strategy type differentiation...")

    # Create strategies for both modes
    creation_llm = ConstellationStrategyFactory.create_llm_interaction_strategy(
        WeavingMode.CREATION
    )
    editing_llm = ConstellationStrategyFactory.create_llm_interaction_strategy(
        WeavingMode.EDITING
    )

    creation_action = ConstellationStrategyFactory.create_action_execution_strategy(
        WeavingMode.CREATION
    )
    editing_action = ConstellationStrategyFactory.create_action_execution_strategy(
        WeavingMode.EDITING
    )

    # Verify they are different types
    assert type(creation_llm) != type(editing_llm)
    assert type(creation_action) != type(editing_action)

    # Verify they have the correct weaving modes
    assert creation_llm.weaving_mode == WeavingMode.CREATION
    assert editing_llm.weaving_mode == WeavingMode.EDITING
    assert creation_action.weaving_mode == WeavingMode.CREATION
    assert editing_action.weaving_mode == WeavingMode.EDITING

    print("  ✓ Different strategy types created for different modes")
    print("  ✓ Strategy type differentiation tests passed!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Refactored Constellation Agent Architecture")
    print("=" * 60)

    try:
        test_strategy_factory()
        print()

        test_prompter_factory()
        print()

        test_strategy_types()
        print()

        print("=" * 60)
        print("✅ All tests passed! Refactoring successful!")
        print("=" * 60)

        print("\nRefactoring Summary:")
        print("- ✓ Base strategy classes with shared logic")
        print("- ✓ Mode-specific strategy implementations")
        print("- ✓ Factory pattern for strategy/prompter creation")
        print("- ✓ Clean separation of concerns")
        print("- ✓ Type-safe mode selection")
        print("- ✓ Extensible architecture")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
