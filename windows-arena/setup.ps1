$scriptFolder = "\\host.lan\Data"

# Load the shared setup-tools module
Import-Module (Join-Path $scriptFolder -ChildPath "setup-tools.psm1")

# Initialize the script folder to the directory of the current script
$requirementsFile = "$PSScriptRoot\..\requirements.txt"
$outputFile = "$PSScriptRoot\Logs.txt"

# Ensure pip is updated to the latest version
try {
    
    Write-Host requirementsFile
    # Install Python packages from requirements.txt using Python's pip module
    if (Test-Path $requirementsFile) {
        Write-Host "Installing required Python packages using pip from requirements file..."
        py -m pip install -r $requirementsFile

        # Write a text file indicating that the setup is finished
        "Setup finished" | Out-File $outputFile
    } else {
        throw "Requirements file not found: $requirementsFile"
    }
} catch {
    # Log the error message to the output file
    $_.Exception.Message | Out-File $outputFile
}