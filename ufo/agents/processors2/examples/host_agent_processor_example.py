"""
Usage example for the refactored Host Agent Processor V2.

This example demonstrates how to use the enhanced Host Agent Processor
with the new framework capabilities including comprehensive error handling,
metrics collection, and proper context management.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List

from ufo.agents.processors2.host_agent_processor import HostAgentProcessorV2
from ufo.module.context import Context, ContextNames


class HostAgentProcessorUsageExample:
    """
    Example class demonstrating various usage patterns for Host Agent Processor V2.
    """

    def __init__(self):
        """Initialize the usage example with logging setup."""
        self.setup_logging()

    def setup_logging(self) -> None:
        """Set up logging for the example."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("host_agent_processor_example.log"),
            ],
        )

    async def basic_usage_example(self) -> None:
        """
        Demonstrate basic usage of Host Agent Processor V2.
        """
        print("=== Basic Host Agent Processor V2 Usage ===\n")

        # Create mock context and agent
        global_context = self.create_mock_global_context()
        mock_host_agent = self.create_mock_host_agent()

        # Create processor with enhanced capabilities
        processor = HostAgentProcessorV2(mock_host_agent, global_context)

        # Print step information
        processor.print_step_info()

        # Execute processing with comprehensive error handling
        result = await processor.process()

        # Display results
        self.display_processing_results(result)

    async def error_handling_example(self) -> None:
        """
        Demonstrate error handling capabilities.
        """
        print("\n=== Error Handling Example ===\n")

        # Create context that will trigger errors
        error_context = self.create_error_context()
        mock_host_agent = self.create_mock_host_agent()

        processor = HostAgentProcessorV2(mock_host_agent, error_context)

        # Process with expected errors
        result = await processor.process()

        # Show how errors are handled
        if not result.success:
            print(f"❌ Processing failed as expected: {result.error}")
            print(f"📊 Failed at phase: {result.phase}")

        # Get metrics from middleware
        self.display_error_metrics(processor)

    async def performance_monitoring_example(self) -> None:
        """
        Demonstrate performance monitoring capabilities.
        """
        print("\n=== Performance Monitoring Example ===\n")

        global_context = self.create_mock_global_context()
        mock_host_agent = self.create_mock_host_agent()

        processor = HostAgentProcessorV2(mock_host_agent, global_context)

        # Run multiple processing cycles
        results = []
        for i in range(3):
            print(f"🔄 Running processing cycle {i + 1}/3...")
            result = await processor.process()
            results.append(result)

            # Update context for next iteration
            global_context.set("round_step", i + 1)

        # Display performance summary
        self.display_performance_summary(results, processor)

    def create_mock_global_context(self) -> Context:
        """
        Create a mock global context for testing.

        Returns:
            Context object with basic test data
        """
        context = Context()

        # Basic session information
        context.set("session_step", 1)
        context.set("round_step", 0)
        context.set("round_num", 0)
        context.set("log_path", "./test_logs/")

        # User request and planning data
        context.set(
            "request", "Open Calculator application and perform basic calculations"
        )
        context.set(
            "prev_plan",
            [
                "Identify available applications",
                "Select Calculator",
                "Perform calculations",
            ],
        )
        context.set("previous_subtasks", ["Desktop analysis"])

        # Mock command dispatcher
        context.set("command_dispatcher", MockCommandDispatcher())

        # Context names for application tracking
        context.set(ContextNames.APPLICATION_ROOT_NAME, "")
        context.set(ContextNames.APPLICATION_PROCESS_NAME, "")

        return context

    def create_error_context(self) -> Context:
        """
        Create a context that will trigger errors for testing error handling.

        Returns:
            Context object configured to trigger errors
        """
        context = self.create_mock_global_context()

        # Set flags to trigger various types of errors
        context.set("simulate_screenshot_error", True)
        context.set("simulate_app_detection_error", False)  # Let some phases succeed

        # Use error-prone command dispatcher
        context.set("command_dispatcher", ErrorProneCommandDispatcher())

        return context

    def create_mock_host_agent(self) -> "MockHostAgent":
        """
        Create a mock host agent for testing.

        Returns:
            Mock host agent instance
        """
        return MockHostAgent("test_host_agent")

    def display_processing_results(self, result) -> None:
        """
        Display processing results in a user-friendly format.

        Args:
            result: ProcessingResult object
        """
        print(
            f"🎯 Processing Result: {'✅ SUCCESS' if result.success else '❌ FAILED'}"
        )
        print(f"⏱️ Execution Time: {result.execution_time:.2f}s")

        if result.success:
            data_keys = list(result.data.keys())
            print(f"📊 Result Data Keys: {data_keys}")

            # Display specific Host Agent results
            if "selected_application_root" in result.data:
                app_root = result.data["selected_application_root"]
                print(f"🎯 Selected Application: {app_root}")

            if "assigned_third_party_agent" in result.data:
                agent_name = result.data["assigned_third_party_agent"]
                print(f"🤖 Assigned Third-Party Agent: {agent_name}")

            if "subtask" in result.data:
                subtask = result.data["subtask"]
                print(f"📝 Current Subtask: {subtask}")
        else:
            print(f"❌ Error: {result.error}")
            if result.phase:
                print(f"📍 Failed Phase: {result.phase.value}")

    def display_error_metrics(self, processor) -> None:
        """
        Display error metrics from middleware.

        Args:
            processor: Host Agent processor instance
        """
        # Find metrics middleware
        metrics_middleware = None
        for middleware in processor.middleware_chain:
            if hasattr(middleware, "get_metrics_summary"):
                metrics_middleware = middleware
                break

        if metrics_middleware:
            metrics = metrics_middleware.get_metrics_summary()
            print(f"📊 Processing Metrics:")
            for key, value in metrics.items():
                print(f"   {key}: {value}")
        else:
            print("📊 No metrics middleware found")

    def display_performance_summary(self, results, processor) -> None:
        """
        Display performance summary from multiple processing cycles.

        Args:
            results: List of ProcessingResult objects
            processor: Host Agent processor instance
        """
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        print(f"📊 Performance Summary:")
        print(f"   Total Cycles: {len(results)}")
        print(f"   Successful: {len(successful_results)}")
        print(f"   Failed: {len(failed_results)}")

        if successful_results:
            avg_time = sum(r.execution_time for r in successful_results) / len(
                successful_results
            )
            print(f"   Average Success Time: {avg_time:.2f}s")

        # Display middleware metrics
        self.display_error_metrics(processor)


class MockHostAgent:
    """Mock Host Agent for testing purposes."""

    def __init__(self, name: str):
        self.name = name
        self.step = 1
        self.blackboard = MockBlackboard()

    def get_response(self, prompt, agent_type, use_backup_engine=True):
        """Mock LLM response."""
        mock_response = {
            "observation": "I can see the desktop with various applications available.",
            "thought": "I need to analyze the available applications and select the appropriate one.",
            "current_subtask": "Select Calculator application",
            "plan": ["Open Calculator", "Perform basic calculations", "Return results"],
            "status": "CONTINUE",
            "function": "select_application_window",
            "arguments": {"id": "1", "name": "Calculator"},
        }
        return json.dumps(mock_response), 0.05

    def response_to_dict(self, response_text: str) -> Dict[str, Any]:
        """Parse response text to dictionary."""
        return json.loads(response_text)

    def message_constructor(self, **kwargs) -> Dict[str, Any]:
        """Mock message constructor."""
        return {
            "messages": [
                {"role": "user", "content": f"Mock prompt with args: {kwargs}"}
            ]
        }

    def print_response(self, response) -> None:
        """Mock response printing."""
        print(f"🤖 Host Agent Response: {response.thought}")

    def add_memory(self, memory_item) -> None:
        """Mock memory addition."""
        pass


class MockBlackboard:
    """Mock blackboard for testing."""

    def is_empty(self) -> bool:
        return True

    def blackboard_to_prompt(self) -> List[str]:
        return []

    def add_trajectories(self, trajectories) -> None:
        pass


class MockCommandDispatcher:
    """Mock command dispatcher for testing."""

    async def execute_commands(self, commands):
        """Mock command execution with realistic responses."""
        results = []

        for command in commands:
            if command.tool_name == "capture_desktop_screenshot":
                results.append(MockResult("mock_screenshot_url_12345"))
            elif command.tool_name == "get_desktop_app_info":
                results.append(
                    MockResult(
                        [
                            {"id": "1", "name": "Calculator", "kind": "application"},
                            {"id": "2", "name": "Notepad", "kind": "application"},
                        ]
                    )
                )
            elif command.tool_name == "select_application_window":
                results.append(
                    MockResult({"root_name": "Calculator", "process_name": "calc.exe"})
                )
            else:
                results.append(MockResult({"status": "success"}))

        return results


class ErrorProneCommandDispatcher(MockCommandDispatcher):
    """Command dispatcher that simulates errors for testing."""

    async def execute_commands(self, commands):
        """Mock command execution with errors."""
        for command in commands:
            if command.tool_name == "capture_desktop_screenshot":
                raise Exception("Simulated screenshot capture error")

        return await super().execute_commands(commands)


class MockResult:
    """Mock result object."""

    def __init__(self, result_data):
        self.result = result_data
        self.namespace = "mock"


async def main():
    """Run the Host Agent Processor V2 usage examples."""
    example = HostAgentProcessorUsageExample()

    # Run all examples
    await example.basic_usage_example()
    await example.error_handling_example()
    await example.performance_monitoring_example()

    print("\n✅ All examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
