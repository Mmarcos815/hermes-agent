# PID + Forward + Attach checks (frida session start)

Quick checklist before every host-side frida attach to a gadget-loaded process.

## 1. Confirm the live PID
```bash
adb -s IP:PORT shell "ps -A | grep <pkg> | grep -v grep"
# Gives the live PID. A stale PID means the process died and restarted.
```

Relaunching the app changes the PID. Re-check this right before every attach — attaching to a dead PID is a silent failure.

## 2. Confirm the gadget port is listening
```bash
adb -s IP:PORT shell "netstat -an | grep 27042"
# Expect: tcp  0  127.0.0.1:27042  0.0.0.0:*  LISTEN
```
No LISTEN line = the gadget is not loaded, or the process died. Do not attach.

## 3. Confirm the host forward exists
```bash
adb -s IP:PORT forward --list | grep 27042
# Expect: <phone> tcp:27042 tcp:27042
```
Any `adb kill-server` / `adb start-server` destroys all forwards. Re-establish before attaching:
```bash
adb -s IP:PORT forward --remove tcp:27042 2>/dev/null
adb -s IP:PORT forward tcp:27042 tcp:27042
```

### Connectivity test (before attach)
```bash
python -c "import socket; s=socket.socket(); s.settimeout(3)
s.connect(('127.0.0.1',27042)); print('REACHABLE'); s.close()"
```
"REACHABLE" = forward is up and the gadget port is reachable from the host. 
Without this, `frida -H 127.0.0.1:27042` fails with 
"unable to connect to remote frida-server" even though the gadget is listening 
on the device.

## 4. Confirm the bypass script is where the gadget reads it
When the gadget is DT_NEEDED-injected into the APK, it reads config + script 
from (1) the APK's native lib dir, then (2) `/data/local/tmp/`. Check both:
```bash
# (1) APK lib dir — system-owned, cannot overwrite post-install; 
#     verify presence only
adb -s IP:PORT shell "ls /data/app/*/<pkg>*/lib/arm64*/frida-gadget-config.json \
  /data/app/*/<pkg>*/lib/arm64*/frida_ssl_bypass.js 2>/dev/null"

# (2) /data/local/tmp/ — writable spot
adb -s IP:PORT shell "ls -la /data/local/tmp/frida-gadget-config.json \
  /data/local/tmp/frida_ssl_bypass.js 2>/dev/null"
```
If (1) is empty but (2) has the files, the gadget may not find them at 
startup — prefer baking them into the APK, or place them in both locations.

## 5. Attach
```bash
frida -H 127.0.0.1:27042 -p <live_PID> -l C:/host/path/bypass.js -q
```
- `-l` takes a **host** path to the bypass JS — a device path like 
  `/data/local/tmp/...` fails with "No such file or directory".
- Omit `--eternalize` for a one-shot verification attach (frida exits after the 
  script runs; you see the console.log output in terminal). With `--eternalize` 
  the process hangs indefinitely and must be backgrounded.

## 6. Verify hooks actually fired
Pull logcat for the app's PID and grep for bypass console output:
```bash
adb -s IP:PORT shell "logcat -d -t 120000" | grep -E "BYPASS|PIN|hook"
```
No hook lines = the script attached but the hooks did not register. Common causes:
- Java classes (OkHttp, UnityWebRequest) not in the classloader — IL2CPP app, 
  switch to native SSL hooks.
- Conscrypt overload signature wrong — check the live stack trace and match the 
  overload to the actual method on the call path.

Then check mitmweb.log for decrypted traffic from the phone IP:
```bash
tail -20 mitmweb.log | grep <phone_ip>
```
Successful `server connect` lines without `TLS handshake failed` = the bypass is 
working and traffic is flowing through the proxy.
