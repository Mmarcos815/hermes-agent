import json

output_path = r"C:\Users\mobil\orca\projects\my 1st\gap_training\api_mobile_supply.jsonl"

all_examples = []

def add_examples(category, items):
    for prompt, completion in items:
        all_examples.append({
            "prompt": prompt[:200],
            "completion": completion[:200],
            "metadata": {"domain": "API Mobile Supply", "subcategory": category}
        })

# --- 50 API Examples (10 each in 5 categories) ---

add_examples("GraphQL Injection", [
    ("GraphQL introspection query exposes schema details", "Use introspection to map schema and extract sensitive types"),
    ("GraphQL batching attack bypasses rate limiting", "Send batched queries to circumvent request limits"),
    ("GraphQL field suggestion leak reveals internal API names", "Exploit error hints to discover hidden fields"),
    ("GraphQL nested query causes DoS via deep recursion", "Craft recursive queries to exhaust server resources"),
    ("GraphQL mutation injected through aliased query", "Bypass authorization using query aliasing"),
    ("GraphQL type confusion allows unauthorized access", "Manipulate type casting in input variables"),
    ("GraphQL query injection via unsanitized input parameter", "Inject malicious GraphQL through user-controlled fields"),
    ("GraphQL persisted query cache poisoning", "Overwrite cached queries with malicious payloads"),
    ("GraphQL subscription attack triggers server-side event flooding", "Use subscriptions to flood backend event handlers"),
    ("GraphQL directive injection alters resolver behavior", "Inject custom directives to change query resolution"),
])

add_examples("gRPC Attacks", [
    ("gRPC metadata injection for privilege escalation", "Tamper with gRPC metadata headers for auth bypass"),
    ("gRPC deserialization of untrusted protobuf data", "Exploit protobuf parsing to execute arbitrary code"),
    ("gRPC server reflection enumeration for API discovery", "Use reflection to enumerate all gRPC service methods"),
    ("gRPC stream hijacking via malicious RST_STREAM", "Inject RST frames to hijack active gRPC streams"),
    ("gRPC message size overflow corrupts server memory", "Send oversized gRPC frames to trigger buffer overflow"),
    ("gRPC channel credential downgrade attack", "Force TLS downgrade on gRPC connections"),
    ("gRPC interceptor bypass through raw socket injection", "Bypass gRPC interceptors by sending crafted frames"),
    ("gRPC bidirectional stream exhaustion", "Open excessive bidirectional streams for DoS"),
    ("gRPC method not found error leaks internal structure", "Enumerate valid methods via error response differences"),
    ("gRPC deadline injection causes resource starvation", "Set extreme deadlines to hang server-side processing"),
])

add_examples("REST API Vulnerabilities", [
    ("REST API mass assignment allows role escalation", "Inject extra JSON fields to overwrite protected attributes"),
    ("REST API path traversal via encoded slashes", "Use double-encoded path traversal on REST endpoints"),
    ("REST API JSONP callback injection for XSS", "Inject script tags into JSONP callback parameters"),
    ("REST API HTTP method override header abuse", "Use X-HTTP-Method-Override to bypass endpoint restrictions"),
    ("REST API OAuth token leakage via redirect_uri", "Steal tokens through open redirect in OAuth flow"),
    ("REST API JWT algorithm confusion RS256 to HS256", "Swap asymmetric JWT algorithm to symmetric for forgery"),
    ("REST API CORS misconfiguration allows credential theft", "Exploit wildcard CORS to read authenticated responses"),
    ("REST API pagination injection via crafted offset", "SQL inject through pagination offset parameters"),
    ("REST API content-type bypass for file upload", "Spoof Content-Type to upload executable files"),
    ("REST API race condition in funds transfer", "Parallel requests exploit timing window to double-spend"),
])

add_examples("API Authentication Bypass", [
    ("API key hardcoded in JavaScript bundle exposed", "Extract API keys from client-side source code"),
    ("API token passed in URL parameter logged by proxies", "Leak tokens through URL parameters cached by intermediaries"),
    ("API OAuth implicit flow token in fragment stolen", "Steal access tokens from URL fragment via referrer leakage"),
    ("API JWT none algorithm bypass authentication", "Set alg=none to bypass JWT signature verification"),
    ("API session fixation via predictable session IDs", "Forge session IDs to hijack authenticated state"),
    ("API SAML XML signature wrapping attack", "Modify SAML assertion with signature wrapping to impersonate"),
    ("API JWT kid parameter path traversal", "Inject path traversal in kid header to use arbitrary keys"),
    ("API refresh token rotation bypass", "Reuse refresh tokens before rotation completes"),
    ("API rate limiting bypass via X-Forwarded-For spoofing", "Rotate spoofed IPs to evade API rate limits"),
    ("API MFA bypass through direct endpoint access", "Access protected endpoints directly skipping MFA step"),
])

add_examples("API Deserialization Attacks", [
    ("API Java deserialization with malicious object graph", "Exploit Java deserialization for remote code execution"),
    ("API PHP object injection via serialized payload", "Inject PHP objects through deserialization for code execution"),
    ("API Python pickle deserialization for arbitrary code exec", "Exploit pickle deserialization to run system commands"),
    ("API .NET BinaryFormatter remote code execution", "Exploit .NET BinaryFormatter for server compromise"),
    ("API Ruby Marshal.load deserialization exploit", "Exploit Ruby Marshal deserialization for code execution"),
    ("API Node.js deserialization via node-serialize", "Exploit JavaScript deserialization for code execution"),
    ("API JSON deserialization type confusion attack", "Manipulate JSON types to bypass validation logic"),
    ("API YAML deserialization with unsafe loader execution", "Exploit YAML deserialization for arbitrary code execution"),
    ("API XML deserialization for server-side file access", "Exploit XML deserialization to read local files"),
    ("API messagepack deserialization for memory corruption", "Exploit MessagePack parsing for buffer overflow attacks"),
])

# --- 50 Mobile Examples (10 each in 5 categories) ---

add_examples("iOS Attacks", [
    ("iOS URL scheme handler XSS injection", "Inject JS through unvalidated URL scheme parameters"),
    ("iOS pasteboard data leakage between apps", "Read sensitive data from shared clipboard buffer"),
    ("iOS NSLog sensitive data exposure in release builds", "Extract secrets from device syslog in production apps"),
    ("iOS Universal Link hijacking via apple-app-site-association", "Forge association file to steal universal link traffic"),
    ("iOS WebView JavaScript bridge code execution", "Exploit WebView JS bridge to run native code"),
    ("iOS keychain data extraction from jailbroken device", "Dump keychain items bypassing iOS data protection"),
    ("iOS method swizzling runtime manipulation", "Hook Objective-C methods via runtime manipulation"),
    ("iOS IPA sideloading with enterprise certificate", "Distribute malicious app using stolen enterprise cert"),
    ("iOS backup authentication bypass for local backups", "Access unencrypted local backups to extract app data"),
    ("iOS notification service extension data exfiltration", "Use notification extension to harvest message content"),
])

add_examples("Android Attacks", [
    ("Android intent hijacking via implicit intent interception", "Register malicious receiver to intercept implicit intents"),
    ("Android exported content provider SQL injection", "Query exported providers with malicious SQL payloads"),
    ("Android WebView addJavascriptInterface RCE", "Exploit deprecated JS bridge for remote code execution"),
    ("Android deep link parameter injection", "Inject malicious parameters into app deep links"),
    ("Android shared preferences plaintext credential storage", "Extract plaintext credentials from shared_prefs XML"),
    ("Android broadcast receiver intent spoofing", "Send crafted broadcasts to trigger privileged actions"),
    ("Android certificate pinning bypass via Frida hook", "Hook SSL functions to bypass certificate pinning"),
    ("Android APK repackaging with malicious payload", "Decompile and inject payload then re-sign APK"),
    ("Android task hijacking via affinity manipulation", "Exploit task affinity to hijack another app's task stack"),
    ("Android Binder transaction overflow in system service", "Overflow Binder buffer to corrupt system_server memory"),
])

add_examples("Mobile Authentication", [
    ("Mobile biometric authentication bypass with fake fingerprint", "Spoof fingerprint sensor with printed overlay"),
    ("Mobile OTP interception via SIM swap attack", "Port victim number to attacker SIM to intercept OTPs"),
    ("Mobile app token storage in insecure SQLite database", "Extract auth tokens from unencrypted app databases"),
    ("Mobile push notification MFA fatigue attack", "Flood user with MFA prompts until accidental approval"),
    ("Mobile in-app purchase receipt forgery", "Forge Apple/Google receipts to unlock premium features"),
    ("Mobile certificate validation bypass with custom CA", "Install rogue CA to MITM mobile app TLS connections"),
    ("Mobile session token reuse after logout", "Reuse cached session tokens after user logout"),
    ("Mobile jailbreak/root detection bypass via hooking", "Hook detection functions to hide rooted device state"),
    ("Mobile clipboard manager credential harvesting", "Steal passwords copied to clipboard by password managers"),
    ("Mobile sideloaded app requesting excessive permissions", "Trick users into granting dangerous runtime permissions"),
])

add_examples("Mobile Network Attacks", [
    ("Mobile baseband processor buffer overflow", "Send malformed SMS to exploit baseband firmware"),
    ("Mobile IMSI catcher for location tracking", "Deploy fake cell tower to capture device identifiers"),
    ("Mobile Wi-Fi evil twin hotspot credential theft", "Spoof trusted Wi-Fi network to harvest credentials"),
    ("Mobile Bluetooth Low Energy spoofing attack", "Clone BLE device to send spoofed commands"),
    ("Mobile NFC relay attack for payment fraud", "Relay NFC signal to authorize remote contactless payment"),
    ("Mobile SMS phishing link with device profiling", "Send targeted phishing SMS with device fingerprinting"),
    ("Mobile cellular protocol downgrade to 2G", "Force network downgrade to intercept unencrypted 2G traffic"),
    ("Mobile DNS spoofing via rogue DHCP response", "Respond to DHCP with malicious DNS server address"),
    ("Mobile MMS payload with zero-day exploit", "Send crafted MMS containing media parser exploit"),
    ("Mobile baseband debug interface left enabled", "Access exposed debug ports on modem processor"),
])

add_examples("Mobile App Reverse Engineering", [
    ("Mobile app binary analysis with IDA Pro disassembly", "Disassemble app binary to find hardcoded secrets"),
    ("Mobile app runtime instrumentation with Frida", "Hook functions at runtime to bypass security checks"),
    ("Mobile app network traffic interception via proxy", "Route app traffic through MITM proxy to analyze API calls"),
    ("Mobile app code decompilation from DEX to Java", "Convert DEX bytecode to readable Java source code"),
    ("Mobile app resource extraction for sensitive data", "Extract hardcoded keys and URLs from app resources"),
    ("Mobile app anti-debugging bypass via patching", "Patch anti-debugging checks to enable dynamic analysis"),
    ("Mobile app memory dump for credential extraction", "Dump process memory to extract plaintext credentials"),
    ("Mobile app control flow graph analysis for vulnerability", "Analyze CFG to identify insecure code paths"),
    ("Mobile app string table analysis for API endpoints", "Extract API endpoints from binary string tables"),
    ("Mobile app dynamic analysis with automated fuzzing", "Fuzz app inputs to discover crash vulnerabilities"),
])

# --- 50 Supply Chain Examples (10 each in 5 categories) ---

add_examples("Dependency Confusion", [
    ("Dependency confusion attack via public registry namespace squat", "Publish malicious package matching internal name to public registry"),
    ("Dependency confusion through typosquatting popular packages", "Publish typo variant to public registry for auto-install"),
    ("Dependency confusion via version number manipulation", "Publish higher version malicious package to override internal"),
    ("Dependency confusion in npm private registry misconfiguration", "Exploit npm fallback to public registry for internal packages"),
    ("Dependency confusion in PyPI with scoped package names", "Squat scoped package namespace on public PyPI"),
    ("Dependency confusion via build script injection in postinstall", "Execute arbitrary code through postinstall script in malicious dep"),
    ("Dependency confusion in Docker base image tags", "Override official image tags with malicious builds"),
    ("Dependency confusion through submodule URL hijacking", "Replace git submodule URL with malicious repository"),
    ("Dependency confusion in Go module proxy poisoning", "Poison Go module proxy cache with malicious versions"),
    ("Dependency confusion in Ruby gems with git source", "Override gem sources to pull from attacker-controlled repo"),
])

add_examples("Build Pipeline Attacks", [
    ("CI/CD pipeline poisoning via pull request workflow injection", "Inject malicious commands into CI pipeline through PR"),
    ("Build server compromise through malicious merge request", "Submit MR exploiting build runner command injection"),
    ("Compromised build cache serving tainted artifacts", "Poison build cache to distribute backdoored binaries"),
    ("Compromised code signing certificate in CI environment", "Steal signing certs from CI to sign malicious updates"),
    ("Build artifact injection via supply chain on build host", "Modify build output after compilation but before signing"),
    ("CI/CD secret exposure through debug logging enabled", "Leak secrets via verbose CI pipeline logging output"),
    ("Pipeline-as-code injection via compromised Jenkinsfile", "Modify Jenkinsfile to execute malicious pipeline stages"),
    ("Build dependency inlining with malicious source code", "Replace source URL in inline dependency with malicious version"),
    ("Docker build context secret leakage via .dockerignore", "Leak secrets through improper dockerignore configuration"),
    ("GitHub Actions workflow injection via third-party action", "Supply malicious action dependency to target repository"),
])

add_examples("Software Supply Chain", [
    ("Software update mechanism MITM with self-signed cert", "Intercept updates lacking certificate pinning"),
    ("Open source maintainer account compromise via phishing", "Phish maintainer to push malicious commits"),
    ("Malicious npm package with install-time data exfiltration", "Steal environment variables via npm install script"),
    ("Compromised compiler inserting backdoors into binaries", "Use self-replicating compiler backdoor across builds"),
    ("Supply chain attack via compromised IDE extension", "Install malicious extension to inject backdoor during dev"),
    ("Open source project takeover via abandoned maintainer", "Assume control of unmaintained project with backdoor"),
    ("Software bill of materials tampering to hide dependencies", "Falsify SBOM to conceal vulnerable dependencies"),
    ("Container image layer cache poisoning in registry", "Overwrite registry layers with malicious image data"),
    ("Package registry account takeover via credential stuffing", "Take over maintainer account with reused passwords"),
    ("Cryptographic hash collision in software distribution", "Forge hash collision to substitute malicious binary"),
])

add_examples("Container Supply Chain", [
    ("Container image vulnerability scanning bypass via layering", "Hide malicious payload in intermediate image layers"),
    ("Kubernetes Helm chart repository compromise", "Distribute malicious Helm charts to target clusters"),
    ("Container registry webhook injection for deployment trigger", "Trigger malicious deployments via registry webhook"),
    ("Dockerfile multi-stage build secret leakage", "Leak secrets between build stages via layer caching"),
    ("Container runtime escape via vulnerable runc version", "Exploit runc vulnerability to escape container isolation"),
    ("Kubernetes operator supply chain compromise", "Distribute malicious operator to manage cluster resources"),
    ("Container image provenance forgery via attestation", "Forge supply chain attestations to bypass verification"),
    ("Service mesh sidecar proxy supply chain injection", "Inject malicious sidecar proxy to intercept service traffic"),
    ("Container image tag mutability attack", "Overwrite mutable image tags with malicious versions"),
    ("Kubernetes admission controller webhook bypass", "Bypass admission control via webhook timeout exploitation"),
])

add_examples("Firmware Supply Chain", [
    ("Firmware update mechanism without signature verification", "Flash malicious firmware bypassing signature checks"),
    ("UEFI rootkit injection via compromised firmware update", "Inject bootkit through signed firmware update mechanism"),
    ("Hardware implant firmware backdoor activation", "Activate hidden backdoor in compromised hardware firmware"),
    ("BIOS password bypass via jumper short circuit", "Clear BIOS passwords via hardware jumper manipulation"),
    ("Firmware supply chain interception during manufacturing", "Intercept devices to inject firmware backdoor pre-delivery"),
    ("Embedded device firmware extraction via JTAG debug", "Extract firmware via JTAG interface for reverse engineering"),
    ("IoT device default credential exploitation in firmware", "Exploit hardcoded credentials in IoT device firmware"),
    ("Firmware downgrade attack to vulnerable version", "Force firmware downgrade to exploit known vulnerabilities"),
    ("Secure boot bypass via compromised platform key", "Replace platform key to disable secure boot verification"),
    ("Firmware OTA update man-in-the-middle interception", "Intercept OTA updates to inject malicious firmware"),
])

# Verify counts
print(f"Total examples collected: {len(all_examples)}")
assert len(all_examples) == 150, f"Expected 150, got {len(all_examples)}"

api_count = sum(1 for e in all_examples if any(x in e["metadata"]["subcategory"] for x in ["GraphQL", "gRPC", "REST", "Authentication", "Deserialization"]))
mobile_count = sum(1 for e in all_examples if any(x in e["metadata"]["subcategory"] for x in ["iOS", "Android", "Mobile", "Reverse"]))
supply_count = sum(1 for e in all_examples if any(x in e["metadata"]["subcategory"] for x in ["Dependency", "Build", "Software", "Container", "Firmware"]))

print(f"Total: {len(all_examples)} | API: {api_count} | Mobile: {mobile_count} | Supply Chain: {supply_count}")

# Write JSONL
with open(output_path, 'w', encoding='utf-8') as f:
    for ex in all_examples:
        f.write(json.dumps(ex, ensure_ascii=False) + '\n')

print(f"Written to: {output_path}")
