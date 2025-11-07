# Part 2: MCP Server Development

!!! info "Coming Soon"
    This tutorial is currently under development. Check back soon for detailed instructions on creating platform-specific MCP servers.

## What You'll Learn

- MCP server architecture
- Defining MCP tools for your platform
- Command execution logic
- Error handling and validation
- Integration with device client

## Temporary Quick Guide

For now, refer to the LinuxAgent MCP server implementation as a reference:

**File**: `ufo/client/mcp/http_servers/linux_mcp_server.py`

### Basic MCP Server Structure

```python
from fastmcp import FastMCP

def create_mobile_mcp_server(host="localhost", port=8020):
    mcp = FastMCP(
        "Mobile MCP Server",
        instructions="MCP server for mobile device automation",
        stateless_http=False,
        json_response=True,
        host=host,
        port=port,
    )

    @mcp.tool()
    async def tap_element(x: int, y: int) -> dict:
        """Tap at coordinates (x, y) on the mobile screen."""
        # TODO: Implement tap via ADB or platform API
        pass
    
    @mcp.tool()
    async def swipe(start_x: int, start_y: int, end_x: int, end_y: int) -> dict:
        """Swipe from start coordinates to end coordinates."""
        # TODO: Implement swipe gesture
        pass
    
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    create_mobile_mcp_server()
```

## Related Documentation

- **[MCP Overview](../../mcp/overview.md)** - Model Context Protocol
- **[Creating MCP Servers](../creating_mcp_servers.md)** - General MCP server tutorial
- **[Linux MCP Server](../../linux/commands.md)** - LinuxAgent MCP reference

---

**Previous**: [← Part 1: Core Components](core_components.md)  
**Next**: [Part 3: Configuration & Deployment →](configuration.md)
