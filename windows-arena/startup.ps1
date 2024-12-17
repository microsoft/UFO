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

try {
    # Escape double quotes in JSON string for safe usage in PowerShell
    $jsonEscaped = $agent_settings -replace '"', '\"'

    # Build the command to execute
    $command = "py -m ufo --request `"$instruction`" --agent_settings `'$jsonEscaped`'"

    # Execute the command
    Invoke-Expression $command
} catch {
    # Log the error message to the output file
    $_.Exception.Message | Out-File $outputFile
}

# Restore the original directory
Set-Location -Path $originalLocation
