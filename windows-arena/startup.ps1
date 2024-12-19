param (
    [string]$instruction = "",
    [string]$agent_settings = ""
)

$scriptFolder = "\\host.lan\Data"
$RepoPath = Join-Path -Path $scriptFolder -ChildPath "mm_agents"
$RepoPath = Join-Path -Path $RepoPath -ChildPath "UFO"
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
    $jsonEscaped = $agent_settings -replace '"', '\"'

    # Build the command to execute
    $command = "py -m windows-arena --request `"$instruction`" --agent_settings `'$jsonEscaped`'"

    # Execute the command and redirect output and error streams to the log file
    Invoke-Expression $command 2>&1 | Tee-Object -FilePath $outputFile -Append
} catch {
    # Log the error message to the output file
    $_.Exception.Message | Out-File -FilePath $outputFile -Append
}

# Restore the original directory
Set-Location -Path $originalLocation
