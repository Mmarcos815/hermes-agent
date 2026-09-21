<#
.SYNOPSIS
    ACL Permission Scanner for Sensitive System Directories

.DESCRIPTION
    Scans specified system directories for misconfigured ACLs that grant
    excessive write access to non-administrative users or the Everyone group.
    This script is intended for security auditing and forensic analysis.

.PARAMETER Paths
    Array of directory paths to scan. Defaults to common sensitive locations.

.PARAMETER IncludeInherited
    Include inherited ACEs in the analysis (default: excluded to focus on
    explicit ACLs which are the higher-risk configuration).

.PARAMETER OutputFile
    Path to write CSV results. If omitted, results print to console.

.PARAMETER Verbose
    Write-verbose output during scan.

.EXAMPLE
    .\acl_audit.ps1 -Paths @("C:\Windows\System32", "C:\Program Files") -OutputFile findings.csv
#>

# Strong typing throughout
[CmdletBinding()]
param(
    [string[]]
    $Paths = @("C:\Windows\System32", "C:\Windows\Temp", "C:\Windows", "C:\Program Files", "C:\Users"),
    [switch]
    $IncludeInherited = $false,
    [string]
    $OutputFile
)

# Type declarations for structured output
class AclFinding {
    [string]$Directory
    [string]$Identity
    [string]$AccessControlType
    [string]$FileSystemRights
    [string]$IsInherited
    [string]$InheritanceFlags
    [string]$PropagationFlags
    [bool]$IsSensitive
    [string]$RiskLevel
    [datetime]$ScanTime
}

class ScanResult {
    [AclFinding[]]$Findings
    [string[]]$Errors
    [datetime]$ScanDate
}

# High-risk rights that indicate write/modify access
$HighRiskRights = @(
    "FullControl",
    "Modify",
    "Write",
    "WriteFiles",
    "WriteData",
    "AppendData",
    "Delete",
    "TakeOwnership",
    "ChangePermissions"
)

# High-risk identities — groups that should NOT have write on system dirs
$HighRiskIdentities = @(
    "Everyone",
    "BUILTIN\Users",
    "BUILTIN\Guests",
    "CREATOR OWNER",
    "CREATOR GROUP",
    "Authenticated Users",
    "INTERACTIVE"
)

# Sensitive directories that warrant stricter ACL requirements
$SensitiveBasePaths = @(
    "C:\Windows\System32",
    "C:\Windows\SysWOW64",
    "C:\Windows\Temp",
    "C:\Windows",
    "C:\Program Files",
    "C:\Program Files (x86)",
    "C:\Users\Public",
    "C:\ProgramData"
)

function Test-SensitivePath {
    param([string]$Path)
    foreach ($sensitive in $SensitiveBasePaths) {
        if ($Path.StartsWith($sensitive, [System.StringComparison]::InvariantCultureIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Test-HighRiskAce {
    param(
        [System.Security.AccessControl.FileSystemSecurity]$Acl,
        [System.Boolean]$IncludeInherited
    )
    # Returns the first high-risk ACE found, or null
    $aclRules = if ($IncludeInherited) {
        $Acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])
    } else {
        $Acl.GetAccessRules($true, $false, [System.Security.Principal.SecurityIdentifier])
    }

    if ($null -eq $aclRules) { return $null }

    foreach ($rule in $aclRules) {
        $rights = $rule.FileSystemRights.ToString()
        $identity = $rule.IdentityReference.Translate([System.Security.Principal.NTAccount]).Value
        $isInherited = $rule.IsInherited

        # Check if this ACE has any high-risk rights
        $riskMatch = $false
        foreach ($highRiskRight in $HighRiskRights) {
            if ($rights.Split(',') -contains $highRiskRight.Trim()) {
                $riskMatch = $true
                break
            }
        }
        if (-not $riskMatch) { continue }

        # Check if the identity is high-risk
        $identityRisk = $false
        foreach ($highRiskIdentity in $HighRiskIdentities) {
            if ($identity -ieq $highRiskIdentity) {
                $identityRisk = $true
                break
            }
        }

        # Everyone with any write is a risk
        # BUILTIN\Users with FullControl/Modify/Write is a risk
        if ($identityRisk) {
            # Determine risk level
            $riskLevel = "Medium"
            if ($identity -match "Everyone|BUILTIN\\Users" -and `
                ($rights -match "FullControl|Modify|Write|Delete|TakeOwnership|ChangePermissions")) {
                $riskLevel = "High"
            } elseif ($identity -match "BUILTIN\\Guests|Authenticated Users" -and `
                ($rights -match "FullControl|Modify")) {
                $riskLevel = "High"
            }

            return [PSCustomObject]@{
                Rights       = $rights
                Identity     = $identity
                IsInherited  = $isInherited
                RiskLevel    = $riskLevel
            }
        }
    }
    return $null
}

# Main scan logic
$results = [ScanResult]::new()
$results.Findings = @()
$results.Errors = @()
$results.ScanDate = Get-Date

Write-Verbose "Starting ACL audit at $(Get-Date -Format u)"

foreach ($basePath in $Paths) {
    Write-Verbose "Scanning: $basePath"

    if (-not (Test-Path $basePath)) {
        $results.Errors += "Path not found: $basePath"
        continue
    }

    try {
        # Get the ACL for the directory itself
        $acl = Get-Acl -Path $basePath -ErrorAction Stop

        $riskAce = Test-HighRiskAce -Acl $acl -IncludeInherited:$IncludeInherited
        if ($null -ne $riskAce) {
            $finding = [AclFinding]::new()
            $finding.Directory = $basePath
            $finding.Identity = $riskAce.Identity
            $finding.AccessControlType = "Allow"
            $finding.FileSystemRights = $riskAce.Rights
            $finding.IsInherited = $riskAce.IsInherited
            $finding.InheritanceFlags = "ContainerInherit"
            $finding.PropagationFlags = "None"
            $finding.IsSensitive = Test-SensitivePath -Path $basePath
            $finding.RiskLevel = $riskAce.RiskLevel
            $finding.ScanTime = Get-Date

            $results.Findings += $finding

            Write-Verbose "  [ALERT] $($finding.RiskLevel) risk on $basePath - $($finding.Identity) has $($finding.FileSystemRights)"
        }
    } catch {
        $results.Errors += "$basePath : $($_.Exception.Message)"
    }
}

# Output handling
$count = $results.Findings.Count
Write-Host "=== ACL Audit Summary ===" -ForegroundColor Cyan
Write-Host "Scanned $($Paths.Count) directories"
Write-Host "Findings: $count" -ForegroundColor $(if ($count -gt 0) { "Yellow" } else { "Green" })
Write-Host "Errors: $($results.Errors.Count)" -ForegroundColor $(if ($results.Errors.Count -gt 0) { "Red" } else { "Green" })

if ($OutputFile) {
    $results.Findings | Export-Csv -Path $OutputFile -NoTypeInformation -Encoding UTF8
    Write-Host "`nResults written to: $OutputFile" -ForegroundColor Green
} else {
    # Print findings to console with color coding
    if ($results.Findings.Count -gt 0) {
        Write-Host "`n=== HIGH-RISK ACL FINDINGS ===" -ForegroundColor Red
        $results.Findings | Format-Table -AutoSize Directory, Identity, FileSystemRights, RiskLevel, IsSensitive
    }
    if ($results.Errors.Count -gt 0) {
        Write-Host "`n=== ERRORS ===" -ForegroundColor DarkGray
        $results.Errors | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    }
}

# Return typed result object for pipeline consumption
return $results