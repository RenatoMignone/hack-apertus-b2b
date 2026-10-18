param(
    [Parameter(Mandatory=$true)]
    [System.Net.IPAddress[]]$AllowedAddresses
)

$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script in an elevated PowerShell window.'
}
if ($AllowedAddresses.Count -eq 0) {
    throw 'Supply each approved teammate IP address.'
}
$capability = Get-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
if ($capability.State -ne 'Installed') {
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
}
Set-Service -Name sshd -StartupType Automatic
$rule = Get-NetFirewallRule -Name OpenSSH-Server-In-TCP -ErrorAction SilentlyContinue
if ($rule) {
    Set-NetFirewallRule -Name OpenSSH-Server-In-TCP -Enabled True -RemoteAddress ($AllowedAddresses.IPAddressToString)
} else {
    New-NetFirewallRule -Name OpenSSH-Server-In-TCP -DisplayName 'Navigator team SSH' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 -RemoteAddress ($AllowedAddresses.IPAddressToString)
}
Start-Service sshd
Write-Output 'SSH is enabled for the supplied teammate addresses. Add individual Windows accounts and their public keys before onboarding.'
