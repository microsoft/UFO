# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Configuration merging must not change cached source documents."""

import yaml

from config.config_loader import ConfigLoader


def test_environment_load_does_not_modify_base_or_previous_result(tmp_path):
    base = {"SERVICE": {"url": "https://production.example", "options": ["base"]}}
    dev = {"SERVICE": {"url": "https://development.example", "options": ["dev"]}}
    base_path = tmp_path / "system.yaml"
    base_path.write_text(yaml.safe_dump(base), encoding="utf-8")
    (tmp_path / "system_dev.yaml").write_text(yaml.safe_dump(dev), encoding="utf-8")
    loader = ConfigLoader()

    production = loader._load_module_configs(tmp_path, "production")
    development = loader._load_module_configs(tmp_path, "dev")

    assert production == base
    assert development == dev
    assert loader._load_yaml(base_path) == base
    assert loader._load_module_configs(tmp_path, "production") == base


def test_mutating_merged_lists_does_not_modify_cached_yaml(tmp_path):
    base = {"SERVICE": {"options": ["base"]}, "DEVICES": ["desktop"]}
    path = tmp_path / "system.yaml"
    path.write_text(yaml.safe_dump(base), encoding="utf-8")
    loader = ConfigLoader()

    result = loader._load_module_configs(tmp_path)
    result["SERVICE"]["options"].append("changed")
    result["DEVICES"].append("mobile")

    assert loader._load_yaml(path) == base
    assert loader._load_module_configs(tmp_path) == base


def test_later_files_do_not_modify_cached_earlier_files(tmp_path):
    base = {"SERVICE": {"url": "https://base.example", "timeout": 30}}
    path = tmp_path / "a.yaml"
    path.write_text(yaml.safe_dump(base), encoding="utf-8")
    (tmp_path / "b.yaml").write_text(
        "SERVICE:\n  url: https://override.example\n", encoding="utf-8"
    )
    loader = ConfigLoader()

    result = loader._load_module_configs(tmp_path)

    assert result["SERVICE"] == {"url": "https://override.example", "timeout": 30}
    assert loader._load_yaml(path) == base
