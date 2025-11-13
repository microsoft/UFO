# Requires: Windows PowerShell 5+ (or PowerShell 7) on Windows 10/11

# ---- config / inputs ---------------------------------------------------------
$appsFile = "app.txt"     # one app name per line (Store name)
$genericFile = "generic_time.txt"     # optional extra prompt text

# ---- helper: write info/error conveniently ----------------------------------
function Info($msg)  { Write-Host "[INFO ] $msg" -ForegroundColor Cyan }
function Warn($msg)  { Write-Warning $msg }
function Fail($msg)  { Write-Error $msg }

# ---- read files --------------------------------------------------------------
if (-not (Test-Path $appsFile)) { throw "Missing apps file: $appsFile" }
$apps = Get-Content $appsFile | Where-Object { $_.Trim() -ne '' }

$common = ""
if (Test-Path $genericFile) { $common = Get-Content $genericFile -Raw }

# Ensure .\rec exists next to this script
# Resolve script directory safely (no assignment to $PSScriptRoot)
$baseDir = if ($PSCommandPath) {
    Split-Path -Parent $PSCommandPath
} else {
    (Get-Location).Path
}

# Ensure .\rec exists under the script (or current) directory
$recDir = Join-Path $baseDir 'rec'
if (-not (Test-Path -LiteralPath $recDir)) {
    New-Item -ItemType Directory -Path $recDir -Force | Out-Null
}

# Ensure .\netdump exists under the script (or current) directory
$netdumpDir = Join-Path $baseDir 'netdump'
if (-not (Test-Path -LiteralPath $netdumpDir)) {
    New-Item -ItemType Directory -Path $netdumpDir -Force | Out-Null
}

# ---- helpers -----------------------------------------------------------------
function Set-NormalizeName([string]$s) {
  if ([string]::IsNullOrWhiteSpace($s)) { return "" }
  $t = $s.ToLowerInvariant()
  $t = ($t -replace '[®™©]', '')
  $t = ($t -replace '[^a-z0-9\s]', ' ')
  $t = ($t -replace '\s+', ' ').Trim()
  return $t
}

function Get-Aliases([string]$name) {
  $aliases = New-Object System.Collections.Generic.HashSet[string]
  if ([string]::IsNullOrWhiteSpace($name)) { return $aliases }

  $aliases.Add($name) | Out-Null

  # strip after colon / dash
  if ($name -match '^(.*?):') { $aliases.Add($Matches[1].Trim()) | Out-Null }
  if ($name -match '^(.*?)-') { $aliases.Add($Matches[1].Trim()) | Out-Null }

  # strip parentheses
  $aliases.Add(($name -replace '\(.*?\)', '').Trim()) | Out-Null

  # normalized originals
  $aliases.Add((Set-NormalizeName $name)) | Out-Null

  # IMPORTANT: create a snapshot before adding more while iterating
  $snapshot = @()
  foreach ($it in $aliases) { $snapshot += $it }

  foreach ($a in $snapshot) {
    $aliases.Add((Set-NormalizeName $a)) | Out-Null
  }

  # common shortener for "X: subtitle"
  if ($name -match '^(.+?):\s') {
    $aliases.Add($Matches[1]) | Out-Null
    $aliases.Add((Set-NormalizeName $Matches[1])) | Out-Null
  }

  return $aliases
}

function Find-InstalledAppName([string]$targetName) {
  $startApps = Get-StartApps | Where-Object { $_.Name }
  $index = @{}
  foreach ($sa in $startApps) {
    $norm = Set-NormalizeName $sa.Name
    if (-not $norm) { continue }
    if (-not $index.ContainsKey($norm)) { $index[$norm] = @() }
    $index[$norm] += ,$sa
  }

  $candidates = Get-Aliases $targetName

  # 1) exact normalized match
  foreach ($cand in $candidates) {
    $norm = Set-NormalizeName $cand
    if ($norm -and $index.ContainsKey($norm)) {
      return ($index[$norm] | Select-Object -First 1)
    }
  }

  # 2) fuzzy "contains" match (your original behavior)
  $allNorms = $index.Keys
  foreach ($cand in $candidates) {
    $normCand = Set-NormalizeName $cand
    if (-not $normCand) { continue }
    $hits = $allNorms | Where-Object { $_ -like "*$normCand*" -or $normCand -like "*$_*" }
    if ($hits) {
      $best = ($hits | Sort-Object Length -Descending | Select-Object -First 1)
      return ($index[$best] | Select-Object -First 1)
    }
  }

  # 3) NEW: word-overlap fallback to handle Store vs Start name differences
  $normTarget = Set-NormalizeName $targetName
  if ($normTarget -and $allNorms) {
    $targetTokens = $normTarget -split ' '
    $targetTokens = $targetTokens | Where-Object { $_ }  # drop empties
    if ($targetTokens.Count -gt 0) {
      $firstToken = $targetTokens[0]

      $bestKey   = $null
      $bestScore = 0

      foreach ($normName in $allNorms) {
        $appTokens = ($normName -split ' ') | Where-Object { $_ }
        if (-not $appTokens) { continue }

        # intersection of tokens
        $intersection = $appTokens | Where-Object { $targetTokens -contains $_ }
        $score = $intersection.Count

        # small bonus if the "brand" (first token) matches
        if ($firstToken -and ($intersection -contains $firstToken)) {
          $score++
        }

        if ($score -gt $bestScore) {
          $bestScore = $score
          $bestKey   = $normName
        }
      }

      # require at least 2 shared tokens to avoid silly matches
      if ($bestKey -and $bestScore -ge 2) {
        return ($index[$bestKey] | Select-Object -First 1)
      }
    }
  }

  return $null
}

function Start-UWPAppByName([string]$preferredName, [ref]$resolvedStartApp) {
  # Try to resolve Start menu app (object with .Name and .AppID)
  $sa = Find-InstalledAppName $preferredName
  if (-not $sa) { return $false }

  $resolvedStartApp.Value = $sa
  if ($sa.AppID) {
    try {
      # This reliably launches UWP/Store apps
      Start-Process "explorer.exe" "shell:appsFolder\$($sa.AppID)"
      Start-Sleep -Seconds 3
      return $true
    } catch {
      Warn "AUMID launch failed for '$($sa.Name)': $($_.Exception.Message)"
    }
  }
  return $false
}

function Invoke-FallbackStartMenuLaunch([string]$text) {
  try {
    powershell -Command "$wshell = New-Object -ComObject wscript.shell; $wshell.SendKeys('^{ESC}'); Start-Sleep -m 900; $wshell.SendKeys('$text'); Start-Sleep -m 900; $wshell.SendKeys('{ENTER}')"
    Start-Sleep -Seconds 3
    return $true
  } catch {
    Warn "Fallback launcher failed: $($_.Exception.Message)"
    return $false
  }
}
function Get-RelatedIdsFromPsList {
    <#
      .SYNOPSIS
        Returns related process IDs for a target app, parsed from helpers\pslist.exe (if present)
        with strong guards to avoid adding PID 0.

      .PARAMETER Target
        A string to match against the process name / window title (case-insensitive).

      .PARAMETER PsListPath
        Path to pslist.exe. If not found, falls back to Get-Process.

      .OUTPUTS
        [int[]] distinct, > 0
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Target,
        [string]$PsListPath = ".\helpers\pslist64.exe"
    )

    $pids = @()

    try {
        if (Test-Path -LiteralPath $PsListPath) {
            # pslist default output usually has lines like:
            # procname           pid   ...
            $raw = & $PsListPath | Out-String
            if (-not [string]::IsNullOrWhiteSpace($raw)) {
                foreach ($line in $raw -split "(`r`n|`n)") {
                    # Try to capture "name" and "pid" numbers; be liberal in spacing
                    if ($line -match '^\s*(?<name>[^\s]+)\s+(?<pid>\d+)\b') {
                        $name = $Matches['name']
                        $pidInt = 0
                        if ([int]::TryParse($Matches['pid'], [ref]$pidInt) -and $pidInt -gt 0) {
                            if ($name -like "*$Target*" -or $Target -like "*$name*") {
                                $pids += $pidInt
                            }
                        }
                    }
                }
            }
        } else {
            # Fallback: use built-in Get-Process and fuzzy match on process name / main window title
            $procs = Get-Process -ErrorAction SilentlyContinue
            foreach ($p in $procs) {
                $name = $p.ProcessName
                $title = $null
                try { $title = $p.MainWindowTitle } catch {}
                if ( ($name -and ($name -like "*$Target*")) -or ($title -and ($title -like "*$Target*")) ) {
                    if ($p.Id -gt 0) { $pids += [int]$p.Id }
                }
            }
        }
    } catch {
        Warn "Get-RelatedIdsFromPsList failed: $($_.Exception.Message)"
    }

    # Final guardrails: remove 0/negatives, dedupe, sort
    $pids = $pids | Where-Object { $_ -is [int] -and $_ -gt 0 } | Sort-Object -Unique
    return ,$pids
}

function Stop-IdsRobust {

    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][object[]]$Ids,
        [string]$AppName = "",
        [string]$PsKillPath = ".\helpers\pskill64.exe",
        [switch]$Tree
    )

    # Sanitize input -> integers > 0
    $pidList = @()
    foreach ($i in $Ids) {
        if ($null -ne $i) {
            $s = "$i".Trim()
            if ($s -match '^\d+$') {
                $v = [int]$s
                if ($v -gt 0) { $pidList += $v }
            }
        }
    }
    $pidList = $pidList | Sort-Object -Unique

    if (-not $pidList -or $pidList.Count -eq 0) {
        Warn "No related PIDs found to terminate for '$AppName'."
        return
    }

    try {
        if (Test-Path -LiteralPath $PsKillPath) {
            $args = @()
            if ($Tree.IsPresent) { $args += '-t' }
            $args += $pidList | ForEach-Object { "$_" }

            Info "$([IO.Path]::GetFileName($PsKillPath)) $($args -join ' ')"
            $p = Start-Process -FilePath $PsKillPath -ArgumentList $args -NoNewWindow -PassThru -Wait -ErrorAction Stop
            if ($p.ExitCode -ne 0) {
                Warn "pskill exited with code $($p.ExitCode). Falling back to Stop-Process."
                foreach ($single_pid in $pidList) {
                    try { Stop-Process -Id $single_pid -Force -ErrorAction Stop } catch { Warn "Stop-Process($pid): $($_.Exception.Message)" }
                    Info "Stopped process Id $single_pid for '$AppName'."
                }
            }
        } else {
            foreach ($single_pid in $pidList) {
                try { Stop-Process -Id $single_pid -Force -ErrorAction Stop } catch { Warn "Stop-Process($pid): $($_.Exception.Message)" }
                Info "Stopped process Id $single_pid for '$AppName'."
            }
        }
    } catch {
        Fail " Stop-IdsRobust failed: $($_.Exception.Message)"
    }
}


function Stop-AppProcesses { param([Parameter(Mandatory)][string]$DisplayName)
  $allIds = @()
  if (Test-Path -LiteralPath ".\helpers\pslist64.exe") {
    $idsFromSys = Get-RelatedIdsFromPsList -Target $DisplayName
    if ($idsFromSys.Count -gt 0) { $allIds += $idsFromSys }
  } else { Fail "pslist64.exe not found; using native fallback." }
  try {
    $procs = Get-Process -ErrorAction SilentlyContinue | Where-Object {
      $_.Name -like "*$DisplayName*" -or $_.MainWindowTitle -like "*$DisplayName*"
    }
    foreach ($p in $procs) { if ($allIds -notcontains $p.Id) { $allIds += $p.Id } }
  } catch {}
  $allIds = $allIds | Sort-Object -Unique
  if ($allIds.Count -eq 0) { Info "No matching processes for '$DisplayName'."; return }
  Info "Terminating related Ids for '$DisplayName': $($allIds -join ', ')"
  Stop-IdsRobust -Ids $allIds -AppName $DisplayName
}

$mitmCA = "$env:USERPROFILE\.mitmproxy\mitmproxy-ca-cert.pem"
$env:SSL_CERT_FILE = $mitmCA
$env:REQUESTS_CA_BUNDLE = $mitmCA

# --- helpers: start/stop mitmdump as a background process
function Start-Mitmdump {
    param(
        [string]$OutFile,
        [string]$Mode = "local",      # or "regular"
        [string[]]$IgnoreHosts = @()
    )

    if (-not (Get-Command mitmdump -ErrorAction SilentlyContinue)) {
        throw "mitmdump not found on PATH."
    }

    $args = @("--mode", $Mode, "-w", $OutFile)

    foreach ($pat in $IgnoreHosts) {
        $args += @("--ignore-hosts", $pat)  # <-- repeat flag per pattern
    }

    Start-Process -FilePath "mitmdump" -ArgumentList $args -WindowStyle Hidden -PassThru
}


function Stop-Mitmdump {
    param([Parameter(Mandatory)]$Process)
    if ($Process -and -not $Process.HasExited) {
        Stop-Process -Id $Process.Id -Force
        # tiny wait to ensure file is flushed
        Start-Sleep -Milliseconds 250
    }
}

# (Optional) enable/disable system proxy around the run (helps UWP/system apps use the proxy)
function Enable-SystemProxy {
    param([string]$Endpoint = "127.0.0.1:8080")
    try {
        netsh winhttp set proxy $Endpoint | Out-Null
    } catch { Warn "Couldn't set WinHTTP proxy: $($_.Exception.Message)" }
}
function Disable-SystemProxy {
    try {
        netsh winhttp reset proxy | Out-Null
    } catch { Warn "Couldn't reset WinHTTP proxy: $($_.Exception.Message)" }
}

# ---- main --------------------------------------------------------------------
$failures = @()

foreach ($rawApp in $apps) {
  $storeName = $rawApp.Trim()
  if (-not $storeName) { continue }

  $resolved = $null
  python .\helpers\rec.py --grab gdigrab --cursor --out ".\rec\$($storeName -replace '[^a-zA-Z0-9]', '_').mp4"
  $dumpFile = ".\netdump\$($storeName -replace '[^a-zA-Z0-9]', '_').mitm"
  $mitmProc = Start-Mitmdump -OutFile $dumpFile -Mode local -IgnoreHosts @(
    '(^|\.)generativelanguage\.googleapis\.com$',
    '^127\.0\.0\.1:7861$'
  )
  $launched = Start-UWPAppByName $storeName ([ref]$resolved)

  $displayName = if ($resolved) { $resolved.Name } else { $storeName }

  if ($launched) {
    Info "Resolved '$storeName' -> Start menu app '$($resolved.Name)'; launched via AUMID."
  } else {
    Warn "Could not AUMID-launch '$storeName'. Fallback to Start-menu keystrokes..."
    $aliasSet = Get-Aliases $storeName
    # try a few best candidates (shortest first often matches Start search)
    foreach ($cand in ($aliasSet | Sort-Object Length)) {
      if (Invoke-FallbackStartMenuLaunch $cand) { $displayName = $cand; break }
    }
  }

  # Build UFO request; app should already be running now
  $request = @"
Bring the '$displayName' app to the front and then do:

$common
"@

  $startTime = Get-Date
  Info ("Starting UFO for: {0} on {1}" -f$displayName, $startTime.ToString("yyyy-MM-dd HH:mm:ss"))
  python -m ufo --task "$($displayName -replace ':', '')" --request "$request"
  try { Stop-AppProcesses -DisplayName $displayName } catch { Warn "Stop-AppProcesses errored: $($_.Exception.Message)" }
  # try { Stop-AppProcesses -DisplayName "msedge" } catch { Warn "Stop-AppProcesses errored: $($_.Exception.Message)" }
  Stop-Mitmdump -Process $mitmProc
  Info "Mitmdump stopped; output saved to $dumpFile"
  $endTime = Get-Date
  $elapsed = New-TimeSpan -Start $startTime -End $endTime
  Info ("Finished UFO for: {0} at {1} (elapsed {2})" -f $displayName, $endTime.ToString("yyyy-MM-dd HH:mm:ss"), $elapsed.ToString("hh\:mm\:ss"))
  python .\helpers\end_rec.py
  # Optional: you could scan UFO logs here to verify it interacted with the app,
  # and add to $failures if not detected.
}

if ($failures.Count -gt 0) {
  Warn "The following apps still failed: $($failures -join ', ')"
} else {
  Write-Host "All done."
}