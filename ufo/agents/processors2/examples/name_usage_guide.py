"""
Middleware和Strategy Name属性 - API使用指南

本指南展示如何使用新的name属性来简化日志输出和提高代码可读性
"""

# =============================================================================
# 1. ProcessorMiddleware - 使用name属性
# =============================================================================

"""
# 基础用法 - 使用默认类名
class MyMiddleware(ProcessorMiddleware):
    def __init__(self):
        super().__init__()  # name = "MyMiddleware"
        
    # ... 实现其他方法

# 使用自定义名称
class TimingMiddleware(ProcessorMiddleware):
    def __init__(self, name: Optional[str] = None):
        super().__init__(name or "timer")  # 使用简短名称
        
    # ... 实现其他方法

# 使用多语言名称
class ValidationMiddleware(ProcessorMiddleware):
    def __init__(self):
        super().__init__(name="验证器")  # 中文名称
        
    # ... 实现其他方法

# 实例化时指定名称
middleware1 = TimingMiddleware()  # name = "timer"
middleware2 = TimingMiddleware(name="custom_timer")  # name = "custom_timer"
middleware3 = ValidationMiddleware()  # name = "验证器"
"""

# =============================================================================
# 2. BaseProcessingStrategy - 使用name属性
# =============================================================================

"""
# 基础用法 - 使用默认类名
class DataCollectionStrategy(BaseProcessingStrategy):
    def __init__(self):
        super().__init__()  # name = "DataCollectionStrategy"
        
    # ... 实现execute方法

# 使用自定义名称
class DesktopDataCollectionStrategy(BaseProcessingStrategy):
    def __init__(self, fail_fast: bool = True):
        super().__init__(name="desktop_data_collector", fail_fast=fail_fast)
        
    # ... 实现execute方法

# 动态名称生成
class VersionedStrategy(BaseProcessingStrategy):
    def __init__(self, version: int):
        super().__init__(name=f"strategy_v{version}")
        
    # ... 实现execute方法

# 实例化示例
strategy1 = DataCollectionStrategy()  # name = "DataCollectionStrategy"
strategy2 = DesktopDataCollectionStrategy()  # name = "desktop_data_collector"
strategy3 = VersionedStrategy(version=2)  # name = "strategy_v2"
"""

# =============================================================================
# 3. 日志输出对比
# =============================================================================

"""
# 旧的日志输出 (使用 __class__.__name__)
INFO - Executing middleware before_process: VeryLongMiddlewareNameThatIsHardToRead
INFO - Starting phase: data_collection, with strategy: ComplexDataCollectionStrategyWithLongName

# 新的日志输出 (使用 name 属性)
INFO - Executing middleware before_process: timer
INFO - Starting phase: data_collection, with strategy: data_collector

# 优势:
• 更简洁的日志输出
• 更好的可读性
• 自定义友好名称
• 支持多语言
• 保持向后兼容
"""

# =============================================================================
# 4. 在ProcessorTemplate中的使用
# =============================================================================

"""
# ProcessorTemplate会自动使用name属性进行日志记录
class MyProcessor(ProcessorTemplate):
    def _setup_middleware(self):
        self.middleware_chain = [
            TimingMiddleware(name="主计时器"),
            ValidationMiddleware(name="数据验证器"),
            CleanupMiddleware(name="清理器")
        ]
    
    def _setup_strategies(self):
        self.strategies[ProcessingPhase.DATA_COLLECTION] = (
            DataCollectionStrategy(name="桌面数据收集器")
        )
        self.strategies[ProcessingPhase.LLM_INTERACTION] = (
            LLMStrategy(name="智能决策器")
        )

# 日志输出将显示:
# INFO - Executing middleware before_process: 主计时器
# INFO - Starting phase: data_collection, with strategy: 桌面数据收集器
"""

# =============================================================================
# 5. 最佳实践
# =============================================================================

"""
# 1. 为常用中间件使用简短易记的名称
class TimingMiddleware(ProcessorMiddleware):
    def __init__(self):
        super().__init__(name="timer")  # 而不是 "TimingMiddleware"

# 2. 为策略使用描述性名称
class DesktopScreenshotStrategy(BaseProcessingStrategy):
    def __init__(self):
        super().__init__(name="screenshot_taker")  # 而不是 "DesktopScreenshotStrategy"

# 3. 支持可配置名称
class RetryMiddleware(ProcessorMiddleware):
    def __init__(self, name: Optional[str] = None, max_retries: int = 3):
        super().__init__(name or f"retry_{max_retries}x")

# 4. 使用有意义的前缀或后缀
class DatabaseStrategy(BaseProcessingStrategy):
    def __init__(self, db_type: str):
        super().__init__(name=f"{db_type}_db")

# 5. 支持版本化命名
class MLModelStrategy(BaseProcessingStrategy):
    def __init__(self, model_version: str):
        super().__init__(name=f"ml_model_{model_version}")
"""

# =============================================================================
# 6. 向后兼容性
# =============================================================================

"""
# 如果不指定name参数，会自动使用类名
class LegacyMiddleware(ProcessorMiddleware):
    def __init__(self):
        super().__init__()  # name = "LegacyMiddleware"

# 这确保了现有代码无需修改即可工作
# 但推荐逐步迁移到使用name参数以获得更好的日志输出
"""

# =============================================================================
# 7. 调试和监控优势
# =============================================================================

"""
# 使用name属性后，日志分析更容易:

# 1. 过滤特定组件的日志
grep "timer" application.log  # 查找所有计时器相关日志

# 2. 监控特定策略的性能
grep "data_collector" application.log | grep "execution_time"

# 3. 识别问题组件
grep "ERROR.*smart_action" application.log  # 查找智能动作策略的错误

# 4. 统计组件使用频率
grep -o "strategy: [^"]*" application.log | sort | uniq -c
"""

print("📖 Middleware和Strategy Name属性 - API使用指南")
print("=" * 60)
print()
print("🔑 核心改进:")
print("• ProcessorMiddleware和BaseProcessingStrategy现在支持name参数")
print("• 日志输出使用name而不是__class__.__name__")
print("• 保持完全向后兼容")
print("• 支持自定义友好名称")
print()
print("💡 使用建议:")
print("• 为常用组件使用简短易记的名称")
print("• 支持可配置名称参数")
print("• 使用描述性而非技术性的名称")
print("• 考虑使用多语言名称提高本地化")
print()
print("✅ 复制上面的代码示例来在你的项目中使用这些功能！")
print("=" * 60)
