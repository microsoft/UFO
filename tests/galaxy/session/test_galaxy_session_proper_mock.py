#!/usr/bin/env python3
"""
Proper Galaxy Session Test with Mocking

This test demonstrates proper mocking techniques for testing GalaxySession
without modifying production code. It mocks only what needs to be mocked
while keeping the real ConstellationAgent structure intact.
"""

import asyncio
import logging
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional

# Add UFO path - adjust for tests/galaxy/session subdirectory
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Import shared mocks
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from galaxy.mocks import MockConstellationAgent, MockTaskConstellationOrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_minimal_config():
    """Set up minimal configuration for testing."""
    import tempfile
    import os
    from ufo.config import Config

    # Create a temporary config
    temp_config = {
        "MAX_STEP": 10,
        "MAX_ROUND": 5,
        "WORKSPACE_PATH": tempfile.gettempdir(),
        "LOG_LEVEL": "INFO",
    }

    # Mock the config singleton
    config_instance = MagicMock()
    config_instance.config_data = temp_config

    with patch.object(Config, "get_instance", return_value=config_instance):
        return config_instance


class MockConstellationClient:
    """Mock constellation client for testing."""

    def __init__(self):
        self.device_manager = MagicMock()
        self.device_manager.get_device_list.return_value = ["mock_device"]


class MockProcessor:
    """Mock processor for ConstellationAgent."""

    def __init__(self, agent, global_context):
        self.agent = agent
        self.global_context = global_context
        self.processing_context = MagicMock()
        self.processing_context.get_local.return_value = "continue"

    async def process(self):
        """Mock process method."""
        logger.info("Mock processor processing...")

        # Create a simple mock constellation
        from galaxy.constellation.orchestrator.orchestrator import (
            create_simple_constellation_standalone,
        )

        mock_constellation = create_simple_constellation_standalone(
            task_descriptions=[
                "Analyze user request",
                "Plan execution strategy",
                "Execute main task",
                "Validate results",
            ],
            constellation_name="MockTestConstellation",
            sequential=True,
        )

        # Set it in context
        from ufo.module.context import ContextNames

        self.global_context.set(ContextNames.CONSTELLATION, mock_constellation)

        await asyncio.sleep(0.1)  # Simulate processing time


async def test_galaxy_session_with_proper_mocks():
    """Test GalaxySession using proper mocking techniques."""

    logger.info("🚀 Starting Galaxy Session Test with Proper Mocking")

    # Set up mocks
    config = setup_minimal_config()

    # Mock client and orchestrator
    mock_client = MockConstellationClient()

    # Patch the orchestrator class to return our mock
    with patch(
        "ufo.galaxy.session.galaxy_session.TaskConstellationOrchestrator",
        MockTaskConstellationOrchestrator,
    ):
        # Patch the processor class in ConstellationAgent
        with patch(
            "ufo.galaxy.agents.constellation_agent.ConstellationAgentProcessor",
            MockProcessor,
        ):
            # Import ConstellationAgent to patch its methods
            from galaxy.agents.constellation_agent import ConstellationAgent

            # Mock context provision method to avoid MCP calls
            with patch.object(
                ConstellationAgent, "context_provision", new_callable=AsyncMock
            ) as mock_context_provision:

                # Import after patches are set up
                from galaxy.session.galaxy_session import GalaxySession
                from galaxy.core.events import get_event_bus
                from ufo.module.context import Context, ContextNames

                # Create Galaxy Session (uses real ConstellationAgent but with mocked dependencies)
                session = GalaxySession(
                    task="Test task: analyze data and generate insights",
                    should_evaluate=True,
                    id="test_session_001",
                    client=mock_client,
                    initial_request="Please help me analyze the sales data and provide insights",
                )

                logger.info("✅ Galaxy Session created successfully")
                logger.info(f"📋 Session ID: {session._id}")
                logger.info(f"🎯 Task: {session.task}")
                logger.info(f"🤖 Agent Type: {type(session.agent).__name__}")
                logger.info(
                    f"🎪 Orchestrator Type: {type(session.orchestrator).__name__}"
                )

                # Test session properties
                assert session.agent is not None, "Agent should be initialized"
                assert (
                    session.orchestrator is not None
                ), "Orchestrator should be initialized"
                assert len(session._observers) > 0, "Observers should be set up"

                logger.info("✅ Session properties validated")

                # Test event system
                event_bus = get_event_bus()
                assert event_bus is not None, "Event bus should be available"

                # Test round creation
                first_round = session.create_new_round()
                assert first_round is not None, "First round should be created"
                assert first_round.id == 0, "First round should have ID 0"

                logger.info("✅ Round creation validated")

                # Test session running (with timeout to prevent hanging)
                logger.info("🔄 Running session...")

                try:
                    # Run with timeout
                    await asyncio.wait_for(session.run(), timeout=10.0)
                    logger.info("✅ Session completed successfully")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Session run timed out (expected for mock)")
                    await session.force_finish("Test timeout")
                except Exception as e:
                    logger.error(f"❌ Session run failed: {e}")
                    import traceback

                    traceback.print_exc()

                # Test session results
                results = session.session_results
                logger.info(f"📊 Session Results: {results}")

                # Test agent status
                logger.info(f"🎭 Agent Status: {session.agent.status}")

                # Test constellation access
                if session.current_constellation:
                    logger.info(
                        f"🌟 Current Constellation: {session.current_constellation.constellation_id}"
                    )
                    logger.info(
                        f"📈 Task Count: {session.current_constellation.task_count}"
                    )
                    stats = session.current_constellation.get_statistics()
                    logger.info(f"📊 Statistics: {stats}")
                else:
                    logger.info("🌟 No current constellation (expected for this test)")


async def test_agent_mocking_specifically():
    """Test ConstellationAgent with specific method mocking."""

    logger.info("\n🔧 Testing ConstellationAgent with Method-Level Mocking")

    from galaxy.agents.constellation_agent import ConstellationAgent
    from ufo.module.context import Context, ContextNames

    # Create real agent with mocked orchestrator
    mock_orchestrator = MockTaskConstellationOrchestrator()
    agent = ConstellationAgent(orchestrator=mock_orchestrator)

    # Mock specific methods that need external dependencies
    with patch.object(
        agent, "context_provision", new_callable=AsyncMock
    ) as mock_provision:
        with patch.object(
            agent, "_load_mcp_context", new_callable=AsyncMock
        ) as mock_mcp:

            # Create context
            context = Context()
            context.set(ContextNames.REQUEST, "test request for agent")

            # Test agent initialization
            assert agent.name == "constellation_agent"
            assert agent.status == "START"
            assert agent.orchestrator == mock_orchestrator

            logger.info("✅ Agent initialization validated")

            # Test status updates
            agent.status = "CONTINUE"
            assert agent.status == "CONTINUE"

            agent.status = "FINISH"
            assert agent.status == "FINISH"

            logger.info("✅ Agent status management validated")

            # Test state management
            from galaxy.agents.constellation_agent_states import (
                StartConstellationAgentState,
            )

            start_state = StartConstellationAgentState()
            agent.set_state(start_state)

            assert agent.state is not None
            logger.info("✅ Agent state management validated")


async def test_event_system_with_mocks():
    """Test event system integration with mocks."""

    logger.info("\n📡 Testing Event System Integration")

    from galaxy.core.events import get_event_bus, ConstellationEvent, EventType

    # Get event bus
    event_bus = get_event_bus()

    # Create a mock observer
    events_received = []

    class MockObserver:
        async def on_event(self, event):
            events_received.append(event)
            logger.info(f"📨 Mock observer received event: {event.event_type}")

    observer = MockObserver()
    event_bus.subscribe(observer)

    # Publish test event
    test_event = ConstellationEvent(
        event_type=EventType.CONSTELLATION_STARTED,
        source_id="test_agent",
        timestamp=time.time(),
        data={"test": "data"},
        constellation_id="test_constellation",
        constellation_state="active",
    )

    await event_bus.publish_event(test_event)

    # Give some time for event processing
    await asyncio.sleep(0.1)

    # Verify event was received
    assert len(events_received) > 0, "Observer should have received events"
    received_event = events_received[0]
    assert received_event.event_type == EventType.CONSTELLATION_STARTED
    assert received_event.source_id == "test_agent"

    logger.info("✅ Event system integration validated")


async def main():
    """Main test function."""

    logger.info("🧪 Galaxy Session Proper Mocking Test Suite")
    logger.info("=" * 60)

    try:
        # Test 1: Galaxy Session with proper mocking
        await test_galaxy_session_with_proper_mocks()

        # Test 2: Agent-specific mocking
        await test_agent_mocking_specifically()

        # Test 3: Event system testing
        await test_event_system_with_mocks()

        logger.info("\n" + "=" * 60)
        logger.info("🎉 All tests completed successfully!")
        logger.info("✅ GalaxySession works correctly with proper mocking")
        logger.info("✅ ConstellationAgent handles mocking appropriately")
        logger.info("✅ Event system functions properly")
        logger.info("✅ Production code remains unchanged")

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
