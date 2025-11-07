# Part 4: Configuration & Deployment

!!! info "Coming Soon"
    This tutorial is currently under development. Check back soon for detailed configuration and deployment instructions.

## What You'll Learn

- Configuring `third_party.yaml`
- Registering devices in `devices.yaml`
- Creating prompt templates
- Deploying server and client
- Galaxy multi-device integration

## Temporary Quick Guide

### Configuration Files

#### `config/ufo/third_party.yaml`

```yaml
ENABLED_THIRD_PARTY_AGENTS: ["MobileAgent"]

THIRD_PARTY_AGENT_CONFIG:
  MobileAgent:
    VISUAL_MODE: True
    AGENT_NAME: "MobileAgent"
    APPAGENT_PROMPT: "ufo/prompts/third_party/mobile_agent.yaml"
    APPAGENT_EXAMPLE_PROMPT: "ufo/prompts/third_party/mobile_agent_example.yaml"
    INTRODUCTION: "MobileAgent controls Android/iOS mobile devices..."
```

#### `config/galaxy/devices.yaml`

```yaml
devices:
  - device_id: "mobile_agent_1"
    server_url: "ws://localhost:5010/ws"
    os: "android"
    capabilities: ["ui_automation", "app_testing"]
    metadata:
      device_model: "Pixel 6"
      android_version: "13"
    max_retries: 5
```

### Deployment Steps

1. Start Agent Server:
```bash
python -m ufo.server.app --port 5010
```

2. Start Device Client:
```bash
python -m ufo.client.client \
  --ws --ws-server ws://localhost:5010/ws \
  --client-id mobile_agent_1 \
  --platform android
```

3. Start MCP Server:
```bash
python -m ufo.client.mcp.http_servers.mobile_mcp_server --port 8020
```

## Related Documentation

- **[Third-Party Configuration](../../configuration/system/third_party_config.md)** - Configuration reference
- **[Galaxy Configuration](../../galaxy/overview.md)** - Multi-device setup
- **[Server Quick Start](../../server/quick_start.md)** - Server deployment

---

**Previous**: [← Part 3: Client Setup](client_setup.md)  
**Next**: [Part 5: Testing & Debugging →](testing.md)
