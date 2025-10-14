# Linux Log Collection and Excel Generation Test

## Overview
This test module (`test_linux_log_collection_excel_generation.py`) demonstrates a cross-platform automation scenario where logs are collected from multiple Linux servers and consolidated into an Excel report on a Windows workstation.

## Test Scenario
**English**: Collect logs from two Linux servers and generate an Excel report on Windows  
**中文**: 从两个Linux服务器采集日志并在Windows上生成Excel报告

## Mock Devices Created

### 1. Linux Server 1 (`linux_server_001`)
- **Hostname**: web-server-01
- **OS**: Ubuntu 22.04 LTS
- **Services**: nginx, postgresql, redis
- **Capabilities**: log_collection, file_operations, system_monitoring, bash_scripting, ssh_access
- **Log Paths**: 
  - `/var/log/nginx/access.log`
  - `/var/log/nginx/error.log`
  - `/var/log/postgresql/postgresql.log`
  - `/var/log/syslog`

### 2. Linux Server 2 (`linux_server_002`)
- **Hostname**: api-server-01
- **OS**: CentOS 8
- **Services**: apache, mysql, mongodb
- **Capabilities**: log_collection, file_operations, system_monitoring, bash_scripting, database_operations
- **Log Paths**:
  - `/var/log/httpd/access_log`
  - `/var/log/httpd/error_log`
  - `/var/log/mysql/mysql.log`
  - `/var/log/mongodb/mongod.log`
  - `/var/log/messages`

### 3. Windows Workstation (`windows_workstation_001`)
- **Hostname**: analyst-pc-01
- **OS**: Windows 11 Pro
- **Software**: Microsoft Office 365, Python 3.11, Excel, Power BI
- **Capabilities**: office_applications, excel_processing, file_management, data_analysis, report_generation
- **Python Packages**: pandas, openpyxl, xlsxwriter

## Test Coverage

### Core Tests
- ✅ **Mock Device Creation**: Validates proper creation of all three AgentProfile objects
- ✅ **Capability Verification**: Ensures devices have required capabilities for the scenario
- ✅ **Log Collection Simulation**: Mocks log collection process from Linux servers
- ✅ **Excel Generation**: Simulates Excel report creation on Windows
- ✅ **Complete Workflow**: Tests end-to-end process from log collection to Excel output

### Advanced Tests
- ✅ **Metadata Validation**: Verifies all devices have proper metadata
- ✅ **Error Handling**: Tests scenarios with partial failures
- ✅ **Device Formatting**: Tests device information formatting for LLM prompts
- ✅ **Request Translation**: Documents Chinese-to-English scenario translation

## Running the Tests

```bash
# Run all tests in the file
python -m pytest tests/test_linux_log_collection_excel_generation.py -v

# Run specific test
python -m pytest tests/test_linux_log_collection_excel_generation.py::TestLinuxLogCollectionExcelGeneration::test_mock_device_creation -v

# Run with detailed output
python -m pytest tests/test_linux_log_collection_excel_generation.py -v -s
```

## Test Results
- **9 tests total**
- **All tests passing** ✅
- **Execution time**: ~11 seconds
- **Coverage**: Mock creation, capability validation, workflow simulation, error handling

## Use Cases
This test serves as a template for:
1. **Cross-platform automation scenarios**
2. **Log collection and analysis workflows**
3. **AgentProfile mock creation for testing**
4. **Constellation device management testing**
5. **Multi-device task coordination validation**

## File Location
```
tests/
├── test_linux_log_collection_excel_generation.py  # Main test file
└── README_log_collection_test.md                   # This documentation
```
