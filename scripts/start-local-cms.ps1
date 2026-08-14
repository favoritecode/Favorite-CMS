Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\favoriteweb"
$FrontendRoot = Join-Path $ProjectRoot "frontend"
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$EnvFile = Join-Path $ProjectRoot ".env"
$LogDir = Join-Path $ProjectRoot "storage\logs"
$StartupLog = Join-Path $LogDir "startup.log"
$StartupErrorLog = Join-Path $LogDir "startup-error.log"
$BackendStdoutLog = Join-Path $LogDir "backend.log"
$BackendStderrLog = Join-Path $LogDir "backend-error.log"
$FrontendStdoutLog = Join-Path $LogDir "frontend.log"
$FrontendStderrLog = Join-Path $LogDir "frontend-error.log"

$BackendHost = "127.0.0.1"
$BackendPort = 8020
$FrontendHost = "127.0.0.1"
$FrontendPort = 3010
$BackendBaseUrl = "http://${BackendHost}:${BackendPort}"
$BackendLiveUrl = "$BackendBaseUrl/health/live"
$BackendReadyUrl = "$BackendBaseUrl/health/ready"
$FrontendLoginUrl = "http://${FrontendHost}:${FrontendPort}/admin/login"

function Write-StartupLog {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [switch]$AsError
    )

    $line = "{0:yyyy-MM-dd HH:mm:ss} {1}" -f (Get-Date), $Message
    Add-Content -LiteralPath $(if ($AsError) { $StartupErrorLog } else { $StartupLog }) -Value $line
    if ($AsError) {
        [Console]::Error.WriteLine($line)
    }
    else {
        Write-Host $line
    }
}

function Stop-WithError {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [int]$ExitCode = 1
    )

    Write-StartupLog -Message "ERROR: $Message" -AsError
    exit $ExitCode
}

function Import-DotEnv {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Stop-WithError "Environment file was not found at $Path."
    }

    foreach ($line in Get-Content -LiteralPath $Path) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.TrimStart().StartsWith("#")) {
            continue
        }

        if ($line -notmatch '^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$') {
            continue
        }

        $name = $Matches[1]
        $value = $Matches[2].Trim()
        if ($value.Length -ge 2) {
            $first = $value.Substring(0, 1)
            $last = $value.Substring($value.Length - 1, 1)
            if (($first -eq '"' -and $last -eq '"') -or ($first -eq "'" -and $last -eq "'")) {
                $value = $value.Substring(1, $value.Length - 2)
            }
        }

        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

function Get-PortListeners {
    param([Parameter(Mandatory = $true)][int]$Port)

    $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    if ($listeners.Count -gt 0) {
        return $listeners
    }

    # netstat remains available when the NetTCPConnection CIM provider is restricted.
    $netstatListeners = foreach ($line in (& netstat.exe -ano -p tcp 2>$null)) {
        if ($line -match '^\s*TCP\s+\S+:(\d+)\s+\S+\s+LISTENING\s+(\d+)\s*$') {
            if ([int]$Matches[1] -eq $Port) {
                [pscustomobject]@{ OwningProcess = [int]$Matches[2] }
            }
        }
    }

    return @($netstatListeners)
}

function Format-PortOwners {
    param([Parameter(Mandatory = $true)][object[]]$Listeners)

    $descriptions = foreach ($ownerProcessId in ($Listeners.OwningProcess | Sort-Object -Unique)) {
        $process = Get-Process -Id $ownerProcessId -ErrorAction SilentlyContinue
        if ($null -eq $process) {
            "PID $ownerProcessId (process details unavailable)"
            continue
        }

        $description = "PID $ownerProcessId ($($process.ProcessName))"
        try {
            if ($process.Path) {
                $description += " at $($process.Path)"
            }
        }
        catch {
            # Process paths can be unavailable without elevation; the PID and name are enough.
        }
        $description
    }

    return ($descriptions -join "; ")
}

function Get-HttpResult {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [int]$TimeoutSeconds = 3
    )

    try {
        $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec $TimeoutSeconds
        $json = $null
        if ($response.Content) {
            try {
                $json = $response.Content | ConvertFrom-Json
            }
            catch {
                $json = $null
            }
        }

        return [pscustomobject]@{
            StatusCode = [int]$response.StatusCode
            Content = [string]$response.Content
            Json = $json
        }
    }
    catch {
        return [pscustomobject]@{
            StatusCode = 0
            Content = ""
            Json = $null
        }
    }
}

function Test-FavoriteBackendLive {
    $result = Get-HttpResult -Uri $BackendLiveUrl
    $health = $result.Json
    if (
        $null -ne $health -and
        $health.PSObject.Properties.Name -contains "data" -and
        $null -ne $health.data
    ) {
        $health = $health.data
    }

    return (
        $result.StatusCode -eq 200 -and
        $null -ne $health -and
        $health.PSObject.Properties.Name -contains "live" -and
        $health.live -eq $true
    )
}

function Wait-FavoriteBackendReady {
    param(
        [System.Diagnostics.Process]$StartedProcess,
        [int]$TimeoutSeconds = 180
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if ($null -ne $StartedProcess) {
            $StartedProcess.Refresh()
            if ($StartedProcess.HasExited) {
                Stop-WithError "Backend exited with code $($StartedProcess.ExitCode). See $BackendStderrLog."
            }
        }

        $result = Get-HttpResult -Uri $BackendReadyUrl
        $health = $result.Json
        if (
            $null -ne $health -and
            $health.PSObject.Properties.Name -contains "data" -and
            $null -ne $health.data
        ) {
            $health = $health.data
        }

        if (
            $result.StatusCode -eq 200 -and
            $null -ne $health -and
            $health.PSObject.Properties.Name -contains "ready" -and
            $health.ready -eq $true
        ) {
            return
        }

        Start-Sleep -Seconds 2
    }

    Stop-WithError "Backend did not report HTTP 200 with ready=true within $TimeoutSeconds seconds. See $BackendStderrLog."
}

function Test-FavoriteFrontend {
    $result = Get-HttpResult -Uri $FrontendLoginUrl -TimeoutSeconds 5
    return (
        $result.StatusCode -eq 200 -and
        $result.Content.Contains("Favorite CMS") -and
        ($result.Content.Contains("Admin sign in") -or $result.Content.Contains("Sign in to Admin"))
    )
}

function Wait-FavoriteFrontend {
    param(
        [System.Diagnostics.Process]$StartedProcess,
        [int]$TimeoutSeconds = 90
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if ($null -ne $StartedProcess) {
            $StartedProcess.Refresh()
            if ($StartedProcess.HasExited) {
                Stop-WithError "Frontend exited with code $($StartedProcess.ExitCode). See $FrontendStderrLog."
            }
        }

        if (Test-FavoriteFrontend) {
            return
        }

        Start-Sleep -Seconds 2
    }

    Stop-WithError "Frontend did not serve the Favorite CMS Admin login within $TimeoutSeconds seconds. See $FrontendStderrLog."
}

try {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

    if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
        Stop-WithError "Python virtual environment executable was not found at $PythonExe."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $FrontendRoot ".next") -PathType Container)) {
        Stop-WithError "The existing Next.js production build is missing. Run 'pnpm run build' in $FrontendRoot."
    }

    $pnpmCommand = Get-Command "pnpm.cmd" -ErrorAction SilentlyContinue
    if ($null -eq $pnpmCommand) {
        $pnpmCommand = Get-Command "pnpm" -ErrorAction SilentlyContinue
    }
    if ($null -eq $pnpmCommand) {
        Stop-WithError "pnpm was not found on PATH."
    }

    Import-DotEnv -Path $EnvFile
    if ($env:FAVORITE_ACTIVE_THEME -ne "favorite.theme.starter") {
        Stop-WithError "FAVORITE_ACTIVE_THEME must be favorite.theme.starter for this local startup."
    }

    # This process-only value wires the Next.js server to the backend without modifying .env.
    $env:FAVORITE_API_URL = $BackendBaseUrl

    $backendProcess = $null
    $backendListeners = @(Get-PortListeners -Port $BackendPort)
    $backendIsFavorite = Test-FavoriteBackendLive
    if (-not $backendIsFavorite -and $backendListeners.Count -gt 0) {
        for ($attempt = 0; $attempt -lt 5; $attempt++) {
            if (Test-FavoriteBackendLive) {
                $backendIsFavorite = $true
                break
            }
            Start-Sleep -Seconds 1
        }
    }

    if ($backendIsFavorite) {
        Write-StartupLog "Reusing the Favorite CMS backend already listening on $BackendHost`:$BackendPort."
    }
    elseif ($backendListeners.Count -gt 0) {
        $owners = Format-PortOwners -Listeners $backendListeners
        Stop-WithError "Port $BackendPort is occupied by an unrelated or unhealthy service: $owners. No process was stopped."
    }
    else {
        Write-StartupLog "Starting Favorite CMS backend on $BackendHost`:$BackendPort."
        $backendProcess = Start-Process `
            -FilePath $PythonExe `
            -ArgumentList @("-m", "uvicorn", "backend.main:app", "--host", $BackendHost, "--port", "$BackendPort") `
            -WorkingDirectory $ProjectRoot `
            -RedirectStandardOutput $BackendStdoutLog `
            -RedirectStandardError $BackendStderrLog `
            -WindowStyle Hidden `
            -PassThru
    }

    Write-StartupLog "Waiting for backend readiness at $BackendReadyUrl."
    Wait-FavoriteBackendReady -StartedProcess $backendProcess
    Write-StartupLog "Backend is ready."

    $frontendProcess = $null
    $frontendListeners = @(Get-PortListeners -Port $FrontendPort)
    $frontendIsFavorite = Test-FavoriteFrontend
    if ($frontendIsFavorite) {
        Write-StartupLog "Reusing the Favorite CMS frontend already listening on $FrontendHost`:$FrontendPort."
    }
    elseif ($frontendListeners.Count -gt 0) {
        $owners = Format-PortOwners -Listeners $frontendListeners
        Stop-WithError "Port $FrontendPort is occupied by an unrelated or unhealthy service: $owners. No process was stopped."
    }
    else {
        Write-StartupLog "Starting Favorite CMS frontend on $FrontendHost`:$FrontendPort."
        $frontendProcess = Start-Process `
            -FilePath $pnpmCommand.Source `
            -ArgumentList @("start", "--hostname", $FrontendHost, "--port", "$FrontendPort") `
            -WorkingDirectory $FrontendRoot `
            -RedirectStandardOutput $FrontendStdoutLog `
            -RedirectStandardError $FrontendStderrLog `
            -WindowStyle Hidden `
            -PassThru
    }

    Wait-FavoriteFrontend -StartedProcess $frontendProcess
    Write-StartupLog "Favorite CMS local servers are healthy on ports $BackendPort and $FrontendPort. Port 3000 was not accessed."
    exit 0
}
catch {
    Stop-WithError "Startup failed: $($_.Exception.Message)"
}
