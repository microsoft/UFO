"""
Device Information Provider

Collects device system information for reporting to the server.
Supports Windows, Linux, macOS, and provides extensibility for mobile and IoT devices.
"""

import logging
import platform
import socket
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DeviceSystemInfo:
    """
    Device system information - lightweight and essential.

    This information is collected automatically from the device and sent
    to the server during registration. It helps constellation clients
    intelligently select appropriate devices for task execution.
    """

    # Basic identification
    device_id: str
    platform: str  # windows, linux, darwin, android, ios, web
    os_version: str

    # Hardware information (simplified)
    cpu_count: int
    memory_total_gb: float

    # Network information
    hostname: str
    ip_address: str

    # Capability information
    supported_features: List[str] = field(default_factory=list)

    # Platform type categorization
    platform_type: str = "computer"  # computer, mobile, web, iot

    # Schema version for future compatibility
    schema_version: str = "1.0"

    # Custom metadata (optional, can be loaded from config)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


class DeviceInfoProvider:
    """
    Collects device system information.

    This class provides methods to gather essential device information
    that helps in device selection and task routing.
    """

    @staticmethod
    def collect_system_info(
        client_id: str, custom_metadata: Optional[Dict[str, Any]] = None
    ) -> DeviceSystemInfo:
        """
        Collect system information from the device.

        :param client_id: The device client ID
        :param custom_metadata: Optional custom metadata from configuration
        :return: DeviceSystemInfo object with collected information
        """
        try:
            return DeviceSystemInfo(
                device_id=client_id,
                platform=DeviceInfoProvider._get_platform(),
                os_version=DeviceInfoProvider._get_os_version(),
                cpu_count=DeviceInfoProvider._get_cpu_count(),
                memory_total_gb=DeviceInfoProvider._get_memory_total_gb(),
                hostname=DeviceInfoProvider._get_hostname(),
                ip_address=DeviceInfoProvider._get_ip_address(),
                supported_features=DeviceInfoProvider._detect_features(),
                platform_type=DeviceInfoProvider._get_platform_type(),
                custom_metadata=custom_metadata or {},
            )
        except Exception as e:
            logger.error(f"Error collecting system info: {e}", exc_info=True)
            # Return minimal info on error
            return DeviceSystemInfo(
                device_id=client_id,
                platform="unknown",
                os_version="unknown",
                cpu_count=0,
                memory_total_gb=0.0,
                hostname="unknown",
                ip_address="unknown",
                supported_features=[],
                platform_type="unknown",
                custom_metadata=custom_metadata or {},
            )

    @staticmethod
    def _get_platform() -> str:
        """Get platform name (windows, linux, darwin, etc.)"""
        try:
            return platform.system().lower()
        except Exception:
            return "unknown"

    @staticmethod
    def _get_os_version() -> str:
        """Get OS version string"""
        try:
            return platform.version()
        except Exception:
            return "unknown"

    @staticmethod
    def _get_cpu_count() -> int:
        """Get number of CPU cores"""
        try:
            import os

            cpu_count = os.cpu_count()
            return cpu_count if cpu_count is not None else 0
        except Exception:
            return 0

    @staticmethod
    def _get_memory_total_gb() -> float:
        """Get total memory in GB"""
        try:
            import psutil

            total_memory = psutil.virtual_memory().total
            return round(total_memory / (1024**3), 2)
        except ImportError:
            logger.warning("psutil not installed, memory info unavailable")
            return 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _get_hostname() -> str:
        """Get device hostname"""
        try:
            return socket.gethostname()
        except Exception:
            return "unknown"

    @staticmethod
    def _get_ip_address() -> str:
        """Get device IP address"""
        try:
            # Get local IP by connecting to external address (doesn't actually send data)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            try:
                # Fallback to hostname resolution
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "unknown"

    @staticmethod
    def _detect_features() -> List[str]:
        """
        Auto-detect device capabilities based on platform.

        Returns a list of supported features that can be used
        for intelligent device selection.
        """
        features = []
        sys_platform = platform.system().lower()

        if sys_platform in ["windows", "linux", "darwin"]:
            # Desktop/laptop computers
            features.extend(
                [
                    "gui",  # Graphical user interface
                    "cli",  # Command line interface
                    "browser",  # Web browser support
                    "file_system",  # File system operations
                    "office",  # Office applications
                ]
            )

            # Windows-specific features
            if sys_platform == "windows":
                features.append("windows_apps")

            # Linux-specific features
            elif sys_platform == "linux":
                features.append("linux_apps")

            # macOS-specific features
            elif sys_platform == "darwin":
                features.append("macos_apps")

        elif sys_platform in ["android", "ios"]:
            # Mobile devices (placeholder for future support)
            features.extend(
                [
                    "mobile_touch",  # Touch interface
                    "mobile_apps",  # Mobile applications
                    "camera",  # Camera support
                    "gps",  # GPS/location services
                ]
            )

        return features

    @staticmethod
    def _get_platform_type() -> str:
        """
        Categorize platform type.

        Returns one of: computer, mobile, web, iot
        """
        sys_platform = platform.system().lower()

        if sys_platform in ["windows", "linux", "darwin"]:
            return "computer"
        elif sys_platform in ["android", "ios"]:
            return "mobile"
        else:
            return "unknown"
