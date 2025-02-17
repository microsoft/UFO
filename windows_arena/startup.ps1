param (
    [string]$instruction = "",
    [string]$agent_settings = ""
)

$RepoPath = "$PSScriptRoot\.."
$outputFile = "$PSScriptRoot\Ufo-runningLogs.txt"

# Store the current directory
$originalLocation = Get-Location

# Change to the target directory
Set-Location -Path $RepoPath

# Delete the log file if it exists
if (Test-Path $outputFile) {
    Remove-Item $outputFile
}

try {
    # Escape double quotes in JSON string for safe usage in PowerShell

    $instructionEscaped = $instruction -replace '\\', '\\' -replace '"', '\"'
    $jsonEscaped = $agent_settings -replace '"', '\"'

    $env:PYTHONIOENCODING = "utf-8"

    # Build the command to execute
#     $command = "py -m windows_arena --request `"$instruction`" --agent_settings `'$jsonEscaped`'"
#
#     # Execute the command and redirect output and error streams to the log file
#     Invoke-Expression $command 2>&1 | Tee-Object -FilePath $outputFile -Append
    Remove-Item -Path "$env:LOCALAPPDATA\Temp\gen_py" -Recurse -Force
    py -m windows_arena --request $instructionEscaped --agent_settings $jsonEscaped 2>&1 | Tee-Object -FilePath $outputFile -Append
} catch {
    # Log the error message to the output file
    $_.Exception.Message | Out-File -FilePath $outputFile -Append
}

# Restore the original directory
Set-Location -Path $originalLocation
