"""
Test Galaxy Configuration Loading and Access

Tests the new Galaxy configuration system with structured attribute access.
"""

import pytest
from config.config_loader import get_galaxy_config


def test_galaxy_config_basic_loading():
    """Test that Galaxy config loads successfully"""
    config = get_galaxy_config()
    assert config is not None
    print("✅ Galaxy config loaded successfully")


def test_galaxy_agent_config_access():
    """Test accessing agent configuration through structured attributes"""
    config = get_galaxy_config()

    # Test agent.CONSTELLATION_AGENT access
    assert hasattr(config, "agent")
    assert hasattr(config.agent, "CONSTELLATION_AGENT")

    constellation_agent = config.agent.CONSTELLATION_AGENT

    # Test typed fields
    assert hasattr(constellation_agent, "API_MODEL")
    assert hasattr(constellation_agent, "API_TYPE")
    assert hasattr(constellation_agent, "API_BASE")

    print(f"✅ Agent API Model: {constellation_agent.API_MODEL}")
    print(f"✅ Agent API Type: {constellation_agent.API_TYPE}")
    print(f"✅ Agent API Base: {constellation_agent.API_BASE}")

    # Test prompt configurations
    assert hasattr(constellation_agent, "CONSTELLATION_CREATION_PROMPT")
    assert hasattr(constellation_agent, "CONSTELLATION_EDITING_PROMPT")
    assert hasattr(constellation_agent, "CONSTELLATION_CREATION_EXAMPLE_PROMPT")
    assert hasattr(constellation_agent, "CONSTELLATION_EDITING_EXAMPLE_PROMPT")

    print(f"✅ Creation Prompt: {constellation_agent.CONSTELLATION_CREATION_PROMPT}")
    print(f"✅ Editing Prompt: {constellation_agent.CONSTELLATION_EDITING_PROMPT}")


def test_galaxy_constellation_config_access():
    """Test accessing constellation runtime configuration"""
    config = get_galaxy_config()

    # Test constellation attribute access
    assert hasattr(config, "constellation")

    # Test typed fields
    assert hasattr(config.constellation, "CONSTELLATION_ID")
    assert hasattr(config.constellation, "HEARTBEAT_INTERVAL")
    assert hasattr(config.constellation, "RECONNECT_DELAY")
    assert hasattr(config.constellation, "MAX_CONCURRENT_TASKS")
    assert hasattr(config.constellation, "MAX_STEP")
    assert hasattr(config.constellation, "DEVICE_INFO")

    print(f"✅ Constellation ID: {config.constellation.CONSTELLATION_ID}")
    print(f"✅ Heartbeat Interval: {config.constellation.HEARTBEAT_INTERVAL}")
    print(f"✅ Reconnect Delay: {config.constellation.RECONNECT_DELAY}")
    print(f"✅ Max Concurrent Tasks: {config.constellation.MAX_CONCURRENT_TASKS}")
    print(f"✅ Max Step: {config.constellation.MAX_STEP}")
    print(f"✅ Device Info: {config.constellation.DEVICE_INFO}")


def test_galaxy_lowercase_attribute_access():
    """Test lowercase attribute access (snake_case)"""
    config = get_galaxy_config()

    # Test constellation config lowercase access
    assert (
        config.constellation.constellation_id == config.constellation.CONSTELLATION_ID
    )
    assert (
        config.constellation.heartbeat_interval
        == config.constellation.HEARTBEAT_INTERVAL
    )
    assert config.constellation.reconnect_delay == config.constellation.RECONNECT_DELAY
    assert (
        config.constellation.max_concurrent_tasks
        == config.constellation.MAX_CONCURRENT_TASKS
    )
    assert config.constellation.max_step == config.constellation.MAX_STEP
    assert config.constellation.device_info == config.constellation.DEVICE_INFO

    print("✅ Lowercase attribute access works correctly")


def test_galaxy_backward_compatible_dict_access():
    """Test backward compatible dictionary-style access"""
    config = get_galaxy_config()

    # Test dict-style access
    assert "CONSTELLATION_AGENT" in config
    assert config["CONSTELLATION_AGENT"] is not None

    assert "CONSTELLATION_ID" in config
    assert config["CONSTELLATION_ID"] == config.constellation.CONSTELLATION_ID

    assert "MAX_STEP" in config
    assert config["MAX_STEP"] == config.constellation.MAX_STEP

    assert "DEVICE_INFO" in config
    assert config["DEVICE_INFO"] == config.constellation.DEVICE_INFO

    print("✅ Backward compatible dict access works")


def test_galaxy_config_usage_in_code():
    """Test typical usage patterns in actual code"""
    config = get_galaxy_config()

    # Pattern 1: Access device info path (like in galaxy_client.py)
    device_info_path = config.constellation.DEVICE_INFO
    assert device_info_path is not None
    assert isinstance(device_info_path, str)
    print(f"✅ Device info path retrieval: {device_info_path}")

    # Pattern 2: Access MAX_STEP (like in galaxy_session.py)
    max_step = config.constellation.MAX_STEP
    assert max_step is not None
    assert isinstance(max_step, int)
    print(f"✅ Max step retrieval: {max_step}")

    # Pattern 3: Access agent config (like in base_constellation_prompter.py)
    agent_config = config.agent.CONSTELLATION_AGENT
    creation_prompt = agent_config.CONSTELLATION_CREATION_PROMPT
    editing_prompt = agent_config.CONSTELLATION_EDITING_PROMPT
    creation_example = agent_config.CONSTELLATION_CREATION_EXAMPLE_PROMPT
    editing_example = agent_config.CONSTELLATION_EDITING_EXAMPLE_PROMPT

    assert creation_prompt is not None
    assert editing_prompt is not None
    assert creation_example is not None
    assert editing_example is not None

    print(f"✅ Prompt templates retrieval successful")


def test_galaxy_config_types():
    """Test that configuration values have correct types"""
    config = get_galaxy_config()

    # Constellation runtime config types
    assert isinstance(config.constellation.CONSTELLATION_ID, str)
    assert isinstance(config.constellation.HEARTBEAT_INTERVAL, (int, float))
    assert isinstance(config.constellation.RECONNECT_DELAY, (int, float))
    assert isinstance(config.constellation.MAX_CONCURRENT_TASKS, int)
    assert isinstance(config.constellation.MAX_STEP, int)
    assert isinstance(config.constellation.DEVICE_INFO, str)

    # Agent config types
    agent = config.agent.CONSTELLATION_AGENT
    assert isinstance(agent.API_MODEL, str)
    assert isinstance(agent.API_TYPE, str)
    assert isinstance(agent.VISUAL_MODE, bool)

    print("✅ All config values have correct types")


def test_galaxy_config_caching():
    """Test that config is properly cached"""
    config1 = get_galaxy_config()
    config2 = get_galaxy_config()

    # Should return the same instance
    assert config1 is config2
    print("✅ Config caching works correctly")


def test_galaxy_config_reload():
    """Test that config can be reloaded"""
    config1 = get_galaxy_config()
    config2 = get_galaxy_config(reload=True)

    # Should return different instances when reloaded
    assert config1 is not config2

    # But values should be the same
    assert config1.constellation.MAX_STEP == config2.constellation.MAX_STEP
    assert (
        config1.agent.CONSTELLATION_AGENT.API_MODEL
        == config2.agent.CONSTELLATION_AGENT.API_MODEL
    )

    print("✅ Config reload works correctly")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Testing Galaxy Configuration System")
    print("=" * 70 + "\n")

    try:
        test_galaxy_config_basic_loading()
        print()

        test_galaxy_agent_config_access()
        print()

        test_galaxy_constellation_config_access()
        print()

        test_galaxy_lowercase_attribute_access()
        print()

        test_galaxy_backward_compatible_dict_access()
        print()

        test_galaxy_config_usage_in_code()
        print()

        test_galaxy_config_types()
        print()

        test_galaxy_config_caching()
        print()

        test_galaxy_config_reload()
        print()

        print("=" * 70)
        print("✅ All Galaxy Configuration Tests Passed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
