# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Example usage of the refactored Session architecture.
Demonstrates how to create sessions for both Windows and Linux platforms.
"""

import asyncio
from fastapi import WebSocket

from ufo.module.session_pool import SessionFactory


async def example_windows_normal_session():
    """Example: Create a normal Windows session."""
    print("=== Windows Normal Session Example ===")

    factory = SessionFactory()
    sessions = factory.create_session(
        task="windows_word_task",
        mode="normal",
        plan="",
        request="Open Microsoft Word and create a new document with a title 'Hello World'",
    )

    session = sessions[0]
    print(f"Created session: {session.__class__.__name__}")
    print(f"Has HostAgent: {session.host_agent is not None}")

    # Run the session
    await session.run()


async def example_windows_service_session(websocket: WebSocket):
    """Example: Create a Windows service session with WebSocket."""
    print("=== Windows Service Session Example ===")

    factory = SessionFactory()
    session = factory.create_service_session(
        task="windows_service_task",
        should_evaluate=False,
        id="ws_session_001",
        request="Open Excel and create a new spreadsheet",
        websocket=websocket,
    )

    print(f"Created session: {session.__class__.__name__}")
    print(f"Has HostAgent: {session.host_agent is not None}")

    await session.run()


async def example_linux_normal_session():
    """Example: Create a normal Linux session."""
    print("=== Linux Normal Session Example ===")

    factory = SessionFactory()
    sessions = factory.create_session(
        task="linux_firefox_task",
        mode="normal",
        plan="",
        request="Open Firefox and search for 'Python programming tutorials'",
        platform_override="linux",  # Optional, auto-detected
        application_name="firefox",  # Required for Linux
    )

    session = sessions[0]
    print(f"Created session: {session.__class__.__name__}")
    print(f"Has HostAgent: {session.host_agent is not None}")

    # Run the session
    await session.run()


async def example_linux_service_session(websocket: WebSocket):
    """Example: Create a Linux service session with WebSocket."""
    print("=== Linux Service Session Example ===")

    factory = SessionFactory()
    session = factory.create_service_session(
        task="linux_service_task",
        should_evaluate=False,
        id="linux_session_001",
        request="Open gedit and create a new file",
        websocket=websocket,
        application_name="gedit",
        platform_override="linux",
    )

    print(f"Created session: {session.__class__.__name__}")
    print(f"Has HostAgent: {session.host_agent is not None}")

    await session.run()


async def example_direct_session_creation():
    """Example: Create sessions directly without factory."""
    print("=== Direct Session Creation Example ===")

    # Windows Session
    from ufo.module.sessions.session import Session

    windows_session = Session(
        task="direct_windows_task",
        should_evaluate=True,
        id=0,
        request="Open Notepad",
        mode="normal",
    )
    print(f"Windows session created: {windows_session.__class__.__name__}")
    print(f"Has HostAgent: {windows_session.host_agent is not None}")

    # Linux Session
    from ufo.module.sessions.linux_session import LinuxSession

    linux_session = LinuxSession(
        task="direct_linux_task",
        should_evaluate=True,
        id=0,
        request="Open terminal",
        mode="normal",
        application_name="gnome-terminal",
    )
    print(f"Linux session created: {linux_session.__class__.__name__}")
    print(f"Has HostAgent: {linux_session.host_agent is not None}")


def example_platform_detection():
    """Example: Demonstrate platform detection."""
    print("=== Platform Detection Example ===")

    import platform

    factory = SessionFactory()
    current_platform = platform.system().lower()
    print(f"Detected platform: {current_platform}")

    # Auto-detection
    sessions = factory.create_session(
        task="auto_detect_task",
        mode="normal",
        plan="",
        request="Open default text editor",
        application_name="notepad" if current_platform == "windows" else "gedit",
    )

    session = sessions[0]
    print(f"Created session type: {session.__class__.__name__}")

    # Manual override
    print("\nTesting with platform override:")

    try:
        windows_sessions = factory.create_session(
            task="forced_windows",
            mode="normal",
            plan="",
            request="Test",
            platform_override="windows",
        )
        print(f"Forced Windows session: {windows_sessions[0].__class__.__name__}")
    except Exception as e:
        print(f"Error creating Windows session: {e}")

    try:
        linux_sessions = factory.create_session(
            task="forced_linux",
            mode="normal",
            plan="",
            request="Test",
            platform_override="linux",
            application_name="firefox",
        )
        print(f"Forced Linux session: {linux_sessions[0].__class__.__name__}")
    except Exception as e:
        print(f"Error creating Linux session: {e}")


async def main():
    """Main function to run all examples."""
    print("Session Architecture Examples\n" + "=" * 50 + "\n")

    # Example 1: Platform detection
    example_platform_detection()
    print("\n" + "=" * 50 + "\n")

    # Example 2: Direct creation
    await example_direct_session_creation()
    print("\n" + "=" * 50 + "\n")

    # Note: Actual session execution requires proper environment setup
    # Uncomment the following to run actual sessions:

    # await example_windows_normal_session()
    # print("\n" + "=" * 50 + "\n")

    # await example_linux_normal_session()
    # print("\n" + "=" * 50 + "\n")

    # For service sessions, you need a WebSocket connection:
    # websocket = ...  # Your WebSocket instance
    # await example_windows_service_session(websocket)
    # await example_linux_service_session(websocket)


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())

    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nKey takeaways:")
    print("1. Use SessionFactory for creating sessions (recommended)")
    print("2. Windows sessions have HostAgent, Linux sessions don't")
    print("3. Linux sessions require application_name parameter")
    print("4. Platform is auto-detected but can be overridden")
    print("5. Both platforms support normal and service modes")
