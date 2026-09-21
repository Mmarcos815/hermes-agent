// intercept: Unity activity lifecycle + TLS plaintext + token stores (read-only, own session)
send("[intercept ready]");
Java.perform(function () {
try {
    var UPA = Java.use("com.unity3d.player.UnityPlayerActivity");
    UPA.onCreate.overload("android.os.Bundle").implementation = function (b) {
        send("[unity] onCreate " + this);
        return this.onCreate(b);
    };
} catch (e) { send("[unity] hook skip: " + e); }

// javax.net.ssl read/write plaintext (covers Java-stack TLS incl SDKs)
try {
    var SSLS = Java.use("com.android.org.conscrypt.Java8EngineSocket");
} catch (e) {}
["com.android.org.conscrypt.ConscryptEngineSocketImpl", "javax.net.ssl.SSLSocket"].forEach(function (cn) {
    try {
        var S = Java.use(cn);
        try {
            S.getInputStream.implementation = function () {
                var ism = this.getInputStream();
                send("[tls] input stream opened " + cn);
                return ism;
            };
        } catch (e) {}
    } catch (e) {}
});

// OkHttp request/response lines (OneSignal/Sumsub/Fingerprint SDKs)
try {
    var RealCall = Java.use("okhttp3.RealCall");
    send("[okhttp] present");
} catch (e) { send("[okhttp] absent: " + e); }

// SharedPreferences token stores (session/bearer at rest, own device)
try {
    var Ctx = Java.use("android.content.ContextWrapper");
    Ctx.getSharedPreferences.overload("java.lang.String", "int").implementation = function (n, m) {
        send("[prefs] open: " + n);
        return this.getSharedPreferences(n, m);
    };
} catch (e) { send("[prefs] skip: " + e); }
send("[intercept armed]");
try {
    var ISR = Java.use("java.io.InputStream");
    ISR.read.overload("[B").implementation = function (b) {
        var n = this.read(b);
        try {
            if (n > 0) {
                var s = Java.array("byte", b).slice(0, Math.min(n, 512));
                var t = "";
                for (var i = 0; i < s.length; i++) { var c = s[i] & 0xFF; t += (c >= 32 && c < 127) ? String.fromCharCode(c) : "."; }
                if (/mintpull|bearer|token|api|auth|checkin|login/i.test(t)) send("[http] " + t.slice(0, 300));
            }
        } catch (e) {}
        return n;
    };
    send("[readhook armed]");
} catch (e) { send("[readhook] skip: " + e); }
});
