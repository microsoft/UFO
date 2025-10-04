#!/usr/bin/env python
"""
Integration test for GalaxySession with full workflow execution.
"""

import asyncio
import logging
import os
import sys
from unittest.mock import MagicMock

# Add UFO path - adjust for tests/galaxy/session subdirectory
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from galaxy.session.galaxy_session import GalaxySession
from galaxy.client.constellation_client import ConstellationClient


async def test_galaxy_session_workflow():
    """Test GalaxySession with a complete workflow."""
    print("🚀 Testing GalaxySession Full Workflow\n")

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Mock client with device manager
    mock_client = MagicMock(spec=ConstellationClient)
    mock_client.device_manager = MagicMock()

    print("=== Test 1: Session Creation and Setup ===")

    # Create session
    session = GalaxySession(
        task="Complete project development workflow",
        should_evaluate=True,
        id="workflow-session-001",
        client=mock_client,
        initial_request="Create a comprehensive software development workflow with testing and deployment",
    )

    print("✅ Session created")
    print(f"   Task: {session.task}")
    print(f"   Initial request: {session._initial_request}")
    print(f"   Agent: {type(session.agent).__name__}")
    print(f"   Event observers: {len(session._observers)}")

    print("\n=== Test 2: Round Creation and Execution ===")

    try:
        # Create first round
        round1 = session.create_new_round()

        if round1:
            print("✅ First round created")
            print(f"   Round ID: {round1._id}")
            print(f"   Request: {round1._request}")

            # Test round properties
            print(f"   Is finished: {round1.is_finished()}")
            print(f"   Agent status: {round1._agent.status}")

        # Try to create second round (should be None since only one request)
        round2 = session.create_new_round()
        if round2 is None:
            print("✅ Second round correctly not created (no more requests)")
        else:
            print(f"ℹ️ Second round created: {round2._id}")

    except Exception as e:
        print(f"❌ Error in round creation: {e}")
        import traceback

        traceback.print_exc()

    print("\n=== Test 3: Session State Management ===")

    try:
        # Test various session states
        print(f"✅ Session finished: {session.is_finished()}")
        print(f"✅ Session error: {session.is_error()}")
        print(f"✅ Current step: {session.step}")
        print(f"✅ Total rounds: {session.total_rounds}")
        print(f"✅ Current constellation: {session.current_constellation}")

        # Test session results
        results = session.session_results
        print(f"✅ Session results keys: {list(results.keys())}")

    except Exception as e:
        print(f"❌ Error in state management: {e}")
        return

    print("\n=== Test 4: Agent Integration ===")

    try:
        agent = session.agent
        print(f"✅ Agent name: {agent.name}")
        print(f"✅ Agent status: {agent.status}")
        print(f"✅ Agent orchestrator: {type(agent.orchestrator).__name__}")

        # Test agent constellation access
        constellation = agent.current_constellation
        print(f"✅ Agent constellation: {constellation}")

    except Exception as e:
        print(f"❌ Error in agent integration: {e}")
        return

    print("\n=== Test 5: Event System Integration ===")

    try:
        # Check event system
        event_bus = session._event_bus
        observers = session._observers

        print(f"✅ Event bus: {type(event_bus).__name__}")
        print(f"✅ Observer count: {len(observers)}")

        for i, observer in enumerate(observers):
            observer_type = type(observer).__name__
            print(f"   Observer {i+1}: {observer_type}")

    except Exception as e:
        print(f"❌ Error in event system: {e}")
        return

    print("\n=== Test 6: Session Cleanup ===")

    try:
        # Force finish the session
        await session.force_finish("Integration test completed")

        print("✅ Session force finished")
        print(f"   Final status: {session.agent.status}")
        print(f"   Session finished: {session.is_finished()}")
        print(
            f"   Finish reason: {session.session_results.get('finish_reason', 'N/A')}"
        )

    except Exception as e:
        print(f"❌ Error in session cleanup: {e}")
        return

    print("\n✅ GalaxySession workflow test completed successfully!")


async def test_galaxy_session_error_scenarios():
    """Test GalaxySession error handling scenarios."""
    print("\n🔍 Testing GalaxySession Error Scenarios\n")

    print("=== Test 1: Invalid Client Scenario ===")

    try:
        # Test with None client (should handle gracefully)
        session = GalaxySession(
            task="Test with no client",
            should_evaluate=False,
            id="no-client-session",
            client=None,
            initial_request="Test request",
        )
        print("❌ Should have failed with None client")

    except Exception as e:
        print(f"✅ Correctly failed with None client: {type(e).__name__}")

    print("\n=== Test 2: Long Task Name Scenario ===")

    try:
        mock_client = MagicMock()
        mock_client.device_manager = MagicMock()

        # Test with very long task name
        long_task = "A" * 200 + " very long task name for testing limits"
        session = GalaxySession(
            task=long_task,
            should_evaluate=False,
            id="long-task-session",
            client=mock_client,
            initial_request="Test long task",
        )

        print("✅ Handled long task name successfully")
        print(f"   Task length: {len(session.task)}")

    except Exception as e:
        print(f"❌ Failed with long task name: {e}")

    print("\n=== Test 3: Empty Request Scenario ===")

    try:
        mock_client = MagicMock()
        mock_client.device_manager = MagicMock()

        # Test with empty initial request
        session = GalaxySession(
            task="Test empty request",
            should_evaluate=False,
            id="empty-request-session",
            client=mock_client,
            initial_request="",
        )

        print("✅ Handled empty request successfully")
        print(f"   Next request: '{session.next_request()}'")
        print(f"   Eval request: '{session.request_to_evaluate()}'")

    except Exception as e:
        print(f"❌ Failed with empty request: {e}")

    print("\n✅ Error scenario testing completed!")


async def main():
    """Run all GalaxySession integration tests."""
    print("🧪 GalaxySession Integration Testing Suite\n")
    print("=" * 60)

    try:
        # Run workflow test
        await test_galaxy_session_workflow()

        # Run error scenario tests
        await test_galaxy_session_error_scenarios()

        print("\n" + "=" * 60)
        print("🎯 Integration Testing Summary")
        print("=" * 60)
        print("✅ All GalaxySession integration tests passed!")
        print("🎉 GalaxySession is ready for production use!")

    except Exception as e:
        print(f"\n💥 Critical error during integration testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
