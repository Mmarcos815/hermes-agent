# Active Directory Lab Build-Out

Educational Active Directory lab for learning AD security concepts.
Designed for a single Windows Server evaluation VM promoting to Domain Controller.

---

## Lab Topology

```
[ Windows Server 2022 Eval ]
  - Domain Controller (DC01)
  - Domain: lab.local
  - IP: 10.0.0.10 / DHCP
```

## Prerequisites

- Windows Server 2022 Evaluation (180-day eval, renewable)
- 4 GB RAM minimum, 60 GB disk
- Hypervisor: VirtualBox / VMware / Hyper-V
- Set NIC to **Host-Only** or **Internal** (isolated — no route to the internet)

---

## Step 1 — Install Windows Server Evaluation

1. Download the ISO from Microsoft Evaluation Center.
2. Boot VM, choose **Windows Server Standard (Desktop Experience)**.
3. Set Administrator password (lab use only — e.g., `LabPass123!`).
4. Complete OOBE, log in as local Administrator.

## Step 2 — Configure Networking

```powershell
# Rename the adapter and set a static IP
Rename-NetAdapter -Name "Ethernet" -NewName "LAB"
New-NetIPAddress -InterfaceAlias "LAB" -IPAddress 10.0.0.10 -PrefixLength 24
Set-DnsClientServerAddress -InterfaceAlias "LAB" -ServerAddresses 127.0.0.1
```

> Pointing DNS at 127.0.0.1 is safe **after** promotion. Before promotion, use `127.0.0.1` as a placeholder or leave DHCP — but the DC must resolve its own name.

## Step 3 — Promote to Domain Controller

```powershell
# Install AD DS role
Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools

# Promote to DC (creates new forest)
Import-Module ADDSDeployment
$pass = ConvertTo-SecureString "LabPass123!" -AsPlainText -Force
Install-ADDSForest `
    -DomainName "lab.local" `
    -DomainNetBIOSName "LAB" `
    -SafeModeAdministratorPassword $pass `
    -InstallDNS `
    -Force
```

The server restarts automatically. Log in as `LAB\Administrator`.

## Step 4 — Create Lab Objects

Run the provided `setup.ps1` from an elevated PowerShell session:

```powershell
.\setup.ps1
```

This creates:

| Object | Type | Purpose |
|--------|------|---------|
| `svc_sql` | User (SPN) | Kerberoasting target |
| `svc_backup` | User (SPN) | Kerberoasting target |
| `jsmith`, `adoe`, `mjones` | Users | Regular users |
| `IT_Admins` | Group | Admin-tier group |
| `Tier0_Admins` | Group | High-privilege group |
| `SQL_Admins` | Group | Nested group target |
| `FileShare01` | Share | SMB enumeration target |

## Step 5 — Verify the Lab

```powershell
# Confirm AD is healthy
Get-ADDomainController
Get-ADUser -Filter * | Select Name, SamAccountName

# Confirm SPNs exist (kerberoast prerequisite)
Setspn -L LAB\svc_sql
```

## Attack Simulations Included

| Script | Technique | MITRE ATT&CK |
|--------|-----------|--------------|
| `attack_paths.py` | Maps privilege-escalation paths through group nesting | T1078, T1098 |
| `kerberoast_sim.py` | Requests and cracks TGS tickets for service accounts | T1558.003 |
| `dcsync_sim.py` | Simulates DC replication credential extraction | T1003.006 |

Run them against the lab **after** `setup.ps1` has populated it.

---

## Reset / Teardown

```powershell
# Remove the forest (irreversible)
Uninstall-ADDSDomainController `
    -DemoteOperationMasterRole `
    -RemoveApplicationPartition `
    -Force
```

To just wipe lab objects without demoting, remove the OUs under `OU=Lab,DC=lab,DC=local`.

---

## Legal / Ethical Notice

These scripts are for **isolated lab environments only**. Attacking networks
without authorization is illegal. Use a host-only adapter and ensure no
production systems share the segment.
