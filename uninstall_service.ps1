# Elevation check
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole] "Administrator")) {
    Write-Host "Restarting script as Administrator..."
    Start-Process powershell "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$serviceName = "NoteApp-Backend"
$nssmPath = Join-Path $PSScriptRoot "tools\nssm\win64/nssm.exe"

Write-Host "Stopping and removing service '$serviceName'..."
& $nssmPath stop $serviceName
& $nssmPath remove $serviceName confirm

Write-Host "Service removed."
