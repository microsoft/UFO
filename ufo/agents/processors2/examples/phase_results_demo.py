"""
Demo of Phase Results Storage in Host Agent Processor V2

This example demonstrates how to access and use the phase results
that are stored as dictionaries during processing.
"""

import asyncio
import json
from typing import Dict, Any


# Mock classes for demonstration
class MockHostAgent:
    def __init__(self, name: str):
        self.name = name
        self.step = 1


class MockContext:
    def __init__(self):
        self._data = {
            "session_step": 1,
            "round_step": 0,
            "round_num": 0,
            "request": "Open Calculator application",
            "log_path": "./demo_logs/",
            "command_dispatcher": MockCommandDispatcher(),
        }

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value


class MockCommandDispatcher:
    async def execute_commands(self, commands):
        from ufo.contracts.contracts import Result

        return [Result(status="success", result={"mock": "data"})]


def demonstrate_phase_results_usage():
    """
    Demonstrate how to access and use phase results stored as dictionaries.
    """
    print("🔍 Host Agent Processor V2 - Phase Results Storage Demo")
    print("=" * 60)

    print("\n📋 **Phase Results Storage Features:**")
    print("   • Each processing phase result is stored in a dictionary")
    print("   • Results are accessible during and after processing")
    print("   • Comprehensive summary information available")
    print("   • Individual phase results can be queried")

    print("\n💡 **Usage Examples:**")
    print(
        """
# Basic usage - Get all phase results
processor = HostAgentProcessorV2(agent, context)
result = await processor.process()

# Access phase results from the final result
phase_results = result.data["phase_results"]  # Dict[ProcessingPhase, ProcessingResult]
phase_summary = result.data["phase_results_summary"]  # Dict[str, Any]

# Or access directly from processor
all_results = processor.get_phase_results()
summary = processor.get_phase_results_summary()

# Get specific phase result
data_collection_result = processor.get_phase_result(ProcessingPhase.DATA_COLLECTION)
llm_result = processor.get_phase_result(ProcessingPhase.LLM_INTERACTION)
"""
    )

    print("\n📊 **Phase Results Dictionary Structure:**")

    # Example of what phase results look like
    example_phase_results = {
        "data_collection": {
            "success": True,
            "execution_time": 1.25,
            "data_keys": [
                "desktop_screenshot_url",
                "target_registry",
                "application_windows_info",
            ],
            "error": None,
        },
        "llm_interaction": {
            "success": True,
            "execution_time": 2.34,
            "data_keys": ["parsed_response", "llm_cost", "subtask", "plan"],
            "error": None,
        },
        "action_execution": {
            "success": True,
            "execution_time": 0.87,
            "data_keys": ["execution_result", "selected_application_root"],
            "error": None,
        },
        "memory_update": {
            "success": True,
            "execution_time": 0.42,
            "data_keys": ["additional_memory", "memory_item"],
            "error": None,
        },
    }

    print(json.dumps(example_phase_results, indent=2, ensure_ascii=False))

    print("\n🛠️ **Practical Usage Scenarios:**")

    scenarios = [
        ("Debugging", "Check which phase failed and why"),
        ("Performance Analysis", "Analyze execution time per phase"),
        ("Data Flow Tracking", "See what data each phase produced"),
        ("Conditional Logic", "Make decisions based on previous phase results"),
        ("Error Recovery", "Retry specific phases that failed"),
        ("Metrics Collection", "Gather detailed performance metrics"),
        ("Testing", "Validate individual phase outputs"),
        ("Logging", "Create detailed execution logs"),
    ]

    for scenario, description in scenarios:
        print(f"   • **{scenario}**: {description}")

    print("\n📝 **Code Examples for Common Tasks:**")

    code_examples = {
        "Check if all phases succeeded": """
# Check if all phases completed successfully
all_results = processor.get_phase_results()
all_successful = all(result.success for result in all_results.values())
print(f"All phases successful: {all_successful}")""",
        "Get execution time breakdown": """
# Get execution time for each phase
summary = processor.get_phase_results_summary()
for phase_name, info in summary.items():
    print(f"{phase_name}: {info['execution_time']:.2f}s")""",
        "Access specific phase data": """
# Get data from a specific phase
from ufo.agents.processors2.core.processor_framework import ProcessingPhase

data_result = processor.get_phase_result(ProcessingPhase.DATA_COLLECTION)
if data_result and data_result.success:
    screenshot_url = data_result.data.get("desktop_screenshot_url")
    target_registry = data_result.data.get("target_registry")
    print(f"Screenshot: {screenshot_url}")
    print(f"Targets: {len(target_registry.targets) if target_registry else 0}")""",
        "Handle phase failures": """
# Handle specific phase failures
summary = processor.get_phase_results_summary()
failed_phases = [name for name, info in summary.items() if not info['success']]

if failed_phases:
    print(f"Failed phases: {failed_phases}")
    for phase_name in failed_phases:
        phase_info = summary[phase_name]
        print(f"  {phase_name} failed: {phase_info['error']}")""",
        "Create execution report": """
# Create detailed execution report
summary = processor.get_phase_results_summary()
total_time = sum(info['execution_time'] for info in summary.values())

report = {
    "total_execution_time": total_time,
    "successful_phases": len([info for info in summary.values() if info['success']]),
    "failed_phases": len([info for info in summary.values() if not info['success']]),
    "phase_breakdown": summary
}

print(json.dumps(report, indent=2))""",
    }

    for task, code in code_examples.items():
        print(f"\n**{task}:**")
        print(code)

    print("\n🔄 **Integration with Middleware:**")
    print(
        """
# Middleware can also access phase results
class CustomAnalysisMiddleware(ProcessorMiddleware):
    async def after_process(self, processor, result):
        # Access phase results from the final result
        phase_results = result.data.get("phase_results", {})
        
        # Analyze performance
        for phase, phase_result in phase_results.items():
            if phase_result.execution_time > 5.0:  # Slow phase threshold
                self.logger.warning(f"Slow phase detected: {phase.value} took {phase_result.execution_time:.2f}s")
        
        # Check for data quality issues
        data_result = phase_results.get(ProcessingPhase.DATA_COLLECTION)
        if data_result and "desktop_screenshot_url" not in data_result.data:
            self.logger.error("Missing screenshot URL in data collection phase")
"""
    )

    print("\n✨ **Benefits of Phase Results Storage:**")

    benefits = [
        ("**Transparency**", "Complete visibility into processing workflow"),
        ("**Debugging**", "Easy identification of failure points"),
        ("**Performance**", "Detailed timing analysis per phase"),
        ("**Flexibility**", "Access to intermediate results for custom logic"),
        ("**Monitoring**", "Real-time processing state awareness"),
        ("**Testing**", "Individual phase validation capabilities"),
        ("**Analytics**", "Rich data for performance optimization"),
        ("**Recovery**", "Ability to retry or skip specific phases"),
    ]

    for benefit, description in benefits:
        print(f"   • {benefit}: {description}")

    print("\n" + "=" * 60)
    print("🎯 **Phase Results Storage Ready for Use!**")
    print("   Access comprehensive execution data for debugging,")
    print("   analysis, and advanced processing workflows.")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_phase_results_usage()
