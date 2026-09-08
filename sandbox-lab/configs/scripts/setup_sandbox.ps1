# ============================================================================
# BIONIC DAUGHTER v1 — SANDBOX SETUP SCRIPT (POWER SHELL)
# ============================================================================
# PURPOSE: Guide dad through setting up the sandbox lab on Windows.
# USAGE: Run in PowerShell as administrator (for VirtualBox install if needed).
# ============================================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "BIONIC DAUGHTER SANDBOX SETUP GUIDE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "STEP 1: Install VirtualBox" -ForegroundColor Yellow
Write-Host "Download from: https://www.virtualbox.org/wiki/Downloads" -ForegroundColor White
Write-Host "Install with default options." -ForegroundColor White
Write-Host "Also install the Extension Pack from VirtualBox preferences." -ForegroundColor White
Write-Host "Press any key when VirtualBox is installed..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "STEP 2: Download Kali Linux VM" -ForegroundColor Yellow
Write-Host "Download pre-built VM from: https://www.kali.org/get-kali/" -ForegroundColor White
Write-Host "Choose the VirtualBox image (.ova file)." -ForegroundColor White
Write-Host "Press any key when downloaded..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "STEP 3: Download Vulnerable Target VMs" -ForegroundColor Yellow
Write-Host "Metasploitable 2: https://sourceforge.net/projects/metasploitable/files/Metasploitable2/" -ForegroundColor White
Write-Host "OWASP Juice Shop: https://owasp.org/www-project-juice-shop/" -ForegroundColor White
Write-Host "DVWA: https://github.com/digininja/DVWA" -ForegroundColor White
Write-Host "VulnHub VMs: https://www.vulnhub.com/" -ForegroundColor White
Write-Host "Download the ones you want to practice on." -ForegroundColor White
Write-Host "Press any key when downloaded..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "STEP 4: Import VMs into VirtualBox" -ForegroundColor Yellow
Write-Host "For each VM (.ova or .ovf file):" -ForegroundColor White
Write-Host "  1. Double-click the .ova file, or File > Import Appliance in VirtualBox" -ForegroundColor White
Write-Host "  2. Review settings and import" -ForegroundColor White
Write-Host "  3. After import, configure network for each VM:" -ForegroundColor White
Write-Host "     - Select the VM > Settings > Network > Adapter 1" -ForegroundColor White
Write-Host "     - Attached to: Internal Network" -ForegroundColor White
Write-Host "     - Name: LabNetwork" -ForegroundColor White
Write-Host "  4. ALL VMs must be on the SAME Internal Network (LabNetwork)" -ForegroundColor White
Write-Host ""
Write-Host "Press any key after importing and configuring VMs..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "STEP 5: Configure Static IPs" -ForegroundColor Yellow
Write-Host "For each VM, set a static IP on the LabNetwork:" -ForegroundColor White
Write-Host "  - Kali (attacker): 10.0.0.101" -ForegroundColor White
Write-Host "  - Metasploitable 2: 10.0.0.102" -ForegroundColor White
Write-Host "  - Juice Shop: 10.0.0.103" -ForegroundColor White
Write-Host "  - Other targets: 10.0.0.104, 10.0.0.105, etc." -ForegroundColor White
Write-Host "Note: Exact method varies by VM. Check the VM's documentation." -ForegroundColor White
Write-Host ""

Write-Host "STEP 6: Verify Isolation (CRITICAL)" -ForegroundColor Yellow
Write-Host "Start the Kali VM and one target VM." -ForegroundColor White
Write-Host "From Kali, run these checks:" -ForegroundColor White
Write-Host "  ping 10.0.0.102  (target - should WORK)" -ForegroundColor Green
Write-Host "  ping 10.0.0.1    (host gateway - should NOT work)" -ForegroundColor Red
Write-Host "  ping 8.8.8.8     (internet - should NOT work)" -ForegroundColor Red
Write-Host ""
Write-Host "If any check gives unexpected results, FIX THE NETWORK before practicing." -ForegroundColor Yellow
Write-Host ""

Write-Host "STEP 7: Take Snapshots" -ForegroundColor Yellow
Write-Host "For each VM, take a clean snapshot:" -ForegroundColor White
Write-Host "  1. Select VM in VirtualBox manager" -ForegroundColor White
Write-Host "  2. Click 'Snapshots' > 'Take'" -ForegroundColor White
Write-Host "  3. Name it clearly: e.g., 'Metasploitable2-Clean-2026-08-15'" -ForegroundColor White
Write-Host "  4. Repeat for each VM" -ForegroundColor White
Write-Host ""

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "SANDBOX SETUP COMPLETE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Safety reminder: Train in the sandbox. It protects you AND everyone else." -ForegroundColor Green
Write-Host "Only practice on systems you own. Never use these skills on real targets" -ForegroundColor Green
Write-Host "without written authorization." -ForegroundColor Green
Write-Host ""
Write-Host "Sandbox lab directory: C:\Users\mobil\OneDrive\Desktop\bionic_daughter_agent\sandbox_lab\" -ForegroundColor White
Write-Host ""
