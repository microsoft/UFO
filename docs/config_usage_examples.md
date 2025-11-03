# 配置读取使用示例

## 📚 快速对比

### ❌ 旧方式（仍然支持，但不推荐）
```python
from ufo.config import Config

configs = Config.get_instance().config_data

# 只能用字典方式访问
api_model = configs["APP_AGENT"]["API_MODEL"]
max_step = configs["MAX_STEP"]
rag_enabled = configs["RAG_EXPERIENCE"]
```

### ✅ 新方式（推荐）
```python
from config.config_loader import get_ufo_config

config = get_ufo_config()

# 🎯 类型安全的属性访问（有 IDE 自动补全！）
api_model = config.app_agent.api_model
max_step = config.system.max_step
rag_enabled = config.rag.experience

# 📦 也支持字典访问（向后兼容）
api_model = config["APP_AGENT"]["API_MODEL"]
max_step = config["MAX_STEP"]
```

---

## 🔄 迁移指南：实际代码示例

### 示例 1: Agent 配置访问

**旧代码（app_agent.py）：**
```python
from ufo.config import Config

class AppAgent:
    def __init__(self):
        configs = Config.get_instance().config_data
        
        # 字典访问
        self.api_model = configs["APP_AGENT"]["API_MODEL"]
        self.api_type = configs["APP_AGENT"]["API_TYPE"]
        self.max_tokens = configs["APP_AGENT"]["MAX_TOKENS"]
        self.temperature = configs["APP_AGENT"]["TEMPERATURE"]
```

**新代码（推荐）：**
```python
from config.config_loader import get_ufo_config

class AppAgent:
    def __init__(self):
        config = get_ufo_config()
        
        # ✨ 类型安全的属性访问
        self.api_model = config.app_agent.api_model
        self.api_type = config.app_agent.api_type
        self.max_tokens = config.app_agent.max_tokens
        self.temperature = config.app_agent.temperature
        
        # 💡 或者更简洁：
        agent_cfg = config.app_agent
        self.api_model = agent_cfg.api_model
        self.api_type = agent_cfg.api_type
```

---

### 示例 2: RAG 配置访问

**旧代码：**
```python
from ufo.config import get_config

configs = get_config()

if configs["RAG_EXPERIENCE"]:
    experience_results = self.rag_experience_retrieve(
        request, configs["RAG_EXPERIENCE_RETRIEVED_TOPK"]
    )

if configs["RAG_DEMONSTRATION"]:
    demo_results = self.rag_demo_retrieve(
        request, configs["RAG_DEMONSTRATION_RETRIEVED_TOPK"]
    )
```

**新代码（推荐）：**
```python
from config.config_loader import get_ufo_config

config = get_ufo_config()

# ✨ 清晰的模块化访问
if config.rag.experience:
    experience_results = self.rag_experience_retrieve(
        request, config.rag.experience_retrieved_topk
    )

if config.rag.demonstration:
    demo_results = self.rag_demo_retrieve(
        request, config.rag.demonstration_retrieved_topk
    )

# 💡 批量访问
rag = config.rag
if rag.experience:
    results = self.retrieve(request, rag.experience_retrieved_topk)
```

---

### 示例 3: 系统配置访问

**旧代码：**
```python
configs = get_config()

max_step = configs["MAX_STEP"]
log_level = configs["LOG_LEVEL"]
control_backend = configs["CONTROL_BACKEND"]
```

**新代码：**
```python
config = get_ufo_config()

# ✨ 语义化的访问路径
max_step = config.system.max_step
log_level = config.system.log_level
control_backend = config.system.control_backend
```

---

### 示例 4: API 配置（多 Agent）

**旧代码：**
```python
configs = get_config()

# Host Agent
host_model = configs["HOST_AGENT"]["API_MODEL"]
host_type = configs["HOST_AGENT"]["API_TYPE"]

# App Agent
app_model = configs["APP_AGENT"]["API_MODEL"]
app_type = configs["APP_AGENT"]["API_TYPE"]

# Backup Agent
backup_model = configs["BACKUP_AGENT"]["API_MODEL"]
```

**新代码：**
```python
config = get_ufo_config()

# ✨ 每个 Agent 都有独立的配置对象
host_model = config.host_agent.api_model
host_type = config.host_agent.api_type

app_model = config.app_agent.api_model
app_type = config.app_agent.api_type

backup_model = config.backup_agent.api_model

# 💡 批量访问
agents = {
    "host": config.host_agent,
    "app": config.app_agent,
    "backup": config.backup_agent
}
```

---

### 示例 5: 动态字段访问（自定义配置）

**新系统的强大之处：无需修改代码即可支持新字段！**

```python
config = get_ufo_config()

# ✨ 直接访问 YAML 中的任何字段
custom_value = config.CUSTOM_FEATURE  # 属性访问
custom_value = config["CUSTOM_FEATURE"]  # 字典访问

# 🎯 嵌套字段
nested = config.MY_MODULE.SUB_CONFIG.SETTING
```

**在 YAML 中添加新字段后，立即可用：**
```yaml
# config/ufo/custom.yaml
CUSTOM_FEATURE: enabled
MY_MODULE:
  SUB_CONFIG:
    SETTING: value
```

---

## 🚀 完整实战示例

### 场景：重构 AppAgent 类

**原始代码（ufo/agents/agent/app_agent.py）：**
```python
from ufo.config import Config

class AppAgent:
    def __init__(self, name: str, app_root_name: str):
        self._name = name
        self._app_root_name = app_root_name
        
        configs = Config.get_instance().config_data
        
        # API 配置
        self.api_model = configs["APP_AGENT"]["API_MODEL"]
        self.api_type = configs["APP_AGENT"]["API_TYPE"]
        
        # RAG 配置
        self.rag_experience = configs["RAG_EXPERIENCE"]
        self.rag_demo = configs["RAG_DEMONSTRATION"]
        
        # 系统配置
        self.max_step = configs["MAX_STEP"]
    
    def retrieve_context(self, request: str):
        configs = Config.get_instance().config_data
        
        if configs["RAG_EXPERIENCE"]:
            results = self.experience_db.retrieve(
                request, 
                configs["RAG_EXPERIENCE_RETRIEVED_TOPK"]
            )
        
        if configs["RAG_DEMONSTRATION"]:
            demos = self.demo_db.retrieve(
                request,
                configs["RAG_DEMONSTRATION_RETRIEVED_TOPK"]
            )
```

**重构后（推荐）：**
```python
from config.config_loader import get_ufo_config

class AppAgent:
    def __init__(self, name: str, app_root_name: str):
        self._name = name
        self._app_root_name = app_root_name
        
        # ✨ 一次加载，全局缓存
        config = get_ufo_config()
        
        # 🎯 类型安全的 API 配置
        agent_cfg = config.app_agent
        self.api_model = agent_cfg.api_model
        self.api_type = agent_cfg.api_type
        
        # 🎯 清晰的 RAG 配置
        rag_cfg = config.rag
        self.rag_experience = rag_cfg.experience
        self.rag_demo = rag_cfg.demonstration
        
        # 🎯 系统配置
        self.max_step = config.system.max_step
    
    def retrieve_context(self, request: str):
        # ✨ 配置已缓存，直接访问
        config = get_ufo_config()
        rag = config.rag
        
        if rag.experience:
            results = self.experience_db.retrieve(
                request, 
                rag.experience_retrieved_topk
            )
        
        if rag.demonstration:
            demos = self.demo_db.retrieve(
                request,
                rag.demonstration_retrieved_topk
            )
```

---

## 🌟 高级用法

### 1. Galaxy 配置（多设备）

```python
from config.config_loader import get_galaxy_config

# 🌌 Galaxy 专用配置
config = get_galaxy_config()

# 设备配置
device_cfg = config.device
server_port = device_cfg.server_port
timeout = device_cfg.timeout

# 协调器配置
orchestrator = config.orchestrator
strategy = orchestrator.strategy
```

### 2. 环境变量覆盖

```python
# 环境变量优先级最高
import os
os.environ["APP_AGENT__API_MODEL"] = "gpt-4-turbo"

config = get_ufo_config()
print(config.app_agent.api_model)  # → "gpt-4-turbo"
```

### 3. 配置验证

```python
from config.config_loader import get_ufo_config

config = get_ufo_config()

# ✅ 自动类型转换
max_step = config.system.max_step  # int
temperature = config.app_agent.temperature  # float
rag_enabled = config.rag.experience  # bool
```

### 4. 配置热重载（高级）

```python
from config.config_loader import reload_ufo_config

# 重新加载配置（清除缓存）
config = reload_ufo_config()
```

---

## 📋 配置字段映射表

| 旧字段路径 | 新字段路径 | 说明 |
|-----------|-----------|------|
| `configs["APP_AGENT"]["API_MODEL"]` | `config.app_agent.api_model` | App Agent API 模型 |
| `configs["HOST_AGENT"]["API_MODEL"]` | `config.host_agent.api_model` | Host Agent API 模型 |
| `configs["MAX_STEP"]` | `config.system.max_step` | 最大步数 |
| `configs["RAG_EXPERIENCE"]` | `config.rag.experience` | RAG 经验检索 |
| `configs["RAG_DEMONSTRATION"]` | `config.rag.demonstration` | RAG 演示检索 |
| `configs["CONTROL_BACKEND"]` | `config.system.control_backend` | 控制后端 |
| `configs["LOG_LEVEL"]` | `config.system.log_level` | 日志级别 |
| `configs["VISUAL_MODE"]` | `config.system.visual_mode` | 可视化模式 |

---

## 🎯 最佳实践

### ✅ 推荐做法

```python
# 1. 在模块顶部导入
from config.config_loader import get_ufo_config

# 2. 在初始化时加载一次
class MyAgent:
    def __init__(self):
        config = get_ufo_config()
        self.config = config  # 保存引用
        
    def process(self):
        # 3. 使用保存的引用
        if self.config.rag.experience:
            ...

# 4. 使用属性访问（有 IDE 支持）
api_model = config.app_agent.api_model

# 5. 批量访问相关配置
rag = config.rag
if rag.experience:
    topk = rag.experience_retrieved_topk
```

### ❌ 避免做法

```python
# ❌ 每次都重新加载
def process():
    configs = Config.get_instance().config_data  # 旧方式
    
# ❌ 硬编码字典访问
value = configs["LONG"]["NESTED"]["PATH"]["KEY"]  # 易出错

# ❌ 混用新旧方式
configs = get_config()  # 旧
config = get_ufo_config()  # 新
```

---

## 🔧 迁移检查清单

- [ ] 替换 `from ufo.config import Config` → `from config.config_loader import get_ufo_config`
- [ ] 替换 `Config.get_instance().config_data` → `get_ufo_config()`
- [ ] 将字典访问改为属性访问（可选但推荐）
- [ ] 测试所有配置读取路径
- [ ] 运行测试套件验证
- [ ] 更新文档

---

## ❓ 常见问题

**Q: 旧代码会立即失效吗？**  
A: 不会！新系统完全向后兼容，旧代码继续工作。

**Q: 什么时候迁移？**  
A: 可以渐进式迁移，修改代码时顺便更新即可。

**Q: 新旧方式性能差异？**  
A: 新方式有配置缓存，性能更优。

**Q: 如何知道配置来自哪个路径？**  
A: 运行时会有警告提示（如果使用旧路径）。

**Q: 支持环境变量覆盖吗？**  
A: 支持！环境变量优先级最高。

---

## 📚 相关文档

- [配置文件结构指南](configuration_guide.md)
- [配置迁移工具](../ufo/tools/README_CONFIG.md)
- [技术实现文档](config_implementation_summary.md)
