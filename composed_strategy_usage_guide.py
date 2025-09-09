#!/usr/bin/env python3
"""
Demonstration of the Generic ComposedStrategy Usage Patterns

This script shows various ways to use the new generic ComposedStrategy
to create flexible, reusable processing pipelines.
"""

# Example usage patterns for the generic ComposedStrategy

print("🚀 Generic ComposedStrategy Usage Patterns")
print("=" * 50)

print("\n1️⃣  App Agent Data Collection (Current Usage)")
print("-" * 40)
print("# The existing composed strategy now uses the generic approach:")
print(
    """
from ufo.agents.processors2.strategies.app_agent_processing_strategy import (
    AppScreenshotCaptureStrategy, 
    AppControlInfoStrategy,
    ComposedStrategy
)

# Traditional way - using the pre-built ComposedAppDataCollectionStrategy
data_collection_strategy = ComposedAppDataCollectionStrategy(fail_fast=True)

# New flexible way - using generic ComposedStrategy directly
custom_data_collection = ComposedStrategy(
    strategies=[
        AppScreenshotCaptureStrategy(fail_fast=True),
        AppControlInfoStrategy(fail_fast=True)
    ],
    name="custom_app_data_collection",
    fail_fast=True,
    phase=ProcessingPhase.DATA_COLLECTION
)
"""
)

print("\n2️⃣  Custom Multi-Phase Pipeline")
print("-" * 40)
print("# Create a pipeline that combines multiple processing phases:")
print(
    """
# Example: Custom workflow for complex app interactions
complex_workflow = ComposedStrategy(
    strategies=[
        # Data collection phase
        AppScreenshotCaptureStrategy(),
        AppControlInfoStrategy(),
        
        # Analysis phase
        AppLLMInteractionStrategy(),
        
        # Action phase  
        AppActionExecutionStrategy(),
        
        # Memory phase
        AppMemoryUpdateStrategy()
    ],
    name="complex_app_workflow",
    fail_fast=False,  # Continue even if some steps fail
    phase=ProcessingPhase.DATA_COLLECTION  # Primary phase
)
"""
)

print("\n3️⃣  Conditional Strategy Composition")
print("-" * 40)
print("# Build strategies dynamically based on conditions:")
print(
    """
def build_adaptive_strategy(user_preferences: Dict, context: Dict) -> ComposedStrategy:
    '''Build strategy based on runtime conditions.'''
    
    base_strategies = [AppScreenshotCaptureStrategy()]
    
    # Add control analysis if UI interaction needed
    if user_preferences.get('ui_interaction', True):
        base_strategies.append(AppControlInfoStrategy())
    
    # Add memory update if learning enabled
    if user_preferences.get('learning_enabled', False):
        base_strategies.append(AppMemoryUpdateStrategy())
    
    # Add custom validation strategy if in debug mode
    if context.get('debug_mode', False):
        base_strategies.append(CustomValidationStrategy())
    
    return ComposedStrategy(
        strategies=base_strategies,
        name="adaptive_strategy",
        fail_fast=user_preferences.get('fail_fast', True)
    )
"""
)

print("\n4️⃣  Parallel Strategy Groups")
print("-" * 40)
print("# Compose strategies that can run in parallel:")
print(
    """
# Group related strategies together
screenshot_group = ComposedStrategy(
    strategies=[
        AppScreenshotCaptureStrategy(),
        DesktopScreenshotCaptureStrategy()  # Hypothetical
    ],
    name="screenshot_capture_group"
)

analysis_group = ComposedStrategy(
    strategies=[
        AppControlInfoStrategy(), 
        AppAccessibilityAnalysisStrategy()  # Hypothetical
    ],
    name="ui_analysis_group"
)

# Combine groups into a higher-level strategy
comprehensive_analysis = ComposedStrategy(
    strategies=[
        screenshot_group,  # Strategies can be composed recursively!
        analysis_group
    ],
    name="comprehensive_app_analysis",
    fail_fast=False
)
"""
)

print("\n5️⃣  Error Handling Patterns")
print("-" * 40)
print("# Different error handling approaches:")
print(
    """
# Fail-fast for critical operations
critical_pipeline = ComposedStrategy(
    strategies=[...],
    name="critical_operations",
    fail_fast=True  # Stop immediately on any failure
)

# Best-effort for optional features  
optional_pipeline = ComposedStrategy(
    strategies=[...],
    name="optional_features",
    fail_fast=False  # Continue and collect partial results
)

# Custom error handling
class RobustComposedStrategy(ComposedStrategy):
    async def execute(self, agent, context):
        result = await super().execute(agent, context)
        
        # Custom recovery logic
        if not result.success:
            self.logger.warning("Attempting recovery...")
            # Implement fallback strategies
            
        return result
"""
)

print("\n6️⃣  Strategy Metadata and Dependencies")
print("-" * 40)
print("# Automatic dependency collection:")
print(
    """
# The generic strategy automatically collects metadata from components
strategy = ComposedStrategy(strategies=[...])

print(f"Dependencies: {strategy._dependencies}")
print(f"Provides: {strategy._provides}")

# This enables:
# - Automatic validation of strategy compatibility
# - Documentation generation
# - Dependency injection optimization
# - Pipeline analysis and optimization
"""
)

print("\n7️⃣  Testing and Development")
print("-" * 40)
print("# Easy testing with mock strategies:")
print(
    """
class MockStrategy(BaseProcessingStrategy):
    def __init__(self, name: str, success: bool = True, data: Dict = None):
        super().__init__(name)
        self.mock_success = success
        self.mock_data = data or {}
    
    async def execute(self, agent, context):
        return ProcessingResult(
            success=self.mock_success,
            data=self.mock_data,
            phase=ProcessingPhase.DATA_COLLECTION
        )

# Test different scenarios
test_strategy = ComposedStrategy([
    MockStrategy("step1", success=True, data={"screenshot": "path"}),
    MockStrategy("step2", success=False),  # Simulate failure
    MockStrategy("step3", success=True, data={"controls": []})
])
"""
)

print("\n✨ Key Benefits of Generic ComposedStrategy")
print("-" * 50)
benefits = [
    "🔄 Reusable composition patterns across different agent types",
    "🎯 Flexible error handling (fail-fast vs. best-effort)",
    "📊 Automatic metadata collection and dependency tracking",
    "🧪 Easy testing with mock strategies and isolated components",
    "🔧 Runtime strategy configuration based on context/preferences",
    "📈 Hierarchical composition (strategies containing strategies)",
    "🚀 Maintains performance while adding flexibility",
    "🛡️ Type-safe composition with proper error handling",
]

for benefit in benefits:
    print(f"  {benefit}")

print("\n🎯 Migration Guide")
print("-" * 20)
print(
    """
Old approach (rigid):
  class SpecificComposedStrategy(BaseProcessingStrategy):
      # Hard-coded strategy combination
      # Difficult to customize or reuse

New approach (flexible):
  # Use generic ComposedStrategy with any combination
  strategy = ComposedStrategy(strategies=[...], ...)
  
  # Or create specialized subclasses for common patterns
  class AppDataCollection(ComposedStrategy):
      def __init__(self):
          super().__init__(strategies=[...])
"""
)

print("\n" + "=" * 50)
print("🎉 Ready to use! The generic ComposedStrategy provides")
print("   a flexible foundation for any strategy composition needs.")
