param (
    [string]$instruction = ""
)

$scriptFolder = "\\host.lan\Data"
$RepoPath = Join-Path -Path $scriptFolder -ChildPath "mm_agents"
$RepoPath = Join-Path -Path $RepoPath -ChildPath "UFO"

# Store the current directory
$originalLocation = Get-Location

# Change to the target directory
Set-Location -Path $RepoPath

# Build the command to execute
$command = "py -m ufo --instruction `"$instruction`" --run_arena `"true`""

# Execute the command
Invoke-Expression $command

# Restore the original directory
Set-Location -Path $originalLocation
