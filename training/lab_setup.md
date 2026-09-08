# Lab Environment Setup

## Architecture

All labs run in an isolated virtual network on your host:

```
Host Machine
├── Kali Linux (Attacker) — 10.10.1.10
└── Target Network (NAT 10.10.1.0/24)
    ├── Metasploitable 2 — 10.10.1.20
    ├── Windows Server 2019 (DC) — 10.10.1.100
    ├── Windows 10 Client — 10.10.1.101
    └── Ubuntu (DVWA) — 10.10.1.50
```

## Step 1: Virtualization Software

### VMware Workstation Pro
1. Install from broadcom.com
2. Create NAT network: `VMnet8`, subnet `10.10.1.0/24`

### VirtualBox
```
VBoxManage natnetwork add --netname redteam --network "10.10.1.0/24" --enable
```

## Step 2: Attacker VM (Kali Linux)

1. Download Kali VMware image from kali.org
2. Import and set network to VMnet8 (NAT)
3. Boot (kali/kali), then update:
   ```bash
   sudo apt update && sudo apt full-upgrade -y
   sudo apt install -y bloodhound neo4j python3-impacket
   ```
4. Set static IP:
   ```bash
   sudo ip addr add 10.10.1.10/24 dev eth0
   ```

## Step 3: Target VMs

| VM | IP | Credentials |
|----|----|-------------|
| Metasploitable 2 | 10.10.1.20 | msfadmin/msfadmin |
| Windows Server 2019 | 10.10.1.100 | Administrator/P@ssw0rd1 |
| Windows 10 | 10.10.1.101 | corp.local\admin |
| Ubuntu DVWA | 10.10.1.50 | root/toor |

### Windows Server Setup
```powershell
# Promote to DC: corp.local
Install-WindowsFeature AD-Domain-Services
# Create test users
New-ADUser -Name "jsmith" -SamAccountName "jsmith" -AccountPassword (ConvertTo-SecureString "P@ssw0rd1" -AsPlainText -Force) -Enabled $true
```

### DVWA Setup
```bash
sudo apt install -y apache2 mysql-server php php-mysql
git clone https://github.com/digininja/DVWA.git /var/www/html/dvwa
sudo chown -R www-data:www-data /var/www/html/dvwa
```

## Step 4: Verify Connectivity

```bash
nmap -sn 10.10.1.0/24        # Ping sweep
nmap -sV 10.10.1.20          # Metasploitable
curl http://10.10.1.50/dvwa  # DVWA
```

## Step 5: Snapshot All VMs

Take clean-state snapshots before starting labs. Reset between exercises if needed.

## Safety

- Never bridge target network to physical LAN
- Disable shared folders between host and targets
- Use NAT/host-only networking only
- No attacks against systems you don't own
