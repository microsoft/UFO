# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Test script to verify that the new config system returns the same values as the old system.
This test compares config values accessed through the old Config class vs the new get_ufo_config().
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import after adding to path
from config.config_loader import get_ufo_config, get_galaxy_config
from ufo.config import Config


def test_system_config_fields():
    """Test that all commonly used system config fields match between old and new systems"""
    print("=" * 80)
    print("Testing System Config Fields")
    print("=" * 80)

    # Get configs
    old_configs = Config.get_instance().config_data
    ufo_config = get_ufo_config()

    # Test common system fields
    test_fields = {
        # LLM Parameters
        "MAX_TOKENS": "max_tokens",
        "MAX_RETRY": "max_retry",
        "TEMPERATURE": "temperature",
        "TOP_P": "top_p",
        "TIMEOUT": "timeout",
        # Control Backend
        "CONTROL_BACKEND": "control_backend",
        "IOU_THRESHOLD_FOR_MERGE": "iou_threshold_for_merge",
        "OMNIPARSER": "omniparser",
        # Execution Limits
        "MAX_STEP": "max_step",
        "MAX_ROUND": "max_round",
        "SLEEP_TIME": "sleep_time",
        # Action Configuration
        "ACTION_SEQUENCE": "action_sequence",
        "MAXIMIZE_WINDOW": "maximize_window",
        "JSON_PARSING_RETRY": "json_parsing_retry",
        # Safety
        "SAFE_GUARD": "safe_guard",
        "CONTROL_LIST": "control_list",
        # History
        "HISTORY_KEYS": "history_keys",
        # Logging
        "PRINT_LOG": "print_log",
        "LOG_LEVEL": "log_level",
        "LOG_TO_MARKDOWN": "log_to_markdown",
        # Save Options
        "SAVE_UI_TREE": "save_ui_tree",
        "SAVE_FULL_SCREEN": "save_full_screen",
        # Screenshot Options
        "INCLUDE_LAST_SCREENSHOT": "include_last_screenshot",
        "CONCAT_SCREENSHOT": "concat_screenshot",
        # Task Management
        "TASK_STATUS": "task_status",
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
        # API Usage
        "USE_APIS": "use_apis",
        "API_PROMPT": "api_prompt",
        # MCP
        "USE_MCP": "use_mcp",
        "MCP_SERVERS_CONFIG": "mcp_servers_config",
        # Device Configuration
        "DEVICE_INFO": "device_info",
        # Prompt Paths
        "HOSTAGENT_PROMPT": "hostagent_prompt",
        "APPAGENT_PROMPT": "appagent_prompt",
        "APPAGENT_EXAMPLE_PROMPT": "appagent_example_prompt",
        "APPAGENT_EXAMPLE_PROMPT_AS": "appagent_example_prompt_as",
        "EVALUATION_PROMPT": "evaluation_prompt",
        # Output
        "OUTPUT_PRESENTER": "output_presenter",
        # Third-Party Agents
        "ENABLED_THIRD_PARTY_AGENTS": "enabled_third_party_agents",
        "THIRD_PARTY_AGENT_CONFIG": "third_party_agent_config",
    }

    passed = 0
    failed = 0
    failures = []

    for old_key, new_attr in test_fields.items():
        try:
            old_value = old_configs.get(old_key)
            new_value = getattr(ufo_config.system, new_attr)

            if old_value == new_value:
                passed += 1
                print(f"✓ {old_key:40s} → {new_attr:40s} MATCH")
            else:
                failed += 1
                failures.append((old_key, new_attr, old_value, new_value))
                print(f"✗ {old_key:40s} → {new_attr:40s} MISMATCH")
                print(f"  Old: {old_value}")
                print(f"  New: {new_value}")
        except Exception as e:
            failed += 1
            failures.append((old_key, new_attr, "ERROR", str(e)))
            print(f"✗ {old_key:40s} → {new_attr:40s} ERROR: {e}")

    print("\n" + "=" * 80)
    print(f"System Config Test Results: {passed} passed, {failed} failed")
    print("=" * 80)

    return passed, failed, failures


def test_rag_config_fields():
    """Test that RAG config fields match"""
    print("\n" + "=" * 80)
    print("Testing RAG Config Fields")
    print("=" * 80)

    old_configs = Config.get_instance().config_data
    ufo_config = get_ufo_config()

    test_fields = {
        "RAG_OFFLINE_DOCS": "offline_docs",
        "RAG_OFFLINE_DOCS_RETRIEVED_TOPK": "offline_docs_retrieved_topk",
        "RAG_ONLINE_SEARCH": "online_search",
        "RAG_ONLINE_SEARCH_TOPK": "online_search_topk",
        "RAG_ONLINE_RETRIEVED_TOPK": "online_retrieved_topk",
        "RAG_EXPERIENCE": "experience",
        "RAG_EXPERIENCE_RETRIEVED_TOPK": "experience_retrieved_topk",
        "RAG_DEMONSTRATION": "demonstration",
        "RAG_DEMONSTRATION_RETRIEVED_TOPK": "demonstration_retrieved_topk",
        "EXPERIENCE_SAVED_PATH": "experience_saved_path",
        "DEMONSTRATION_SAVED_PATH": "demonstration_saved_path",
    }

    passed = 0
    failed = 0
    failures = []

    for old_key, new_attr in test_fields.items():
        try:
            old_value = old_configs.get(old_key)
            new_value = getattr(ufo_config.rag, new_attr)

            if old_value == new_value:
                passed += 1
                print(f"✓ {old_key:45s} → {new_attr:40s} MATCH")
            else:
                failed += 1
                failures.append((old_key, new_attr, old_value, new_value))
                print(f"✗ {old_key:45s} → {new_attr:40s} MISMATCH")
                print(f"  Old: {old_value}")
                print(f"  New: {new_value}")
        except Exception as e:
            failed += 1
            failures.append((old_key, new_attr, "ERROR", str(e)))
            print(f"✗ {old_key:45s} → {new_attr:40s} ERROR: {e}")

    print("\n" + "=" * 80)
    print(f"RAG Config Test Results: {passed} passed, {failed} failed")
    print("=" * 80)

    return passed, failed, failures


def test_agent_config_fields():
    """Test that agent config fields match"""
    print("\n" + "=" * 80)
    print("Testing Agent Config Fields")
    print("=" * 80)

    old_configs = Config.get_instance().config_data
    ufo_config = get_ufo_config()

    agents_to_test = [
        ("HOST_AGENT", ufo_config.host_agent, "host_agent"),
        ("APP_AGENT", ufo_config.app_agent, "app_agent"),
        ("BACKUP_AGENT", ufo_config.backup_agent, "backup_agent"),
        ("EVALUATION_AGENT", ufo_config.evaluation_agent, "evaluation_agent"),
    ]

    passed = 0
    failed = 0
    failures = []

    for old_key, new_config, config_name in agents_to_test:
        try:
            if old_key not in old_configs:
                print(f"⚠ {old_key} not in old config, skipping")
                continue

            old_agent = old_configs[old_key]

            # Test common agent fields
            agent_fields = {
                "API_TYPE": "api_type",
                "API_BASE": "api_base",
                "API_KEY": "api_key",
                "API_VERSION": "api_version",
                "API_MODEL": "api_model",
                "VISUAL_MODE": "visual_mode",
            }

            for old_field, new_attr in agent_fields.items():
                try:
                    old_value = old_agent.get(old_field)
                    new_value = getattr(new_config, new_attr)

                    if old_value == new_value:
                        passed += 1
                        print(
                            f"✓ {old_key}.{old_field:20s} → {config_name}.{new_attr:20s} MATCH"
                        )
                    else:
                        failed += 1
                        failures.append(
                            (
                                f"{old_key}.{old_field}",
                                f"{config_name}.{new_attr}",
                                old_value,
                                new_value,
                            )
                        )
                        print(
                            f"✗ {old_key}.{old_field:20s} → {config_name}.{new_attr:20s} MISMATCH"
                        )
                        print(f"  Old: {old_value}")
                        print(f"  New: {new_value}")
                except AttributeError:
                    # Field might not exist in new config if it's in _extras
                    try:
                        new_value = new_config._extras.get(old_field.upper())
                        if old_agent.get(old_field) == new_value:
                            passed += 1
                            print(
                                f"✓ {old_key}.{old_field:20s} → {config_name}._extras[{old_field}] MATCH"
                            )
                        else:
                            failed += 1
                            print(
                                f"✗ {old_key}.{old_field:20s} FIELD NOT FOUND IN NEW CONFIG"
                            )
                    except:
                        failed += 1
                        print(
                            f"✗ {old_key}.{old_field:20s} FIELD NOT FOUND IN NEW CONFIG"
                        )

        except Exception as e:
            failed += 1
            failures.append((old_key, config_name, "ERROR", str(e)))
            print(f"✗ {old_key:40s} → {config_name:40s} ERROR: {e}")

    print("\n" + "=" * 80)
    print(f"Agent Config Test Results: {passed} passed, {failed} failed")
    print("=" * 80)

    return passed, failed, failures


def main():
    """Run all config migration tests"""
    print("\n" + "=" * 80)
    print("CONFIG MIGRATION VALIDATION TEST")
    print("Testing: Old Config.get_instance().config_data vs New get_ufo_config()")
    print("=" * 80 + "\n")

    total_passed = 0
    total_failed = 0
    all_failures = []

    # Test system config
    passed, failed, failures = test_system_config_fields()
    total_passed += passed
    total_failed += failed
    all_failures.extend(failures)

    # Test RAG config
    passed, failed, failures = test_rag_config_fields()
    total_passed += passed
    total_failed += failed
    all_failures.extend(failures)

    # Test agent config
    passed, failed, failures = test_agent_config_fields()
    total_passed += passed
    total_failed += failed
    all_failures.extend(failures)

    # Print summary
    print("\n" + "=" * 80)
    print("FINAL TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_passed + total_failed}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success Rate: {total_passed / (total_passed + total_failed) * 100:.1f}%")
    print("=" * 80)

    if all_failures:
        print("\nFailed Tests:")
        for old_key, new_key, old_val, new_val in all_failures:
            print(f"  {old_key} → {new_key}")
            if old_val != "ERROR":
                print(f"    Old: {old_val}")
                print(f"    New: {new_val}")

    return total_failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
