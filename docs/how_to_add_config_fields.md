# 如何添加新配置项

## 🎯 核心理念：零代码添加！

新配置系统的最大优势：**直接在 YAML 文件中添加字段，无需修改任何 Python 代码！**

---

## 🚀 快速添加（3 步完成）

### 方法 1: 动态字段（推荐，最简单）

#### 1️⃣ 在 YAML 中添加字段

```yaml
# config/ufo/custom.yaml（新建或编辑任意 YAML 文件）

# 添加顶层字段
NEW_FEATURE_ENABLED: true
CUSTOM_TIMEOUT: 30
MY_API_KEY: "your-key-here"

# 添加嵌套字段
ADVANCED_SETTINGS:
  retry_count: 3
  cache_enabled: true
  models:
    - gpt-4
    - gpt-3.5-turbo
```

#### 2️⃣ 立即在代码中使用

```python
from config.config_loader import get_ufo_config

config = get_ufo_config()

# ✅ 直接访问，无需任何其他步骤！
enabled = config.NEW_FEATURE_ENABLED
timeout = config.CUSTOM_TIMEOUT
api_key = config.MY_API_KEY

# ✅ 嵌套访问
retry = config.ADVANCED_SETTINGS.retry_count
cache = config.ADVANCED_SETTINGS.cache_enabled
models = config.ADVANCED_SETTINGS.models
```

#### 3️⃣ 完成！🎉

就这么简单！配置系统会自动发现并加载所有 YAML 字段。

---

## 📁 方法 2: 结构化添加（推荐用于复杂配置）

### 场景：添加新的模块化配置（如新增一个 Agent）

#### 1️⃣ 创建新的 YAML 文件

```yaml
# config/ufo/evaluator_agent.yaml（新建文件）

EVALUATOR_AGENT:
  API_TYPE: "openai"
  API_MODEL: "gpt-4"
  API_BASE: "https://api.openai.com/v1"
  API_KEY: "YOUR_KEY"
  MAX_TOKENS: 2000
  TEMPERATURE: 0.7
  TOP_P: 0.9
  RESPONSE_FORMAT: "text"
  
  # 特定配置
  EVALUATION_METRICS:
    - accuracy
    - efficiency
    - user_satisfaction
  
  ENABLE_FEEDBACK: true
  FEEDBACK_THRESHOLD: 0.8
```

#### 2️⃣ 代码中访问

```python
from config.config_loader import get_ufo_config

config = get_ufo_config()

# ✅ 直接访问新 Agent 配置
evaluator = config.EVALUATOR_AGENT
model = evaluator.API_MODEL
metrics = evaluator.EVALUATION_METRICS

# 或者字典方式
model = config["EVALUATOR_AGENT"]["API_MODEL"]
```

#### 3️⃣ （可选）添加到 Schema 以获得类型提示

```python
# config/config_schemas.py

class UFOConfig(BaseModel):
    # ... 现有字段 ...
    
    # 添加新的 Agent 配置
    evaluator_agent: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Evaluator agent configuration"
    )
```

现在你获得了 IDE 自动补全：
```python
config = get_ufo_config()
config.evaluator_agent.  # ← IDE 会自动补全！
```

---

## 🎨 实际案例演示

### 案例 1: 添加新的 RAG 功能配置

#### YAML 配置
```yaml
# config/ufo/rag.yaml（编辑现有文件）

# 原有配置...
RAG_EXPERIENCE: true
RAG_DEMONSTRATION: true

# ✨ 新增：知识图谱检索
RAG_KNOWLEDGE_GRAPH: true
RAG_KG_RETRIEVED_TOPK: 5
RAG_KG_MIN_SCORE: 0.7
RAG_KG_DATABASE_PATH: "vectordb/knowledge_graph"

# ✨ 新增：多模态检索
RAG_MULTIMODAL: false
RAG_MULTIMODAL_IMAGE_ENABLED: true
RAG_MULTIMODAL_VIDEO_ENABLED: false
```

#### 代码使用
```python
config = get_ufo_config()
rag = config.rag  # 或 config["RAG"]

# ✅ 立即可用！
if rag.knowledge_graph:  # 或 config["RAG_KNOWLEDGE_GRAPH"]
    results = kg_db.retrieve(
        query,
        topk=rag.kg_retrieved_topk,
        min_score=rag.kg_min_score
    )

if rag.multimodal and rag.multimodal_image_enabled:
    image_results = multimodal_search(query)
```

---

### 案例 2: 添加实验性功能开关

#### YAML 配置
```yaml
# config/ufo/experiments.yaml（新建文件）

EXPERIMENTS:
  # 功能开关
  enable_auto_recovery: true
  enable_parallel_execution: false
  enable_cloud_sync: false
  
  # 实验参数
  auto_recovery:
    max_retries: 3
    backoff_seconds: 5
    recovery_strategies:
      - "rollback"
      - "partial_retry"
      - "skip"
  
  parallel_execution:
    max_workers: 4
    timeout_per_task: 300
```

#### 代码使用
```python
config = get_ufo_config()
exp = config.EXPERIMENTS

# ✅ 功能开关
if exp.enable_auto_recovery:
    recovery_cfg = exp.auto_recovery
    for i in range(recovery_cfg.max_retries):
        try:
            execute_task()
            break
        except Exception:
            time.sleep(recovery_cfg.backoff_seconds)

if exp.enable_parallel_execution:
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=exp.parallel_execution.max_workers) as executor:
        # 并行执行
        pass
```

---

### 案例 3: 添加环境特定配置

#### 开发环境配置
```yaml
# config/ufo/config_dev.yaml（开发环境）

DEBUG_MODE: true
LOG_LEVEL: "DEBUG"
ENABLE_PROFILING: true
MOCK_API_CALLS: true

DEV_SETTINGS:
  hot_reload: true
  verbose_logging: true
  save_intermediate_results: true
  test_data_path: "tests/fixtures"
```

#### 生产环境配置
```yaml
# config/ufo/config_prod.yaml（生产环境）

DEBUG_MODE: false
LOG_LEVEL: "WARNING"
ENABLE_PROFILING: false
MOCK_API_CALLS: false

PROD_SETTINGS:
  performance_monitoring: true
  error_reporting: true
  cache_enabled: true
```

#### 代码使用
```python
config = get_ufo_config()

# ✅ 环境自适应
if config.DEBUG_MODE:
    logger.setLevel(logging.DEBUG)
    print(f"Dev settings: {config.DEV_SETTINGS}")

if hasattr(config, 'PROD_SETTINGS') and config.PROD_SETTINGS.performance_monitoring:
    enable_performance_tracking()
```

---

## 🔧 高级技巧

### 技巧 1: 使用环境变量覆盖

```python
# 环境变量命名规则：使用双下划线分隔嵌套层级
import os

# 覆盖顶层字段
os.environ["NEW_FEATURE_ENABLED"] = "false"

# 覆盖嵌套字段
os.environ["ADVANCED_SETTINGS__retry_count"] = "5"
os.environ["EVALUATOR_AGENT__API_MODEL"] = "gpt-4-turbo"

config = get_ufo_config()
# ✅ 环境变量优先级最高
print(config.NEW_FEATURE_ENABLED)  # → False
```

---

### 技巧 2: 动态加载不同配置文件

```yaml
# config/ufo/agents.yaml（基础配置）
APP_AGENT:
  API_MODEL: "gpt-4"
  TEMPERATURE: 0.7

# config/ufo/agents_experimental.yaml（实验配置）
APP_AGENT:
  API_MODEL: "gpt-4-turbo"
  TEMPERATURE: 0.9
  EXPERIMENTAL_FEATURES: true
```

系统会自动合并所有 YAML 文件！

---

### 技巧 3: 使用默认值保证安全

```python
config = get_ufo_config()

# ✅ 安全访问（带默认值）
feature_enabled = getattr(config, 'NEW_FEATURE', False)
timeout = getattr(config, 'TIMEOUT', 30)

# ✅ 字典方式
feature_enabled = config.get('NEW_FEATURE', False)

# ✅ 检查是否存在
if hasattr(config, 'NEW_FEATURE'):
    # 使用新功能
    pass
```

---

## 📋 完整工作流示例

### 需求：添加多语言支持配置

#### Step 1: 创建配置文件

```yaml
# config/ufo/i18n.yaml

INTERNATIONALIZATION:
  enabled: true
  default_language: "en"
  supported_languages:
    - "en"
    - "zh"
    - "ja"
    - "es"
  
  translation:
    auto_detect: true
    fallback_to_english: true
    cache_translations: true
  
  locale_settings:
    date_format: "YYYY-MM-DD"
    time_format: "24h"
    timezone: "UTC"
```

#### Step 2: 在代码中使用

```python
# ufo/utils/i18n.py

from config.config_loader import get_ufo_config

class I18nManager:
    def __init__(self):
        config = get_ufo_config()
        self.i18n_config = config.INTERNATIONALIZATION
        
        # ✅ 直接使用配置
        self.enabled = self.i18n_config.enabled
        self.default_lang = self.i18n_config.default_language
        self.supported = self.i18n_config.supported_languages
        
    def translate(self, text: str, target_lang: str = None):
        if not self.enabled:
            return text
        
        target = target_lang or self.default_lang
        
        if target not in self.supported:
            if self.i18n_config.translation.fallback_to_english:
                target = "en"
            else:
                raise ValueError(f"Unsupported language: {target}")
        
        # 翻译逻辑...
        return translated_text
```

#### Step 3: 测试

```python
# tests/test_i18n.py

from config.config_loader import get_ufo_config

def test_i18n_config():
    config = get_ufo_config()
    
    # ✅ 验证配置加载
    assert hasattr(config, 'INTERNATIONALIZATION')
    i18n = config.INTERNATIONALIZATION
    
    assert i18n.enabled == True
    assert i18n.default_language == "en"
    assert "zh" in i18n.supported_languages
    
    # ✅ 验证嵌套配置
    assert i18n.translation.auto_detect == True
    assert i18n.locale_settings.timezone == "UTC"
```

#### Step 4: 文档更新

```markdown
# docs/i18n_guide.md

## 多语言配置

配置文件：`config/ufo/i18n.yaml`

- `INTERNATIONALIZATION.enabled`: 启用多语言支持
- `INTERNATIONALIZATION.default_language`: 默认语言
- `INTERNATIONALIZATION.supported_languages`: 支持的语言列表
```

---

## ✅ 最佳实践

### 1. 命名规范

```yaml
# ✅ 推荐：使用大写+下划线（兼容旧配置）
NEW_FEATURE_ENABLED: true
MAX_RETRY_COUNT: 3

# ✅ 推荐：嵌套用小写+下划线
ADVANCED_CONFIG:
  retry_count: 3
  enable_cache: true

# ❌ 避免：混合命名风格
newFeatureEnabled: true  # 驼峰（不推荐）
max-retry-count: 3       # 短横线（无法用属性访问）
```

### 2. 结构组织

```yaml
# ✅ 推荐：按功能模块分组
RAG_CONFIG:
  experience:
    enabled: true
    topk: 5
  demonstration:
    enabled: true
    topk: 3
  knowledge_graph:
    enabled: false
    topk: 10

# ❌ 避免：扁平化所有配置
RAG_EXPERIENCE_ENABLED: true
RAG_EXPERIENCE_TOPK: 5
RAG_DEMO_ENABLED: true
RAG_DEMO_TOPK: 3
# ... 太多顶层字段
```

### 3. 默认值处理

```yaml
# ✅ 推荐：为可选功能提供明确的默认值
OPTIONAL_FEATURES:
  feature_a: false  # 明确禁用
  feature_b: true   # 明确启用
  timeout: 30       # 明确的数值

# ✅ 代码中也使用默认值
enabled = config.get('OPTIONAL_FEATURE', False)
```

### 4. 文档注释

```yaml
# ✅ 推荐：添加注释说明
# 新的实验性功能：自动任务恢复
# 启用后，失败的任务会自动重试
AUTO_RECOVERY:
  enabled: false  # 默认禁用，需手动开启
  max_retries: 3  # 最大重试次数
  backoff: 5      # 重试间隔（秒）
```

---

## 🔍 配置验证

### 使用验证工具检查新配置

```bash
# 验证配置正确性
python -m ufo.tools.validate_config

# 输出示例：
# ✓ Configuration valid
# ✓ Found 5 YAML files in config/ufo/
# ✓ NEW_FEATURE_ENABLED: true
# ✓ INTERNATIONALIZATION loaded successfully
```

### 代码中验证

```python
from config.config_loader import get_ufo_config

config = get_ufo_config()

# ✅ 验证必需字段
required_fields = ['APP_AGENT', 'HOST_AGENT', 'SYSTEM']
for field in required_fields:
    assert hasattr(config, field), f"Missing required config: {field}"

# ✅ 验证新添加的字段
if hasattr(config, 'NEW_FEATURE'):
    assert isinstance(config.NEW_FEATURE, bool), "NEW_FEATURE must be boolean"
```

---

## 📊 配置优先级总结

```
优先级（从高到低）：

1. 环境变量              os.environ["FIELD_NAME"] = "value"
   ↓
2. config/ufo/*.yaml     新配置路径（推荐）
   ↓
3. ufo/config/*.yaml     旧配置路径（向后兼容）
   ↓
4. 代码中的默认值         getattr(config, 'FIELD', default)
```

---

## 🎯 快速检查清单

添加新配置项时，检查以下项目：

- [ ] 在 `config/ufo/` 下创建或编辑 YAML 文件
- [ ] 使用清晰的命名（大写+下划线）
- [ ] 添加注释说明用途
- [ ] 提供合理的默认值
- [ ] 在代码中使用 `get_ufo_config()` 访问
- [ ] 运行验证工具测试 `python -m ufo.tools.validate_config`
- [ ] 添加单元测试验证配置加载
- [ ] （可选）更新文档说明新配置

---

## ❓ 常见问题

**Q: 必须重启程序才能生效吗？**  
A: 是的，配置在程序启动时加载并缓存。如需热重载，可以调用 `reload_ufo_config()`。

**Q: 可以在运行时修改配置吗？**  
A: 可以修改配置对象，但不推荐。建议使用环境变量或创建新配置文件。

**Q: 新增字段会破坏旧代码吗？**  
A: 不会！新字段是增量添加，不影响现有字段。

**Q: 如何删除配置项？**  
A: 从 YAML 删除字段即可。代码中使用 `getattr()` 或 `get()` 提供默认值避免报错。

**Q: 配置文件可以有多少个？**  
A: 无限制！系统会自动加载 `config/ufo/` 下所有 `.yaml` 文件并合并。

---

## 📚 相关文档

- [配置使用示例](config_usage_examples.md) - 代码示例
- [配置结构指南](configuration_guide.md) - 完整配置说明
- [快速参考](config_quick_reference.txt) - 速查表
- [迁移工具](../ufo/tools/README_CONFIG.md) - 配置迁移
