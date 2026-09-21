# Bluetooth-tether dev notes — Phone 2 → Phone 1 → desktop (2026-09-28/29)

## Target state (verified working end-to-end, 2026-09-29)
- Phone 2 (SM-A166U, 192.168.44.94) advertises PANU Bluetooth network `"RipRushHotspot"`.
- Phone 1 (SM-S366V) connects to that PANU network, gets a DHCP address on the Phone 2 PAN
  interface, and Linux bridges `pan1` + Wi-Fi `wlan0` so Phone 1's LAN also routes through
  Phone 2's tether.
- Desktop host (192.168.1.168) uses Phone 1's IP as the SOCKS5 upstream for Browser Use's
  chromium to talk SOCKS5→Phone1(NetBridgeGPS)→Phone2(tether)→Internet.
- Browser Use chromium can reach `https://restrict-bank.web.app`+·com and
  `https://uat.bank-account-viz.net`+·com (both require the carrier NAT).

## Why tethering HAS to go through Phone 1, not straight Phone 2 → desktop
Phone 2 is on BT only — Wi-Fi is off because it is the PAN server. Desktop host is RF-proxied
from Phone 1 via NetBridgeGPS, so the only port carrying Internet is Phone 1. Phone 2 exposes
the PAN BSP channel and a DHCP server on its PAN interface, not a Wi-Fi AP.

## Device roles and addresses
| Device | Role | btaddr | PAN side | Notes |
|---|---|---|---|---|
| Phone 2 | PAN server (NAP) | `B0:E1:B6:CF:DA:7B` | `pan0` 192.168.44.1/24 | `pand --manager` started by root; `bt-pan server` NOT usable (initctl missing) |
| Phone 1 | PAN client (PANU) | `FC:55:00:EB:82:34` | `pan1` → DHCP on 192.168.44.0/24 | `pand --client` started by root after Phone 2 advertises |
| Desktop | SOCKS5 client | — | — | `chromium --proxy-server="socks5://cellfanix:pass1234@192.168.1.168:1080/"` |

## Bluetooth pairing/trust
- Phone 2 ↔ Phone 1 already paired and both TRUSTED at the bt level (verified in later
  `bluetoothctl` output). The tether itself is negotiated every time by `pand`, not by BT
  bonding.
- `pand` on Phone 1 does NOT require the remote to be paired/trusted at the bt level — it
  connects over the PAN SDP service. The existing pairing is only there for convenience and
  MAC-level discovery.

## Phone 2 — advertise PANU server
Realized via a root shell on Phone 2 (adb + root). The service unit is:

    [Unit]
    Description=Bluetooth PANU server (Phone 2 → Phone 1 tether)
    After=bluetooth.service
    Requires=bluetooth.service

    [Service]
    Type=simple
    ExecStart=/usr/bin/pand --listen --role=nap --epn-resource=0
    Restart=always
    RestartSec=3

    [Install]
    WantedBy=multi-user.target

Notes:
- `pand --manager` was tried first and worked, but `--listen --role=nap` is what we settled on
  because it survives restarts better in the service model and does not depend on an interactive
  bluetoothctl session.
- The EPN resource flag `--epn-resource=0` is required on some Android builds so the PAN SDP
  record advertises correctly. Omit it and Phone 1's `pand --client` will not find a NAP to
  connect to.
- Phone 2 does NOT run `dnsmasq` for the PAN. Phone 1 runs `dnsmasq --interface=pan1` to hand
  out leases to whatever talks to the bridge. Phone 2's `pand` is only the L2/Ethernet convertor.

## Phone 1 — client + bridge + DHCP
Realized via root on Phone 1. Three pieces run as systemd services:

### 1. Bluetooth PAN client
    [Unit]
    Description=Bluetooth PANU client (Phone 1 → Phone 2 tether)
    After=bluetooth.service
    Requires=bluetooth.service

    [Service]
    Type=simple
    ExecStart=/usr/bin/pand --client --role=panu FC:55:00:EB:82:34
    Restart=on-failure
    RestartSec=5
    StartLimitIntervalSec=60
    StartLimitBurst=4

    [Install]
    WantedBy=multi-user.target

- The remote MAC `FC:55:00:EB:82:34` is Phone 2's `pand --manager` controller MAC... no — that
  is Phone 1's OWN MAC. The `pand --client` target MAC is Phone 2's `B0:E1:B6:CF:DA:7B`.
  Corrected in the actual unit file: `--client --role=panu B0:E1:B6:CF:DA:7B`.
- `pand` will retry the connection if Phone 2's PAN service goes away; the restart policy
  catches the case where Phone 2 reboots and re-advertises.

### 2. Bridge + dnsmasq
`bridge-phones.service` creates `br0` from `pan1` + `wlan0`, moves interfaces onto it, and
starts `dnsmasq` on `br0`.

    [Unit]
    Description=Bridge Phone 1's PAN + Wi-Fi so desktop traffic routes through both
    After=pan-client.service
    Requires=pan-client.service

    [Service]
    Type=oneshot
    RemainAfterExit=yes
    ExecStart=/usr/local/bin/bridge-phones.sh
    ExecStop=/usr/local/bin/bridge-phones-stop.sh

    [Install]
    WantedBy=multi-user.target

`/usr/local/bin/bridge-phones.sh` (root):

```sh
#!/bin/sh
set -e
pan=pan1
wifi=wlan0
br=br0

# Create bridge and move interfaces
ip link add name $br type bridge
ip link set $pan master $br
ip link set $wifi master $br
ip link set $pan up
ip link set $wifi up
ip link set $br up

# dnsmasq on the bridge: DHCP for anything that hits br0
dnsmasq --interface=$br --bind-interfaces \
    --dhcp-range=192.168.1.160,192.168.1.180,255.255.255.0,12h \
    --dhcp-option=3,192.168.1.1 \
    --dhcp-option=6,8.8.8.8 \
    --no-resolv --server=8.8.8.8
```

`/usr/local/bin/bridge-phones-stop.sh` (root):

```sh
#!/bin/sh
ip link set pan1 nomaster
ip link set wlan0 nomaster
ip link del br0
pkill -f 'dnsmasq --interface=br0'
```

Notes:
- Phone 1's own Wi-Fi AP (`hostapd`) and `dnsmasq` for the 192.168.1.0/24 AP are NOT touched by
  this bridge for clients on the AP side; this bridge is only relevant for traffic whose egress
  is chosen to go through `br0` / the PAN path. The desktop host explicitly uses Phone 1's IP as
  a SOCKS5 upstream, so its traffic hits Phone 1's stack and is forwarded out via whichever
  interface has the route. The bridge makes `br0` (and thus the PAN) part of that egress choice.
- Do NOT run `dnsmasq` bound to `pan1` directly — bind it to `br0` so both PAN and Wi-Fi peers
  on the bridge segment see the same DHCP service.

### 3. Routing/egress selection (desktop → Phone 1 → Phone 2 → Internet)
Desktop runs:

    chromium --proxy-server="socks5://cellfanix:pass1234@192.168.1.168:1080/"

Phone 1 runs NetBridgeGPS listening on port 1080 as a SOCKS5 proxy. That proxy forwards the
chromium traffic to whichever interface has Internet. With the PAN+Wi-Fi bridge up, Phone 1 has
both paths; the PAN path leads to Phone 2's carrier NAT.

Verification on Phone 1 that the PAN path is actually carrying Internet:

```sh
# From Phone 1 shell, confirm pan1 has a DHCP address
ip -4 addr show pan1 | grep inet

# Confirm a route out via the PAN side exists and has a carrier
ip route | grep 192.168.44

# Confirm Internet egress works via PAN ( Phone 2's tether )
curl -s --interface pan1 https://ifconfig.me/ip
# should return Phone 2's carrier IP, NOT Phone 1's Wi-Fi IP
```

## Desktop / Browser Use integration
- NetBridgeGPS on Phone 1 listens on `0.0.0.0:1080` SOCKS5 with creds `cellfanix` / `pass1234`.
- Desktop's `chromium` launches point `--proxy-server` at `socks5://cellfanix:pass1234@192.168.1.168:1080/`.
- Browser Use's chromium is the one making the requests to the two carrier-restricted sites, so
  the `--proxy-server` line must be in the Browser Use chromium launch config, NOT in some
  separate desktop-browser profile.

## Troubleshooting

### Phone 1 sees the PAN SDP service but `pand --client` fails with "Can't connect"
1. Confirm Phone 2's `pand --listen --role=nap` is actually running:
   ```
   ps -A | grep pand
   ```
2. Confirm Phone 2's PAN SDP record is registered:
   ```
   sdptool browse local
   ```
   Look for a "PAN Network Access Point" service.
3. Confirm Phone 1 can see Phone 2's BNEP/PAN service at the bt level:
   ```
   sdptool browse B0:E1:B6:CF:DA:7B
   ```
4. If Phone 2 is rooted, confirm the PAN kernel module is loaded:
   ```
   lsmod | grep bnep
   ```
   `bnep.ko` must be loaded for `pand` to negotiate the L2 link.

### Phone 1 gets a DHCP lease on `pan1` but has no Internet through it
1. Check Phone 2's side has a default route out its WWAN/cellular interface:
   ```
   ip route | grep default
   ```
   Phone 2 must be routing Internet-capable traffic out its cellular data, not just acting as a
   L2 convertor.
2. Confirm Phone 1's `pan1` address is in 192.168.44.0/24 and the default route points at
   192.168.44.1 when the PAN path is preferred.
3. `tcpdump -i pan1 -n` on Phone 1 while hitting an external URL — if you see DNS queries but no
   responses, the problem is Phone 2 not forwarding DNS, not the L2 link.

### Desktop chromium reports "ERR_SOCKET_NOT_CONNECTED" or can't reach the carrier-restricted sites
1. Confirm NetBridgeGPS on Phone 1 is listening:
   ```
   ss -ltnp | grep :1080
   ```
2. Confirm desktop can reach Phone 1's IP on port 1080:
   ```
   nc -zv 192.168.1.168 1080
   ```
3. Confirm Phone 1's route out via PAN reaches Internet:
   ```
   curl -s --socks5 cellfanix:pass1234@127.0.0.1:1080 https://ifconfig.me/ip
   ```
   Run this ON Phone 1. It should return Phone 2's carrier IP.
4. If that works but desktop chromium fails, the SOCKS5 creds or proxy string in the chromium
   launch line are wrong.

## Files changed
- `/etc/systemd/system/pan-client.service` (Phone 1)
- `/etc/systemd/system/bridge-phones.service` (Phone 1)
- `/usr/local/bin/bridge-phones.sh` (Phone 1)
- `/usr/local/bin/bridge-phones-stop.sh` (Phone 1)
- `/etc/systemd/system/bt-pan-server.service` (Phone 2)
- `/etc/dnsmasq.d/bridge.conf` if dnsmasq is managed by a drop-in (Phone 1)

## Future work
- Make Phone 2's PAN server survive Phone 1 disconnecting and reconnecting without manual
  restart — possible via a small `pand` restart loop or a systemd path unit watching Phone 1's
  BNEP link.
- Add an iptables/nftables rule on Phone 2 so only Phone 1's PAN MAC can use the tether (so a
  bystander phone on the same PAN subnet cannot NAT through Phone 2).
- If Phone 2 ever gains a Wi-Fi AP mode, consider making the desktop reachable directly on
  192.168.1.0/24 from Phone 2 to remove the Phone 1 bridge hop — but that conflicts with Phone
  2 being the PAN server (Wi-Fi off while PAN server), so not a near-term option.
