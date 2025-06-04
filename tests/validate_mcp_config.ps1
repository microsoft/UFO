# MCP Configuration Validation Script
# This script validates all MCP configuration files and components

param(
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Continue"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-YamlFile {
    param(
        [string]$FilePath,
        [string]$Description
    )
    
    Write-ColorOutput "Testing $Description..." "Cyan"
    
    if (Test-Path $FilePath) {
        Write-ColorOutput "  ✓ File exists: $FilePath" "Green"
        
        try {
            # Test YAML parsing using Python
            $testCommand = "import yaml; yaml.safe_load(open('$($FilePath.Replace('\', '\\'))'));print('Valid YAML')"
            $result = python -c $testCommand 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "  ✓ Valid YAML syntax" "Green"
                return $true
            } else {
                Write-ColorOutput "  ✗ Invalid YAML syntax: $result" "Red"
                return $false
            }
        }
        catch {
            Write-ColorOutput "  ✗ Error parsing YAML: $($_.Exception.Message)" "Red"
            return $false
        }
    } else {
        Write-ColorOutput "  ✗ File not found: $FilePath" "Red"
        return $false
    }
}

function Test-Directory {
    param(
        [string]$DirectoryPath,
        [string]$Description
    )
    
    Write-ColorOutput "Testing $Description..." "Cyan"
    
    if (Test-Path $DirectoryPath -PathType Container) {
        Write-ColorOutput "  ✓ Directory exists: $DirectoryPath" "Green"
        return $true
    } else {
        Write-ColorOutput "  ✗ Directory not found: $DirectoryPath" "Red"
        return $false
    }
}

function Test-ConfigurationIntegrity {
    Write-ColorOutput "Testing Configuration Integrity..." "Cyan"
    
    try {
        # Test that servers config references valid instruction files
        $serversConfigPath = "ufo\config\mcp_servers.yaml"
        $pythonScript = @"
import yaml
import os

with open('$($serversConfigPath.Replace('\', '\\'))') as f:
    config = yaml.safe_load(f)

servers = config.get('mcp_servers', {})
for name, server_config in servers.items():
    instructions_path = server_config.get('instructions_path', '')
    if instructions_path:
        full_path = os.path.join('.', instructions_path)
        if os.path.exists(full_path):
            print(f'✓ {name}: Instructions file exists')
        else:
            print(f'✗ {name}: Instructions file missing: {full_path}')
"@
        
        $result = python -c $pythonScript
        Write-ColorOutput $result "White"
        
    }
    catch {
        Write-ColorOutput "  ✗ Error checking configuration integrity: $($_.Exception.Message)" "Red"
    }
}

# Main validation
Write-ColorOutput "MCP Configuration Validation" "Yellow"
Write-ColorOutput "=" * 40 "Yellow"

# Test directory structure
$baseDir = Get-Location
$ufoConfigDir = Join-Path $baseDir "ufo\config"
$mcpInstructionsDir = Join-Path $ufoConfigDir "mcp_instructions"

Test-Directory $ufoConfigDir "UFO Config Directory"
Test-Directory $mcpInstructionsDir "MCP Instructions Directory"

# Test main configuration files
$mcpServersConfig = Join-Path $ufoConfigDir "mcp_servers.yaml"
$mcpLauncherConfig = Join-Path $ufoConfigDir "mcp_launcher.yaml"
$mcpConfigScript = Join-Path $ufoConfigDir "mcp_config.py"

Test-YamlFile $mcpServersConfig "MCP Servers Configuration"
Test-YamlFile $mcpLauncherConfig "MCP Launcher Configuration"

if (Test-Path $mcpConfigScript) {
    Write-ColorOutput "✓ MCP Config Manager exists: $mcpConfigScript" "Green"
} else {
    Write-ColorOutput "✗ MCP Config Manager missing: $mcpConfigScript" "Red"
}

# Test instruction files
Write-ColorOutput "Testing MCP Instruction Files..." "Cyan"
$instructionFiles = @("powerpoint.yaml", "word.yaml", "excel.yaml", "web.yaml", "shell.yaml")

foreach ($file in $instructionFiles) {
    $filePath = Join-Path $mcpInstructionsDir $file
    Test-YamlFile $filePath "MCP Instructions for $($file.Replace('.yaml', ''))"
}

# Test PowerShell launcher
$launcherScript = Join-Path $baseDir "launch_mcp_servers.ps1"
if (Test-Path $launcherScript) {
    Write-ColorOutput "✓ PowerShell Launcher exists: $launcherScript" "Green"
} else {
    Write-ColorOutput "✗ PowerShell Launcher missing: $launcherScript" "Red"
}

# Test configuration integrity
Test-ConfigurationIntegrity

Write-ColorOutput "`nValidation Complete!" "Yellow"
Write-ColorOutput "=" * 40 "Yellow"
