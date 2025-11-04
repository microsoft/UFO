# AIP Transport Layer

The transport layer provides the foundation for AIP's communication infrastructure. It abstracts the underlying network protocol, enabling protocol-level code to work with any transport implementation.

## Transport Abstraction

AIP defines a `Transport` interface that all transport implementations must follow:

```python
from aip.transport import Transport

class Transport(ABC):
    @abstractmethod
    async def connect(self, url: str, **kwargs) -> None:
        """Connect to remote endpoint"""
        
    @abstractmethod
    async def send(self, data: bytes) -> None:
        """Send data"""
        
    @abstractmethod
    async def receive(self) -> bytes:
        """Receive data"""
        
    @abstractmethod
    async def close(self) -> None:
        """Close connection"""
        
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status"""
```

## WebSocket Transport

The primary transport implementation is `WebSocketTransport`, built on the WebSocket protocol for persistent, full-duplex communication.

### Initialization

```python
from aip.transport import WebSocketTransport

transport = WebSocketTransport(
    ping_interval=30.0,      # Ping every 30 seconds
    ping_timeout=180.0,      # Wait up to 180s for pong
    close_timeout=10.0,      # Wait up to 10s for close handshake
    max_size=100 * 1024 * 1024  # Max message size: 100MB
)
```

### Client-Side Connection

```python
# Connect to server
await transport.connect("ws://localhost:8000/ws")

# Send message
await transport.send(b"Hello Server")

# Receive message
data = await transport.receive()

# Close connection
await transport.close()
```

### Server-Side Usage

For server-side WebSocket handling (e.g., with FastAPI):

```python
from fastapi import WebSocket
from aip.transport import WebSocketTransport

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Create transport from existing WebSocket
    transport = WebSocketTransport(websocket=websocket)
    
    # Now use transport as normal
    data = await transport.receive()
    await transport.send(b"Response")
```

!!!info
    The WebSocket transport automatically detects whether it's wrapping a FastAPI WebSocket or a client WebSocket connection.

### Configuration Parameters

**ping_interval (float)**

Time between ping messages (seconds). Keepalive mechanism to detect broken connections.

Default: 30.0

**ping_timeout (float)**

Maximum wait time for pong response (seconds). Connection marked as dead if no pong received.

Default: 180.0

**close_timeout (float)**

Timeout for graceful close handshake (seconds).

Default: 10.0

**max_size (int)**

Maximum message size in bytes. Messages exceeding this limit are rejected.

Default: 100MB (104,857,600 bytes)

!!!tip
    Set `max_size` based on your application's needs. Large models or screenshots may require higher limits.

### Connection States

The transport tracks connection state through `TransportState`:

- `DISCONNECTED`: Not connected
- `CONNECTING`: Connection in progress
- `CONNECTED`: Active connection
- `DISCONNECTING`: Closing connection
- `ERROR`: Error occurred

Check state:

```python
if transport.state == TransportState.CONNECTED:
    await transport.send(data)
```

### Error Handling

**Connection Errors**

```python
try:
    await transport.connect("ws://localhost:8000/ws")
except ConnectionError as e:
    print(f"Failed to connect: {e}")
```

**Send/Receive Errors**

```python
try:
    await transport.send(data)
except ConnectionError:
    # Connection closed
    await reconnect()
except IOError as e:
    # I/O error
    log_error(e)
```

!!!warning
    Always handle `ConnectionError` when the connection closes unexpectedly during send/receive operations.

### Ping/Pong Keepalive

WebSocket automatically sends ping frames at `ping_interval`:

```
Client                     Server
  │                          │
  │ ping                     │
  │─────────────────────────>│
  │                          │
  │ pong                     │
  │<─────────────────────────│
  │                          │
```

If no pong received within `ping_timeout`, the connection is marked as dead and closed.

### Graceful Shutdown

```python
# Close with timeout
await transport.close()

# Wait for complete shutdown
await transport.wait_closed()
```

The transport sends a WebSocket close frame and waits for the peer's close frame within `close_timeout`.

### Adapter Pattern

AIP uses adapters to support both client-side (`websockets` library) and server-side (FastAPI `WebSocket`) connections transparently:

```python
# Automatically creates appropriate adapter
transport = WebSocketTransport(websocket=fastapi_websocket)
# vs
transport = WebSocketTransport()
await transport.connect(url)
```

Adapters handle API differences between WebSocket implementations, providing a unified interface.

## Message Encoding

AIP uses UTF-8 encoded JSON for all messages:

```python
# Protocol layer
msg = ClientMessage(...)
json_str = msg.model_dump_json()  # Pydantic serialization
bytes_data = json_str.encode('utf-8')

# Transport layer
await transport.send(bytes_data)
```

On receive:

```python
# Transport layer
bytes_data = await transport.receive()

# Protocol layer
json_str = bytes_data.decode('utf-8')
msg = ClientMessage.model_validate_json(json_str)
```

## Performance Considerations

**Large Messages**

For messages approaching `max_size`, consider:

- Compressing data before sending
- Splitting into multiple messages
- Using streaming protocols

**High Throughput**

For high message rates:

- Batch multiple small messages into one
- Reduce `ping_interval` to detect failures faster
- Use connection pooling for multiple devices

**Low Latency**

For real-time applications:

- Minimize `ping_interval` (10-15s)
- Use dedicated connections per device
- Avoid large message batches

## Transport Extensions

While WebSocket is the default, AIP's architecture supports additional transports:

### HTTP/3 (Future)

Benefits:
- Multiplexing without head-of-line blocking
- 0-RTT connection resumption
- Better mobile network performance

### gRPC (Future)

Benefits:
- Strong typing with Protocol Buffers
- Built-in load balancing
- Streaming RPCs

### Custom Transports

Implement the `Transport` interface:

```python
from aip.transport.base import Transport

class CustomTransport(Transport):
    async def connect(self, url: str, **kwargs) -> None:
        # Custom connection logic
        pass
    
    # Implement other methods...
```

## Best Practices

**Set Appropriate Timeouts**

Configure ping/close timeouts based on network conditions:

- Local network: Short timeouts (10-30s ping)
- Internet: Longer timeouts (30-60s ping)
- Unreliable network: Very long timeouts (60-180s ping)

**Monitor Connection Health**

Check `is_connected` before critical operations.

**Handle Disconnections Gracefully**

Always have reconnection logic in place (see [Resilience](./resilience.md)).

**Log Transport Events**

Enable transport-level logging for debugging:

```python
import logging
logging.getLogger("aip.transport").setLevel(logging.DEBUG)
```

**Resource Cleanup**

Always close transports when done to prevent resource leaks:

```python
try:
    await transport.connect(url)
    # Use transport...
finally:
    await transport.close()
```

## API Reference

```python
from aip.transport import (
    Transport,           # Abstract base class
    WebSocketTransport,  # WebSocket implementation
    TransportState,      # Connection states
)
```

For more information:

- [Protocol Reference](./protocols.md) - How protocols use transports
- [Resilience](./resilience.md) - Connection management
- [Endpoints](./endpoints.md) - Transport usage in endpoints
