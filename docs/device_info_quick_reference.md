# Device Info Feature - Quick Reference

## 快速开始

### 1. Device端自动上报（无需配置）
Device client在注册时会自动收集并上报系统信息：
```python
# ufo/client/websocket.py
# 注册时自动执行，无需手动调用
await websocket_client.register_client()
```

### 2. Server端配置（可选）
创建配置文件 `config/my_devices.yaml`:
```yaml
devices:
  my_device_001:
    tags: ["production"]
    tier: "high_performance"
    additional_features: ["excel_macros"]
    max_concurrent_tasks: 5
```

启动服务器时加载配置：
```python
ws_manager = WSManager(device_config_path="config/my_devices.yaml")
```

### 3. Constellation端查询
```python
# 查询特定设备信息
device_info = await connection_manager.request_device_info("device_001")

print(f"Platform: {device_info['platform']}")
print(f"CPU: {device_info['cpu_count']}")
print(f"Memory: {device_info['memory_total_gb']} GB")
print(f"Features: {device_info['supported_features']}")
```

## 设备信息结构

```python
{
    "device_id": "device_001",
    "platform": "windows",           # windows/linux/darwin
    "os_version": "10.0.19041",
    "cpu_count": 8,
    "memory_total_gb": 16.0,
    "hostname": "my-computer",
    "ip_address": "192.168.1.100",
    "supported_features": [          # 自动检测的功能
        "gui",
        "cli",
        "browser",
        "file_system",
        "office",
        "windows_apps"
    ],
    "platform_type": "computer",     # computer/mobile/web/iot
    "schema_version": "1.0",
    "custom_metadata": {             # 服务端配置的额外信息
        "tags": ["production"],
        "tier": "high_performance"
    }
}
```

## 消息类型

### Constellation -> Server
```python
ClientMessage(
    type=ClientMessageType.DEVICE_INFO_REQUEST,
    client_type=ClientType.CONSTELLATION,
    target_id="device_001",
    ...
)
```

### Server -> Constellation
```python
ServerMessage(
    type=ServerMessageType.DEVICE_INFO_RESPONSE,
    result={...device_info...},
    status=TaskStatus.OK,
    ...
)
```

## API参考

### DeviceInfoProvider
```python
from ufo.client.device_info_provider import DeviceInfoProvider

# 收集系统信息
info = DeviceInfoProvider.collect_system_info(
    client_id="device_001",
    custom_metadata={"env": "prod"}
)

# 转换为字典
info_dict = info.to_dict()
```

### WSManager
```python
# 获取设备信息
device_info = ws_manager.get_device_system_info("device_001")

# 获取所有设备信息
all_devices = ws_manager.get_all_devices_info()
```

### Connection Manager
```python
# 请求设备信息
info = await connection_manager.request_device_info("device_001")
```

## 智能设备选择示例

### 根据平台选择
```python
async def select_device_by_platform(devices, platform):
    for device_id in devices:
        info = await request_device_info(device_id)
        if info and info["platform"] == platform:
            return device_id
    return None
```

### 根据功能选择
```python
async def select_device_with_feature(devices, feature):
    for device_id in devices:
        info = await request_device_info(device_id)
        if info and feature in info["supported_features"]:
            return device_id
    return None
```

### 根据资源选择
```python
async def select_high_performance_device(devices):
    candidates = []
    for device_id in devices:
        info = await request_device_info(device_id)
        if info:
            score = info["cpu_count"] * info["memory_total_gb"]
            candidates.append((device_id, score))
    
    # 返回资源最多的设备
    if candidates:
        return max(candidates, key=lambda x: x[1])[0]
    return None
```

### 根据标签选择
```python
async def select_device_by_tag(devices, tag):
    for device_id in devices:
        info = await request_device_info(device_id)
        if info:
            tags = info.get("custom_metadata", {}).get("tags", [])
            if tag in tags:
                return device_id
    return None
```

## 配置示例

### 最小配置
```yaml
devices:
  device_001:
    tags: ["production"]
```

### 完整配置
```yaml
devices:
  device_001:
    # 分类标签
    tags: ["production", "office_automation", "windows"]
    
    # 性能层级
    tier: "high_performance"
    
    # 额外功能
    additional_features:
      - "excel_macros"
      - "power_automate"
    
    # 资源限制
    max_concurrent_tasks: 5
    priority: "high"
    
    # 业务信息
    department: "Finance"
    environment: "production"
    
    # 位置信息
    location:
      datacenter: "US-West"
      building: "Main Office"
    
    # 可用时间
    business_hours: "09:00-18:00 UTC-8"
```

## 故障排查

### 设备信息未收集
检查日志中是否有错误：
```
[WS] Error collecting device info: ...
```
即使收集失败，设备也会正常注册（只是没有系统信息）。

### 查询返回None
可能原因：
1. 设备未连接到服务器
2. 设备是constellation client（不是device）
3. 设备注册时未上报系统信息

检查：
```python
# 检查设备是否连接
if ws_manager.is_device_connected("device_001"):
    info = ws_manager.get_device_system_info("device_001")
```

### 服务端配置未生效
确保：
1. 配置文件路径正确
2. YAML/JSON格式正确
3. device_id匹配
4. WSManager初始化时传入了配置路径

查看日志：
```
[WSManager] Loaded 3 device configurations
[WSManager] Merged server config for device device_001
```

## 测试命令

```bash
# 运行所有测试
python tests/run_device_info_tests.py

# 运行单元测试
python -m pytest tests/unit/test_device_info_provider.py -v
python -m pytest tests/unit/test_ws_manager_device_info.py -v

# 运行集成测试
python -m pytest tests/integration/test_device_info_flow.py -v

# 运行演示
python tests/demo_device_info.py
```

## 常见问题

**Q: 设备信息多久更新一次？**
A: 当前实现中，设备信息在注册时收集一次。如需动态更新，可实现Pull模式。

**Q: 可以收集哪些信息？**
A: 当前收集：platform, os_version, cpu_count, memory_total_gb, hostname, ip_address, features。不收集敏感信息。

**Q: 支持哪些平台？**
A: 完全支持Windows/Linux/macOS。预留了Mobile/Web/IoT接口。

**Q: 服务端配置是必需的吗？**
A: 不是。设备会自动收集系统信息。服务端配置是可选的补充。

**Q: 如何添加自定义字段？**
A: 通过服务端配置文件的custom_metadata或在DeviceInfoProvider中扩展。

## 更多信息

详细文档: `docs/device_info_implementation_summary.md`
