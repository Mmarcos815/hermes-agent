// trustkill: accept-all X509TrustManager (own session, read-only posture)
send("[trustkill ready]");
Java.perform(function () {
    var managers = [
        "javax.net.ssl.X509TrustManager",
        "com.android.org.conscrypt.TrustManagerImpl",
        "org.chromium.net.impl.X509TrustManagerImpl"
    ];
    managers.forEach(function (cn) {
        try {
            var M = Java.use(cn);
            var ovs = M.checkServerTrusted.overloads;
            ovs.forEach(function (ov) {
                ov.implementation = function () { send("[trustkill] bypass " + cn); return; };
            });
            send("[trustkill] hooked " + cn + " x" + ovs.length);
        } catch (e) { send("[trustkill] skip " + cn); }
    });
});
send("[trustkill armed]");
