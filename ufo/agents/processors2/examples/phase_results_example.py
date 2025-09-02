"""
Real-world example showing how to use phase results storage in Host Agent Processor V2.

This example demonstrates practical usage patterns for accessing and analyzing
the results from each processing phase.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from ufo.agents.processors2.core.processor_framework import (
    ProcessingPhase,
    ProcessingResult,
)

# Configure logging
logging.basicConfig(level=logging.INFO)


async def example_processing_with_phase_results():
    """
    Example showing how to process with phase results analysis.
    """
    print("🔬 Real-world Phase Results Usage Example")
    print("=" * 50)

    # This would be your actual processor initialization
    # processor = HostAgentProcessorV2(host_agent, global_context)
    # result = await processor.process()

    # For demo purposes, we'll simulate the result structure
    simulated_result = create_simulated_processing_result()

    print("\n1. 📊 **Analyzing Overall Processing Result:**")
    analyze_overall_result(simulated_result)

    print("\n2. 🔍 **Examining Individual Phase Results:**")
    analyze_phase_results(simulated_result)

    print("\n3. 🎯 **Performance Analysis:**")
    analyze_performance(simulated_result)

    print("\n4. 📈 **Creating Custom Reports:**")
    create_custom_report(simulated_result)

    print("\n5. 🛠️ **Error Handling with Phase Results:**")
    handle_phase_errors(simulated_result)


def create_simulated_processing_result() -> Dict[str, Any]:
    """Create simulated processing result with phase results."""

    # Simulate phase results (this would come from actual processing)
    phase_results = {}

    # Data Collection Phase Result
    phase_results[ProcessingPhase.DATA_COLLECTION] = ProcessingResult(
        success=True,
        data={
            "desktop_screenshot_url": "screenshot_12345.png",
            "target_registry": {"targets_count": 8},
            "application_windows_info": [
                {"id": "1", "name": "Calculator", "kind": "application"},
                {"id": "2", "name": "Notepad", "kind": "application"},
            ],
        },
        phase=ProcessingPhase.DATA_COLLECTION,
        execution_time=1.25,
    )

    # LLM Interaction Phase Result
    phase_results[ProcessingPhase.LLM_INTERACTION] = ProcessingResult(
        success=True,
        data={
            "parsed_response": {
                "status": "CONTINUE",
                "function": "select_application_window",
            },
            "llm_cost": 0.034,
            "subtask": "Select Calculator application",
            "plan": ["Open Calculator", "Perform calculations"],
        },
        phase=ProcessingPhase.LLM_INTERACTION,
        execution_time=2.34,
    )

    # Action Execution Phase Result
    phase_results[ProcessingPhase.ACTION_EXECUTION] = ProcessingResult(
        success=True,
        data={
            "execution_result": [
                {"status": "success", "result": {"root_name": "Calculator"}}
            ],
            "selected_application_root": "Calculator",
            "selected_target_id": "1",
        },
        phase=ProcessingPhase.ACTION_EXECUTION,
        execution_time=0.87,
    )

    # Memory Update Phase Result
    phase_results[ProcessingPhase.MEMORY_UPDATE] = ProcessingResult(
        success=True,
        data={
            "additional_memory": {"Agent": "HostAgent", "Cost": 0.034},
            "memory_item": {"keys_count": 15},
        },
        phase=ProcessingPhase.MEMORY_UPDATE,
        execution_time=0.42,
    )

    # Create phase results summary
    phase_results_summary = {}
    for phase, result in phase_results.items():
        phase_results_summary[phase.value] = {
            "success": result.success,
            "execution_time": result.execution_time,
            "data_keys": list(result.data.keys()),
            "error": result.error,
        }

    return {
        "success": True,
        "execution_time": 4.88,
        "data": {
            "phase_results": phase_results,
            "phase_results_summary": phase_results_summary,
            "selected_application_root": "Calculator",
            "subtask": "Select Calculator application",
        },
    }


def analyze_overall_result(result: Dict[str, Any]) -> None:
    """Analyze the overall processing result."""

    success = result["success"]
    total_time = result["execution_time"]

    print(f"   ✅ Overall Success: {success}")
    print(f"   ⏱️  Total Execution Time: {total_time:.2f}s")

    if "phase_results" in result["data"]:
        phase_results = result["data"]["phase_results"]
        total_phases = len(phase_results)
        successful_phases = sum(1 for pr in phase_results.values() if pr.success)

        print(f"   📊 Phases Completed: {successful_phases}/{total_phases}")

        if successful_phases < total_phases:
            failed_phases = [
                phase.value for phase, pr in phase_results.items() if not pr.success
            ]
            print(f"   ❌ Failed Phases: {failed_phases}")


def analyze_phase_results(result: Dict[str, Any]) -> None:
    """Analyze individual phase results."""

    phase_results = result["data"].get("phase_results", {})

    for phase, phase_result in phase_results.items():
        phase_name = phase.value
        success_icon = "✅" if phase_result.success else "❌"

        print(f"   {success_icon} **{phase_name.title()}**:")
        print(f"      Duration: {phase_result.execution_time:.2f}s")
        print(f"      Data Keys: {list(phase_result.data.keys())}")

        # Show specific important data for each phase
        if phase == ProcessingPhase.DATA_COLLECTION:
            targets = len(phase_result.data.get("application_windows_info", []))
            print(f"      Applications Found: {targets}")

        elif phase == ProcessingPhase.LLM_INTERACTION:
            cost = phase_result.data.get("llm_cost", 0)
            subtask = phase_result.data.get("subtask", "N/A")
            print(f"      LLM Cost: ${cost:.4f}")
            print(f"      Current Subtask: {subtask}")

        elif phase == ProcessingPhase.ACTION_EXECUTION:
            selected_app = phase_result.data.get("selected_application_root", "N/A")
            print(f"      Selected Application: {selected_app}")

        elif phase == ProcessingPhase.MEMORY_UPDATE:
            memory_keys = phase_result.data.get("memory_item", {}).get("keys_count", 0)
            print(f"      Memory Keys Stored: {memory_keys}")

        if not phase_result.success and phase_result.error:
            print(f"      ❌ Error: {phase_result.error}")

        print()


def analyze_performance(result: Dict[str, Any]) -> None:
    """Analyze performance metrics from phase results."""

    phase_results = result["data"].get("phase_results", {})

    # Calculate timing statistics
    execution_times = [pr.execution_time for pr in phase_results.values()]
    total_time = sum(execution_times)
    avg_time = total_time / len(execution_times) if execution_times else 0

    print(f"   📈 Performance Metrics:")
    print(f"      Total Time: {total_time:.2f}s")
    print(f"      Average Phase Time: {avg_time:.2f}s")

    # Find slowest and fastest phases
    if phase_results:
        slowest_phase = max(phase_results.items(), key=lambda x: x[1].execution_time)
        fastest_phase = min(phase_results.items(), key=lambda x: x[1].execution_time)

        print(
            f"      Slowest Phase: {slowest_phase[0].value} ({slowest_phase[1].execution_time:.2f}s)"
        )
        print(
            f"      Fastest Phase: {fastest_phase[0].value} ({fastest_phase[1].execution_time:.2f}s)"
        )

    # Performance recommendations
    print(f"\n   💡 Performance Insights:")
    for phase, phase_result in phase_results.items():
        if phase_result.execution_time > 2.0:
            print(
                f"      • {phase.value} is taking longer than expected ({phase_result.execution_time:.2f}s)"
            )
        elif phase_result.execution_time < 0.1:
            print(
                f"      • {phase.value} completed very quickly ({phase_result.execution_time:.2f}s)"
            )


def create_custom_report(result: Dict[str, Any]) -> None:
    """Create a custom execution report."""

    phase_summary = result["data"].get("phase_results_summary", {})

    # Create structured report
    report = {
        "execution_summary": {
            "overall_success": result["success"],
            "total_execution_time": result["execution_time"],
            "timestamp": "2025-09-02T10:30:00Z",
        },
        "phase_breakdown": {},
        "recommendations": [],
    }

    # Process each phase
    for phase_name, phase_info in phase_summary.items():
        report["phase_breakdown"][phase_name] = {
            "status": "SUCCESS" if phase_info["success"] else "FAILED",
            "duration_ms": int(phase_info["execution_time"] * 1000),
            "output_data_count": len(phase_info["data_keys"]),
            "key_outputs": phase_info["data_keys"][:3],  # Top 3 outputs
        }

        # Add recommendations based on phase performance
        if phase_info["execution_time"] > 3.0:
            report["recommendations"].append(
                f"Consider optimizing {phase_name} - execution time exceeded 3.0s"
            )

    print("   📋 Custom Execution Report:")
    import json

    print(json.dumps(report, indent=6, ensure_ascii=False))


def handle_phase_errors(result: Dict[str, Any]) -> None:
    """Demonstrate error handling using phase results."""

    phase_results = result["data"].get("phase_results", {})

    print("   🔧 Error Handling Strategies:")

    # Check for any failed phases
    failed_phases = [phase for phase, pr in phase_results.items() if not pr.success]

    if not failed_phases:
        print("      ✅ No errors detected - all phases completed successfully")
        return

    # Handle different types of phase failures
    for failed_phase in failed_phases:
        phase_result = phase_results[failed_phase]
        error_message = phase_result.error or "Unknown error"

        print(f"      ❌ {failed_phase.value} failed: {error_message}")

        # Suggest recovery actions based on phase type
        if failed_phase == ProcessingPhase.DATA_COLLECTION:
            print("         💡 Recovery: Retry screenshot capture or use cached data")

        elif failed_phase == ProcessingPhase.LLM_INTERACTION:
            print("         💡 Recovery: Try backup LLM engine or use simpler prompt")

        elif failed_phase == ProcessingPhase.ACTION_EXECUTION:
            print(
                "         💡 Recovery: Fallback to manual action or alternative target"
            )

        elif failed_phase == ProcessingPhase.MEMORY_UPDATE:
            print("         💡 Recovery: Continue without memory update (non-critical)")

    # Show what data is still available from successful phases
    successful_phases = [phase for phase, pr in phase_results.items() if pr.success]
    if successful_phases:
        print(f"      📊 Available data from successful phases:")
        for phase in successful_phases:
            data_keys = list(phase_results[phase].data.keys())
            print(
                f"         • {phase.value}: {data_keys[:3]}{'...' if len(data_keys) > 3 else ''}"
            )


async def main():
    """Run the example."""
    await example_processing_with_phase_results()

    print("\n" + "=" * 50)
    print("🎉 Phase Results Storage Example Complete!")
    print("   Use these patterns to analyze and debug")
    print("   your Host Agent Processor executions.")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
