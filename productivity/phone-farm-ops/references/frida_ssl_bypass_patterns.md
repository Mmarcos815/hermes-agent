# Frida SSL Bypass Patterns — SDK 36 + IL2CPP Unity

Topical depth for the phone-farm-ops Frida gadget workflow. Read when 
writing or debugging a Frida SSL pinning bypass script for Android, 
especially Unity/IL2CPP apps on SDK 36 (Android 16).

## Config file format (frida-gadget auto-load)

The gadget reads `frida-gadget-config.json` (or `.js`) from its search 
path at startup. Reliable format:

```json
{"interaction": "listen", "script": "frida_ssl_bypass.js"}
```

- `interaction: "listen"` — tells the gadget to load the script in listen 
  mode at startup. Without it, auto-load behavior is inconsistent — the 
  gadget may start the console instead of running the bypass.
- `script` — path to the bypass JS. Use an absolute path 
  (`/data/local/tmp/bypass.js`) when the script lives in `/data/local/tmp/`, 
  or a bare filename (`frida_ssl_bypass.js`) when both files are colocated 
  in the same directory.
- Both `.js` and `.json` extensions are discovered — only the `script` key 
  and `interaction` field matter; the extension is not significant.

**Search order when `libfrida-gadget.so` is DT_NEEDED-injected into the APK:**
1. The gadget's own directory — the APK's `lib/arm64-v8a/` or `lib/arm64/` 
   dir where the `.so` lives.
2. `/data/local/tmp/`

When injecting via DT_NEEDED, prefer baking config + script into the APK so 
they ship inside the installed APK. If pushing post-install, place them in 
BOTH the APK lib dir AND `/data/local/tmp/` to cover both search locations.

**Pitfall:** Files inside the installed APK's native lib dir are owned by 
`system:system` and cannot be overwritten via `adb push` or shell 
redirection after install. To update the config or script in that location, 
rebuild the APK with the corrected files and reinstall.

## SDK 36 (Android 16) Conscrypt hooks

On SDK 36, `com.android.org.conscrypt.TrustManagerImpl` cert-validation 
call path goes through:

```
checkTrusted(X509Certificate[] chain, String authType)           [~line 526]
  → checkTrustedRecursive(...)                                    [~line 677]
  → getTrustedChainForServer(X509Certificate[], String, SSLSession) [~line 374]
```

Hook these directly rather than `verifyChain` overloads, whose signatures 
shifted across SDK versions:

```javascript
var CTM = Java.use("com.android.org.conscrypt.TrustManagerImpl");

// Primary entry: checkTrusted(chain[], authType)
CTM.checkTrusted.overload(
  "java.security.cert.X509Certificate[]", "java.lang.String"
).implementation = function(chain, authType) {
  // return silently = trust all
};

// Socket overload — also on the call path
CTM.checkTrusted.overload(
  "java.security.cert.X509Certificate[]", "java.lang.String", "java.net.Socket"
).implementation = function(chain, authType, socket) {
  // return silently = trust all
};

// Chain builder — return the server chain as-is
CTM.getTrustedChainForServer.overload(
  "java.security.cert.X509Certificate[]", "java.lang.String",
  "javax.net.ssl.SSLSession"
).implementation = function(serverChain, authType, session) {
  return serverChain;
};
```

**Always verify against the live stack trace.** Pull logcat for the app's PID 
and grep for `com.android.org.conscrypt.TrustManagerImpl` to see which method 
is actually on the call path, then hook that specific overload. Wrap each 
`.overload()` call in `try/catch` — the overload may not exist on a given 
device or app classloader.

## IL2CPP / Unity native SSL hooks

Unity apps compiled with IL2CPP ship no Java OkHttp or UnityWebRequest 
classes — those hooks report `ClassNotFoundException` and never fire. The 
app's HTTPS traffic goes through native C# → native SSL (BoringSSL or 
Conscrypt native library). Hook the native exports instead:

```javascript
// SSL_CTX_set_verify — clear the verify callback so no cert check is installed
var SSL_CTX_set_verify = Module.getExportByName(null, "SSL_CTX_set_verify");
if (SSL_CTX_set_verify) {
  Interceptor.attach(SSL_CTX_set_verify, {
    onEnter: function(args) { this.context.args[2] = ptr(0); }
  });
}

// SSL_get_verify_result — force X509_V_OK (0)
var SSL_get_verify_result = Module.getExportByName(null, "SSL_get_verify_result");
if (SSL_get_verify_result) {
  Interceptor.attach(SSL_get_verify_result, {
    onLeave: function(retval) { retval.replace(0); }
  });
}

// X509_verify_cert — force success (1)
var X509_verify_cert = Module.getExportByName(null, "X509_verify_cert");
if (X509_verify_cert) {
  Interceptor.attach(X509_verify_cert, {
    onLeave: function(retval) { retval.replace(1); }
  });
}

// SSL_do_handshake — force success (1)
var SSL_do_handshake = Module.getExportByName(null, "SSL_do_handshake");
if (SSL_do_handshake) {
  Interceptor.attach(SSL_do_handshake, {
    onLeave: function(retval) { retval.replace(1); }
  });
}
```

**Pitfalls:**
- `Module.getExportByName(null, "...")` returns `null` if the export is not 
  found in any loaded module. Always check for `null` before calling 
  `Interceptor.attach()`.
- If `null`, search a specific module:
  ```javascript
  var mod = Process.findModuleByName("libssl.so");
  if (mod) mod.enumerateExports().forEach(function(e) {
    if (e.name.indexOf("SSL_CTX_set_verify") >= 0)
      console.log(e.name, e.address);
  });
  ```
  The export name may be versioned; grep the export list for a substring 
  match rather than assuming the exact name.
- `retval.replace(N)` must use the correct return type: `0` for 
  `SSL_get_verify_result` (int, 0 = X509_V_OK), `1` for `X509_verify_cert` 
  and `SSL_do_handshake` (int, 1 = success). A wrong value silently fails 
  to override the return.
- On Android 16 the SSL library may be `libssl.so`, `libconscrypt.so`, or 
  BoringSSL built into the app's own native libs — check all modules loaded 
  by the app process, not just one name.

## Frida CLI usage notes

### `-l` flag requires a HOST-side path
`frida -l` must point to a script file on the host machine where frida.exe 
runs. A device path like `/data/local/tmp/bypass.js` is interpreted as a 
host path and fails with "No such file or directory". Pattern:
- Gadget auto-load: push script to device, config's `script` points to the 
  device path.
- Host-side attach: `frida -H 127.0.0.1:27042 -p <PID> -l C:/path/to/bypass.js` 
  — pass a host path (e.g. `C:/tmp/bypass.js` or `farm_3phones/frida_ssl_bypass.js`).

### `--eternalize` hangs indefinitely
`frida -l script.js --eternalize` keeps the script resident and holds the 
connection open — it does NOT exit. Use only for a persistent daemon, and run 
it with `background=true` in the terminal tool. For a one-shot verification 
attach (confirm hooks loaded, then detach), omit `--eternalize` so frida exits 
after the script runs.

### Target the live PID only
Before attaching, confirm the target PID is alive and the gadget port is 
listening. A stale PID from a previous launch causes a silent attach failure:
```bash
adb -s IP:PORT shell "ps -A | grep <pkg> | grep -v grep"
adb -s IP:PORT shell "netstat -an | grep 27042"
```
Relaunching the app changes the PID — re-check before every attach.

### Re-establish ADB forward after any ADB daemon restart
`adb kill-server` + `adb start-server` destroys all forwards. Re-establish 
before any host-side attach:
```bash
adb -s IP:PORT forward --remove tcp:27042 2>/dev/null
adb -s IP:PORT forward tcp:27042 tcp:27042
adb -s IP:PORT forward --list | grep 27042   # verify present
```
Without the forward, `frida -H 127.0.0.1:27042` fails with 
"unable to connect to remote frida-server" even though the gadget is 
listening on the device — the forward is the bridge.

## mitmweb log monitoring

After a mitmweb or ADB restart, the log file `mitmweb.log` may stop 
updating even though mitmweb is running and the phone is connecting. Check 
the most recently modified `.log` file in the working directory:
```bash
ls -lt *.log | head -5
tail -f <most_recent> | grep <phone_ip>
```
Also watch live connections as a traffic indicator:
```bash
netstat -an | grep :8082 | grep ESTABLISHED
```
