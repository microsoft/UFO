"""
演示如何按照set_phase_result的调用顺序读取phase results
"""

import asyncio
import logging
from collections import OrderedDict
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List


# 模拟的类定义
class ProcessingPhase(Enum):
    """Processing phases enum"""

    DATA_COLLECTION = "data_collection"
    LLM_INTERACTION = "llm_interaction"
    ACTION_EXECUTION = "action_execution"
    MEMORY_UPDATE = "memory_update"


@dataclass
class ProcessingResult:
    """Processing result data class"""

    success: bool
    data: Dict[str, Any]
    phase: Optional[ProcessingPhase] = None
    execution_time: float = 0.0
    error: Optional[str] = None


class ProcessingContext:
    """模拟的ProcessingContext类，展示OrderedDict的使用"""

    def __init__(self):
        self.phase_results: OrderedDict[ProcessingPhase, ProcessingResult] = (
            OrderedDict()
        )

    def set_phase_result(
        self, phase: ProcessingPhase, result: ProcessingResult
    ) -> None:
        """按顺序存储phase结果"""
        self.phase_results[phase] = result
        print(f"🔄 Stored result for phase: {phase.value}")

    def get_all_phase_results(self) -> OrderedDict[ProcessingPhase, ProcessingResult]:
        """获取所有phase结果，保持插入顺序"""
        return self.phase_results.copy()

    def get_phase_results_in_order(
        self,
    ) -> List[tuple[ProcessingPhase, ProcessingResult]]:
        """按执行顺序获取phase结果"""
        return list(self.phase_results.items())

    def get_phase_execution_order(self) -> List[ProcessingPhase]:
        """获取phase执行顺序"""
        return list(self.phase_results.keys())


async def demonstrate_ordered_phase_results():
    """演示按顺序读取phase results"""

    print("🧪 Phase Results 顺序访问演示")
    print("=" * 50)

    # 创建处理上下文
    context = ProcessingContext()

    print("\n📥 1. 按不同顺序设置phase结果:")

    # 故意按非标准顺序设置phase结果来证明顺序保持
    phases_to_set = [
        ProcessingPhase.LLM_INTERACTION,  # 先设置LLM
        ProcessingPhase.DATA_COLLECTION,  # 再设置数据收集
        ProcessingPhase.MEMORY_UPDATE,  # 然后内存更新
        ProcessingPhase.ACTION_EXECUTION,  # 最后动作执行
    ]

    for i, phase in enumerate(phases_to_set):
        result = ProcessingResult(
            success=True,
            phase=phase,
            execution_time=i * 0.5 + 1.0,
            data={f"{phase.value}_data": f"result_{i+1}", "execution_order": i + 1},
        )

        # 模拟一些时间延迟
        await asyncio.sleep(0.1)

        context.set_phase_result(phase, result)

    print(f"\n📊 2. 验证插入顺序保持:")

    # 获取执行顺序
    execution_order = context.get_phase_execution_order()
    print(f"   执行顺序: {[phase.value for phase in execution_order]}")

    # 验证顺序是否与设置顺序一致
    expected_order = [phase.value for phase in phases_to_set]
    actual_order = [phase.value for phase in execution_order]

    if expected_order == actual_order:
        print("   ✅ 顺序保持正确!")
    else:
        print(f"   ❌ 顺序错误! 期望: {expected_order}, 实际: {actual_order}")

    print(f"\n🔍 3. 按顺序访问结果:")

    # 使用get_phase_results_in_order按顺序访问
    ordered_results = context.get_phase_results_in_order()

    for i, (phase, result) in enumerate(ordered_results):
        print(f"   {i+1}. {phase.value}:")
        print(f"      ✅ Success: {result.success}")
        print(f"      ⏱️  Time: {result.execution_time:.1f}s")
        print(f"      📊 Data: {result.data}")
        print()

    print(f"📈 4. 使用顺序信息进行分析:")

    # 分析执行流程
    print(f"   📋 执行流程分析:")
    ordered_results = context.get_phase_results_in_order()

    for i, (phase, result) in enumerate(ordered_results):
        if i == 0:
            print(f"   ▶️  第一步: {phase.value} ({result.execution_time:.1f}s)")
        elif i == len(ordered_results) - 1:
            print(f"   🏁 最后一步: {phase.value} ({result.execution_time:.1f}s)")
        else:
            print(f"   ⏩ 第{i+1}步: {phase.value} ({result.execution_time:.1f}s)")

    # 计算累计时间
    total_time = sum(result.execution_time for _, result in ordered_results)
    print(f"   ⏱️  总执行时间: {total_time:.1f}s")

    # 检查阶段间的依赖性
    print(f"\n🔗 5. 检查阶段间数据依赖:")

    for i, (phase, result) in enumerate(ordered_results):
        if i > 0:
            prev_phase, prev_result = ordered_results[i - 1]
            print(f"   {prev_phase.value} → {phase.value}")

            # 模拟检查数据依赖
            if phase == ProcessingPhase.ACTION_EXECUTION:
                if ProcessingPhase.LLM_INTERACTION in [
                    p for p, r in ordered_results[:i]
                ]:
                    print(f"     ✅ {phase.value} 可以使用 LLM 的决策结果")
                else:
                    print(f"     ⚠️  {phase.value} 缺少 LLM 的决策结果")


async def demonstrate_order_comparison():
    """对比字典和OrderedDict的顺序保持能力"""

    print("\n" + "=" * 50)
    print("🔬 字典类型顺序对比演示")
    print("=" * 50)

    # 普通字典 (Python 3.7+ 虽然保持插入顺序，但不保证)
    regular_dict = {}
    ordered_dict = OrderedDict()

    phases = [
        ProcessingPhase.ACTION_EXECUTION,  # 最后的先加入
        ProcessingPhase.DATA_COLLECTION,
        ProcessingPhase.MEMORY_UPDATE,
        ProcessingPhase.LLM_INTERACTION,  # 第一个最后加入
    ]

    print("\n📥 以相同顺序向两种字典类型添加项目:")

    for i, phase in enumerate(phases):
        result = ProcessingResult(
            success=True, phase=phase, execution_time=i + 1.0, data={"order": i}
        )

        regular_dict[phase] = result
        ordered_dict[phase] = result

        print(f"   添加: {phase.value}")

    print(f"\n📊 结果对比:")

    regular_keys = list(regular_dict.keys())
    ordered_keys = list(ordered_dict.keys())

    print(f"   普通字典顺序: {[k.value for k in regular_keys]}")
    print(f"   OrderedDict顺序: {[k.value for k in ordered_keys]}")

    if regular_keys == ordered_keys:
        print(f"   ✅ 两者顺序一致 (Python 3.7+ 行为)")
    else:
        print(f"   ⚠️  两者顺序不同")

    print(f"\n💡 为什么使用OrderedDict:")
    print(f"   • 明确保证插入顺序")
    print(f"   • 向后兼容老版本Python")
    print(f"   • 语义明确：顺序很重要")
    print(f"   • 提供顺序相关的方法")


async def demonstrate_practical_usage():
    """展示实际使用场景"""

    print("\n" + "=" * 50)
    print("🛠️  实际使用场景演示")
    print("=" * 50)

    context = ProcessingContext()

    # 模拟正常的处理流程
    print("\n🔄 模拟正常处理流程:")

    normal_flow = [
        (ProcessingPhase.DATA_COLLECTION, {"apps_found": 5, "screenshot": "captured"}),
        (
            ProcessingPhase.LLM_INTERACTION,
            {"decision": "open_calculator", "confidence": 0.95},
        ),
        (ProcessingPhase.ACTION_EXECUTION, {"action": "click", "target": "Calculator"}),
        (ProcessingPhase.MEMORY_UPDATE, {"saved_items": 3}),
    ]

    for phase, data in normal_flow:
        result = ProcessingResult(
            success=True, phase=phase, data=data, execution_time=1.5
        )
        context.set_phase_result(phase, result)

    print(f"\n📈 分析处理流程:")

    # 1. 按顺序检查每个阶段
    print(f"   🔍 阶段完成情况:")
    for i, (phase, result) in enumerate(context.get_phase_results_in_order()):
        print(f"      {i+1}. {phase.value}: {'✅' if result.success else '❌'}")

    # 2. 检查关键数据传递
    print(f"\n   📊 关键数据传递:")
    ordered_results = context.get_phase_results_in_order()

    for i in range(len(ordered_results) - 1):
        current_phase, current_result = ordered_results[i]
        next_phase, next_result = ordered_results[i + 1]

        print(f"      {current_phase.value} → {next_phase.value}")

        # 检查数据依赖
        if (
            current_phase == ProcessingPhase.DATA_COLLECTION
            and next_phase == ProcessingPhase.LLM_INTERACTION
        ):
            apps_found = current_result.data.get("apps_found", 0)
            print(f"         传递数据: {apps_found} 个应用程序")

        elif (
            current_phase == ProcessingPhase.LLM_INTERACTION
            and next_phase == ProcessingPhase.ACTION_EXECUTION
        ):
            decision = current_result.data.get("decision")
            confidence = current_result.data.get("confidence", 0)
            print(f"         传递决策: {decision} (置信度: {confidence:.0%})")

    # 3. 性能分析
    print(f"\n   ⏱️  性能分析:")
    times = [
        result.execution_time for _, result in context.get_phase_results_in_order()
    ]
    phases = [phase.value for phase, _ in context.get_phase_results_in_order()]

    for phase_name, time in zip(phases, times):
        print(f"      {phase_name}: {time:.1f}s")

    print(f"      总计: {sum(times):.1f}s")


async def main():
    """运行所有演示"""

    await demonstrate_ordered_phase_results()
    await demonstrate_order_comparison()
    await demonstrate_practical_usage()

    print("\n" + "=" * 50)
    print("🎉 Phase Results 顺序访问演示完成!")
    print()
    print("关键要点:")
    print("• ✅ 使用 OrderedDict 确保按 set_phase_result 调用顺序存储")
    print("• 🔍 get_phase_results_in_order() 返回按执行顺序的结果")
    print("• 📊 get_phase_execution_order() 返回执行顺序的阶段列表")
    print("• 🛠️  可用于流程分析、依赖检查、性能监控")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
