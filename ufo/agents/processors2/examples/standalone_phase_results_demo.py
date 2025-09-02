"""
Standalone demonstration of phase results storage functionality.

This example works independently and shows how to use the phase results
storage feature without requiring full UFO dependencies.
"""

import asyncio
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional

# Standalone definitions for demonstration
class ProcessingPhase(Enum):
    """Enumeration of processing phases."""
    DATA_COLLECTION = "data_collection"
    LLM_INTERACTION = "llm_interaction" 
    ACTION_EXECUTION = "action_execution"
    MEMORY_UPDATE = "memory_update"

@dataclass
class ProcessingResult:
    """Result from a processing phase."""
    success: bool
    data: Dict[str, Any]
    phase: ProcessingPhase
    execution_time: float = 0.0
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def demonstrate_phase_results_usage():
    """
    Comprehensive demonstration of phase results storage and usage patterns.
    """
    print("🔬 Phase Results Storage - Standalone Demo")
    print("=" * 60)
    
    # Create simulated phase results
    phase_results = create_sample_phase_results()
    
    print("\n1. 📊 **Accessing Individual Phase Results:**")
    demonstrate_phase_access(phase_results)
    
    print("\n2. 🔍 **Debugging with Phase Data:**")
    demonstrate_debugging(phase_results)
    
    print("\n3. 📈 **Performance Analytics:**")
    demonstrate_performance_analysis(phase_results)
    
    print("\n4. 🛠️ **Error Analysis and Recovery:**")
    demonstrate_error_handling(phase_results)
    
    print("\n5. 📋 **Workflow Control Based on Results:**")
    demonstrate_workflow_control(phase_results)

def create_sample_phase_results() -> Dict[ProcessingPhase, ProcessingResult]:
    """Create sample phase results for demonstration."""
    
    results = {}
    
    # Data Collection - Success
    results[ProcessingPhase.DATA_COLLECTION] = ProcessingResult(
        success=True,
        phase=ProcessingPhase.DATA_COLLECTION,
        execution_time=1.45,
        data={
            "screenshot_path": "screenshots/desktop_20250902_103045.png",
            "applications_found": [
                {"name": "Calculator", "pid": 1234, "position": {"x": 100, "y": 50}},
                {"name": "Notepad", "pid": 5678, "position": {"x": 300, "y": 150}},
                {"name": "VS Code", "pid": 9012, "position": {"x": 500, "y": 200}}
            ],
            "ui_elements_count": 47,
            "accessibility_tree_depth": 5
        },
        metadata={
            "screenshot_resolution": "1920x1080",
            "capture_method": "win32_screenshot",
            "processing_duration": 0.12
        }
    )
    
    # LLM Interaction - Success
    results[ProcessingPhase.LLM_INTERACTION] = ProcessingResult(
        success=True,
        phase=ProcessingPhase.LLM_INTERACTION,
        execution_time=2.78,
        data={
            "llm_response": {
                "action": "click",
                "target": "Calculator",
                "reasoning": "User requested to open calculator for mathematical operations"
            },
            "prompt_tokens": 1250,
            "completion_tokens": 89,
            "total_cost": 0.0345,
            "model_used": "gpt-4-turbo",
            "confidence_score": 0.92
        },
        metadata={
            "api_endpoint": "openai",
            "temperature": 0.1,
            "retry_count": 0
        }
    )
    
    # Action Execution - Partial Success
    results[ProcessingPhase.ACTION_EXECUTION] = ProcessingResult(
        success=True,
        phase=ProcessingPhase.ACTION_EXECUTION,
        execution_time=1.23,
        data={
            "executed_action": "click",
            "target_element": {
                "name": "Calculator",
                "coordinates": {"x": 100, "y": 50},
                "element_type": "application_window"
            },
            "execution_status": "success",
            "window_state_after": "active",
            "screenshot_after": "screenshots/after_action_20250902_103048.png"
        },
        metadata={
            "automation_tool": "pyautogui",
            "click_duration": 0.05,
            "verification_passed": True
        }
    )
    
    # Memory Update - Failed (for demonstration)
    results[ProcessingPhase.MEMORY_UPDATE] = ProcessingResult(
        success=False,
        phase=ProcessingPhase.MEMORY_UPDATE,
        execution_time=0.67,
        error="Database connection timeout after 30 seconds",
        data={
            "attempted_updates": [
                {"key": "last_action", "value": "click_calculator"},
                {"key": "current_application", "value": "Calculator"},
                {"key": "session_actions_count", "value": 15}
            ],
            "successful_updates": 0,
            "failed_updates": 3
        },
        metadata={
            "database_type": "sqlite",
            "connection_attempts": 3,
            "fallback_memory_used": True
        }
    )
    
    return results

def demonstrate_phase_access(phase_results: Dict[ProcessingPhase, ProcessingResult]):
    """Show how to access individual phase results."""
    
    for phase, result in phase_results.items():
        status_emoji = "✅" if result.success else "❌"
        print(f"   {status_emoji} **{phase.value.replace('_', ' ').title()}** ({result.execution_time:.2f}s)")
        
        # Show key data points
        print(f"      📊 Data keys: {list(result.data.keys())}")
        
        if result.metadata:
            print(f"      🏷️  Metadata: {list(result.metadata.keys())}")
        
        # Phase-specific insights
        if phase == ProcessingPhase.DATA_COLLECTION:
            apps_count = len(result.data.get("applications_found", []))
            ui_elements = result.data.get("ui_elements_count", 0)
            print(f"      📱 Found {apps_count} applications, {ui_elements} UI elements")
            
        elif phase == ProcessingPhase.LLM_INTERACTION:
            cost = result.data.get("total_cost", 0)
            confidence = result.data.get("confidence_score", 0)
            print(f"      💰 Cost: ${cost:.4f}, Confidence: {confidence:.0%}")
            
        elif phase == ProcessingPhase.ACTION_EXECUTION:
            action = result.data.get("executed_action", "N/A")
            status = result.data.get("execution_status", "N/A")
            print(f"      🎯 Action: {action}, Status: {status}")
            
        elif phase == ProcessingPhase.MEMORY_UPDATE:
            if result.success:
                updates = len(result.data.get("attempted_updates", []))
                print(f"      💾 Memory updates: {updates}")
            else:
                print(f"      ⚠️  Error: {result.error}")
        
        print()

def demonstrate_debugging(phase_results: Dict[ProcessingPhase, ProcessingResult]):
    """Show debugging capabilities with phase results."""
    
    print("   🐛 Debugging Information:")
    
    # Overall execution timeline
    total_time = sum(result.execution_time for result in phase_results.values())
    print(f"      ⏱️  Total execution time: {total_time:.2f}s")
    
    # Phase timing breakdown
    print(f"      📊 Phase timing breakdown:")
    for phase, result in phase_results.items():
        percentage = (result.execution_time / total_time) * 100
        print(f"         • {phase.value}: {result.execution_time:.2f}s ({percentage:.1f}%)")
    
    # Data flow analysis
    print(f"\n      🔄 Data Flow Analysis:")
    
    # Check data dependencies between phases
    data_collection_result = phase_results[ProcessingPhase.DATA_COLLECTION]
    llm_result = phase_results[ProcessingPhase.LLM_INTERACTION]
    
    apps_found = len(data_collection_result.data.get("applications_found", []))
    target_app = llm_result.data.get("llm_response", {}).get("target", "Unknown")
    
    print(f"         • Data Collection found {apps_found} applications")
    print(f"         • LLM selected '{target_app}' as target")
    
    # Verify data consistency
    available_apps = [app["name"] for app in data_collection_result.data.get("applications_found", [])]
    if target_app in available_apps:
        print(f"         ✅ Target application '{target_app}' was available")
    else:
        print(f"         ❌ Target application '{target_app}' was not found in available apps")

def demonstrate_performance_analysis(phase_results: Dict[ProcessingPhase, ProcessingResult]):
    """Analyze performance metrics from phase results."""
    
    print("   📈 Performance Analysis:")
    
    # Execution time analysis
    execution_times = [(phase.value, result.execution_time) for phase, result in phase_results.items()]
    execution_times.sort(key=lambda x: x[1], reverse=True)
    
    print(f"      🏃 Phase execution ranking (slowest to fastest):")
    for i, (phase_name, time) in enumerate(execution_times, 1):
        print(f"         {i}. {phase_name.replace('_', ' ').title()}: {time:.2f}s")
    
    # Resource usage analysis
    print(f"\n      💾 Resource Usage:")
    
    # LLM costs
    llm_result = phase_results[ProcessingPhase.LLM_INTERACTION]
    if llm_result.success:
        cost = llm_result.data.get("total_cost", 0)
        tokens = (llm_result.data.get("prompt_tokens", 0) + 
                 llm_result.data.get("completion_tokens", 0))
        print(f"         💰 LLM Cost: ${cost:.4f} ({tokens} tokens)")
    
    # Storage usage
    data_collection_result = phase_results[ProcessingPhase.DATA_COLLECTION]
    screenshots = [key for key in data_collection_result.data if "screenshot" in key.lower()]
    if screenshots:
        print(f"         📸 Screenshots captured: {len(screenshots)}")
    
    # Performance recommendations
    print(f"\n      💡 Performance Recommendations:")
    
    # Identify slow phases
    avg_time = sum(result.execution_time for result in phase_results.values()) / len(phase_results)
    for phase, result in phase_results.items():
        if result.execution_time > avg_time * 1.5:
            print(f"         • Consider optimizing {phase.value} (above average time)")
    
    # Cost optimization
    llm_result = phase_results[ProcessingPhase.LLM_INTERACTION]
    if llm_result.success and llm_result.data.get("total_cost", 0) > 0.05:
        print(f"         • LLM costs are high - consider prompt optimization")

def demonstrate_error_handling(phase_results: Dict[ProcessingPhase, ProcessingResult]):
    """Demonstrate error handling using phase results."""
    
    print("   🛠️ Error Analysis and Recovery:")
    
    # Find failed phases
    failed_phases = [(phase, result) for phase, result in phase_results.items() if not result.success]
    successful_phases = [(phase, result) for phase, result in phase_results.items() if result.success]
    
    if not failed_phases:
        print("      ✅ No errors detected - all phases completed successfully")
    else:
        print(f"      ❌ Failed phases: {len(failed_phases)}/{len(phase_results)}")
        
        for phase, result in failed_phases:
            print(f"\n         🔧 {phase.value.replace('_', ' ').title()} Failure Analysis:")
            print(f"            Error: {result.error}")
            print(f"            Execution time: {result.execution_time:.2f}s")
            
            # Show partial data if available
            if result.data:
                print(f"            Partial data available: {list(result.data.keys())}")
                
                # Specific error analysis for memory update
                if phase == ProcessingPhase.MEMORY_UPDATE:
                    attempted = len(result.data.get("attempted_updates", []))
                    successful = result.data.get("successful_updates", 0)
                    print(f"            Updates attempted: {attempted}, successful: {successful}")
            
            # Suggest recovery strategies
            print(f"            💡 Recovery strategies:")
            if phase == ProcessingPhase.MEMORY_UPDATE:
                print(f"               • Continue with in-memory storage")
                print(f"               • Retry database connection later")
                print(f"               • Use fallback storage mechanism")
    
    # Show impact assessment
    if failed_phases:
        print(f"\n      📊 Impact Assessment:")
        critical_failures = [p for p, r in failed_phases if p in [ProcessingPhase.DATA_COLLECTION, ProcessingPhase.LLM_INTERACTION]]
        non_critical_failures = [p for p, r in failed_phases if p not in critical_failures]
        
        if critical_failures:
            critical_names = [p.value for p in critical_failures]
            print(f"         ⚠️  Critical failures: {critical_names} - workflow cannot continue")
        
        if non_critical_failures:
            non_critical_names = [p.value for p in non_critical_failures]
            print(f"         📝 Non-critical failures: {non_critical_names} - workflow can continue")

def demonstrate_workflow_control(phase_results: Dict[ProcessingPhase, ProcessingResult]):
    """Show how to use phase results for workflow control."""
    
    print("   🔄 Workflow Control Based on Phase Results:")
    
    # Analyze workflow state
    data_collection = phase_results[ProcessingPhase.DATA_COLLECTION]
    llm_interaction = phase_results[ProcessingPhase.LLM_INTERACTION]
    action_execution = phase_results[ProcessingPhase.ACTION_EXECUTION]
    memory_update = phase_results[ProcessingPhase.MEMORY_UPDATE]
    
    print(f"      🎯 Workflow Decision Tree:")
    
    # Decision logic based on results
    if not data_collection.success:
        print(f"         ❌ Cannot proceed - data collection failed")
        print(f"            → Recommend: Retry data collection or use cached data")
        return
    
    print(f"         ✅ Data collection successful - proceeding to analysis")
    
    if not llm_interaction.success:
        print(f"         ❌ LLM interaction failed")
        print(f"            → Recommend: Use fallback action or manual intervention")
        return
    
    # Check LLM confidence
    confidence = llm_interaction.data.get("confidence_score", 0)
    if confidence < 0.8:
        print(f"         ⚠️  LLM confidence low ({confidence:.0%})")
        print(f"            → Recommend: Request user confirmation before action")
    else:
        print(f"         ✅ LLM confidence high ({confidence:.0%}) - safe to proceed")
    
    if not action_execution.success:
        print(f"         ❌ Action execution failed")
        print(f"            → Recommend: Retry with alternative method")
        return
    
    print(f"         ✅ Action executed successfully")
    
    # Memory update is non-critical
    if not memory_update.success:
        print(f"         ⚠️  Memory update failed (non-critical)")
        print(f"            → Action: Continue workflow, fix memory in background")
    else:
        print(f"         ✅ Memory updated - full workflow completed successfully")
    
    # Next steps based on current state
    print(f"\n      🚀 Recommended Next Steps:")
    if all(result.success for result in [data_collection, llm_interaction, action_execution]):
        print(f"         • Workflow ready for next iteration")
        print(f"         • Continue with next user task")
        if not memory_update.success:
            print(f"         • Schedule memory sync in background")
    else:
        print(f"         • Review failed phases and implement recovery")
        print(f"         • Consider workflow rollback if necessary")

async def main():
    """Run the demonstration."""
    await demonstrate_phase_results_usage()
    
    print("\n" + "=" * 60)
    print("🎉 Phase Results Storage Demo Complete!")
    print()
    print("Key Benefits Demonstrated:")
    print("• 🔍 Granular debugging capabilities")  
    print("• 📊 Performance analysis and optimization")
    print("• 🛠️ Intelligent error handling and recovery")
    print("• 🔄 Dynamic workflow control")
    print("• 📈 Resource usage tracking")
    print()
    print("Use these patterns in your HostAgentProcessor implementations!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
