<#
.SYNOPSIS
    Populate the AD lab with users, groups, service accounts, and shares.
.DESCRIPTION
    Run from an elevated PowerShell session after promoting the DC.
    Creates realistic AD objects for attack-path and credential-theft simulations.
.EXAMPLE
    .\setup.ps1
#>

#Requires -Modules ActiveDirectory
#Requires -RunAsAdministrator

[CmdletBinding()]
param(
    [string]$DomainDN = (Get-ADDomain).DistinguishedName,
    [string]$LabOU  = "Lab"
)

$ErrorActionPreference = "Stop"

function Write-Step { param([string]$Msg) Write-Host "[+] $Msg" -ForegroundColor Cyan }

# ── 1. Create Lab OU container ──────────────────────────────────────────────
Write-Step "Creating Lab OU..."
New-ADOrganizationalUnit -Name $LabOU -Path $DomainDN -ProtectedFromAccidentalDeletion $false
$LabPath = "OU=$LabOU,$DomainDN"

# ── 2. Create service accounts (Kerberoasting targets) ─────────────────────
Write-Step "Creating service accounts with SPN..."

$svcAccounts = @(
    @{ Sam = "svc_sql";     SPN = "MSSQLSvc/dc01.lab.local:1433"; Desc = "SQL service account" },
    @{ Sam = "svc_backup";  SPN = "bkp/dc01.lab.local";           Desc = "Backup service account" }
)

foreach ($svc in $svcAccounts) {
    $upn   = "$($svc.Sam)@$((Get-ADDomain).DNSRoot)"
    $pwd   = ConvertTo-SecureString "P@ssw0rd1!" -AsPlainText -Force
    $exist = Get-ADUser -Filter { SamAccountName -eq $svc.Sam } -ErrorAction SilentlyContinue

    if (-not $exist) {
        New-ADUser -SamAccountName $svc.Sam `
                   -UserPrincipalName $upn `
                   -Name $svc.Sam `
                   -Description $svc.Desc `
                   -AccountPassword $pwd `
                   -Enabled $true `
                   -Path $LabPath `
                   -PasswordNeverExpires $true `
                   -CannotChangePassword $true
    }
    # Register SPN (idempotent — Set-ADUser skips duplicates)
    Set-ADUser -Identity $svc.Sam -ServicePrincipalNames @{ Add = $svc.SPN }
    Write-Host "  $($svc.Sam)  ->  $($svc.SPN)"
}

# ── 3. Create regular users ────────────────────────────────────────────────
Write-Step "Creating regular users..."

$users = @(
    @{ Sam = "jsmith";  Name = "John Smith";   Dept = "IT" },
    @{ Sam = "adoe";    Name = "Alice Doe";    Dept = "HR" },
    @{ Sam = "mjones";  Name = "Mike Jones";   Dept = "Finance" }
)

foreach ($u in $users) {
    $upn   = "$($u.Sam)@$((Get-ADDomain).DNSRoot)"
    $pwd   = ConvertTo-SecureString "UserPass1!" -AsPlainText -Force
    $exist = Get-ADUser -Filter { SamAccountName -eq $u.Sam } -ErrorAction SilentlyContinue

    if (-not $exist) {
        New-ADUser -SamAccountName $u.Sam `
                   -UserPrincipalName $upn `
                   -Name $u.Name `
                   -Department $u.Dept `
                   -AccountPassword $pwd `
                   -Enabled $true `
                   -Path $LabPath `
                   -ChangePasswordAtLogon $false
    }
    Write-Host "  $($u.Sam)  ($($u.Name))"
}

# ── 4. Create groups and nesting ──────────────────────────────────────────
Write-Step "Creating groups..."

$groups = @("IT_Admins", "Tier0_Admins", "SQL_Admins", "HelpDesk")
foreach ($g in $groups) {
    $exist = Get-ADGroup -Filter { Name -eq $g } -ErrorAction SilentlyContinue
    if (-not $exist) {
        New-ADGroup -Name $g -GroupScope Global -GroupCategory Security -Path $LabPath
    }
    Write-Host "  $g"
}

# Group memberships (simulates privilege nesting)
Add-ADGroupMember -Identity "IT_Admins"    -Members "jsmith"
Add-ADGroupMember -Identity "SQL_Admins"  -Members "svc_sql"
Add-ADGroupMember -Identity "Tier0_Admins" -Members "IT_Admins", "Administrator"
Add-ADGroupMember -Identity "HelpDesk"    -Members "adoe", "mjones"

Write-Host "`n[+] Group nesting:" -ForegroundColor Cyan
Write-Host "    Tier0_Admins > IT_Admins > jsmith"
Write-Host "    Tier0_Admins > Administrator"
Write-Host "    SQL_Admins   > svc_sql"

# ── 5. Create SMB share ────────────────────────────────────────────────────
Write-Step "Creating SMB share for enumeration practice..."
$sharePath = "C:\LabShare"
if (-not (Test-Path $sharePath)) { New-Item -ItemType Directory -Path $sharePath -Force }
"Secret data for simulation" | Out-File -FilePath "$sharePath\readme.txt"
New-SmbShare -Name "FileShare01" -Path $sharePath -FullAccess "Everyone" -ErrorAction SilentlyContinue
Write-Host "  \\\\dc01\\FileShare01"

Write-Host "`n[OK] Lab objects created successfully." -ForegroundColor Green
