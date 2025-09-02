"""
Phase Results 按顺序访问 - API使用指南

本指南展示如何使用新的按顺序访问phase results的功能
"""

# =============================================================================
# 1. 基础用法 - 获取按执行顺序的Phase Results
# =============================================================================

"""
# 初始化和处理
processor = HostAgentProcessorV2(host_agent, global_context)
result = await processor.process()

# 方法1：获取OrderedDict格式的所有结果（保持插入顺序）
ordered_results = processor.get_phase_results()
for phase, result in ordered_results.items():
    print(f"Phase: {phase.value}, Success: {result.success}")

# 方法2：获取按顺序的(phase, result)元组列表
results_in_order = processor.get_phase_results_in_order()
for i, (phase, result) in enumerate(results_in_order):
    print(f"Step {i+1}: {phase.value} ({result.execution_time:.2f}s)")

# 方法3：只获取执行顺序的阶段列表
execution_order = processor.get_phase_execution_order()
print(f"Execution order: {[phase.value for phase in execution_order]}")
"""

# =============================================================================
# 2. 流程分析 - 基于执行顺序分析处理流程
# =============================================================================

"""
def analyze_processing_flow(processor: HostAgentProcessorV2):
    '''分析处理流程，按执行顺序检查各阶段'''
    
    results_in_order = processor.get_phase_results_in_order()
    
    print("🔍 Processing Flow Analysis:")
    
    for i, (phase, result) in enumerate(results_in_order):
        status_emoji = "✅" if result.success else "❌"
        step_type = "First" if i == 0 else "Last" if i == len(results_in_order) - 1 else f"Step {i+1}"
        
        print(f"  {status_emoji} {step_type}: {phase.value}")
        print(f"     Duration: {result.execution_time:.2f}s")
        
        if not result.success:
            print(f"     Error: {result.error}")
            break  # 分析失败点
    
    # 计算总执行时间
    total_time = sum(result.execution_time for _, result in results_in_order)
    print(f"  ⏱️ Total execution time: {total_time:.2f}s")
"""

# =============================================================================
# 3. 数据依赖检查 - 验证阶段间的数据传递
# =============================================================================

"""
def check_data_dependencies(processor: HostAgentProcessorV2):
    '''检查阶段间的数据依赖关系'''
    
    results_in_order = processor.get_phase_results_in_order()
    
    print("🔗 Data Dependencies Check:")
    
    for i in range(len(results_in_order) - 1):
        current_phase, current_result = results_in_order[i]
        next_phase, next_result = results_in_order[i + 1]
        
        print(f"  {current_phase.value} → {next_phase.value}")
        
        # 检查关键数据传递
        if current_phase == ProcessingPhase.DATA_COLLECTION:
            apps_found = len(current_result.data.get('applications_found', []))
            if apps_found > 0:
                print(f"    ✅ Provides {apps_found} applications for next phase")
            else:
                print(f"    ⚠️ No applications found for next phase")
        
        elif current_phase == ProcessingPhase.LLM_INTERACTION:
            confidence = current_result.data.get('confidence_score', 0)
            target = current_result.data.get('llm_response', {}).get('target')
            
            if target:
                print(f"    ✅ Selected target: {target} (confidence: {confidence:.0%})")
            else:
                print(f"    ⚠️ No target selected for action execution")
        
        elif current_phase == ProcessingPhase.ACTION_EXECUTION:
            execution_status = current_result.data.get('execution_status')
            if execution_status == 'success':
                print(f"    ✅ Action completed successfully")
            else:
                print(f"    ⚠️ Action execution had issues: {execution_status}")
"""

# =============================================================================
# 4. 错误恢复策略 - 基于执行顺序的错误处理
# =============================================================================

"""
def implement_error_recovery(processor: HostAgentProcessorV2) -> dict:
    '''基于执行顺序实现错误恢复策略'''
    
    results_in_order = processor.get_phase_results_in_order()
    recovery_plan = {
        'can_continue': True,
        'recovery_actions': [],
        'failed_at_step': None
    }
    
    for i, (phase, result) in enumerate(results_in_order):
        if not result.success:
            recovery_plan['can_continue'] = False
            recovery_plan['failed_at_step'] = i + 1
            
            # 基于失败的阶段和之前成功的阶段，制定恢复策略
            successful_phases = [p for p, r in results_in_order[:i] if r.success]
            
            if phase == ProcessingPhase.DATA_COLLECTION:
                if not successful_phases:
                    recovery_plan['recovery_actions'].append('Retry screenshot capture')
                    recovery_plan['recovery_actions'].append('Use cached desktop data if available')
                else:
                    recovery_plan['recovery_actions'].append('Use partial data from previous attempts')
            
            elif phase == ProcessingPhase.LLM_INTERACTION:
                if ProcessingPhase.DATA_COLLECTION in [p for p, r in results_in_order[:i]]:
                    recovery_plan['recovery_actions'].append('Retry with simplified prompt')
                    recovery_plan['recovery_actions'].append('Use fallback LLM model')
                else:
                    recovery_plan['recovery_actions'].append('Cannot proceed without data collection')
            
            elif phase == ProcessingPhase.ACTION_EXECUTION:
                if ProcessingPhase.LLM_INTERACTION in [p for p, r in results_in_order[:i]]:
                    recovery_plan['recovery_actions'].append('Retry action with alternative method')
                    recovery_plan['recovery_actions'].append('Request user manual intervention')
                else:
                    recovery_plan['recovery_actions'].append('No decision available for execution')
            
            elif phase == ProcessingPhase.MEMORY_UPDATE:
                # Memory update failure is usually non-critical
                recovery_plan['can_continue'] = True
                recovery_plan['recovery_actions'].append('Continue with in-memory storage')
                recovery_plan['recovery_actions'].append('Schedule background memory sync')
            
            break
    
    return recovery_plan

# Usage example:
recovery_plan = implement_error_recovery(processor)
if not recovery_plan['can_continue']:
    print(f"Process failed at step {recovery_plan['failed_at_step']}")
    for action in recovery_plan['recovery_actions']:
        print(f"  • {action}")
"""

# =============================================================================
# 5. 性能优化 - 基于执行顺序的性能分析
# =============================================================================

"""
def optimize_performance_based_on_order(processor: HostAgentProcessorV2):
    '''基于执行顺序进行性能优化分析'''
    
    results_in_order = processor.get_phase_results_in_order()
    
    print("📈 Performance Optimization Analysis:")
    
    # 1. 识别瓶颈阶段
    times = [(phase, result.execution_time) for phase, result in results_in_order]
    times.sort(key=lambda x: x[1], reverse=True)
    
    print("  🐌 Slowest phases (optimization targets):")
    for phase, time in times[:3]:  # Top 3 slowest
        print(f"    {phase.value}: {time:.2f}s")
    
    # 2. 分析阶段间的等待时间
    print("  ⏳ Phase transition analysis:")
    for i in range(len(results_in_order) - 1):
        current_phase, current_result = results_in_order[i]
        next_phase, next_result = results_in_order[i + 1]
        
        # 检查是否有可以并行化的机会
        if (current_phase == ProcessingPhase.DATA_COLLECTION and 
            next_phase == ProcessingPhase.LLM_INTERACTION):
            print(f"    💡 Could parallelize screenshot processing during LLM call")
        
        elif (current_phase == ProcessingPhase.ACTION_EXECUTION and 
              next_phase == ProcessingPhase.MEMORY_UPDATE):
            print(f"    💡 Memory update could run in background")
    
    # 3. 建议优化措施
    print("  🚀 Optimization recommendations:")
    
    for phase, result in results_in_order:
        if result.execution_time > 2.0:  # > 2 seconds
            if phase == ProcessingPhase.DATA_COLLECTION:
                print("    • Cache desktop screenshots")
                print("    • Optimize UI element detection")
            elif phase == ProcessingPhase.LLM_INTERACTION:
                print("    • Use streaming responses")
                print("    • Implement prompt caching")
            elif phase == ProcessingPhase.ACTION_EXECUTION:
                print("    • Pre-validate targets")
                print("    • Use faster automation libraries")
"""

# =============================================================================
# 6. 工作流控制 - 基于执行顺序的动态决策
# =============================================================================

"""
def dynamic_workflow_control(processor: HostAgentProcessorV2) -> str:
    '''基于执行顺序和结果动态控制后续工作流'''
    
    results_in_order = processor.get_phase_results_in_order()
    execution_order = processor.get_phase_execution_order()
    
    # 检查当前执行到哪一步
    last_completed_phase = execution_order[-1] if execution_order else None
    
    if not last_completed_phase:
        return "WORKFLOW_START"
    
    last_result = processor.get_phase_result(last_completed_phase)
    
    # 基于最后完成的阶段和结果决定下一步
    if last_completed_phase == ProcessingPhase.DATA_COLLECTION:
        if last_result.success:
            apps_found = len(last_result.data.get('applications_found', []))
            if apps_found == 0:
                return "WORKFLOW_RETRY_DATA_COLLECTION"
            elif apps_found == 1:
                return "WORKFLOW_SKIP_LLM_DIRECT_ACTION"  # 只有一个app，跳过LLM
            else:
                return "WORKFLOW_CONTINUE_TO_LLM"
        else:
            return "WORKFLOW_FALLBACK_MODE"
    
    elif last_completed_phase == ProcessingPhase.LLM_INTERACTION:
        if last_result.success:
            confidence = last_result.data.get('confidence_score', 0)
            if confidence < 0.6:
                return "WORKFLOW_REQUEST_USER_CONFIRMATION"
            else:
                return "WORKFLOW_CONTINUE_TO_ACTION"
        else:
            return "WORKFLOW_USE_DEFAULT_ACTION"
    
    elif last_completed_phase == ProcessingPhase.ACTION_EXECUTION:
        if last_result.success:
            return "WORKFLOW_CONTINUE_TO_MEMORY"
        else:
            return "WORKFLOW_RETRY_ACTION_ALTERNATIVE"
    
    elif last_completed_phase == ProcessingPhase.MEMORY_UPDATE:
        return "WORKFLOW_COMPLETE"
    
    return "WORKFLOW_UNKNOWN_STATE"

# Usage:
next_step = dynamic_workflow_control(processor)
print(f"Next workflow step: {next_step}")
"""

# =============================================================================
# 7. 完整的使用示例
# =============================================================================

"""
async def comprehensive_phase_analysis_example():
    '''完整的phase results按顺序分析示例'''
    
    processor = HostAgentProcessorV2(host_agent, global_context)
    result = await processor.process()
    
    print("🔍 Comprehensive Phase Analysis")
    print("=" * 50)
    
    # 1. 基础顺序信息
    execution_order = processor.get_phase_execution_order()
    print(f"📋 Execution Order: {[p.value for p in execution_order]}")
    
    # 2. 详细的按顺序分析
    results_in_order = processor.get_phase_results_in_order()
    print(f"\\n📊 Detailed Phase Analysis:")
    
    for i, (phase, phase_result) in enumerate(results_in_order):
        print(f"  {i+1}. {phase.value}:")
        print(f"     Status: {'✅ Success' if phase_result.success else '❌ Failed'}")
        print(f"     Time: {phase_result.execution_time:.2f}s")
        print(f"     Data Keys: {list(phase_result.data.keys())[:5]}")  # Show first 5 keys
        
        if not phase_result.success:
            print(f"     Error: {phase_result.error}")
        print()
    
    # 3. 流程分析
    analyze_processing_flow(processor)
    
    # 4. 数据依赖检查
    check_data_dependencies(processor)
    
    # 5. 性能分析
    optimize_performance_based_on_order(processor)
    
    # 6. 错误恢复
    if not result.get('success', True):
        recovery_plan = implement_error_recovery(processor)
        print(f"\\n🛠️ Recovery Plan:")
        for action in recovery_plan['recovery_actions']:
            print(f"  • {action}")
    
    # 7. 工作流控制
    next_step = dynamic_workflow_control(processor)
    print(f"\\n🚀 Next Step: {next_step}")
    
    return result
"""

print("📖 Phase Results 按顺序访问 - API 使用指南")
print("=" * 60)
print()
print("🔑 核心API方法:")
print("• get_phase_results() - 返回OrderedDict，保持插入顺序")
print("• get_phase_results_in_order() - 返回(phase, result)元组列表")
print("• get_phase_execution_order() - 返回执行顺序的阶段列表")
print()
print("💡 主要用途:")
print("• 🔍 流程分析和调试")
print("• 📊 性能优化和瓶颈识别")
print("• 🔗 数据依赖关系验证")
print("• 🛠️ 错误恢复策略制定")
print("• 🚀 动态工作流控制")
print()
print("✅ 复制上面的代码示例来在你的项目中使用这些功能！")
print("=" * 60)
