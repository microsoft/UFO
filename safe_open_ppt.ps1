# Script Name: safe_open_ppt.ps1

param(
    [Parameter(Mandatory=$true, HelpMessage="Please enter the full path to the PowerPoint file.")]
    [string]$FilePath
)

# Check if the file exists
if (-not (Test-Path $FilePath)) {
    Write-Error "ERROR: File '$FilePath' does not exist."
    exit 1
}

# Basic check for PowerPoint file extension
if (-not ($FilePath.ToLower().EndsWith(".pptx") -or $FilePath.ToLower().EndsWith(".ppt"))) {
    # You can choose to exit here or continue trying to open
    # exit 1
}

# Create PowerPoint application object
try {
    $pptApp = New-Object -ComObject PowerPoint.Application -ErrorAction Stop
}
catch {
    exit 1
}

$pptApp.Visible = -1 # Make PowerPoint window visible

# Open your specified file
try {
    Write-Host "Attempting to open file: $FilePath"
    $presentation = $pptApp.Presentations.Open($FilePath)
}
catch {
    # Attempt to clean up COM object if PowerPoint didn't open any presentation
    if ($pptApp.Presentations.Count -eq 0) {
        $pptApp.Quit()
    }
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pptApp) | Out-Null
    Remove-Variable pptApp
    exit 1
}

# (Optional) If you want to ensure only this one is open, check again and close others
if ($pptApp.Presentations.Count -gt 1) {
    Write-Host "Multiple presentations detected. Closing others besides '$($presentation.Name)'."
    For ($i = $pptApp.Presentations.Count; $i -ge 1; $i--) {
        $currentPresentation = $pptApp.Presentations.Item($i)
        if ($currentPresentation.FullName -ne $presentation.FullName) {
            Write-Host "Closing: $($currentPresentation.Name)"
            $currentPresentation.Close()
        }
    }
}

Write-Host "Script execution finished."

# Note: This script does not automatically release COM objects unless an error occurs during opening.
# The PowerPoint application itself will remain open until manually closed by the user
# or another script calls $pptApp.Quit().
# If you want the script to close PowerPoint after execution (even if the file opened successfully), add:
# $pptApp.Quit()
# [System.Runtime.InteropServices.Marshal]::ReleaseComObject($presentation) | Out-Null
# [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pptApp) | Out-Null
# Remove-Variable presentation, pptApp