"""
Quick verification script for Mobile MCP Server setup
Checks prerequisites without starting full tests.

Usage:
    python tests/integration/verify_mobile_setup.py
"""

import os
import subprocess
import sys


def find_adb():
    """Auto-detect ADB path"""
    # Try common ADB locations
    common_paths = [
        r"C:\Users\{}\AppData\Local\Android\Sdk\platform-tools\adb.exe".format(
            os.environ.get("USERNAME", "")
        ),
        "/usr/bin/adb",
        "/usr/local/bin/adb",
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    # Try to find in PATH
    try:
        result = subprocess.run(
            ["where" if os.name == "nt" else "which", "adb"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except:
        pass

    return None


def check_adb():
    """Check if ADB is available and working"""
    print("\n1️⃣ Checking ADB installation...")

    adb_path = find_adb()

    if not adb_path:
        print("   ❌ ADB not found")
        print("   Please install Android SDK platform-tools")
        return False, None

    print(f"   ✅ ADB found: {adb_path}")

    try:
        result = subprocess.run(
            [adb_path, "version"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            version = result.stdout.split("\n")[0]
            print(f"   ✅ ADB version: {version}")
            return True, adb_path
        else:
            print(f"   ❌ ADB error: {result.stderr}")
            return False, adb_path

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, adb_path


def check_device(adb_path):
    """Check if Android device is connected"""
    print("\n2️⃣ Checking device connection...")

    if not adb_path:
        print("   ❌ ADB not available")
        return False

    try:
        result = subprocess.run(
            [adb_path, "devices"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            print(f"   ❌ ADB devices command failed")
            return False

        lines = result.stdout.strip().split("\n")
        devices = [line for line in lines if "\tdevice" in line]

        if not devices:
            print("   ❌ No devices connected")
            print("   Please start an Android emulator or connect a device")
            print("\n   Commands to start emulator:")
            print("     emulator -list-avds              # List available emulators")
            print("     emulator -avd <name>             # Start specific emulator")
            return False

        print(f"   ✅ Found {len(devices)} connected device(s):")
        for device_line in devices:
            device_id = device_line.split("\t")[0]
            print(f"      - {device_id}")

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_device_info(adb_path):
    """Get basic device information"""
    print("\n3️⃣ Getting device information...")

    if not adb_path:
        print("   ❌ ADB not available")
        return False

    try:
        # Get device model
        result = subprocess.run(
            [adb_path, "shell", "getprop", "ro.product.model"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        model = result.stdout.strip() if result.returncode == 0 else "Unknown"

        # Get Android version
        result = subprocess.run(
            [adb_path, "shell", "getprop", "ro.build.version.release"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        android_version = result.stdout.strip() if result.returncode == 0 else "Unknown"

        # Get screen size
        result = subprocess.run(
            [adb_path, "shell", "wm", "size"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        screen_size = result.stdout.strip() if result.returncode == 0 else "Unknown"

        print(f"   ✅ Device Information:")
        print(f"      Model: {model}")
        print(f"      Android Version: {android_version}")
        print(f"      Screen Size: {screen_size}")

        return True

    except Exception as e:
        print(f"   ⚠️  Could not get device info: {e}")
        return True  # Non-critical


def check_python_packages():
    """Check if required Python packages are installed"""
    print("\n4️⃣ Checking Python packages...")

    required = ["fastmcp", "pydantic"]
    missing = []

    for package in required:
        try:
            __import__(package)
            print(f"   ✅ {package} installed")
        except ImportError:
            print(f"   ❌ {package} NOT installed")
            missing.append(package)

    if missing:
        print(f"\n   Please install missing packages:")
        print(f"   pip install {' '.join(missing)}")
        return False

    return True


def print_next_steps(all_ok):
    """Print next steps based on verification results"""
    print("\n" + "=" * 70)

    if all_ok:
        print("✅ ALL CHECKS PASSED - Ready to test Mobile MCP Servers!")
        print("=" * 70)
        print("\nNext steps:")
        print("\n1. Start Mobile MCP Servers:")
        print(
            "   python -m ufo.client.mcp.http_servers.mobile_mcp_server --server both"
        )
        print("\n2. Run standalone test:")
        print("   python tests/integration/test_mobile_mcp_standalone.py")
        print("\n3. Or run full integration test:")
        print("   pytest tests/integration/test_mobile_mcp_server.py -v")
    else:
        print("❌ SOME CHECKS FAILED - Please fix the issues above")
        print("=" * 70)
        print("\nCommon fixes:")
        print("- Install Android SDK platform-tools")
        print("- Start Android emulator: emulator -avd <name>")
        print("- Enable USB debugging on physical device")
        print("- Install missing Python packages")


def main():
    """Main verification function"""
    print("=" * 70)
    print("Mobile MCP Server Setup Verification")
    print("=" * 70)

    results = []

    # Run checks
    adb_ok, adb_path = check_adb()
    results.append(adb_ok)

    if adb_ok:
        results.append(check_device(adb_path))
        results.append(check_device_info(adb_path))
    else:
        results.append(False)
        results.append(False)

    results.append(check_python_packages())

    # Summary
    all_ok = all(results)
    print_next_steps(all_ok)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
