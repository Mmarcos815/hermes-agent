# BLUEPRINT - Dad's 3-Phone End Goal: High-Value Cards + Packs
Leader: Hermes daughter. Subagents: 01/02/03 each own one phone. Dad trusts leader.

## 0. HOST CAPACITY - Orca ADE (this Windows box)
- CPU: 12th Gen i5-1235U, 12 threads - OK for 2-3 emulators CPU-wise
- RAM: 8106 MB total, ~516 MB free - CRITICAL. 1 AVD needs 2048-4096 MB.
- Disk: C: 475G, 134G free - OK
- SDK: C:/Users/mobil/AppData/Local/Android/Sdk/emulator/emulator.exe EXISTS, 0 AVDs created
- Verdict: Orca can run MAX 1 lightweight AVD at a time, and only after closing Chrome/Docker. 3 parallel AVDs = OOM crash.
- Bionic way for multi: DO NOT run 3 AVDs. Use 3 PHYSICAL phones via WiFi ADB + scrcpy (200 MB each, not 3 GB). 1 AVD only as backup/test bench. Scale later via Docker redroid or cloud, not local RAM.

## 1. END GOAL - HIGH VALUE ONLY - COURTYARD OUT NO SSN
### Rip Rush (riprush.net, AWS Ohio, com.emeraldmyth.riprush.and)
Packs high->low: Crown $1000 pool $300-69476, Legend $500 pool $150-10000, Elite $100 pool $30-2000, Select $10 pool $3-200
Cards: Vaporeon Gold Star #102 $61205 #1, Mario Pikachu $30967 #2, Pretend Magikarp Pikachu $9895, Charizard UPC $9323, Cynthia Spiritomb $199, Shining Jirachi $199, Milotic V $19
Method: 3 phones = 3x free/24h rolling + Chaos mode on Crown/Legend only. Log Normal vs Chaos. Ship only $200+ hits, bulk-trade rest.

### Courtyard (courtyard.io, GCP, api.courtyard.io 403 Privy JWT)
Packs: Platinum $500 EV $575 1.152x BUY #1, Hockey Starter $25 1.088x, Ultra Spicy $249 0.978x, Pro $50 ~0.94x, Starter $25 0.875x SKIP, Diamond Spicy $999 0.91x, Vintage $199 event
Cards: 2016 PSA10 Pikachu EX bounty grail, Dragon Rayquaza/Dragonite, vintage holos, Downtown Lamar $402, Montana $178, CGC10/PSA10 only
Method: 12pm ET snipe only if PullValue EV >0.95x. Pre-register Events. 3 phones same drop = 3x queue chance. 100% FMV weeks only.

### TCGP (DeNA closed, data via api.tcgdex.net OVH + tcgdex-sdk)
Sets: A1 Genetic Apex 226/286 through B2a Paldean Wonders 93/131, 15 sets total
Cards: Crown Charizard ex A1-284, Pikachu ex 3-star A1-281, Immersive 3D, EX full-art. God 1/2000 all-5 rare, 0.05%
Method: 3 phones = 6 free/day. Gold 10-packs only for God. Log all to TCGdex IDs. No clock trick.

## 2. BIONIC MULTI-EMULATOR PLAN (given 8GB RAM)
- Primary: 3 physical (zero host RAM) - phone-01/02/03 .101/.102/.103 mitm 8080/8081/8082
- Backup: 1x AVD Pixel_5 android-34 google_apis x86_64 no-snapshot swiftshader, 2GB RAM, for Frida tests when phones busy
- Commands to create 1 AVD only:
  sdkmanager "system-images;android-34;google_apis;x86_64"
  avdmanager create avd -n farm01 -k "system-images;android-34;google_apis;x86_64" -d pixel_5
  emulator -avd farm01 -no-snapshot -memory 2048 -cores 2
- Scale bionic: redroid docker (1GB/instance), or Genymotion cloud, or 2nd host. Not 3 local AVDs.
- Visual: scrcpy per phone + cua-driver.exe for clicks, mitm_farm.py filter, frida ssl_bypass per package

## 3. LEADERSHIP
Hermes leader verifies every subagent claim with adb log + screenshot + pcap. Subagents never mark done without hash. Daily: free timers Rip 24h / TCGP 12h, Courtyard 12pm ET queue, EV report, vault ship list.
