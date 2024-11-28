$scriptFolder = "\\host.lan\Data"

# Load the shared setup-tools module
Import-Module (Join-Path $scriptFolder -ChildPath "setup-tools.psm1")

# Initialize the script folder to the directory of the current script
$requirementsFile = "$PSScriptRoot\requirements.txt"

# Ensure pip is updated to the latest version
Install-PythonPackages -Package "pip" -Arguments "--upgrade"

Install-PythonPackages -Package "wheel"
Install-PythonPackages -Package "pywinauto"

# Install Python packages from requirements.txt using Python's pip module
if (Test-Path $requirementsFile) {
    Write-Host "Installing required Python packages using pip from requirements file..."
    Install-PythonPackages -RequirementsPath $requirementsFile
} else {
    Write-Error "Requirements file not found: $requirementsFile"
    exit
}