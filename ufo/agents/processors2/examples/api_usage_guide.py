"""
Quick Reference Guide: Using Phase Results in Host Agent Processor V2

This guide shows the essential API methods for accessing and using phase results
in your HostAgentProcessorV2 implementations.
"""

# =============================================================================
# 1. BASIC USAGE - Getting Phase Results After Processing
# =============================================================================

# After processing is complete, access phase results:
"""
from ufo.agents.processors2.host_agent_processor import HostAgentProcessorV2

# Initialize and process
processor = HostAgentProcessorV2(host_agent, global_context)
result = await processor.process()

# Access all phase results
all_phase_results = processor.get_phase_results()
for phase, phase_result in all_phase_results.items():
    print(f"{phase.value}: {phase_result.success}")

# Get summary of all phases
summary = processor.get_phase_results_summary()
print(summary)

# Get specific phase result
data_collection_result = processor.get_phase_result(ProcessingPhase.DATA_COLLECTION)
if data_collection_result:
    print(f"Found {len(data_collection_result.data.get('applications_found', []))} apps")
"""

# =============================================================================
# 2. ERROR HANDLING - Check Phase Success Before Continuing
# =============================================================================

"""
# Check if critical phases completed successfully
critical_phases = [ProcessingPhase.DATA_COLLECTION, ProcessingPhase.LLM_INTERACTION]
for phase in critical_phases:
    phase_result = processor.get_phase_result(phase)
    if not phase_result or not phase_result.success:
        logger.error(f"Critical phase {phase.value} failed: {phase_result.error if phase_result else 'Not executed'}")
        # Implement fallback or early return
        return create_error_response(f"Failed at {phase.value}")

# Non-critical phase failures are okay to continue
memory_result = processor.get_phase_result(ProcessingPhase.MEMORY_UPDATE)
if memory_result and not memory_result.success:
    logger.warning(f"Memory update failed, continuing with fallback: {memory_result.error}")
"""

# =============================================================================
# 3. PERFORMANCE MONITORING - Track Execution Times
# =============================================================================

"""
# Monitor execution times for optimization
all_results = processor.get_phase_results()
total_time = sum(result.execution_time for result in all_results.values())
logger.info(f"Total processing time: {total_time:.2f}s")

# Find slowest phase
slowest_phase = max(all_results.items(), key=lambda x: x[1].execution_time)
logger.info(f"Slowest phase: {slowest_phase[0].value} ({slowest_phase[1].execution_time:.2f}s)")

# Alert if any phase takes too long
for phase, result in all_results.items():
    if result.execution_time > 5.0:  # 5 second threshold
        logger.warning(f"Phase {phase.value} took {result.execution_time:.2f}s - consider optimization")
"""

# =============================================================================
# 4. DATA FLOW ANALYSIS - Use Previous Phase Results
# =============================================================================

"""
# Use data from previous phases for decision making
data_collection = processor.get_phase_result(ProcessingPhase.DATA_COLLECTION)
llm_interaction = processor.get_phase_result(ProcessingPhase.LLM_INTERACTION)

if data_collection and llm_interaction:
    # Get available applications from data collection
    available_apps = [app['name'] for app in data_collection.data.get('applications_found', [])]
    
    # Get LLM's selected target
    target_app = llm_interaction.data.get('llm_response', {}).get('target')
    
    # Validate LLM selection against available data
    if target_app not in available_apps:
        logger.warning(f"LLM selected unavailable app '{target_app}'. Available: {available_apps}")
        # Implement recovery logic
"""

# =============================================================================
# 5. COST TRACKING - Monitor LLM Usage
# =============================================================================

"""
# Track LLM costs and token usage
llm_result = processor.get_phase_result(ProcessingPhase.LLM_INTERACTION)
if llm_result and llm_result.success:
    cost = llm_result.data.get('total_cost', 0)
    tokens = llm_result.data.get('prompt_tokens', 0) + llm_result.data.get('completion_tokens', 0)
    
    logger.info(f"LLM Usage - Cost: ${cost:.4f}, Tokens: {tokens}")
    
    # Alert on high costs
    if cost > 0.10:  # 10 cents threshold
        logger.warning(f"High LLM cost: ${cost:.4f} - consider prompt optimization")
"""

# =============================================================================
# 6. DEBUGGING - Detailed Phase Information
# =============================================================================

"""
# Get detailed information for debugging
summary = processor.get_phase_results_summary()
logger.debug("Phase Results Summary:")
for phase_name, phase_info in summary.items():
    status = "SUCCESS" if phase_info['success'] else "FAILED" 
    logger.debug(f"  {phase_name}: {status} ({phase_info['execution_time']:.2f}s)")
    
    if not phase_info['success'] and phase_info['error']:
        logger.debug(f"    Error: {phase_info['error']}")
    
    logger.debug(f"    Data keys: {phase_info['data_keys']}")

# Access raw phase result data for debugging
action_result = processor.get_phase_result(ProcessingPhase.ACTION_EXECUTION)
if action_result:
    logger.debug(f"Action execution details: {action_result.data}")
    logger.debug(f"Action metadata: {action_result.metadata}")
"""

# =============================================================================
# 7. WORKFLOW CONTROL - Conditional Logic Based on Results
# =============================================================================

"""
# Implement conditional workflow logic
def should_continue_workflow(processor: HostAgentProcessorV2) -> tuple[bool, str]:
    '''
    Determine if workflow should continue based on phase results.
    Returns: (should_continue, reason)
    '''
    
    # Check critical phases
    data_result = processor.get_phase_result(ProcessingPhase.DATA_COLLECTION)
    if not data_result or not data_result.success:
        return False, "Data collection failed"
    
    llm_result = processor.get_phase_result(ProcessingPhase.LLM_INTERACTION)
    if not llm_result or not llm_result.success:
        return False, "LLM interaction failed"
    
    # Check LLM confidence
    confidence = llm_result.data.get('confidence_score', 0)
    if confidence < 0.7:  # 70% threshold
        return False, f"LLM confidence too low: {confidence:.0%}"
    
    action_result = processor.get_phase_result(ProcessingPhase.ACTION_EXECUTION)
    if not action_result or not action_result.success:
        return False, "Action execution failed"
    
    return True, "All critical phases completed successfully"

# Usage:
can_continue, reason = should_continue_workflow(processor)
if not can_continue:
    logger.error(f"Workflow stopped: {reason}")
    return create_error_response(reason)
else:
    logger.info(f"Workflow continuing: {reason}")
"""

# =============================================================================
# 8. CUSTOM ANALYTICS - Build Reports from Phase Data
# =============================================================================

"""
def generate_execution_report(processor: HostAgentProcessorV2) -> dict:
    '''Generate custom execution report from phase results.'''
    
    all_results = processor.get_phase_results()
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'execution_summary': {
            'total_phases': len(all_results),
            'successful_phases': sum(1 for r in all_results.values() if r.success),
            'total_time': sum(r.execution_time for r in all_results.values()),
            'overall_success': all(r.success for r in all_results.values())
        },
        'phase_details': {},
        'performance_metrics': {},
        'cost_analysis': {}
    }
    
    # Add phase-specific details
    for phase, result in all_results.items():
        report['phase_details'][phase.value] = {
            'success': result.success,
            'execution_time': result.execution_time,
            'data_keys': list(result.data.keys()),
            'error': result.error
        }
    
    # Add LLM cost analysis
    llm_result = processor.get_phase_result(ProcessingPhase.LLM_INTERACTION)
    if llm_result and llm_result.success:
        report['cost_analysis'] = {
            'llm_cost': llm_result.data.get('total_cost', 0),
            'tokens_used': (llm_result.data.get('prompt_tokens', 0) + 
                          llm_result.data.get('completion_tokens', 0)),
            'model': llm_result.data.get('model_used', 'unknown')
        }
    
    return report

# Usage:
report = generate_execution_report(processor)
logger.info(f"Execution report generated: {report['execution_summary']}")
"""

# =============================================================================
# 9. INTEGRATION EXAMPLE - Complete Workflow
# =============================================================================

"""
async def process_with_phase_monitoring(host_agent, global_context):
    '''Complete example of processing with phase result monitoring.'''
    
    processor = HostAgentProcessorV2(host_agent, global_context)
    
    try:
        # Execute processing
        logger.info("Starting Host Agent processing...")
        result = await processor.process()
        
        # Check overall result
        if not result.get('success', False):
            logger.error(f"Processing failed: {result.get('error', 'Unknown error')}")
            return result
        
        # Analyze phase results
        logger.info("Analyzing phase results...")
        
        # Performance check
        total_time = sum(r.execution_time for r in processor.get_phase_results().values())
        if total_time > 10.0:  # 10 second threshold
            logger.warning(f"Processing took {total_time:.2f}s - performance review needed")
        
        # Cost check
        llm_result = processor.get_phase_result(ProcessingPhase.LLM_INTERACTION)
        if llm_result:
            cost = llm_result.data.get('total_cost', 0)
            if cost > 0.05:  # 5 cents threshold
                logger.warning(f"High LLM cost: ${cost:.4f}")
        
        # Validate workflow completion
        can_continue, reason = should_continue_workflow(processor)
        if not can_continue:
            logger.error(f"Workflow validation failed: {reason}")
            return {'success': False, 'error': f'Validation failed: {reason}'}
        
        # Generate analytics
        report = generate_execution_report(processor)
        logger.info(f"Processing completed successfully in {report['execution_summary']['total_time']:.2f}s")
        
        # Add phase results to response
        result['phase_results_summary'] = processor.get_phase_results_summary()
        result['execution_report'] = report
        
        return result
        
    except Exception as e:
        logger.error(f"Processing failed with exception: {e}")
        
        # Even on failure, try to get partial phase results
        try:
            partial_results = processor.get_phase_results_summary()
            logger.info(f"Partial results available: {list(partial_results.keys())}")
        except:
            logger.warning("No partial results available")
        
        raise
"""

print("📖 Phase Results API Quick Reference")
print("=" * 50)
print("✅ Copy the examples above to use phase results in your code")
print(
    "🔍 Key methods: get_phase_results(), get_phase_result(), get_phase_results_summary()"
)
print(
    "📊 Use cases: Debugging, Performance monitoring, Cost tracking, Workflow control"
)
print("=" * 50)
