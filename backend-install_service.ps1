# Elevation check
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole] "Administrator")) {
    Write-Host "Restarting script as Administrator..."
    Start-Process powershell "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$serviceName = "NoteApp-Backend"

# Paths
$exePath = Join-Path $PSScriptRoot "NoteApp-backend.exe"
$nssmPath = Join-Path $PSScriptRoot "tools\nssm\win64/nssm.exe"
$appDir = $PSScriptRoot

# Check if EXE exists
if (-not (Test-Path $exePath)) {
    Write-Error "Executable not found: $exePath"
    exit 1
}

Write-Host "Installing service '$serviceName'..."
Write-Host "EXE Path: $exePath"
Write-Host "App Directory: $appDir"

& $nssmPath install $serviceName $exePath
& $nssmPath set $serviceName AppDirectory $appDir
& $nssmPath set $serviceName AppStdout (Join-Path $appDir "stdout.log")
& $nssmPath set $serviceName AppStderr (Join-Path $appDir "stderr.log")
& $nssmPath set $serviceName AppRotateFiles 1
& $nssmPath set $serviceName Start SERVICE_AUTO_START

Write-Host "Starting service..."
& $nssmPath start $serviceName

Write-Host "Service installed and started."
