# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Regression tests for environment-specific MCP configuration files."""

import pytest
import yaml

from config.config_loader import ConfigLoader


@pytest.mark.parametrize("stem", ["mcp", "agent_mcp"])
@pytest.mark.parametrize("env", ["dev", "test", "prod"])
def test_mcp_environment_override_preserves_namespace(tmp_path, stem, env):
    base = {
        "HostAgent": {
            "default": {
                "action": [{"namespace": "Executor", "type": "http", "port": 8000}],
                "data_collection": [{"namespace": "Collector", "type": "local"}],
            }
        },
        "AppAgent": {"default": {"action": [{"namespace": "AppExecutor"}]}},
    }
    override = {
        "HostAgent": {
            "default": {
                "action": [{"namespace": "Executor", "type": "http", "port": 9000}]
            }
        }
    }
    (tmp_path / f"{stem}.yaml").write_text(yaml.safe_dump(base), encoding="utf-8")
    (tmp_path / f"{stem}_{env}.yaml").write_text(
        yaml.safe_dump(override), encoding="utf-8"
    )
    (tmp_path / "system.yaml").write_text("MAX_STEP: 10\n", encoding="utf-8")
    (tmp_path / f"system_{env}.yaml").write_text(
        "MAX_STEP: 20\n", encoding="utf-8"
    )

    result = ConfigLoader()._load_module_configs(tmp_path, env)

    host = result["mcp"]["HostAgent"]["default"]
    assert host["action"] == override["HostAgent"]["default"]["action"]
    assert host["data_collection"] == base["HostAgent"]["default"]["data_collection"]
    assert result["mcp"]["AppAgent"] == base["AppAgent"]
    assert "HostAgent" not in result
    assert result["MAX_STEP"] == 20


@pytest.mark.parametrize("stem", ["mcp", "agent_mcp"])
def test_mcp_override_is_not_loaded_in_production(tmp_path, stem):
    (tmp_path / f"{stem}.yaml").write_text("timeout: 30\n", encoding="utf-8")
    (tmp_path / f"{stem}_dev.yaml").write_text("timeout: 5\n", encoding="utf-8")

    result = ConfigLoader()._load_module_configs(tmp_path, "production")

    assert result == {"mcp": {"timeout": 30}}
