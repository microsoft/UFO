"""
新配置系统：添加配置项实战演示

这个文件展示了如何添加新配置项并在代码中使用。
"""

# ═══════════════════════════════════════════════════════════════════
# 演示 1: 添加简单配置项
# ═══════════════════════════════════════════════════════════════════

# 步骤 1: 在 config/ufo/custom.yaml 添加（假设已添加）:
"""
ENABLE_AUTO_SAVE: true
AUTO_SAVE_INTERVAL: 300  # 秒
"""

# 步骤 2: 代码中使用
from config.config_loader import get_ufo_config


def demo_simple_config():
    """演示：读取简单配置项"""
    config = get_ufo_config()

    # ✅ 直接访问
    if config.ENABLE_AUTO_SAVE:
        interval = config.AUTO_SAVE_INTERVAL
        print(f"自动保存已启用，间隔：{interval}秒")
    else:
        print("自动保存已禁用")


# ═══════════════════════════════════════════════════════════════════
# 演示 2: 添加嵌套配置（新 Agent）
# ═══════════════════════════════════════════════════════════════════

# 在 config/ufo/agents.yaml 添加:
"""
EVALUATOR_AGENT:
  API_TYPE: "openai"
  API_MODEL: "gpt-4"
  API_BASE: "https://api.openai.com/v1"
  API_KEY: "YOUR_KEY"
  MAX_TOKENS: 2000
  TEMPERATURE: 0.7
  TOP_P: 0.9
  
  # 专用配置
  EVALUATION_CRITERIA:
    accuracy: 0.8
    efficiency: 0.7
    usability: 0.9
"""


def demo_nested_config():
    """演示：读取嵌套配置（新 Agent）"""
    config = get_ufo_config()

    # ✅ 属性访问（推荐）
    evaluator = config.EVALUATOR_AGENT

    print(f"Evaluator Agent:")
    print(f"  模型: {evaluator.API_MODEL}")
    print(f"  类型: {evaluator.API_TYPE}")
    print(f"  温度: {evaluator.TEMPERATURE}")

    # ✅ 访问深度嵌套
    criteria = evaluator.EVALUATION_CRITERIA
    print(f"\n评估标准:")
    print(f"  准确性: {criteria.accuracy}")
    print(f"  效率: {criteria.efficiency}")
    print(f"  可用性: {criteria.usability}")


# ═══════════════════════════════════════════════════════════════════
# 演示 3: 添加 RAG 扩展配置
# ═══════════════════════════════════════════════════════════════════

# 在 config/ufo/rag.yaml 添加:
"""
# 原有配置...
RAG_EXPERIENCE: true
RAG_DEMONSTRATION: true

# ✨ 新增：知识图谱检索
RAG_KNOWLEDGE_GRAPH:
  enabled: true
  topk: 5
  min_score: 0.7
  database_path: "vectordb/knowledge_graph"
  query_expansion: true

# ✨ 新增：多模态检索
RAG_MULTIMODAL:
  enabled: false
  image_search: true
  video_search: false
  audio_search: false
"""


def demo_rag_extension():
    """演示：使用扩展的 RAG 配置"""
    config = get_ufo_config()

    # ✅ 访问新增的 RAG 配置
    kg_config = config.RAG_KNOWLEDGE_GRAPH

    if kg_config.enabled:
        print(f"知识图谱检索已启用:")
        print(f"  TopK: {kg_config.topk}")
        print(f"  最低分数: {kg_config.min_score}")
        print(f"  数据库: {kg_config.database_path}")
        print(f"  查询扩展: {kg_config.query_expansion}")

        # 模拟检索
        results = knowledge_graph_retrieve(
            query="示例查询", topk=kg_config.topk, min_score=kg_config.min_score
        )

    # ✅ 多模态配置
    multimodal = config.RAG_MULTIMODAL
    if multimodal.enabled:
        search_modes = []
        if multimodal.image_search:
            search_modes.append("图像")
        if multimodal.video_search:
            search_modes.append("视频")
        if multimodal.audio_search:
            search_modes.append("音频")

        print(f"\n多模态检索: {', '.join(search_modes)}")


# ═══════════════════════════════════════════════════════════════════
# 演示 4: 实验性功能配置
# ═══════════════════════════════════════════════════════════════════

# 在 config/ufo/experiments.yaml 添加:
"""
EXPERIMENTS:
  # 功能开关
  auto_recovery: true
  parallel_execution: false
  cloud_sync: false
  
  # 详细配置
  recovery_settings:
    max_retries: 3
    backoff_factor: 2
    timeout: 300
    strategies:
      - "rollback"
      - "partial_retry"
      - "skip_failed"
  
  parallel_settings:
    max_workers: 4
    timeout_per_task: 600
    chunk_size: 10
"""


def demo_experimental_features():
    """演示：使用实验性功能配置"""
    config = get_ufo_config()
    exp = config.EXPERIMENTS

    # ✅ 功能开关
    if exp.auto_recovery:
        recovery = exp.recovery_settings

        print("自动恢复已启用:")
        print(f"  最大重试: {recovery.max_retries}")
        print(f"  退避因子: {recovery.backoff_factor}")
        print(f"  超时: {recovery.timeout}秒")
        print(f"  策略: {', '.join(recovery.strategies)}")

        # 使用配置
        for attempt in range(recovery.max_retries):
            try:
                execute_task()
                break
            except Exception as e:
                if attempt < recovery.max_retries - 1:
                    wait_time = recovery.backoff_factor**attempt
                    print(
                        f"重试 {attempt + 1}/{recovery.max_retries}，等待 {wait_time}秒..."
                    )
                    # time.sleep(wait_time)

    if exp.parallel_execution:
        parallel = exp.parallel_settings
        print(f"\n并行执行: {parallel.max_workers} workers")


# ═══════════════════════════════════════════════════════════════════
# 演示 5: 环境变量覆盖
# ═══════════════════════════════════════════════════════════════════


def demo_env_override():
    """演示：使用环境变量覆盖配置"""
    import os

    # ✅ 设置环境变量（运行前执行）
    os.environ["ENABLE_AUTO_SAVE"] = "false"
    os.environ["AUTO_SAVE_INTERVAL"] = "600"

    # 覆盖嵌套字段（双下划线）
    os.environ["EVALUATOR_AGENT__API_MODEL"] = "gpt-4-turbo"
    os.environ["RAG_KNOWLEDGE_GRAPH__topk"] = "10"

    # 重新加载配置（可选，如果想清除缓存）
    from config.config_loader import reload_ufo_config

    config = reload_ufo_config()

    print("环境变量覆盖后:")
    print(f"  自动保存: {config.ENABLE_AUTO_SAVE}")  # → False
    print(f"  保存间隔: {config.AUTO_SAVE_INTERVAL}")  # → 600
    print(f"  Evaluator 模型: {config.EVALUATOR_AGENT.API_MODEL}")  # → gpt-4-turbo
    print(f"  KG TopK: {config.RAG_KNOWLEDGE_GRAPH.topk}")  # → 10


# ═══════════════════════════════════════════════════════════════════
# 演示 6: 安全访问（可选配置）
# ═══════════════════════════════════════════════════════════════════


def demo_safe_access():
    """演示：安全访问可能不存在的配置"""
    config = get_ufo_config()

    # ✅ 方法 1: getattr 带默认值
    feature_enabled = getattr(config, "OPTIONAL_FEATURE", False)
    timeout = getattr(config, "OPTIONAL_TIMEOUT", 30)

    print(f"可选功能: {feature_enabled}")
    print(f"可选超时: {timeout}")

    # ✅ 方法 2: hasattr 检查
    if hasattr(config, "NEW_EXPERIMENTAL_FEATURE"):
        print(f"实验功能: {config.NEW_EXPERIMENTAL_FEATURE}")
    else:
        print("实验功能未配置，使用默认行为")

    # ✅ 方法 3: try-except
    try:
        value = config.SOME_OPTIONAL_CONFIG
        print(f"配置值: {value}")
    except AttributeError:
        print("配置不存在，使用默认值")
        value = "default_value"


# ═══════════════════════════════════════════════════════════════════
# 演示 7: 完整使用案例 - 多语言支持
# ═══════════════════════════════════════════════════════════════════

# 在 config/ufo/i18n.yaml 添加:
"""
I18N:
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
    cache_enabled: true
  
  locale:
    date_format: "YYYY-MM-DD"
    time_format: "24h"
    timezone: "UTC"
"""


class I18nManager:
    """多语言管理器示例"""

    def __init__(self):
        config = get_ufo_config()
        self.i18n_config = config.I18N

        self.enabled = self.i18n_config.enabled
        self.default_lang = self.i18n_config.default_language
        self.supported = self.i18n_config.supported_languages
        self.translation_cfg = self.i18n_config.translation
        self.locale_cfg = self.i18n_config.locale

    def is_supported(self, lang: str) -> bool:
        """检查语言是否支持"""
        return lang in self.supported

    def translate(self, text: str, target_lang: str = None):
        """翻译文本"""
        if not self.enabled:
            return text

        target = target_lang or self.default_lang

        if not self.is_supported(target):
            if self.translation_cfg.fallback_to_english:
                target = "en"
            else:
                raise ValueError(f"不支持的语言: {target}")

        # 翻译逻辑...
        return f"[{target}] {text}"

    def format_datetime(self, dt):
        """格式化日期时间"""
        date_fmt = self.locale_cfg.date_format
        time_fmt = self.locale_cfg.time_format
        # 格式化逻辑...
        return f"{date_fmt} {time_fmt}"


def demo_i18n():
    """演示：使用多语言配置"""
    i18n = I18nManager()

    print(f"多语言支持: {'启用' if i18n.enabled else '禁用'}")
    print(f"默认语言: {i18n.default_lang}")
    print(f"支持的语言: {', '.join(i18n.supported)}")
    print(f"自动检测: {i18n.translation_cfg.auto_detect}")
    print(f"日期格式: {i18n.locale_cfg.date_format}")

    # 使用翻译
    text = i18n.translate("Hello World", "zh")
    print(f"\n翻译结果: {text}")


# ═══════════════════════════════════════════════════════════════════
# 辅助函数（模拟）
# ═══════════════════════════════════════════════════════════════════


def knowledge_graph_retrieve(query: str, topk: int, min_score: float):
    """模拟知识图谱检索"""
    return [f"Result {i}" for i in range(topk)]


def execute_task():
    """模拟任务执行"""
    pass


# ═══════════════════════════════════════════════════════════════════
# 主程序
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("新配置系统：添加配置项实战演示")
    print("=" * 70)

    print("\n【演示 1】简单配置项")
    print("-" * 70)
    demo_simple_config()

    print("\n【演示 2】嵌套配置（新 Agent）")
    print("-" * 70)
    demo_nested_config()

    print("\n【演示 3】RAG 扩展配置")
    print("-" * 70)
    demo_rag_extension()

    print("\n【演示 4】实验性功能")
    print("-" * 70)
    demo_experimental_features()

    print("\n【演示 5】环境变量覆盖")
    print("-" * 70)
    demo_env_override()

    print("\n【演示 6】安全访问")
    print("-" * 70)
    demo_safe_access()

    print("\n【演示 7】完整案例 - 多语言")
    print("-" * 70)
    demo_i18n()

    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)
