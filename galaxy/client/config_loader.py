# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation Configuration Loader

Loads device registration configuration from various sources including
config files, command line arguments, and environment variables.
"""

import json
import logging
import os
import argparse
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class DeviceConfig:
    """Configuration for a single device"""

    device_id: str
    server_url: str
    os: str = "unknown"
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    auto_connect: bool = True
    max_retries: int = 5


@dataclass
class ConstellationConfig:
    """Configuration for the constellation system"""

    task_name: str = "test_task"
    heartbeat_interval: float = 30.0
    reconnect_delay: float = 5.0
    max_concurrent_tasks: int = 10
    devices: List[DeviceConfig] = field(default_factory=list)

    @classmethod
    def from_file(cls, config_path: str) -> "ConstellationConfig":
        """
        Load configuration from a JSON or YAML file.

        :param config_path: Path to the configuration file
        :return: ConstellationConfig instance
        """
        file_path = Path(config_path)
        if file_path.suffix.lower() in [".yaml", ".yml"]:
            return cls.from_yaml(config_path)
        else:
            return cls.from_json(config_path)

    @classmethod
    def from_json(cls, config_path: str) -> "ConstellationConfig":
        """
        Load configuration from a JSON file.

        :param config_path: Path to the configuration file
        :return: ConstellationConfig instance
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Parse devices
            devices = []
            for device_data in config_data.get("devices", []):
                device_config = DeviceConfig(
                    device_id=device_data["device_id"],
                    server_url=device_data["server_url"],
                    os=device_data.get("os", "unknown"),
                    capabilities=device_data.get("capabilities", []),
                    metadata=device_data.get("metadata", {}),
                    auto_connect=device_data.get("auto_connect", True),
                    max_retries=device_data.get("max_retries", 5),
                )
                devices.append(device_config)

            return cls(
                task_name=config_data.get("task_name", "test_task"),
                heartbeat_interval=config_data.get("heartbeat_interval", 30.0),
                reconnect_delay=config_data.get("reconnect_delay", 5.0),
                max_concurrent_tasks=config_data.get("max_concurrent_tasks", 10),
                devices=devices,
            )

        except Exception as e:
            logging.getLogger(__name__).error(
                f"Failed to load config from {config_path}: {e}"
            )
            return cls()

    @classmethod
    def from_yaml(cls, config_path: str) -> "ConstellationConfig":
        """
        Load configuration from a YAML file.

        :param config_path: Path to the configuration file
        :return: ConstellationConfig instance
        """
        if yaml is None:
            raise ImportError(
                "PyYAML is required for YAML configuration files. Install with: pip install PyYAML"
            )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # Parse devices
            devices = []
            for device_data in config_data.get("devices", []):
                device_config = DeviceConfig(
                    device_id=device_data["device_id"],
                    server_url=device_data["server_url"],
                    os=device_data.get("os", "unknown"),
                    capabilities=device_data.get("capabilities", []),
                    metadata=device_data.get("metadata", {}),
                    auto_connect=device_data.get("auto_connect", True),
                    max_retries=device_data.get("max_retries", 5),
                )
                devices.append(device_config)

            return cls(
                task_name=config_data.get("task_name", "test_task"),
                heartbeat_interval=config_data.get("heartbeat_interval", 30.0),
                reconnect_delay=config_data.get("reconnect_delay", 5.0),
                max_concurrent_tasks=config_data.get("max_concurrent_tasks", 10),
                devices=devices,
            )

        except FileNotFoundError as e:
            logging.getLogger(__name__).error(
                f"YAML config file not found: {config_path} - {e}", exc_info=True
            )
            return cls()
        except yaml.YAMLError as e:
            logging.getLogger(__name__).error(
                f"Invalid YAML syntax in config file {config_path}: {e}", exc_info=True
            )
            return cls()
        except KeyError as e:
            logging.getLogger(__name__).error(
                f"Missing required field in YAML config {config_path}: {e}",
                exc_info=True,
            )
            return cls()
        except ValueError as e:
            logging.getLogger(__name__).error(
                f"Invalid value in YAML config {config_path}: {e}", exc_info=True
            )
            return cls()
        except Exception as e:
            logging.getLogger(__name__).error(
                f"Unexpected error loading YAML config from {config_path}: {e}",
                exc_info=True,
            )
            return cls()

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ConstellationConfig":
        """
        Create configuration from command line arguments.

        :param args: Parsed command line arguments
        :return: ConstellationConfig instance
        """
        config = cls()

        if hasattr(args, "task_name") and args.task_name:
            config.task_name = args.task_name

        if hasattr(args, "heartbeat_interval") and args.heartbeat_interval:
            config.heartbeat_interval = args.heartbeat_interval

        if hasattr(args, "max_concurrent_tasks") and args.max_concurrent_tasks:
            config.max_concurrent_tasks = args.max_concurrent_tasks

        # Parse device arguments
        if hasattr(args, "devices") and args.devices:
            for device_str in args.devices:
                try:
                    # Expected format: device_id:server_url
                    parts = device_str.split(":")
                    if len(parts) >= 2:
                        device_id = parts[0]
                        server_url = parts[1]

                        device_config = DeviceConfig(
                            device_id=device_id,
                            server_url=server_url,
                        )
                        config.devices.append(device_config)

                except IndexError as e:
                    logging.getLogger(__name__).error(
                        f"Invalid device config format: {device_str} - expected 'device_id:server_url' - {e}",
                        exc_info=True,
                    )
                except ValueError as e:
                    logging.getLogger(__name__).error(
                        f"Invalid device config value: {device_str} - {e}",
                        exc_info=True,
                    )
                except Exception as e:
                    logging.getLogger(__name__).error(
                        f"Unexpected error parsing device config: {device_str} - {e}",
                        exc_info=True,
                    )

        return config

    @classmethod
    def from_env(cls) -> "ConstellationConfig":
        """
        Create configuration from environment variables.

        :return: ConstellationConfig instance
        """
        config = cls()

        # Load basic configuration
        config.task_name = os.getenv("TASK_NAME", config.task_name)
        config.heartbeat_interval = float(
            os.getenv("CONSTELLATION_HEARTBEAT_INTERVAL", config.heartbeat_interval)
        )
        config.max_concurrent_tasks = int(
            os.getenv("CONSTELLATION_MAX_CONCURRENT_TASKS", config.max_concurrent_tasks)
        )

        # Load devices from environment
        devices_json = os.getenv("CONSTELLATION_DEVICES")
        if devices_json:
            try:
                devices_data = json.loads(devices_json)
                for device_data in devices_data:
                    device_config = DeviceConfig(
                        device_id=device_data["device_id"],
                        server_url=device_data["server_url"],
                        capabilities=device_data.get("capabilities", []),
                        metadata=device_data.get("metadata", {}),
                        auto_connect=device_data.get("auto_connect", True),
                    )
                    config.devices.append(device_config)

            except Exception as e:
                logging.getLogger(__name__).error(
                    f"Failed to parse devices from environment: {e}"
                )

        return config

    def to_file(self, config_path: str) -> None:
        """
        Save configuration to a JSON or YAML file based on file extension.

        :param config_path: Path to save the configuration
        """
        file_path = Path(config_path)
        if file_path.suffix.lower() in [".yaml", ".yml"]:
            self.to_yaml(config_path)
        else:
            self.to_json(config_path)

    def to_json(self, config_path: str) -> None:
        """
        Save configuration to a JSON file.

        :param config_path: Path to save the configuration
        """
        try:
            config_data = {
                "task_name": self.task_name,
                "heartbeat_interval": self.heartbeat_interval,
                "reconnect_delay": self.reconnect_delay,
                "max_concurrent_tasks": self.max_concurrent_tasks,
                "devices": [
                    {
                        "device_id": device.device_id,
                        "server_url": device.server_url,
                        "capabilities": device.capabilities,
                        "metadata": device.metadata,
                        "auto_connect": device.auto_connect,
                        "max_retries": device.max_retries,
                    }
                    for device in self.devices
                ],
            }

            # Ensure directory exists
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logging.getLogger(__name__).info(f"Configuration saved to {config_path}")

        except Exception as e:
            logging.getLogger(__name__).error(
                f"Failed to save config to {config_path}: {e}"
            )

    def to_yaml(self, config_path: str) -> None:
        """
        Save configuration to a YAML file.

        :param config_path: Path to save the configuration
        """
        if yaml is None:
            raise ImportError(
                "PyYAML is required for YAML configuration files. Install with: pip install PyYAML"
            )

        try:
            config_data = {
                "task_name": self.task_name,
                "heartbeat_interval": self.heartbeat_interval,
                "reconnect_delay": self.reconnect_delay,
                "max_concurrent_tasks": self.max_concurrent_tasks,
                "devices": [
                    {
                        "device_id": device.device_id,
                        "server_url": device.server_url,
                        "capabilities": device.capabilities,
                        "metadata": device.metadata,
                        "auto_connect": device.auto_connect,
                        "max_retries": device.max_retries,
                    }
                    for device in self.devices
                ],
            }

            # Ensure directory exists
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    config_data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )

            logging.getLogger(__name__).info(f"Configuration saved to {config_path}")

        except Exception as e:
            logging.getLogger(__name__).error(
                f"Failed to save config to {config_path}: {e}"
            )

    def add_device(
        self,
        device_id: str,
        server_url: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_connect: bool = True,
    ) -> None:
        """
        Add a device to the configuration.

        :param device_id: Device identifier
        :param server_url: UFO server WebSocket URL
        :param capabilities: Device capabilities
        :param metadata: Additional metadata
        :param auto_connect: Whether to automatically connect
        """
        device_config = DeviceConfig(
            device_id=device_id,
            server_url=server_url,
            capabilities=capabilities.copy() if capabilities else [],
            metadata=metadata.copy() if metadata else {},
            auto_connect=auto_connect,
        )
        self.devices.append(device_config)

    def remove_device(self, device_id: str) -> bool:
        """
        Remove a device from the configuration.

        :param device_id: Device identifier
        :return: True if device was found and removed
        """
        for i, device in enumerate(self.devices):
            if device.device_id == device_id:
                del self.devices[i]
                return True
        return False

    def get_device_config(self, device_id: str) -> Optional[DeviceConfig]:
        """
        Get device configuration by ID.

        :param device_id: Device identifier
        :return: DeviceConfig if found, None otherwise
        """
        for device in self.devices:
            if device.device_id == device_id:
                return device
        return None

    @classmethod
    def create_sample_config(cls, file_path: str) -> None:
        """
        Create a sample configuration file.

        :param file_path: Path where to create the sample config
        """
        create_sample_config(file_path)


def create_sample_config(config_path: str) -> None:
    """
    Create a sample configuration file.

    :param config_path: Path to create the sample config
    """
    sample_config = ConstellationConfig(
        task_name="test_task",
        heartbeat_interval=30.0,
        reconnect_delay=5.0,
        max_concurrent_tasks=8,
        devices=[
            DeviceConfig(
                device_id="laptop_001",
                server_url="ws://192.168.1.100:5000/ws",
                capabilities=["web_browsing", "office_applications", "file_management"],
                metadata={
                    "location": "office",
                    "os": "windows",
                    "performance": "medium",
                },
                auto_connect=True,
                max_retries=5,
            ),
            DeviceConfig(
                device_id="workstation_002",
                server_url="ws://192.168.1.101:5000/ws",
                capabilities=["software_development", "data_analysis", "heavy_compute"],
                metadata={"location": "lab", "os": "windows", "performance": "high"},
                auto_connect=True,
                max_retries=3,
            ),
            DeviceConfig(
                device_id="server_003",
                server_url="ws://192.168.1.102:5000/ws",
                capabilities=["database_management", "api_services", "backup"],
                metadata={
                    "location": "datacenter",
                    "os": "linux",
                    "performance": "high",
                },
                auto_connect=True,
                max_retries=10,
            ),
        ],
    )

    sample_config.to_file(config_path)


def setup_argument_parser() -> argparse.ArgumentParser:
    """
    Set up command line argument parser for constellation configuration.

    :return: Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Constellation Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load from config file (JSON or YAML)
  python -m ufo.constellation.client --config config/constellation.json
  python -m ufo.constellation.client --config config/constellation.yaml
  
  # Add devices via command line
  python -m ufo.constellation.client \\
    --device laptop_001:ws://192.168.1.100:5000/ws \\
    --device workstation_002:ws://192.168.1.101:5000/ws
  
  # Create sample config
  python -m ufo.constellation.client --create-sample-config config/sample.json
  python -m ufo.constellation.client --create-sample-config config/sample.yaml
        """,
    )

    parser.add_argument(
        "--config", "-c", type=str, help="Path to constellation configuration file"
    )

    parser.add_argument(
        "--constellation-id",
        type=str,
        default="constellation_orchestrator",
        help="Unique identifier for this constellation instance",
    )

    parser.add_argument(
        "--heartbeat-interval",
        type=float,
        default=30.0,
        help="Heartbeat interval in seconds (default: 30.0)",
    )

    parser.add_argument(
        "--max-concurrent-tasks",
        type=int,
        default=10,
        help="Maximum concurrent tasks (default: 10)",
    )

    parser.add_argument(
        "--device",
        "-d",
        action="append",
        dest="devices",
        help="Add device in format: device_id:server_url",
    )

    parser.add_argument(
        "--create-sample-config",
        type=str,
        help="Create a sample configuration file at the specified path",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    return parser


if __name__ == "__main__":
    # Example usage
    parser = setup_argument_parser()
    args = parser.parse_args()

    if args.create_sample_config:
        create_sample_config(args.create_sample_config)
        print(f"Sample configuration created at {args.create_sample_config}")
    else:
        if args.config:
            config = ConstellationConfig.from_file(args.config)
        else:
            config = ConstellationConfig.from_args(args)

        print(f"Loaded configuration with {len(config.devices)} devices")
        for device in config.devices:
            print(f"  - {device.device_id}: {device.server_url}")
