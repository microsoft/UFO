# 策略依赖管理装饰器系统使用指南

## 概览

新的装饰器系统为Host Agent策略提供了简洁、声明式的依赖管理方式，支持编译时验证和运行时一致性检查。

## 核心装饰器

### 1. `@strategy_config` - 组合装饰器

一次性声明策略的所有依赖和提供字段：

```python
from ufo.agents.processors2.core.strategy_dependency import (
    strategy_config, StrategyDependency, DependencyType
)

@strategy_config(
    dependencies=[
        StrategyDependency("user_request", DependencyType.REQUIRED, "用户原始请求"),
        StrategyDependency("current_app", DependencyType.OPTIONAL, "当前激活的应用")
    ],
    provides=["parsed_request", "request_intent", "target_elements"]
)
class MyStrategy(ProcessingStrategy):
    # 策略实现...
```

### 2. `@depends_on` - 依赖装饰器

逐个声明单个依赖：

```python
@depends_on("parsed_request", DependencyType.REQUIRED, "已解析的用户请求")
@depends_on("app_context", DependencyType.OPTIONAL, "应用上下文信息")
@provides("action_plan", "execution_steps")
class ActionPlanningStrategy(ProcessingStrategy):
    # 策略实现...
```

### 3. `@provides` - 提供装饰器

声明策略提供的字段：

```python
@provides("execution_result", "success_status", "error_details")
class ActionExecutionStrategy(ProcessingStrategy):
    # 策略实现...
```

## 依赖类型

### DependencyType.REQUIRED
- 必须存在的依赖，缺失会导致验证失败
- 用于策略的核心输入数据

### DependencyType.OPTIONAL
- 可选依赖，缺失不会导致验证失败
- 用于增强功能或配置数据

### DependencyType.COMPUTED
- 运行时计算的依赖
- 可以从其他字段动态生成

## 验证机制

### 1. 策略链验证（编译时）

在ProcessorTemplate初始化时自动进行：

```python
class MyProcessor(ProcessorTemplate):
    def _setup_strategies(self):
        # 策略注册...
        pass
    # 初始化时会自动验证策略链的依赖关系
```

验证内容：
- 检查每个策略的依赖是否能被前面的策略提供
- 识别循环依赖
- 验证必需依赖的可用性

### 2. 运行时一致性检查

在每个策略执行后自动进行：

- 验证策略实际返回的字段是否与`@provides`声明一致
- 检查缺失字段和额外字段
- 记录警告日志（可配置为错误）

## 使用示例

### 完整的策略实现示例

```python
from ufo.agents.processors2.core.strategy_dependency import (
    strategy_config, StrategyDependency, DependencyType
)

@strategy_config(
    dependencies=[
        StrategyDependency("user_request", DependencyType.REQUIRED, "用户请求"),
        StrategyDependency("app_state", DependencyType.OPTIONAL, "应用状态")
    ],
    provides=["parsed_elements", "action_type", "confidence_score"]
)
class ElementAnalysisStrategy(ProcessingStrategy):
    
    def __init__(self):
        super().__init__("element_analysis")
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        # 获取依赖数据
        user_request = context.get_local("user_request")
        app_state = context.get_local("app_state", {})  # 可选依赖
        
        # 策略逻辑...
        parsed_elements = self.analyze_elements(user_request, app_state)
        action_type = self.determine_action_type(user_request)
        confidence_score = self.calculate_confidence(parsed_elements, action_type)
        
        # 返回数据 - 必须与provides声明一致
        return ProcessingResult(
            success=True,
            data={
                "parsed_elements": parsed_elements,
                "action_type": action_type, 
                "confidence_score": confidence_score,
                # 如果包含额外字段会收到警告：
                # "extra_field": "value"  # 这会触发警告
            }
        )
```

### 策略链配置示例

```python
class HostAgentProcessor(ProcessorTemplate):
    
    def _setup_strategies(self):
        self.strategies = {
            ProcessingPhase.ANALYSIS: RequestParsingStrategy(),
            ProcessingPhase.PLANNING: ActionPlanningStrategy(),
            ProcessingPhase.EXECUTION: ActionExecutionStrategy(),
            ProcessingPhase.VALIDATION: ResultSummaryStrategy(),
        }
        # 策略链会在初始化时自动验证
```

## 错误处理和调试

### 常见验证错误

1. **依赖缺失**: `Missing required dependency 'field_name' for strategy 'StrategyName'`
2. **提供不一致**: `Strategy 'StrategyName' provides consistency errors: Missing fields: ['field1'], Extra fields: ['field2']`
3. **循环依赖**: `Circular dependency detected between strategies`

### 日志配置

```python
import logging

# 启用详细的依赖验证日志
logging.getLogger("StrategyDependencyValidator").setLevel(logging.DEBUG)
logging.getLogger("ProcessorTemplate").setLevel(logging.INFO)
```

### 调试提示

1. **使用测试脚本**: 运行 `test_decorator_system.py` 验证策略配置
2. **检查元数据**: 验证装饰器是否正确设置了 `_strategy_dependencies` 和 `_strategy_provides` 属性
3. **逐步验证**: 先验证策略链，再测试运行时执行

## 配置选项

### 严格模式

可以配置ProcessorTemplate使provides不一致导致错误而不是警告：

```python
class StrictProcessor(ProcessorTemplate):
    
    def __init__(self, agent, global_context):
        self.strict_provides_validation = True  # 启用严格模式
        super().__init__(agent, global_context)
```

### 自定义验证规则

可以继承和扩展验证器：

```python
class CustomValidator(StrategyDependencyValidator):
    
    def validate_custom_rules(self, strategies):
        # 自定义验证逻辑
        pass
```

## 最佳实践

1. **明确声明**: 总是明确声明策略的所有依赖和提供字段
2. **合理分类**: 正确区分REQUIRED和OPTIONAL依赖
3. **一致性**: 确保execute方法返回的字段与provides声明完全一致
4. **文档化**: 为每个依赖和提供字段添加清晰的描述
5. **测试驱动**: 使用测试脚本验证策略配置的正确性

## 迁移指南

### 从旧系统迁移

1. **添加装饰器**: 为现有策略类添加适当的装饰器
2. **验证配置**: 运行测试脚本确保配置正确
3. **更新返回值**: 确保execute方法返回与provides一致的字段
4. **测试验证**: 全面测试策略链的执行

### 渐进式迁移

- 可以同时使用新旧系统
- 优先迁移关键策略
- 逐步验证和测试每个迁移的策略

这个装饰器系统提供了类型安全、声明式、可验证的策略依赖管理，大大提高了Host Agent策略开发的效率和可靠性。
