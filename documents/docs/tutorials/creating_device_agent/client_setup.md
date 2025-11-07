# Part 3: Client Setup

!!! info "Coming Soon"
    This tutorial is currently under development. Check back soon for detailed instructions on setting up the device client.

## What You'll Learn

- Client initialization and configuration
- MCP server manager integration
- WebSocket connection setup
- Platform detection and handling

## Temporary Quick Guide

For now, refer to the existing client implementation:

**File**: `ufo/client/client.py`

### Basic Client Setup

```bash
# Start device client
python -m ufo.client.client \
  --ws \
  --ws-server ws://localhost:5010/ws \
  --client-id mobile_agent_1 \
  --platform android
```

### Client Configuration Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `--ws` | ✅ Yes | Enable WebSocket mode | `--ws` |
| `--ws-server` | ✅ Yes | Server WebSocket URL | `ws://localhost:5010/ws` |
| `--client-id` | ✅ Yes | Unique device identifier | `mobile_agent_1` |
| `--platform` | ✅ Yes | Platform type | `--platform android` |

## Related Documentation

- **[Client Overview](../../client/overview.md)** - Client architecture
- **[Linux Client Setup](../../getting_started/quick_start_linux.md)** - LinuxAgent client reference
- **[AIP Protocol](../../aip/overview.md)** - Communication protocol

---

**Previous**: [← Part 2: MCP Server](mcp_server.md)  
**Next**: [Part 4: Configuration & Deployment →](configuration.md)
