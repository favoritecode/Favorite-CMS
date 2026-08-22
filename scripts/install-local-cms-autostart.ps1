Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$TaskName = "Favorite CMS Local Servers"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$StartupScript = Join-Path $ProjectRoot "scripts\start-local-cms.ps1"
$LogDir = Join-Path $ProjectRoot "storage\logs"

try {
    if (-not (Test-Path -LiteralPath $StartupScript -PathType Leaf)) {
        throw "Startup script was not found at $StartupScript."
    }

    $windowsPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $windowsPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Run this installer from an elevated PowerShell session under the user who should start Favorite CMS at logon."
    }

    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

    $powerShellExe = (Get-Command "powershell.exe" -ErrorAction Stop).Source
    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $actionArguments = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$StartupScript`""

    $action = New-ScheduledTaskAction `
        -Execute $powerShellExe `
        -Argument $actionArguments `
        -WorkingDirectory $ProjectRoot
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $currentUser
    $principal = New-ScheduledTaskPrincipal `
        -UserId $currentUser `
        -LogonType Interactive `
        -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -MultipleInstances IgnoreNew `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -ExecutionTimeLimit ([TimeSpan]::Zero)

    $task = New-ScheduledTask `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "Starts the Favorite CMS backend on 127.0.0.1:8020, waits for readiness, then starts the Next.js Admin on 127.0.0.1:3010."

    Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
    Write-Host "Scheduled Task '$TaskName' was created or updated for $currentUser."
    Write-Host "It will run at user logon from $ProjectRoot."
    exit 0
}
catch {
    [Console]::Error.WriteLine("Failed to install Scheduled Task '$TaskName': $($_.Exception.Message)")
    exit 1
}
