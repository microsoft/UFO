# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Configuration Schema Definitions

Hybrid design: Fixed typed fields + dynamic field support.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentConfig:
    """
    Agent configuration with common fields + dynamic extras.

    Fixed fields provide IDE autocomplete and type safety.
    Any additional fields from YAML are accessible via dict-style or attribute access.
    """

    # ========== Fixed Common Fields (Type-Safe) ==========
    visual_mode: bool = True
    reasoning_model: bool = False
    api_type: str = "azure_ad"
    api_base: str = ""
    api_key: str = ""
    api_version: str = "2025-02-01-preview"
    api_model: str = "gpt-4.1-20250414"

    # Azure AD fields
    aad_tenant_id: Optional[str] = None
    aad_api_scope: Optional[str] = None
    aad_api_scope_base: Optional[str] = None
    api_deployment_id: Optional[str] = None

    # Prompt paths
    prompt: Optional[str] = None
    example_prompt: Optional[str] = None

    # ========== Dynamic Fields (Auto-populated from YAML) ==========
    _extras: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __getattr__(self, name: str) -> Any:
        """Support dynamic attribute access for extra fields"""
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        # Support uppercase access (API_MODEL, API_TYPE, etc.)
        # Map to lowercase attribute if exists
        lower_name = name.lower()
        if hasattr(self.__class__, lower_name):
            return getattr(self, lower_name)

        # Check extras (try both exact name and uppercase version)
        if name in self._extras:
            return self._extras[name]

        # If lowercase requested, try uppercase in extras
        upper_name = name.upper()
        if upper_name in self._extras:
            return self._extras[upper_name]

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __getitem__(self, key: str) -> Any:
        """Support dict-style access"""
        # Try fixed fields first
        if hasattr(self, key) and not key.startswith("_"):
            return getattr(self, key)
        # Then try extras
        if key in self._extras:
            return self._extras[key]
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator"""
        return (hasattr(self, key) and not key.startswith("_")) or (key in self._extras)

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-style get with default"""
        try:
            return self[key]
        except KeyError:
            return default

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """
        Create AgentConfig from dictionary.

        Known fields are mapped to typed attributes.
        Unknown fields are stored in _extras.
        """
        # Known field mappings
        known_fields = {
            "VISUAL_MODE": "visual_mode",
            "REASONING_MODEL": "reasoning_model",
            "API_TYPE": "api_type",
            "API_BASE": "api_base",
            "API_KEY": "api_key",
            "API_VERSION": "api_version",
            "API_MODEL": "api_model",
            "AAD_TENANT_ID": "aad_tenant_id",
            "AAD_API_SCOPE": "aad_api_scope",
            "AAD_API_SCOPE_BASE": "aad_api_scope_base",
            "API_DEPLOYMENT_ID": "api_deployment_id",
            "PROMPT": "prompt",
            "EXAMPLE_PROMPT": "example_prompt",
        }

        # Extract known fields
        kwargs = {}
        extras = {}

        for key, value in data.items():
            if key in known_fields:
                kwargs[known_fields[key]] = value
            else:
                # Store unknown fields as extras
                extras[key] = value

        # Create instance
        instance = cls(**kwargs)
        instance._extras = extras

        return instance


@dataclass
class RAGConfig:
    """RAG configuration with fixed fields + dynamic extras"""

    # ========== Fixed Fields ==========
    offline_docs: bool = False
    offline_docs_retrieved_topk: int = 1
    online_search: bool = False
    online_search_topk: int = 5
    online_retrieved_topk: int = 5
    experience: bool = False
    experience_retrieved_topk: int = 5
    demonstration: bool = False
    demonstration_retrieved_topk: int = 5

    # ========== Dynamic Fields ==========
    _extras: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        # Support uppercase access with RAG_ prefix (RAG_OFFLINE_DOCS -> offline_docs)
        if name.startswith("RAG_"):
            # Remove RAG_ prefix and convert to lowercase
            field_name = name[4:].lower()  # RAG_OFFLINE_DOCS -> offline_docs
            if hasattr(self.__class__, field_name):
                return getattr(self, field_name)

        # Support uppercase access without prefix (OFFLINE_DOCS -> offline_docs)
        lower_name = name.lower()
        if hasattr(self.__class__, lower_name):
            return getattr(self, lower_name)

        # Check extras (try both exact name and uppercase version)
        if name in self._extras:
            return self._extras[name]

        # If lowercase requested, try uppercase in extras
        upper_name = name.upper()
        if upper_name in self._extras:
            return self._extras[upper_name]

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key) and not key.startswith("_"):
            return getattr(self, key)
        if key in self._extras:
            return self._extras[key]
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RAGConfig":
        """Create RAGConfig with known fields + extras"""
        known_mappings = {
            "RAG_OFFLINE_DOCS": "offline_docs",
            "RAG_OFFLINE_DOCS_RETRIEVED_TOPK": "offline_docs_retrieved_topk",
            "RAG_ONLINE_SEARCH": "online_search",
            "RAG_ONLINE_SEARCH_TOPK": "online_search_topk",
            "RAG_ONLINE_RETRIEVED_TOPK": "online_retrieved_topk",
            "RAG_EXPERIENCE": "experience",
            "RAG_EXPERIENCE_RETRIEVED_TOPK": "experience_retrieved_topk",
            "RAG_DEMONSTRATION": "demonstration",
            "RAG_DEMONSTRATION_RETRIEVED_TOPK": "demonstration_retrieved_topk",
        }

        kwargs = {}
        extras = {}

        for key, value in data.items():
            if key in known_mappings:
                kwargs[known_mappings[key]] = value
            elif key.startswith("RAG_") or key in [
                "BING_API_KEY",
                "EXPERIENCE_SAVED_PATH",
                "DEMONSTRATION_SAVED_PATH",
                "EXPERIENCE_PROMPT",
                "DEMONSTRATION_PROMPT",
            ]:
                extras[key] = value

        instance = cls(**kwargs)
        instance._extras = extras
        return instance


@dataclass
class SystemConfig:
    """System configuration with fixed fields + dynamic extras"""

    # ========== LLM Parameters ==========
    max_tokens: int = 2000
    max_retry: int = 20
    temperature: float = 0.0
    top_p: float = 0.0
    timeout: int = 60

    # ========== Control Backend ==========
    control_backend: List[str] = field(default_factory=lambda: ["uia"])
    iou_threshold_for_merge: float = 0.1

    # ========== Execution Limits ==========
    max_step: int = 50
    max_round: int = 1
    sleep_time: int = 1
    rectangle_time: int = 1

    # ========== Action Configuration ==========
    action_sequence: bool = False
    show_visual_outline_on_screen: bool = False
    maximize_window: bool = False
    json_parsing_retry: int = 3

    # ========== Safety ==========
    safe_guard: bool = False
    control_list: List[str] = field(
        default_factory=lambda: [
            "Button",
            "Edit",
            "TabItem",
            "Document",
            "ListItem",
            "MenuItem",
            "ScrollBar",
            "TreeItem",
            "Hyperlink",
            "ComboBox",
            "RadioButton",
            "Spinner",
            "CheckBox",
            "Group",
            "Text",
        ]
    )

    # ========== History ==========
    history_keys: List[str] = field(
        default_factory=lambda: [
            "step",
            "subtask",
            "action_representation",
            "user_confirm",
        ]
    )

    # ========== Annotation ==========
    annotation_colors: Dict[str, str] = field(default_factory=dict)
    highlight_bbox: bool = True
    annotation_font_size: int = 22

    # ========== Control Actions ==========
    click_api: str = "click_input"
    after_click_wait: int = 0
    input_text_api: str = "type_keys"
    input_text_enter: bool = False
    input_text_inter_key_pause: float = 0.05

    # ========== Logging ==========
    print_log: bool = False
    concat_screenshot: bool = False
    log_level: str = "DEBUG"
    include_last_screenshot: bool = True
    request_timeout: int = 250
    log_xml: bool = False
    log_to_markdown: bool = True
    screenshot_to_memory: bool = True

    # ========== Image Performance ==========
    default_png_compress_level: int = 1

    # ========== Save Options ==========
    save_ui_tree: bool = False
    save_full_screen: bool = False

    # ========== Task Management ==========
    task_status: bool = True
    task_status_file: Optional[str] = None
    save_experience: str = "always_not"

    # ========== Evaluation ==========
    eva_session: bool = True
    eva_round: bool = False
    eva_all_screenshots: bool = True

    # ========== Customization ==========
    ask_question: bool = False
    use_customization: bool = False
    qa_pair_file: str = "customization/global_memory.jsonl"
    qa_pair_num: int = 20

    # ========== Omniparser ==========
    omniparser: Dict[str, Any] = field(default_factory=dict)

    # ========== Control Filtering ==========
    control_filter_type: List[str] = field(default_factory=list)
    control_filter_top_k_plan: int = 2
    control_filter_top_k_semantic: int = 15
    control_filter_top_k_icon: int = 15
    control_filter_model_semantic_name: str = "all-MiniLM-L6-v2"
    control_filter_model_icon_name: str = "clip-ViT-B-32"

    # ========== API Usage ==========
    use_apis: bool = True
    api_prompt: str = "ufo/prompts/share/base/api.yaml"

    # ========== MCP (Model Context Protocol) ==========
    use_mcp: bool = True
    mcp_servers_config: str = "config/ufo/mcp.yaml"
    mcp_preferred_apps: List[str] = field(default_factory=list)
    mcp_fallback_to_ui: bool = True
    mcp_instructions_path: str = "ufo/config/mcp_instructions"
    mcp_tool_timeout: int = 30
    mcp_log_execution: bool = False

    # ========== Device Configuration ==========
    device_info: str = "config/device_config.yaml"

    # ========== Prompt Paths ==========
    hostagent_prompt: str = "ufo/prompts/share/base/host_agent.yaml"
    appagent_prompt: str = "ufo/prompts/share/base/app_agent.yaml"
    followeragent_prompt: str = "ufo/prompts/share/base/app_agent.yaml"
    evaluation_prompt: str = "ufo/prompts/evaluation/evaluate.yaml"
    hostagent_example_prompt: str = (
        "ufo/prompts/examples/{mode}/host_agent_example.yaml"
    )
    appagent_example_prompt: str = "ufo/prompts/examples/{mode}/app_agent_example.yaml"
    appagent_example_prompt_as: str = (
        "ufo/prompts/examples/{mode}/app_agent_example_as.yaml"
    )

    # ========== API and App-specific Prompts ==========
    app_api_prompt_address: Dict[str, str] = field(default_factory=dict)
    word_api_prompt: str = "ufo/prompts/apps/word/api.yaml"
    excel_api_prompt: str = "ufo/prompts/apps/excel/api.yaml"

    # ========== Constellation Prompts ==========
    constellation_creation_prompt: str = (
        "galaxy/prompts/constellation/share/constellation_creation.yaml"
    )
    constellation_editing_prompt: str = (
        "galaxy/prompts/constellation/share/constellation_editing.yaml"
    )
    constellation_creation_example_prompt: str = (
        "galaxy/prompts/constellation/examples/constellation_creation_example.yaml"
    )
    constellation_editing_example_prompt: str = (
        "galaxy/prompts/constellation/examples/constellation_editing_example.yaml"
    )

    # ========== Third-Party Agents ==========
    enabled_third_party_agents: List[str] = field(default_factory=list)
    third_party_agent_config: Dict[str, Any] = field(default_factory=dict)

    # ========== Output ==========
    output_presenter: str = "rich"

    # ========== Prices (from legacy config) ==========
    prices: Dict[str, Any] = field(default_factory=dict)

    # ========== Dynamic Fields ==========
    _extras: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        # Support uppercase access (MAX_TOKENS, MAX_STEP, etc.)
        # Map to lowercase attribute if exists
        lower_name = name.lower()
        if hasattr(self.__class__, lower_name):
            return getattr(self, lower_name)

        # Check extras (try both exact name and uppercase version)
        if name in self._extras:
            return self._extras[name]

        # If lowercase requested, try uppercase in extras
        upper_name = name.upper()
        if upper_name in self._extras:
            return self._extras[upper_name]

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key) and not key.startswith("_"):
            return getattr(self, key)
        if key in self._extras:
            return self._extras[key]
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemConfig":
        """Create SystemConfig with known fields + extras"""
        known_mappings = {
            # LLM Parameters
            "MAX_TOKENS": "max_tokens",
            "MAX_RETRY": "max_retry",
            "TEMPERATURE": "temperature",
            "TOP_P": "top_p",
            "TIMEOUT": "timeout",
            # Control Backend
            "CONTROL_BACKEND": "control_backend",
            "IOU_THRESHOLD_FOR_MERGE": "iou_threshold_for_merge",
            # Execution Limits
            "MAX_STEP": "max_step",
            "MAX_ROUND": "max_round",
            "SLEEP_TIME": "sleep_time",
            "RECTANGLE_TIME": "rectangle_time",
            # Action Configuration
            "ACTION_SEQUENCE": "action_sequence",
            "SHOW_VISUAL_OUTLINE_ON_SCREEN": "show_visual_outline_on_screen",
            "MAXIMIZE_WINDOW": "maximize_window",
            "JSON_PARSING_RETRY": "json_parsing_retry",
            # Safety
            "SAFE_GUARD": "safe_guard",
            "CONTROL_LIST": "control_list",
            # History
            "HISTORY_KEYS": "history_keys",
            # Annotation
            "ANNOTATION_COLORS": "annotation_colors",
            "HIGHLIGHT_BBOX": "highlight_bbox",
            "ANNOTATION_FONT_SIZE": "annotation_font_size",
            # Control Actions
            "CLICK_API": "click_api",
            "AFTER_CLICK_WAIT": "after_click_wait",
            "INPUT_TEXT_API": "input_text_api",
            "INPUT_TEXT_ENTER": "input_text_enter",
            "INPUT_TEXT_INTER_KEY_PAUSE": "input_text_inter_key_pause",
            # Logging
            "PRINT_LOG": "print_log",
            "CONCAT_SCREENSHOT": "concat_screenshot",
            "LOG_LEVEL": "log_level",
            "INCLUDE_LAST_SCREENSHOT": "include_last_screenshot",
            "REQUEST_TIMEOUT": "request_timeout",
            "LOG_XML": "log_xml",
            "LOG_TO_MARKDOWN": "log_to_markdown",
            "SCREENSHOT_TO_MEMORY": "screenshot_to_memory",
            # Image Performance
            "DEFAULT_PNG_COMPRESS_LEVEL": "default_png_compress_level",
            # Save Options
            "SAVE_UI_TREE": "save_ui_tree",
            "SAVE_FULL_SCREEN": "save_full_screen",
            # Task Management
            "TASK_STATUS": "task_status",
            "TASK_STATUS_FILE": "task_status_file",
            "SAVE_EXPERIENCE": "save_experience",
            # Evaluation
            "EVA_SESSION": "eva_session",
            "EVA_ROUND": "eva_round",
            "EVA_ALL_SCREENSHOTS": "eva_all_screenshots",
            # Customization
            "ASK_QUESTION": "ask_question",
            "USE_CUSTOMIZATION": "use_customization",
            "QA_PAIR_FILE": "qa_pair_file",
            "QA_PAIR_NUM": "qa_pair_num",
            # Omniparser
            "OMNIPARSER": "omniparser",
            # Control Filtering
            "CONTROL_FILTER_TYPE": "control_filter_type",
            "CONTROL_FILTER_TOP_K_PLAN": "control_filter_top_k_plan",
            "CONTROL_FILTER_TOP_K_SEMANTIC": "control_filter_top_k_semantic",
            "CONTROL_FILTER_TOP_K_ICON": "control_filter_top_k_icon",
            "CONTROL_FILTER_MODEL_SEMANTIC_NAME": "control_filter_model_semantic_name",
            "CONTROL_FILTER_MODEL_ICON_NAME": "control_filter_model_icon_name",
            # API Usage
            "USE_APIS": "use_apis",
            "API_PROMPT": "api_prompt",
            # MCP
            "USE_MCP": "use_mcp",
            "MCP_SERVERS_CONFIG": "mcp_servers_config",
            "MCP_PREFERRED_APPS": "mcp_preferred_apps",
            "MCP_FALLBACK_TO_UI": "mcp_fallback_to_ui",
            "MCP_INSTRUCTIONS_PATH": "mcp_instructions_path",
            "MCP_TOOL_TIMEOUT": "mcp_tool_timeout",
            "MCP_LOG_EXECUTION": "mcp_log_execution",
            # Device Configuration
            "DEVICE_INFO": "device_info",
            # Prompt Paths
            "HOSTAGENT_PROMPT": "hostagent_prompt",
            "APPAGENT_PROMPT": "appagent_prompt",
            "FOLLOWERAGENT_PROMPT": "followeragent_prompt",
            "EVALUATION_PROMPT": "evaluation_prompt",
            "HOSTAGENT_EXAMPLE_PROMPT": "hostagent_example_prompt",
            "APPAGENT_EXAMPLE_PROMPT": "appagent_example_prompt",
            "APPAGENT_EXAMPLE_PROMPT_AS": "appagent_example_prompt_as",
            # API and App-specific Prompts
            "APP_API_PROMPT_ADDRESS": "app_api_prompt_address",
            "WORD_API_PROMPT": "word_api_prompt",
            "EXCEL_API_PROMPT": "excel_api_prompt",
            # Constellation Prompts
            "CONSTELLATION_CREATION_PROMPT": "constellation_creation_prompt",
            "CONSTELLATION_EDITING_PROMPT": "constellation_editing_prompt",
            "CONSTELLATION_CREATION_EXAMPLE_PROMPT": "constellation_creation_example_prompt",
            "CONSTELLATION_EDITING_EXAMPLE_PROMPT": "constellation_editing_example_prompt",
            # Third-Party Agents
            "ENABLED_THIRD_PARTY_AGENTS": "enabled_third_party_agents",
            "THIRD_PARTY_AGENT_CONFIG": "third_party_agent_config",
            # Output
            "OUTPUT_PRESENTER": "output_presenter",
            # Prices
            "PRICES": "prices",
        }

        kwargs = {}
        extras = {}

        for key, value in data.items():
            if key in known_mappings:
                kwargs[known_mappings[key]] = value
            else:
                # All other fields go to extras
                extras[key] = value

        instance = cls(**kwargs)
        instance._extras = extras
        return instance


@dataclass
class UFOConfig:
    """
    Complete UFO configuration with typed modules + dynamic raw access.

    This hybrid approach provides:
    1. Typed access to common configurations: config.system.max_step
    2. Dynamic access to any YAML key: config["ANY_NEW_KEY"]
    3. Backward compatibility: config["OLD_KEY"] still works
    """

    # ========== Typed Module Configs (Recommended) ==========
    host_agent: AgentConfig
    app_agent: AgentConfig
    backup_agent: AgentConfig
    evaluation_agent: AgentConfig
    operator: AgentConfig
    rag: RAGConfig
    system: SystemConfig

    # ========== Raw Dictionary (Backward Compatible) ==========
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __getattr__(self, name: str) -> Any:
        """
        Support dynamic attribute access for any config key.

        Allows: config.ANY_NEW_YAML_KEY
        """
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        # Check if it's in raw config
        if name in self._raw:
            value = self._raw[name]
            # Wrap dict values in DynamicConfig for nested access
            if isinstance(value, dict):
                from config.config_loader import DynamicConfig

                return DynamicConfig(value, name=name)
            return value

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __getitem__(self, key: str) -> Any:
        """
        Support dict-style access for backward compatibility.

        Allows: config["ANY_KEY"]
        """
        return self._raw[key]

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator"""
        return key in self._raw

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-style get with default"""
        return self._raw.get(key, default)

    def keys(self):
        """Get all raw config keys"""
        return self._raw.keys()

    def items(self):
        """Get all raw config items"""
        return self._raw.items()

    def values(self):
        """Get all raw config values"""
        return self._raw.values()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert UFOConfig back to dictionary format.
        Returns the raw config dictionary for backward compatibility.
        """
        return self._raw.copy()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UFOConfig":
        """Create UFOConfig from merged configuration dictionary"""
        return cls(
            host_agent=AgentConfig.from_dict(data.get("HOST_AGENT", {})),
            app_agent=AgentConfig.from_dict(data.get("APP_AGENT", {})),
            backup_agent=AgentConfig.from_dict(data.get("BACKUP_AGENT", {})),
            evaluation_agent=AgentConfig.from_dict(data.get("EVALUATION_AGENT", {})),
            operator=AgentConfig.from_dict(data.get("OPERATOR", {})),
            rag=RAGConfig.from_dict(data),
            system=SystemConfig.from_dict(data),
            _raw=data,
        )


@dataclass
class ConstellationRuntimeConfig:
    """
    Constellation runtime configuration with fixed fields + dynamic extras.
    """

    # ========== Fixed Fields ==========
    constellation_id: str = "test_constellation"
    heartbeat_interval: float = 30.0
    reconnect_delay: float = 5.0
    max_concurrent_tasks: int = 6
    max_step: int = 15
    device_info: str = "config/galaxy/devices.yaml"
    log_to_markdown: bool = True

    # ========== Dynamic Fields ==========
    _extras: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        # Support uppercase access (DEVICE_INFO, MAX_STEP, etc.)
        # Map to lowercase attribute if exists
        lower_name = name.lower()
        if hasattr(self.__class__, lower_name):
            return getattr(self, lower_name)

        # Check extras (try both exact name and uppercase version)
        if name in self._extras:
            return self._extras[name]

        # If lowercase requested, try uppercase in extras
        upper_name = name.upper()
        if upper_name in self._extras:
            return self._extras[upper_name]

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key) and not key.startswith("_"):
            return getattr(self, key)
        if key in self._extras:
            return self._extras[key]
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConstellationRuntimeConfig":
        """Create ConstellationRuntimeConfig from dictionary"""
        known_mappings = {
            "CONSTELLATION_ID": "constellation_id",
            "HEARTBEAT_INTERVAL": "heartbeat_interval",
            "RECONNECT_DELAY": "reconnect_delay",
            "MAX_CONCURRENT_TASKS": "max_concurrent_tasks",
            "MAX_STEP": "max_step",
            "DEVICE_INFO": "device_info",
        }

        kwargs = {}
        extras = {}

        for key, value in data.items():
            if key in known_mappings:
                kwargs[known_mappings[key]] = value
            else:
                extras[key] = value

        instance = cls(**kwargs)
        instance._extras = extras
        return instance


@dataclass
class GalaxyAgentConfig:
    """
    Galaxy agent configuration wrapper providing typed access.
    """

    constellation_agent: AgentConfig

    def __getattr__(self, name: str) -> Any:
        # Provide direct access to CONSTELLATION_AGENT
        if name.upper() == "CONSTELLATION_AGENT":
            return self.constellation_agent
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __getitem__(self, key: str) -> Any:
        if key == "CONSTELLATION_AGENT":
            return self.constellation_agent
        raise KeyError(key)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GalaxyAgentConfig":
        """Create GalaxyAgentConfig from dictionary"""
        return cls(
            constellation_agent=AgentConfig.from_dict(
                data.get("CONSTELLATION_AGENT", {})
            )
        )


@dataclass
class GalaxyConfig:
    """
    Complete Galaxy configuration with typed modules + dynamic raw access.

    Provides structured access:
    - config.agent.CONSTELLATION_AGENT → typed agent config
    - config.constellation.MAX_STEP → typed constellation config
    - config["ANY_KEY"] → backward compatible dict access
    """

    # ========== Typed Module Configs ==========
    agent: GalaxyAgentConfig
    constellation: ConstellationRuntimeConfig

    # ========== Raw Dictionary (Backward Compatible) ==========
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __getattr__(self, name: str) -> Any:
        """Support dynamic attribute access"""
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        if name in self._raw:
            value = self._raw[name]
            if isinstance(value, dict):
                from config.config_loader import DynamicConfig

                return DynamicConfig(value, name=name)
            return value

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __getitem__(self, key: str) -> Any:
        """Support dict-style access"""
        return self._raw[key]

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator"""
        return key in self._raw

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-style get with default"""
        return self._raw.get(key, default)

    def keys(self):
        return self._raw.keys()

    def items(self):
        return self._raw.items()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GalaxyConfig":
        """Create GalaxyConfig from merged configuration dictionary"""
        return cls(
            agent=GalaxyAgentConfig.from_dict(data),
            constellation=ConstellationRuntimeConfig.from_dict(data),
            _raw=data,
        )
