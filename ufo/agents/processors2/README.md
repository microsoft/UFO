# Host Agent Processor Framework V2

This document provides a comprehensive guide to the refactored Host Agent Processor framework, which has been redesigned using modern software engineering principles for enhanced maintainability, extensibility, and robustness.

## Overview

The Host Agent Processor V2 framework introduces a modular architecture based on the Template Method, Strategy, and Middleware patterns. This design provides:

- **Modular Strategies**: Separate strategies for each processing phase
- **Enhanced Middleware**: Comprehensive logging, error handling, and metrics
- **Robust Error Handling**: Graceful error propagation and recovery
- **Context Management**: Proper separation of global and local context
- **Type Safety**: Full type hints for better development experience

## Architecture

### Core Components

```
HostAgentProcessorV2
├── ProcessorTemplate (Base Class)
├── Processing Strategies
│   ├── DesktopDataCollectionStrategy
│   ├── HostLLMInteractionStrategy  
│   ├── HostActionExecutionStrategy
│   └── HostMemoryUpdateStrategy
└── Middleware Chain
    ├── HostAgentLoggingMiddleware
    ├── ErrorRecoveryMiddleware
    ├── MetricsMiddleware
    └── CleanupMiddleware
```

### Processing Flow

1. **Before Processing**: Middleware setup and initialization
2. **Data Collection**: Desktop screenshot and application detection
3. **LLM Interaction**: Generate response based on collected data
4. **Action Execution**: Execute planned actions
5. **Memory Update**: Update agent memory with results
6. **After Processing**: Cleanup and finalization

## Key Features

### 1. Modular Strategies

Each processing phase is implemented as a separate strategy:

```python
class DesktopDataCollectionStrategy(BaseProcessingStrategy):
    """Strategy for collecting desktop information and screenshots."""
    
    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        # Implementation for data collection
        pass
```

### 2. Enhanced Error Handling

```python
class ProcessingException(Exception):
    """Custom exception for processing errors with context."""
    
    def __init__(self, message: str, phase: ProcessingPhase, context: Dict[str, Any] = None):
        super().__init__(message)
        self.phase = phase
        self.context = context or {}
```

### 3. Context Management

```python
class ProcessingContext:
    """Manages both global and local processing context."""
    
    def __init__(self, global_context: Context):
        self.global_context = global_context
        self.local_data = {}
        self.phase_results = {}
```

### 4. Middleware System

```python
class HostAgentLoggingMiddleware(BaseMiddleware):
    """Comprehensive logging middleware for Host Agent."""
    
    async def before_process(self, context: ProcessingContext) -> None:
        # Setup logging
    
    async def after_process(self, context: ProcessingContext, result: ProcessingResult) -> None:
        # Log results
    
    async def on_error(self, context: ProcessingContext, error: Exception) -> None:
        # Handle errors
```

## Usage Examples

### Basic Usage

```python
from ufo.agents.processors2.host_agent_processor import HostAgentProcessorV2
from ufo.module.context import Context

# Create context and agent
global_context = Context()
host_agent = HostAgent("host_agent_1")

# Initialize processor
processor = HostAgentProcessorV2(host_agent, global_context)

# Process request
result = await processor.process()

if result.success:
    print(f"✅ Processing successful: {result.data}")
else:
    print(f"❌ Processing failed: {result.error}")
```

### Custom Strategy Implementation

```python
class CustomDataCollectionStrategy(BaseProcessingStrategy):
    """Custom strategy for specialized data collection."""
    
    async def execute(self, context: ProcessingContext) -> ProcessingResult:
        try:
            # Custom implementation
            custom_data = await self.collect_custom_data(context)
            
            return ProcessingResult.success(
                phase=ProcessingPhase.DATA_COLLECTION,
                data={"custom_data": custom_data}
            )
        except Exception as e:
            return ProcessingResult.failure(
                phase=ProcessingPhase.DATA_COLLECTION,
                error=str(e)
            )
```

### Custom Middleware

```python
class CustomMetricsMiddleware(BaseMiddleware):
    """Custom middleware for application-specific metrics."""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = None
    
    async def before_process(self, context: ProcessingContext) -> None:
        self.start_time = time.time()
        self.metrics["process_count"] = self.metrics.get("process_count", 0) + 1
    
    async def after_process(self, context: ProcessingContext, result: ProcessingResult) -> None:
        duration = time.time() - self.start_time
        self.metrics["total_processing_time"] = self.metrics.get("total_processing_time", 0) + duration
        
        if result.success:
            self.metrics["success_count"] = self.metrics.get("success_count", 0) + 1
```

## Configuration

### Strategy Configuration

Strategies can be configured or replaced:

```python
processor = HostAgentProcessorV2(host_agent, global_context)

# Replace with custom strategy
processor.strategies[ProcessingPhase.DATA_COLLECTION] = CustomDataCollectionStrategy(
    processor.agent,
    processor.context
)
```

### Middleware Configuration

Middleware can be added or reordered:

```python
processor = HostAgentProcessorV2(host_agent, global_context)

# Add custom middleware
processor.middleware_chain.append(CustomMetricsMiddleware())

# Insert middleware at specific position
processor.middleware_chain.insert(1, CustomSecurityMiddleware())
```

## Error Handling

The framework provides comprehensive error handling:

### Strategy-Level Errors

```python
# Strategies can return failure results
return ProcessingResult.failure(
    phase=ProcessingPhase.LLM_INTERACTION,
    error="Failed to generate response",
    context={"attempt": attempt_count}
)

# Or raise ProcessingException for immediate termination
raise ProcessingException(
    message="Critical data collection error",
    phase=ProcessingPhase.DATA_COLLECTION,
    context={"error_code": "SCREEN_CAPTURE_FAILED"}
)
```

### Middleware Error Handling

```python
class ErrorRecoveryMiddleware(BaseMiddleware):
    async def on_error(self, context: ProcessingContext, error: Exception) -> None:
        if isinstance(error, ProcessingException):
            # Attempt recovery based on phase
            if error.phase == ProcessingPhase.DATA_COLLECTION:
                await self.attempt_data_collection_recovery(context)
        
        # Log error details
        self.logger.error(f"Processing error in {error.phase}: {error}")
```

## Performance and Monitoring

### Built-in Metrics

The framework includes built-in metrics collection:

- Processing duration per phase
- Success/failure rates
- Error frequency and types
- Memory usage patterns

### Custom Metrics

Implement custom metrics middleware for application-specific monitoring:

```python
class ApplicationMetricsMiddleware(BaseMiddleware):
    def __init__(self, metrics_collector):
        self.metrics = metrics_collector
    
    async def after_process(self, context: ProcessingContext, result: ProcessingResult) -> None:
        self.metrics.record_processing_result(
            phase=result.phase,
            success=result.success,
            duration=result.execution_time,
            agent_type=context.global_context.get("agent_type")
        )
```

## Testing

The framework is designed for comprehensive testing:

### Unit Testing Strategies

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_desktop_data_collection_strategy():
    # Setup mocks
    mock_agent = MagicMock()
    mock_context = ProcessingContext(Context())
    
    # Test strategy
    strategy = DesktopDataCollectionStrategy(mock_agent, mock_context)
    result = await strategy.execute(mock_context)
    
    assert result.success
    assert "screenshot_url" in result.data
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_full_processor_workflow():
    # Setup complete processor
    processor = HostAgentProcessorV2(mock_agent, mock_context)
    
    # Execute full workflow
    result = await processor.process()
    
    # Verify results
    assert result.success
    assert all(phase in result.data for phase in expected_phases)
```

## Migration Guide

### From HostAgentProcessor to HostAgentProcessorV2

1. **Update imports**:
   ```python
   # Old
   from ufo.agents.processors.host_agent_processor import HostAgentProcessor
   
   # New
   from ufo.agents.processors2.host_agent_processor import HostAgentProcessorV2
   ```

2. **Update initialization**:
   ```python
   # Old
   processor = HostAgentProcessor(agent)
   
   # New
   processor = HostAgentProcessorV2(agent, global_context)
   ```

3. **Update method calls**:
   ```python
   # Old
   result = processor.process()
   
   # New
   result = await processor.process()  # Now async
   ```

## Best Practices

### Strategy Design

1. **Single Responsibility**: Each strategy should handle one specific phase
2. **Error Handling**: Always return ProcessingResult, don't raise exceptions unless critical
3. **Context Usage**: Use local context for temporary data, global for persistent state
4. **Type Safety**: Include comprehensive type hints

### Middleware Design

1. **Lightweight**: Keep middleware focused and efficient
2. **Order Matters**: Consider middleware execution order
3. **Error Resilience**: Middleware should handle their own errors gracefully
4. **Resource Cleanup**: Always clean up resources in middleware

### Context Management

1. **Global vs Local**: Use global context for session-wide data, local for processing-specific data
2. **Context Promotion**: Promote important local data to global context when needed
3. **Immutable Data**: Avoid modifying shared context data directly

## Troubleshooting

### Common Issues

1. **Missing Context Data**: Ensure required context is set before processing
2. **Middleware Conflicts**: Check middleware order and dependencies
3. **Strategy Failures**: Implement proper error handling in custom strategies
4. **Memory Leaks**: Use cleanup middleware for resource management

### Debug Logging

Enable debug logging for detailed execution information:

```python
import logging
logging.getLogger("ufo.agents.processors2").setLevel(logging.DEBUG)
```

## Contributing

When extending the framework:

1. Follow the established patterns (Strategy, Middleware, Template Method)
2. Include comprehensive type hints
3. Add proper error handling and logging
4. Write unit and integration tests
5. Update documentation

## Conclusion

The Host Agent Processor V2 framework provides a robust, extensible foundation for agent processing workflows. Its modular design and comprehensive error handling make it suitable for production use while remaining maintainable and testable.

For more examples and advanced usage patterns, see the examples directory and test files.
